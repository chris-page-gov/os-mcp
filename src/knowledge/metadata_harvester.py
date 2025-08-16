"""Metadata harvesting utilities for building a local knowledge base of OS NGD collections.

The harvester pulls:
  * All (latest) collections (id, title, description, itemType, extent)
  * Queryables for each collection (type info, enum values)
  * Light sample: first N feature items (ids + selected attributes) when requested

It writes timestamped JSON snapshots under data/metadata/ so that downstream
processes (LLM planning, gold standard QA generation, evaluation harness) can
operate on a stable, reproducible view of the schema even if upstream changes.

Design goals:
  * Non-intrusive: re-use existing OSAPIClient instance (avoid extra auth logic)
  * Bounded: optional limits on feature sampling to respect rate limiting
  * Deterministic output ordering for diff friendliness
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from api_service.os_api import OSAPIClient


@dataclass
class QueryableInfo:
    name: str
    type: str
    nullable: bool
    is_enum: bool
    enum_values: Optional[List[str]] = None
    max_length: Optional[int] = None
    format: Optional[str] = None


@dataclass
class CollectionSnapshot:
    id: str
    title: str
    description: str
    itemType: str
    queryables: List[QueryableInfo]
    enum_queryables: List[QueryableInfo]
    total_queryables: int
    enum_count: int
    sample_features: Optional[List[Dict[str, Any]]] = None
    field_presence: Optional[Dict[str, Dict[str, Any]]] = None  # per-field stats


class MetadataHarvester:
    def __init__(self, client: OSAPIClient, output_dir: str = "data/metadata"):
        self.client = client
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def harvest(
        self,
        sample_features: bool = False,
        sample_limit: int = 3,
        collect_stats: bool = False,
        enum_value_cap: int = 10,
    ) -> Dict[str, Any]:
        """Harvest collections + queryables (+ optional feature samples) and persist a snapshot.

        Returns the in-memory structure also.
        """
        if collect_stats and not sample_features:
            # Stats rely on sampled features
            sample_features = True
        collections_cache = await self.client.cache_collections()
        collection_ids = [c.id for c in collections_cache.collections]

        # Fetch queryables in batches to avoid huge parallel fan-out
        snapshots: List[CollectionSnapshot] = []
        batch_size = 15
        for i in range(0, len(collection_ids), batch_size):
            batch = collection_ids[i : i + batch_size]
            queryables_map = await self.client.fetch_collections_queryables(batch)
            for cid in sorted(batch):
                q = queryables_map.get(cid)
                if not q:
                    continue
                q_infos: List[QueryableInfo] = []
                enum_infos: List[QueryableInfo] = []
                for name, meta in sorted(q.all_queryables.items()):
                    qi = QueryableInfo(
                        name=name,
                        type=meta.get("type", "string"),
                        nullable=bool(meta.get("nullable", False)),
                        is_enum=bool(meta.get("is_enum", False)),
                        enum_values=meta.get("enum_values"),
                        max_length=meta.get("max_length"),
                        format=meta.get("format"),
                    )
                    q_infos.append(qi)
                    if qi.is_enum:
                        enum_infos.append(qi)

                sample_data = None
                field_presence: Optional[Dict[str, Dict[str, Any]]] = None
                if sample_features:
                    # Try to fetch a tiny sample deterministically (limit= sample_limit)
                    try:
                        params = {"limit": str(sample_limit)}
                        data = await self.client.make_request(
                            "COLLECTION_FEATURES", params=params, path_params=[cid]
                        )
                        features = data.get("features", [])
                        trimmed: List[Dict[str, Any]] = []
                        if collect_stats:
                            field_presence = {}
                        for f in features:
                            props = f.get("properties", {})
                            subset = {k: props[k] for k in list(props)[:10]}
                            trimmed.append(
                                {
                                    "id": f.get("id"),
                                    "properties_subset": subset,
                                }
                            )
                            if collect_stats and field_presence is not None:
                                for qn in props.keys():
                                    rec = field_presence.setdefault(
                                        qn,
                                        {
                                            "present": 0,
                                            "sample_size": 0,
                                            "enum_values_seen": set(),
                                        },
                                    )
                                    rec["sample_size"] += 1
                                    if props[qn] is not None:
                                        rec["present"] += 1
                                        # capture enum value if defined as enum
                                        if any(e.name == qn for e in enum_infos):
                                            rec["enum_values_seen"].add(str(props[qn]))
                        sample_data = trimmed
                    except Exception as e:  # pragma: no cover - non critical
                        sample_data = [{"error": str(e)}]
                        field_presence = None

                # Finalise enum value sets into lists
                if field_presence:
                    for v in field_presence.values():
                        if isinstance(v.get("enum_values_seen"), set):
                            vals = list(v["enum_values_seen"])[:enum_value_cap]
                            v["enum_values_seen"] = vals
                            # add simple presence ratio
                            if v.get("sample_size"):
                                v["presence_ratio"] = round(
                                    v["present"] / max(1, v["sample_size"]), 3
                                )

                snapshots.append(
                    CollectionSnapshot(
                        id=cid,
                        title=q.title,
                        description=q.description,
                        itemType="feature",  # always feature presently
                        queryables=q_infos,
                        enum_queryables=enum_infos,
                        total_queryables=q.total_queryables,
                        enum_count=q.enum_count,
                        sample_features=sample_data,
                        field_presence=field_presence,
                    )
                )

        snapshot_doc: Dict[str, Any] = {
            "generated_at": time.time(),
            "collection_count": len(snapshots),
            "collections": [asdict(s) for s in snapshots],
        }

        ts = int(snapshot_doc["generated_at"])
        outfile = self.output_dir / f"schema_snapshot_{ts}.json"
        with outfile.open("w", encoding="utf-8") as f:
            json.dump(snapshot_doc, f, ensure_ascii=False, indent=2)

        # Also write/refresh a latest pointer
        latest_path = self.output_dir / "latest.json"
        with latest_path.open("w", encoding="utf-8") as f:
            json.dump(snapshot_doc, f, ensure_ascii=False, indent=2)

        return snapshot_doc


async def _main():  # pragma: no cover - convenience entrypoint
    client = OSAPIClient()
    harvester = MetadataHarvester(client)
    await harvester.harvest(sample_features=False)
    await client.close()


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(_main())
