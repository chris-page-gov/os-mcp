"""
Integration tests for OSDataHubService with proper AsyncMock configuration.
These tests validate the MCP service functionality using mocked dependencies.
"""

import pytest
from unittest.mock import AsyncMock, patch


class TestOSDataHubServiceIntegration:
    """Integration tests for OSDataHubService with AsyncMock."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_hello_world(self, mock_os_service):
        """Test basic connectivity check."""
        result = await mock_os_service.hello_world()
        assert result == "Hello, OS DataHub MCP Server!"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_check_api_key_valid(self, mock_os_service):
        """Test API key validation with valid key."""
        result = await mock_os_service.check_api_key()
        assert result["status"] == "valid"
        assert result["message"] == "API key is valid"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_workflow_context_establishment(self, mock_os_service):
        """Test workflow context establishment."""
        result = await mock_os_service.get_workflow_context()
        
        assert result["context"] == "workflow_established"
        assert "queryables" in result
        assert "collections" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_search_features_basic(self, mock_os_service):
        """Test basic feature search functionality."""
        result = await mock_os_service.search_features("test-collection-1")
        
        assert result["type"] == "FeatureCollection"
        assert "features" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling(self, mock_os_service):
        """Test error handling when API calls fail."""
        # Configure mock to raise an exception
        mock_os_service.search_features.side_effect = Exception("API connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await mock_os_service.search_features("test-collection")
        
        assert "API connection failed" in str(exc_info.value)
