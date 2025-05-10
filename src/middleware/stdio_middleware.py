import json
from typing import Callable
from utils.logging_config import get_logger

logger = get_logger(__name__)


class StdioMiddleware:
    """
    Authenticate stdio connections using environment variables.
    Currently just checks that key is not empty.
    This is a placeholder for a more secure authentication mechanism in the future.
    """

    def __init__(self):
        self.authenticated = False
        self.client_id = "anonymous"

    def require_auth(self, func: Callable) -> Callable:
        """Decorator to require authentication for a function."""

        def wrapper(*args, **kwargs):
            # Check authentication first
            if not self.authenticated:
                logger.error(
                    json.dumps({"error": "Authentication required", "code": 401}),
                )
                return None

            return func(*args, **kwargs)

        return wrapper

    def authenticate(self, key: str) -> bool:
        """
        Authenticate with API key.
        Currently just checks that key is not empty.
        Also sets client_id for identification.
        """
        if key and key.strip():
            self.authenticated = True
            # Use the key as the client identifier
            self.client_id = key
            return True
        else:
            self.authenticated = False
            return False
