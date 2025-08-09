# Ordnance Survey MCP Server

A MCP server for accessing UK geospatial data through Ordnance Survey APIs.

## What it does

Provides LLM access to the Ordnance Survey's Data Hub APIs, including the comprehensive National Geographic Database (NGD).

**With PSGA (Public Service Geospatial Agreement) access:**
- Access to 50+ detailed geospatial data collections
- Complete UK street networks with attributes
- Building footprints and heights
- Land use classifications 
- Transport infrastructure (roads, railways, airports)
- Administrative boundaries at all levels
- Water features and hydrography
- Points of interest and addresses

**With Open Data access:**
- Basic street network (main roads)
- Limited points of interest
- Administrative boundaries (basic level)
- Open Names dataset

Ask simple questions such as "find me all cinemas in Leeds City Centre" or use the prompt templates for more complex, specific use cases - relating to street works, planning, etc.

This MCP server enforces a 2 step workflow plan to ensure that the user gets the best results possible.

## Quick Start

### 1. Get an OS API Key with PSGA Access

For full access to all NGD (National Geographic Database) features, you need Public Service Geospatial Agreement (PSGA) access:

#### Option A: PSGA Access (Recommended - Full Features)

**For UK Public Sector Organizations:**

1. **Register at [OS Data Hub](https://osdatahub.os.uk/)** with your official government/public sector email
2. **Select "Public Sector" during registration** to access PSGA licensing
3. **Create a new project** and select the PSGA license option
4. **Add the following APIs to your project:**
   - **OS NGD API - Features** (PSGA license)
   - **OS NGD API - Tiles** (PSGA license) 
   - **OS Places API** (PSGA license)
   - **OS Names API** (PSGA license)
   - **OS Linked Identifiers API** (PSGA license)

**PSGA provides access to:**
- Complete street network data (`trn-ntwk-street-*` collections)
- Building footprints and heights (`bld-*` collections)
- Land use classifications (`lus-*` collections)
- Administrative boundaries (`bdx-*` collections)
- Transport infrastructure (`trn-*` collections)
- Water features (`hyd-*` collections)
- Higher resolution and more detailed datasets

#### Option B: Open Data Access (Limited Features)

**For Individual/Commercial Use:**

1. **Register at [OS Data Hub](https://osdatahub.os.uk/)** with any email
2. **Create a new project** and select "Open Data" products
3. **Add these Open Data APIs:**
   - **OS NGD API - Features** (Open Data license)
   - **OS Open Names API** 
   - **OS Open Roads API**

**Open Data provides access to:**
- Basic street network (`trn-ntwk-street-1` collection only)
- Points of interest (limited set)
- Administrative boundaries (basic level)
- Open Names dataset
- Reduced detail and coverage compared to PSGA

#### Setting up your API Key:

1. **Navigate to "My Projects"** in your OS Data Hub account
2. **Click on your project name**
3. **Copy the "Project API Key"** (starts with your project name)
4. **Set as environment variable:**
   ```bash
   export OS_API_KEY="your_project_api_key_here"
   ```

#### Verifying Your Access Level:

You can check your access level by testing different collection IDs:

```bash
# Test PSGA access (will return 403 if you only have Open Data access)
curl "https://api.os.uk/features/ngd/ofa/v1/collections/trn-ntwk-street-2?key=YOUR_API_KEY"

# Test Open Data access (should work for all users)
curl "https://api.os.uk/features/ngd/ofa/v1/collections/trn-ntwk-street-1?key=YOUR_API_KEY"
```

### 2. Run with Docker and add to your Claude Desktop config (easiest)

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

### 3. ChatGPT Integration (via HTTP API)

ChatGPT doesn't have native MCP support, but you can connect it using our REST bridge:

#### Step 1: Start the Services

```bash
# Terminal 1: Start the MCP Server
cd /path/to/os-mcp
export OS_API_KEY="your_api_key_here"
export STDIO_KEY="any_value"
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8002

# Terminal 2: Start the ChatGPT Bridge
python chatgpt_bridge.py
```

This starts:
- **MCP Server** on `http://localhost:8002/mcp`
- **ChatGPT Bridge** on `http://localhost:8090`

### 3. ChatGPT Integration (via HTTP API)

ChatGPT doesn't have native MCP support, but you can connect it using our REST bridge:

#### Step 1: Start the Services

```bash
# Terminal 1: Start the MCP Server
cd /path/to/os-mcp
export OS_API_KEY="your_api_key_here"
export STDIO_KEY="any_value"
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8002

# Terminal 2: Start the ChatGPT Bridge
python chatgpt_bridge.py
```

This starts:
- **MCP Server** on `http://localhost:8002/mcp`
- **ChatGPT Bridge** on `http://localhost:8090`

#### Step 2: Use ChatGPT with Direct API Calls (Recommended)

Since ChatGPT Custom GPTs require HTTPS and external accessibility, the easiest approach is to use these methods:

**Option A: Python Code with ChatGPT Code Interpreter**
Give ChatGPT this Python code to run:

```python
import requests

# Configuration - adjust if your servers are on different ports
MCP_BASE_URL = "http://localhost:8002/mcp"
BRIDGE_BASE_URL = "http://localhost:8090"

def test_direct_mcp():
    """Test direct connection to MCP server"""
    headers = {"Authorization": "Bearer dev-token", "Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": "1", 
        "method": "tools/call",
        "params": {
            "name": "search_features",
            "arguments": {
                "collection_id": "trn-ntwk-street-1",
                "bbox": "-1.52,52.40,-1.50,52.42",
                "limit": 5
            }
        }
    }
    
    try:
        response = requests.post(MCP_BASE_URL, json=payload, headers=headers)
        print("MCP Response:", response.status_code)
        print(response.text[:500])
    except Exception as e:
        print("Error connecting to MCP server:", e)

def search_coventry_streets():
    """Search for streets in Coventry using the bridge (if working)"""
    try:
        response = requests.get(f"{BRIDGE_BASE_URL}/search/streets", 
                              params={"bbox": "-1.52,52.40,-1.50,52.42", "limit": 5})
        return response.json()
    except Exception as e:
        print("Bridge error:", e)
        return None

# Test both approaches
print("Testing MCP server directly:")
test_direct_mcp()

print("\nTesting bridge server:")
result = search_coventry_streets()
if result:
    print("Bridge working:", result)
```

**Option B: Direct curl commands with ChatGPT**
Ask ChatGPT to help you run these commands:

```bash
# Test MCP server directly
curl -X POST http://localhost:8002/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call", 
    "params": {
      "name": "search_features",
      "arguments": {
        "collection_id": "trn-ntwk-street-1",
        "bbox": "-1.52,52.40,-1.50,52.42",
        "limit": 5
      }
    }
  }'

# Test collections
curl -X POST http://localhost:8002/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2", 
    "method": "tools/call",
    "params": {
      "name": "get_collections",
      "arguments": {}
    }
  }'
```

#### Alternative: Create a Custom GPT (Advanced - Requires HTTPS Tunnel)

For advanced users who want to set up a Custom GPT:

1. **Set up an HTTPS tunnel** (required for Custom GPTs):
   ```bash
   # Install ngrok or similar
   # Point it to your bridge server on port 8090
   ```

2. **Go to the ChatGPT GPT Editor** at https://chatgpt.com/gpts/editor/
3. **Configure with the tunnel URL** in your OpenAPI specification
4. **Add Actions** → Copy and paste the corrected `chatgpt_openapi.json`

#### Step 3: Example Queries

Ask ChatGPT to help you with:
- "Use the API to find streets near London Bridge (bbox: -0.1,51.5,-0.05,51.52)"
- "Search for buildings in Manchester city centre (bbox: -2.25,53.47,-2.23,53.49)"
- "Get information about available data collections"

#### Bounding Box Examples:

- **London**: `-0.1,51.5,-0.05,51.52`
- **Manchester**: `-2.25,53.47,-2.23,53.49`
- **Birmingham**: `-1.92,52.47,-1.88,52.49`
- **Edinburgh**: `-3.21,55.94,-3.17,55.96`
- **Coventry**: `-1.52,52.40,-1.50,52.42`

### 4. VS Code Integration (Native MCP Support)

Use the provided VS Code workspace file for easy setup:

```bash
# Open the workspace in VS Code
code os-mcp-vscode.code-workspace
```

Or manually configure by adding to your VS Code `settings.json`:

```json
{
  "mcp.servers": {
    "os-mcp-server": {
      "url": "http://localhost:8000/mcp",
      "headers": {
        "Authorization": "Bearer dev-token"
      },
      "description": "UK Ordnance Survey geospatial data access"
    }
  }
}
```

Then use GitHub Copilot Chat with `@os-mcp-server` to access geospatial data.

## Requirements

- Python 3.11+
- OS API Key from [OS Data Hub](https://osdatahub.os.uk/)
- Set a STDIO_KEY env var which can be any value for now whilst auth is improved.

### PSGA Eligibility

**Who qualifies for PSGA access:**
- UK Central Government departments
- Local authorities and councils
- NHS organizations
- Police forces and emergency services
- Educational institutions (universities, schools)
- Other public sector bodies

**Benefits of PSGA vs Open Data:**
- **50+ collections** vs 5-10 open collections
- **Complete street network** with detailed attributes vs basic roads only
- **Building-level data** including heights and footprints
- **Land use classifications** for planning and development
- **Transport infrastructure** including railways, airports, bus routes
- **Higher accuracy** and more frequent updates
- **Commercial use permitted** within public sector context

**Note:** If you're not eligible for PSGA, the MCP server will still work with Open Data access, but with reduced functionality and data coverage.

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

### VS Code Integration (Native MCP Support)

VS Code now has native MCP support. To connect your OS MCP Server:

1. **Start the server in HTTP mode**:
   ```bash
   python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000
   ```

2. **Configure VS Code settings** - Add to your VS Code `settings.json`:
   ```json
   {
     "mcp.servers": {
       "os-mcp-server": {
         "url": "http://localhost:8000/mcp",
         "headers": {
           "Authorization": "Bearer dev-token"
         },
         "description": "UK Ordnance Survey geospatial data access"
       }
     }
   }
   ```

3. **Access via GitHub Copilot Chat** in VS Code:
   - Open GitHub Copilot Chat
   - Use `@os-mcp-server` to interact with the OS MCP tools
   - Ask questions like: "Find streets near Nottingham NG1 7FG"
```

### Testing Connection

Test the MCP server with your specific location (e.g., CV1 3BZ Coventry):

```bash
# Basic connectivity test
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "hello_world",
      "arguments": {"name": "CV1 3BZ User"}
    }
  }'

# Search for streets around CV1 3BZ (Coventry city centre)
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0", 
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "search_features",
      "arguments": {
        "collection_id": "trn-ntwk-street-1",
        "bbox": "-1.52,52.40,-1.50,52.42",
        "limit": 5
      }
    }
  }'
