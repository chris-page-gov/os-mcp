import json
import pytest
from unittest.mock import AsyncMock
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_features_invalid_filter_too_long():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    # Provide workflow context shortcut
    class _WF:  # minimal planner with collections info
        basic_collections_info: dict[str, dict[str, object]] = {"col1": {}}
    service.workflow_planner = _WF()  # type: ignore
    long_filter = "a" * 1001
    out = await service.search_features("col1", filter=long_filter)
    data = json.loads(out)
    assert data["error_code"] == "INVALID_INPUT"
    assert "Filter too long" in data["message"]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_features_invalid_collection():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {"valid": {}}
    service.workflow_planner = _WF()  # type: ignore
    out = await service.search_features("invalid", query_attr="usrn", query_attr_value="123")
    data = json.loads(out)
    assert data["error_code"] == "INVALID_COLLECTION"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_feature_upstream_error():
    api_client = AsyncMock()
    api_client.make_request.side_effect = Exception("boom")
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    # Provide minimal planner to bypass workflow gate
    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {"c": {}}
    service.workflow_planner = _WF()  # type: ignore
    out = await service.get_feature("c","f")
    data = json.loads(out)
    # get_feature wraps upstream exceptions in UPSTREAM_ERROR envelope
    assert data.get("error_code") == "UPSTREAM_ERROR"
    assert "boom" in data.get("message","")

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bulk_features_mixed_modes():
    api_client = AsyncMock()
    # emulate get_feature path
    async def fake_get_feature(collection_id: str, feature_id: str, crs: str | None = None):  # pragma: no cover - simple
        return json.dumps({"id": feature_id})
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    service.get_feature = fake_get_feature  # type: ignore
    service.search_features = AsyncMock(return_value=json.dumps({"features": [{"id":"x"}]}))  # type: ignore
    # Provide planner so search_features path isn't blocked
    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {"col": {}}
    service.workflow_planner = _WF()  # type: ignore
    out = await service.get_bulk_features("col", ["A","B"], query_by_attr="usrn")
    data = json.loads(out)
    assert len(data["results"]) == 2

@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_detailed_collections_requires_planner():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    out = await service.fetch_detailed_collections("x")
    data = json.loads(out)
    # Initially blocked by workflow context guard wrapper (generic envelope)
    assert data.get("details", {}).get("blocked_tool") == "fetch_detailed_collections"
