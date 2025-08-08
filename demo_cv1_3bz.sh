#!/bin/bash
# Demo script showing OS MCP Server in action for Coventry CV1 3BZ
# This demonstrates the MCP protocol calls you would make

echo "🗺️  OS MCP Server Demo - Coventry CV1 3BZ"
echo "=============================================="
echo

echo "1. Testing MCP Server Connectivity..."
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "tools/call",
    "params": {
      "name": "hello_world",
      "arguments": {"name": "Coventry User"}
    }
  }' | jq '.'
echo

echo "2. Getting Available Data Collections..."
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "2",
    "method": "tools/call",
    "params": {
      "name": "get_workflow_context",
      "arguments": {}
    }
  }' | jq '.'
echo

echo "3. Searching for Streets around CV1 3BZ (Coventry City Centre)..."
# CV1 3BZ is approximately at coordinates: -1.51, 52.41
# Using a small bounding box around this area
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "3",
    "method": "tools/call",
    "params": {
      "name": "search_features",
      "arguments": {
        "collection_id": "trn-ntwk-street-1",
        "bbox": "-1.52,52.40,-1.50,52.42",
        "limit": 5
      }
    }
  }' | jq '.'
echo

echo "4. Looking for Retail Areas near CV1 3BZ..."
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "4",
    "method": "tools/call",
    "params": {
      "name": "search_features",
      "arguments": {
        "collection_id": "lus-fts-site-1",
        "bbox": "-1.52,52.40,-1.50,52.42",
        "filter": "oslandusetertiarygroup = '\''Retail'\''",
        "limit": 3
      }
    }
  }' | jq '.'
echo

echo "5. Finding Address Information in your area..."
curl -s -X POST http://localhost:8000/mcp \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "5",
    "method": "tools/call",
    "params": {
      "name": "search_features",
      "arguments": {
        "collection_id": "adr-fts-addressbasepremium-1",
        "bbox": "-1.515,52.405,-1.505,52.415",
        "filter": "postcode LIKE '\''CV1%'\''",
        "limit": 5
      }
    }
  }' | jq '.'

echo
echo "Demo complete! This shows how the MCP server provides geospatial data"
echo "for your specific location in Coventry through standardized MCP calls."
