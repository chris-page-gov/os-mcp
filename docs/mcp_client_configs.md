# MCP Server Client Configurations

This document provides configuration examples for connecting the OS MCP server to various AI clients.

## Quick Reference

| Client | Transport | Native MCP? | Config Location |
|--------|-----------|-------------|-----------------|
| Claude Code | stdio | Yes | `~/.claude.json` |
| Claude Desktop | stdio | Yes | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| VS Code | stdio | Yes | `.vscode/mcp.json` or settings |
| OpenAI | http | Bridge needed | Custom |
| Gemini | http | Bridge needed | Custom |

---

## Claude Code (CLI)

Add via command line:

```bash
claude mcp add os-mcp --scope user -- bash -c 'cd /path/to/os-mcp && OS_API_KEY=$OS_API_KEY STDIO_KEY=dev python3 -m server --transport stdio'
```

Or edit `~/.claude.json` directly:

```json
{
  "mcpServers": {
    "os-mcp": {
      "type": "stdio",
      "command": "bash",
      "args": [
        "-c",
        "cd /path/to/os-mcp && OS_API_KEY=$OS_API_KEY STDIO_KEY=dev python3 -m server --transport stdio"
      ],
      "env": {}
    }
  }
}
```

### Using Docker (devcontainer)

If running in a devcontainer:

```json
{
  "mcpServers": {
    "os-mcp": {
      "type": "stdio",
      "command": "docker",
      "args": [
        "exec", "-i", "CONTAINER_NAME",
        "bash", "-c",
        "cd /workspaces/os-mcp && python -m server --transport stdio"
      ],
      "env": {
        "OS_API_KEY": "${OS_API_KEY}",
        "STDIO_KEY": "dev"
      }
    }
  }
}
```

Replace `CONTAINER_NAME` with your devcontainer name (e.g., `reverent_sanderson`).

---

## Claude Desktop

**Config location (macOS):** `~/Library/Application Support/Claude/claude_desktop_config.json`

**Config location (Windows):** `%APPDATA%\Claude\claude_desktop_config.json`

### Direct Python (requires local install)

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "python3",
      "args": ["-m", "server", "--transport", "stdio"],
      "cwd": "/path/to/os-mcp",
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "STDIO_KEY": "dev",
        "PYTHONPATH": "/path/to/os-mcp"
      }
    }
  }
}
```

### Using Docker

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "OS_API_KEY=your-api-key-here",
        "-e", "STDIO_KEY=dev",
        "os-mcp-server"
      ]
    }
  }
}
```

Build the Docker image first:
```bash
cd /path/to/os-mcp
docker build -t os-mcp-server .
```

### Using devcontainer

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "docker",
      "args": [
        "exec", "-i", "CONTAINER_NAME",
        "bash", "-c",
        "cd /workspaces/os-mcp && python -m server --transport stdio"
      ],
      "env": {
        "OS_API_KEY": "your-api-key-here",
        "STDIO_KEY": "dev"
      }
    }
  }
}
```

---

## VS Code (Copilot Chat / MCP Extension)

**Config location:** `.vscode/mcp.json` in your workspace, or VS Code settings.

### Workspace config (`.vscode/mcp.json`)

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "python3",
      "args": ["-m", "server", "--transport", "stdio"],
      "cwd": "${workspaceFolder}",
      "env": {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "STDIO_KEY": "dev",
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

### Using Docker

```json
{
  "mcpServers": {
    "os-mcp": {
      "command": "docker",
      "args": [
        "exec", "-i", "CONTAINER_NAME",
        "bash", "-c",
        "cd /workspaces/os-mcp && python -m server --transport stdio"
      ],
      "env": {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "STDIO_KEY": "dev"
      }
    }
  }
}
```

### User settings (`settings.json`)

```json
{
  "mcp.servers": {
    "os-mcp": {
      "command": "python3",
      "args": ["-m", "server", "--transport", "stdio"],
      "cwd": "/path/to/os-mcp",
      "env": {
        "OS_API_KEY": "${env:OS_API_KEY}",
        "STDIO_KEY": "dev"
      }
    }
  }
}
```

---

## OpenAI (HTTP Transport)

OpenAI clients don't natively support MCP. Use HTTP transport with a bridge or proxy.

### Start the server in HTTP mode

```bash
cd /path/to/os-mcp
OS_API_KEY=your-api-key BEARER_TOKENS=your-bearer-token \
  python3 -m server --transport streamable-http --host 0.0.0.0 --port 8000
```

### Configuration for MCP bridge/proxy

```json
{
  "mcpServers": {
    "os-mcp": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-bearer-token"
      }
    }
  }
}
```

### Health check

```bash
curl http://localhost:8000/health
```

---

## Google Gemini (HTTP Transport)

Gemini doesn't have native MCP support. Use the same HTTP transport approach as OpenAI.

### Start the server

```bash
cd /path/to/os-mcp
OS_API_KEY=your-api-key BEARER_TOKENS=your-bearer-token \
  python3 -m server --transport streamable-http --host 0.0.0.0 --port 8000
```

### Configuration

```json
{
  "mcpServers": {
    "os-mcp": {
      "type": "http",
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer your-bearer-token"
      }
    }
  }
}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OS_API_KEY` | Yes | Ordnance Survey Data Hub API key |
| `STDIO_KEY` | Yes (stdio) | Authentication key for stdio transport |
| `BEARER_TOKENS` | Yes (http) | Comma-separated bearer tokens for HTTP transport |
| `OPENAI_API_KEY` | No | Enables experimental `chat` tool |
| `PYTHONPATH` | Recommended | Set to repo root for module resolution |

---

## Getting an OS API Key

1. Register at [OS Data Hub](https://osdatahub.os.uk/)
2. Create a new project
3. Add the "OS NGD API - Features" to your project
4. Copy the API key from your project dashboard

---

## Troubleshooting

### Server not connecting

1. Check the server starts manually:
   ```bash
   cd /path/to/os-mcp
   OS_API_KEY=your-key STDIO_KEY=dev python3 -m server --transport stdio
   ```

2. Verify dependencies are installed:
   ```bash
   pip install -e .
   ```

3. Check container is running (if using Docker):
   ```bash
   docker ps
   ```

### Tools not appearing

1. Restart your client after configuration changes
2. Check MCP status:
   - Claude Code: Run `/mcp`
   - Claude Desktop: Check MCP indicator in UI

### Authentication errors

1. Verify `OS_API_KEY` is set correctly
2. For HTTP transport, ensure `BEARER_TOKENS` matches your config
3. For stdio, ensure `STDIO_KEY` is set

---

## Available Tools

After connecting, these tools become available:

| Category | Tools |
|----------|-------|
| Geography | `select_geographic_area`, `fetch_boundaries`, `search_geographic_areas` |
| Statistics | `list_ons_datasets`, `get_dataset_info`, `get_statistics`, `compare_areas` |
| OS NGD | `search_features`, `get_feature`, `get_linked_identifiers`, `os_ngd_list_mapping_collections` |
| Routing | `get_routing_data` |
| Knowledge | `suggest_collections`, `suggest_fields` |

See the [README](../README.md) for full tool documentation.
