#!/usr/bin/env python
"""
End‑to‑end example invoking the MCP server over stdio to:
 1. Initialize session
 2. os_ngd_init_mapping_workflow
 3. fetch_detailed_collections for a target land use collection
 4. search_features for cinemas (oslandusetertiarygroup = 'Cinema')

Requirements:
  - Environment variables: OS_API_KEY (real), STDIO_KEY (any non-empty, default dev-key)
  - Project installed editable (pip install -e .) so `python -m server` works

Usage:
  OS_API_KEY=your_key python scripts/workflow_cinema_example.py

If the land use collection or enum field is absent, the script reports gracefully.
"""
from __future__ import annotations
import asyncio
import os
import sys
import json
from typing import Any, Dict

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession
from mcp.types import TextContent

COLLECTION_CANDIDATES = [
    "lus-fts-site-1",  # land use sites (expected)
]
TARGET_ENUM_FIELD = "oslandusetertiarygroup"
TARGET_ENUM_VALUE = "Cinema"


def require_env(var: str) -> str:
    val = os.environ.get(var)
    if not val:
        print(f"ERROR: {var} not set; export {var}=... and retry", file=sys.stderr)
        sys.exit(1)
    return val


async def call_tool(session: ClientSession, name: str, args: Dict[str, Any] | None = None) -> Any:
    """Invoke a tool and return parsed JSON if possible else raw string/dict.

    Ensures type awareness for mypy by only reading .text from TextContent blocks.
    """
    # Use Any here because the mcp.types exported ToolResult may not expose all
    # internal generics under the pinned mcp version; we only need 'content'.
    result: Any = await session.call_tool(name, args or {})  # type: ignore[assignment]
    texts: list[str] = []
    for c in result.content:
        if isinstance(c, TextContent):  # ignore image/audio/resources for this workflow
            texts.append(c.text)
    raw = "\n".join(texts) if texts else ""
    if not raw:
        return {"_note": "no textual content"}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


async def main() -> None:
    require_env("OS_API_KEY")
    stdio_key = os.environ.get("STDIO_KEY", "dev-key")

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "server", "--transport", "stdio"],
        env={
            "STDIO_KEY": stdio_key,
            "OS_API_KEY": os.environ["OS_API_KEY"],
            "OS_MCP_SERVER_NAME": "os-mcp-dev-script",
        },
    )

    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            print("[1] os_ngd_init_mapping_workflow ...", flush=True)
            ctx = await call_tool(session, "os_ngd_init_mapping_workflow")
            if isinstance(ctx, dict) and ctx.get("error_code"):
                print("Failed to get workflow context:", ctx)
                return

            print("Context retrieved; keys:", list(ctx.keys())[:10])

            # Pick first available candidate collection present in context summary if any
            target_collection = None
            if isinstance(ctx, dict):
                # naive scan of textified context
                ser = json.dumps(ctx)
                for cid in COLLECTION_CANDIDATES:
                    if cid in ser:
                        target_collection = cid
                        break
            if not target_collection:
                target_collection = COLLECTION_CANDIDATES[0]
                print(f"WARNING: {target_collection} not spotted in context; continuing anyway")

            print(f"[2] fetch_detailed_collections for {target_collection} ...")
            details = await call_tool(
                session,
                "fetch_detailed_collections",
                {"collection_ids": [target_collection]},
            )
            if isinstance(details, dict) and details.get("error_code"):
                print("Failed to fetch detailed collections:", details)
                return

            # Inspect enum queryables
            enum_ok = False
            if (
                isinstance(details, dict)
                and "collections" in details
                and target_collection in details["collections"]
            ):
                col = details["collections"][target_collection]
                enum_q = col.get("enum_queryables", {}) if isinstance(col, dict) else {}
                if TARGET_ENUM_FIELD in enum_q:
                    enum_ok = True
                    print(
                        f"Found enum field '{TARGET_ENUM_FIELD}' with {len(enum_q[TARGET_ENUM_FIELD].get('values', []))} values"
                    )
                else:
                    print(f"Enum field '{TARGET_ENUM_FIELD}' not present; enum_queryables keys: {list(enum_q.keys())}")

            if not enum_ok:
                print("Cannot perform cinema filter search (enum field missing). Exiting gracefully.")
                return

            print("[3] search_features (cinemas)...")
            search_res = await call_tool(
                session,
                "search_features",
                {
                    "collection_id": target_collection,
                    "filter": f"{TARGET_ENUM_FIELD} = '{TARGET_ENUM_VALUE}'",
                    "limit": 5,
                },
            )
            if isinstance(search_res, dict) and search_res.get("error_code"):
                print("Search returned error envelope:", search_res)
                return

            # Summarize features
            if isinstance(search_res, dict):
                feats = search_res.get("features")
                if isinstance(feats, list):
                    print(f"Returned {len(feats)} feature(s)")
                    for f in feats[:5]:
                        if not isinstance(f, dict):
                            continue
                        fid = f.get("id")
                        props = f.get("properties", {}) if isinstance(f.get("properties"), dict) else {}
                        tertiary = props.get(TARGET_ENUM_FIELD)
                        print(f" - id={fid} {TARGET_ENUM_FIELD}={tertiary}")
                else:
                    print("Unexpected search response shape:")
                    snippet = json.dumps(search_res, indent=2)
                    print(snippet[:2000])

if __name__ == "__main__":  # pragma: no cover
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
