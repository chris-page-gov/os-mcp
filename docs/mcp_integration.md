# VS Code MCP Integration & Prompt Library Guide

## Overview
This document describes how to integrate the `os-mcp` Model Context Protocol (MCP) server with Visual Studio Code's latest MCP-enabled Copilot agent mode. It also proposes a structured prompt library (with Warwickshire-focused geospatial workflows) to exercise Ordnance Survey NGD APIs via MCP tools.

## Goals
- Seamless MCP server registration (stdio or streamable HTTP) in VS Code.
- Auth + rate limiting alignment with existing middleware.
- Consistent, guided 2‑step planning workflow enforced by tools.
- Extensible prompt taxonomy (planning, search, routing, linked identifiers, diagnostics, enrichment).
- High-quality Warwickshire example prompts to bootstrap agent reasoning.
- Foundation for sampling & prompt selection inside VS Code chat.

## MCP Server Transports
| Transport | Use Case | Pros | Cons |
|----------|----------|------|------|
| stdio | Local dev / fastest startup | Simple, low latency | Per-session only |
| streamable-http | Shared / multi-client | Reusable endpoint, easier auth via Bearer | Slightly more setup |

Health Check (HTTP transport): once running you can probe `GET /health` (no auth) for `{ "status": "ok" }` to support editor/task readiness checks.

## Required Environment Variables
| Variable | Purpose | When Required |
|----------|---------|---------------|
| OS_API_KEY | NGD DataHub access | Always |
| STDIO_KEY | Stdio auth gate | stdio transport |
| BEARER_TOKENS | Comma list of allowed tokens | HTTP transport |
| DEBUG=1 | Verbose logging | Optional |

## VS Code Configuration (servers.json)
Create (user) MCP config (example `~/.config/vscode/mcp/servers.json`):
```jsonc
{
  "servers": {
    "os-ngd": {
      "command": "python",
      "args": ["-m", "server", "--transport", "stdio"],
      "env": {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "STDIO_KEY": "dev-stdio-key"
      }
    }
  }
}
```
HTTP variant (combining launch & discovery):
```jsonc
{
  "servers": {
    "os-ngd-http": {
      "type": "http-streamable",
      "url": "http://127.0.0.1:8000",
      "command": "python",
      "args": ["-m", "server", "--transport", "streamable-http", "--host", "127.0.0.1", "--port", "8000"],
      "env": {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "BEARER_TOKENS": "vs-code-token"
      },
      "auth": { "scheme": "bearer", "token": "vs-code-token" }
    }
  }
}
```

## Task Definitions (Optional)
`.vscode/tasks.json`:
```jsonc
{
  "version": "2.0.0",
  "tasks": [
    { "label": "Run MCP (stdio)", "type": "shell", "command": "python -m server --transport stdio" },
    { "label": "Run MCP (http)", "type": "shell", "command": "python -m server --transport streamable-http --host 127.0.0.1 --port 8000" }
  ]
}
```

## Tools & Sequence
| Tool | Typical First Use? | Purpose |
|------|--------------------|---------|
| get_workflow_context | Yes | Bootstraps planning context (collections list, planning rules) |
| fetch_detailed_collections | After planning | Pulls queryables for selected collections |
| search_features | After queryables | Executes filtered feature searches |
| get_feature | On-demand | Single feature retrieval |
| get_bulk_features | On-demand batch | Batch retrieval / attribute enrichment |
| get_linked_identifiers | On-demand | Cross-identifier resolution |
| get_bulk_linked_features | On-demand batch | Batch cross-links |
| get_prompt_templates | Anytime | Discover prompt patterns |
| get_routing_data | Specialized | Build+extract routing network slices |
| (HTTP only) /health | N/A | Out-of-band liveness check (not a tool call) |

### Listing Tools in VS Code Chat
In the Copilot Chat panel, type:
```
@os-ngd list tools
```
You should see all registered tools including `get_prompt_templates`, `fetch_detailed_collections`, and `get_routing_data`.

### Testing a Simple Tool Call
```
@os-ngd call hello_world {"name": "Tester"}
```
Expect: `Hello, Tester!` response.

