import json
import pytest
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService

# Re‑use DummyAPI pattern from chat tests (simplified inline to avoid import coupling)
from typing import Any, Dict, List, Optional
class DummyAPI:
    async def initialise(self) -> None:  # type: ignore[override]
        return None
    async def close(self) -> None:  # type: ignore[override]
        return None
    async def get_api_key(self) -> str:  # type: ignore[override]
        return "dummy"
    async def make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None, path_params: Optional[List[str]] = None) -> Dict[str, Any]:  # type: ignore[override]
        return {"collections": []}
    async def make_request_no_auth(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2) -> str:  # type: ignore[override]
        return "{}"
    async def cache_openapi_spec(self):  # type: ignore[override]
        from models import OpenAPISpecification
        return OpenAPISpecification(title="t", version="1", base_url="u", endpoints={}, collection_ids=[], supported_crs={}, crs_guide={})
    async def cache_collections(self):  # type: ignore[override]
        from models import CollectionsCache
        return CollectionsCache(collections=[], raw_response={})
    async def fetch_collections_queryables(self, collection_ids: List[str]):  # type: ignore[override]
        from models import CollectionQueryables
        return {}

@pytest.mark.unit
@pytest.mark.asyncio
async def test_version_info_basic():
    mcp = FastMCP("test-version")
    svc = OSDataHubService(DummyAPI(), mcp)
    out = await svc.version_info()
    data = json.loads(out)
    assert data["package"] == "os-mcp"
    assert "version" in data and isinstance(data["version"], str)
    assert data["mode"] in {"dev", "prod"}
