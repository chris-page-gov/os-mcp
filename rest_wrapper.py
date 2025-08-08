"""
REST API Wrapper for OS MCP Server
Provides a simple REST interface that Power Apps can use,
which internally calls the MCP server via JSON-RPC.
"""

from fastapi import FastAPI, HTTPException, Header, Query
from typing import Optional
import httpx
import asyncio
import json

app = FastAPI(title="OS MCP REST Wrapper", version="1.0.0")

MCP_SERVER_URL = "http://127.0.0.1:8000/mcp"

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OS MCP REST Wrapper"}

@app.post("/tools/list")
async def list_tools(authorization: str = Header(..., description="Bearer token")):
    """List available MCP tools"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "tools/list",
                    "params": {}
                }
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/tools/hello")
async def hello_world(
    name: str = Query(default="World", description="Name to greet"),
    authorization: str = Header(..., description="Bearer token")
):
    """Test connectivity with hello_world tool"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": "1", 
                    "method": "tools/call",
                    "params": {
                        "name": "hello_world",
                        "arguments": {"name": name}
                    }
                }
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/features")
async def search_features(
    collection_id: str = Query(default="trn-ntwk-street-1", description="Data collection ID"),
    bbox: str = Query(default="-1.16,52.95,-1.15,52.96", description="Bounding box (min_lon,min_lat,max_lon,max_lat)"),
    filter: Optional[str] = Query(default=None, description="CQL filter expression"),
    limit: int = Query(default=10, description="Maximum results"),
    authorization: str = Header(..., description="Bearer token")
):
    """Search for geospatial features"""
    try:
        arguments = {
            "collection_id": collection_id,
            "bbox": bbox,
            "limit": limit
        }
        if filter:
            arguments["filter"] = filter
            
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "tools/call", 
                    "params": {
                        "name": "search_features",
                        "arguments": arguments
                    }
                }
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections")
async def list_collections(authorization: str = Header(..., description="Bearer token")):
    """List available data collections"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "tools/call",
                    "params": {
                        "name": "list_collections", 
                        "arguments": {}
                    }
                }
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workflow/context")
async def get_workflow_context(authorization: str = Header(..., description="Bearer token")):
    """Get workflow context and available collections"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={"Authorization": authorization, "Content-Type": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": "1",
                    "method": "tools/call",
                    "params": {
                        "name": "get_workflow_context",
                        "arguments": {}
                    }
                }
            )
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