## Structured Error Envelopes
All tool errors return:
```jsonc
{
  "error": "MESSAGE",
  "message": "MESSAGE",
  "error_code": "INVALID_COLLECTION|...",
  "tool": "search_features",
  "details": { ... },
  "retry_guidance": { "tool": "search_features", "hint": "..." }
}
```
Integrating with VS Code Chat: The agent can branch on `error_code` to automatically run recovery (e.g., call `get_workflow_context` or list valid collections).

## Prompt Library Design
Directory (proposal):
```
src/prompt_templates/
  prompt_templates.py        # existing base
  warwickshire.py            # new region-focused prompts
  planning.py (future)       # generic planning patterns
  routing.py (future)
  diagnostics.py (future)
```
Merge strategy:
```python
from .prompt_templates import PROMPT_TEMPLATES as BASE
from .warwickshire import WARWICKSHIRE_PROMPTS
PROMPT_TEMPLATES = {**BASE, **WARWICKSHIRE_PROMPTS}
```
Expose categories by namespacing keys or grouping under dicts (future: extend get_prompt_templates(category=...)).

## Warwickshire Prompt Set (Initial Draft)
Key prompts (summaries):
1. planning_warwickshire_overview – multi-collection planning (road links + land use). 
2. fetch_roadlink_queryables_warwick – enumerate road classifications.
3. search_cinemas_leamington – land use tertiary group filter example.
4. search_rail_stations_warwick – bbox + rail node lookup.
5. bulk_lookup_specific_roadlinks – enrich network segment IDs.
6. linked_identifiers_uprn_to_toid_example – cross-identifier exploration.
7. route_network_build_small_bbox – build & inspect restrictions.
8. analyze_turn_restrictions_stratford – restriction classification.
9. search_primary_roads_rugby – classification filter & bbox.
10. diagnostic_invalid_collection – force INVALID_COLLECTION path.
11. diagnostic_missing_workflow_context – force WORKFLOW_CONTEXT_REQUIRED.
12. enrichment_name_resolution – combine bulk + single feature.
13. linked_bulk_identifiers_crosscheck – batch link consistency.
14. planning_multi_collection_landuse_transport – integrated plan with sequential queries.

Full prompt texts are implemented across:
```
prompt_templates/
  warwickshire.py
  planning.py
  routing.py
  diagnostics.py
```

## Sampling & Chat Integration
VS Code Copilot can:
- List prompts (via get_prompt_templates).
- Sample suggestions: maintain a small client-side palette referencing keys.
- Use error envelopes to adapt (branch on error_code, iterate planning steps).

Future extension: Add a `suggest_workflow` tool to parse user natural language, returning a ranked list of prompt_template keys + justification.

## Using Prompts Inside VS Code Chat
1. List all prompts:
  ```
  @os-ngd call get_prompt_templates {}
  ```
2. Filter by category (substring match):
  ```
  @os-ngd call get_prompt_templates {"category": "warwickshire"}
  @os-ngd call get_prompt_templates {"category": "planning"}
  @os-ngd call get_prompt_templates {"category": "routing"}
  @os-ngd call get_prompt_templates {"category": "diagnostics"}
  ```
3. Choose a prompt key (e.g. `search_cinemas_leamington`) and ask Copilot:
  ```
  Use the prompt template 'search_cinemas_leamington' and execute the workflow.
  ```
  The agent should: (a) call `get_workflow_context`, (b) call `fetch_detailed_collections`, (c) call `search_features` with the Cinema filter.

## Validating the Two‑Step Workflow Enforcement
1. Attempt a search prematurely:
  ```
  @os-ngd call search_features {"collection_id": "lus-fts-site-1", "filter": "oslandusetertiarygroup = 'Cinema'"}
  ```
2. If context not initialized you'll receive `WORKFLOW_CONTEXT_REQUIRED` in the error envelope.
3. Recover:
  ```
  @os-ngd call get_workflow_context {}
  @os-ngd call fetch_detailed_collections {"collection_ids": "lus-fts-site-1"}
  ```
4. Re-run the search; it should now succeed (subject to real API data & credentials).

## Exercising Diagnostic Prompts
1. Trigger invalid collection error:
  ```
  @os-ngd call search_features {"collection_id": "invalid-collection"}
  ```
  Expect `INVALID_COLLECTION` with `valid_collections` in details.
