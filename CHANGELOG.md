# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and adheres to Semantic Versioning.

## [Unreleased]

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
- Tool count increased from 22 to 29 (7 new MCP-Apps tools: 3 geography + 4 statistics)
- Resource count increased from 6 to 9 (3 new UI resources)
- Test count increased from 83 to 141 (58 new tests: 14 geography + 23 statistics + 19 ONS client)

### Internal
- New directory structure: `src/ui/`, `src/tools/`, `src/clients/`
- `src/mcp_service/ui_resources.py` - UI resource registration module
- `src/tools/geography_tools.py` - Modular geography tool implementations
- `src/tools/statistics_tools.py` - ONS statistics tool implementations
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

