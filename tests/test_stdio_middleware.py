"""Tests for STDIO middleware authentication and rate limiting"""

import json
import time
import pytest
from unittest.mock import MagicMock, patch

from middleware.stdio_middleware import StdioRateLimiter, StdioMiddleware


class TestStdioRateLimiter:
    """Tests for StdioRateLimiter class"""

    def test_init(self):
        """Test rate limiter initialization"""
        limiter = StdioRateLimiter(requests_per_minute=10, window_seconds=60)

        assert limiter.requests_per_minute == 10
        assert limiter.window_seconds == 60
        assert len(limiter.request_timestamps) == 0

    def test_check_rate_limit_within_limit(self):
        """Test requests within rate limit pass"""
        limiter = StdioRateLimiter(requests_per_minute=5, window_seconds=60)

        # Should allow 5 requests
        for i in range(5):
            assert limiter.check_rate_limit() is True

    def test_check_rate_limit_exceeded(self):
        """Test rate limit exceeded returns False"""
        limiter = StdioRateLimiter(requests_per_minute=3, window_seconds=60)

        # Fill up the limit
        for _ in range(3):
            limiter.check_rate_limit()

        # Next request should be rejected
        assert limiter.check_rate_limit() is False

    def test_check_rate_limit_clears_old_requests(self):
        """Test that old requests are cleared from window"""
        limiter = StdioRateLimiter(requests_per_minute=2, window_seconds=1)

        # Make 2 requests
        limiter.check_rate_limit()
        limiter.check_rate_limit()

        # Should be at limit
        assert limiter.check_rate_limit() is False

        # Wait for window to pass
        time.sleep(1.1)

        # Old requests should be cleared, new one allowed
        assert limiter.check_rate_limit() is True


class TestStdioMiddleware:
    """Tests for StdioMiddleware class"""

    def test_init(self):
        """Test middleware initialization"""
        middleware = StdioMiddleware(requests_per_minute=15)

        assert middleware.authenticated is False
        assert middleware.client_id == "anonymous"
        assert middleware.rate_limiter.requests_per_minute == 15

    def test_authenticate_success(self):
        """Test successful authentication"""
        middleware = StdioMiddleware()

        result = middleware.authenticate("valid-api-key")

        assert result is True
        assert middleware.authenticated is True
        assert middleware.client_id == "valid-api-key"

    def test_authenticate_empty_key(self):
        """Test authentication fails with empty key"""
        middleware = StdioMiddleware()

        result = middleware.authenticate("")

        assert result is False
        assert middleware.authenticated is False

    def test_authenticate_whitespace_key(self):
        """Test authentication fails with whitespace-only key"""
        middleware = StdioMiddleware()

        result = middleware.authenticate("   ")

        assert result is False
        assert middleware.authenticated is False

    def test_authenticate_none_key(self):
        """Test authentication fails with None key"""
        middleware = StdioMiddleware()

        result = middleware.authenticate(None)

        assert result is False
        assert middleware.authenticated is False


class TestRequireAuthAndRateLimitDecorator:
    """Tests for require_auth_and_rate_limit decorator"""

    @pytest.mark.asyncio
    async def test_async_unauthenticated_blocked(self):
        """Test async function blocked when not authenticated"""
        middleware = StdioMiddleware()

        @middleware.require_auth_and_rate_limit
        async def test_func():
            return "success"

        result = await test_func()
        data = json.loads(result)

        assert data["error"] == "Authentication required"
        assert data["code"] == 401

    @pytest.mark.asyncio
    async def test_async_authenticated_allowed(self):
        """Test async function allowed when authenticated"""
        middleware = StdioMiddleware()
        middleware.authenticate("valid-key")

        @middleware.require_auth_and_rate_limit
        async def test_func():
            return "success"

        result = await test_func()
        assert result == "success"

    @pytest.mark.asyncio
    async def test_async_rate_limited(self):
        """Test async function rate limited"""
        middleware = StdioMiddleware(requests_per_minute=2)
        middleware.authenticate("valid-key")

        @middleware.require_auth_and_rate_limit
        async def test_func():
            return "success"

        # Make requests up to limit
        await test_func()
        await test_func()

        # Next should be rate limited
        result = await test_func()
        data = json.loads(result)

        assert data["error"] == "Rate limited"
        assert data["code"] == 429

    def test_sync_unauthenticated_blocked(self):
        """Test sync function blocked when not authenticated"""
        middleware = StdioMiddleware()

        @middleware.require_auth_and_rate_limit
        def test_func():
            return "success"

        result = test_func()
        data = json.loads(result)

        assert data["error"] == "Authentication required"
        assert data["code"] == 401

    def test_sync_authenticated_allowed(self):
        """Test sync function allowed when authenticated"""
        middleware = StdioMiddleware()
        middleware.authenticate("valid-key")

        @middleware.require_auth_and_rate_limit
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

    def test_sync_rate_limited(self):
        """Test sync function rate limited"""
        middleware = StdioMiddleware(requests_per_minute=2)
        middleware.authenticate("valid-key")

        @middleware.require_auth_and_rate_limit
        def test_func():
            return "success"

        # Make requests up to limit
        test_func()
        test_func()

        # Next should be rate limited
        result = test_func()
        data = json.loads(result)

        assert data["error"] == "Rate limited"
        assert data["code"] == 429


class TestStdioMiddlewareIntegration:
    """Integration tests for stdio middleware"""

    @pytest.mark.asyncio
    async def test_full_flow_authenticated(self):
        """Test full flow with authentication"""
        middleware = StdioMiddleware(requests_per_minute=10)

        # Not authenticated initially
        assert middleware.authenticated is False

        # Authenticate
        assert middleware.authenticate("my-key") is True

        @middleware.require_auth_and_rate_limit
        async def protected_func(arg):
            return f"result: {arg}"

        # Should work now
        result = await protected_func("test")
        assert result == "result: test"

    @pytest.mark.asyncio
    async def test_rate_limit_recovery(self):
        """Test that rate limit recovers after window"""
        middleware = StdioMiddleware(requests_per_minute=1)
        middleware.rate_limiter.window_seconds = 1  # Short window for test
        middleware.authenticate("key")

        @middleware.require_auth_and_rate_limit
        async def test_func():
            return "ok"

        # First request passes
        result1 = await test_func()
        assert result1 == "ok"

        # Second request rate limited
        result2 = await test_func()
        assert "Rate limited" in result2

        # Wait for window
        time.sleep(1.1)

        # Should work again
        result3 = await test_func()
        assert result3 == "ok"
