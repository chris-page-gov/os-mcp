import os
from typing import List, Callable, Awaitable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


def get_valid_bearer_tokens() -> List[str]:
    """
    Get valid bearer tokens from environment variable.
    """
    try:
        tokens = os.environ.get("BEARER_TOKENS", "").split(",")
        valid_tokens = [
            t.strip() for t in tokens if t.strip()
        ]  # Added .strip() to clean whitespace

        if not valid_tokens:
            logger.warning(
                "No BEARER_TOKENS configured, all authentication will be rejected"
            )
            return []  # Return empty list to block all authentication attempts

        return valid_tokens
    except Exception as e:
        logger.error(f"Error getting valid tokens: {e}")
        return []  # Return empty list on error as well


async def verify_bearer_token(token: str) -> bool:
    """Verify bearer token is valid."""
    try:
        valid_tokens = get_valid_bearer_tokens()

        # If no valid tokens are configured, or token is empty, reject all requests
        if not valid_tokens or not token:
            return False

        # Check if the provided token is in the valid list
        return token in valid_tokens
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        return False  # Return False on error to block access


class HTTPMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        # Skip auth for auth discovery endpoints and OPTIONS requests
        if request.url.path == "/.well-known/mcp-auth" or request.method == "OPTIONS":
            return await call_next(request)

        # Validate Origin header
        origin = request.headers.get("origin", "")
        if origin and not self._is_valid_origin(origin, request):
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(
                f"Blocked request with suspicious origin from {client_ip}, Origin: {origin}"
            )
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid origin"},
            )

        # Block calls from browser plugins based on headers
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

        # Bearer token authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            if await verify_bearer_token(token):
                # Add token to request state for access in session manager
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
        """
        Validate Origin header to prevent DNS rebinding attacks.
        """
        # Allow localhost and standard local development origins
        valid_local_origins = ["http://localhost:", "http://127.0.0.1:"]

        # In production, you should check against your actual allowed domains
        valid_domains = os.environ.get("ALLOWED_ORIGINS", "").split(",")
        valid_domains = [d.strip() for d in valid_domains if d.strip()]

        # Check local origins
        for valid_origin in valid_local_origins:
            if origin.startswith(valid_origin):
                return True

        # Check against whitelist domains
        for domain in valid_domains:
            if (
                origin == domain
                or origin.startswith(f"https://{domain}")
                or origin.startswith(f"http://{domain}")
            ):
                return True

        return False

    def _is_browser_plugin(self, user_agent: str, request: Request) -> bool:
        """
        Check if request is from a browser plugin.
        """
        plugin_patterns = [
            "Chrome-Extension",
            "Mozilla/5.0 (compatible; Extension)",
            "Browser-Extension",
        ]

        for pattern in plugin_patterns:
            if pattern.lower() in user_agent.lower():
                return True

        # Check Origin header
        origin = request.headers.get("origin", "")
        if origin and (
            origin.startswith("chrome-extension://")
            or origin.startswith("moz-extension://")
            or origin.startswith("safari-extension://")
        ):
            return True

        return False
