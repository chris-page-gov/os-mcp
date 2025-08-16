#!/usr/bin/env python
import asyncio, os, json
from typing import Any, Dict, List, Optional
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import TextContent

BBOX = "-1.57,52.27,-1.50,52.31"
FALLBACK_FILTER = "LOWER(name) LIKE '%cinema%'"

async def main():
    params = StdioServerParameters(
        command="python",
        args=["-m", "src.server", "--transport", "stdio"],
        env={
            "OS_API_KEY": os.environ.get("OS_API_KEY", ""),
            "STDIO_KEY": os.environ.get("STDIO_KEY", "dev-key"),
        },
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Step 1: workflow context
            ctx = await session.call_tool("get_workflow_context", {})
            ctx_text: str = next((c.text for c in ctx.content if isinstance(c, TextContent)), "{}")
            try:
                ctx_json: Dict[str, Any] = json.loads(ctx_text)
            except Exception:
                ctx_json = {}
            # Heuristic: find candidate collections likely about land use / sites
            candidates: List[str] = []
            coll_list = ctx_json.get("CRITICAL_COLLECTION_LIST", [])
            if isinstance(coll_list, list):
                for raw_cid in coll_list:
                    cid: str
                    if isinstance(raw_cid, str):
                        cid = raw_cid
                    else:
                        continue
                    if any(k in cid for k in ["site", "land", "lnd"]):
                        candidates.append(cid)
            # Narrow typical NGD site collections prefix patterns
            candidates = sorted(set(candidates))[:6]
            # Step 2: fetch detailed queryables for candidates batch
            if candidates:
                await session.call_tool("fetch_detailed_collections", {"collection_ids": ",".join(candidates)})
            # Pull detailed again via fetch to inspect enum fields individually
            detected_collection: Optional[str] = None
            detected_field: Optional[str] = None
            # Try each candidate individually to examine enum_queryables
            for cid in candidates:
                det = await session.call_tool("fetch_detailed_collections", {"collection_ids": cid})
                det_text: str = next((c.text for c in det.content if isinstance(c, TextContent)), "{}")
                try:
                    det_json: Dict[str, Any] = json.loads(det_text)
                except Exception:
                    continue
                detailed_raw = det_json.get("detailed_collections", {})  # type: ignore[assignment]
                if not isinstance(detailed_raw, dict):  # type: ignore[truthy-bool]
                    continue
                detailed: Dict[str, Any] = detailed_raw  # type: ignore[assignment]
                coll_meta_any = detailed.get(cid) or {}  # type: ignore[index]
                if not isinstance(coll_meta_any, dict):
                    continue
                enums_any = coll_meta_any.get("enum_queryables") or {}  # type: ignore[assignment]
                if not isinstance(enums_any, dict):  # type: ignore[truthy-bool]
                    continue
                for field, values in enums_any.items():  # type: ignore[union-attr]
                    if not isinstance(field, str):
                        continue
                    if isinstance(values, list):
                        for v in values:
                            if isinstance(v, str) and v.lower() == "cinema":
                                detected_collection = cid
                                detected_field = field
                                break
                        if detected_collection:
                            break
                if detected_collection:
                    break
            # Build primary filter if we found a matching enum value
            primary_filter = None
            if detected_collection and detected_field:
                primary_filter = f"{detected_field} = 'Cinema'"
            # Choose collection for fallback (first candidate if none matched)
            fallback_collection = detected_collection or (candidates[0] if candidates else None)
            results_payload: Dict[str, Any] = {
                "bbox": BBOX,
                "detected_collection": detected_collection,
                "detected_field": detected_field,
                "primary_filter": primary_filter,
            }
            search_result_json = None
            if primary_filter and detected_collection:
                primary_res = await session.call_tool("search_features", {
                    "collection_id": detected_collection,
                    "filter": primary_filter,
                    "bbox": BBOX,
                    "limit": 50
                })
                primary_text: Optional[str] = next((c.text for c in primary_res.content if isinstance(c, TextContent)), None)
                try:
                    search_result_json = json.loads(primary_text) if primary_text else None
                except Exception:
                    pass
                results_payload["primary_result_raw"] = primary_text
            # Fallback if no features or no primary filter
            if not search_result_json or not (isinstance(search_result_json, dict) and search_result_json.get("features")):
                if fallback_collection:
                    fb_res = await session.call_tool("search_features", {
                        "collection_id": fallback_collection,
                        "filter": FALLBACK_FILTER,
                        "bbox": BBOX,
                        "limit": 50
                    })
                    fb_text: Optional[str] = next((c.text for c in fb_res.content if isinstance(c, TextContent)), None)
                    results_payload.update({
                        "fallback_used": True,
                        "fallback_collection": fallback_collection,
                        "fallback_filter": FALLBACK_FILTER,
                        "fallback_result_raw": fb_text,
                    })
                else:
                    results_payload.update({
                        "fallback_used": True,
                        "fallback_error": "No candidate collection identified"
                    })
            else:
                results_payload["fallback_used"] = False
            print(json.dumps(results_payload, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
