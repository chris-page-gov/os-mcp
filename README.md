# Ordnance Survey - MCP Server

VERSION: 0.1.2

A Python-based MCP server that provides access to the Ordnance Survey APIs, supporting both STDIO and HTTP (streamable) modes.

## Overview

This service creates a bridge between MCP clients and OS DataHub APIs - making it easy to query national geographic data through a standardised protocol.

It can run in two modes:

- STDIO mode: Ideal for Claude Desktop and local tool integration such as Cursor

- HTTP (streamable) mode: Perfect for web clients/applications

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

### 1. STDIO Mode (for Claude Desktop)

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

### 2. HTTP (Streamable) Mode

This mode is ideal for web clients or when you need to stream large datasets.

You will need to set the `OS_API_KEY`and `BEARER_TOKEN` environment variables.

Each request to the MCP server will need to be authenticated with a bearer token - it's currently set to `dev-token` in the client test script.

1. **Start the server:**

```bash
python src/server.py --transport streamable-http --host 127.0.0.1 --port 8000
```

2. **Test using the provided client script:**

```bash
python src/client_test.py
```

> **Note:** The client test script (`client_test.py`) is a great way to verify your server setup and see example code for programmatic interaction with the API. It uses the `mcp.client.streamable_http` library to demonstrate proper connection handling and tool calling.

The client script demonstrates:

- Connecting to the MCP server
- Initialising a session
- Listing available tools
- Making test calls (e.g., `hello_world` tool)

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
- `get_map_tile` - Get a map tile in EPSG:27700 projection - THIS DOES NOT WORK - NEED TO FIX

## Using Prompt Templates

This service provides pre-configured prompt templates to help you get started.

To access these templates ask Claude "show me available prompt templates"

Current prompt templates are:

- `connected_usrns` - Find all USRNs that are directly connected to a given USRN

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License.

This project does not have the endorsement of Ordnance Survey.
