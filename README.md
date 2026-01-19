# Ordnance Survey MCP Server

A MCP server for accessing UK geospatial data through Ordnance Survey APIs.

## What it does

Provides LLM access to the Ordnance Survey's Data Hub APIs. 

Ask simple questions such as find me all cinemas in Leeds City Centre or use the prompt templates for more complex, specific use cases - relating to street works, planning, etc.

This MCP server enforces a 2 step workflow plan to ensure that the user gets the best results possible.

## Getting Started

**New to OS MCP?** Start with the **[User Tutorial](docs/tutorial.md)** - a hands-on guide covering:
- Setup for Claude Desktop, Claude Code CLI, and Cowork
- 8 progressive exercises from basic queries to advanced workflows
- Interactive widget demonstrations
- Troubleshooting and quick reference

## MCP-Apps Integration (Complete)

Interactive UI widgets make this an exemplary MCP-Apps implementation. See the documentation:

- **[User Tutorial](docs/tutorial.md)** - Hands-on getting started guide
- **[MCP Apps Guide](docs/mcp_apps_guide.md)** - Detailed widget documentation
- **[Skills Reference](SKILL.md)** - Complete tool and workflow reference
- **[Design Document](plans/os-mcp-apps-design.md)** - Architecture and widget specifications
- **[Progress Tracker](plans/PROGRESS.md)** - Implementation status (all sprints complete)

### Implementation Progress

| Sprint | Focus | Status | Key Deliverables |
|--------|-------|--------|------------------|
| 1 | MCP-Apps Foundation | ✅ Complete | Directory structure, UI resources, geography tools |
| 2 | Selection Flow | ✅ Complete | Postcode search, ONS API integration, widget polish |
| 3 | ONS Statistics | ✅ Complete | ONS API client, statistics tools, 42 new tests |
| 4 | Statistics Dashboard | ✅ Complete | Chart.js widget, data visualization, export |
| 5 | Enhanced Features | ✅ Complete | Feature inspector, route planner, cross-widget communication |
| 6 | Polish & Release | ✅ Complete | 320+ tests, >80% coverage, Docker, CI/CD |
| 7 | Tool Search | ✅ Complete | defer_loading, MCP toolset integration |
| 8 | Architecture Review | ✅ Complete | Query router, 38 tools (6 always-loaded, 32 deferred), evaluation framework |

### New Geography Tools (Sprint 1-2)

Three new tools for UK geographic boundary selection (bypass workflow context):

| Tool | Description |
|------|-------------|
| `select_geographic_area` | Opens interactive map widget for area selection (supports focus_level/focus_name) |
| `fetch_boundaries` | Fetches GeoJSON boundaries from ONS Geography API |
| `search_geographic_areas` | Searches UK areas by name |

Supported geographic levels: Parliamentary Constituencies, Local Authority Districts, Wards, LSOA, MSOA, Output Areas.
Use `focus_level` + `focus_name` to zoom to a larger area before selecting smaller areas (e.g., select OAs within Coventry West).

### New Statistics Tools (Sprint 3-4)

Four new tools for ONS statistics data (bypass workflow context):

| Tool | Description |
|------|-------------|
| `list_ons_datasets` | Lists available ONS datasets with category/search filters |
| `get_dataset_info` | Gets detailed metadata for a specific dataset |
| `get_statistics` | Retrieves statistical observations for geographic areas |
| `compare_areas` | Compares statistics across multiple areas |

Available dataset categories: wellbeing, economy, housing, population, health, employment, census.
The internal ONS client runs under an async context manager and raises `ONSAPIError` on connection failures.

The statistics dashboard widget (`ui://os-ons/statistics-dashboard`) provides:
- Chart.js line and bar chart visualizations
- Summary statistics cards
- Area comparison tables with rankings
- CSV, JSON, and clipboard export

### Enhanced Feature Tools (Sprint 5)

**Feature Inspector** - Detailed feature exploration with linked identifiers:

| Tool | Description |
|------|-------------|
| `inspect_feature` | Opens feature inspector widget with UI resource reference |
| `get_feature_with_linked` | Prepares feature data with linked identifiers (TOID, UPRN, USRN) |

The feature inspector widget (`ui://os-ons/feature-inspector`) provides:
- Properties table with filtering and type-aware formatting
- Leaflet map visualization of feature geometry
- Linked identifiers display with tabbed navigation
- Click-to-navigate between linked features
- Export functionality (JSON, CSV, clipboard)

