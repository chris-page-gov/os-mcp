import json
import pytest
from mcp_service.os_service import OSDataHubService

class DummyAPIClient:
    async def cache_collections(self):
        class C:
            def __init__(self):
                self.collections = [
                    type("X", (), {"id": "addr-fts-address-1", "title": "Addresses", "description": ""})(),
                    type("Y", (), {"id": "bld-fts-building-4", "title": "Buildings", "description": ""})(),
                ]
        return C()
    async def cache_openapi_spec(self):
        class S:
            def model_dump(self):
                return {}
        return S()
    async def make_request(self, *args, **kwargs):
        if args and args[0] == "COLLECTION_FEATURES":
            collection_id = kwargs.get("path_params", [None])[0]
            if collection_id == "addr-fts-address-1":
                return {"features": [
                    {"properties": {"streetName": "Gloucester Street", "postcode": "CV1 3BZ", "mainBuildingId": "B123"}},
                    {"properties": {"streetName": "Gloucester Street", "postcode": "CV1 3BZ", "mainBuildingId": "B124"}},
                ]}
            if collection_id == "bld-fts-building-4":
                # Simulate building features
                return {"features": [
                    {"properties": {"mainBuildingId": "B123", "buildinguse": "Residential"}},
                    {"properties": {"mainBuildingId": "B124", "buildinguse": "Retail"}},
                ], "type": "FeatureCollection"}
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
    def resource(self, *_args, **_kwargs):
        def deco(fn):
            return fn
        return deco
    def prompt(self, *_args, **_kwargs):
        def deco(fn):
            return fn
        return deco

@pytest.mark.asyncio
async def test_summarise_buildings_by_road(monkeypatch):
    svc = OSDataHubService(DummyAPIClient(), DummyMCPService())
    await svc.get_workflow_context()
    result_json = await svc.summarise_buildings_by_road("Gloucester Street", postcode="CV1")
    data = json.loads(result_json)
    assert data["status"] == "ok"
    assert data["aggregates"]["total_buildings"] >= 0
    assert data["road"] == "Gloucester Street"
