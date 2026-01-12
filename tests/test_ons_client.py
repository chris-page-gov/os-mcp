"""Tests for ONS Statistics API Client"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from clients.ons_client import (
    ONSAPIClient,
    ONSAPIError,
    ONSRateLimiter,
    ONSCache,
    ONS_API_BASE,
)


class TestONSRateLimiter:
    """Tests for ONS rate limiter"""

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        """Test acquiring within rate limit"""
        limiter = ONSRateLimiter(max_requests=10, window=1)

        # Should be able to acquire 10 times without delay
        for _ in range(10):
            await limiter.acquire()

        assert len(limiter.requests) == 10

    @pytest.mark.asyncio
    async def test_acquire_clears_old_requests(self):
        """Test that old requests are cleared from window"""
        limiter = ONSRateLimiter(max_requests=5, window=1)

        # Add some requests
        for _ in range(3):
            await limiter.acquire()

        # Wait for window to pass
        await asyncio.sleep(1.1)

        # Acquire again - old requests should be cleared
        await limiter.acquire()
        assert len(limiter.requests) == 1


class TestONSCache:
    """Tests for ONS cache"""

    def test_set_and_get(self):
        """Test basic set and get"""
        cache = ONSCache(ttl=60)
        cache.set("key1", {"data": "value"})

        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_nonexistent(self):
        """Test getting non-existent key"""
        cache = ONSCache(ttl=60)
        result = cache.get("nonexistent")
        assert result is None

    def test_expired_entry(self):
        """Test that expired entries return None"""
        cache = ONSCache(ttl=0)  # Immediate expiry
        cache.set("key1", {"data": "value"})

        # Should be expired immediately
        import time
        time.sleep(0.1)
        result = cache.get("key1")
        assert result is None

    def test_clear(self):
        """Test clearing cache"""
        cache = ONSCache(ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestONSAPIError:
    """Tests for ONSAPIError exception"""

    def test_error_with_status_code(self):
        """Test error with status code"""
        error = ONSAPIError("Not found", status_code=404)
        assert str(error) == "Not found"
        assert error.status_code == 404

    def test_error_without_status_code(self):
        """Test error without status code"""
        error = ONSAPIError("Generic error")
        assert error.status_code == 0


class TestONSAPIClient:
    """Tests for ONS API client"""

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client works as context manager"""
        async with ONSAPIClient() as client:
            assert client._session is not None
        # Session should be closed after exiting
        assert client._session is None

    @pytest.mark.asyncio
    async def test_base_url(self):
        """Test client uses correct base URL"""
        client = ONSAPIClient()
        assert client.base_url == ONS_API_BASE
        assert "api.beta.ons.gov.uk" in client.base_url

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_request_success(self, mock_get):
        """Test successful API request"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"items": []})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient(enable_cache=False) as client:
            result = await client._request("/datasets")

        assert result == {"items": []}

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_request_error(self, mock_get):
        """Test API request error handling"""
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient(enable_cache=False) as client:
            with pytest.raises(ONSAPIError) as exc_info:
                await client._request("/datasets")

        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_cache_hit(self, mock_get):
        """Test that cached responses are returned"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"items": ["dataset1"]})
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient() as client:
            # First call
            result1 = await client._request("/datasets")
            # Second call - should hit cache
            result2 = await client._request("/datasets")

        assert result1 == result2
        # Should only have made one actual request
        assert mock_get.call_count == 1

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_list_datasets(self, mock_get):
        """Test list_datasets method"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [{"id": "test-dataset"}],
            "total_count": 1,
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient() as client:
            result = await client.list_datasets(limit=10)

        assert "items" in result
        assert len(result["items"]) == 1

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_dataset(self, mock_get):
        """Test get_dataset method"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "id": "wellbeing-local-authority",
            "title": "Personal well-being",
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient() as client:
            result = await client.get_dataset("wellbeing-local-authority")

        assert result["id"] == "wellbeing-local-authority"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_search_datasets(self, mock_get):
        """Test search_datasets method"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {"id": "house-prices", "title": "House price statistics", "description": "", "keywords": []},
                {"id": "wellbeing", "title": "Wellbeing data", "description": "", "keywords": []},
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient() as client:
            result = await client.search_datasets("house")

        # Should filter to only matching datasets
        assert len(result) == 1
        assert result[0]["id"] == "house-prices"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_list_census_datasets(self, mock_get):
        """Test list_census_datasets method"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {"id": "TS063", "title": "Occupation"},
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient() as client:
            result = await client.list_census_datasets(population_type="UR")

        assert len(result) == 1
        assert result[0]["id"] == "TS063"

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_get_observations(self, mock_get):
        """Test get_observations method"""
        # First call for latest version
        version_response = AsyncMock()
        version_response.status = 200
        version_response.json = AsyncMock(return_value={"version": 4})
        version_response.__aenter__ = AsyncMock(return_value=version_response)
        version_response.__aexit__ = AsyncMock(return_value=None)

        # Second call for observations
        obs_response = AsyncMock()
        obs_response.status = 200
        obs_response.json = AsyncMock(return_value={
            "observation": "7.5",
            "dimensions": {"time": {"label": "2022-23"}},
        })
        obs_response.__aenter__ = AsyncMock(return_value=obs_response)
        obs_response.__aexit__ = AsyncMock(return_value=None)

        mock_get.side_effect = [version_response, obs_response]

        async with ONSAPIClient(enable_cache=False) as client:
            result = await client.get_observations(
                "wellbeing-local-authority",
                dimensions={"geography": "E08000026", "estimate": "average-mean"},
                wildcard_dimension="time",
            )

        assert "observation" in result or "observations" in result


class TestONSAPIClientConvenienceMethods:
    """Tests for convenience methods"""

    @pytest.mark.asyncio
    @patch("aiohttp.ClientSession.get")
    async def test_list_local_authority_datasets(self, mock_get):
        """Test filtering for local authority datasets"""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "items": [
                {"id": "wellbeing-local-authority", "title": "Local Authority Wellbeing", "description": ""},
                {"id": "national-data", "title": "National Statistics", "description": ""},
                {"id": "regional-gdp", "title": "Regional GDP", "description": ""},
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)
        mock_get.return_value = mock_response

        async with ONSAPIClient() as client:
            result = await client.list_local_authority_datasets()

        # Should filter to only LA-related datasets
        ids = [d["id"] for d in result]
        assert "wellbeing-local-authority" in ids
        assert "regional-gdp" in ids
        assert "national-data" not in ids
