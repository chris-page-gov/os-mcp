import json
import pytest
from unittest.mock import AsyncMock
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_features_requires_workflow_context():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    # No workflow_planner set
    out = await service.search_features(collection_id="some-coll")
    data = json.loads(out)
    assert data["error"] == "WORKFLOW CONTEXT REQUIRED"
    assert data["blocked_tool"] == "search_features"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_features_invalid_collection_envelope():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)

    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {"valid-coll": {}}
        detailed_collections_cache: dict[str, dict[str, object]] = {}

    service.workflow_planner = _WF()  # type: ignore[assignment]

    # Mock API call should not be reached for invalid collection, but ensure safety
    api_client.make_request.return_value = {"features": []}

    out = await service.search_features(collection_id="invalid-coll")
    data = json.loads(out)
    assert data["error_code"] == "INVALID_COLLECTION"
    assert data["retry_guidance"]["tool"] == "search_features"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_detailed_collections_invalid_collection():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)

    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {"valid-coll": {}}
        detailed_collections_cache: dict[str, dict[str, object]] = {}

    service.workflow_planner = _WF()  # type: ignore[assignment]

    out = await service.fetch_detailed_collections("invalid-one")
    data = json.loads(out)
    assert data["error_code"] == "INVALID_COLLECTION"
    assert "valid_collections" in data.get("details", {})


@pytest.mark.unit
@pytest.mark.asyncio
async def test_linked_identifiers_filtering():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)

    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {}
        detailed_collections_cache: dict[str, dict[str, object]] = {}

    service.workflow_planner = _WF()  # type: ignore[assignment]

    api_client.make_request.return_value = {
        "results": [
            {"identifier": "1", "featureType": "RoadLink"},
            {"identifier": "2", "featureType": "RoadNode"},
            {"identifier": "3", "featureType": "RoadLink"},
        ]
    }

    out = await service.get_linked_identifiers("TOID", "X", feature_type="RoadLink")
    data = json.loads(out)
    assert len(data["results"]) == 2
    assert all(r["featureType"] == "RoadLink" for r in data["results"])
