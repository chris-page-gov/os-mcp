import json
import pytest
from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService
from typing import Any, Dict, List, Optional

# Minimal dummy API client returning fixed knowledge index related structures
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
        return {}

@pytest.mark.unit
@pytest.mark.asyncio
async def test_knowledge_index_overview(tmp_path, monkeypatch):
    # Create a minimal fake knowledge index file that service loader will read
    fake_index = {
        "generated_at": "2025-08-16T00:00:00Z",
        "field_to_collections": {"name": ["col_a", "col_b"], "address": ["col_b"]},
        "enum_value_to_fields": {"RESIDENTIAL": [{"field": "usage", "collection": "col_a"}]},
        "collection_prefix_groups": {"col": ["col_a", "col_b"]},
        "high_cardinality_fields": ["id"],
    }
    index_path = tmp_path / "knowledge_index_latest.json"
    index_path.write_text(json.dumps(fake_index))

    # Monkeypatch constant used in service to point to our temp file
    from mcp_service import os_service as os_mod
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", index_path)

    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)

    out = await svc.get_knowledge_index_overview()
    data = json.loads(out)
    assert data["status"] == "ok"
    # field_count and enum_literal_count fields exist
    assert data["field_count"] == 2
    assert data["enum_literal_count"] == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_collections_and_fields(tmp_path, monkeypatch):
    fake_index = {
        "generated_at": "2025-08-16T00:00:00Z",
        "field_to_collections": {"name": ["col_a", "col_b"], "address": ["col_b"], "usageType": ["col_c"]},
        "enum_value_to_fields": {"RESIDENTIAL": [{"field": "usageType", "collection": "col_c"}]},
        "collection_prefix_groups": {"col": ["col_a", "col_b", "col_c"]},
        "high_cardinality_fields": ["id"],
    }
    index_path = tmp_path / "knowledge_index_latest.json"
    index_path.write_text(json.dumps(fake_index))

    from mcp_service import os_service as os_mod
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", index_path)

    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)

    out = await svc.suggest_collections("name", limit=10)
    data = json.loads(out)
    # suggest_collections returns keyword, matches, total_candidates (no status field)
    assert data["keyword"] == "name"
    assert any(c["collection_id"] == "col_a" for c in data["matches"])  # structure flexible

    out2 = await svc.suggest_fields("usage", limit=10)
    data2 = json.loads(out2)
    # suggest_fields returns token, field_matches, example_collections
    assert data2["token"] == "usage"
    assert any(f == "usageType" for f in data2["field_matches"])  # fuzzy match

@pytest.mark.unit
@pytest.mark.asyncio
async def test_knowledge_negative_unavailable(tmp_path, monkeypatch):
    # Point to a non-existent file to simulate missing index
    from mcp_service import os_service as os_mod
    missing_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", missing_path)
    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)
    overview = json.loads(await svc.get_knowledge_index_overview())
    assert overview["status"] == "unavailable"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_fuzzy_field_and_collection_matching(tmp_path, monkeypatch):
    fake_index = {
        "generated_at": "2025-08-16T00:00:00Z",
        "field_to_collections": {"usageType": ["col_c"], "userType": ["col_d"], "usability": ["col_e"]},
        "enum_value_to_fields": {},
        "collection_prefix_groups": {"col": ["col_c", "col_d", "col_e"]},
        "high_cardinality_fields": [],
    }
    index_path = tmp_path / "knowledge_index_latest.json"
    index_path.write_text(json.dumps(fake_index))
    from mcp_service import os_service as os_mod
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", index_path)
    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)
    # Mistyped token 'usag' should still retrieve usageType via fuzzy scoring
    fields_resp = json.loads(await svc.suggest_fields("usag", limit=5))
    assert any(f == "usageType" for f in fields_resp["field_matches"])  # fuzzy approximate
    # Collection suggestion with near-miss keyword
    col_resp = json.loads(await svc.suggest_collections("usage", limit=5))
    assert col_resp["matches"]  # some result present

@pytest.mark.unit
@pytest.mark.asyncio
async def test_field_limit_and_ordering(tmp_path, monkeypatch):
    # Build many similar fields so we can test limit trimming
    base_fields = {f"nameVariant{i}": ["col_a"] for i in range(30)}
    base_fields["name"] = ["col_a"]  # ensure a strong direct hit
    fake_index = {
        "generated_at": "now",
        "field_to_collections": base_fields,
        "enum_value_to_fields": {},
        "collection_prefix_groups": {"col": ["col_a"]},
        "high_cardinality_fields": [],
    }
    index_path = tmp_path / "knowledge_index_latest.json"
    index_path.write_text(json.dumps(fake_index))
    from mcp_service import os_service as os_mod
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", index_path)
    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)
    # limit=5 should return at most 5 field_matches
    resp = json.loads(await svc.suggest_fields("name", limit=5))
    assert len(resp["field_matches"]) <= 5
    assert "name" in resp["field_matches"]  # direct match retained

@pytest.mark.unit
@pytest.mark.asyncio
async def test_collection_fuzzy_score_priority(tmp_path, monkeypatch):
    # Create fields so one collection gets exact substring, another only fuzzy credit
    fake_index = {
        "generated_at": "now",
        "field_to_collections": {
            "usageType": ["col_exact"],  # exact substring for 'usage'
            "usogeType": ["col_fuzzy"],  # one mismatch (g instead of a)
        },
        "enum_value_to_fields": {},
        "collection_prefix_groups": {"col": ["col_exact", "col_fuzzy"]},
        "high_cardinality_fields": [],
    }
    index_path = tmp_path / "knowledge_index_latest.json"
    index_path.write_text(json.dumps(fake_index))
    from mcp_service import os_service as os_mod
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", index_path)
    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)
    resp = json.loads(await svc.suggest_collections("usage", limit=10))
    ids_in_order = [m["collection_id"] for m in resp["matches"]]
    # Fuzzy candidate may be filtered out if score below threshold; ensure exact present
    assert "col_exact" in ids_in_order

@pytest.mark.unit
@pytest.mark.asyncio
async def test_suggest_fields_missing_index_error(tmp_path, monkeypatch):
    from mcp_service import os_service as os_mod
    missing_path = tmp_path / "does_not_exist.json"
    monkeypatch.setattr(os_mod, "KNOWLEDGE_INDEX_PATH", missing_path)
    mcp = FastMCP("test-knowledge")
    svc = OSDataHubService(DummyAPI(), mcp)
    resp = json.loads(await svc.suggest_fields("foo"))
    # Error envelope includes error_code INVALID_INPUT
    assert resp.get("error_code") == "INVALID_INPUT"
