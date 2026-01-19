import json
import pytest
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService
from typing import Any, Dict, List, Optional

class DummyAPI:
    async def initialise(self): return None
    async def close(self): return None
    async def get_api_key(self) -> str: return "k"
    async def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, path_params: Optional[List[str]] = None):
        # minimal responses for collection endpoints
        if endpoint == "COLLECTIONS":
            return {"collections": []}
        return {}
    async def make_request_no_auth(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2): return "{}"
    async def cache_openapi_spec(self):
        from models import OpenAPISpecification
        return OpenAPISpecification(title="t", version="1", base_url="u", endpoints={}, collection_ids=[], supported_crs={}, crs_guide={})
    async def cache_collections(self):
        from models import CollectionsCache
        return CollectionsCache(collections=[], raw_response={})
    async def fetch_collections_queryables(self, collection_ids: List[str]): return {}

@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_guard_blocks_without_context():
    mcp = FastMCP("guard-test")
    svc = OSDataHubService(DummyAPI(), mcp)
    # choose a guarded tool (search_features depends on context in guard list)
    out = await svc.search_features(collection_id="dummy", limit=1)
    data = json.loads(out)
    assert data.get("error_code") == "WORKFLOW_CONTEXT_REQUIRED"
    assert data.get("tool") == "search_features"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_workflow_context_allows_subsequent_calls():
    mcp = FastMCP("guard-test")
    svc = OSDataHubService(DummyAPI(), mcp)
    ctx_raw = await svc.os_ngd_init_mapping_workflow()
    ctx = json.loads(ctx_raw)
    assert ctx.get("status") == "ok"
    # After context established, guarded call should proceed (may still error differently if missing params)
    out = await svc.os_ngd_list_mapping_collections()
    data = json.loads(out)
    assert isinstance(data.get("ids", []), list)
