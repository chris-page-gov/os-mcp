#!/usr/bin/env python3
"""
Debug script to test the OS MCP Server API directly
"""

import asyncio
import json
import os
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def test_os_mcp_debug():
    """Test the OS MCP server with proper session handling"""
    
    print("🔧 Debug Test: OS MCP Server API Authentication")
    print("=" * 55)
    
    # Check environment
    api_key = os.environ.get("OS_API_KEY")
    if not api_key:
        print("❌ OS_API_KEY not set in environment")
        return
    
    print(f"✅ OS_API_KEY found (length: {len(api_key)})")
    print(f"   First 20 chars: {api_key[:20]}...")
    print()
    
    # Start the server process
    print("🚀 Starting MCP server in stdio mode...")
    
    try:
        async with stdio_client(
            command="python",
            args=["src/server.py", "--transport", "stdio"],
            env=dict(os.environ, **{"OS_API_KEY": api_key, "STDIO_KEY": "test"})
        ) as (read, write):
            async with ClientSession(read, write) as session:
                print("✅ Connected to MCP server")
                
                # Test 1: Check API key function
                print("\n1. Testing check_api_key tool...")
                try:
                    result = await session.call_tool("check_api_key", {})
                    print(f"   Result: {result.content[0].text}")
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                
                # Test 2: Get workflow context (this calls OS API)
                print("\n2. Testing get_workflow_context (calls OS API)...")
                try:
                    result = await session.call_tool("get_workflow_context", {})
                    content = result.content[0].text
                    if "collections" in content.lower():
                        print("   ✅ Successfully called OS API and got collections!")
                        # Parse and show first few collections
                        try:
                            data = json.loads(content)
                            collections = data.get("collections", [])
                            print(f"   Found {len(collections)} collections:")
                            for i, col in enumerate(collections[:5]):
                                print(f"      {i+1}. {col.get('id', 'Unknown')}")
                        except:
                            print("   Raw response:", content[:200], "...")
                    else:
                        print(f"   ❌ Unexpected response: {content[:200]}...")
                        
                except Exception as e:
                    print(f"   ❌ Error calling OS API: {e}")
                    if "401" in str(e):
                        print("      This indicates the API key is being rejected by OS servers")
                    elif "403" in str(e):
                        print("      This indicates permission issues with the API key")
                
                print("\n✅ MCP server connection test complete")
                
    except Exception as e:
        print(f"❌ Failed to connect to MCP server: {e}")

if __name__ == "__main__":
    asyncio.run(test_os_mcp_debug())
