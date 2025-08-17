import json
import pytest
from mcp_service.os_service import OSDataHubService
from api_service.protocols import APIClient  # type: ignore
from mcp_service.protocols import MCPService  # type: ignore


class DummyAPIClient:
    async def cache_collections(self):
        class C:  # minimal
            def __init__(self):
                self.collections = [type("X", (), {"id": "addr-fts-address-1", "title": "Addresses", "description": ""})()]
        return C()
    async def cache_openapi_spec(self):
        class S:  # minimal stub
            def model_dump(self):
                return {}
        return S()
    async def make_request(self, *args, **kwargs):
        if args and args[0] == "COLLECTION_FEATURES":
            # Return minimal geojson-like payload
            return {"features": [{"properties": {"streetName": "Gloucester Street", "postcode": "CV1 3BZ"}}]}
        return {}
    async def close(self):
        pass

class DummyMCPService:
    def tool(self):
        def deco(fn):
            return fn
        return deco
    def run(self):
        pass
    # provide resource & prompt decorators used during registration
    def resource(self, *_args, **_kwargs):  # type: ignore
        def deco(fn):
            return fn
        return deco
    def prompt(self, *_args, **_kwargs):  # type: ignore
        def deco(fn):
            return fn
        return deco

@pytest.mark.asyncio
async def test_lookup_addresses_basic(tmp_path, monkeypatch):
    svc = OSDataHubService(DummyAPIClient(), DummyMCPService())
    # Ensure workflow context loaded
    ctx = await svc.get_workflow_context()
    assert 'CRITICAL_COLLECTION_LIST' in ctx
    result_json = await svc.lookup_addresses("Gloucester Street", postcode="CV1")
    data = json.loads(result_json)
    assert data["status"] == "ok"
    assert data["road"] == "Gloucester Street"
    assert data["address_collection"].startswith("addr")
    assert data["field_used"] is not None
    assert isinstance(data["raw"], dict)
