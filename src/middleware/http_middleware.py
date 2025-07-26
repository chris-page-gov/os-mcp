import os
import time
from collections import defaultdict, deque
from typing import List, Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """HTTP-layer rate limiting"""

    def __init__(self, requests_per_minute: int = 10, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.request_timestamps = defaultdict(lambda: deque())

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = time.time()
        timestamps = self.request_timestamps[client_id]

        while timestamps and current_time - timestamps[0] >= self.window_seconds:
            timestamps.popleft()

        if len(timestamps) >= self.requests_per_minute:
            logger.warning(f"HTTP rate limit exceeded for client {client_id}")
            return False

        timestamps.append(current_time)
        return True


def get_valid_bearer_tokens() -> List[str]:
    """Get valid bearer tokens from environment variable."""
    try:
        tokens = os.environ.get("BEARER_TOKENS", "").split(",")
        valid_tokens = [t.strip() for t in tokens if t.strip()]

        if not valid_tokens:
            logger.warning(
                "No BEARER_TOKENS configured, all authentication will be rejected"
            )
            return []

        return valid_tokens
    except Exception as e:
        logger.error(f"Error getting valid tokens: {e}")
        return []


async def verify_bearer_token(token: str) -> bool:
    """Verify bearer token is valid."""
    try:
        valid_tokens = get_valid_bearer_tokens()
        if not valid_tokens or not token:
            return False
        return token in valid_tokens
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return False


class HTTPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 10):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute=requests_per_minute)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path == "/.well-known/mcp-auth" or request.method == "OPTIONS":
            return await call_next(request)

        session_id = request.headers.get("mcp-session-id")
        if not session_id:
            client_ip = request.client.host if request.client else "unknown"
            session_id = f"ip-{client_ip}"

        if not self.rate_limiter.check_rate_limit(session_id):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={"Retry-After": "60"},
            )

        origin = request.headers.get("origin", "")
        if origin and not self._is_valid_origin(origin, request):
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                f"Blocked request with suspicious origin from {client_ip}, Origin: {origin}"
            )
            return JSONResponse(status_code=403, content={"detail": "Invalid origin"})

        user_agent = request.headers.get("user-agent", "")
        if self._is_browser_plugin(user_agent, request):
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                f"Blocked browser plugin access from {client_ip}, User-Agent: {user_agent}"
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Browser plugin access is not allowed"},
            )

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            if await verify_bearer_token(token):
                request.state.token = token
                return await call_next(request)
            else:
                logger.warning(
                    f"Invalid bearer token attempt from {request.client.host if request.client else 'unknown'}"
                )
        else:
            logger.warning(
                f"Missing or invalid Authorization header from {request.client.host if request.client else 'unknown'}"
            )

        return JSONResponse(
            status_code=401,
            content={"detail": "Authentication required"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    def _is_valid_origin(self, origin: str, request: Request) -> bool:
        """Validate Origin header to prevent DNS rebinding attacks."""
        valid_local_origins = ["http://localhost:", "http://127.0.0.1:"]
        valid_domains = os.environ.get("ALLOWED_ORIGINS", "").split(",")
        valid_domains = [d.strip() for d in valid_domains if d.strip()]

        for valid_origin in valid_local_origins:
            if origin.startswith(valid_origin):
                return True

        for domain in valid_domains:
            if (
                origin == domain
                or origin.startswith(f"https://{domain}")
                or origin.startswith(f"http://{domain}")
            ):
                return True

        return False

    def _is_browser_plugin(self, user_agent: str, request: Request) -> bool:
        """Check if request is from a browser plugin."""
        plugin_patterns = [
            "Chrome-Extension",
            "Mozilla/5.0 (compatible; Extension)",
            "Browser-Extension",
        ]

        for pattern in plugin_patterns:
            if pattern.lower() in user_agent.lower():
                return True

        origin = request.headers.get("origin", "")
        if origin and (
            origin.startswith("chrome-extension://")
            or origin.startswith("moz-extension://")
            or origin.startswith("safari-extension://")
        ):
            return True

        return False
