"""Fetch public NGD markdown docs, hash contents, extract candidate field names, and
produce a variance report against live queryables snapshot.

Heuristics (initial iteration):
  * Collect all markdown URLs ending in `.md` found in `docs/ngd_sources.md`.
  * Fetch content concurrently (bounded concurrency).
  * Extract candidate field names via regex patterns:
      - Backticked identifiers: `field_name`
      - Table style: lines starting with `| field_name |` (snake/camel alnum + underscore)
      - Emphasis patterns: **field_name** if it matches identifier pattern
  * Compare aggregated documented field names with union of queryables across collections.
  * Persist docs snapshot + variance summary as JSON with timestamp for reproducibility.

Limitations / Future Enhancements:
  * Per-collection mapping (needs semantic parsing of docs) not attempted yet.
  * Enum extraction from tables could be added when consistent pattern confirmed.
  * Currently treats all documented identifiers as global; may produce false positives.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Set

import aiohttp


NGD_SOURCES_MD = Path("docs/ngd_sources.md")
OUTPUT_DIR = Path("data/metadata")


IDENTIFIER_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*)`")
TABLE_CELL_RE = re.compile(r"^\|\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\|")
STAR_BOLD_RE = re.compile(r"\*\*([a-zA-Z_][a-zA-Z0-9_]*)\*\*")


@dataclass
class DocRecord:
    url: str
    sha256: str
    size: int
    field_names: List[str]


async def _fetch(session: aiohttp.ClientSession, url: str) -> str:
    timeout = aiohttp.ClientTimeout(total=30)
    async with session.get(url, timeout=timeout) as resp:
        resp.raise_for_status()
        return await resp.text()


def extract_doc_urls() -> List[str]:
    if not NGD_SOURCES_MD.exists():
        return []
    urls: List[str] = []
    for line in NGD_SOURCES_MD.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(">"):
            continue
        # crude URL detection
        md_urls = re.findall(r"https?://[^ )]+", line)
        for u in md_urls:
            if u.endswith(".md") and "docs.os.uk" in u:
                urls.append(u)
    return sorted(set(urls))


def extract_field_names(markdown: str) -> Set[str]:
    names: Set[str] = set()
    for regex in (IDENTIFIER_RE, STAR_BOLD_RE):
        for m in regex.finditer(markdown):
            names.add(m.group(1))
    for line in markdown.splitlines():
        m = TABLE_CELL_RE.match(line)
        if m:
            names.add(m.group(1))
    return names


async def fetch_all(urls: List[str]) -> List[DocRecord]:
    records: List[DocRecord] = []
    connector = aiohttp.TCPConnector(limit=5, force_close=True)
    async with aiohttp.ClientSession(connector=connector) as session:
        sem = asyncio.Semaphore(5)

        async def runner(u: str):
            async with sem:
                try:
                    txt = await _fetch(session, u)
                except Exception as e:  # pragma: no cover
                    txt = f"ERROR: {e}"
                h = hashlib.sha256(txt.encode("utf-8")).hexdigest()
                fields = sorted(extract_field_names(txt)) if not txt.startswith("ERROR:") else []
                records.append(
                    DocRecord(url=u, sha256=h, size=len(txt), field_names=fields)
                )

        await asyncio.gather(*(runner(u) for u in urls))
    return records


def load_latest_queryables_union() -> Set[str]:
    latest = OUTPUT_DIR / "latest.json"
    if not latest.exists():
        return set()
    data = json.loads(latest.read_text(encoding="utf-8"))
    field_names: Set[str] = set()
    for col in data.get("collections", []):
        for q in col.get("queryables", []):
            name = q.get("name")
            if name:
                field_names.add(name)
    return field_names


async def build_variance_report() -> Dict[str, Any]:
    urls = extract_doc_urls()
    docs = await fetch_all(urls)
    documented_fields: Set[str] = set()
    for d in docs:
        documented_fields.update(d.field_names)

    live_fields = load_latest_queryables_union()

    only_in_docs = sorted(documented_fields - live_fields)
    only_live = sorted(live_fields - documented_fields)

    report: Dict[str, Any] = {
        "generated_at": time.time(),
        "doc_count": len(docs),
        "documented_field_count": len(documented_fields),
        "live_field_count": len(live_fields),
        "variance": {
            "only_in_docs": only_in_docs[:200],  # limit to keep file manageable
            "only_in_live": only_live[:200],
        },
        "docs": [asdict(r) for r in docs],
        "notes": [
            "This is a global comparison; future versions will attempt per-collection mapping.",
            "Field name extraction is heuristic (backticks, table first column, bold identifiers).",
        ],
    }

    ts = int(report["generated_at"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_file = OUTPUT_DIR / f"docs_snapshot_{ts}.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    latest = OUTPUT_DIR / "docs_latest.json"
    with latest.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return report


async def _main():  # pragma: no cover
    rep = await build_variance_report()
    print(json.dumps({k: v for k, v in rep.items() if k in ("doc_count", "documented_field_count", "live_field_count")}, indent=2))


if __name__ == "__main__":  # pragma: no cover
    asyncio.run(_main())