```

### VS Code Example Usage

In VS Code with GitHub Copilot Chat, you can ask natural language questions:

- `@os-mcp-server I'm at CV1 3BZ in Coventry. What streets are around here?`
- `@os-mcp-server Show me retail areas near CV1 3BZ`
- `@os-mcp-server Find transport links in Coventry city centre`

## Response Formats & Error Handling

### Success Responses
Tools return JSON (as a string over MCP) with domain-specific fields, e.g.:

```json
{"collections": [{"id": "trn-ntwk-street-1", "title": "Street Network"}]}
```

### Standardized Error Envelope (v1)
All tools now wrap failures in a consistent envelope while preserving the legacy `error` key for backward compatibility:

```json
{
  "status": "error",
  "version": 1,
  "tool": "search_features",
  "error_code": "INVALID_INPUT",
  "message": "Invalid input: Unmatched quotes in filter",
  "error": "Invalid input: Unmatched quotes in filter",  
  "details": {"raw_param": "filter value that failed"},
  "retry_guidance": {
    "tool": "search_features",
    "next_steps": [
      "Review message & adjust parameters",
      "Call get_workflow_context() for fresh collection/queryable info if unsure"
    ],
    "always_available_tools": ["get_workflow_context", "hello_world", "check_api_key"]
  }
}
```

