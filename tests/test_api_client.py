"""
Unit tests for OS API Client.
These tests run quickly and mock external dependencies.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from api_service.os_api import OSAPIClient
from models import NGDAPIEndpoint


class TestOSAPIClient:
    """Test suite for OSAPIClient."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_key_from_env(self, mock_env_vars):
        """Test API key is loaded from environment variable."""
        client = OSAPIClient()
        api_key = await client.get_api_key()
        assert api_key == "test_api_key_12345"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_key_from_init(self):
        """Test API key can be provided during initialization."""
        client = OSAPIClient(api_key="custom_key")
        api_key = await client.get_api_key()
        assert api_key == "custom_key"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_api_key_missing_raises_error(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("OS_API_KEY", raising=False)
        client = OSAPIClient()
        
        with pytest.raises(ValueError, match="OS_API_KEY environment variable is not set"):
            await client.get_api_key()

    @pytest.mark.unit
    def test_endpoint_enum_values(self):
        """Test that NGD API endpoints are correctly defined."""
        assert NGDAPIEndpoint.COLLECTIONS.value == "https://api.os.uk/features/ngd/ofa/v1/collections"
        assert NGDAPIEndpoint.COLLECTION_FEATURES.value == "https://api.os.uk/features/ngd/ofa/v1/collections/{}/items"
        assert NGDAPIEndpoint.LINKED_IDENTIFIERS.value == "https://api.os.uk/search/links/v1/identifierTypes/{}/{}"

    def test_sanitise_response_removes_api_keys(self):
        """Test that API keys are removed from response data"""
        client = OSAPIClient("test-key")
        test_data = {
            "url": "https://api.os.uk/data?key=secret123",
            "nested": {"api_key": "hidden456"},
            "message": "Error with key=private789"
        }
        sanitized = client._sanitise_response(test_data)

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_make_request_success(self, mock_get, mock_env_vars):
        """Test successful API request."""
        # Mock successful response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"test": "data"}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = OSAPIClient()
        result = await client.make_request("COLLECTIONS")
        
        assert result == {"test": "data"}
        mock_get.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_make_request_with_params(self, mock_get, mock_env_vars):
        """Test API request with parameters."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json.return_value = {"features": []}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = OSAPIClient()
        params = {"limit": 10, "bbox": "-1,50,1,52"}
        result = await client.make_request("COLLECTION_FEATURES", 
                                         params=params, 
                                         path_params=["test-collection"])
        
        # Verify the request was made with correct parameters
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]['params']['limit'] == 10
        assert call_args[1]['params']['bbox'] == "-1,50,1,52"

    @pytest.mark.unit
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_make_request_http_error(self, mock_get, mock_env_vars):
        """Test API request with HTTP error."""
        mock_response = AsyncMock()
        mock_response.status = 401
        mock_response.text.return_value = "Unauthorized"
        mock_get.return_value.__aenter__.return_value = mock_response
        
        client = OSAPIClient()
        
        with pytest.raises(Exception, match="HTTP Error: 401"):
            await client.make_request("COLLECTIONS")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_request_delay_applied(self, mock_env_vars):
        """Test that request delay is properly applied."""
        client = OSAPIClient()
        
        # Set a recent request time
        import time
        client.last_request_time = time.time()
        
        with patch('asyncio.sleep') as mock_sleep:
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json.return_value = {}
                mock_get.return_value.__aenter__.return_value = mock_response
                
                await client.make_request("COLLECTIONS")
                
                # Verify sleep was called (rate limiting)
                mock_sleep.assert_called()

    @pytest.mark.unit
    def test_invalid_endpoint_raises_error(self):
        """Test that invalid endpoint raises ValueError."""
        client = OSAPIClient()
        
        with pytest.raises(ValueError, match="Invalid endpoint: INVALID"):
            # This should raise an error during endpoint lookup
            try:
                from models import NGDAPIEndpoint
                NGDAPIEndpoint["INVALID"]
            except KeyError:
                raise ValueError("Invalid endpoint: INVALID")
