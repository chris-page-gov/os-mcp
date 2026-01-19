import json
from typing import Any, Dict, List, Callable, Awaitable
import pytest
from mcp_service.os_service import OSDataHubService


class DummyCollection:
    def __init__(self) -> None:
        self.id = "addr-fts-address-1"
        self.title = "Addresses"
        self.description = ""


class DummyCollectionsCache:
    def __init__(self) -> None:
        self.collections: List[DummyCollection] = [DummyCollection()]


class DummyOpenAPISpec:
    def model_dump(self) -> Dict[str, Any]:  # minimal stub
        return {}


class DummyQueryables:
    def __init__(self, cid: str) -> None:
        self.id = cid
        self.title = cid
        self.description = ""
        self.all_queryables: Dict[str, Any] = {}
        self.enum_queryables: Dict[str, List[str]] = {}
        self.has_enum_filters = False
        self.total_queryables = 0
        self.enum_count = 0


class DummyAPIClient:
    async def initialise(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def get_api_key(self) -> str:
        return "dummy"

    async def make_request(self, endpoint: str, params: Dict[str, Any] | None = None, path_params: List[str] | None = None) -> Dict[str, Any]:  # type: ignore[override]
        if endpoint == "COLLECTIONS":
            return {"collections": [{"id": "addr-fts-address-1", "title": "Addresses", "description": ""}]}
        if endpoint == "COLLECTION_FEATURES":
            return {"features": []}
        return {}

    async def make_request_no_auth(self, url: str, params: Dict[str, Any] | None = None, max_retries: int = 2) -> str:  # type: ignore[override]
        return "{}"

    async def cache_openapi_spec(self) -> DummyOpenAPISpec:  # type: ignore[override]
        return DummyOpenAPISpec()

    async def cache_collections(self) -> DummyCollectionsCache:  # type: ignore[override]
        return DummyCollectionsCache()

    async def fetch_collections_queryables(self, collection_ids: List[str]) -> Dict[str, DummyQueryables]:  # type: ignore[override]
        return {cid: DummyQueryables(cid) for cid in collection_ids}
    # remove old stub methods (replaced above)


class DummyMCPService:
    def tool(
        self, *_args: Any, **_kwargs: Any
    ) -> Callable[[Callable[..., Awaitable[Any]]], Callable[..., Awaitable[Any]]]:
        def deco(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            return fn
        return deco

    def run(self) -> None:  # pragma: no cover - not used
        return None

    def resource(self, *_args: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # type: ignore
        def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn
        return deco

    def prompt(self, *_args: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # type: ignore
        def deco(fn: Callable[..., Any]) -> Callable[..., Any]:
            return fn
        return deco


@pytest.mark.asyncio
async def test_diagnose_address_fields_basic() -> None:
    svc = OSDataHubService(DummyAPIClient(), DummyMCPService())
    await svc.os_ngd_init_mapping_workflow()
    result = await svc.diagnose_address_fields("Gloucester Street")
    data: Dict[str, Any] = json.loads(result)
    assert data["status"] == "ok"
    assert isinstance(data.get("address_collection"), str) and data["address_collection"].startswith("addr")
    assert isinstance(data.get("candidate_fields"), list) and len(data["candidate_fields"]) > 0
    assert isinstance(data.get("attempts"), list) and len(data["attempts"]) > 0
    first_attempt: Dict[str, Any] = data["attempts"][0]
    assert "field" in first_attempt and "value_variant" in first_attempt
    assert (
        "feature_count" in first_attempt
        or "upstream_error_code" in first_attempt
        or "exception" in first_attempt
    )
