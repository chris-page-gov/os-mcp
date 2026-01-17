"""Detailed tests for HTTP middleware"""

import os
import time
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from starlette.testclient import TestClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from middleware.http_middleware import (
    RateLimiter,
    get_valid_bearer_tokens,
    verify_bearer_token,
    HTTPMiddleware,
)


class TestRateLimiter:
    """Tests for RateLimiter class"""

    def test_init_defaults(self):
        """Test rate limiter default initialization"""
        limiter = RateLimiter()

        assert limiter.requests_per_minute == 10
        assert limiter.window_seconds == 60
        assert len(limiter.request_timestamps) == 0

    def test_init_custom_values(self):
        """Test rate limiter with custom values"""
        limiter = RateLimiter(requests_per_minute=20, window_seconds=30)

        assert limiter.requests_per_minute == 20
        assert limiter.window_seconds == 30

    def test_check_rate_limit_first_request(self):
        """Test first request is always allowed"""
        limiter = RateLimiter(requests_per_minute=5)

        result = limiter.check_rate_limit("client1")

        assert result is True
        assert len(limiter.request_timestamps["client1"]) == 1

    def test_check_rate_limit_within_limit(self):
        """Test requests within limit are allowed"""
        limiter = RateLimiter(requests_per_minute=5, window_seconds=60)

        # Make 5 requests (at limit)
        for _ in range(5):
            result = limiter.check_rate_limit("client1")
            assert result is True

        assert len(limiter.request_timestamps["client1"]) == 5

    def test_check_rate_limit_exceeded(self):
        """Test request exceeding limit is blocked"""
        limiter = RateLimiter(requests_per_minute=3, window_seconds=60)

        # Fill limit
        for _ in range(3):
            limiter.check_rate_limit("client1")

        # 4th request should fail
        result = limiter.check_rate_limit("client1")

        assert result is False

    def test_check_rate_limit_different_clients(self):
        """Test rate limits are per-client"""
        limiter = RateLimiter(requests_per_minute=2, window_seconds=60)

        # Client 1 uses their limit
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")
        assert limiter.check_rate_limit("client1") is False

        # Client 2 still has full limit
        assert limiter.check_rate_limit("client2") is True
        assert limiter.check_rate_limit("client2") is True

    def test_check_rate_limit_window_expiry(self):
        """Test that old requests are cleared from window"""
        limiter = RateLimiter(requests_per_minute=2, window_seconds=1)

        # Use limit
        limiter.check_rate_limit("client1")
        limiter.check_rate_limit("client1")
        assert limiter.check_rate_limit("client1") is False

        # Wait for window to expire
        time.sleep(1.1)

        # Should be allowed again
        assert limiter.check_rate_limit("client1") is True


class TestGetValidBearerTokens:
    """Tests for get_valid_bearer_tokens function"""

    def test_get_tokens_from_bearer_tokens_env(self):
        """Test getting tokens from BEARER_TOKENS env var"""
        with patch.dict(os.environ, {"BEARER_TOKENS": "token1,token2,token3"}):
            tokens = get_valid_bearer_tokens()

            assert tokens == ["token1", "token2", "token3"]

    def test_get_tokens_strips_whitespace(self):
        """Test that whitespace is stripped from tokens"""
        with patch.dict(os.environ, {"BEARER_TOKENS": " token1 , token2 , token3 "}):
            tokens = get_valid_bearer_tokens()

            assert tokens == ["token1", "token2", "token3"]

    def test_get_tokens_ignores_empty_parts(self):
        """Test that empty parts are ignored"""
        with patch.dict(os.environ, {"BEARER_TOKENS": "token1,,token2,  ,token3"}):
            tokens = get_valid_bearer_tokens()

            assert tokens == ["token1", "token2", "token3"]

    def test_get_tokens_fallback_to_legacy(self):
        """Test fallback to legacy BEARER_TOKEN"""
        with patch.dict(os.environ, {"BEARER_TOKEN": "legacy_token"}, clear=False):
            # Remove BEARER_TOKENS if present
            os.environ.pop("BEARER_TOKENS", None)
            tokens = get_valid_bearer_tokens()

            assert tokens == ["legacy_token"]

    def test_get_tokens_empty_returns_empty_list(self):
        """Test empty env var returns empty list"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BEARER_TOKENS", None)
            os.environ.pop("BEARER_TOKEN", None)
            tokens = get_valid_bearer_tokens()

            assert tokens == []


class TestVerifyBearerToken:
    """Tests for verify_bearer_token function"""

    @pytest.mark.asyncio
    async def test_verify_valid_token(self):
        """Test verification of valid token"""
        with patch.dict(os.environ, {"BEARER_TOKENS": "valid_token"}):
            result = await verify_bearer_token("valid_token")

            assert result is True

    @pytest.mark.asyncio
    async def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        with patch.dict(os.environ, {"BEARER_TOKENS": "valid_token"}):
            result = await verify_bearer_token("invalid_token")

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_empty_token(self):
        """Test verification of empty token"""
        with patch.dict(os.environ, {"BEARER_TOKENS": "valid_token"}):
            result = await verify_bearer_token("")

            assert result is False

    @pytest.mark.asyncio
    async def test_verify_with_auth_bypass(self):
        """Test verification with auth bypass enabled"""
        with patch.dict(os.environ, {"OS_MCP_AUTH_BYPASS": "true"}):
            result = await verify_bearer_token("any_token")

            assert result is True

    @pytest.mark.asyncio
    async def test_verify_no_valid_tokens_configured(self):
        """Test verification when no tokens configured"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("BEARER_TOKENS", None)
            os.environ.pop("BEARER_TOKEN", None)
            os.environ.pop("OS_MCP_AUTH_BYPASS", None)

            result = await verify_bearer_token("some_token")

            assert result is False


