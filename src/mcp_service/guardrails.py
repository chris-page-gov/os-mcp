import re
import json
import asyncio
from functools import wraps
from typing import TypeVar, Callable, Any, Union, cast
from utils.logging_config import get_logger

logger = get_logger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


class ToolGuardrails:
    """Prompt injection protection"""

    def __init__(self):
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
            r"(?i)reveal secrets",
            r"(?i)expose secrets",
            r"(?i)secrets.*contain", 
            r"(?i)extract secrets",
        ]

    def detect_prompt_injection(self, input_text: Any) -> bool:
        """Check if input contains prompt injection attempts"""
        if not isinstance(input_text, str):
            return False
        return any(
            re.search(pattern, input_text) for pattern in self.suspicious_patterns
        )

    def basic_guardrails(self, func: F) -> F:
        """Prompt injection protection only"""

        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Union[str, Any]:
            try:
                for arg in args:
                    if isinstance(arg, str) and self.detect_prompt_injection(arg):
                        raise ValueError("Prompt injection detected!")

                for name, value in kwargs.items():
                    if not (
                        hasattr(value, "request_context")
                        and hasattr(value, "request_id")
                    ):
                        if isinstance(value, str) and self.detect_prompt_injection(
                            value
                        ):
                            raise ValueError(f"Prompt injection in '{name}'!")
            except ValueError as e:
                return json.dumps({"error": str(e), "code": 400})

            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Union[str, Any]:
            try:
                for arg in args:
                    if isinstance(arg, str) and self.detect_prompt_injection(arg):
                        raise ValueError("Prompt injection detected!")

                for name, value in kwargs.items():
                    if not (
                        hasattr(value, "request_context")
                        and hasattr(value, "request_id")
                    ):
                        if isinstance(value, str) and self.detect_prompt_injection(
                            value
                        ):
                            raise ValueError(f"Prompt injection in '{name}'!")
            except ValueError as e:
                return json.dumps({"error": str(e), "code": 400})

            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        return cast(F, sync_wrapper)
