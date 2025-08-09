"""Utility helpers for building standardized error envelopes for tool responses."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, Mapping, Optional, Union


class ErrorCode(str, Enum):
    """Standard error codes for tool responses.

    Keep values stable – they form part of the public contract consumed by LLM tooling.
    """

    GENERAL_ERROR = "GENERAL_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    RATE_LIMIT = "RATE_LIMIT"
    NOT_FOUND = "NOT_FOUND"
    WORKFLOW_CONTEXT_REQUIRED = "WORKFLOW_CONTEXT_REQUIRED"
    INVALID_COLLECTION = "INVALID_COLLECTION"
    UPSTREAM_ERROR = "UPSTREAM_ERROR"


_DEFAULT_RETRY_HINTS: Mapping[ErrorCode, str] = {
    ErrorCode.INVALID_INPUT: "Validate and correct your parameters (check enum values & syntax) then retry",
    ErrorCode.AUTH_REQUIRED: "Acquire/refresh credentials then retry",
    ErrorCode.RATE_LIMIT: "Wait for the rate limit window to reset then retry",
    ErrorCode.WORKFLOW_CONTEXT_REQUIRED: "Call get_workflow_context() then follow planning steps",
    ErrorCode.INVALID_COLLECTION: "Call get_workflow_context() to inspect valid collections and retry",
    ErrorCode.UPSTREAM_ERROR: "Temporary upstream failure – retry with backoff if idempotent",
    ErrorCode.GENERAL_ERROR: "Review error, adjust inputs (ensure workflow context if required), then retry",
    ErrorCode.NOT_FOUND: "Verify identifier / collection and retry if a typo was present",
}


def build_error_envelope(
    *,
    tool: str,
    message: str,
    code: Union[ErrorCode, str] = ErrorCode.GENERAL_ERROR,
    details: Optional[Dict[str, Any]] = None,
    retry_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized error envelope.

    Args:
        tool: Name of tool emitting the error
        message: Human readable message (stable, concise)
        code: ErrorCode enum value or backward compatible string
        details: Optional machine-friendly structured details
        retry_hint: Optional override for retry guidance string

    Returns:
        Dict serialized envelope (JSON serialisable)
    """

    # Normalise code to string value
    if isinstance(code, ErrorCode):  # pragma: no branch (simple normalization)
        code_value = code.value
        hint_key = code
    else:  # user supplied legacy / custom string
        try:
            hint_key = ErrorCode(code)  # attempt mapping to known enum
        except Exception:  # noqa: BLE001 - broad ok: fallback to GENERAL_ERROR hint
            hint_key = ErrorCode.GENERAL_ERROR
        code_value = str(code)

    envelope: Dict[str, Any] = {
        "error": message,  # legacy compatibility field
        "message": message,
        "error_code": code_value,
        "tool": tool,
    }
    if details:
        envelope["details"] = details

    envelope["retry_guidance"] = {
        "tool": tool,
        "hint": retry_hint or _DEFAULT_RETRY_HINTS.get(hint_key, _DEFAULT_RETRY_HINTS[ErrorCode.GENERAL_ERROR]),
    }
    return envelope


__all__ = ["ErrorCode", "build_error_envelope"]
