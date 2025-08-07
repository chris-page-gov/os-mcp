#!/usr/bin/env python3

import asyncio
import subprocess
import json
import tempfile
import os

async def debug_claude_mcp_issue():
    """
    Debug the exact issue Claude is experiencing with the MCP server
    """
    
    print("🔍 Debugging Claude MCP Connection Issue")
    print("=" * 50)
    
    # Check environment
    api_key = os.environ.get("OS_API_KEY")
    if not api_key:
        print("❌ OS_API_KEY not found in environment")
        return
    
    print(f"✅ OS_API_KEY found")
    print(f"   Length: {len(api_key)} characters")
    print(f"   First 15 chars: {api_key[:15]}...")
    print(f"   Contains spaces: {'Yes' if ' ' in api_key else 'No'}")
    newlines = ['\n', '\r']
    print(f"   Contains newlines: {'Yes' if any(c in api_key for c in newlines) else 'No'}")
    
    # Test 1: Direct API call (like our diagnostic script)
    print("\n1. Testing direct OS API call...")
    try:
        import requests
        url = f"https://api.os.uk/features/ngd/ofa/v1/collections?key={api_key}"
        response = requests.get(url, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success! Found {len(data.get('collections', []))} collections")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Test what the MCP server's API client would do
    print("\n2. Testing MCP server's API client approach...")
    try:
        # Simulate the exact same request the MCP server makes
        import aiohttp
        async with aiohttp.ClientSession() as session:
            # This mimics the exact request format from os_api.py
            endpoint = "https://api.os.uk/features/ngd/ofa/v1/collections"
            params = {"key": api_key}
            headers = {
                "User-Agent": "os-ngd-mcp-server/1.0",
                "Accept": "application/json"
            }
            
            async with session.get(endpoint, params=params, headers=headers) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✅ Success! Found {len(data.get('collections', []))} collections")
                else:
                    text = await response.text()
                    print(f"   ❌ Error: {text}")
                    
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Check for potential API key formatting issues
    print("\n3. Checking API key format...")
    
    # Check for BOM or invisible characters
    encoded = api_key.encode('utf-8')
    if encoded.startswith(b'\xef\xbb\xbf'):
        print("   ⚠️  API key starts with UTF-8 BOM - this could cause issues")
    
    # Check for non-printable characters
    printable_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
    non_printable = [c for c in api_key if c not in printable_chars]
    if non_printable:
        print(f"   ⚠️  API key contains non-standard characters: {non_printable}")
    else:
        print("   ✅ API key contains only standard characters")
    
    # Check expected format
    if len(api_key) < 30:
        print("   ⚠️  API key seems too short (expected 30+ characters)")
    elif len(api_key) > 100:
        print("   ⚠️  API key seems too long (expected under 100 characters)")
    else:
        print("   ✅ API key length appears reasonable")

if __name__ == "__main__":
    asyncio.run(debug_claude_mcp_issue())
