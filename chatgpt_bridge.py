#!/usr/bin/env python3
"""
Quick demo script showing how to use the OS MCP Server with ChatGPT
This creates a simple REST interface that ChatGPT can use.
"""

from fastapi import FastAPI, HTTPException
import httpx
import asyncio
import json
import uvicorn
from typing import Optional

app = FastAPI(title="OS MCP ChatGPT Bridge", version="1.0.0")

# MCP Server URL - adjust port as needed
MCP_SERVER_URL = "http://127.0.0.1:8002/mcp"

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "OS MCP ChatGPT Bridge",
        "description": "REST API bridge for connecting ChatGPT to OS MCP Server",
        "endpoints": {
            "/health": "Health check",
            "/collections": "Get available data collections",
            "/search/streets": "Search for streets in a bounding box",
            "/search/buildings": "Search for buildings in a bounding box"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "OS MCP ChatGPT Bridge"}

@app.get("/collections")
async def get_collections():
    """Get available data collections"""
    try:
        async with httpx.AsyncClient() as client:
            # First establish session
            init_response = await client.post(
                MCP_SERVER_URL,
                headers={
                    "Authorization": "Bearer dev-token",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": "init",
                    "method": "initialize", 
                    "params": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {},
                        "clientInfo": {"name": "chatgpt-bridge", "version": "1.0.0"}
                    }
                }
            )
            
            # Get workflow context (which includes collections)
            response = await client.post(
                MCP_SERVER_URL,
                headers={
                    "Authorization": "Bearer dev-token",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": "collections",
                    "method": "tools/call",
                    "params": {
                        "name": "get_workflow_context",
                        "arguments": {}
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error connecting to MCP server: {str(e)}")

@app.get("/search/streets")
async def search_streets(
    bbox: str,
    limit: int = 10
):
    """
    Search for streets in a bounding box
    
    Args:
        bbox: Bounding box as "min_lon,min_lat,max_lon,max_lat"
        limit: Maximum number of results (default 10)
    
    Example:
        /search/streets?bbox=-0.1,51.5,-0.05,51.52&limit=5
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={
                    "Authorization": "Bearer dev-token",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": "search-streets",
                    "method": "tools/call",
                    "params": {
                        "name": "search_features",
                        "arguments": {
                            "collection_id": "trn-ntwk-street-1",
                            "bbox": bbox,
                            "limit": limit
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/buildings")
async def search_buildings(
    bbox: str,
    limit: int = 10
):
    """
    Search for buildings in a bounding box
    
    Args:
        bbox: Bounding box as "min_lon,min_lat,max_lon,max_lat"
        limit: Maximum number of results (default 10)
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                headers={
                    "Authorization": "Bearer dev-token",
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                },
                json={
                    "jsonrpc": "2.0",
                    "id": "search-buildings",
                    "method": "tools/call",
                    "params": {
                        "name": "search_features",
                        "arguments": {
                            "collection_id": "bld-fts-building-1",
                            "bbox": bbox,
                            "limit": limit
                        }
                    }
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}", "detail": response.text}
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting OS MCP ChatGPT Bridge on http://localhost:8090")
    print("📍 Connect ChatGPT Custom GPT to: http://localhost:8090")
    print("🗺️  Available endpoints:")
    print("   GET /collections - List available data collections")
    print("   GET /search/streets?bbox=lon1,lat1,lon2,lat2 - Search streets")
    print("   GET /search/buildings?bbox=lon1,lat1,lon2,lat2 - Search buildings")
    
    uvicorn.run(app, host="0.0.0.0", port=8090)
