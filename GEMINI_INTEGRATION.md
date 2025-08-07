# Google Gemini Integration Guide

## Overview

Connect Google Gemini to your OS MCP Server to search UK geospatial data using natural language queries.

## Integration Methods

### Method 1: Gemini Code Execution (Recommended - Works Now)

This approach uses Gemini's built-in code execution to call your APIs directly.

#### Step 1: Ensure Your Servers Are Running

```bash
# Make sure these are still running:
# Terminal 1: MCP Server (for Claude Desktop)
python src/server.py --transport streamable-http --host 0.0.0.0 --port 8002

# Terminal 2: ChatGPT Bridge (optional, for testing)
python chatgpt_bridge.py
```

#### Step 2: Copy This Code to Gemini

Go to [Google Gemini](https://gemini.google.com/) and paste this Python code:

```python
import requests
import json

# Your OS API configuration
API_KEY = "qLiLe3zOqgDFHT0iIDn1xQqNUc7b7PCO"  # Replace with your full API key
BASE_URL = "https://api.os.uk/features/ngd/ofa/v1"

def search_uk_streets(bbox, limit=10):
    """
    Search for streets in the UK using Ordnance Survey data
    
    Args:
        bbox: Bounding box as "min_lon,min_lat,max_lon,max_lat"
        limit: Maximum number of results (default 10)
    
    Returns:
        List of street names found in the area
    """
    url = f"{BASE_URL}/collections/trn-ntwk-street-1/items"
    params = {
        "bbox": bbox,
        "limit": limit,
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            streets = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                name = props.get('designatedname1_text', 'Unknown')
                town = props.get('townname1_text', '')
                if town:
                    streets.append(f"{name}, {town}")
                else:
                    streets.append(name)
            return {
                "success": True,
                "count": len(streets),
                "streets": streets
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def search_uk_buildings(bbox, limit=5):
    """
    Search for buildings in the UK using Ordnance Survey data
    Requires PSGA access for detailed building data
    """
    url = f"{BASE_URL}/collections/bld-fts-buildingline-1/items"
    params = {
        "bbox": bbox,
        "limit": limit,
        "key": API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "count": data.get('numberReturned', 0),
                "message": f"Found {data.get('numberReturned', 0)} buildings in the area"
            }
        elif response.status_code == 403:
            return {
                "success": False, 
                "error": "Building data requires PSGA access. Only street data available with Open Data license."
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_os_collections():
    """Get available Ordnance Survey data collections"""
    url = f"{BASE_URL}/collections"
    params = {"key": API_KEY}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            collections = []
            for collection in data.get('collections', []):
                collections.append({
                    "id": collection.get('id'),
                    "title": collection.get('title'),
                    "description": collection.get('description', '')[:100]
                })
            return {
                "success": True,
                "count": len(collections),
                "collections": collections[:10]  # Show first 10
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# Example usage functions for Gemini
def demo_coventry_search():
    """Demo: Search for streets around Coventry CV1 3BZ"""
    print("🏙️ Searching streets near Coventry CV1 3BZ...")
    result = search_uk_streets("-1.52,52.40,-1.50,52.42", 8)
    
    if result["success"]:
        print(f"Found {result['count']} streets:")
        for i, street in enumerate(result['streets'], 1):
            print(f"{i}. {street}")
    else:
        print(f"Error: {result['error']}")
    
    return result

def demo_london_search():
    """Demo: Search for streets around central London"""
    print("🌆 Searching streets near London Bridge...")
    result = search_uk_streets("-0.1,51.5,-0.05,51.52", 5)
    
    if result["success"]:
        print(f"Found {result['count']} streets:")
        for i, street in enumerate(result['streets'], 1):
            print(f"{i}. {street}")
    else:
        print(f"Error: {result['error']}")
    
    return result

# Run the demos
print("=== OS Geospatial Data Demo ===")
coventry_result = demo_coventry_search()
print("\n" + "="*40 + "\n")
london_result = demo_london_search()

print("\n=== Available Data Collections ===")
collections = get_os_collections()
if collections["success"]:
    print(f"Your API key provides access to {collections['count']} collections:")
    for collection in collections['collections']:
        print(f"• {collection['title']}")
```

#### Step 3: Ask Gemini Questions

After running the code, you can ask Gemini questions like:

- "What streets did you find near Coventry?"
- "Can you search for streets in a different area? Try Manchester city centre."
- "What collections are available in the OS database?"
- "Explain what PSGA access provides vs Open Data access"

### Method 2: Gemini Function Calling (Advanced)

For more advanced integration, you can use Gemini's function calling feature:

#### Bounding Box Examples for Common UK Cities:

```python
# Copy these bounding boxes for different UK locations:

UK_LOCATIONS = {
    "london_central": "-0.15,51.48,-0.05,51.53",
    "london_bridge": "-0.1,51.5,-0.05,51.52", 
    "manchester_centre": "-2.25,53.47,-2.23,53.49",
    "birmingham_centre": "-1.92,52.47,-1.88,52.49",
    "edinburgh_centre": "-3.21,55.94,-3.17,55.96",
    "coventry_cv1": "-1.52,52.40,-1.50,52.42",
    "bristol_centre": "-2.61,51.44,-2.58,51.46",
    "leeds_centre": "-1.56,53.79,-1.53,53.81",
    "liverpool_centre": "-2.99,53.40,-2.96,53.42",
    "glasgow_centre": "-4.28,55.85,-4.24,55.87"
}

def search_city_streets(city_name, limit=10):
    """Search streets in a specific UK city"""
    bbox = UK_LOCATIONS.get(city_name.lower().replace(" ", "_"))
    if not bbox:
        return {"error": f"City '{city_name}' not found. Available: {list(UK_LOCATIONS.keys())}"}
    
    return search_uk_streets(bbox, limit)

# Example: Search any city
result = search_city_streets("manchester_centre", 8)
print(f"Streets in Manchester: {result}")
```

## Example Gemini Prompts

Once you have the functions loaded, try these prompts:

1. **Basic search**: "Show me streets near Coventry city centre"
2. **Compare areas**: "Find streets in both London Bridge and Manchester centre, then compare them"
3. **Explain data**: "What's the difference between the street data you found and what building data would show?"
4. **Custom area**: "Search for streets in coordinates -1.9,52.47,-1.88,52.49 (Birmingham)"

## Troubleshooting

- **"Connection error"**: Make sure your API key is valid and has the right permissions
- **"HTTP 403"**: Your API key may only have Open Data access (limited collections)
- **"HTTP 401"**: Check your API key format and make sure it's not expired

## Next Steps

- Try asking Gemini to create maps or visualizations of the data
- Use Gemini to analyze patterns in street names or urban planning
- Combine with other data sources for richer analysis