| Field | Purpose |
|-------|---------|
| `status` | Always `error` for this envelope |
| `version` | Schema version (start at 1) |
| `tool` | Originating tool name |
| `error_code` | Machine category (`INVALID_INPUT`, `GENERAL_ERROR`, more coming) |
| `message` | Human readable explanation |
| `error` | Same as `message` (compat) |
| `details` | Extra context (may be null) |
| `retry_guidance` | Structured hints for automated or user-guided recovery |

Minimal client handling pattern:
```python
def is_error(payload: dict) -> bool:
    return payload.get("status") == "error" or ("error" in payload and "status" not in payload)

def error_message(payload: dict) -> str:
    if payload.get("status") == "error":
        return payload.get("message", payload.get("error", "Unknown error"))
    return ""
```

### Discovery Endpoints (HTTP mode)
When launched with `--transport streamable-http`:

| Endpoint | Description |
|----------|-------------|
| `/.well-known/mcp.json` | Capability + basic tool listing |
| `/.well-known/mcp-auth` | Auth scheme & rate limit hints |
| `/mcp/tools` | Full tool metadata (name + description) |
| `/mcp/status` | Uptime & lightweight health info |

Sample `/mcp/tools` response:
```json
[
  {"name": "get_workflow_context", "description": "Get basic workflow context - no detailed queryables yet"},
  {"name": "search_features", "description": "Search for features in a collection with full CQL2 filter support."}
]
```

