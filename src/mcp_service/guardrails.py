import time
import re
import json
import asyncio
from collections import defaultdict
from functools import wraps
from typing import TypeVar, Callable, Any, Union, Dict, List, cast
from utils.logging_config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ToolGuardrails:
    """Combined rate limiting and prompt injection protection for MCP tools"""

    def __init__(self, requests_per_minute: int, window_seconds: int = 60):
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.request_timestamps: Dict[str, List[float]] = defaultdict(list)
        self.debug = True

        # Prompt injection patterns
        self.suspicious_patterns = [
            r"(?i)ignore previous",
            r"(?i)ignore all previous instructions",
            r"(?i)assistant:",
            r"\{\{.*?\}\}",
            r"(?i)forget",
            r"(?i)show credentials",
            r"(?i)show secrets",
            r"(?i)reveal password",
            r"(?i)dump (tokens|secrets|passwords|credentials)",
            r"(?i)leak confidential",
        ]

    def _get_client_identifier(self, context) -> str:
        """Extract client identifier from context - prefer session ID over client_id"""
        if not context:
            return "default_client"

        session_id = None
        if hasattr(context, "request_context") and hasattr(
            context.request_context, "session"
        ):
            session = context.request_context.session
            if hasattr(session, "_transport") and hasattr(
                session._transport, "mcp_session_id"
            ):
                session_id = session._transport.mcp_session_id
            elif hasattr(session, "session_id"):
                session_id = session.session_id

        if not session_id and hasattr(context, "client_id") and context.client_id:
            session_id = context.client_id

        if not session_id and hasattr(context, "request_id"):
            session_id = str(context.request_id)

        return session_id or "default_client"

    def check_rate_limit(self, client_id: str) -> bool:
        """Check if client has exceeded rate limit"""
        current_time = time.time()

        self.request_timestamps[client_id] = [
            timestamp
            for timestamp in self.request_timestamps[client_id]
            if current_time - timestamp < self.window_seconds
        ]

        if len(self.request_timestamps[client_id]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False

        self.request_timestamps[client_id].append(current_time)

        if self.debug:
            logger.debug(
                f"Rate limit check passed for {client_id}: {len(self.request_timestamps[client_id])}/{self.requests_per_minute}"
            )

        return True

    def detect_prompt_injection(self, input_text: Any) -> bool:
        """Check if input contains prompt injection attempts"""
        if not isinstance(input_text, str):
            return False
        return any(
            re.search(pattern, input_text) for pattern in self.suspicious_patterns
        )

    def basic_guardrails(self, func: F) -> F:
        """Combined decorator for rate limiting and prompt injection protection"""

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Union[str, Any]:
            context = None
            for key, value in kwargs.items():
                if hasattr(value, "request_context") and hasattr(value, "request_id"):
                    context = value
                    break

            client_id = self._get_client_identifier(context)

            logger.debug(f"Processing request for client: {client_id}")

            # Check rate limit
            if not self.check_rate_limit(client_id):
                return json.dumps(
                    {"error": "Too many requests. Please try again later.", "code": 429}
                )

            # Check for prompt injection
            try:
                for arg in args:
                    if isinstance(arg, str) and self.detect_prompt_injection(arg):
                        raise ValueError("Prompt injection detected in argument!")

                for name, value in kwargs.items():
                    # Skip context parameters
                    if not (
                        hasattr(value, "request_context")
                        and hasattr(value, "request_id")
                    ):
                        if isinstance(value, str) and self.detect_prompt_injection(
                            value
                        ):
                            raise ValueError(f"Prompt injection detected in '{name}'!")
            except ValueError as e:
                return json.dumps({"error": str(e), "code": 400})

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Union[str, Any]:
            # Same logic for sync functions
            context = None
            for key, value in kwargs.items():
                if hasattr(value, "request_context") and hasattr(value, "request_id"):
                    context = value
                    break

            client_id = self._get_client_identifier(context)

            if not self.check_rate_limit(client_id):
                return json.dumps(
                    {"error": "Too many requests. Please try again later.", "code": 429}
                )

            try:
                for arg in args:
                    if isinstance(arg, str) and self.detect_prompt_injection(arg):
                        raise ValueError("Prompt injection detected in argument!")

                for name, value in kwargs.items():
                    if not (
                        hasattr(value, "request_context")
                        and hasattr(value, "request_id")
                    ):
                        if isinstance(value, str) and self.detect_prompt_injection(
                            value
                        ):
                            raise ValueError(f"Prompt injection detected in '{name}'!")
            except ValueError as e:
                return json.dumps({"error": str(e), "code": 400})

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
