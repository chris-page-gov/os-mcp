# Ordnance Survey MCP Server

A smart MCP server for accessing UK geospatial data through Ordnance Survey APIs.

## What it does

- **Smart workflow**: Automatically discovers what data is available and how to filter it
- **Collection-specific filtering**: Uses exact enum values for precise queries (e.g., find all 'Cinema' locations or 'A Road' streets in this particular area)
- **Intelligent planning**: Guides you through the best approach for your geospatial queries

## Quick Start

### 1. Get an OS API Key

Register at [OS Data Hub](https://osdatahub.os.uk/) to get your free API key.

### 2. Run with Docker (easiest)

```bash
# Build
docker build -t os-mcp-server .

# Add to your Claude Desktop config:
{
  "mcpServers": {
    "os-mcp-server": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "-e", "OS_API_KEY=your_api_key_here",
        "-e", "STDIO_KEY=any_value",
        "os-mcp-server"
      ]
    }
  }
}
```

## How it works

```
1. Ask a question
   ↓
2. Server gets workflow context (collections + filtering options)
   ↓
3. Smart planning: "I'll search the 'lus-fts-site-1' collection
   using filter 'oslandusetertiarygroup = \"Cinema\"'"
   ↓
4. Precise results using collection-specific enum values
```

## Data Flow

```
User Request
    ↓
get_workflow_context() ← [REQUIRED FIRST]
    ↓
Collection Discovery (streets, buildings, land use, etc.)
    ↓
Queryables Discovery (enum values: 'Cinema', 'A Road', etc.)
    ↓
Smart Query Construction based on LLM's plan
    ↓
search_features(filter="oslandusetertiarygroup = 'Cinema'")
    ↓
OS Data Hub APIs
    ↓
Results returned to user
```

## Available Tools

**Core workflow:**

- `get_workflow_context` - [Required first] Get collections and filtering options
- `search_features` - Search with intelligent filtering using collection-specific enum values

**Additional tools:**

- `get_collection_info` - Collection details
- `get_collection_queryables` - Available filters for a collection
- `get_feature` - Get specific feature by ID
- `hello_world` - Test connectivity
- `check_api_key` - Verify setup

## Key Benefits

- **No guessing**: Server tells you exactly what enum values are available
- **Precise filtering**: Use exact values like `'Cinema'`, `'A Road'`, `'Open'`
- **Collection-aware**: Each collection (streets, buildings, land use) has its own filtering options
- **Enforced planning**: Prevents mistakes by requiring context first

## Requirements

- Python 3.11+
- OS API Key from [OS Data Hub](https://osdatahub.os.uk/)

## License

MIT License. This project does not have the endorsement of Ordnance Survey. This is a personal project and not affiliated with Ordnance Survey. This is not a commercial product. It is actively being worked on so expect breaking changes and bugs.
