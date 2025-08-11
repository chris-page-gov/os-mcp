import json
import pytest
from unittest.mock import AsyncMock
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_routing_data_success_minimal():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    # Stub routing service methods
    service.routing_service.build_routing_network = AsyncMock(return_value={"status":"success"})  # type: ignore
    service.routing_service.get_flat_nodes = lambda : {"nodes":[{"id":"n1"}]}  # type: ignore
    service.routing_service.get_flat_edges = lambda : {"edges":[{"id":"e1"}]}  # type: ignore
    service.routing_service.get_network_info = lambda : {"network":{"count":1}}  # type: ignore
    # Provide planner to satisfy workflow context requirement
    class _WF:
        basic_collections_info: dict[str, dict[str, object]] = {}
    service.workflow_planner = _WF()  # type: ignore
    out = await service.get_routing_data(bbox="0,0,1,1", limit=10)
    data = json.loads(out)
    assert data["status"] == "success"
    assert data["nodes"] and data["edges"]

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_routing_data_build_failure_short_circuit():
    api_client = AsyncMock()
    mcp = FastMCP("os-ngd-api")
    service = OSDataHubService(api_client, mcp)
    service.routing_service.build_routing_network = AsyncMock(return_value={"status":"error","detail":"x"})  # type: ignore
    # Without planner, call will be blocked (workflow context required)
    out = await service.get_routing_data()
    data = json.loads(out)
    assert data.get("blocked_tool") == "get_routing_data"
