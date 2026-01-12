import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_service.os_service import OSDataHubService


class DummyAPI:
    async def initialise(self) -> None:  # type: ignore[override]
        return None

    async def close(self) -> None:  # type: ignore[override]
        return None

    async def get_api_key(self) -> str:  # type: ignore[override]
        return "dummy"

    async def make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        path_params: Optional[List[str]] = None,
    ) -> Dict[str, Any]:  # type: ignore[override]
        return {"collections": []}

    async def make_request_no_auth(
        self, url: str, params: Optional[Dict[str, Any]] = None, max_retries: int = 2
    ) -> str:  # type: ignore[override]
        return "{}"

    async def cache_openapi_spec(self):  # type: ignore[override]
        from models import OpenAPISpecification

        return OpenAPISpecification(
            title="t",
            version="1",
            base_url="u",
            endpoints={},
            collection_ids=[],
            supported_crs={},
            crs_guide={},
        )

    async def cache_collections(self):  # type: ignore[override]
        from models import CollectionsCache

        return CollectionsCache(collections=[], raw_response={})

    async def fetch_collections_queryables(self, collection_ids: List[str]):  # type: ignore[override]
        return {}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_list_and_get_agent_skill(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Create a minimal valid Agent Skills directory
    skills_root = tmp_path / "skills"
    skill_dir = skills_root / "my-skill"
    skill_dir.mkdir(parents=True)

    (skill_dir / "SKILL.md").write_text(
        """---
name: my-skill
description: A test skill
---

Body
""",
        encoding="utf-8",
    )

    monkeypatch.setenv("OS_MCP_SKILLS_DIRS", str(skills_root))

    mcp = FastMCP("test-skills")
    svc = OSDataHubService(DummyAPI(), mcp)

    listed_raw = await svc.list_agent_skills()
    listed = json.loads(listed_raw)
    assert listed["status"] == "ok"
    assert any(s["name"] == "my-skill" for s in listed["skills"])

    got_raw = await svc.get_agent_skill("my-skill")
    got = json.loads(got_raw)
    assert got["status"] == "ok"
    assert "SKILL.md" in got["location"]
    assert "name: my-skill" in got["content"]
