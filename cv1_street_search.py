#!/usr/bin/env python3
"""
Quick script to find streets around CV1 3BZ in Coventry
This simulates what @os-mcp-server would return in VS Code GitHub Copilot Chat
"""

import asyncio
import os
from typing import Dict, Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.server import main
import subprocess
import time
import requests
import json

async def find_streets_cv1_3bz():
    """Find streets around CV1 3BZ in Coventry"""
    
    print("🏠 Finding streets around CV1 3BZ, Coventry...")
    print("=" * 50)
    
    # CV1 3BZ coordinates (approximately)
    cv1_lon = -1.51
    cv1_lat = 52.41
    
    # Create a small bounding box around CV1 3BZ
    bbox_size = 0.005  # About 500m radius
    bbox = f"{cv1_lon - bbox_size},{cv1_lat - bbox_size},{cv1_lon + bbox_size},{cv1_lat + bbox_size}"
    
    # MCP server URL
    server_url = "http://localhost:8000/mcp"
    headers = {
        "Authorization": "Bearer dev-token",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream"
    }
    
    # First, let's check if server is responding
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        print(f"✅ Server health check: {response.status_code}")
    except Exception as e:
        print(f"❌ Server not responding: {e}")
        return
    
    # Search for streets
    street_query = {
        "jsonrpc": "2.0",
        "id": "cv1-streets",
        "method": "tools/call",
        "params": {
            "name": "search_features",
            "arguments": {
                "collection_id": "trn-ntwk-street-1", 
                "bbox": bbox,
                "limit": 20
            }
        }
    }
    
    try:
        print(f"🔍 Searching for streets in bounding box: {bbox}")
        response = requests.post(server_url, headers=headers, json=street_query, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and 'content' in data['result']:
                print("🛣️  Streets found around CV1 3BZ:")
                print("-" * 30)
                
                # Parse the response text
                content = data['result']['content'][0]['text']
                if 'features' in content:
                    # Try to extract street names
                    features = json.loads(content)['features']
                    streets = []
                    for feature in features:
                        if 'properties' in feature and 'name' in feature['properties']:
                            street_name = feature['properties']['name']
                            if street_name and street_name not in streets:
                                streets.append(street_name)
                    
                    if streets:
                        for i, street in enumerate(streets[:15], 1):
                            print(f"{i:2d}. {street}")
                    else:
                        print("No named streets found in the response")
                        print("Raw response content:", content[:200], "...")
                else:
                    print("Response format unexpected:")
                    print(content[:300], "...")
            else:
                print("❌ Unexpected response format:")
                print(json.dumps(data, indent=2)[:500])
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error querying streets: {e}")
    
    # Also search for retail areas
    print("\n🏪 Searching for retail areas nearby...")
    retail_query = {
        "jsonrpc": "2.0",
        "id": "cv1-retail",
        "method": "tools/call",
        "params": {
            "name": "search_features",
            "arguments": {
                "collection_id": "zoomstack-retail-points",
                "bbox": bbox,
                "limit": 10
            }
        }
    }
    
    try:
        response = requests.post(server_url, headers=headers, json=retail_query, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                content = data['result']['content'][0]['text']
                print("🛍️  Retail areas:", content[:200] if len(content) > 200 else content)
        
    except Exception as e:
        print(f"❌ Error querying retail areas: {e}")

if __name__ == "__main__":
    asyncio.run(find_streets_cv1_3bz())
