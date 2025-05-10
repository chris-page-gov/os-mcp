import os
from typing import List
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from utils.logging_config import get_logger

# API Key authentication
# TODO: This is a placeholder for a more secure authentication mechanism in the future. 
# This will be removed and it just the start.
api_key_header = APIKeyHeader(name="x-api-key")

# OAuth support (can be expanded)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = get_logger(__name__)


def get_valid_api_keys() -> List[str]:
    """
    Get valid API keys from environment variable.
    For now, accept any non-empty API key.
    This is a placeholder for a more secure authentication mechanism in the future.
    """
    keys = os.environ.get("API_KEYS", "").split(",")
    valid_keys = [k for k in keys if k.strip()]

    # TODO: This is a placeholder for a more secure authentication mechanism in the future
    if not valid_keys:
        return ["*"]

    return valid_keys


def verify_api_key(api_key: str = Security(api_key_header)) -> bool:
    """Verify API key is valid."""
    valid_keys = get_valid_api_keys()
    if not valid_keys or api_key not in valid_keys:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return True


async def verify_oauth_token(token: str = Depends(oauth2_scheme)) -> dict:
    """Verify OAuth token."""
    # Implement JWT verification here
    # For now, simplified implementation - will need to be updated to use JWT
    if not token or token == "invalid":
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"sub": "user", "scopes": ["read", "execute"]}


class SSEMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
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

        # Continue with normal auth flow
        api_key = request.headers.get("x-api-key")
        valid_keys = get_valid_api_keys()

        if api_key and api_key.strip():
            # Accept any non-empty key if "*" is in valid keys
            if "*" in valid_keys or api_key in valid_keys:
                return await call_next(request)

        # Try Bearer token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # Implement token verification
            token = auth_header.replace("Bearer ", "")
            # For now, simplified check
            if token and token != "invalid":
                return await call_next(request)

        return JSONResponse(
            status_code=401, content={"detail": "Authentication required"}
        )

    def _is_browser_plugin(self, user_agent: str, request: Request) -> bool:
        """
        Check if request is from a browser plugin.
        You can add specific patterns to detect browser plugins.
        """
        plugin_patterns = [
            "Chrome-Extension",
            "Mozilla/5.0 (compatible; Extension)",
            "Browser-Extension",
            # Add more patterns as needed
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
