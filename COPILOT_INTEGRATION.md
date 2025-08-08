# OS MCP Server - Copilot Integration Guide

This guide explains how to install, configure, and integrate the OS MCP Server with Microsoft Copilot Studio to enable geospatial data access for UK Ordnance Survey data.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Copilot Studio Integration](#copilot-studio-integration)
- [Testing the Integration](#testing-the-integration)
- [Available Tools](#available-tools)
- [Usage Examples](#usage-examples)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)

## 🌍 Overview

The OS MCP Server provides access to UK Ordnance Survey geospatial data through the Model Context Protocol (MCP). This enables Copilot to search for streets, buildings, addresses, land use data, and more across the UK using natural language queries.

### Key Features:
- 🗺️ **Geospatial Search**: Streets, buildings, addresses, land use data
- 📍 **Location-based Queries**: Search by postcode, coordinates, or bounding box
- 🔍 **Advanced Filtering**: CQL (Common Query Language) support
- 🚀 **Real-time Data**: Direct access to OS DataHub APIs
- 🔐 **Secure**: Bearer token authentication with rate limiting

## 📚 Prerequisites

### System Requirements
- **Python 3.11+** installed and accessible
- **Network access** to OS DataHub APIs (`api.os.uk`)
- **Port 8000** available for the MCP server (configurable)

### API Access
- **OS DataHub Account**: Sign up at [https://osdatahub.os.uk/](https://osdatahub.os.uk/)
- **OS API Key**: Generate from your OS DataHub dashboard
- **API Quota**: Ensure sufficient quota for your expected usage

### Copilot Studio Requirements
- **Copilot Studio access** with MCP server permissions
- **Network connectivity** from Copilot Studio to your server
- **HTTPS endpoint** (recommended for production)

> **Note**: The Swagger/OpenAPI specification (`os-mcp-swagger.yaml`) is provided for reference and documentation purposes. With native MCP support, Copilot Studio discovers the server capabilities automatically through the MCP protocol.

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chris-page-gov/os-mcp.git
cd os-mcp
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Alternative: Install via pip

```bash
pip install -e .
```

## ⚙️ Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Required: Your OS DataHub API key
OS_API_KEY=your_os_api_key_here

# Optional: Server configuration
MCP_HOST=0.0.0.0
MCP_PORT=8000
MCP_DEBUG=false

# Optional: Authentication (for production)
MCP_AUTH_TOKEN=your_secure_token_here
```

### 2. Set Environment Variables

**Windows:**
```cmd
set OS_API_KEY=your_os_api_key_here
```

**macOS/Linux:**
```bash
export OS_API_KEY=your_os_api_key_here
```

### 3. Start the Server

```bash
# Start with streamable HTTP transport (required for Copilot)
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000

# Or with debug mode for development
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000 --debug
```

### 4. Verify Server is Running

```bash
# Check server status
curl http://localhost:8000/.well-known/mcp-auth

# Should return:
# {"authMethods":[{"type":"http","scheme":"bearer"}]}
```

## 🤖 Copilot Studio Integration

Based on Microsoft's official documentation, Copilot Studio integrates with MCP servers through **Custom Connectors** created in Power Apps, not direct MCP connections.

### Step 1: Create Custom MCP Connector in Power Apps

1. **Navigate to Copilot Studio**:
   - Select **Agents** in the left navigation
   - Select your agent from the list
   - Go to the **Tools** page for your agent
   - Select **Add a tool** → **New tool** → **Custom connector**

2. **Create the Custom Connector**:
   - You'll be taken to Power Apps
   - Select **New custom connector**
   - Select **Import OpenAPI file**
   - Import the `os-mcp-swagger.yaml` file from this repository

3. **Configure Authentication** (this is where you set up the Bearer token):
   - **Authentication Type**: Select `No authentication`
   - **Note**: We'll configure the Bearer token manually in the next step since the OS MCP Server uses custom header authentication that doesn't fit the standard auth types

### Step 2: Add Custom Authorization Header

Since API Key authentication isn't available in the dropdown, we'll use "No authentication" and add the Bearer token as a custom header:

1. **Select "No authentication"** from the dropdown
2. **Proceed to the Definition tab** (next step after Security)
3. **In the Definition tab**, you'll need to modify the Swagger definition to include the Authorization header
4. **Or configure the header in the operation parameters** (depending on the Power Apps interface)

### Step 2: Complete Power Apps Custom Connector Setup

1. **Set Authentication to "No authentication"**:
   - This is correct since we'll handle the Bearer token through the Swagger definition

2. **Review the imported definition**:
   - Verify the `/mcp` endpoint is correctly configured
   - Ensure `x-ms-agentic-protocol: mcp-streamable-1.0` is present
   - Check that the host points to your server
   - **Important**: Verify the Authorization header is defined in the Swagger parameters

3. **Ensure Authorization Header is Configured**:
   The `os-mcp-swagger.yaml` file should include this parameter definition:
   ```yaml
   parameters:
     - name: Authorization
       in: header
       description: Bearer token for authentication
       required: true
       type: string
       default: "Bearer dev-token"
   ```

4. **Test the connector**:
   - Use Power Apps' test functionality
   - When prompted for the Authorization header, enter: `Bearer dev-token`
   - Verify authentication works with your MCP server
   - Confirm MCP tools are discoverable

5. **Create the connector**:
   - Complete the setup process in Power Apps
   - Note the connector ID for use in Copilot Studio

### Step 3: Add MCP Connector to Your Agent

1. **Back in Copilot Studio**:
   - Go to **Tools** page for your agent
   - Select **Add a tool**
   - Select **Model Context Protocol**
   - Find your newly created custom connector in the list

2. **Configure the connection**:
   - **Authorize the connection** with your authentication details
   - Enter `Bearer dev-token` when prompted for the Authorization header
   - Select **Add to agent** or **Add and configure**

3. **Verify tool integration**:
   - Check that MCP tools appear in your agent's Tools section
   - Test with simple queries to ensure functionality

### Step 3: Configure Tool Access

Configure which MCP tools Copilot can access:

1. **Tool Selection**:
   - ✅ `hello_world` - Basic connectivity test
   - ✅ `get_workflow_context` - Essential for understanding data structure
   - ✅ `search_features` - Main geospatial search capability
   - ✅ `list_collections` - Discover available data types
   - ✅ `get_collection_info` - Get details about specific collections
   - ⚠️ `check_api_key` - Optional (may expose sensitive info)

2. **Tool Permissions**:
   - Set appropriate access levels for each tool
   - Consider limiting some tools to specific user roles

### Step 4: Natural Language Integration

With native MCP support, Copilot can automatically:

- **Discover available tools** from your MCP server
- **Generate appropriate calls** based on user queries
- **Handle responses** and format them naturally
- **Chain multiple calls** for complex queries

**Example Natural Language Queries:**
```
User: "What streets are near Nottingham NG1 7FG?"
→ Copilot automatically calls search_features with appropriate parameters

User: "Show me retail areas in Coventry city center"
→ Copilot uses land use collection with retail filtering

User: "Find A-roads in the local area"
→ Copilot applies road classification filters
```

## 🧪 Testing the Integration

### 1. Direct MCP Server Testing

Test the MCP server directly before adding to Copilot:

```bash
# Test MCP initialization
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "initialize",
    "params": {
      "protocolVersion": "1.0",
      "capabilities": {},
      "clientInfo": {"name": "test-client", "version": "1.0.0"}
    }
  }'
```

### 2. Test Tool Discovery

```bash
# List available tools
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/list",
    "params": {}
  }'
```

### 3. Test Geospatial Functionality

```bash
# Test workflow context (essential first step)
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "get_workflow_context",
      "arguments": {}
    }
  }'

# Test street search
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search_features",
      "arguments": {
        "collection_id": "trn-ntwk-street-1",
        "bbox": "-1.16,52.95,-1.15,52.96",
        "limit": 5
      }
    }
  }'