**Route Planner** - Interactive route planning:

| Tool | Description |
|------|-------------|
| `plan_route` | Opens route planner widget with optional preset start/end points |
| `get_route_network` | Gets road network data for a bounding box |

The route planner widget (`ui://os-ons/route-planner`) provides:
- Map-based start/end point selection with draggable markers
- Waypoint support for multi-stop routes
- Turn-by-turn directions display
- Route summary (distance, estimated time, segments)

**Cross-Widget Communication** - Share selections across widgets:

| Tool | Description |
|------|-------------|
| `get_shared_context` | Gets current cross-widget shared state |
| `update_shared_context` | Adds/removes/clears selections in shared context |
| `share_selection` | Shares selection from one widget to another |

### Experimental Chat Tool
If you set `OPENAI_API_KEY` (and optionally `OPENAI_MODEL`), an additional `chat` MCP tool becomes available. This tool:
- Bypasses the workflow-context requirement (you can call it first).
- Accepts `messages` (list/dict or JSON string) mirroring OpenAI Chat API format.
- Returns a JSON object with `model`, `output`, and optional `usage` fields.

Example (VS Code MCP chat):
```
@os-ngd call chat {"messages": [{"role": "user", "content": "Summarise how to find cinema sites using the tools."}]}
```
Use it for high‑level reasoning, drafting complex multi-step plans, or exploratory Q&A before executing data tools. It does NOT access OS data directly—combine with the workflow plan + data tools for real results.

## Quick Start

### 1. Get an OS API Key

