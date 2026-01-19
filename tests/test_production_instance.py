import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import venv
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from mcp.server.fastmcp import FastMCP
from mcp_service.os_service import OSDataHubService


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.mark.integration
@pytest.mark.slow
def test_production_health_and_version():
    """Build wheel, install into isolated venv, run HTTP server, verify enriched /health reports prod mode & version."""
    if os.environ.get("OS_MCP_RUN_SLOW") != "1":
        pytest.skip("Set OS_MCP_RUN_SLOW=1 to run slow production build tests")
    try:
        import build  # type: ignore  # noqa: F401
    except ImportError:  # pragma: no cover
        pytest.skip("python-build not installed; skipping production integration test")

    repo_root = Path(__file__).resolve().parents[1]
    dist_tmp = Path(tempfile.mkdtemp(prefix="os_mcp_dist_"))

    # Build wheel
    subprocess.run([sys.executable, "-m", "build", "--wheel", "--outdir", str(dist_tmp)], check=True)
    wheels = list(dist_tmp.glob("os_mcp-*.whl"))
    assert wheels, "Wheel build failed (no wheel found)"
    wheel_path = wheels[0]
    m = re.match(r"os_mcp-([0-9A-Za-z_.+-]+)-", wheel_path.name)
    assert m, "Could not parse version from wheel filename"
    built_version = m.group(1)

    # Create venv & install
    venv_dir = Path(tempfile.mkdtemp(prefix="os_mcp_venv_"))
    venv.EnvBuilder(with_pip=True).create(str(venv_dir))
    py_bin = venv_dir / ("Scripts" if os.name == "nt" else "bin") / "python"
    subprocess.run([str(py_bin), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(py_bin), "-m", "pip", "install", str(wheel_path)], check=True)

    port = _free_port()
    env = os.environ.copy()
    env.update({
        "OS_API_KEY": env.get("OS_API_KEY", "dummy-key"),
        "BEARER_TOKENS": "test-token",
    })
    proc = subprocess.Popen(
        [str(py_bin), "-m", "server", "--transport", "streamable-http", "--host", "127.0.0.1", "--port", str(port)],
        cwd=str(repo_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        deadline = time.time() + 25
        health_json: Dict[str, Any] | None = None
        import urllib.request
        while time.time() < deadline:
            if proc.poll() is not None:
                stdout, stderr = proc.communicate(timeout=1)
                raise AssertionError(f"Server exited early. stdout=\n{stdout}\nstderr=\n{stderr}")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as resp:  # type: ignore
                    payload = resp.read().decode()
                    health_json = json.loads(payload)
                    break
            except Exception:  # pragma: no cover - retry until deadline
                time.sleep(0.5)
        assert health_json is not None, "Timed out waiting for /health"
        assert health_json.get("status") == "ok"
        assert health_json.get("version") == built_version
        assert health_json.get("mode") == "prod"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            proc.kill()


class StubAPI:
    """Deterministic stub to compare MCP tool outputs to underlying API data."""

    def __init__(self):
        self._collections = [
            {"id": "col-1", "title": "Collection One", "description": "d1"},
            {"id": "col-2", "title": "Collection Two", "description": "d2"},
        ]

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
        raise ValueError(f"Unexpected endpoint {endpoint}")

    async def make_request_no_auth(self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2) -> str:  # pragma: no cover
        return "{}"

    async def cache_openapi_spec(self) -> Any:  # pragma: no cover
        from models import OpenAPISpecification
        return OpenAPISpecification(
            title="stub", version="1", base_url="https://example.com", endpoints={}, collection_ids=[c["id"] for c in self._collections], supported_crs={}, crs_guide={}
        )

    async def cache_collections(self) -> Any:  # pragma: no cover
        from models import CollectionsCache
        return CollectionsCache(collections=[], raw_response={})

    async def fetch_collections_queryables(self, collection_ids: List[str]) -> Dict[str, Any]:  # pragma: no cover
        return {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mcp_os_ngd_list_mapping_collections_matches_api():
    stub = StubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    api_data = await stub.make_request("COLLECTIONS")
    out = await service.os_ngd_list_mapping_collections()
    mcp_data = json.loads(out)
    assert "ids" in mcp_data
    expected = sorted([c["id"] for c in api_data["collections"]])
    assert sorted(mcp_data["ids"]) == expected


class RichStubAPI:
    """Richer deterministic stub supporting collection listing, feature retrieval and filtered searches."""

    def __init__(self):
        self._collections = [
            {"id": "col-1", "title": "Collection One", "description": "d1"},
        ]
        # Simple feature set with attributes we can filter on
        self._features: dict[str, list[dict[str, Any]]] = {
            "col-1": [
                {"id": "f1", "type": "Feature", "properties": {"name": "Alpha", "category": "A"}, "geometry": None},
                {"id": "f2", "type": "Feature", "properties": {"name": "Beta", "category": "B"}, "geometry": None},
                {"id": "f3", "type": "Feature", "properties": {"name": "Gamma", "category": "A"}, "geometry": None},
            ]
        }

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
        if endpoint == "COLLECTION_FEATURE_BY_ID":
            assert path_params and len(path_params) == 2
            collection_id, feature_id = path_params
            for feat in self._features.get(collection_id, []):
                if feat["id"] == feature_id:
                    return feat
            raise ValueError("Feature not found")
        if endpoint == "COLLECTION_FEATURES":
            assert path_params and len(path_params) == 1
            collection_id = path_params[0]
            feats = list(self._features.get(collection_id, []))
            filt = (params or {}).get("filter") if params else None
            if isinstance(filt, str):
                # Very small subset parser: field = 'value'
                import re as _re
                m = _re.match(r"\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*'([^']*)'\s*", filt)
                if m:
                    field, value = m.group(1), m.group(2)
                    feats = [f for f in feats if f.get("properties", {}).get(field) == value]
            limit = int((params or {}).get("limit", 10))
            offset = int((params or {}).get("offset", 0))
            feats_page = feats[offset: offset + limit]
            return {"type": "FeatureCollection", "features": feats_page, "numberMatched": len(feats), "numberReturned": len(feats_page)}
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

    async def fetch_collections_queryables(self, collection_ids: List[str]) -> Dict[str, Any]:  # pragma: no cover
        return {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mcp_get_feature_matches_api():
    stub = RichStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    # initialise workflow context so guard allows tool usage
    await service.os_ngd_init_mapping_workflow()
    api_feature = await stub.make_request("COLLECTION_FEATURE_BY_ID", path_params=["col-1", "f1"])
    out = await service.get_feature("col-1", "f1")
    mcp_feature = json.loads(out)
    assert mcp_feature == api_feature


@pytest.mark.unit
@pytest.mark.asyncio
async def test_mcp_search_features_matches_api_filter():
    stub = RichStubAPI()
    mcp = FastMCP("equivalence")
    service = OSDataHubService(stub, mcp)
    await service.os_ngd_init_mapping_workflow()
    filt = "category = 'A'"
    api_result = await stub.make_request(
        "COLLECTION_FEATURES", params={"filter": filt, "limit": 100}, path_params=["col-1"]
    )
    out = await service.search_features(collection_id="col-1", filter=filt, limit=100)
    mcp_result = json.loads(out)
    assert mcp_result == api_result
