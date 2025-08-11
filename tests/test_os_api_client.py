import pytest
from api_service.os_api import OSAPIClient


def test_sanitise_api_key_removes_query_params():
    c = OSAPIClient(api_key="ABC123")
    dirty = "https://example.com/path?key=ABC123&foo=bar"
    cleaned = c._sanitise_api_key(dirty)  # type: ignore[attr-defined]
    assert "key=" not in cleaned
    assert cleaned.startswith("https://example.com/path")


def test_sanitise_response_nested():
    c = OSAPIClient()
    data = {
        "outer": {
            "link": "https://api.service.com/resource?api_key=SECRET",
            "items": [
                {"url": "https://api.service.com/thing?token=ABC"},
                {"plain": "ok"},
            ],
        }
    }
    out = c._sanitise_response(data)  # type: ignore[attr-defined]
    # Tokenised params stripped
    assert "api_key=" not in str(out)
    assert "token=" not in str(out)


def test_filter_latest_collections_versions():
    c = OSAPIClient()
    raw = [
        {"id": "trn-ntwk-roadlink-1", "title": "r1"},
        {"id": "trn-ntwk-roadlink-3", "title": "r3"},
        {"id": "trn-ntwk-roadlink-2", "title": "r2"},
        {"id": "other-collection", "title": "o"},
    ]
    filtered = c._filter_latest_collections(raw)  # type: ignore[attr-defined]
    ids = {col.id for col in filtered}
    # Only highest version of roadlink kept plus standalone
    assert "trn-ntwk-roadlink-3" in ids
    assert "trn-ntwk-roadlink-1" not in ids
    assert "other-collection" in ids


def test_parse_openapi_spec_for_llm_basic():
    c = OSAPIClient()
    spec = {
        "info": {"title": "Test API", "version": "1.0"},
        "servers": [{"url": "https://api.example.com"}],
        "paths": {
            "/collections": {"get": {"parameters": []}},
            "/collections/{collectionId}/items": {
                "get": {
                    "parameters": [
                        {"name": "collectionId", "schema": {"enum": ["c1", "c2"]}},
                        {"name": "bbox-crs", "schema": {"enum": ["CRS84"]}},
                        {"name": "crs", "schema": {"enum": ["CRS84"]}},
                    ]
                }
            },
        },
    }
    parsed = c._parse_openapi_spec_for_llm(spec, ["fallback"])  # type: ignore[attr-defined]
    assert parsed["title"] == "Test API"
    assert set(parsed["collection_ids"]) == {"c1", "c2"}
    assert parsed["supported_crs"]["input"] == ["CRS84"]
    assert parsed["supported_crs"]["output"] == ["CRS84"]
    assert "/collections" in parsed["endpoints"]
