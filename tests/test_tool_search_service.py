"""Tests for get_tool_search_config tool in OSDataHubService"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestGetToolSearchConfigTool:
    """Tests for get_tool_search_config tool method"""

    @pytest.fixture
    def mock_service(self):
        """Create a mock service with the tool method"""
        from mcp_service.os_service import OSDataHubService

        mock_api = MagicMock()
        mock_api.get_api_key = AsyncMock(return_value="test-key")
        mock_mcp = MagicMock()
        # Make mcp.tool() return a pass-through decorator so methods aren't replaced with MagicMock
        mock_mcp.tool.return_value = lambda f: f

        with patch.dict("os.environ", {"OS_API_KEY": "test-key"}):
            service = OSDataHubService(mock_api, mock_mcp)

        return service

    @pytest.mark.asyncio
    async def test_get_tool_search_config_basic(self, mock_service):
        """Test basic tool search config retrieval"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        assert "always_loaded" in data
        assert "deferred" in data
        assert "counts" in data
        assert "mcp_toolset_config" in data
        assert "system_prompt" in data
        assert "categories" in data

    @pytest.mark.asyncio
    async def test_get_tool_search_config_counts(self, mock_service):
        """Test that counts are accurate"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        counts = data["counts"]
        assert counts["always_loaded"] == len(data["always_loaded"])
        assert counts["deferred"] == len(data["deferred"])
        assert counts["total"] == counts["always_loaded"] + counts["deferred"]

    @pytest.mark.asyncio
    async def test_get_tool_search_config_with_category(self, mock_service):
        """Test filtering by category"""
        result = await mock_service.get_tool_search_config(category="core")
        data = json.loads(result)

        assert "filtered_category" in data
        assert data["filtered_category"] == "core"
        assert "tools" in data

        # Core tools should include hello_world
        assert "hello_world" in data["tools"]

    @pytest.mark.asyncio
    async def test_get_tool_search_config_invalid_category(self, mock_service):
        """Test with invalid category"""
        result = await mock_service.get_tool_search_config(category="invalid_xyz")
        data = json.loads(result)

        assert "error" in data
        assert "invalid" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_get_tool_search_config_mcp_toolset_structure(self, mock_service):
        """Test MCP toolset config structure"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        mcp_config = data["mcp_toolset_config"]
        assert mcp_config["type"] == "mcp_toolset"
        assert "default_config" in mcp_config
        assert mcp_config["default_config"]["defer_loading"] is True
        assert "configs" in mcp_config

    @pytest.mark.asyncio
    async def test_get_tool_search_config_categories_list(self, mock_service):
        """Test categories list contains expected values"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        categories = data["categories"]
        expected = ["core", "workflow", "geography", "statistics", "features"]

        for cat in expected:
            assert cat in categories

    @pytest.mark.asyncio
    async def test_get_tool_search_config_geography_category(self, mock_service):
        """Test geography category contains expected tools"""
        result = await mock_service.get_tool_search_config(category="geography")
        data = json.loads(result)

        assert "tools" in data
        tools = data["tools"]

        assert "select_geographic_area" in tools
        assert "fetch_boundaries" in tools

    @pytest.mark.asyncio
    async def test_get_tool_search_config_statistics_category(self, mock_service):
        """Test statistics category contains expected tools"""
        result = await mock_service.get_tool_search_config(category="statistics")
        data = json.loads(result)

        assert "tools" in data
        tools = data["tools"]

        assert "list_ons_datasets" in tools
        assert "get_statistics" in tools

    @pytest.mark.asyncio
    async def test_get_tool_search_config_system_prompt_content(self, mock_service):
        """Test system prompt contains useful content"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        prompt = data["system_prompt"]
        assert "categories" in prompt.lower()
        assert "tool" in prompt.lower()

    @pytest.mark.asyncio
    async def test_get_tool_search_config_always_loaded_sorted(self, mock_service):
        """Test that always_loaded list is sorted"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        always_loaded = data["always_loaded"]
        assert always_loaded == sorted(always_loaded)

    @pytest.mark.asyncio
    async def test_get_tool_search_config_deferred_sorted(self, mock_service):
        """Test that deferred list is sorted"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        deferred = data["deferred"]
        assert deferred == sorted(deferred)

    @pytest.mark.asyncio
    async def test_get_tool_search_config_tool_includes_itself(self, mock_service):
        """Test that get_tool_search_config is in always_loaded"""
        result = await mock_service.get_tool_search_config()
        data = json.loads(result)

        assert "get_tool_search_config" in data["always_loaded"]

    @pytest.mark.asyncio
    async def test_get_tool_search_config_case_insensitive_category(self, mock_service):
        """Test that category filtering is case-insensitive"""
        result1 = await mock_service.get_tool_search_config(category="CORE")
        result2 = await mock_service.get_tool_search_config(category="core")
        result3 = await mock_service.get_tool_search_config(category="Core")

        data1 = json.loads(result1)
        data2 = json.loads(result2)
        data3 = json.loads(result3)

        # All should return the same tools
        assert data1.get("tools", {}).keys() == data2.get("tools", {}).keys()
        assert data2.get("tools", {}).keys() == data3.get("tools", {}).keys()
