# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server providing LLM access to Ordnance Survey's Data Hub APIs for UK geospatial data. The server enforces a **2-step workflow** where LLMs must first get workflow context, then fetch detailed collection queryables before making data searches.

## Common Commands

```bash
# Install in editable mode with test dependencies
pip install -e .[test]

# Run all tests
pytest tests

# Run a single test file
pytest tests/test_chat_tool.py

# Run a specific test
pytest tests/test_chat_tool.py::test_chat_valid_messages

# Run with coverage
pytest --cov=src --cov=tests --cov-report=term-missing

# Type checking (strict mode enforced in CI)
mypy src

# Start server (stdio transport - default)
python -m server --transport stdio

# Start server (HTTP transport)
python -m server --transport streamable-http --host 127.0.0.1 --port 8000

# Health check (requires running HTTP server)
curl -s http://127.0.0.1:8000/health

# Quick dev smoke test
./scripts/dev_stdio_list_tools.sh
```

## Architecture

### Entry Point & Transport Layer
- `src/server.py` - Main entry point. Supports stdio (default) and streamable-http transports via `--transport` flag. Creates `FastMCP` instance and wires up middleware.

### Core Service Layer
- `src/mcp_service/os_service.py` - `OSDataHubService` class: registers all MCP tools, resources, and prompts. Contains the 22+ tools (search_features, get_feature, chat, routing, etc.). Implements workflow context enforcement via `_require_workflow_context` decorator.
- `src/api_service/os_api.py` - `OSAPIClient`: handles all HTTP requests to OS Data Hub APIs. Includes rate limiting, API key sanitization, collection caching, and OpenAPI spec parsing.

### Workflow Enforcement
The server requires a 2-step workflow:
1. Call `get_workflow_context()` to initialize the `WorkflowPlanner` with basic collection info
2. Call `fetch_detailed_collections(collection_ids)` to get queryables for specific collections
3. Only then can `search_features` and similar tools be called

Tools in `skip_functions` set (hello_world, check_api_key, chat, list_collections, etc.) bypass this requirement.

### Middleware Stack
- `src/middleware/http_middleware.py` - Bearer token auth for HTTP transport (reads `BEARER_TOKENS` env var)
- `src/middleware/stdio_middleware.py` - Auth and rate limiting for stdio transport (reads `STDIO_KEY` env var)
- `src/middleware/request_id_middleware.py` - Adds X-Request-ID headers

### Prompt Templates & Resources
- `src/prompt_templates/` - Categorized prompt templates (planning, routing, diagnostics, warwickshire, mcp_apps)
- `src/prompt_templates/mcp_apps.py` - 13 prompts for MCP-Apps widget workflows
- `src/mcp_service/prompts.py` - Registers MCP prompts
- `src/mcp_service/resources.py` - Registers MCP resources (documentation access)

### Documentation
- `SKILL.md` - Skills documentation for LLM context (geographic hierarchy, workflows, tools reference)
- `docs/mcp_apps_guide.md` - User guide for MCP-Apps interactive widgets

### Knowledge Index
- `src/knowledge/` - Metadata harvester and index builder for field/collection suggestions
- `data/metadata/knowledge_index_latest.json` - Pre-built index for `suggest_collections` and `suggest_fields` tools

### Error Handling
- `src/utils/error_envelope.py` - Structured error envelopes with `ErrorCode` enum (WORKFLOW_CONTEXT_REQUIRED, INVALID_COLLECTION, UPSTREAM_ERROR, etc.)

### MCP-Apps UI Resources (Interactive Widgets)
- `src/mcp_service/ui_resources.py` - Registers MCP-Apps UI resources (`ui://` URI scheme)
- `src/ui/` - HTML widget files for interactive UI components
- `src/tools/geography_tools.py` - Geography selection tools that integrate with ONS boundaries API
- `src/tools/statistics_tools.py` - ONS Statistics API tools
- `src/tools/feature_inspector_tools.py` - Feature inspection tools with linked identifiers
- `src/tools/route_planner_tools.py` - Route planning tools
- `src/tools/widget_communication.py` - Cross-widget communication tools

#### Available UI Resources
| URI | Description |
|-----|-------------|
| `ui://os-ons/geography-selector` | Interactive map for selecting UK geographic areas |
| `ui://os-ons/statistics-dashboard` | Dashboard for ONS statistics visualization |
| `ui://os-ons/feature-inspector` | Feature detail view with properties, map, and linked IDs |
| `ui://os-ons/route-planner` | Route planning with waypoints and turn-by-turn directions |

#### Geography Tools (bypass workflow context)
| Tool | Description |
|------|-------------|
| `select_geographic_area` | Opens interactive map widget, returns `_meta.uiResourceUris` |
| `fetch_boundaries` | Fetches GeoJSON boundaries from ONS Geography API |
| `search_geographic_areas` | Searches areas by name using ONS API |

#### Statistics Tools (bypass workflow context)
| Tool | Description |
|------|-------------|
| `list_ons_datasets` | Lists available ONS datasets with category filtering |
| `get_dataset_info` | Gets detailed metadata for a specific dataset |
| `get_statistics` | Retrieves observations for geographic areas |
| `compare_areas` | Compares statistics across multiple areas |

