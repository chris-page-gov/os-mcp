#!/usr/bin/env python3
"""
Location-Based Search Examples for OS MCP Server

This script demonstrates practical searches using Nottingham NG1 7FG and Coventry CV1
as real UK locations to showcase the OS MCP Server's geospatial capabilities.

Features demonstrated:
- Street network searches
- Building and land use queries  
- Bounding box area searches
- Filter-based location finding
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SERVER_URL = "http://localhost:8000/mcp/"
HEADERS = {"Authorization": "Bearer dev-token"}

# Example locations with coordinates (WGS84 - EPSG:4326)
NOTTINGHAM_LOCATION = {
    "name": "Nottingham NG1 7FG", 
    "postcode": "NG1 7FG",
    "lat": 52.9548,
    "lon": -1.1543,
    "bbox": [-1.16, 52.95, -1.15, 52.96]  # [min_lon, min_lat, max_lon, max_lat]
}

COVENTRY_LOCATION = {
    "name": "Coventry CV1",
    "postcode": "CV1",
    "lat": 52.4081,
    "lon": -1.5101,
    "bbox": [-1.52, 52.40, -1.50, 52.42]
}

def extract_text_from_result(result) -> str:
    """Safely extract text from MCP tool result"""
    if result.content and len(result.content) > 0:
        content = result.content[0]
        if hasattr(content, 'text'):
            return content.text
        else:
            return str(content)
    return "No response"

def format_bbox(bbox: List[float]) -> str:
    """Format bounding box for API calls"""
    return ",".join(map(str, bbox))

async def setup_session():
    """Establish a connection and get workflow context"""
    logger.info("🔌 Connecting to OS MCP Server...")
    
    client_manager = streamablehttp_client(SERVER_URL, headers=HEADERS)
    read_stream, write_stream, get_session_id = await client_manager.__aenter__()
    
    session = ClientSession(read_stream, write_stream)
    await session.__aenter__()
    
    # Initialize
    await session.initialize()
    session_id = get_session_id()
    logger.info(f"✅ Connected! Session ID: {session_id}")
    
    # Get workflow context (required before any searches)
    logger.info("🎯 Getting workflow context...")
    result = await session.call_tool("get_workflow_context", {})
    context_text = extract_text_from_result(result)
    workflow_context = json.loads(context_text)
    logger.info("✅ Workflow context loaded")
    
    return session, client_manager, workflow_context

async def search_streets_in_area(session: ClientSession, location: Dict[str, Any]) -> Dict[str, Any]:
    """Search for streets in the specified area"""
    logger.info(f"🛣️  Searching for streets around {location['name']}...")
    
    try:
        bbox_str = format_bbox(location['bbox'])
        
        result = await session.call_tool("search_features", {
            "collection_id": "trn-ntwk-street-1",
            "bbox": bbox_str,
            "limit": 10
        })
        
        response_text = extract_text_from_result(result)
        street_data = json.loads(response_text)
        
        if "features" in street_data:
            features = street_data["features"]
            logger.info(f"✅ Found {len(features)} streets around {location['name']}")
            
            # Show some example streets
            for i, feature in enumerate(features[:3]):
                props = feature.get("properties", {})
                street_name = props.get("designatedname1_text", "Unnamed street")
                road_class = props.get("roadclassification", "Unknown classification")
                logger.info(f"  {i+1}. {street_name} ({road_class})")
        else:
            logger.warning(f"⚠️ No streets found around {location['name']}")
            
        return street_data
        
    except Exception as e:
        logger.error(f"❌ Street search failed for {location['name']}: {e}")
        return {"error": str(e)}

async def find_a_roads(session: ClientSession, location: Dict[str, Any]) -> Dict[str, Any]:
    """Find A roads specifically in the area"""
    logger.info(f"🛣️  Looking for A roads around {location['name']}...")
    
    try:
        bbox_str = format_bbox(location['bbox'])
        
        result = await session.call_tool("search_features", {
            "collection_id": "trn-ntwk-street-1", 
            "bbox": bbox_str,
            "filter": "roadclassification = 'A Road'",
            "limit": 5
        })
        
        response_text = extract_text_from_result(result)
        road_data = json.loads(response_text)
        
        if "features" in road_data:
            features = road_data["features"]
            logger.info(f"✅ Found {len(features)} A roads around {location['name']}")
            
            for i, feature in enumerate(features):
                props = feature.get("properties", {})
                road_name = props.get("designatedname1_text", "Unnamed A road")
                road_number = props.get("roadnumber", "No number")
                logger.info(f"  {i+1}. {road_name} (A{road_number})")
        else:
            logger.info(f"ℹ️ No A roads found in the immediate area of {location['name']}")
            
        return road_data
        
    except Exception as e:
        logger.error(f"❌ A road search failed for {location['name']}: {e}")
        return {"error": str(e)}

async def find_land_use_features(session: ClientSession, location: Dict[str, Any], land_use_type: str) -> Dict[str, Any]:
    """Search for specific land use features"""
    logger.info(f"🏢 Searching for {land_use_type} around {location['name']}...")
    
    try:
        bbox_str = format_bbox(location['bbox'])
        
        result = await session.call_tool("search_features", {
            "collection_id": "lus-fts-site-1",
            "bbox": bbox_str,
            "filter": f"oslandusetertiarygroup = '{land_use_type}'",
            "limit": 5
        })
        
        response_text = extract_text_from_result(result)
        land_use_data = json.loads(response_text)
        
        if "features" in land_use_data:
            features = land_use_data["features"]
            logger.info(f"✅ Found {len(features)} {land_use_type.lower()} locations around {location['name']}")
            
            for i, feature in enumerate(features):
                props = feature.get("properties", {})
                site_name = props.get("distname1", f"{land_use_type} site")
                logger.info(f"  {i+1}. {site_name}")
        else:
            logger.info(f"ℹ️ No {land_use_type.lower()} locations found around {location['name']}")
            
        return land_use_data
        
    except Exception as e:
        logger.error(f"❌ {land_use_type} search failed for {location['name']}: {e}")
        return {"error": str(e)}

async def find_buildings(session: ClientSession, location: Dict[str, Any]) -> Dict[str, Any]:
    """Search for building outlines in the area"""
    logger.info(f"🏗️  Searching for buildings around {location['name']}...")
    
    try:
        bbox_str = format_bbox(location['bbox'])
        
        result = await session.call_tool("search_features", {
            "collection_id": "bld-fts-buildingline-1",
            "bbox": bbox_str,
            "limit": 10
        })
        
        response_text = extract_text_from_result(result)
        building_data = json.loads(response_text)
        
        if "features" in building_data:
            features = building_data["features"]
            logger.info(f"✅ Found {len(features)} building outlines around {location['name']}")
        else:
            logger.info(f"ℹ️ No building data found around {location['name']}")
            
        return building_data
        
    except Exception as e:
        logger.error(f"❌ Building search failed for {location['name']}: {e}")
        return {"error": str(e)}

async def search_by_street_name(session: ClientSession, street_pattern: str) -> Dict[str, Any]:
    """Search for streets by name pattern"""
    logger.info(f"🔍 Searching for streets matching '{street_pattern}'...")
    
    try:
        result = await session.call_tool("search_features", {
            "collection_id": "trn-ntwk-street-1",
            "filter": f"designatedname1_text LIKE '%{street_pattern}%'",
            "limit": 10
        })
        
        response_text = extract_text_from_result(result)
        street_data = json.loads(response_text)
        
        if "features" in street_data:
            features = street_data["features"]
            logger.info(f"✅ Found {len(features)} streets matching '{street_pattern}'")
            
            for i, feature in enumerate(features[:5]):
                props = feature.get("properties", {})
                street_name = props.get("designatedname1_text", "Unknown street")
                road_class = props.get("roadclassification", "Unknown")
                logger.info(f"  {i+1}. {street_name} ({road_class})")
        else:
            logger.info(f"ℹ️ No streets found matching '{street_pattern}'")
            
        return street_data
        
    except Exception as e:
        logger.error(f"❌ Street name search failed: {e}")
        return {"error": str(e)}

async def demonstrate_location_searches():
    """Main demonstration of location-based searches"""
    logger.info("🚀 Starting Location-Based Search Examples")
    logger.info("📍 Using Nottingham NG1 7FG and Coventry CV1 as example locations")
    
    session = None
    client_manager = None
    
    try:
        # Setup session and get workflow context
        session, client_manager, workflow_context = await setup_session()
        
        # Demonstrate searches for both locations
        for location in [NOTTINGHAM_LOCATION, COVENTRY_LOCATION]:
            logger.info(f"\n{'='*50}")
            logger.info(f"🌍 Exploring {location['name']}")
            logger.info(f"📍 Coordinates: {location['lat']}, {location['lon']}")
            logger.info(f"📦 Search area: {location['bbox']}")
            logger.info(f"{'='*50}")
            
            # 1. General street search
            await search_streets_in_area(session, location)
            
            # 2. Find A roads specifically
            await find_a_roads(session, location)
            
            # 3. Find retail locations
            await find_land_use_features(session, location, "Retail")
            
            # 4. Find transport hubs  
            await find_land_use_features(session, location, "Transport")
            
            # 5. Find building outlines
            await find_buildings(session, location)
            
            await asyncio.sleep(1)  # Brief pause between locations
        
        # Additional pattern-based searches
        logger.info(f"\n{'='*50}")
        logger.info("🔍 Pattern-Based Street Searches")
        logger.info(f"{'='*50}")
        
        # Search for High Streets
        await search_by_street_name(session, "High")
        
        # Search for Market Streets  
        await search_by_street_name(session, "Market")
        
        logger.info("\n🎉 Location search examples completed successfully!")
        logger.info("💡 Next steps: Try advanced filtering examples in 03_advanced_filtering.py")
        
    except Exception as e:
        logger.error(f"💥 Location searches failed: {e}")
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
    
    # Run the location searches
    try:
        asyncio.run(demonstrate_location_searches())
    except KeyboardInterrupt:
        logger.info("👋 Location searches interrupted by user")
    except Exception as e:
        logger.error(f"💥 Location searches failed: {e}")
        exit(1)
