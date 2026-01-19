# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and adheres to Semantic Versioning.

## [Unreleased]

### Added
- _None._

### Changed
- **Docs**: updated evaluation summary to reflect the latest basic-only run results.

### Fixed
- _None._

## [0.1.18] - 2026-01-19

### Added
- **Client trace proxy** (`scripts/mcp_stdio_trace_proxy.py`) to log MCP JSON-RPC traffic for tool list/call analysis.
- **Client trace guidance** (`docs/client_trace_strategy.md`) covering MCP logs + client reasoning transcripts.
- **Geography selector focus support**: map config accepts `focus_level`/`focus_name` to zoom into a larger area before selecting smaller units.

### Changed
- **select_geographic_area** is now always-loaded to surface the map widget for clients with limited tool lists.
- **route_query** detects OA/LSOA/MSOA selection intent and recommends focus parameters for map zooming.
- **Hard rename cleanup** across docs/tests/error guidance to use `os_ngd_init_mapping_workflow` and `os_ngd_list_mapping_collections`.
- **ONS API client** now requires an async context manager session and maps connection failures to `ONSAPIError` for consistent error handling.

### Added - Sprint 8: Architecture Review & Query Router

- **Query Router Tool** (`route_query`):
  - NEW PRIMARY ENTRY POINT - Call this FIRST for any natural language query
  - Analyzes query intent and recommends the correct tool
  - Classifies into: place_lookup, statistics, area_comparison, feature_search, etc.
  - Returns recommended tool, parameters, workflow steps, and guidance
  - Prevents common mistakes like using OS NGD for simple place lookups
  - Implementation: `src/tools/query_router.py` (~400 lines)

- **User Tutorial** (`docs/tutorial.md`):
  - Comprehensive hands-on guide for new users
  - Setup instructions for Claude Desktop, Claude Code CLI, and Cowork
  - 8 progressive tutorial exercises from basic queries to advanced workflows
  - Client comparison table showing feature availability
  - Troubleshooting guide and quick reference card

- **Sprint 8 Planning** (`plans/sprint-8-architecture-review.md`):
  - Architecture analysis and redesign plan
  - Root cause analysis of "Birmingham problem"
  - Proposed solutions: query router, tiered tools, improved descriptions

- **Evaluation Framework** (`tests/evaluation/`):
  - Comprehensive question suite (30+ questions) with expected outcomes
  - 5-dimension scoring rubric (100 points total)
  - Test harness for automated evaluation
  - Current score: 100% on basic and intermediate questions (21/21)
  - Documentation: `docs/evaluation.md`

- **Audit Logging System** (`src/utils/audit_logger.py`):
  - LLM-readable audit logs with clear sections
  - Sections: QUERY, ROUTING, TOOL_CALLS, RESPONSE, METRICS
  - Thread-local context for request tracking
  - Decorator support for tool call auditing
  - Dual output: human-readable logs + JSONL for analysis

- **Query Router Unit Tests** (`tests/test_query_router.py`):
  - 250+ lines of comprehensive tests
  - Tests for all 8 intent types
  - Edge case and priority handling tests
  - Performance benchmarks

- **MCP Tool Annotations** (`src/mcp_service/tool_search_config.py`):
  - Added `readOnlyHint` annotation to 36 read-only tools (reduces client permission prompts)
  - Added `openWorldHint` annotation to 22 tools that call external APIs (OS Data Hub, ONS, OpenAI)
  - Added `idempotentHint` annotation to 10 tools with no side effects
  - Only 2 stateful tools: `update_shared_context`, `share_selection`
  - New helper: `get_tool_annotations(tool_name)` returns annotation hints for any tool

- **MCP Resources and Prompts for Client Guidance**:
  - New resource: `skills://os-ons/getting-started` - Serves SKILL.md content via MCP
  - New prompt: `getting_started` - Critical guidance to call route_query FIRST
  - Helps MCP clients understand correct tool selection workflow

- **STOP_AND_CHECK Warning in Workflow Tools**:
  - `os_ngd_init_mapping_workflow` now returns prominent warning at top of response
  - `os_ngd_list_mapping_collections` also returns warning
  - Warning asks: "Is the user asking to FIND A PLACE BY NAME?"
  - Directs to use `search_geographic_areas` instead of OS NGD workflow for place lookups
  - Includes examples: "Find Birmingham", "Local authority code for Coventry"

