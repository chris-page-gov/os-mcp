# Ordnance Survey - MCP Server

VERSION: 0.1.0

A Python-based MCP server that provides access to the Ordnance Survey APIs, supporting both STDIO and HTTP (streamable) modes.

## Overview

This service creates a bridge between MCP clients and OS DataHub APIs - making it easy to query national geographic data through a standardised protocol.

It can run in two modes:

- STDIO mode: Ideal for Claude Desktop and local tool integration such as Cursor

- HTTP (streamable) mode:

## Project Structure

- **api_service** - Asynchronous HTTP client implementation for the OS APIs

  - Handles authentication, request formatting, and response processing
  - Manages rate limiting and error handling
  - Provides a clean interface to the external API endpoints

- **mcp_service** - Exposes OS APIs functionality as MCP tools

  - Converts API responses to MCP-compatible formats
  - Implements business logic for feature operations
  - Provides a standardised interface

- **middleware** - Middleware for the MCP server

  - `stdio_middleware.py`: Handles authentication for STDIO transport
  - `http_middleware.py`: Handles authentication for HTTP transport

- **prompt_templates** - Prompt templates for common operations

  - Provides pre-configured prompt templates to help you get started with some common operations

- **config_docs** - Documentation for OS APIs

  - Provides documentation for the OS APIs

- **utils** - Utility functions for the MCP server

  - Provides utility functions for the MCP server such as logging

## Features

- Collection management (listing and querying collections)
- Feature search with spatial and attribute filters
- Individual feature retrieval by ID
- Linked identifier operations
- Bulk feature operations

## Requirements

- Python 3.11+
- OS API Key (set as environment variable `OS_API_KEY`)
- You will need to register for an OS Data Hub account to get an API key

## Running the Server

### 1. Docker Mode (for Claude Desktop)

The easiest way to run the server with Claude Desktop is using Docker:

1. **Build the Docker image:**

```bash
docker build -t os-mcp-server .
```

2. **Configure Claude Desktop** by adding this to your Claude configuration:

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
        "STDIO_KEY=your-key-here",
        "-e",
        "OS_API_KEY=ADD_KEY",
        "os-mcp-server"
      ]
    }
  }
}
```

> **Note:** Leave `STDIO_KEY` as `"STDIO_KEY=your-key-here"` for now. Replace `ADD_KEY` with your actual OS API key.

### 2. STDIO Mode (for Claude Desktop)

This is the default mode, ideal for integration with Claude Desktop or other MCP hosts that use STDIO.

1. **Configure your MCP host** (e.g., in Claude Desktop's configuration):

```json
{
  "mcpServers": {
    "os-ngd-api": {
      "command": "/Users/username/.local/bin/uv",
      "args": ["--directory", "src/", "run", "server.py"],
      "env": {
        "OS_API_KEY": "your_api_key_here",
        "STDIO_KEY": "your_api_key_here"
      }
    }
  }
}
```

2. **Start the server manually** (for testing):

```bash
export OS_API_KEY=your_api_key_here
export STDIO_KEY=your_stdio_key_here
python server.py --transport stdio  # or just python server.py
```

### 3. HTTP (Streamable) Mode

This mode is ideal for web clients or when you need to stream large datasets.

You will need to set the `OS_API_KEY`and `BEARER_TOKEN` environment variables.

Each request to the MCP server will need to be authenticated with a bearer token - it's currently set to `dev-token` in the client test script.

1. **Start the server:**

```bash
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000
```

2. **Test using the provided client script:**

```bash
python src/http_client_test.py
```

> **Note:** The client test scripts (`http_client_test.py` and `stdio_client_test.py`) are a great way to verify your server setup.

### 4. Dev Container Setup (for VS Code Development)

If you're running the server in a VS Code dev container:

1. **Ensure your `.devcontainer/devcontainer.json` includes port forwarding:**

```json
{
  "image": "mcr.microsoft.com/devcontainers/python:3.11",
  "remoteUser": "vscode",
  "containerEnv": {
    "PYTHONPATH": "src",
    "OS_API_KEY": "${localEnv:OS_API_KEY}",
    "STDIO_KEY": "${localEnv:OS_API_KEY}",
    "BEARER_TOKEN": "${localEnv:BEARER_TOKEN}"
  },
  "forwardPorts": [8000],
  "portsAttributes": {
    "8000": {
      "label": "MCP Server",
      "onAutoForward": "notify"
    }
  }
}
```

2. **Start the server with host binding to all interfaces:**

```bash
PYTHONPATH=src python3 src/server.py --transport streamable-http --host 0.0.0.0 --port 8000 --debug
```

3. **Configure Claude Desktop to connect to the forwarded port:**

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

**Note:** Remove any `command` field from the Claude Desktop config when using URL-based connection.
### 5. Testing Connection

To verify your server is working correctly, you can test the connection with curl:

```bash
# Test the server is responding
curl -v http://localhost:8000/mcp/ \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "id": 1}'
```

A successful response will include initialization data and session information.

## Available Tools

All tools are available in both STDIO and HTTP modes:

- `hello_world` - Test connectivity
- `check_api_key` - Verify API key configuration
- `list_collections` - List available feature collections
- `get_collection_info` - Get details about a specific collection
- `get_collection_queryables` - Get filterable properties for a collection
- `search_features` - Search features by various criteria
- `get_feature` - Retrieve a specific feature by ID
- `get_linked_identifiers` - Find related identifiers
- `get_bulk_features` - Retrieve multiple features in a single call
- `get_bulk_linked_features` - Get linked features in bulk
- `get_prompt_templates` - Get standard prompt templates for common operations
- `search_by_uprn` - Search for addresses by UPRN
- `search_by_post_code` - Search for addresses by POSTCODE

## Using Prompt Templates

This service provides comprehensive pre-configured prompt templates to help you get started with complex geospatial analysis workflows.

To access these templates, ask Claude: **"show me available prompt templates"**

### Template Categories

#### **Basic USRN Analysis**

- `usrn_breakdown` - Break down USRN into component road links for routing analysis

## Troubleshooting

### Connection Issues

If you're having trouble connecting to the server:

1. **Check environment variables** are properly set:
   ```bash
   echo "OS_API_KEY: $OS_API_KEY"
   echo "BEARER_TOKEN: $BEARER_TOKEN"
   ```

2. **Verify port forwarding** (for dev containers):
   - Ensure port 8000 is forwarded in your devcontainer config
   - Check VS Code shows the forwarded port in the PORTS panel

3. **Test server connectivity**:
   ```bash
   # From inside container
   curl -I http://127.0.0.1:8000/mcp/
   
   # From host machine (with port forwarding)
   curl -I http://localhost:8000/mcp/
   ```

4. **Check server logs** for authentication and connection errors

### Authentication Issues

- Ensure `BEARER_TOKEN` is set to `dev-token` in your environment
- Verify the Authorization header format: `Bearer dev-token`
- Check that the token matches between client and server configuration

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

This project does not have the endorsement of Ordnance Survey.
