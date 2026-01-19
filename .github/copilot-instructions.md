# Copilot instructions for os-mcp

## Big picture
- Entry point is `src/server.py` (CLI: `python -m server` or `os-mcp`). It builds a `FastMCP` server for either **stdio** or **streamable-http**, and wires Starlette middleware.
- The main orchestrator is `OSDataHubService` in `src/mcp_service/os_service.py`: registers tools/resources/prompts and wraps tools with **guardrails + workflow enforcement + auth/rate-limit (stdio)**.
- External calls to Ordnance Survey Data Hub go through `OSAPIClient` in `src/api_service/os_api.py` (async `aiohttp`, caching, API-key sanitisation).
- “MCP-Apps” widgets live in `src/ui/` and are registered as `ui://...` resources via `src/mcp_service/ui_resources.py`; most widget-facing tool logic is in `src/tools/`.

## Workflow contract (critical)
- Many data tools are gated by `_require_workflow_context` inside `OSDataHubService`.
- Required flow for feature search:
  1) call `get_workflow_context()` (initialises `WorkflowPlanner` with basic collections)
  2) call `fetch_detailed_collections(["collection-id", ...])` (loads queryables/enums)
  3) then call `search_features(...)` using enum values exactly as provided
- Some tools bypass workflow enforcement via the service’s `skip_functions` set (e.g. geography/statistics/widgets/chat). If you add a tool that should be callable first, add it there.

## Tool search (defer_loading)
- Tool search config lives in `src/mcp_service/tool_search_config.py`.
- Keep these consistent (tests assert it):
  - membership in `ALWAYS_LOADED_TOOLS` vs `DEFERRED_TOOLS`
  - `TOOL_DESCRIPTIONS[name]["defer_loading"]`
  - `ToolCategory` selection + keywords

## Response + error conventions
- Many MCP tools return **JSON strings** (`json.dumps(...)`) rather than raw dicts. Preserve this contract unless refactoring end-to-end.
- For failures, prefer `utils/error_envelope.build_error_envelope(tool=..., code=ErrorCode..., message=...)` over ad-hoc strings.

## Auth / middleware (important for tests)
- Stdio auth/rate limiting: `src/middleware/stdio_middleware.py` (requires `STDIO_KEY`).
- HTTP auth/rate limiting + anti-abuse checks: `src/middleware/http_middleware.py` (requires `BEARER_TOKENS`).
- Tests/integration may set `OS_MCP_AUTH_BYPASS=1` to bypass auth middleware.

## Testing + common pitfall
- Install test deps: `pip install -e .[test]`
- Run tests: `python -m pytest`
- Type check (strict): `mypy src`
- **FastMCP mocking gotcha**: when unit-testing `OSDataHubService`, set `mock_mcp.tool.return_value = lambda f: f` so the decorator does not replace async methods (see `AGENTS.md`).

## Quick run commands
- Stdio: `python -m server --transport stdio`
- HTTP: `python -m server --transport streamable-http --host 127.0.0.1 --port 8000`
- VS Code tasks: “Run MCP (stdio)” and “Run MCP (http)”