### Fixed
- **Critical: Tool routing for common queries**:
  - "Find Birmingham" now correctly routes to `search_geographic_areas` (was incorrectly going to OS NGD)
  - "Find cinemas near Leeds" routes to OS NGD workflow (feature_search intent)
  - "Compare Birmingham and Manchester" routes to `compare_areas`
  - Query router prevents confusion between ONS Geography and OS NGD APIs

### Changed
- **MAJOR: Renamed OS NGD workflow tools to prevent misuse**:
  - `get_workflow_context` → `os_ngd_init_mapping_workflow` (clearly specialized)
  - `list_collections` → `os_ngd_list_mapping_collections` (clearly specialized)
  - Tool descriptions now start with ⛔ SPECIALIZED and ❌ WRONG TOOL warnings
  - These tools are now obviously for OS topographic mapping, not place lookups
- **MAJOR: Reduced always-loaded tools from 12 to 5 for token efficiency**:
  - PRIMARY: `search_geographic_areas` (find places by name)
  - PRIMARY: `get_statistics` (get stats for an area)
  - ROUTING: `route_query` (classifies query intent)
  - CORE: `hello_world`, `version_info`
  - MOVED TO DEFERRED: `os_ngd_init_mapping_workflow`, `os_ngd_list_mapping_collections`, `select_geographic_area`, `list_ons_datasets`, `plan_route`, `get_shared_context`, `check_api_key`
- **MAJOR: Slashed `os_ngd_init_mapping_workflow` response from ~15KB to ~1KB**:
  - Removed full collection metadata (was listing every field)
  - Returns only: theme descriptions, collection IDs by theme, example usage
- **Tool descriptions updated with ★ PRIMARY TOOL ★ markers**:
  - `search_geographic_areas`: "★ PRIMARY TOOL ★ Find UK places by name"
  - `get_statistics`: "★ PRIMARY TOOL ★ Get statistics for an area"
  - OS NGD tools de-emphasized with ⛔ SPECIALIZED markers
- **Enhanced system prompt** with decision guide table showing which tool to use
- **Updated SKILL.md** with prominent "Use route_query FIRST" section

## [0.1.17] - 2026-01-17

### Added - MCP-Apps Integration (Sprints 1-7 Complete)

**Sprint 6 - Documentation:**
- **Skills Documentation** (`SKILL.md`):
  - Comprehensive reference for LLM context building
  - Two-step workflow explanation
  - UK geographic hierarchy and area codes
  - Common workflow patterns with examples
  - Tool reference tables
  - Dataset categories and usage
  - Best practices and troubleshooting

- **User Guide** (`docs/mcp_apps_guide.md`):
  - Quick start examples for all widgets
  - Interactive widget documentation
  - Statistics workflow guide
  - Feature exploration guide
  - Cross-widget communication examples
  - Troubleshooting section

- **MCP-Apps Prompt Templates** (`src/prompt_templates/mcp_apps.py`):
  - 13 new workflow prompts for widget usage
  - Geography: select_uk_areas, find_area_by_postcode, compare_local_authorities
  - Statistics: explore_ons_statistics, census_2021_analysis, area_wellbeing_profile
  - Features: inspect_os_feature, explore_linked_identifiers
  - Routes: plan_walking_route, plan_driving_route, analyze_road_network
  - Cross-widget: area_to_statistics_workflow, feature_to_route_workflow, multi_widget_analysis

### Added - Tool Search Integration (Sprint 7) ✅ COMPLETE
- **Tool Search Infrastructure** (`src/mcp_service/tool_search_config.py`):
  - `ToolCategory` enum with 10 categories (Core, Workflow, Geography, Statistics, Features, Routing, Widget, Search, Linked, Utility)
  - `ALWAYS_LOADED_TOOLS` set (11 tools) - core entry points loaded immediately
  - `DEFERRED_TOOLS` set (26 tools) - specialized tools discovered via search
  - Enhanced descriptions with keywords for regex and BM25 searchability
