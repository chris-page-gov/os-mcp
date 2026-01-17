"""Detailed tests for error_envelope module"""

import pytest
from utils.error_envelope import ErrorCode, build_error_envelope, _DEFAULT_RETRY_HINTS


class TestErrorCodeEnum:
    """Tests for ErrorCode enum"""

    def test_all_error_codes_have_values(self):
        """Test that all error codes have string values"""
        for code in ErrorCode:
            assert isinstance(code.value, str)
            assert len(code.value) > 0

    def test_error_code_values_are_uppercase(self):
        """Test that error code values are uppercase"""
        for code in ErrorCode:
            assert code.value == code.value.upper()

    def test_specific_error_codes_exist(self):
        """Test that specific expected error codes exist"""
        expected_codes = [
            "GENERAL_ERROR",
            "INVALID_INPUT",
            "AUTH_REQUIRED",
            "RATE_LIMIT",
            "NOT_FOUND",
            "WORKFLOW_CONTEXT_REQUIRED",
            "INVALID_COLLECTION",
            "UPSTREAM_ERROR",
        ]

        actual_codes = [code.value for code in ErrorCode]

        for expected in expected_codes:
            assert expected in actual_codes


class TestDefaultRetryHints:
    """Tests for default retry hints mapping"""

    def test_all_error_codes_have_hints(self):
        """Test that all error codes have retry hints"""
        for code in ErrorCode:
            assert code in _DEFAULT_RETRY_HINTS
            assert len(_DEFAULT_RETRY_HINTS[code]) > 0

    def test_hints_are_actionable(self):
        """Test that hints contain action words"""
        action_words = ["retry", "validate", "call", "wait", "review", "verify", "acquire"]

        for hint in _DEFAULT_RETRY_HINTS.values():
            hint_lower = hint.lower()
            assert any(word in hint_lower for word in action_words)


class TestBuildErrorEnvelope:
    """Tests for build_error_envelope function"""

    def test_basic_envelope_structure(self):
        """Test basic error envelope structure"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Something went wrong"
        )

        assert "error" in envelope
        assert "message" in envelope
        assert "error_code" in envelope
        assert "tool" in envelope
        assert "retry_guidance" in envelope

    def test_envelope_message_in_both_fields(self):
        """Test that message appears in both error and message fields"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Test error message"
        )

        assert envelope["error"] == "Test error message"
        assert envelope["message"] == "Test error message"

    def test_envelope_default_error_code(self):
        """Test default error code is GENERAL_ERROR"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Error"
        )

        assert envelope["error_code"] == "GENERAL_ERROR"

    def test_envelope_with_specific_error_code(self):
        """Test envelope with specific ErrorCode enum"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Not found",
            code=ErrorCode.NOT_FOUND
        )

        assert envelope["error_code"] == "NOT_FOUND"

    def test_envelope_with_string_error_code(self):
        """Test envelope with string error code (legacy)"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Custom error",
            code="CUSTOM_CODE"
        )

        assert envelope["error_code"] == "CUSTOM_CODE"

    def test_envelope_tool_name(self):
        """Test tool name is included"""
        envelope = build_error_envelope(
            tool="search_features",
            message="Error"
        )

        assert envelope["tool"] == "search_features"

    def test_envelope_with_details(self):
        """Test envelope with details dict"""
        details = {"collection": "bld-fts-building-1", "field": "osid"}

        envelope = build_error_envelope(
            tool="test_tool",
            message="Error",
            details=details
        )

        assert envelope["details"] == details

    def test_envelope_without_details(self):
        """Test envelope without details omits the field"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Error"
        )

        assert "details" not in envelope

    def test_envelope_retry_guidance_structure(self):
        """Test retry_guidance structure"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Error"
        )

        assert "tool" in envelope["retry_guidance"]
        assert "hint" in envelope["retry_guidance"]
        assert envelope["retry_guidance"]["tool"] == "test_tool"

    def test_envelope_custom_retry_hint(self):
        """Test custom retry hint override"""
        custom_hint = "Do this specific thing to fix it"

        envelope = build_error_envelope(
            tool="test_tool",
            message="Error",
            retry_hint=custom_hint
        )

        assert envelope["retry_guidance"]["hint"] == custom_hint

    def test_envelope_default_retry_hint_by_code(self):
        """Test that appropriate default retry hint is used"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Workflow required",
            code=ErrorCode.WORKFLOW_CONTEXT_REQUIRED
        )

        expected_hint = _DEFAULT_RETRY_HINTS[ErrorCode.WORKFLOW_CONTEXT_REQUIRED]
        assert envelope["retry_guidance"]["hint"] == expected_hint

    def test_envelope_with_all_parameters(self):
        """Test envelope with all parameters"""
        envelope = build_error_envelope(
            tool="complex_tool",
            message="Complex error occurred",
            code=ErrorCode.UPSTREAM_ERROR,
            details={"status": 500, "upstream": "external-api"},
            retry_hint="Wait 30 seconds and retry"
        )

        assert envelope["tool"] == "complex_tool"
        assert envelope["message"] == "Complex error occurred"
        assert envelope["error_code"] == "UPSTREAM_ERROR"
        assert envelope["details"]["status"] == 500
        assert envelope["retry_guidance"]["hint"] == "Wait 30 seconds and retry"

    def test_envelope_unknown_string_code_uses_general_hint(self):
        """Test that unknown string code falls back to GENERAL_ERROR hint"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Unknown error",
            code="UNKNOWN_CUSTOM_CODE"
        )

        expected_hint = _DEFAULT_RETRY_HINTS[ErrorCode.GENERAL_ERROR]
        assert envelope["retry_guidance"]["hint"] == expected_hint

    def test_envelope_known_string_code_uses_appropriate_hint(self):
        """Test that known string code uses appropriate hint"""
        envelope = build_error_envelope(
            tool="test_tool",
            message="Rate limited",
            code="RATE_LIMIT"  # String version of known code
        )

        expected_hint = _DEFAULT_RETRY_HINTS[ErrorCode.RATE_LIMIT]
        assert envelope["retry_guidance"]["hint"] == expected_hint


class TestErrorEnvelopeSerializability:
    """Tests for error envelope JSON serializability"""

    def test_envelope_is_json_serializable(self):
        """Test that envelope can be JSON serialized"""
        import json

        envelope = build_error_envelope(
            tool="test_tool",
            message="Error message",
            code=ErrorCode.INVALID_INPUT,
            details={"key": "value", "number": 123}
        )

        # Should not raise
        json_str = json.dumps(envelope)
        assert isinstance(json_str, str)

        # Should roundtrip
        parsed = json.loads(json_str)
        assert parsed == envelope

    def test_envelope_with_nested_details(self):
        """Test envelope with nested details structure"""
        import json

        envelope = build_error_envelope(
            tool="test_tool",
            message="Error",
            details={
                "level1": {
                    "level2": {
                        "value": [1, 2, 3]
                    }
                }
            }
        )

        json_str = json.dumps(envelope)
        parsed = json.loads(json_str)
        assert parsed["details"]["level1"]["level2"]["value"] == [1, 2, 3]
