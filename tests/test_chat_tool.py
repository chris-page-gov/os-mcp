import os
import json
import pytest
from _pytest.monkeypatch import MonkeyPatch  # type: ignore
from typing import Dict, Any, List, Optional

from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService
from api_service.protocols import APIClient  # type: ignore
from models import (
    OpenAPISpecification,
    CollectionsCache,
    CollectionQueryables,
)


class DummyAPI:  # Structural typing; no need to inherit from Protocol
    async def initialise(self) -> None:  # pragma: no cover - not used in tests
        return None

    async def close(self) -> None:  # pragma: no cover - not used
        return None

    async def get_api_key(self) -> str:  # pragma: no cover
        return "dummy"

    async def make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[List[str]] = None,
    ) -> Dict[str, Any]:  # pragma: no cover
        # Minimal shape expected by list_collections if ever called
        return {"collections": []}

    async def make_request_no_auth(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> str:  # pragma: no cover
        return "{}"

    async def cache_openapi_spec(self) -> OpenAPISpecification:  # pragma: no cover
        return OpenAPISpecification(
            title="test",
            version="1.0",
            base_url="https://example.com",
            endpoints={},
            collection_ids=[],
            supported_crs={},
            crs_guide={},
        )

    async def cache_collections(self) -> CollectionsCache:  # pragma: no cover
        return CollectionsCache(collections=[], raw_response={})

    async def fetch_collections_queryables(
        self, collection_ids: List[str]
    ) -> Dict[str, CollectionQueryables]:  # pragma: no cover
        return {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_success(monkeypatch: MonkeyPatch):
    os.environ['OPENAI_API_KEY'] = 'test-key'
    mcp = FastMCP("test")
    service = OSDataHubService(DummyAPI(), mcp)

    from typing import List, Dict, Any

    async def fake_invoke(messages: List[Dict[str, Any]], model: str, api_key: str) -> Dict[str, Any]:  # noqa: D401
        return {"model": model, "output": f"Echo: {messages[-1]['content']}"}

    monkeypatch.setattr(service, "_invoke_llm", fake_invoke)
    out = await service.chat([{"role": "user", "content": "Hello"}])
    data = json.loads(out)
    assert data['output'].startswith("Echo: Hello")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_missing_key():
    os.environ.pop('OPENAI_API_KEY', None)
    mcp = FastMCP("test2")
    service = OSDataHubService(DummyAPI(), mcp)
    out = await service.chat([{"role": "user", "content": "Hi"}])
    data = json.loads(out)
    assert data['error'] == 'MISSING_OPENAI_API_KEY'


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_invalid_json():
    os.environ['OPENAI_API_KEY'] = 'test-key'
    mcp = FastMCP("test3")
    service = OSDataHubService(DummyAPI(), mcp)
    out = await service.chat("not-json")
    data = json.loads(out)
    assert data['error'] == 'INVALID_JSON'


@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_no_workflow_context_required(monkeypatch: MonkeyPatch):
    os.environ['OPENAI_API_KEY'] = 'test-key'
    mcp = FastMCP("test4")
    service = OSDataHubService(DummyAPI(), mcp)

    from typing import List, Dict, Any

    async def fake_invoke(messages: List[Dict[str, Any]], model: str, api_key: str) -> Dict[str, Any]:  # noqa: D401
        return {"model": model, "output": "OK"}

    monkeypatch.setattr(service, "_invoke_llm", fake_invoke)
    out = await service.chat([{"role": "user", "content": "Ping"}])
    data = json.loads(out)
    assert data['output'] == 'OK'
