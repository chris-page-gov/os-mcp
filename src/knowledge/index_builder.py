"""Build higher-level indices from harvested metadata snapshot for fast query planning.

Outputs a JSON file `knowledge_index_latest.json` with structures:
  - field_to_collections: field -> [collection ids]
  - enum_value_to_fields: enum literal -> list of {field, collection}
  - collection_prefix_groups: prefix (first two hyphen parts) -> [collections]
  - collection_stats: {collection: {enum_count, total_queryables}}
  - high_cardinality_fields (heuristic): fields appearing in > X collections

These indices accelerate mapping from user intent tokens to candidate collections.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List

SNAP_DIR = Path("data/metadata")


def load_latest_snapshot() -> Dict[str, Any]:
    latest = SNAP_DIR / "latest.json"
    if not latest.exists():
        raise FileNotFoundError("Run metadata harvester first (latest.json missing)")
    return json.loads(latest.read_text(encoding="utf-8"))


def build_indices(snapshot: Dict[str, Any], multi_field_threshold: int = 5) -> Dict[str, Any]:
    field_to_collections: Dict[str, List[str]] = defaultdict(list)
    enum_value_to_fields: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    collection_prefix_groups: Dict[str, List[str]] = defaultdict(list)
    collection_stats: Dict[str, Dict[str, Any]] = {}

    for col in snapshot.get("collections", []):
        cid = col["id"]
        parts = cid.split("-")
        prefix = "-".join(parts[:2]) if len(parts) >= 2 else parts[0]
        collection_prefix_groups[prefix].append(cid)
        collection_stats[cid] = {
            "enum_count": col.get("enum_count", 0),
            "total_queryables": col.get("total_queryables", 0),
        }
        for q in col.get("queryables", []):
            fname = q.get("name")
            if not fname:
                continue
            field_to_collections[fname].append(cid)
            if q.get("is_enum") and q.get("enum_values"):
                for val in q["enum_values"][:50]:  # guard size
                    enum_value_to_fields[val].append({"field": fname, "collection": cid})

    high_cardinality_fields = [
        f for f, cols in field_to_collections.items() if len(cols) >= multi_field_threshold
    ]

    return {
        "field_to_collections": field_to_collections,
        "enum_value_to_fields": enum_value_to_fields,
        "collection_prefix_groups": collection_prefix_groups,
        "collection_stats": collection_stats,
        "high_cardinality_fields": high_cardinality_fields,
        "source_generated_from": "latest.json",
    }


def write_indices(indices: Dict[str, Any]):
    out = SNAP_DIR / "knowledge_index_latest.json"
    with out.open("w", encoding="utf-8") as f:
        json.dump(indices, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":  # pragma: no cover
    snap = load_latest_snapshot()
    idx = build_indices(snap)
    write_indices(idx)
    print("Knowledge index written.")
