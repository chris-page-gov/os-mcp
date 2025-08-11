# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and adheres to Semantic Versioning.

## [Unreleased]
### Planned
- `suggest_workflow` tool for automatic prompt recommendation.
- Additional regional prompt modules (e.g. London, Manchester).
- Caching / performance instrumentation documentation.
### Added
- Experimental `chat` tool (OpenAI) behind OPENAI_API_KEY.
	- Added initial chat tool tests (unit) covering success, missing key, invalid JSON, and context bypass.
	- Documentation updates (README, Claude Desktop tutorial, VS Code integration guide) referencing chat tool and test count.

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