Register at [OS Data Hub](https://osdatahub.os.uk/) to get your free API key and set up a project.

### 2. Run with Docker (Claude Desktop) or VS Code MCP Chat

```bash
# Clone the repository:
git clone https://github.com/chris-page-gov/os-mcp.git
cd os-mcp
```

Then build the Docker image:

```bash
docker build -t os-mcp-server .
```

Add the following to your Claude Desktop config (STDIO transport – simplest / default):

```json
{
  "mcpServers": {
    "os-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-e",
        "OS_API_KEY=your_api_key_here",
        "-e",
        "STDIO_KEY=any_value",
        "os-mcp-server"
      ]
    }
  }
}
```

Open Claude Desktop and you should now see all available tools, resources, and prompts (including `chat` if `OPENAI_API_KEY` is set).

#### Optional: Run the HTTP transport in Docker (expose on 127.0.0.1)
Claude Desktop today primarily connects over stdio. If you also want an HTTP endpoint (e.g. for the experimental frontend or scripted cURL usage) alongside Claude, run a second container exposing port 8000:

```bash
docker run \
  --rm \
  -p 8000:8000 \
  -e OS_API_KEY=your_api_key_here \
  -e BEARER_TOKENS=dev-token \
  os-mcp-server \
  python -m server --transport streamable-http --host 0.0.0.0 --port 8000
```

Test from the host:
```bash
curl -s http://127.0.0.1:8000/health
curl -s -H 'Authorization: Bearer dev-token' http://127.0.0.1:8000/.well-known/mcp-auth
```

You can keep the stdio (Claude) container and the HTTP container separate (recommended) or run only the HTTP one if your client supports HTTP MCP directly. The stdio example above remains the canonical Claude configuration.

### VS Code MCP Setup (Development vs Production)
This repository now ships with a workspace MCP configuration in `.vscode/settings.json` so you do **not** need to create a user‑level `~/.config/vscode/mcp/servers.json` for normal development. Opening the repo in VS Code automatically registers (and can auto‑start) the dev stdio server and provides an HTTP entry.

You can still register two entries (dev + prod) if you want to compare an installed wheel with the live editable code. The built‑in workspace config already covers the editable/dev case.

| Name | Purpose | Command | Args |
|------|---------|---------|------|
| `os-mcp-dev` | Live editable repo (after `pip install -e .`) | python | -m server --transport stdio |
| `os-ngd` | Installed wheel (built artifact) | python | -m server --transport stdio |

1. (Dev) Install in editable mode:
```bash
pip install -e .[test]
```
2. (Optional Prod) Build & install a wheel into a separate venv:
```bash
python -m pip install --upgrade build
python -m build
python -m venv ~/.local/share/os-ngd-venv
~/.local/share/os-ngd-venv/bin/pip install dist/os_mcp-*.whl
```
3. (Optional) User‑level config: Only if you want additional named entries beyond what the workspace provides (e.g. a production wheel). Create or edit `~/.config/vscode/mcp/servers.json` (Linux) or the equivalent on your platform and add an `os-ngd` entry as shown below. Keep the dev entry only if you prefer user‑level management instead of the workspace file.

4. Reload VS Code, open Copilot Chat and list tools (workspace dev entry example):
```
@os-mcp-stdio list tools
```
5. List & filter prompts:
```
@os-mcp-stdio call get_prompt_templates {}
@os-mcp-stdio call get_prompt_templates {"category": "planning"}
```
6. Run a workflow using a prompt key (e.g. `search_cinemas_leamington`).

#### Fast Dev Smoke Test (No VS Code UI)
Use the helper script to launch a temporary stdio server and list tools:
```bash
./scripts/dev_stdio_list_tools.sh
```
Expected output includes `Tool count: 22` (number may grow as tools are added) followed by the tool names.

See `docs/mcp_integration.md` for expanded guidance (routing, diagnostics, planning heuristics) and an HTTP transport variant.

### HTTP Health Check
If you run the HTTP transport (from the repo root without installing the package):
```
python -m server --transport streamable-http --host 127.0.0.1 --port 8000
```
You can verify the server is up (no auth required):
```
curl -s http://127.0.0.1:8000/health
```
Response:
```
{"status":"ok"}
```

#### Favicon & static assets
The server now serves a tiny static `/favicon.ico` (transparent PNG) without requiring authentication. This prevents noisy 401 warnings in logs from automatic browser favicon requests. The asset is intentionally minimal and contains no sensitive data; exposing it publicly is standard practice and poses no security risk. All other routes (except `/.well-known/mcp-auth` and `/health`) still require a valid bearer token when using the HTTP transport.

For a full cURL tutorial of the MCP /mcp endpoint, see `docs/http_usage.md`.

## Frontend (Experimental)
A browser UI scaffold (React + Vite + TypeScript + Leaflet) lives in `frontend/` providing:
- Tutorial prompt chips
- Chat panel (local only for now)
- Output panel with Answer / Map / Data tabs
- Automatic GeoJSON detection: FeatureCollections added as map layers
- Layer visibility toggling & removal (Data tab legend)

MVP design goals & roadmap are documented in `docs/frontend_mvp.md`.

Run it locally (against a running HTTP MCP server) — be sure to export a bearer token or every /mcp request will 401:
```bash
# In one terminal: start MCP HTTP server (export token first)
export BEARER_TOKENS=dev-token
python -m server --transport streamable-http --host 127.0.0.1 --port 8000
# In another terminal: start frontend dev server
cd frontend
npm install
npm run dev
# Open the printed localhost URL (typically http://localhost:5173)
```
The scaffold currently does not yet stream live MCP calls—gateway / SSE wiring is planned. Map tab initializes only when opened.

## Requirements

- Python 3.11+
- OS API Key from [OS Data Hub](https://osdatahub.os.uk/)
- Set a STDIO_KEY env var (any value currently) for stdio auth
- (Frontend) Node 18+ & npm if you want to run the experimental UI

### Environment Variable Sources (Devcontainer vs Local .env)
This project primarily injects environment variables via the devcontainer configuration (`.devcontainer/devcontainer.json`), **not** the root `.env` file. The `.env` file is illustrative only (ignored by git) and not automatically loaded by the server.

Priority / resolution order at runtime:
1. Explicit process environment (e.g. exported in your shell, or set in VS Code Run/Debug configuration).
2. Devcontainer `containerEnv` and MCP server `env` blocks (these forward selected host variables on rebuild).
3. (Optional) Manual `export VAR=value` inside the container shell before launching `python -m server`.

Variables in use:
- `OS_API_KEY` – required OS Data Hub key.
- `STDIO_KEY` – required for stdio transport auth (simple shared secret, any non-empty value in dev).
- `BEARER_TOKENS` – comma-separated list of allowed HTTP Bearer tokens.
- `BEARER_TOKEN` (legacy) – deprecated; only used if `BEARER_TOKENS` unset. Will be removed in >=0.2.0.
- `OPENAI_API_KEY` – enables experimental `chat` MCP tool (set to activate). Optional `OPENAI_MODEL` to override default model (gpt-4o-mini).
- `OS_MCP_AUTH_BYPASS` – test-only bypass for HTTP auth/rate limits (values: 1/true/yes).
- `ALLOWED_ORIGINS` – optional comma list of additional allowed origins beyond localhost.
 - `OS_MCP_CA_BUNDLE` – path to a custom PEM bundle (corporate / intercepting proxy root cert) to trust for outbound HTTPS (aiohttp SSL context).
 - `OS_MCP_SSL_NO_VERIFY` – development override (1/true/yes) to disable TLS certificate verification entirely (avoid in production; logs will warn when set).

To change values persistently, edit `.devcontainer/devcontainer.json` then rebuild the container. For one-off testing, simply `export` them in the integrated terminal prior to running the server.

## Development

Python tests (explicit path for some environments):
```bash
pytest tests
```
With coverage report:
```bash
pytest --cov=src --cov=tests --cov-report=term-missing
```
Type checking:
```bash
mypy src
```
Frontend build:
```bash
cd frontend
npm run build
```

### Test Coverage Mapping
The test suite intentionally exercises every documented server capability:
| README Feature / Section | Test File(s) / Marker |
|--------------------------|-----------------------|
| Two‑step workflow enforcement (`WORKFLOW_CONTEXT_REQUIRED`) | `tests/test_service_additional.py::test_search_features_requires_workflow_context` |
| Invalid / diagnostic envelopes (`INVALID_COLLECTION`) | `tests/test_service_additional.py::test_search_features_invalid_collection_envelope` |
| Queryables + detailed collections | `tests/test_os_service_search_and_features.py::test_fetch_detailed_collections_requires_planner` |
| Bulk + single feature retrieval | `tests/test_os_service_search_and_features.py::test_get_bulk_features_mixed_modes`, `...::test_get_feature_upstream_error` (error path) |
| Linked identifiers + bulk links | `tests/test_service_additional.py::test_linked_identifiers_filtering` |
| Routing data tool | `tests/test_routing_service_network.py` |
| Structured error envelope shape | `tests/test_error_envelope_build.py` |
| Request ID middleware | `tests/test_request_id_logging.py` |
| Auth (bearer / stdio) & HTTP middleware | `tests/test_http_middleware_security.py`, `tests/test_middleware.py` |
| Health/version endpoints (prod build) | `tests/test_production_instance.py::test_production_health_and_version` |
| Version info MCP tool | `tests/test_version_info_tool.py` |
| Prompt templates & category filtering | `tests/test_prompt_categories.py`, `tests/test_warwickshire_prompts.py` |
| Equivalence vs OS API (parity) | `tests/test_equivalence_os_api.py`, `tests/test_os_service_search_and_features.py` |
| Chat tool (experimental) | `tests/test_chat_tool.py` |
| Stdio rate limiting (smoke) | `tests/integration/test_stdio_client.py` |
| Favicon / static asset exposure | `tests/test_favicon.py` |
| HTTP /mcp security (bearer required) | `tests/test_http_middleware_security.py` |

Slow / build heavy production instance test is gated by `OS_MCP_RUN_SLOW=1` (see `tests/test_production_instance.py`).

### Running Tests Inside the Devcontainer
The devcontainer already installs dependencies with test extras. Typical flows:
```bash
# All fast tests
pytest -q

# Include slow production build test
OS_MCP_RUN_SLOW=1 pytest -q tests/test_production_instance.py::test_build_and_install_wheel

# Coverage (backend focus)
pytest --cov=src --cov=tests --cov-report=term-missing
```

### Lint / Type Strictness
`mypy --strict` is enforced in CI (see `pyproject.toml` for strict flags). Any new public API or tool should include minimal tests plus type annotations to keep this passing.

### Frontend Development (Container)
Node 20 is available in the devcontainer. To iterate:
```bash
cd frontend
npm install
npm run dev
```
The frontend currently relies on a locally running HTTP MCP server (start with `BEARER_TOKENS=dev-token python -m server --transport streamable-http --host 127.0.0.1 --port 8000`). SSE streaming is planned; current tests mock core logic and GeoJSON parsing.

### Adding a New Tool (Guide)
1. Add implementation to `mcp_service/os_service.py`.
2. Register it on the `FastMCP` instance (follow existing pattern).
3. Create unit tests covering success + 1 error path.
4. (If external API call) add to equivalence parity tests if applicable.
5. Update this README & CHANGELOG (Unreleased).
6. Optionally extend prompt templates referencing the new tool; add template test.

### Environment Consistency
Within the devcontainer the following are pre-set (see `.devcontainer/devcontainer.json`): `OS_API_KEY`, `STDIO_KEY`, `BEARER_TOKENS`, `OPENAI_API_KEY` (forwarded if present). Override any temporarily via `export VAR=...` before running tests or server. No `.env` auto‑loading is performed.

## Test Suite Status
Active test coverage includes routing, error envelopes, authentication paths, prompt category filtering, linked identifiers, chat tool, and frontend logic (planning heuristic, MCP tool wrapper, GeoJSON detection, layer toggling/removal). Current counts: backend 52 + frontend 20 = 72 passing tests as of 2025‑08‑11.

### Troubleshooting: ModuleNotFoundError 'src.server'
If you previously configured VS Code (or another MCP client) with `-m src.server` you may now see:
```
ModuleNotFoundError: No module named 'src'
```
Cause: Modern invocation relies on the installed package layout; `src` is not on `PYTHONPATH` in many runtime contexts (especially remote containers / production venvs). The project now standardizes on:
```
python -m server --transport stdio
```
or HTTP:
```
python -m server --transport streamable-http --host 127.0.0.1 --port 8000
```
Fix Steps:
1. Open your `~/.config/vscode/mcp/servers.json` (or equivalent) and replace any `"-m", "src.server"` args with `"-m", "server"`.
2. Remove obsolete devcontainer `customizations.vscode.mcp.servers` blocks or local tasks referencing `src.server` (these were removed in 0.1.13).
3. Reload VS Code and run `@os-mcp-dev list tools`.
4. (Optional) Verify Docker / deployment scripts also use `-m server`.
Result: Single, reliable entrypoint across editable (`pip install -e .`) and wheel installs.

### Troubleshooting: TLS / Corporate Proxy Certificates
If you see HTTPS errors such as:
```
SSL: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate
```
or `curl` shows `certificate has unknown CA`, your environment is likely behind a corporate / intercepting proxy that resigns TLS with an internal root certificate **not** present in the container image.

There are three supported remediation paths (prefer 1):

1. Install the corporate root CA into the container trust store (secure, persistent):
  - Place the PEM (or convert DER to PEM) in `certs/corporate-root.pem` (directory is git‑ignored; never commit real certs).
  - Run: `./scripts/setup_corp_ca.sh certs/corporate-root.pem`
  - The script copies it to `/usr/local/share/ca-certificates/` and runs `update-ca-certificates` so future `python -m server` and `curl` calls succeed.
2. Provide a one‑off custom bundle without modifying global trust (scoped to this server process):
  - Export: `export OS_MCP_CA_BUNDLE=/workspace/os-mcp/certs/corporate-root.pem`
  - Start the server; the client session builds an `ssl.SSLContext` with that bundle only.
3. (Last resort) Temporarily disable verification for debugging ONLY:
  - `export OS_MCP_SSL_NO_VERIFY=1`
  - Start the server; outbound requests skip certificate validation (MITM / tampering risks). Remove as soon as the root cause is fixed.

Detection / confirmation steps inside the devcontainer:
```bash
curl -v https://api.os.uk/places/v1/health 2>&1 | grep -i 'certificate' || true
python - <<'PY'
import ssl, certifi, os
print('Default CA count:', len(open(certifi.where(),'rb').read().split(b'-----END CERTIFICATE-----')))
print('OS_MCP_CA_BUNDLE:', os.environ.get('OS_MCP_CA_BUNDLE'))
print('OS_MCP_SSL_NO_VERIFY:', os.environ.get('OS_MCP_SSL_NO_VERIFY'))
PY
```

Security Notes:
- Prefer installing / supplying the real corporate root (options 1 or 2). They retain end‑to‑end validation properties.
- Option 3 (`OS_MCP_SSL_NO_VERIFY`) should never ship to production, CI, or shared environments. Add it only to a local shell, not to `devcontainer.json`.
- The `certs/` directory is ignored by git (see `.gitignore`) so you can safely stage local corporate certificates without risk of accidental commit.

If you rotate corporate roots, re-run the setup script with the new file and restart the container or server.

### Differentiating Dev vs Prod Names
You can optionally set a custom server display name (e.g. to show both dev + prod simultaneously) via:
```
export OS_MCP_SERVER_NAME=os-mcp-dev
python -m server --transport stdio
```
If unset it defaults to `os-ngd-api`. Register two entries pointing at the same code but with different `env` blocks setting `OS_MCP_SERVER_NAME` to keep them distinct in the VS Code MCP Servers panel.

### Building a Production STDIO Environment Inside the Devcontainer
Create an immutable (wheel-installed) environment alongside your editable dev install:
```bash
./scripts/build_prod_stdio.sh   # builds wheel + venv at ~/.local/share/os-ngd-prod
```
The script prints a JSON snippet for your container user MCP config (e.g. `/home/vscode/.vscode-server/data/User/mcp.json`). Example entry:
```jsonc
{
  "os-ngd-prod": {
    "command": "/home/vscode/.local/share/os-ngd-prod/bin/python",
    "args": ["-m", "server", "--transport", "stdio"],
    "env": {
      "OS_API_KEY": "${env:OS_API_KEY}",
      "STDIO_KEY": "prod-key",
      "OS_MCP_SERVER_NAME": "os-ngd-prod"
    }
  }
}
```
Next steps to use the production instance:
1. Add/update the snippet in your container user MCP config (path typically `/home/vscode/.vscode-server/data/User/mcp.json`).
2. Reload the VS Code window so it picks up the new entry: Command Palette (Ctrl/Cmd+Shift+P) → "Developer: Reload Window".
3. Start the server in one of these ways:
  - Command Palette → "Model Context Protocol: Start Server" → select `os-ngd-prod`
  - MCP Servers view (if enabled) → click the ▶ start button next to `os-ngd-prod`
  - Open a chat and reference a tool from `os-ngd-prod` (auto-starts)
4. Verify it started: View → Output → dropdown: Model Context Protocol / os-ngd-prod (look for startup log) or list tools (`@os-ngd-prod list tools`).

Troubleshooting: If it fails to start, ensure `OS_API_KEY` is available in the container environment. For a quick test you can replace `${env:OS_API_KEY}` with a literal key string in the config (remember to revert afterwards).

Re-run the script after code changes (and version bump) to refresh the production venv:
```bash
./scripts/build_prod_stdio.sh && echo "Prod venv refreshed"
```

### Manual STDIO Smoke Test (Production Wheel)

Quickly verify the production wheel install works end‑to‑end without a GUI MCP client.

1. (Re)build the production venv if needed:
  ```bash
  ./scripts/build_prod_stdio.sh
  ```
2. Launch the production stdio server (foreground) in one terminal using the helper:
  ```bash
  ./scripts/run_prod_stdio.sh
  ```
  Add `--debug` for verbose logging.
3. In a second terminal list tools via a tiny Python client:
  ```bash
  PROD_VENV="$HOME/.local/share/os-ngd-prod" python - <<'PY'
import asyncio, os
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main():
   params = StdioServerParameters(
      command=os.path.join(os.environ["PROD_VENV"], "bin", "os-mcp"),
      args=["--transport", "stdio"],
      env={
        "STDIO_KEY": os.environ.get("STDIO_KEY", "dev-key"),
        "OS_MCP_MODE": "prod",  # explicit override (optional)
      },
   )
   async with stdio_client(params) as (r, w):
      async with ClientSession(r, w) as session:
        await session.initialize()
        tools = await session.list_tools()
        print("Tool count:", len(tools.tools))

asyncio.run(main())
PY
  ```
4. Expected: client prints `Tool count: <n>` and server logs include `Processing request of type ListToolsRequest`.

If you see `command not found: os-mcp`, re-run the build script and confirm `${HOME}/.local/share/os-ngd-prod/bin/os-mcp` exists. If the server appears to "hang" after startup logs, it is waiting for JSON‑RPC input—use the Python snippet above instead of manual typing.


### Note on `${env:...}` Placeholders in Shell Scripts
VS Code MCP configs often use `${env:VAR_NAME}` syntax (resolved by VS Code, not the shell). When authoring Bash scripts with `set -u` (treat unset vars as errors), an unescaped `${env:OS_API_KEY}` inside a heredoc will be interpreted by Bash and trigger an `unbound variable` error because `env` is not defined as a shell variable.

Safe patterns:
1. Escape the first `$`: `\${env:OS_API_KEY}` inside the heredoc.
2. Assign a literal once and reuse it: `PLACEHOLDER='${env:OS_API_KEY}'` then reference `$PLACEHOLDER` in emitted JSON.
3. For comments, also escape: `# uses \${env:OS_API_KEY}`.

Avoid placing raw `${env:` tokens directly in shell heredocs under `set -u` unless escaped or wrapped as above. A helper script `scripts/check_env_placeholders.sh` enforces this to prevent regressions.

## License

MIT License. This project does not have the endorsement of Ordnance Survey. This is a personal project and not affiliated with Ordnance Survey. This is not a commercial product. It is actively being worked on so expect breaking changes and bugs.
