#!/usr/bin/env python3
"""
MCP Client Demonstration for OS MCP Server

This script demonstrates a complete MCP client workflow using the OS MCP Server
with Nottingham NG1 7FG and Coventry CV1 as practical examples.

Features demonstrated:
- Full MCP protocol implementation
- Session management with proper cleanup
- Error handling and recovery
- Real-world geospatial queries
- Performance considerations
"""

import asyncio
import logging
import json
import os
import time
from typing import Dict, Any, List, Optional
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SERVER_URL = "http://localhost:8000/mcp/"
HEADERS = {"Authorization": "Bearer dev-token"}

class OSMCPClient:
    """Complete MCP client for OS MCP Server"""
    
    def __init__(self, server_url: str, headers: Dict[str, str]):
        self.server_url = server_url
        self.headers = headers
        self.session: Optional[ClientSession] = None
        self.client_manager = None
        self.session_id: Optional[str] = None
        self.workflow_context: Optional[Dict[str, Any]] = None
        
    async def connect(self) -> None:
        """Establish connection to the MCP server"""
        logger.info("🔌 Connecting to OS MCP Server...")
        
        try:
            self.client_manager = streamablehttp_client(self.server_url, headers=self.headers)
            read_stream, write_stream, get_session_id = await self.client_manager.__aenter__()
            
            self.session = ClientSession(read_stream, write_stream)
            await self.session.__aenter__()
            
            # Initialize the session
            init_result = await self.session.initialize()
            self.session_id = get_session_id()
            
            logger.info(f"✅ Connected successfully! Session ID: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
            await self.cleanup()
            raise
    
    async def cleanup(self) -> None:
        """Clean up connections"""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
                logger.info("🔌 Session closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing session: {e}")
        
        if self.client_manager:
            try:
                await self.client_manager.__aexit__(None, None, None)
                logger.info("🔌 Client connection closed")
            except Exception as e:
                logger.warning(f"⚠️ Error closing client: {e}")
    
    def extract_text_from_result(self, result) -> str:
        """Safely extract text from MCP tool result"""
        try:
            if result.content and len(result.content) > 0:
                content = result.content[0]
                if hasattr(content, 'text'):
                    return content.text
                else:
                    return str(content)
            return "No response"
        except Exception as e:
            return f"Error extracting text: {e}"
    
    async def call_tool_safe(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool with error handling and response parsing"""
        try:
            if not self.session:
                raise RuntimeError("No active session")
            
            start_time = time.time()
            result = await self.session.call_tool(tool_name, arguments)
            duration = time.time() - start_time
            
            response_text = self.extract_text_from_result(result)
            
            try:
                response_data = json.loads(response_text)
            except json.JSONDecodeError:
                response_data = {"raw_response": response_text}
            
            logger.debug(f"Tool {tool_name} completed in {duration:.2f}s")
            return response_data
            
        except Exception as e:
            logger.error(f"❌ Tool {tool_name} failed: {e}")
            return {"error": str(e)}
    
    async def get_workflow_context(self) -> Dict[str, Any]:
        """Get workflow context (required before searches)"""
        if self.workflow_context:
            return self.workflow_context
            
        logger.info("🎯 Getting workflow context...")
        
        context = await self.call_tool_safe("get_workflow_context", {})
        if "error" not in context:
            self.workflow_context = context
            logger.info("✅ Workflow context cached")
        
        return context
    
    async def list_available_tools(self) -> List[str]:
        """List all available tools"""
        try:
            tools_result = await self.session.list_tools()
            tools = [tool.name for tool in tools_result.tools]
            logger.info(f"📚 Found {len(tools)} available tools")
            return tools
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
            return []
    
    async def test_connectivity(self) -> bool:
        """Test basic connectivity and functionality"""
        logger.info("🧪 Testing connectivity...")
        
        # Test hello world
        hello_result = await self.call_tool_safe("hello_world", {"name": "MCP Demo Client"})
        if "error" in hello_result:
            return False
        
        # Test API key
        api_result = await self.call_tool_safe("check_api_key", {})
        if "error" in api_result or api_result.get("status") != "success":
            logger.warning("⚠️ API key check failed")
            return False
        
        logger.info("✅ Connectivity test passed")
        return True

class LocationExplorer:
    """Explores specific locations using the MCP client"""
    
    def __init__(self, client: OSMCPClient):
        self.client = client
        
        # Define our example locations
        self.locations = {
            "nottingham": {
                "name": "Nottingham NG1 7FG",
                "postcode": "NG1 7FG",
                "bbox": [-1.16, 52.95, -1.15, 52.96]
            },
            "coventry": {
                "name": "Coventry CV1",
                "postcode": "CV1",
                "bbox": [-1.52, 52.40, -1.50, 52.42]
            }
        }
    
    def format_bbox(self, bbox: List[float]) -> str:
        """Format bounding box for API calls"""
        return ",".join(map(str, bbox))
    
    async def explore_streets(self, location_key: str) -> Dict[str, Any]:
        """Explore streets around a location"""
        location = self.locations[location_key]
        logger.info(f"🛣️ Exploring streets around {location['name']}...")
        
        result = await self.client.call_tool_safe("search_features", {
            "collection_id": "trn-ntwk-street-1",
            "bbox": self.format_bbox(location['bbox']),
            "limit": 8
        })
        
        if "features" in result:
            features = result["features"]
            logger.info(f"✅ Found {len(features)} streets")
            
            # Analyze street types
            street_types = {}
            for feature in features:
                props = feature.get("properties", {})
                road_class = props.get("roadclassification", "Unknown")
                street_types[road_class] = street_types.get(road_class, 0) + 1
            
            logger.info(f"   Street types: {dict(street_types)}")
        
        return result
    
    async def find_a_roads(self, location_key: str) -> Dict[str, Any]:
        """Find A roads specifically"""
        location = self.locations[location_key]
        logger.info(f"🛣️ Finding A roads around {location['name']}...")
        
        result = await self.client.call_tool_safe("search_features", {
            "collection_id": "trn-ntwk-street-1",
            "bbox": self.format_bbox(location['bbox']),
            "filter": "roadclassification = 'A Road'",
            "limit": 5
        })
        
        if "features" in result:
            features = result["features"]
            logger.info(f"✅ Found {len(features)} A roads")
            
            for i, feature in enumerate(features[:3], 1):
                props = feature.get("properties", {})
                name = props.get("designatedname1_text", "Unnamed A road")
                number = props.get("roadnumber", "No number")
                logger.info(f"   {i}. {name} (A{number})")
        
        return result
    
    async def find_retail_areas(self, location_key: str) -> Dict[str, Any]:
        """Find retail areas"""
        location = self.locations[location_key]
        logger.info(f"🏪 Finding retail areas around {location['name']}...")
        
        result = await self.client.call_tool_safe("search_features", {
            "collection_id": "lus-fts-site-1",
            "bbox": self.format_bbox(location['bbox']),
            "filter": "oslandusetiera = 'Retail'",
            "limit": 5
        })
        
        if "features" in result:
            features = result["features"]
            logger.info(f"✅ Found {len(features)} retail areas")
        
        return result
    
    async def search_postcodes(self, postcode_pattern: str) -> Dict[str, Any]:
        """Search for addresses by postcode"""
        logger.info(f"🏠 Searching addresses in {postcode_pattern}...")
        
        result = await self.client.call_tool_safe("search_features", {
            "collection_id": "adr-fts-addressbasepremium-1",
            "filter": f"postcode LIKE '{postcode_pattern}%'",
            "limit": 5
        })
        
        if "features" in result:
            features = result["features"]
            logger.info(f"✅ Found {len(features)} addresses")
        
        return result
    
    async def comprehensive_exploration(self) -> Dict[str, Any]:
        """Perform comprehensive exploration of both locations"""
        logger.info("🌍 Starting comprehensive location exploration...")
        
        results = {}
        
        for location_key, location_info in self.locations.items():
            logger.info(f"\n{'='*50}")
            logger.info(f"📍 Exploring {location_info['name']}")
            logger.info(f"{'='*50}")
            
            location_results = {}
            
            try:
                # Explore streets
                location_results['streets'] = await self.explore_streets(location_key)
                
                # Find A roads
                location_results['a_roads'] = await self.find_a_roads(location_key)
                
                # Find retail areas
                location_results['retail'] = await self.find_retail_areas(location_key)
                
                # Search addresses by postcode
                location_results['addresses'] = await self.search_postcodes(
                    location_info['postcode'].split()[0]  # First part of postcode
                )
                
            except Exception as e:
                logger.error(f"❌ Error exploring {location_info['name']}: {e}")
                location_results['error'] = str(e)
            
            results[location_key] = location_results
            
            # Brief pause between locations
            await asyncio.sleep(1)
        
        return results

async def main():
    """Main demonstration function"""
    logger.info("🚀 Starting OS MCP Client Demonstration")
    logger.info("📍 Using Nottingham NG1 7FG and Coventry CV1 as examples")
    
    # Check environment
    if not os.environ.get("OS_API_KEY"):
        logger.error("❌ OS_API_KEY environment variable not set!")
        logger.info("💡 Get your API key from: https://osdatahub.os.uk/")
        return False
    
    client = OSMCPClient(SERVER_URL, HEADERS)
    explorer = LocationExplorer(client)
    
    try:
        # Connect to server
        await client.connect()
        
        # Test connectivity
        if not await client.test_connectivity():
            logger.error("❌ Connectivity test failed")
            return False
        
        # List available tools
        tools = await client.list_available_tools()
        logger.info(f"🔧 Available tools: {', '.join(tools)}")
        
        # Get workflow context
        workflow_context = await client.get_workflow_context()
        if "error" in workflow_context:
            logger.error("❌ Failed to get workflow context")
            return False
        
        # Perform comprehensive exploration
        exploration_results = await explorer.comprehensive_exploration()
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 EXPLORATION SUMMARY")
        logger.info("="*60)
        
        for location_key, results in exploration_results.items():
            location_name = explorer.locations[location_key]['name']
            logger.info(f"\n📍 {location_name}:")
            
            if 'error' in results:
                logger.info(f"   ❌ Error: {results['error']}")
                continue
            
            for search_type, data in results.items():
                if isinstance(data, dict) and "features" in data:
                    feature_count = len(data["features"])
                    logger.info(f"   🔍 {search_type}: {feature_count} results")
                elif isinstance(data, dict) and "error" in data:
                    logger.info(f"   ❌ {search_type}: {data['error']}")
        
        logger.info("\n🎉 OS MCP Client demonstration completed successfully!")
        logger.info("💡 This demonstrates the full MCP protocol with real UK geospatial data")
        
        return True
        
    except Exception as e:
        logger.error(f"💥 Demonstration failed: {e}")
        return False
    
    finally:
        await client.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("👋 Demonstration interrupted by user")
        exit(0)
    except Exception as e:
        logger.error(f"💥 Demonstration crashed: {e}")
        exit(1)
