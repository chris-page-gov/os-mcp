import os
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from utils.logging_config import get_logger

logger = get_logger(__name__)


def get_valid_bearer_tokens() -> List[str]:
    """
    Get valid bearer tokens from environment variable.
    """
    tokens = os.environ.get("BEARER_TOKENS", "").split(",")
    valid_tokens = [t for t in tokens if t.strip()]

    if not valid_tokens:
        return ["dev-token"]

    return valid_tokens


async def verify_bearer_token(token: str) -> bool:
    """Verify bearer token is valid."""
    valid_tokens = get_valid_bearer_tokens()
    if not token or token not in valid_tokens:
        return False
    return True


class HTTPMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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

        # Skip auth for auth discovery endpoints
        if request.url.path == "/.well-known/mcp-auth":
            return await call_next(request)

        # Bearer token authentication
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
            if await verify_bearer_token(token):
                # Add token to request state for access in session manager
                request.state.token = token
                return await call_next(request)

        return JSONResponse(
            status_code=401, content={"detail": "Authentication required"}
        )

    def _is_valid_origin(self, origin: str, request: Request) -> bool:
        """
        Validate Origin header to prevent DNS rebinding attacks.
        """
        # Allow localhost and standard local development origins
        valid_local_origins = ["http://localhost:", "http://127.0.0.1:"]

        for valid_origin in valid_local_origins:
            if origin.startswith(valid_origin):
                # Check if the port matches our server port
                # This is a simplified approach - in production you'd use more robust validation
                return True

        # Implement additional origin validation logic here
        # For example, check against a whitelist of allowed domains

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
