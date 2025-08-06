# Ordnance Survey MCP Server

A MCP server for accessing UK geospatial data through Ordnance Survey APIs.

## What it does

Provides LLM access to the Ordnance Survey's Data Hub APIs. 

Ask simple questions such as find me all cinemas in Leeds City Centre or use the prompts templates for more complex, speciifc use cases - relating to street works, planning, etc.

This MCP server enforces a 2 step workflow plan to ensure that the user gets the best results possible.

## Quick Start

### 1. Get an OS API Key

Register at [OS Data Hub](https://osdatahub.os.uk/) to get your free API key and set up a project.

### 2. Run with Docker and add to your Claude Desktop config (easiest)

```bash
Clone the repository:
git clone https://github.com/your-username/os-mcp-server.git
cd os-mcp-server
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

## Requirements

- Python 3.11+
- OS API Key from [OS Data Hub](https://osdatahub.os.uk/)
- Set a STDIO_KEY env var which can be any value for now whilst auth is improved.

## Advanced Setup (HTTP Mode)

For direct HTTP access or development setups:

### HTTP (Streamable) Mode

```bash
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

Configure for HTTP access:
```json
{
  "mcpServers": {
    "os-ngd-api": {
      "url": "http://localhost:8000/mcp/",
      "headers": {
        "Authorization": "Bearer dev-token"
      }
    }
  }
}
```

### Testing Connection

```bash
curl -v http://localhost:8000/mcp/ \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream"
```

## Troubleshooting

### Connection Issues

1. **Check environment variables** are properly set:
   ```bash
   echo "OS_API_KEY: $OS_API_KEY"
   echo "BEARER_TOKEN: $BEARER_TOKEN"
   ```

2. **Test server connectivity**:
   ```bash
   curl -I http://localhost:8000/mcp/
   ```

3. **Check server logs** for authentication and connection errors

### Authentication Issues

- Ensure `BEARER_TOKEN` is set to `dev-token` in your environment
- Verify the Authorization header format: `Bearer dev-token`

## License

MIT License. This project does not have the endorsement of Ordnance Survey. This is a personal project and not affiliated with Ordnance Survey. This is not a commercial product. It is actively being worked on so expect breaking changes and bugs.
