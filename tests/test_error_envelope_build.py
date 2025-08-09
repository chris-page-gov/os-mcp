import pytest
from utils.error_envelope import build_error_envelope, ErrorCode


def test_build_error_envelope_enum():
    env = build_error_envelope(tool="search", message="bad input", code=ErrorCode.INVALID_INPUT)
    assert env["error_code"] == ErrorCode.INVALID_INPUT.value
    assert env["retry_guidance"]["hint"].lower().startswith("validate")


def test_build_error_envelope_string_maps():
    env = build_error_envelope(tool="search", message="bad input", code="INVALID_INPUT")
    assert env["error_code"] == "INVALID_INPUT"
    assert "retry_guidance" in env


def test_build_error_envelope_unknown_string():
    env = build_error_envelope(tool="x", message="oops", code="SOMETHING_NEW")
    assert env["error_code"] == "SOMETHING_NEW"
    # Falls back to general error hint
    assert "retry_guidance" in env
    assert "retry" in env["retry_guidance"]["hint"].lower()


def test_build_error_envelope_custom_retry():
    env = build_error_envelope(tool="x", message="oops", code=ErrorCode.GENERAL_ERROR, retry_hint="Custom")
    assert env["retry_guidance"]["hint"] == "Custom"
