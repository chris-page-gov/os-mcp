import asyncio
from typing import Any, Dict, List

import pytest

from api_service.os_api import OSAPIClient
from models import Collection, CollectionsCache, CollectionQueryables, OpenAPISpecification


@pytest.mark.asyncio
async def test_cache_openapi_spec_caches(monkeypatch: Any):
    """cache_openapi_spec should call underlying retrieval only once."""
    client = OSAPIClient(api_key="DUMMY")

    spec_calls: List[Dict[str, Any]] = []

    async def fake_make_request(endpoint, **kwargs):  # type: ignore[override]
        spec_calls.append({"endpoint": endpoint})
        assert endpoint == "OPENAPI_SPEC"
        return {
            "info": {"title": "Fake Spec", "version": "9.9"},
            "servers": [{"url": "https://api.example.com"}],
            "paths": {},
        }

    # Provide a minimal collections cache so _get_open_api_spec can parse collection ids
    async def fake_cache_collections():  # type: ignore[override]
        return CollectionsCache(
            collections=[
                Collection(id="abc-1", title="A1"),
                Collection(id="road-link-2", title="Road Link v2"),
            ],
            raw_response={"collections": []},
        )

    monkeypatch.setattr(client, "make_request", fake_make_request)  # type: ignore[arg-type]
    monkeypatch.setattr(client, "cache_collections", fake_cache_collections)  # type: ignore[arg-type]

    spec1 = await client.cache_openapi_spec()
    spec2 = await client.cache_openapi_spec()

    assert isinstance(spec1, OpenAPISpecification)
    assert spec1 is spec2  # cached instance
    assert len(spec_calls) == 1  # only called once
    assert spec1.title == "Fake Spec"


@pytest.mark.asyncio
async def test_cache_collections_filters_versions(monkeypatch: Any):
    """cache_collections should retain only highest version per base id."""
    client = OSAPIClient(api_key="X")

    async def fake_make_request(endpoint, **kwargs):  # type: ignore[override]
        assert endpoint == "COLLECTIONS"
        return {
            "collections": [
                {"id": "trn-ntwk-roadlink-1", "title": "r1"},
                {"id": "trn-ntwk-roadlink-3", "title": "r3"},
                {"id": "trn-ntwk-roadlink-2", "title": "r2"},
                {"id": "standalone", "title": "s"},
            ]
        }

    monkeypatch.setattr(client, "make_request", fake_make_request)  # type: ignore[arg-type]

    cache = await client.cache_collections()
    ids = {c.id for c in cache.collections}
    assert "trn-ntwk-roadlink-3" in ids
    assert "trn-ntwk-roadlink-1" not in ids
    assert "standalone" in ids


@pytest.mark.asyncio
async def test_get_collections_error_sanitises(monkeypatch: Any):
    """_get_collections should sanitise API key in error messages."""
    client = OSAPIClient(api_key="SECRET123")

    async def fake_make_request(endpoint, **kwargs):  # type: ignore[override]
        raise ValueError("HTTP Error: 401 - https://api.os.uk/path?key=SECRET123")

    monkeypatch.setattr(client, "make_request", fake_make_request)  # type: ignore[arg-type]

    with pytest.raises(ValueError) as exc:
        await client._get_collections()  # type: ignore[attr-defined]

    msg = str(exc.value)
    assert "SECRET123" not in msg  # key removed
    assert "Failed to get collections" in msg


@pytest.mark.asyncio
async def test_fetch_collections_queryables_enums(monkeypatch: Any):
    """fetch_collections_queryables processes enum and non-enum properties."""
    client = OSAPIClient(api_key="KEY")

    collections = CollectionsCache(
        collections=[
            Collection(id="roads", title="Roads"),
            Collection(id="buildings", title="Buildings"),
        ],
        raw_response={"collections": []},
    )

    async def fake_cache_collections():  # type: ignore[override]
        return collections

    async def fake_make_request(endpoint, path_params=None, **kwargs):  # type: ignore[override]
        collection_id: str = (path_params or ["roads"])[0]
        return {
            "properties": {
                "status": {
                    "type": ["string", "null"],
                    "enumeration": True,
                    "enum": ["open", "closed"],
                    "maxLength": 12,
                },
                "length_m": {"type": "number", "minimum": 0},
            }
        }

    monkeypatch.setattr(client, "cache_collections", fake_cache_collections)  # type: ignore[arg-type]
    monkeypatch.setattr(client, "make_request", fake_make_request)  # type: ignore[arg-type]

    result = await client.fetch_collections_queryables(["roads", "buildings"])
    assert set(result.keys()) == {"roads", "buildings"}
    for q in result.values():
        assert isinstance(q, CollectionQueryables)
        assert q.has_enum_filters is True
        assert "status" in q.enum_queryables
        assert q.enum_queryables["status"]["values"] == ["open", "closed"]
        assert q.all_queryables["status"]["nullable"] is True
        assert q.all_queryables["length_m"]["type"] == "number"


@pytest.mark.asyncio
async def test_close_resets_caches(monkeypatch: Any):
    """close should clear cached spec and collections."""
    client = OSAPIClient(api_key="KEY")

    # Prepare fake caches
    client._cached_openapi_spec = OpenAPISpecification(
        title="T", version="1", base_url="u", endpoints={}, collection_ids=[], supported_crs={}, crs_guide={}
    )
    client._cached_collections = CollectionsCache(collections=[], raw_response={})

    # Fake session with async close
    class DummySession:
        async def close(self):
            await asyncio.sleep(0)

    client.session = DummySession()

    await client.close()
    assert client._cached_openapi_spec is None
    assert client._cached_collections is None
