"""Tests for standardized error envelope in tool responses."""
import json
import pytest
from unittest.mock import AsyncMock
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_envelope_unmatched_quotes():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)

    class _WF:
        basic_collections_info = {"test-coll": {}}
        detailed_collections_cache = {}

    service.workflow_planner = _WF()  # type: ignore[attr-defined]

    result_json = await service.search_features(
        collection_id="test-coll", filter="name = 'Cinema"
    )
    data = json.loads(result_json)
    assert "error" in data
    assert "retry_guidance" in data
    assert data["retry_guidance"]["tool"] == "search_features"
    assert "MANDATORY_INSTRUCTION 1" in data["retry_guidance"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_envelope_filter_too_long():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)

    class _WF:
        basic_collections_info = {"test-coll": {}}
        detailed_collections_cache = {}

    service.workflow_planner = _WF()  # type: ignore[attr-defined]

    long_filter = "a" * 1001
    result_json = await service.search_features(
        collection_id="test-coll", filter=long_filter
    )
    data = json.loads(result_json)
    assert data["error"].startswith("Invalid input: Filter too long")
    assert data["retry_guidance"]["tool"] == "search_features"
