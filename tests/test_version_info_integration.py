import json
import pytest
from mcp.server.fastmcp import FastMCP
from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService

@pytest.mark.unit
@pytest.mark.asyncio
async def test_version_info_stdio_roundtrip():
    # Use real FastMCP (stdio) but invoke tool directly (simulating stdio transport registration path)
    mcp = FastMCP("test-stdio-version")
    service = OSDataHubService(OSAPIClient(), mcp)
    out = await service.version_info()
    data = json.loads(out)
    assert data["package"] == "os-mcp"
    assert data["mode"] in {"dev", "prod"}
    assert isinstance(data["version"], str)
