"""Utility helpers for building standardized error envelopes for tool responses."""
from __future__ import annotations
from typing import Any, Dict, Optional


def build_error_envelope(
    *,
    tool: str,
    message: str,
    code: str = "GENERAL_ERROR",
    details: Optional[Dict[str, Any]] = None,
    retry_hint: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized error envelope.

    Kept minimal for backward compatibility while enabling forward evolution.
    """
    envelope: Dict[str, Any] = {
        "error": message,  # legacy compatibility
        "message": message,
        "error_code": code,
        "tool": tool,
    }
    if details:
        envelope["details"] = details
    envelope["retry_guidance"] = {
        "tool": tool,
        "hint": retry_hint
        or "Review error, adjust parameters (ensure workflow context if required), then retry",
    }
    return envelope

__all__ = ["build_error_envelope"]