```

### 4. Test in Copilot Studio

Once the MCP server is connected:

1. **Test Connection**: Use the built-in test feature in MCP server settings
2. **Natural Language Testing**: Try these queries in Copilot chat:
   - `"Hello from the OS MCP server"` (tests hello_world)
   - `"What data collections are available?"` (tests list_collections)
   - `"Find streets in Nottingham NG1 area"` (tests search_features)
   - `"Show me retail areas near Coventry"` (tests filtering)

3. **Monitor Tool Usage**: Check Copilot Studio analytics for:
   - Successful MCP tool calls
   - Error rates and failure patterns
   - Response times and performance
   - User satisfaction with geospatial responses

## 🔧 Available Tools

The OS MCP Server provides these tools for Copilot:

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `hello_world` | Test connectivity | `name` |
| `check_api_key` | Verify OS API key status | None |
| `get_workflow_context` | Get collections and filtering guide | None |
| `list_collections` | List all data collections | None |
| `search_features` | Search geospatial features | `collection_id`, `bbox`, `filter`, `limit` |
| `get_feature` | Get specific feature by ID | `collection_id`, `feature_id` |
| `get_collection_info` | Get collection details | `collection_id` |
| `get_collection_queryables` | Get available filters | `collection_id` |

### Key Data Collections

| Collection ID | Description | Example Searches |
|---------------|-------------|------------------|
| `trn-ntwk-street-1` | Street network | Roads, streets, highways |
| `adr-fts-addressbasepremium-1` | Address data | Postcodes, building addresses |
| `lus-fts-site-1` | Land use sites | Retail, transport, residential areas |
| `bld-fts-buildingline-1` | Building outlines | Building footprints |

## 💡 Usage Examples

With native MCP integration, users can ask natural language questions and Copilot automatically chooses the right tools and parameters:

### Example 1: Find Streets by Postcode

**User Query**: `"What streets are in NG1 7FG?"`

**What Copilot Does Automatically**:
1. Recognizes this as a location-based query
2. Calls `get_workflow_context` to understand available collections
3. Calls `search_features` with:
   ```json
   {
     "collection_id": "trn-ntwk-street-1",
     "bbox": "-1.16,52.95,-1.15,52.96",
     "limit": 10
   }
   ```
4. Formats results as a natural language response

### Example 2: Find Retail Areas

**User Query**: `"Show me shops and retail areas near Coventry city center"`

**What Copilot Does Automatically**:
1. Identifies this needs land use data with retail filtering
2. Calls `search_features` with:
   ```json
   {
     "collection_id": "lus-fts-site-1",
     "bbox": "-1.52,52.40,-1.50,52.42",
     "filter": "oslandusetertiarygroup = 'Retail'",
     "limit": 20
   }
   ```
3. Presents results in a user-friendly format

### Example 3: Find A-Roads

**User Query**: `"What are the main A-roads in this area?"`

**What Copilot Does Automatically**:
1. Understands "A-roads" refers to road classification
2. Applies appropriate filtering
3. Calls `search_features` with:
   ```json
   {
     "collection_id": "trn-ntwk-street-1",
     "filter": "roadclassification = 'A Road' AND operationalstate = 'Open'",
     "bbox": "{context-appropriate-area}",
     "limit": 15
   }
   ```

### Example 4: Multi-step Queries

**User Query**: `"What types of data can you show me about Birmingham?"`

**What Copilot Does Automatically**:
1. Calls `list_collections` to see available data types
2. Calls `get_collection_info` for relevant collections
3. Provides overview of available data (streets, addresses, land use, etc.)
4. Suggests specific queries the user can ask

### Example 5: Complex Filtering

**User Query**: `"Find all the pedestrian streets that are currently open in central London"`

**What Copilot Does Automatically**:
1. Recognizes need for multiple filters
2. Constructs complex CQL filter
3. Calls `search_features` with sophisticated filtering:
   ```json
   {
     "collection_id": "trn-ntwk-street-1",
     "filter": "roadclassification = 'Pedestrianised Street' AND operationalstate = 'Open'",
     "bbox": "{london-center-bbox}",
     "limit": 25
   }
   ```

## 🔍 Troubleshooting

### Common Issues

#### 1. MCP Server Connection Failed
```bash
# Check if server is running and accessible
curl http://localhost:8000/.well-known/mcp-auth

