import json
import pytest
from unittest.mock import AsyncMock
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService


class _WF:  # minimal workflow planner stub
    def __init__(self, collections: list[str]):
        self.basic_collections_info = {c: {} for c in collections}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_features_dangerous_pattern_block():
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    svc.workflow_planner = _WF(["col1"])  # bypass guard
    out = await svc.search_features("col1", filter="SELECT * FROM table")
    data = json.loads(out)
    assert data.get("error_code") == "INVALID_INPUT"
    assert "Invalid input" in data.get("message", "")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_features_unmatched_quotes():
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    svc.workflow_planner = _WF(["col1"])  # bypass guard
    out = await svc.search_features("col1", filter="name = 'abc")
    data = json.loads(out)
    assert data.get("error_code") == "INVALID_INPUT"
    assert "Unmatched quotes" in data.get("message", "")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bulk_linked_features_exception_path():
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    # monkeypatch underlying method to raise so gather propagates
    async def boom(*_args, **_kwargs):  # pragma: no cover - simple
        raise RuntimeError("explode")
    svc.get_linked_identifiers = boom  # type: ignore
    svc.workflow_planner = _WF([])
    out = await svc.get_bulk_linked_features("TOID", ["1","2"])  # will catch exception
    data = json.loads(out)
    assert data.get("error_code") == "UPSTREAM_ERROR"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_invalid_payload_dict():
    import os
    os.environ['OPENAI_API_KEY'] = 'k'
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    # dict missing 'messages' key
    out = await svc.chat({"foo": "bar"})
    data = json.loads(out)
    assert data.get("error") == "INVALID_PAYLOAD"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_invalid_format_list():
    import os
    os.environ['OPENAI_API_KEY'] = 'k'
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    out = await svc.chat([{"role": "user", "content": "hi"}, "not-dict"])  # second element invalid
    data = json.loads(out)
    assert data.get("error") == "INVALID_FORMAT"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_detailed_collections_invalid_id():
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    # provide planner with only valid1
    svc.workflow_planner = type("WF", (), {"basic_collections_info": {"valid1": {}}, "get_detailed_context": lambda self, cols: {"available_collections": {}}})()  # type: ignore
    out = await svc.fetch_detailed_collections("missing")
    data = json.loads(out)
    assert data.get("error_code") == "INVALID_COLLECTION"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_routing_data_early_return_on_build_error():
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    svc.workflow_planner = _WF([])
    # force build failure -> function should early return without nodes/edges
    async def fail_build(_bbox, _limit):
        return {"status": "error", "detail": "fail"}
    svc.routing_service.build_routing_network = fail_build  # type: ignore
    out = await svc.get_routing_data()
    data = json.loads(out)
    assert data.get("build_status", {}).get("status") == "error"
    assert "nodes" not in data and "edges" not in data


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bulk_features_exception_path():
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    svc.workflow_planner = _WF(["col"])  # collection for search path if needed
    async def raise_get_feature(*args, **kwargs):  # pragma: no cover - simple
        raise RuntimeError("boom")
    svc.get_feature = raise_get_feature  # type: ignore
    out = await svc.get_bulk_features("col", ["a","b"])  # triggers exception gather
    data = json.loads(out)
    assert data.get("error_code") == "UPSTREAM_ERROR"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_collections_missing_index_error(tmp_path, monkeypatch):
    from mcp_service import os_service as os_mod
    missing_path = tmp_path / "missing.json"
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", missing_path)
    api_client = AsyncMock()
    mcp = FastMCP("addl")
    svc = OSDataHubService(api_client, mcp)
    resp = json.loads(await svc.suggest_collections("foo"))
    assert resp.get("error_code") == "INVALID_INPUT"
