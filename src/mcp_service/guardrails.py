import time
import re
import json
import asyncio
from collections import defaultdict
from functools import wraps
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ToolGuardrails:
    """
    Combined rate limiting and prompt injection protection for MCP tools
    Very basic implementation for now!!
    TODO: Add more sophisticated prompt injection detection
    """

    def __init__(self, requests_per_minute: int, window_seconds: int = 60, client_id: str = "default_client"):
        # Rate limiting settings
        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.request_timestamps = defaultdict(list)
        self.client_id = client_id
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

        if self.debug:
            logger.debug(f"ToolGuardrails initialized with {requests_per_minute} rpm")

    def check_rate_limit(self, client_id):
        """Check if client has exceeded rate limit"""
        if self.debug:
            logger.debug(f"Checking rate limit for client '{client_id}'")

        current_time = time.time()

        # Debug: show current timestamps
        if self.debug:
            current_count = len(self.request_timestamps[client_id])
            logger.debug(
                f"Current timestamps: {current_count}/{self.requests_per_minute}"
            )

        # Remove timestamps older than the window
        self.request_timestamps[client_id] = [
            timestamp
            for timestamp in self.request_timestamps[client_id]
            if current_time - timestamp < self.window_seconds
        ]

        # Check if over limit
        if len(self.request_timestamps[client_id]) >= self.requests_per_minute:
            if self.debug:
                logger.debug(f"RATE LIMIT EXCEEDED for '{client_id}'")
            logger.warning(f"Rate limit exceeded for client {client_id}")
            return False

        # Record this request
        self.request_timestamps[client_id].append(current_time)

        if self.debug:
            logger.debug(
                f"Request recorded. New count: {len(self.request_timestamps[client_id])}"
            )
        return True

    def detect_prompt_injection(self, input_text):
        """Check if input contains prompt injection attempts"""
        if not isinstance(input_text, str):
            return False
        return any(
            re.search(pattern, input_text) for pattern in self.suspicious_patterns
        )

    def basic_guardrails(self, func):
        """Combined decorator for rate limiting and prompt injection protection"""

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Check rate limit first - use the current client_id at runtime
            if not self.check_rate_limit(self.client_id):
                return json.dumps(
                    {"error": "Too many requests. Please try again later.", "code": 429}
                )

            # Then check for prompt injection in arguments
            try:
                # Check positional arguments
                for arg in args:
                    if isinstance(arg, str) and self.detect_prompt_injection(arg):
                        raise ValueError(
                            "Prompt injection attempt detected in a positional argument!"
                        )

                # Check keyword arguments
                for name, value in kwargs.items():
                    if isinstance(value, str) and self.detect_prompt_injection(value):
                        raise ValueError(
                            f"Prompt injection attempt detected in argument '{name}'!"
                        )
            except ValueError as e:
                return json.dumps({"error": str(e), "code": 400})

            # If all checks pass, call the original function
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Check rate limit first - use the current client_id at runtime
            if not self.check_rate_limit(self.client_id):
                return json.dumps(
                    {"error": "Too many requests. Please try again later.", "code": 429}
                )

            # Then check for prompt injection in arguments
            try:
                # Check positional arguments
                for arg in args:
                    if isinstance(arg, str) and self.detect_prompt_injection(arg):
                        raise ValueError(
                            "Prompt injection attempt detected in a positional argument!"
                        )

                # Check keyword arguments
                for name, value in kwargs.items():
                    if isinstance(value, str) and self.detect_prompt_injection(value):
                        raise ValueError(
                            f"Prompt injection attempt detected in argument '{name}'!"
                        )
            except ValueError as e:
                return json.dumps({"error": str(e), "code": 400})

            # If all checks pass, call the original function
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