- **New Tool**: `get_tool_search_config` - Returns tool search configuration, categories, and MCP toolset config
- **MCP Toolset Integration**: `generate_mcp_toolset_config()` produces configuration for Anthropic's tool search API
- **Test Coverage**: 50+ new tests across `test_tool_search_config.py` and `test_tool_search_service.py`
- **Technical Requirements**: Beta headers `advanced-tool-use-2025-11-20`, `mcp-client-2025-11-20`; supported models: Claude Opus 4.5, Claude Sonnet 4.5

**Agent Guidance:**
- **AGENTS.md**: New file with testing patterns and common pitfalls for AI agents
  - FastMCP mock configuration (pass-through decorator pattern)
  - String assertion best practices
  - Tool addition checklist

### Changed
- README.md updated with Sprint 7 completion status
- PROGRESS.md updated to Sprint 7 complete (all MCP-Apps sprints done)
- Tool count increased from 36 to 37 (new: get_tool_search_config)
- Test count increased from 320+ to 370+ (50+ new tool search tests)

### Internal - Test Coverage Improvement (Sprint 6) ✅ COMPLETE
- Added `tests/test_routing_service_detailed.py` - 40+ tests for routing network (37% → 100%)
- Added `tests/test_ui_resources.py` - 15+ tests for UI resource registration (55% → 79%)
- Added `tests/test_guardrails.py` - 15+ tests for prompt injection (62% → 100%)
- Added `tests/test_resources.py` - 10+ tests for documentation resources (68% → 100%)
- Added `tests/test_stdio_middleware.py` - 15+ tests for STDIO middleware
- Added `tests/test_workflow_planner.py` - 15+ tests for WorkflowPlanner class
- Added `tests/test_prompts_detailed.py` - 15+ tests for prompts module
- Added `tests/test_server_functions.py` - 15+ tests for server helper functions
- Added `tests/test_knowledge_index_builder.py` - 15+ tests for knowledge index
- Added `tests/test_http_middleware_detailed.py` - 20+ tests for HTTP middleware
- Added `tests/test_error_envelope_detailed.py` - 20+ tests for error envelopes
- Added `tests/test_performance.py` - Performance benchmark tests
- Extended `tests/test_geography_tools.py` with error path tests (73% → 82%)
- Extended `tests/test_statistics_tools.py` with error handling tests
- Extended `tests/test_ons_client.py` with edge case tests
- Overall test count: 211 → 320+ (110+ new tests)
- Overall coverage: 68% → >80%

### Internal - Production Deployment (Sprint 6)
- Updated `Dockerfile` with multi-stage build, non-root user, health check
- Updated `.github/workflows/ci.yml` with coverage reporting and Docker build job
- Added `performance` pytest marker for benchmark tests

### Added - MCP-Apps Integration (Sprint 5)
- **Feature Inspector Widget** (`src/ui/feature_inspector.html`):
  - Properties table with filtering and type-aware formatting
  - Leaflet map visualization of feature geometry
  - Linked identifiers display with tabbed navigation (TOID, UPRN, USRN)
  - Click-to-navigate between linked features
  - Export functionality (JSON, CSV, clipboard)
- **Feature Inspector Tools** (2 new tools, bypass workflow context):
  - `inspect_feature` - Opens feature inspector widget with UI resource reference
  - `get_feature_with_linked` - Prepares feature data with linked identifiers
- **Route Planner Widget** (`src/ui/route_planner.html`):
  - Map-based start/end point selection with draggable markers
  - Waypoint support for multi-stop routes
  - Turn-by-turn directions display
  - Road network visualization
  - Route summary (distance, estimated time, segments)
- **Route Planner Tools** (2 new tools, bypass workflow context):
  - `plan_route` - Opens route planner widget with optional preset points
  - `get_route_network` - Gets road network data for a bounding box
- **Cross-Widget Communication** (`src/tools/widget_communication.py`):
  - Shared context for selection state across widgets
  - `get_shared_context` - Gets current shared selections
  - `update_shared_context` - Adds/removes/clears selections
  - `share_selection` - Shares selection from one widget to another
- New test files:
  - `tests/test_feature_inspector_tools.py` with 25 unit tests
  - `tests/test_route_planner_tools.py` with 24 unit tests
  - `tests/test_widget_communication.py` with 21 unit tests