### Tool Metadata Contract
| Key | Type | Notes |
|-----|------|-------|
| `name` | string | Stable identifier used in MCP `tools/call` |
| `description` | string | Current docstring, concise for LLM use |

### Roadmap (non-breaking planned additions)
- New `error_code` values: `RATE_LIMIT`, `AUTH_REQUIRED`, `WORKFLOW_PREREQUISITE`
- Optional `trace_id` for correlation
- Structured `hints` array (machine actionable tokens)
- Pagination envelope standardisation

If you need any of these earlier, open an issue with your use case.

## Troubleshooting

### API Key Issues (401 "Missing or unsupported API key provided")

If you're getting a 401 error, follow these steps:

#### 1. **Verify Your API Key Format**

Your OS API key should look like this format:
```
your-project-name-abc123def456ghi789jkl012mno345pqr678stu901vwx234yzab567cde890
```

**Common mistakes:**
- Using the **Project ID** instead of the **API Key**
- Using an **Application Key** instead of the **Project API Key**
- Including extra characters or spaces

#### 2. **Check Your OS DataHub Project Setup**

1. **Log into [OS DataHub](https://osdatahub.os.uk/)**
2. **Go to "My Projects"**
3. **Click on your project name**
4. **Verify these APIs are added:**
   - ✅ **OS NGD API - Features** (with correct license)
   - ✅ **OS Places API** (if using PSGA)
   - ✅ **OS Names API** (if using PSGA)

5. **Copy the "Project API Key"** (long string at the top of the project page)

#### 3. **Test Your API Key Directly**

```bash
# Replace YOUR_API_KEY with your actual key
curl "https://api.os.uk/features/ngd/ofa/v1/collections?key=YOUR_API_KEY"

# Should return JSON with available collections
# If you get 401, the API key is invalid
# If you get 403, you may need PSGA access for that collection
```

#### 4. **Environment Variable Setup**

Make sure your environment variable is set correctly:

```bash
# Check if it's set
echo "OS_API_KEY: $OS_API_KEY"

# Set it correctly (replace with your actual key)
export OS_API_KEY="your-project-name-abc123def456ghi789jkl012mno345pqr678stu901vwx234yzab567cde890"

# For permanent setup, add to your shell profile:
echo 'export OS_API_KEY="your-actual-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

#### 5. **Docker Environment Variables**

If using Docker, ensure the environment variable is passed correctly:

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
        "OS_API_KEY=your-actual-project-api-key-here",
        "-e",
        "STDIO_KEY=any_value",
        "os-mcp-server"
      ]
    }
  }
}
```

#### 6. **License Type Issues**

**If you have Open Data access but trying to access PSGA collections:**
```bash
# This will work with Open Data
curl "https://api.os.uk/features/ngd/ofa/v1/collections/trn-ntwk-street-1?key=YOUR_API_KEY"

# This requires PSGA access (will return 403 with Open Data key)
curl "https://api.os.uk/features/ngd/ofa/v1/collections/bld-fts-buildingline-1?key=YOUR_API_KEY"
```

#### 7. **Quick Diagnostic Tool**

Run the included diagnostic script to automatically check your API key:

```bash
# Make it executable and run
chmod +x diagnose_api_key.sh
./diagnose_api_key.sh
```

This will test your API key and tell you exactly what access level you have.

#### 8. **Claude Desktop Specific Issues**

If your API key works in terminal but fails in Claude Desktop:

**Claude Desktop Config Location (macOS):**
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

**For Docker setup (most common):**
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
        "OS_API_KEY=your-actual-api-key-here",
        "-e",
        "STDIO_KEY=any_value",
        "os-mcp-server"
      ]
    }
  }
}
```

**To edit your Claude config on macOS:**
```bash
# Open the config file in your default editor
open ~/Library/Application\ Support/Claude/claude_desktop_config.json

# Or edit with nano/vim
nano ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**❌ Common mistake:** Using `"OS_API_KEY=$OS_API_KEY"` instead of the actual key value
**✅ Correct:** Use your literal API key: `"OS_API_KEY=qLiLe3zOqgDFHT0iIDn1..."`

**For non-Docker setup:**
- Claude Desktop may not inherit your shell environment variables
- Set the API key directly in your system environment or Claude config
- On macOS: Add to `/etc/launchd.conf` or set in Claude Desktop preferences

#### 9. **Key Regeneration**

If your key still doesn't work:
1. **Go to your OS DataHub project**
2. **Click "Regenerate API Key"**
3. **Update your environment variables with the new key**

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