2. Use diagnostic prompt:
  Ask Copilot to apply `diagnostic_invalid_collection` pattern and observe recovery behaviour.

## Routing Workflow Verification
1. Get routing template list:
  ```
  @os-ngd call get_prompt_templates {"category": "routing"}
  ```
2. Use `routing_network_build_and_summarise` prompt instructions to call:
  ```
  @os-ngd call get_routing_data {"bbox": "<minx,miny,maxx,maxy>", "limit": 100, "build_network": true}
  ```
3. Confirm returned JSON includes counts / restriction summaries (depending on implementation state).

## Full Local Test Cycle
From the repo root:
```
python -m server --transport stdio  # or streamable-http
```
In another terminal run unit tests:
```
pytest -q
```
All tests (currently >20) should pass; category tests validate prompt filtering.

## Raw HTTP / cURL Usage
For detailed examples of posting MCP JSON envelopes (tools/call) directly to the `/mcp` endpoint—including `get_workflow_context`, `fetch_detailed_collections`, `search_features`, prompts filtering, routing, and error handling—see `http_usage.md` in this directory.

## VS Code Launch Task (Optional)
Create `.vscode/tasks.json`:
```jsonc
{
  "version": "2.0.0",
  "tasks": [
   {"label": "MCP STDIO", "type": "shell", "command": "python -m server --transport stdio"},
   {"label": "MCP HTTP", "type": "shell", "command": "python -m server --transport streamable-http --host 127.0.0.1 --port 8000"}
  ]
}
```

## Quick Troubleshooting Matrix
| Symptom | Likely Cause | Action |
|---------|-------------|--------|
| `WORKFLOW_CONTEXT_REQUIRED` | Skipped planning step | Run `get_workflow_context` then `fetch_detailed_collections` |
| `INVALID_COLLECTION` | Typo or unsupported collection id | List collections or inspect `valid_collections` in error details |
| Empty prompt filter result | Category substring mismatch | Re-check category value / use broader substring |
| Bearer auth failure (HTTP) | Missing or wrong token | Set `BEARER_TOKENS` & pass correct Authorization header |
| No prompts listed | Server not started / wrong server name | Verify servers.json entry and that process is running |

## Completion Checklist for Integration
1. servers.json configured (stdio or http).
2. Server process running (no startup errors).
3. `@os-ngd list tools` shows expected tools.
4. `get_prompt_templates` returns base + extended prompts.
5. Category filtering returns correct subsets (validated manually or via tests).
6. Two-step workflow error path observed & recovered.
7. Diagnostic error envelope observed (`INVALID_COLLECTION`).
8. Routing data tool exercised (if bbox & data available).
9. All pytest tests pass locally.
10. CHANGELOG updated & version bumped.

## Security & Rate Limits
- HTTP middleware (bearer tokens) + RequestIDMiddleware for traceable logs.
- Rate limiting at HTTP layer + guardrails in stdio for misuse patterns.

## Implementation Steps (Proposed PR)
1. Add `warwickshire.py` with WARWICKSHIRE_PROMPTS.
2. Update aggregator and extend `get_prompt_templates` to accept new category.
3. Add tests: category retrieval + one template content assertion.
4. Update CHANGELOG (Unreleased) with implementation line.
5. (Optional) Add `suggest_workflow` stub tool.

## Testing Strategy
- Unit: retrieval of warwickshire prompt subset.
- Integration: Chat agent fetches prompt, then executes prescribed tool sequence (mock API if needed).

## Maintenance Guidelines
- Keep prompt keys stable; treat as public contract for agents.
- Version bump when adding or materially changing prompts.
- Provide region-specific modules (e.g., `london.py`) under same pattern.

## Appendix: Example Full Prompt (search_cinemas_leamington)
```
"search_cinemas_leamington": "Goal: List cinema sites near Royal Leamington Spa. Step 1: get_workflow_context(). Step 2: fetch_detailed_collections('lus-fts-site-1'). Step 3: search_features(collection_id='lus-fts-site-1', filter=\"oslandusetertiarygroup = 'Cinema'\"). Provide concise list with id, name (if present), and coordinate centroid." 
```

## Open Questions
- Provide CRSs other than default? (Add guidance in prompts.)
- Add caching introspection tool? (Potential future enhancement.)

---
Last Updated: 2025-08-09