class TestHTTPMiddlewareDispatch:
    """Tests for HTTPMiddleware dispatch method"""

    def setup_method(self):
        """Set up test application"""
        async def home(request):
            return JSONResponse({"status": "ok"})

        self.app = Starlette(routes=[Route("/", home)])

    @pytest.mark.asyncio
    async def test_public_endpoints_bypass_auth(self):
        """Test that public endpoints bypass authentication"""
        middleware = HTTPMiddleware(self.app)

        # Create mock request for /health
        mock_request = MagicMock()
        mock_request.url.path = "/health"
        mock_request.method = "GET"

        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_favicon_bypasses_auth(self):
        """Test that favicon.ico bypasses authentication"""
        middleware = HTTPMiddleware(self.app)

        mock_request = MagicMock()
        mock_request.url.path = "/favicon.ico"
        mock_request.method = "GET"

        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_options_request_bypasses_auth(self):
        """Test that OPTIONS requests bypass authentication"""
        middleware = HTTPMiddleware(self.app)

        mock_request = MagicMock()
        mock_request.url.path = "/some/path"
        mock_request.method = "OPTIONS"

        mock_response = MagicMock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware.dispatch(mock_request, call_next)

        call_next.assert_called_once()


class TestHTTPMiddlewareOriginValidation:
    """Tests for origin validation in HTTPMiddleware"""

    def test_valid_localhost_origin(self):
        """Test localhost origins are valid"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()

        assert middleware._is_valid_origin("http://localhost:3000", mock_request) is True
        assert middleware._is_valid_origin("http://127.0.0.1:8080", mock_request) is True

    def test_invalid_origin(self):
        """Test unknown origins are invalid"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()

        with patch.dict(os.environ, {"ALLOWED_ORIGINS": ""}):
            assert middleware._is_valid_origin("http://evil.com", mock_request) is False

    def test_allowed_origins_from_env(self):
        """Test origins from ALLOWED_ORIGINS env var"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()

        with patch.dict(os.environ, {"ALLOWED_ORIGINS": "example.com,trusted.org"}):
            assert middleware._is_valid_origin("https://example.com", mock_request) is True
            assert middleware._is_valid_origin("https://trusted.org", mock_request) is True
            assert middleware._is_valid_origin("https://untrusted.com", mock_request) is False


class TestHTTPMiddlewareBrowserPluginDetection:
    """Tests for browser plugin detection"""

    def test_detect_chrome_extension_user_agent(self):
        """Test detection of Chrome extension user agent"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""

        assert middleware._is_browser_plugin("Chrome-Extension/1.0", mock_request) is True

    def test_detect_extension_origin(self):
        """Test detection of extension origins"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()

        # Mock headers.get to return extension origin
        def get_header(name, default=""):
            if name == "origin":
                return "chrome-extension://abc123"
            return default

        mock_request.headers.get = get_header

        assert middleware._is_browser_plugin("Normal User Agent", mock_request) is True

    def test_normal_user_agent_not_detected(self):
        """Test that normal user agents are not flagged"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()
        mock_request.headers.get.return_value = ""

        assert middleware._is_browser_plugin("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", mock_request) is False

    def test_detect_moz_extension_origin(self):
        """Test detection of Firefox extension origins"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()

        def get_header(name, default=""):
            if name == "origin":
                return "moz-extension://abc123"
            return default

        mock_request.headers.get = get_header

        assert middleware._is_browser_plugin("Normal UA", mock_request) is True

    def test_detect_safari_extension_origin(self):
        """Test detection of Safari extension origins"""
        app = MagicMock()
        middleware = HTTPMiddleware(app)
        mock_request = MagicMock()

        def get_header(name, default=""):
            if name == "origin":
                return "safari-extension://abc123"
            return default

        mock_request.headers.get = get_header

        assert middleware._is_browser_plugin("Normal UA", mock_request) is True
