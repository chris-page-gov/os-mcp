# Ordnance Survey MCP Server

A MCP server for accessing UK geospatial data through Ordnance Survey APIs.

## What it does

Provides LLM access to the Ordnance Survey's Data Hub APIs. 

Ask simple questions such as find me all cinemas in Leeds City Centre or use the prompt templates for more complex, specific use cases - relating to street works, planning, etc.

This MCP server enforces a 2 step workflow plan to ensure that the user gets the best results possible.

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

Open Claude Desktop and you should now see all available tools, resources, and prompts.

### VS Code MCP (Experimental) Setup
1. Create `~/.config/vscode/mcp/servers.json`:
```jsonc
{
  "servers": {
    "os-ngd": {
      "command": "python",
      "args": ["-m", "server", "--transport", "stdio"],
      "env": {"OS_API_KEY": "${env:OS_API_KEY}", "STDIO_KEY": "dev"}
    }
  }
}
```
2. Start VS Code, open Copilot Chat, and issue:
```
@os-ngd list tools
```
3. List prompts:
```
@os-ngd call get_prompt_templates {}
```
4. Filter prompts (e.g. planning):
```
@os-ngd call get_prompt_templates {"category": "planning"}
```
5. Execute a workflow using a prompt key (e.g. `search_cinemas_leamington`).

See `docs/mcp_integration.md` for full guidance, including routing and diagnostics prompts.

### HTTP Health Check
If you run the HTTP transport:
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

For a full cURL tutorial of the MCP /mcp endpoint, see `docs/http_usage.md`.

## Frontend (Experimental)
A browser UI scaffold (React + Vite + TypeScript + Leaflet) lives in `frontend/` providing:
- Tutorial prompt chips
- Chat panel (local only for now)
- Output panel with Answer / Map / Data tabs

MVP design goals & roadmap are documented in `docs/frontend_mvp.md`.

Run it locally (against a running HTTP MCP server):
```bash
# In one terminal: start MCP HTTP server
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

## Development

Python tests:
```bash
pytest
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

## License

MIT License. This project does not have the endorsement of Ordnance Survey. This is a personal project and not affiliated with Ordnance Survey. This is not a commercial product. It is actively being worked on so expect breaking changes and bugs.
