# OS MCP Server Demo - CV1 3BZ Coventry

## VS Code + GitHub Copilot Chat Example

Once you have the OS MCP Server connected to VS Code, here's how you would interact with it:

### Example Conversation in VS Code Copilot Chat:

**You:** `@os-mcp-server I'm at CV1 3BZ in Coventry city centre. What streets are around here?`

**Copilot with MCP:** 
*Uses search_features tool with coordinates around CV1 3BZ (-1.51, 52.41)*

Response: "Based on OS data for CV1 3BZ area, here are the main streets:
- Corporation Street (major road through city centre)
- Trinity Street (shopping area)
- Hertford Street (pedestrian zone)
- High Street (main commercial street)
- Warwick Row (connecting road)"

---

**You:** `@os-mcp-server Show me retail areas and shops near my location`

**Copilot with MCP:**
*Uses search_features with land use collection and retail filter*

Response: "Retail areas near CV1 3BZ:
- West Orchards Shopping Centre (major retail complex)
- Lower Precinct (shopping center)
- City Centre retail units along Corporation Street
- Independent shops on Far Gosford Street
- Retail parks on the city outskirts"

---

**You:** `@os-mcp-server What types of data can you show me about Coventry?`

**Copilot with MCP:**
*Uses get_workflow_context and list_collections*

Response: "I can provide OS DataHub information including:
- **Street Networks**: Roads, paths, highways (trn-ntwk-street-1)
- **Addresses**: Postcode and building data (adr-fts-addressbasepremium-1) 
- **Land Use**: Retail, residential, commercial areas (lus-fts-site-1)
- **Buildings**: Building outlines and footprints (bld-fts-buildingline-1)
- **Transport**: Rail, bus routes and transport hubs

Just ask me specific questions about any of these!"

---

## Real MCP Protocol Calls

Behind the scenes, these interactions use standard MCP JSON-RPC calls:

```json
// Finding streets near CV1 3BZ
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_features",
    "arguments": {
      "collection_id": "trn-ntwk-street-1",
      "bbox": "-1.52,52.40,-1.50,52.42",
      "limit": 10
    }
  }
}
```

```json
// Finding retail areas with filtering
{
  "jsonrpc": "2.0", 
  "method": "tools/call",
  "params": {
    "name": "search_features",
    "arguments": {
      "collection_id": "lus-fts-site-1",
      "bbox": "-1.52,52.40,-1.50,52.42",
      "filter": "oslandusetertiarygroup = 'Retail'",
      "limit": 5
    }
  }
}
```

## Natural Language → Geospatial Queries

The power of MCP integration is that you can ask natural questions:

- ❓ "Where's the nearest hospital?"
- ❓ "Show me all A-roads in Coventry"
- ❓ "Find pedestrian streets in the city centre"
- ❓ "What's the address of buildings on Corporation Street?"

And the MCP server automatically:
1. 🔍 Determines the right data collection
2. 📍 Converts your location to coordinates
3. 🗺️ Applies appropriate filters
4. 📊 Returns structured geospatial data
5. 💬 Presents it in natural language

## Try It Yourself!

1. **Start the server**: `python src/server.py --transport streamable-http --host 0.0.0.0 --port 8000`
2. **Open VS Code**: `code os-mcp-vscode.code-workspace`
3. **Use Copilot Chat**: Ask questions with `@os-mcp-server`
4. **Explore your area**: Ask about streets, shops, transport around CV1 3BZ!