# Verify MCP endpoint responds
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"method": "initialize", "params": {"protocolVersion": "1.0"}}'
```

#### 2. Authentication Issues in Power Apps Custom Connector

**Common Authentication Problems:**

1. **Wrong Authentication Type Selected**:
   - ❌ Don't use Basic authentication (username/password) 
   - ❌ Don't use Windows authentication
   - ✅ Use "No authentication" since API Key option isn't available

2. **Missing Authorization Header in Swagger**:
   - ❌ Authorization header not defined in imported Swagger file
   - ✅ Ensure `os-mcp-swagger.yaml` includes Authorization parameter:
   ```yaml
   parameters:
     - name: Authorization
       in: header
       required: true
       type: string
       default: "Bearer dev-token"
   ```

3. **Incorrect Header Value Format**:
   - ❌ Wrong: `dev-token`
   - ❌ Wrong: `Bearer: dev-token`  
   - ✅ Correct: `Bearer dev-token`

4. **Swagger Import Issues**:
   ```bash
   # Verify your MCP server responds correctly
   curl -X POST http://localhost:8000/mcp \
     -H "Authorization: Bearer dev-token" \
     -H "Content-Type: application/json" \
     -d '{"method": "initialize", "params": {"protocolVersion": "1.0"}}'
   ```

5. **Token Mismatch**:
   - Verify token matches server configuration (`dev-token` for development)
   - Check server logs for authentication attempts
   - Ensure no extra spaces or characters in token

**Power Apps Custom Connector Specific Solutions:**

1. **Authentication Configuration**:
   - Select "No authentication" (this is correct)
   - Authorization handled through Swagger parameter definition
   - Don't try to force API Key or Basic auth

2. **Swagger Definition Check**:
   - Verify `os-mcp-swagger.yaml` imported correctly
   - Check that `x-ms-agentic-protocol: mcp-streamable-1.0` is present
   - Ensure Authorization header parameter is defined
   - Confirm host/basePath point to your running server

3. **Test the Custom Connector**:
   - Use Power Apps Test feature before adding to Copilot Studio
   - Enter `Bearer dev-token` when prompted for Authorization header
   - Check network trace for correct header format
   - Verify server receives expected Authorization header

4. **Copilot Studio Integration Issues**:
   - Ensure custom connector appears in MCP connector list
   - Verify authorization step completes successfully
   - Check that tools appear in agent's Tools section

#### 3. Tools Not Appearing in Copilot
- Check MCP server is enabled and active
- Verify tool permissions are correctly set
- Test tools individually using direct MCP calls
- Review Copilot Studio logs for MCP-related errors

#### 4. Server Not Starting
```bash
# Check if port is in use
netstat -tlnp | grep :8000

