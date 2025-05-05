# OS NGD Features API - MCP Server

A Python-based MCP server that provides access to the Ordnance Survey National Geographic Database (NGD) Features API.

## Overview

This service creates a bridge between MCP clients and the OS NGD Features API, making it easy to query geographic data through a standardised protocol.

The service handles authentication, (basic) rate limiting, and provides a simplified interface to the complex OS API.

## Project Structure

- **api_service** - HTTP client implementation for the OS NGD Features API

  - Handles authentication, request formatting, and response processing
  - Manages rate limiting and error handling
  - Provides a clean interface to the external API endpoints

- **mcp_service** - Exposes OS NGD API functionality as MCP tools

  - Converts API responses to MCP-compatible formats
  - Implements business logic for feature operations
  - Provides a standardized interface for other services

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
- Dependencies: aiohttp, mcp[cli]

## Usage

Configure in your MCP host configuration file (e.g Claude Desktop):

```json
{
  "mcpServers": {
    "os-ngd-api": {
      "command": "/Users/username/.local/bin/uv",
      "args": ["--directory", "src/", "run", "main.py"],
      "env": {
        "OS_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

## Claude Desktop Integration

This MCP service has only been tested with Claude Desktop.

The aim is to make this service work with various MCP hosts/clients, but this has not been tested yet.

When using with Claude Desktop:

1. Ensure Claude Desktop is configured to access local tools
2. The service will be available as a tool once it's running
3. No additional network configuration is needed

## Available Tools

All of this is a work in progress, but the following tools are available:

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

## Using Prompt Templates

This service provides pre-configured prompt templates to help you get started.

To access these templates ask Claude "show me available prompt templates"

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

This project does not have the endorsement of Ordnance Survey.
