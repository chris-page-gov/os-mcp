import json
import sys
from typing import Callable


class StdioAuthenticator:
    """
    Authenticate stdio connections using environment variables.
    Currently just checks that key is not empty.
    This is a placeholder for a more secure authentication mechanism in the future.
    """

    def __init__(self):
        self.authenticated = False

    def require_auth(self, func: Callable) -> Callable:
        """Decorator to require authentication for a function."""

        def wrapper(*args, **kwargs):
            if not self.authenticated:
                print(
                    json.dumps({"error": "Authentication required", "code": 401}),
                    file=sys.stderr,
                )
                return None
            return func(*args, **kwargs)

        return wrapper

    def authenticate(self, key: str) -> bool:
        """
        Authenticate with API key.
        Currently just checks that key is not empty.
        """
        # Always require a key, but accept any non-empty value
        self.authenticated = bool(key and key.strip())
        return self.authenticated
