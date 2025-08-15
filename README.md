# Ordnance Survey MCP Server

A MCP server for accessing UK geospatial data through Ordnance Survey APIs.

## What it does

Provides LLM access to the Ordnance Survey's Data Hub APIs. 

Ask simple questions such as find me all cinemas in Leeds City Centre or use the prompt templates for more complex, specific use cases - relating to street works, planning, etc.

This MCP server enforces a 2 step workflow plan to ensure that the user gets the best results possible.

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

Add the following to your Claude Desktop config:

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

### VS Code MCP Setup (Development vs Production)
You can register two entries so you always know whether you are using live source (editable) or an installed, versioned artifact:

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
3. Create or edit `~/.config/vscode/mcp/servers.json`:
```jsonc
{
  "servers": {
    "os-mcp-dev": {
      "command": "python",
  "args": ["-m", "server", "--transport", "stdio"],
      "env": { "OS_API_KEY": "${env:OS_API_KEY}", "STDIO_KEY": "dev-key" }
    },
    "os-ngd": {
      "command": "~/.local/share/os-ngd-venv/bin/python",
      "args": ["-m", "server", "--transport", "stdio"],
      "env": { "OS_API_KEY": "${env:OS_API_KEY}", "STDIO_KEY": "prod-key" }
    }
  }
}
```
4. Reload VS Code, open Copilot Chat and list tools:
```
@os-mcp-dev list tools
```
Switch to production:
```
@os-ngd list tools
```
5. List & filter prompts:
```
@os-mcp-dev call get_prompt_templates {}
@os-mcp-dev call get_prompt_templates {"category": "planning"}
```
6. Run a workflow using a prompt key (e.g. `search_cinemas_leamington`).

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

## License

MIT License. This project does not have the endorsement of Ordnance Survey. This is a personal project and not affiliated with Ordnance Survey. This is not a commercial product. It is actively being worked on so expect breaking changes and bugs.
