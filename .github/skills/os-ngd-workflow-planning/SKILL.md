---
name: os-ngd-workflow-planning
description: Plan and execute Ordnance Survey NGD searches using this MCP server’s required 2-step workflow (planning + fetch queryables) before running feature searches. Use when you need reliable OS NGD collection selection, filters, and query sequencing.
compatibility: Designed for agents using the os-mcp MCP server (stdio or HTTP transport).
metadata:
  author: CHRISCARLON/os-mcp
  kind: mcp-skill
---

# OS NGD Workflow Planning (os-mcp)

## When to use this skill
Use this skill when the user asks to search OS NGD features (e.g. cinemas, roads, buildings) and you want consistent, accurate results.

This MCP server enforces a **2-step workflow**:
1. Create a plan and name the collections you will query
2. Fetch queryables for those collections before calling search tools

## How to use this skill

### Step 0 — Confirm server access
- If you need to sanity check connectivity, call the tool `hello_world`.
- If you need to ensure OS credentials are configured, call `check_api_key`.

### Step 1 — Get workflow context
Call:
- `get_workflow_context`

This returns a list of available collections and the workflow requirement.

### Step 2 — Choose collections and fetch queryables
Based on the workflow context, pick the smallest set of relevant collection IDs.

Call:
- `fetch_detailed_collections` with a comma-separated list of collection IDs

Use the returned queryables to decide:
- Which fields are filterable
- Which values are enums vs free text
- Which CRS/bbox patterns are supported

### Step 3 — Execute searches
Now perform feature searches:
- Prefer `search_features` for discovery
- Use `get_feature` if you already have a feature ID
- Use bulk tools if you have many identifiers

### Step 4 — Summarize and verify
- Explain what was queried (collection IDs, bbox, filters)
- If results are empty, retry with relaxed filters, larger bbox, or alternate collections

## References
- See: references/REFERENCE.md