#### Feature Inspector Tools (bypass workflow context)
| Tool | Description |
|------|-------------|
| `inspect_feature` | Opens feature inspector widget with UI resource reference |
| `get_feature_with_linked` | Prepares feature data with linked identifiers |

#### Route Planner Tools (bypass workflow context)
| Tool | Description |
|------|-------------|
| `plan_route` | Opens route planner widget with start/end configuration |
| `get_route_network` | Gets road network data for a bounding box |

#### Cross-Widget Communication Tools (bypass workflow context)
| Tool | Description |
|------|-------------|
| `get_shared_context` | Gets current cross-widget shared state |
| `update_shared_context` | Adds/removes/clears selections in shared context |
| `share_selection` | Shares selection from one widget to another |

#### Supported Geographic Levels
- `parl_const` - Parliamentary Constituencies (650)
- `local_auth` - Local Authority Districts (~350)
- `ward` - Electoral Wards (~8,000)
- `lsoa` - Lower Super Output Areas (~35,000)
- `msoa` - Middle Super Output Areas (~7,000)
- `oa` - Output Areas (~180,000)

## Tool Search Integration (Planned - Sprint 7)

The project is preparing to implement Anthropic's Tool Search facility for dynamic tool discovery:

### Overview
- With 36+ tools, the project approaches the threshold where tool selection accuracy degrades
- Tool search enables `defer_loading: true` to load tools on-demand rather than upfront
- Two search variants: regex (`tool_search_tool_regex_20251119`) and BM25 (`tool_search_tool_bm25_20251119`)

### Tool Categories (Planned)
| Category | Always Loaded | Deferred |
|----------|---------------|----------|
| Core | hello_world, version_info, check_api_key | - |
| Workflow | get_workflow_context, list_collections | fetch_detailed_collections |
| Geography | select_geographic_area | fetch_boundaries, search_geographic_areas |
| Statistics | list_ons_datasets | get_dataset_info, get_statistics, compare_areas |
| Features | - | search_features, get_feature, inspect_feature |

### Technical Requirements
- Beta headers: `advanced-tool-use-2025-11-20`, `mcp-client-2025-11-20`
- Supported models: Claude Opus 4.5, Claude Sonnet 4.5
- MCP integration via `mcp_toolset` with `default_config.defer_loading`

See `docs/mcp_toolsearch.md` for full documentation.

## Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `OS_API_KEY` | Required - Ordnance Survey Data Hub API key |
| `STDIO_KEY` | Required for stdio transport auth |
| `BEARER_TOKENS` | Comma-separated list of valid HTTP bearer tokens |
| `OPENAI_API_KEY` | Enables experimental `chat` MCP tool |
| `OS_MCP_AUTH_BYPASS` | Test-only bypass for auth (1/true/yes) |
| `OS_MCP_SERVER_NAME` | Custom server display name (default: os-ngd-api) |

## Testing Notes

- Tests use `pytest-asyncio` with `asyncio_mode = "auto"`
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Slow production build test gated by `OS_MCP_RUN_SLOW=1`
- Many tests mock `OSAPIClient` or specific service methods

## Adding a New Tool

1. Add implementation method to `OSDataHubService` in `src/mcp_service/os_service.py`
2. Add tool name to `tool_names` list in `register_tools()`
3. If tool should bypass workflow context, add to `skip_functions` set in `_require_workflow_context()`
4. Create tests covering success path and at least one error path
5. Run `mypy src` - strict typing is enforced
6. **Update documentation** (see below)

## Documentation Requirements (MANDATORY)

**You MUST update documentation after completing any significant work.** This is not optional.

### After ANY code changes, update:

1. **`CHANGELOG.md`** - Add entry under `[Unreleased]` section describing what changed
   - Use categories: Added, Changed, Fixed, Removed, Internal
   - Be specific about what was added/changed

2. **`plans/PROGRESS.md`** - Update task statuses and metrics
   - Mark completed tasks with ✅
   - Update the metrics table (test count, tools, resources)
   - Add notes about what was implemented

3. **`README.md`** - Update if:
   - New tools were added (update tool count, add to tables)
   - New features were added (add user-facing documentation)
   - Sprint status changed (update progress table)

4. **This file (`CLAUDE.md`)** - Update if:
   - Architecture changed (new modules, patterns)
   - New environment variables added
   - New commands needed

### Documentation checklist (copy into your work):
```
- [ ] CHANGELOG.md updated with changes
- [ ] plans/PROGRESS.md task statuses updated
- [ ] plans/PROGRESS.md metrics updated (tests, tools, resources)
- [ ] README.md progress table updated (if sprint completed)
- [ ] CLAUDE.md updated (if architecture changed)
```

### MCP-Apps Implementation Tracking

This project is actively implementing MCP-Apps features. See:
- `plans/PROGRESS.md` - Detailed sprint/task tracking
- `plans/os-mcp-apps-design.md` - Design document
- `plans/on-ons mcp implementation-roadmap.md` - Sprint breakdown

When working on MCP-Apps features, always update `plans/PROGRESS.md` with:
- Task completion status
- Files created/modified
- Any blockers or issues encountered