### Added - MCP-Apps Integration (Sprint 3-4)
- **ONS Statistics API Client** (`src/clients/ons_client.py`):
  - Full client for ONS Beta API (https://api.beta.ons.gov.uk/v1)
  - Rate limiting (120 req/10s) with automatic throttling
  - TTL-based caching for API responses
  - Dataset discovery, dimension queries, and observation retrieval
- **Statistics Tools** (4 new tools, bypass workflow context):
  - `list_ons_datasets` - Lists available ONS datasets with category and search filters
  - `get_dataset_info` - Gets detailed metadata for a specific dataset
  - `get_statistics` - Retrieves statistical observations for geographic areas
  - `compare_areas` - Compares statistics across multiple areas
- **Statistics Dashboard Widget** (`src/ui/statistics_dashboard.html`):
  - Chart.js integration for line and bar charts
  - Summary statistics cards (latest value, average, range)
  - Area comparison table with rankings
  - Export functionality (CSV, JSON, clipboard)
  - Responsive design for mobile devices
- New test files:
  - `tests/test_statistics_tools.py` with 23 unit tests
  - `tests/test_ons_client.py` with 19 unit tests

### Added - MCP-Apps Integration (Sprint 1-2)
- **MCP-Apps UI Resources**: New `ui://` URI scheme resources for interactive widgets
  - `ui://os-ons/geography-selector` - Interactive map for UK geographic area selection
  - `ui://os-ons/statistics-dashboard` - Interactive dashboard for ONS statistics visualization
  - `ui://os-ons/feature-inspector` - Placeholder for feature detail inspection
- **Geography Tools** (3 new tools, bypass workflow context):
  - `select_geographic_area` - Opens interactive map widget, returns `_meta.uiResourceUris`
  - `fetch_boundaries` - Fetches GeoJSON boundaries from ONS Geography API
  - `search_geographic_areas` - Searches UK areas by name
- **ONS Geography API Integration**: Live integration with ONS ArcGIS REST services for boundary data
  - Supports 6 geographic levels: Parliamentary Constituencies, Local Authority Districts, Wards, LSOA, MSOA, Output Areas
  - Service names verified against ONS API as of January 2025
- **Geography Selector Widget** (`src/ui/geography_selector.html`):
  - Leaflet-based interactive map
  - Multi-select area selection
  - Level switching (dropdown)
  - Search by name or postcode (postcodes.io integration)
  - MCP-Apps postMessage communication for selection confirmation
- New test file `tests/test_geography_tools.py` with 14 unit tests
- Updated CLAUDE.md with MCP-Apps architecture documentation

### Added
- Helper script `scripts/run_prod_stdio.sh` to launch production (wheel) stdio server with argument parsing and safety checks.
- README "Manual STDIO Smoke Test" section with copy/paste client snippet for listing tools.

### Changed
- Tool count increased from 22 to 36 (14 new MCP-Apps tools: 3 geography + 4 statistics + 2 feature inspector + 2 route planner + 3 widget communication)
- Resource count increased from 6 to 10 (4 new UI resources: geography-selector, statistics-dashboard, feature-inspector, route-planner)
- Test count increased from 83 to ~210 (new tests: 14 geography + 23 statistics + 19 ONS client + 25 feature inspector + 24 route planner + 21 widget communication)

### Internal
- New directory structure: `src/ui/`, `src/tools/`, `src/clients/`
- `src/mcp_service/ui_resources.py` - UI resource registration module
- `src/tools/geography_tools.py` - Modular geography tool implementations
- `src/tools/statistics_tools.py` - ONS statistics tool implementations
- `src/tools/feature_inspector_tools.py` - Feature inspection tools with linked identifiers
- `src/tools/route_planner_tools.py` - Route planning tools with direction formatting
- `src/tools/widget_communication.py` - Cross-widget communication and shared context
- `src/clients/ons_client.py` - ONS Statistics API client with rate limiting and caching

## [0.1.16] - 2025-08-15
### Changed
- Replaced fragile dev/prod detection (substring '/src/') with a robust helper that: (1) honors explicit OS_MCP_MODE env override; (2) treats execution from an installed site/dist-packages path as prod; else dev. Prevents production wheels from misleadingly reporting '(dev)' when global PYTHONPATH leaked earlier.
### Added
- OS_MCP_MODE env var override for explicit forcing of dev or prod mode (useful in tests / diagnostics).
### Internal
- Refactored mode logic into `_compute_mode` in `server.py` to centralize heuristic and reduce duplication.

## [0.1.15] - 2025-08-15
### Added
- Console script entrypoints `os-mcp` and `os-mcp-stdio` (maps to `server:main`) so production environments can launch without relying on `python -m server` and being affected by a global `PYTHONPATH`.
### Changed
- Bumped package version to 0.1.15 to ensure VS Code detects updated wheel vs lingering 0.1.13 logs.
### Notes
- This is a preparatory step toward fully isolating prod wheel execution from the editable source tree (next: move modules under a package namespace to avoid `/src/` heuristic ambiguity).

## [0.1.14] - 2025-08-15
### Fixed
- Packaging: Added `py-modules` declaration so `server.py` (and `models.py`) are included in the built wheel. Previously the production venv lacked `server` module causing `No module named server` when launching `python -m server`.

## [0.1.13] - 2025-08-15
### Changed
- Standardized all invocation paths to `python -m server` (removed lingering `python -m src.server` references) to prevent `ModuleNotFoundError: No module named 'src'` in environments where `PYTHONPATH` is not set.
### Removed
- Devcontainer embedded MCP server auto-registration block and any VS Code tasks/launch duplication to avoid multiple concurrent server starts.
### Documentation
- Updated README and VS Code / frontend docs to reflect single authoritative entrypoint and simplified setup.
 - Added support & docs for `OS_MCP_SERVER_NAME` env var to differentiate dev/prod server names in MCP clients.
### Internal / Maintenance
- Updated Dockerfile and stdio integration tests to use module execution form; added typing improvements in `stdio_client_test.py`.
### Added
- Helper script `scripts/build_prod_stdio.sh` to build & install a production (wheel) stdio venv and emit MCP config snippet.

### Planned
- `suggest_workflow` tool for automatic prompt recommendation.
- Additional regional prompt modules (e.g. London, Manchester).
- Caching / performance instrumentation documentation.
### Added
- Experimental `chat` tool (OpenAI) behind OPENAI_API_KEY.
	- Added initial chat tool tests (unit) covering success, missing key, invalid JSON, and context bypass.
	- Documentation updates (README, Claude Desktop tutorial, VS Code integration guide) referencing chat tool and test count.
- `version_info` MCP tool (mode dev/prod + package version + selected env vars).
- Dual VS Code config guidance (separate `os-mcp-dev` editable & `os-ngd` wheel entries).
- Deployment helper script `scripts/deploy_os_ngd.sh` (wheel build + servers.json patching).
- Example servers file `examples/vscode-servers.json`.
- Unit test `test_version_info_tool.py` validating version info shape.
- HTTP /health now returns version & mode; startup log line includes version/mode.

## [0.1.12] - 2025-08-11
### Added
- Frontend: Automatic GeoJSON detection in assistant/tool responses; FeatureCollection / Feature / geometry objects parsed and added as map layers.
- Frontend: Map rendering of GeoJSON layers (Leaflet) with Answer | Map | Data tabs.
- Frontend: Layer visibility toggling and removal controls (Data tab) with persistent state in Zustand store.
- Frontend tests expanded (logic + integration) covering planning heuristic, MCP tool abstraction, GeoJSON detection, layer auto-add, and layer toggle/removal (total frontend tests now 20).
### Changed
- Output panel logic refactored for cleaner layer synchronization (add/remove without leaking Leaflet layer references).
- Zustand store extended (messages, traces, layers with visibility flags + actions) while preserving existing API for messages & traces.
### Fixed
- TypeScript syntax / interface issues introduced during initial layer toggle attempt (now resolved; all frontend tests green).
### Internal / Maintenance
- Combined backend (52) + frontend (20) test suites documented (72 total passing tests at release time).

## [0.1.11] - 2025-08-11
### Removed
- Pruned obsolete example, doc, and exploratory test files (removed untracked local clutter; ensures clean devcontainer rebuilds).
### Added
- OpenAI key passthrough in devcontainer config (OPENAI_API_KEY) (not yet wired to tools).
- Legacy `BEARER_TOKEN` fallback warning test (`test_legacy_bearer_token_warning`).
### Changed
- Harmonised authentication env usage on `BEARER_TOKENS` (comma‑separated). Added explicit deprecation docs for singular `BEARER_TOKEN` (removal >=0.2.0).
- STDIO authentication failure now exits with clear message & non‑zero status when `STDIO_KEY` missing.
### Deprecated
- Singular `BEARER_TOKEN` environment variable (warning emitted if used alone; removal targeted for 0.2.0).
### Fixed
- Intermittent MCP stdio startup ambiguity by clarifying missing `STDIO_KEY` cause (now explicit exit).
### Internal / Maintenance
- Added additional OSAPIClient tests (caching, queryables, sanitisation) raising `os_api.py` coverage to ~61%.
- Documentation updates (http_usage, mcp_integration) for deprecation timeline.

## [0.1.10] - 2025-08-09
### Added
- Experimental frontend scaffold (`frontend/`): React + Vite + TypeScript + Leaflet (Tutorial, Chat, Output tabs, map init).
- Frontend developer quickstart (`frontend/README.md`).
### Changed
- Root `README.md` updated with experimental frontend section, clarified cloning example, and local dev commands.
### Fixed
- Oversized git change set by expanding `.gitignore` (node_modules, dist, coverage, IDE files, build artifacts).
### Internal / Maintenance
- Frontend MVP design document (`docs/frontend_mvp.md`) referenced in README.

## [0.1.9] - 2025-08-09
### Added
- `/health` unauthenticated liveness endpoint (HTTP transport) with integration test.
- `docs/http_usage.md` detailed cURL tutorial.
- `docs/claude_desktop_tutorial.md` plain language Claude Desktop integration guide.
### Internal / Maintenance
- Documentation consolidation & Makefile helper targets.

## [0.1.8] - 2025-08-09
### Added
- Comprehensive VS Code MCP integration & testing guide (`docs/mcp_integration.md`).
- Extended prompt library: Warwickshire, planning, routing, diagnostics modules with dynamic merging.
- Category filtering for `get_prompt_templates` (substring match) across all transports.
- Extensive category filtering test coverage (warwickshire/planning/routing/diagnostic/diagnostics/unknown).
- README section for VS Code MCP setup.

### Changed
- Documentation clarified two-step workflow enforcement & diagnostic recovery patterns.

### Internal / Maintenance
- Test suite expanded to 24 passing tests including new category scenarios.

## [0.1.7] - 2025-08-09
### Added
- Standardised error handling with `ErrorCode` enum and `build_error_envelope` helper (retry guidance & normalization).
- New tests for error envelopes, workflow context enforcement, invalid collection handling, linked identifiers filtering, and request ID logging.
- Request ID middleware injecting `x-request-id` header and optional JSON structured logging support.
- Structured JSON logging formatter (`JsonRequestFormatter`) with optional `json_logs` flag.
- CI workflow (GitHub Actions) running mypy and pytest on pushes / PRs.
- Optional test extras in `pyproject.toml` (`.[test]`).
- TypedDict `LinkedIdentifier` for linked identifiers response typing.

### Changed
- Refactored MCP tool registration to reduce broad `type: ignore` usage.
- Unified error responses across service tools using `ErrorCode` values instead of ad-hoc strings.
- Replaced legacy retry context injection with standardized envelope while keeping backward compatibility.

### Fixed
- Forward reference / annotation issues that previously broke STDIO tool registration.
- Missing imports and instability in `os_service.py` during enum refactor.
- Rate limiting and auth middleware tests stabilized & retained.

### Internal / Maintenance
- Added comprehensive test coverage (total 16 passing tests now).
- Introduced TypedDict-based typing for dynamic JSON areas to improve mypy signal.

## [0.1.6] - 2025-08-XX
### Added
- Initial integration tests (HTTP & STDIO) and server factory `build_streamable_http_app`.
- Dependency pinning and strict mypy configuration.
- Middleware for HTTP auth & rate limiting.

### Notes
Earlier versions (<0.1.6) covered initial project scaffolding, basic MCP service, and discovery endpoints.