# Try different port
python src/server.py --transport streamable-http --port 8001
```

#### 5. Geospatial Queries Failing
- Verify OS API key is valid and has quota remaining
- Check bounding box coordinates are in correct format (lon,lat,lon,lat)
- Ensure collection IDs are valid (use `list_collections` first)
- Validate CQL filter syntax for complex queries

### Debug Mode

Enable debug logging:

```bash
python src/server.py --transport streamable-http --debug
```

### Log Analysis

Check server logs for:
- Authentication failures
- API rate limiting
- Invalid requests
- Network connectivity issues

## 🔐 Authentication Quick Reference

### For Copilot Studio MCP Integration (via Power Apps Custom Connector):

**Required Steps:**
1. Create Custom Connector in Power Apps (imported from `os-mcp-swagger.yaml`)
2. Configure Authentication in Power Apps:
   - **Authentication Type**: `No authentication` (since API Key isn't available)
   - **Authorization handled by**: Swagger definition with Authorization header parameter
3. When testing/using in Copilot Studio: Enter `Bearer dev-token` when prompted for Authorization header

### Power Apps Authentication Setup (No API Key Option):

**Step-by-Step Process:**
1. **Authentication Type**: Select `No authentication`
2. **Authorization Header**: Configured through Swagger definition
3. **Header Configuration in Swagger**:
   ```yaml
   parameters:
     - name: Authorization
       in: header
       required: true
       type: string
       default: "Bearer dev-token"
   ```
4. **When using**: Enter `Bearer dev-token` when prompted

### For Direct API Testing:
```bash
curl -H "Authorization: Bearer dev-token"
```

### Header Format:
```
Authorization: Bearer dev-token
```
**NOT**: `dev-token` (missing Bearer)
**NOT**: `Bearer: dev-token` (incorrect colon placement)

### Process Summary:
1. ✅ Select "No authentication" in Power Apps Security step
2. ✅ Import `os-mcp-swagger.yaml` (contains Authorization header definition)
3. ✅ Add Custom Connector to Copilot Studio as MCP tool
4. ✅ Enter `Bearer dev-token` when prompted for Authorization header

## 🔐 Security Considerations

### Production Deployment

1. **HTTPS**: Always use HTTPS in production
2. **Authentication**: Use strong, unique bearer tokens
3. **Rate Limiting**: Configure appropriate limits
4. **Network Security**: Restrict access to necessary IPs
5. **Monitoring**: Set up logging and monitoring

### Environment Variables

```bash
# Production configuration
OS_API_KEY=your_production_api_key
MCP_AUTH_TOKEN=your_strong_random_token
MCP_RATE_LIMIT=100
MCP_LOG_LEVEL=INFO
```

### Firewall Configuration

```bash
# Allow only Copilot Studio IPs (example)
ufw allow from copilot-studio-ip-range to any port 8000
```

## 📚 Additional Resources

- **OS DataHub Documentation**: [https://osdatahub.os.uk/docs](https://osdatahub.os.uk/docs)
- **MCP Protocol Specification**: [https://spec.modelcontextprotocol.io/](https://spec.modelcontextprotocol.io/)
- **Copilot Studio Documentation**: [Microsoft Copilot Studio Docs](https://docs.microsoft.com/en-us/microsoft-copilot-studio/)
- **CQL Filter Reference**: [OGC CQL Documentation](https://docs.geoserver.org/stable/en/user/filter/cql_filter.html)

## 🆘 Support

For issues and questions:

1. **Check the logs** with debug mode enabled
2. **Review this documentation** for common solutions
3. **Test with the Jupyter notebook** examples
4. **Verify OS API key** and quota status
5. **Check network connectivity** between components

---

**Ready to explore UK geospatial data with Copilot! 🗺️🤖**
