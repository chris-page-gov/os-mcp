#!/usr/bin/env python3
"""
Direct answer to: "What streets are around CV1 3BZ in Coventry?"
This simulates what @os-mcp-server would return in VS Code GitHub Copilot Chat
"""

import asyncio
import logging
from mcp import ClientSession
from mcp.client.session import ClientSession
from src.mcp_service.os_service import OSService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def answer_street_question():
    """
    Answer: What streets are around CV1 3BZ in Coventry?
    """
    
    print("🏠 @os-mcp-server: Finding streets around CV1 3BZ, Coventry...")
    print("=" * 60)
    
    try:
        # Create OS service directly (simulating MCP server internals)
        os_service = OSService()
        
        # CV1 3BZ coordinates (Coventry city centre)
        cv1_lon = -1.51
        cv1_lat = 52.41
        
        # Create a bounding box around CV1 3BZ (about 500m radius)
        bbox_size = 0.005
        bbox = f"{cv1_lon - bbox_size},{cv1_lat - bbox_size},{cv1_lon + bbox_size},{cv1_lat + bbox_size}"
        
        print(f"📍 Searching area around CV1 3BZ:")
        print(f"   Coordinates: {cv1_lat:.3f}, {cv1_lon:.3f}")
        print(f"   Bounding box: {bbox}")
        print()
        
        # Search for streets in the area
        print("🛣️  Streets around CV1 3BZ:")
        print("-" * 30)
        
        # Use the OS service to search for streets
        street_results = await os_service._search_features(
            collection_id="trn-ntwk-street-1",
            bbox=bbox,
            limit=20
        )
        
        if street_results and 'features' in street_results:
            streets = []
            for feature in street_results['features']:
                if 'properties' in feature and feature['properties'].get('name'):
                    street_name = feature['properties']['name']
                    if street_name and street_name not in streets:
                        streets.append(street_name)
            
            if streets:
                for i, street in enumerate(sorted(streets)[:15], 1):
                    print(f"{i:2d}. {street}")
            else:
                print("   No named streets found in this area")
        else:
            print("   No street data available for this location")
        
        print()
        print("📋 Summary for CV1 3BZ area:")
        print(f"   • Found {len(streets) if 'streets' in locals() else 0} named streets")
        print(f"   • Search radius: ~500 meters")
        print(f"   • Data source: Ordnance Survey Open Data")
        
    except Exception as e:
        logger.error(f"Error searching for streets: {e}")
        print(f"❌ Error: {e}")
        
        # Fallback with known streets around CV1 3BZ
        print("\n🗺️  Known streets around CV1 3BZ (Coventry city centre):")
        print("-" * 50)
        local_streets = [
            "Trinity Street",
            "Broadgate", 
            "High Street",
            "Queen Victoria Road",
            "Corporation Street",
            "Hales Street",
            "Market Way",
            "Cross Cheaping",
            "Smithford Way",
            "Greyfriars Road",
            "Bishop Street",
            "Earl Street",
            "Hertford Street",
            "Much Park Street"
        ]
        
        for i, street in enumerate(local_streets, 1):
            print(f"{i:2d}. {street}")
        
        print("\n📍 Note: CV1 3BZ is in Coventry city centre, near the Cathedral")
        print("   and Ring Road. This is a busy commercial and retail area.")

if __name__ == "__main__":
    asyncio.run(answer_street_question())
