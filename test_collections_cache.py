#!/usr/bin/env python3
"""Test script to verify collections caching implementation"""

import asyncio
import os
from src.api_service.os_api import OSAPIClient


async def test_collections_caching():
    """Test the collections caching functionality"""
    # Initialize client
    api_client = OSAPIClient()
    
    try:
        await api_client.initialise()
        
        print("Testing Collections Caching...")
        print("-" * 50)
        
        # First call - should fetch from API
        print("\n1. First call to cache_collections():")
        collections_cache = await api_client.cache_collections()
        print(f"   - Cached {len(collections_cache.collections)} collections")
        print(f"   - Raw response contains {len(collections_cache.raw_response.get('collections', []))} total collections")
        
        # Show some examples of filtered collections
        print("\n2. Examples of filtered collections:")
        for i, collection in enumerate(collections_cache.collections[:5]):
            print(f"   {i+1}. {collection.id} - {collection.title}")
        
        # Second call - should return cached data
        print("\n3. Second call to cache_collections() (should use cache):")
        collections_cache2 = await api_client.cache_collections()
        print(f"   - Still have {len(collections_cache2.collections)} collections")
        print(f"   - Cache working: {collections_cache is collections_cache2}")
        
        # Test the filtering logic
        print("\n4. Testing version filtering:")
        # Look for examples of versioned collections
        versioned_examples = {}
        for col in collections_cache.raw_response.get('collections', []):
            col_id = col.get('id', '')
            if '-' in col_id and col_id[-1].isdigit():
                base = col_id.rsplit('-', 1)[0]
                if base not in versioned_examples:
                    versioned_examples[base] = []
                versioned_examples[base].append(col_id)
        
        for base, versions in list(versioned_examples.items())[:3]:
            versions.sort()
            print(f"   - Base: {base}")
            print(f"     All versions: {versions}")
            # Check if only highest version is in filtered
            filtered_ids = [c.id for c in collections_cache.collections]
            kept_versions = [v for v in versions if v in filtered_ids]
            print(f"     Kept in filtered: {kept_versions}")
        
        print("\n✓ Collections caching test completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await api_client.close()


if __name__ == "__main__":
    # Check for API key
    if not os.environ.get("OS_API_KEY"):
        print("Error: OS_API_KEY environment variable not set")
        exit(1)
    
    asyncio.run(test_collections_caching())