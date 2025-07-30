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
- **Copilot Studio access** with custom connector permissions
- **Network connectivity** from Copilot Studio to your server
- **HTTPS endpoint** (recommended for production)

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

### Step 1: Import the Swagger Specification

1. **Open Copilot Studio** and navigate to your copilot
2. **Go to Actions** → **Add an action** → **Import from OpenAPI**
3. **Upload the Swagger file**: Use `/os-mcp-swagger.yaml` from the repository
4. **Configure the endpoint**:
   - **Base URL**: `http://your-server:8000` (or your public endpoint)
   - **Authentication**: Bearer token
   - **Token**: `dev-token` (or your custom token)

### Step 2: Configure the Custom Connector

1. **Review imported actions**:
   - `InvokeMCP` - Main MCP endpoint
   - `GetAuthMethods` - Authentication discovery

2. **Test the connection**:
   - Use the test feature in Copilot Studio
   - Send a simple `hello_world` request

3. **Configure security**:
   - Set up proper authentication headers
   - Configure rate limiting if needed

### Step 3: Create Copilot Topics

Create topics that leverage the OS MCP Server:

```yaml
# Example topic: Find streets near a location
Topic: Find Streets
Trigger phrases:
  - "Find streets near {location}"
  - "What streets are in {postcode}"
  - "Show me roads around {place}"

Action: InvokeMCP
Parameters:
  method: "tools/call"
  params:
    name: "search_features"
    arguments:
      collection_id: "trn-ntwk-street-1"
      bbox: "{calculated_bbox}"
      limit: 10
```

### Step 4: Handle Responses

Configure response handling to format geospatial data for users:

```yaml
Response processing:
  - Parse GeoJSON features
  - Extract street names and classifications
  - Format as user-friendly list
  - Optionally show on map (if available)
```

## 🧪 Testing the Integration

### 1. Direct API Testing

Test the MCP server directly:

```bash
# Test hello world
curl -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "hello_world",
      "arguments": {"name": "Test User"}
    }
  }'
```

### 2. Workflow Context Test

```bash
# Get available collections and filtering guidance
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
```

### 3. Geospatial Search Test

```bash
# Search for streets in Nottingham
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

### Example 1: Find Streets by Postcode

**User Query**: "What streets are in NG1 7FG?"

**Copilot Action**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_features",
    "arguments": {
      "collection_id": "trn-ntwk-street-1",
      "bbox": "-1.16,52.95,-1.15,52.96",
      "limit": 10
    }
  }
}
```

### Example 2: Find Retail Areas

**User Query**: "Show me shops near Coventry city center"

**Copilot Action**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_features",
    "arguments": {
      "collection_id": "lus-fts-site-1",
      "bbox": "-1.52,52.40,-1.50,52.42",
      "filter": "oslandusetertiarygroup = 'Retail'",
      "limit": 20
    }
  }
}
```

### Example 3: Find A-Roads

**User Query**: "What A-roads are in the area?"

**Copilot Action**:
```json
{
  "method": "tools/call",
  "params": {
    "name": "search_features",
    "arguments": {
      "collection_id": "trn-ntwk-street-1",
      "filter": "roadclassification = 'A Road' AND operationalstate = 'Open'",
      "bbox": "-1.16,52.95,-1.15,52.96",
      "limit": 15
    }
  }
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Server Not Starting
```bash
# Check if port is in use
netstat -tlnp | grep :8000

# Try different port
python src/server.py --transport streamable-http --port 8001
```

#### 2. API Key Issues
```bash
# Verify API key is set
echo $OS_API_KEY

# Test API key directly
curl -H "key: $OS_API_KEY" "https://api.os.uk/features/v1/wfs?service=WFS&request=GetCapabilities"
```

#### 3. Connection Refused
- Check firewall settings
- Verify server is running
- Ensure correct host/port configuration

#### 4. Authentication Errors
- Verify bearer token format: `Bearer your-token`
- Check token matches server configuration
- Ensure proper header formatting

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
