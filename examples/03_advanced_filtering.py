#!/usr/bin/env python3
"""
Advanced Filtering Examples for OS MCP Server

This script demonstrates sophisticated CQL filtering and query techniques
using Nottingham NG1 7FG and Coventry CV1 as example locations.

Features demonstrated:
- Complex CQL filter expressions
- Enum-based precise filtering
- Multi-criteria searches
- Error handling and edge cases
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
SERVER_URL = "http://localhost:8000/mcp/"
HEADERS = {"Authorization": "Bearer dev-token"}

# Example locations
NOTTINGHAM_BBOX = [-1.16, 52.95, -1.15, 52.96]
COVENTRY_BBOX = [-1.52, 52.40, -1.50, 52.42]

def extract_text_from_result(result) -> str:
    """Safely extract text from MCP tool result"""
    try:
        if result.content and len(result.content) > 0:
            content = result.content[0]
            if hasattr(content, 'text'):
                return content.text
            else:
                return str(content)
        return "No response"
    except Exception:
        return "Error extracting text"

def format_bbox(bbox: List[float]) -> str:
    """Format bounding box for API calls"""
    return ",".join(map(str, bbox))

async def setup_session():
    """Establish connection and get workflow context"""
    logger.info("🔌 Connecting to OS MCP Server...")
    
    client_manager = streamablehttp_client(SERVER_URL, headers=HEADERS)
    read_stream, write_stream, get_session_id = await client_manager.__aenter__()
    
    session = ClientSession(read_stream, write_stream)
    await session.__aenter__()
    
    await session.initialize()
    session_id = get_session_id()
    logger.info(f"✅ Connected! Session ID: {session_id}")
    
    # Get workflow context
    logger.info("🎯 Getting workflow context...")
    result = await session.call_tool("get_workflow_context", {})
    context_text = extract_text_from_result(result)
    workflow_context = json.loads(context_text)
    logger.info("✅ Workflow context loaded")
    
    return session, client_manager, workflow_context

async def demonstrate_complex_street_filtering(session: ClientSession) -> None:
    """Show complex filtering on street data"""
    logger.info("🛣️  Demonstrating complex street filtering...")
    
    examples = [
        {
            "name": "A Roads that are Open",
            "filter": "roadclassification = 'A Road' AND operationalstate = 'Open'",
            "description": "Find A roads that are currently operational"
        },
        {
            "name": "Primary Roads in Nottingham area",
            "filter": "roadclassification = 'A Road' OR roadclassification = 'Motorway'",
            "bbox": NOTTINGHAM_BBOX,
            "description": "Find major roads (A roads or motorways) around Nottingham"
        },
        {
            "name": "Streets with 'High' in name",
            "filter": "designatedname1_text LIKE '%High%'",
            "description": "Find streets containing 'High' (High Street, High Road, etc.)"
        },
        {
            "name": "Pedestrian-only areas",
            "filter": "roadclassification = 'Pedestrianised Street'",
            "bbox": COVENTRY_BBOX,
            "description": "Find pedestrian-only areas around Coventry"
        }
    ]
    
    for example in examples:
        logger.info(f"\n📋 {example['name']}")
        logger.info(f"   {example['description']}")
        logger.info(f"   Filter: {example['filter']}")
        
        try:
            params = {
                "collection_id": "trn-ntwk-street-1",
                "filter": example['filter'],
                "limit": 5
            }
            
            if 'bbox' in example:
                params['bbox'] = format_bbox(example['bbox'])
                logger.info(f"   Area: {example['bbox']}")
            
            result = await session.call_tool("search_features", params)
            response_text = extract_text_from_result(result)
            data = json.loads(response_text)
            
            if "features" in data and data["features"]:
                features = data["features"]
                logger.info(f"   ✅ Found {len(features)} results")
                
                for i, feature in enumerate(features[:2]):
                    props = feature.get("properties", {})
                    name = props.get("designatedname1_text", "Unnamed")
                    classification = props.get("roadclassification", "Unknown")
                    state = props.get("operationalstate", "Unknown")
                    logger.info(f"      {i+1}. {name} ({classification}, {state})")
            else:
                logger.info(f"   ℹ️ No results found")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
        
        await asyncio.sleep(0.5)

async def demonstrate_land_use_enum_filtering(session: ClientSession) -> None:
    """Show enum-based land use filtering"""
    logger.info("\n🏢 Demonstrating land use enum filtering...")
    
    # These enum values should come from the workflow context in practice
    land_use_examples = [
        {
            "name": "Entertainment venues",
            "filter": "oslandusetertiarygroup = 'Cinema' OR oslandusetertiarygroup = 'Theatre'",
            "bbox": NOTTINGHAM_BBOX,
            "description": "Find cinemas and theatres in Nottingham"
        },
        {
            "name": "Retail locations",
            "filter": "oslandusetiera = 'Retail'",
            "bbox": COVENTRY_BBOX,
            "description": "Find retail areas in Coventry"
        },
        {
            "name": "Transport hubs",
            "filter": "oslandusetertiarygroup = 'Transport'",
            "description": "Find transport facilities"
        },
        {
            "name": "Educational facilities",
            "filter": "oslandusetertiarygroup = 'Education'",
            "bbox": NOTTINGHAM_BBOX,
            "description": "Find schools, universities etc. in Nottingham"
        }
    ]
    
    for example in land_use_examples:
        logger.info(f"\n📋 {example['name']}")
        logger.info(f"   {example['description']}")
        logger.info(f"   Filter: {example['filter']}")
        
        try:
            params = {
                "collection_id": "lus-fts-site-1",
                "filter": example['filter'],
                "limit": 3
            }
            
            if 'bbox' in example:
                params['bbox'] = format_bbox(example['bbox'])
            
            result = await session.call_tool("search_features", params)
            response_text = extract_text_from_result(result)
            data = json.loads(response_text)
            
            if "features" in data and data["features"]:
                features = data["features"]
                logger.info(f"   ✅ Found {len(features)} results")
                
                for i, feature in enumerate(features):
                    props = feature.get("properties", {})
                    name = props.get("distname1", "Unnamed location")
                    tertiary = props.get("oslandusetertiarygroup", "Unknown type")
                    logger.info(f"      {i+1}. {name} ({tertiary})")
            else:
                logger.info(f"   ℹ️ No results found")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
        
        await asyncio.sleep(0.5)

async def demonstrate_address_searches(session: ClientSession) -> None:
    """Show address-based searching"""
    logger.info("\n🏠 Demonstrating address searches...")
    
    address_examples = [
        {
            "name": "Nottingham postcodes",
            "filter": "postcode LIKE 'NG1%'",
            "description": "Find addresses in NG1 area"
        },
        {
            "name": "Coventry postcodes", 
            "filter": "postcode LIKE 'CV1%'",
            "description": "Find addresses in CV1 area"
        }
    ]
    
    for example in address_examples:
        logger.info(f"\n📋 {example['name']}")
        logger.info(f"   {example['description']}")
        logger.info(f"   Filter: {example['filter']}")
        
        try:
            result = await session.call_tool("search_features", {
                "collection_id": "adr-fts-addressbasepremium-1",
                "filter": example['filter'],
                "limit": 5
            })
            
            response_text = extract_text_from_result(result)
            data = json.loads(response_text)
            
            if "features" in data and data["features"]:
                features = data["features"]
                logger.info(f"   ✅ Found {len(features)} addresses")
                
                for i, feature in enumerate(features[:2]):
                    props = feature.get("properties", {})
                    address = props.get("address", "No address")
                    postcode = props.get("postcode", "No postcode")
                    logger.info(f"      {i+1}. {address}, {postcode}")
            else:
                logger.info(f"   ℹ️ No addresses found")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
        
        await asyncio.sleep(0.5)

async def demonstrate_spatial_queries(session: ClientSession) -> None:
    """Show spatial relationship queries"""
    logger.info("\n🌍 Demonstrating spatial queries...")
    
    spatial_examples = [
        {
            "name": "Features in Nottingham center",
            "collection": "lus-fts-site-1",
            "bbox": [-1.155, 52.954, -1.153, 52.956],  # Very tight around center
            "description": "Features in tight Nottingham city center area"
        },
        {
            "name": "Streets in Coventry center",
            "collection": "trn-ntwk-street-1", 
            "bbox": [-1.512, 52.407, -1.508, 52.409],  # Tight Coventry center
            "description": "Streets in central Coventry"
        }
    ]
    
    for example in spatial_examples:
        logger.info(f"\n📋 {example['name']}")
        logger.info(f"   {example['description']}")
        logger.info(f"   Bbox: {example['bbox']}")
        
        try:
            result = await session.call_tool("search_features", {
                "collection_id": example['collection'],
                "bbox": format_bbox(example['bbox']),
                "limit": 8
            })
            
            response_text = extract_text_from_result(result)
            data = json.loads(response_text)
            
            if "features" in data and data["features"]:
                features = data["features"]
                logger.info(f"   ✅ Found {len(features)} features in area")
                
                # Show summary of what was found
                if example['collection'] == "lus-fts-site-1":
                    land_uses = set()
                    for feature in features:
                        props = feature.get("properties", {})
                        land_use = props.get("oslandusetertiarygroup", "Unknown")
                        if land_use != "Unknown":
                            land_uses.add(land_use)
                    logger.info(f"      Land use types: {', '.join(sorted(land_uses))}")
                
                elif example['collection'] == "trn-ntwk-street-1":
                    road_types = set()
                    for feature in features:
                        props = feature.get("properties", {})
                        road_type = props.get("roadclassification", "Unknown")
                        if road_type != "Unknown":
                            road_types.add(road_type)
                    logger.info(f"      Road types: {', '.join(sorted(road_types))}")
            else:
                logger.info(f"   ℹ️ No features found in area")
                
        except Exception as e:
            logger.error(f"   ❌ Error: {e}")
        
        await asyncio.sleep(0.5)

async def demonstrate_error_handling(session: ClientSession) -> None:
    """Show error handling for invalid queries"""
    logger.info("\n⚠️  Demonstrating error handling...")
    
    error_examples = [
        {
            "name": "Invalid collection ID",
            "params": {
                "collection_id": "invalid-collection-id",
                "limit": 5
            },
            "expected": "Collection not found error"
        },
        {
            "name": "Invalid filter syntax",
            "params": {
                "collection_id": "trn-ntwk-street-1",
                "filter": "invalid_field = 'test'",
                "limit": 5  
            },
            "expected": "Filter error"
        },
        {
            "name": "Invalid bbox format",
            "params": {
                "collection_id": "trn-ntwk-street-1",
                "bbox": "invalid-bbox",
                "limit": 5
            },
            "expected": "Bbox format error"
        }
    ]
    
    for example in error_examples:
        logger.info(f"\n📋 {example['name']}")
        logger.info(f"   Expected: {example['expected']}")
        
        try:
            result = await session.call_tool("search_features", example['params'])
            response_text = extract_text_from_result(result)
            data = json.loads(response_text)
            
            if "error" in data:
                logger.info(f"   ✅ Correctly caught error: {data['error'][:100]}...")
            else:
                logger.warning(f"   ⚠️ Expected error but got: {len(data.get('features', []))} features")
                
        except Exception as e:
            logger.info(f"   ✅ Exception handled: {str(e)[:100]}...")
        
        await asyncio.sleep(0.5)

async def main():
    """Main demonstration function"""
    logger.info("🚀 Starting Advanced Filtering Examples")
    logger.info("🎯 Using Nottingham NG1 7FG and Coventry CV1 for demonstrations")
    
    session = None
    client_manager = None
    
    try:
        # Setup session
        session, client_manager, workflow_context = await setup_session()
        
        # Run all demonstrations
        await demonstrate_complex_street_filtering(session)
        await demonstrate_land_use_enum_filtering(session)
        await demonstrate_address_searches(session)
        await demonstrate_spatial_queries(session)
        await demonstrate_error_handling(session)
        
        logger.info("\n🎉 Advanced filtering examples completed successfully!")
        logger.info("💡 These examples show the power of precise CQL filtering")
        logger.info("💡 In practice, use get_collection_queryables() to see available enum values")
        
    except Exception as e:
        logger.error(f"💥 Advanced filtering examples failed: {e}")
        raise
    
    finally:
        # Clean up
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
    
    # Run the advanced filtering examples
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Advanced filtering examples interrupted by user")
    except Exception as e:
        logger.error(f"💥 Advanced filtering examples failed: {e}")
        exit(1)
