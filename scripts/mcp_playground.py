import asyncio
import json
import os
from mcp_service.os_service import OSDataHubService

class DummyAPIClient:
    async def cache_collections(self):
        class C:
            def __init__(self):
                self.collections = [
                    type("Addr", (), {"id": "addr-fts-address-1", "title": "Addresses", "description": ""})(),
                    type("Bld", (), {"id": "bld-fts-building-4", "title": "Buildings", "description": ""})(),
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
                return {"type": "FeatureCollection", "features": [
                    {"properties": {"mainBuildingId": "B123", "buildinguse": "Residential"}},
                    {"properties": {"mainBuildingId": "B124", "buildinguse": "Retail"}},
                ]}
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

async def main():
    svc = OSDataHubService(DummyAPIClient(), DummyMCPService())
    await svc.os_ngd_init_mapping_workflow()
    print("Type a chat message (or 'exit' to quit):")
    while True:
        user = input("You: ").strip()
        if user.lower() in ("exit", "quit"): break
        chat_json = json.dumps({"messages":[{"role":"user","content":user}]})
        resp = await svc.chat(messages=chat_json)
        print("AI:", resp)
        if "summarise_buildings_by_road" in user.lower():
            # Demo: call the tool directly as well
            summary = await svc.summarise_buildings_by_road("Gloucester Street", postcode="CV1 3BZ")
            print("\n[Tool] summarise_buildings_by_road result:\n", json.dumps(json.loads(summary), indent=2))

if __name__ == "__main__":
    asyncio.run(main())
