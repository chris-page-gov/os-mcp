# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and adheres to Semantic Versioning.

## [Unreleased]
### Planned
### Added
- `/health` unauthenticated liveness endpoint (HTTP transport) with integration test.
- `docs/http_usage.md` detailed cURL tutorial.
- `docs/claude_desktop_tutorial.md` plain language Claude Desktop integration guide.

- `suggest_workflow` tool for automatic prompt recommendation.
- Additional regional prompt modules (e.g. London, Manchester).
- Caching / performance instrumentation documentation.

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

