#!/usr/bin/env python3
"""
Basic Usage Examples for OS MCP Server

This script demonstrates the fundamental operations of the OS MCP Server
including connection setup, authentication, and basic tool usage.

Example locations:
- Nottingham NG1 7FG
- Coventry CV1
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SERVER_URL = "http://localhost:8000/mcp/"
HEADERS = {"Authorization": "Bearer dev-token"}

async def setup_session():
    """Establish a connection to the OS MCP Server"""
    logger.info("🔌 Connecting to OS MCP Server...")
    
    try:
        # Connect to the server
        client_manager = streamablehttp_client(SERVER_URL, headers=HEADERS)
        read_stream, write_stream, get_session_id = await client_manager.__aenter__()
        
        # Create MCP session
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        
        # Initialize the session
        init_result = await session.initialize()
        session_id = get_session_id()
        
        logger.info(f"✅ Connected successfully! Session ID: {session_id}")
        logger.info(f"📋 Server initialized: {init_result}")
        
        return session, client_manager, session_id
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        raise

async def list_available_tools(session: ClientSession) -> Dict[str, Any]:
    """List all available tools from the server"""
    logger.info("🔍 Discovering available tools...")
    
    try:
        tools_result = await session.list_tools()
        tools = {tool.name: tool.description for tool in tools_result.tools}
        
        logger.info(f"📚 Found {len(tools)} available tools:")
        for name, description in tools.items():
            logger.info(f"  • {name}: {description}")
        
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to list tools: {e}")
        raise

def extract_text_from_result(result) -> str:
    """Safely extract text from MCP tool result"""
    if result.content and len(result.content) > 0:
        content = result.content[0]
        if hasattr(content, 'text'):
            return content.text
        else:
            return str(content)
    return "No response"
    """Test basic connectivity with hello_world tool"""
    logger.info("👋 Testing basic connectivity...")
    
    try:
        result = await session.call_tool("hello_world", {"name": "Nottingham Explorer"})
        
        # Extract text content from the result
        response = extract_text_from_result(result)
        logger.info(f"✅ Hello world response: {response}")
        return response
            
    except Exception as e:
        logger.error(f"❌ Hello world failed: {e}")
        raise

async def check_api_key_status(session: ClientSession) -> Dict[str, Any]:
    """Verify that the OS API key is properly configured"""
    logger.info("🔑 Checking API key configuration...")
    
    try:
        result = await session.call_tool("check_api_key", {})
        
        # Parse the JSON response
        response_text = extract_text_from_result(result)
        response_data = json.loads(response_text)
        
        if response_data.get("status") == "success":
            logger.info(f"✅ API key status: {response_data.get('message')}")
        else:
            logger.error(f"❌ API key issue: {response_data.get('message')}")
        
        return response_data    except Exception as e:
        logger.error(f"❌ API key check failed: {e}")
        raise

async def get_workflow_context(session: ClientSession) -> Dict[str, Any]:
    """Get the workflow context - this is required before any searches"""
    logger.info("🎯 Getting workflow context (required for all searches)...")
    
    try:
        result = await session.call_tool("get_workflow_context", {})
        
        if result.content and len(result.content) > 0:
            response_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            context_data = json.loads(response_text)
            
            logger.info("✅ Workflow context retrieved successfully!")
            
            # Show available collections
            if "available_collections" in context_data:
                collections = context_data["available_collections"]
                logger.info(f"📊 Found {len(collections)} data collections:")
                for coll_id, coll_info in collections.items():
                    logger.info(f"  • {coll_id}: {coll_info.get('title', 'No title')}")
            
            # Show key guidance
            if "MANDATORY_PLANNING_REQUIREMENT" in context_data:
                logger.info("📋 Planning requirement: You must explain your approach before making searches")
            
            return context_data
        else:
            logger.warning("⚠️ Empty response from get_workflow_context")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Failed to get workflow context: {e}")
        raise

async def list_collections(session: ClientSession) -> Dict[str, Any]:
    """List all available data collections"""
    logger.info("📚 Listing all available data collections...")
    
    try:
        result = await session.call_tool("list_collections", {})
        
        if result.content and len(result.content) > 0:
            response_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            collections_data = json.loads(response_text)
            
            if "collections" in collections_data:
                collections = collections_data["collections"]
                logger.info(f"✅ Found {len(collections)} collections:")
                
                for collection in collections:
                    coll_id = collection.get("id", "Unknown ID")
                    title = collection.get("title", "No title")
                    logger.info(f"  • {coll_id}: {title}")
                
                return collections_data
            else:
                logger.warning("⚠️ No collections found in response")
                return {}
        else:
            logger.warning("⚠️ Empty response from list_collections")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Failed to list collections: {e}")
        raise

async def get_collection_details(session: ClientSession, collection_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific collection"""
    logger.info(f"🔍 Getting details for collection: {collection_id}")
    
    try:
        result = await session.call_tool("get_collection_info", {"collection_id": collection_id})
        
        if result.content and len(result.content) > 0:
            response_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            collection_data = json.loads(response_text)
            
            logger.info(f"✅ Collection details retrieved for {collection_id}")
            
            # Show key information
            if "title" in collection_data:
                logger.info(f"  📋 Title: {collection_data['title']}")
            if "description" in collection_data:
                desc = collection_data['description'][:100] + "..." if len(collection_data['description']) > 100 else collection_data['description']
                logger.info(f"  📝 Description: {desc}")
            
            return collection_data
        else:
            logger.warning(f"⚠️ Empty response for collection {collection_id}")
            return {}
            
    except Exception as e:
        logger.error(f"❌ Failed to get collection details for {collection_id}: {e}")
        raise

