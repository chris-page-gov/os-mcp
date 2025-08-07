# ChatGPT Integration Guide for OS MCP Server

This guide shows you how to connect ChatGPT to the OS MCP Server for UK geospatial data access.

## Method 1: Custom GPT with OpenAPI Specification (Recommended)

### Step 1: Start the Services

1. **Start the MCP Server:**
   ```bash
   cd /path/to/os-mcp
   export OS_API_KEY="your_api_key_here"
   export STDIO_KEY="any_value"
   python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000
   ```

2. **Start the REST Wrapper:**
   ```bash
   # In a new terminal
   python rest_wrapper.py --port 8080
   ```

### Step 2: Create a Custom GPT

1. **Go to ChatGPT Plus** and click "Create a GPT"
2. **Configure the GPT:**
   - **Name:** "UK Geospatial Assistant"
   - **Description:** "Access UK geospatial data from Ordnance Survey"
   - **Instructions:** 
     ```
     You are a UK geospatial data assistant. You can search for streets, buildings, 
     points of interest, and other geographic features across the UK using Ordnance 
     Survey data. Always provide helpful context about locations and suggest related 
     queries.
     ```

3. **Add Actions (OpenAPI Schema):**
   ```json
   {
     "openapi": "3.0.0",
     "info": {
       "title": "OS MCP Server API",
       "version": "1.0.0",
       "description": "UK Ordnance Survey geospatial data access"
     },
     "servers": [
       {
         "url": "http://localhost:8080",
         "description": "Local OS MCP REST Wrapper"
       }
     ],
     "paths": {
       "/health": {
         "get": {
           "summary": "Health check",
           "responses": {
             "200": {
               "description": "Service status"
             }
           }
         }
       },
       "/collections": {
         "get": {
           "summary": "Get available data collections",
           "parameters": [
             {
               "name": "authorization",
               "in": "header",
               "required": true,
               "schema": {
                 "type": "string",
                 "default": "Bearer dev-token"
               }
             }
           ],
           "responses": {
             "200": {
               "description": "List of available collections"
             }
           }
         }
       },
       "/search/features": {
         "post": {
           "summary": "Search for geographic features",
           "parameters": [
             {
               "name": "authorization",
               "in": "header",
               "required": true,
               "schema": {
                 "type": "string",
                 "default": "Bearer dev-token"
               }
             },
             {
               "name": "collection_id",
               "in": "query",
               "required": true,
               "schema": {
                 "type": "string",
                 "enum": [
                   "trn-ntwk-street-1",
                   "bld-fts-building-1",
                   "poi-ntwk-retail-1"
                 ]
               },
               "description": "Collection to search in"
             },
             {
               "name": "bbox",
               "in": "query",
               "required": false,
               "schema": {
                 "type": "string"
               },
               "description": "Bounding box: min_lon,min_lat,max_lon,max_lat"
             },
             {
               "name": "limit",
               "in": "query",
               "required": false,
               "schema": {
                 "type": "integer",
                 "default": 10
               }
             }
           ],
           "responses": {
             "200": {
               "description": "Geographic features found"
             }
           }
         }
       }
     }
   }
   ```

4. **Test the Connection:**
   - Test with: "What streets are near London Bridge?"
   - Or: "Find retail locations in Manchester city centre"

## Method 2: Direct HTTP Integration

If you can't use Custom GPTs, you can provide ChatGPT with curl commands:

### Example Commands for ChatGPT:

```bash
# Get available collections
curl -X GET "http://localhost:8080/collections" \
  -H "Authorization: Bearer dev-token"

# Search for streets in a specific area
curl -X POST "http://localhost:8080/search/features" \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_id": "trn-ntwk-street-1",
    "bbox": "-0.1,51.5,-0.05,51.52",
    "limit": 10
  }'

# Search for buildings
curl -X POST "http://localhost:8080/search/features" \
  -H "Authorization: Bearer dev-token" \
  -d '{
    "collection_id": "bld-fts-building-1",
    "bbox": "-1.52,52.40,-1.50,52.42",
    "limit": 5
  }'
```

## Method 3: Code Interpreter Integration

You can also use ChatGPT's Code Interpreter with Python requests:

```python
import requests
import json

# Configuration
BASE_URL = "http://localhost:8080"
HEADERS = {"Authorization": "Bearer dev-token"}

# Get collections
def get_collections():
    response = requests.get(f"{BASE_URL}/collections", headers=HEADERS)
    return response.json()

# Search features
def search_features(collection_id, bbox=None, limit=10):
    params = {
        "collection_id": collection_id,
        "limit": limit
    }
    if bbox:
        params["bbox"] = bbox
    
    response = requests.post(f"{BASE_URL}/search/features", 
                           headers=HEADERS, params=params)
    return response.json()

# Example usage
collections = get_collections()
print("Available collections:", len(collections))

# Search for streets in London
london_streets = search_features(
    collection_id="trn-ntwk-street-1",
    bbox="-0.1,51.5,-0.05,51.52",
    limit=5
)
print("Streets found:", london_streets)
```

## Troubleshooting

### Common Issues:

1. **Connection Refused:**
   - Make sure both MCP server (port 8000) and REST wrapper (port 8080) are running
   - Check firewall settings

2. **401 Unauthorized:**
   - Verify your OS_API_KEY is set correctly
   - Ensure "Bearer dev-token" is used in Authorization header

3. **Custom GPT Not Working:**
   - Verify the OpenAPI schema is valid
   - Check that localhost URLs are accessible
   - Consider using ngrok for public access if needed

### Making it Publicly Accessible:

If you want to use this with ChatGPT from anywhere, you can use ngrok:

```bash
# Install ngrok (if not already installed)
# Then expose your REST wrapper
ngrok http 8080

# Use the ngrok URL in your Custom GPT configuration
# e.g., https://abc123.ngrok.io instead of http://localhost:8080
```

## Example Queries for ChatGPT:

Once set up, you can ask ChatGPT:

- "What streets are near Buckingham Palace?"
- "Find all retail locations in Birmingham city centre"
- "Show me buildings around Manchester Piccadilly station"
- "What transport infrastructure is near Heathrow Airport?"

The ChatGPT integration will translate these natural language queries into the appropriate API calls to get UK geospatial data!
