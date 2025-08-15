import json
import pytest
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService

# Comprehensive stub covering all OS API endpoints used by service tools
class FullStubAPI:
    def __init__(self):
        self._collections = [
            {"id": "col-1", "title": "Collection One", "description": "First collection"},
            {"id": "col-2", "title": "Collection Two", "description": "Second collection"},
        ]
        self._features: dict[str, list[dict[str, Any]]] = {
            "col-1": [
                {"id": "f1", "type": "Feature", "properties": {"name": "Alpha", "code": 1}, "geometry": None},
                {"id": "f2", "type": "Feature", "properties": {"name": "Beta", "code": 2}, "geometry": None},
            ],
            "col-2": [
                {"id": "g1", "type": "Feature", "properties": {"name": "Gamma", "code": 3}, "geometry": None},
            ],
        }
        self._linked: List[Dict[str, Any]] = [
            {"identifier": "X1", "featureType": "Road", "linkedIdentifier": "L1", "relation": "sameAs"},
            {"identifier": "X2", "featureType": "Building", "linkedIdentifier": "L2", "relation": "related"},
        ]

    # --- API client protocol methods ---
    async def initialise(self) -> None:  # pragma: no cover
        return None
    async def close(self) -> None:  # pragma: no cover
        return None
    async def get_api_key(self) -> str:  # pragma: no cover
        return "stub-key"

    async def make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        if endpoint == "COLLECTIONS":
            return {"collections": self._collections}
        elif endpoint == "COLLECTION_INFO":
            assert path_params and len(path_params) == 1
            cid = path_params[0]
            for c in self._collections:
                if c["id"] == cid:
                    return c
            raise ValueError("Collection not found")
        elif endpoint == "COLLECTION_QUERYABLES":
            assert path_params and len(path_params) == 1
            cid = path_params[0]
            return {
                "id": cid,
                "properties": {"name": {"type": "string"}, "code": {"type": "integer"}},
                "enum_queryables": {"name": ["Alpha", "Beta", "Gamma"]},
            }
        elif endpoint == "COLLECTION_FEATURE_BY_ID":
            assert path_params and len(path_params) == 2
            cid, fid = path_params
            for f in self._features.get(cid, []):
                if f["id"] == fid:
                    return f
            raise ValueError("Feature not found")
        elif endpoint == "COLLECTION_FEATURES":
            assert path_params and len(path_params) == 1
            cid = path_params[0]
            feats = list(self._features.get(cid, []))
            filt = (params or {}).get("filter") if params else None
            if isinstance(filt, str):
                import re as _re
                m = _re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*'([^']*)'\s*", filt)
                if m:
                    field, value = m.group(1), m.group(2)
                    feats = [f for f in feats if str(f.get("properties", {}).get(field)) == value]
            limit = int((params or {}).get("limit", 10))
            offset = int((params or {}).get("offset", 0))
            feats_page = feats[offset: offset + limit]
            return {"type": "FeatureCollection", "features": feats_page, "numberMatched": len(feats), "numberReturned": len(feats_page)}
        elif endpoint == "LINKED_IDENTIFIERS":
            assert path_params and len(path_params) == 2
            return {"results": self._linked}
        else:
            raise ValueError(f"Unexpected endpoint {endpoint}")

    async def make_request_no_auth(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2) -> str:  # pragma: no cover
        return "{}"

    async def cache_openapi_spec(self):  # pragma: no cover
        from models import OpenAPISpecification
        return OpenAPISpecification(
            title="stub", version="1", base_url="https://example.com", endpoints={}, collection_ids=[c["id"] for c in self._collections], supported_crs={}, crs_guide={}
        )

    async def cache_collections(self):  # pragma: no cover
        from models import CollectionsCache, Collection
        col_models = [Collection(id=c["id"], title=c["title"], description=c.get("description", "")) for c in self._collections]
        return CollectionsCache(collections=col_models, raw_response={})

    async def fetch_collections_queryables(self, collection_ids: List[str]):  # pragma: no cover
        from models import CollectionQueryables
        out: Dict[str, CollectionQueryables] = {}
        for cid in collection_ids:
            out[cid] = CollectionQueryables(
                id=cid,
                title=f"Title {cid}",
                description=f"Desc {cid}",
                all_queryables={"name": {"type": "string"}, "code": {"type": "integer"}},
                enum_queryables={"name": ["Alpha", "Beta", "Gamma"]},
                has_enum_filters=True,
                total_queryables=2,
                enum_count=1,
            )
        return out

# --- Tests ---

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_single_collection_matches_api():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    api_col = await stub.make_request("COLLECTION_INFO", path_params=["col-1"])
    out = await service.get_single_collection("col-1")
    svc_col = json.loads(out)
    assert svc_col == api_col

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_single_collection_queryables_matches_api():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    api_q = await stub.make_request("COLLECTION_QUERYABLES", path_params=["col-1"])
    out = await service.get_single_collection_queryables("col-1")
    svc_q = json.loads(out)
    assert svc_q == api_q

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_linked_identifiers_matches_api():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    api_li = await stub.make_request("LINKED_IDENTIFIERS", path_params=["TOID", "X1"])
    out = await service.get_linked_identifiers("TOID", "X1")
    svc_li = json.loads(out)
    assert svc_li == api_li
    # Filtered version
    out_filtered = await service.get_linked_identifiers("TOID", "X1", feature_type="Road")
    filtered = json.loads(out_filtered)
    assert all(item.get("featureType") == "Road" for item in filtered.get("results", []))

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bulk_features_matches_api():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    out = await service.get_bulk_features("col-1", ["f1", "f2"])
    svc_bulk = json.loads(out)
    assert len(svc_bulk.get("results", [])) == 2
    # Verify each element equals underlying get_feature
    for idx, fid in enumerate(["f1", "f2"]):
        api_feat = await stub.make_request("COLLECTION_FEATURE_BY_ID", path_params=["col-1", fid])
        assert svc_bulk["results"][idx] == api_feat  # results elements are already dicts

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bulk_features_query_attr_matches_api():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    # Query by attribute code -> features with code 1 or 2 individually
    out = await service.get_bulk_features("col-1", ["1", "2"], query_by_attr="code")
    svc_bulk = json.loads(out)
    assert len(svc_bulk.get("results", [])) == 2
    # Each result is parsed search_features output; check id matches expectation
    returned_ids = [r.get("features", [{}])[0].get("id") for r in svc_bulk["results"]]
    assert set(returned_ids) == {"f1", "f2"}

@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_bulk_linked_features_matches_api():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    out = await service.get_bulk_linked_features("TOID", ["X1", "X2"])
    svc_bulk = json.loads(out)
    assert len(svc_bulk.get("results", [])) == 2
    # Each element is a dict containing results list
    assert all("results" in element for element in svc_bulk.get("results", []))

@pytest.mark.unit
@pytest.mark.asyncio
async def test_fetch_detailed_collections_matches_api_queryables():
    stub = FullStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.get_workflow_context()
    out = await service.fetch_detailed_collections("col-1")
    svc_detail = json.loads(out)
    detailed = svc_detail.get("detailed_collections", {}).get("col-1")
    assert detailed is not None
    assert "all_queryables" in detailed and "enum_queryables" in detailed
    assert detailed.get("enum_count") == 1