async def main():
    """Main demonstration function"""
    logger.info("🚀 Starting OS MCP Server Basic Usage Examples")
    logger.info("📍 Example locations: Nottingham NG1 7FG, Coventry CV1")
    
    session = None
    client_manager = None
    
    try:
        # 1. Establish connection
        session, client_manager, session_id = await setup_session()
        
        # 2. List available tools
        tools = await list_available_tools(session)
        
        # 3. Test basic connectivity
        hello_response = await test_hello_world(session)
        
        # 4. Verify API key configuration
        api_status = await check_api_key_status(session)
        
        # 5. Get workflow context (required for searches)
        workflow_context = await get_workflow_context(session)
        
        # 6. List all collections
        collections = await list_collections(session)
        
        # 7. Get details for key collections we'll use in location examples
        key_collections = ["trn-ntwk-street-1", "lus-fts-site-1", "bld-fts-buildingline-1"]
        
        for collection_id in key_collections:
            try:
                await get_collection_details(session, collection_id)
            except Exception as e:
                logger.warning(f"⚠️ Could not get details for {collection_id}: {e}")
        
        logger.info("🎉 Basic usage examples completed successfully!")
        logger.info("💡 Next steps: Try the location-specific searches in 02_location_searches.py")
        
    except Exception as e:
        logger.error(f"💥 Example failed: {e}")
        raise
    
    finally:
        # Clean up connections
        if session:
            try:
                await session.__aexit__(None, None, None)
                logger.info("🔌 Session closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing session: {e}")
        
        if client_manager:
            try:
                await client_manager.__aexit__(None, None, None)
                logger.info("🔌 Client connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing client: {e}")

if __name__ == "__main__":
    # Check environment variables
    if not os.environ.get("OS_API_KEY"):
        logger.error("❌ OS_API_KEY environment variable not set!")
        logger.info("💡 Get your API key from: https://osdatahub.os.uk/")
        exit(1)
    
    logger.info("🔑 OS_API_KEY detected")
    
    # Run the examples
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Examples interrupted by user")
    except Exception as e:
        logger.error(f"💥 Examples failed: {e}")
        exit(1)
