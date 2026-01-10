# MCP-Apps Integration Starter Code

This file contains practical starter code for integrating MCP-Apps into your existing os-mcp server.

## 1. Directory Structure to Create

```
src/
├── server.py                    # Update this file
├── ui_resources.py             # NEW: UI resource management
├── ui/                         # NEW: Widget HTML files
│   ├── geography_selector.html
│   ├── statistics_dashboard.html
│   └── feature_inspector.html
├── tools/
│   ├── geography_tools.py      # NEW: Geographic selection tools
│   └── ons_tools.py           # NEW: ONS statistics tools
└── clients/
    └── ons_client.py          # NEW: ONS API wrapper
```

## 2. Updated server.py (Integration Points)

```python
# src/server.py
"""
OS/ONS MCP Server with MCP-Apps Support
"""
import os
import logging
from pathlib import Path
from fastmcp import FastMCP

# Import UI resources module
from .ui_resources import register_ui_resources

# Import new tools
from .tools.geography_tools import register_geography_tools
from .tools.ons_tools import register_ons_tools

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastMCP
mcp = FastMCP(
    "os-ons-api",
    dependencies=[
        "fastmcp[all]",
        "aiohttp",
        "aiofiles",
        "geojson",
        "shapely"
    ]
)

async def initialize_server():
    """Initialize server with all resources and tools"""
    logger.info("Initializing OS/ONS MCP Server with MCP-Apps support...")
    
    # Register UI resources (MCP-Apps)
    logger.info("Registering UI resources...")
    await register_ui_resources(mcp)
    
    # Register geography tools (including UI-enabled tools)
    logger.info("Registering geography tools...")
    await register_geography_tools(mcp)
    
    # Register ONS statistics tools
    logger.info("Registering ONS statistics tools...")
    await register_ons_tools(mcp)
    
    # Register existing tools (from your current implementation)
    # ... keep your existing tool registrations ...
    
    logger.info("Server initialization complete")

# Run initialization on startup
@mcp.on_startup
async def startup():
    await initialize_server()

if __name__ == "__main__":
    import sys
    
    # Get transport from command line
    transport = "stdio"  # default
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        transport = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "stdio"
    
    # Run server
    if transport == "stdio":
        mcp.run_stdio()
    elif transport in ["streamable-http", "http"]:
        host = "127.0.0.1"
        port = 8000
        if "--host" in sys.argv:
            idx = sys.argv.index("--host")
            host = sys.argv[idx + 1]
        if "--port" in sys.argv:
            idx = sys.argv.index("--port")
            port = int(sys.argv[idx + 1])
        
        logger.info(f"Starting HTTP server on {host}:{port}")
        mcp.run_http(host=host, port=port)
    else:
        logger.error(f"Unknown transport: {transport}")
        sys.exit(1)
```

## 3. UI Resources Module

```python
# src/ui_resources.py
"""
MCP-Apps UI Resource Management

This module handles registration and serving of UI resources (widgets)
that provide interactive interfaces for geographic selection and visualization.
"""
import logging
from pathlib import Path
from typing import Optional
import aiofiles

logger = logging.getLogger(__name__)

# Base directory for UI resources
UI_DIR = Path(__file__).parent / "ui"

async def load_ui_resource(filename: str) -> str:
    """
    Load UI resource HTML file from disk.
    
    Args:
        filename: Name of HTML file (e.g., 'geography_selector.html')
    
    Returns:
        HTML content as string
    
    Raises:
        FileNotFoundError: If the resource file doesn't exist
    """
    filepath = UI_DIR / filename
    if not filepath.exists():
        raise FileNotFoundError(f"UI resource not found: {filepath}")
    
    async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
        return await f.read()

async def register_ui_resources(mcp):
    """
    Register all UI resources with the MCP server.
    
    UI resources use the 'ui://' URI scheme and are rendered in sandboxed
    iframes by MCP hosts that support the MCP-Apps extension.
    
    Args:
        mcp: FastMCP instance
    """
    logger.info("Loading UI resources from %s", UI_DIR)
    
    # Ensure UI directory exists
    UI_DIR.mkdir(exist_ok=True)
    
    # 1. Geography Selector Widget
    try:
        geography_selector_html = await load_ui_resource("geography_selector.html")
        
        await mcp.add_resource(
            uri="ui://os-ons/geography-selector",
            name="Geographic Area Selector",
            description=(
                "Interactive map widget for selecting UK geographic areas at various "
                "administrative levels (Parliamentary Constituencies, Local Authorities, "
                "Wards, Output Areas, etc.). Features hierarchical selection, search by "
                "name or postcode, and visual boundary display."
            ),
            mime_type="text/html;profile=mcp-app",
            content=geography_selector_html,
            annotations={
                "audience": ["user"],  # This UI is for user interaction
                "priority": 1.0,       # High priority for discovery
                "capabilities": [
                    "hierarchical_selection",
                    "boundary_visualization", 
                    "search",
                    "multi_select"
                ]
            }
        )
        logger.info("✓ Registered: ui://os-ons/geography-selector")
        
    except FileNotFoundError as e:
        logger.warning("Geography selector widget not found, skipping: %s", e)
    
    # 2. Statistics Dashboard Widget
    try:
        dashboard_html = await load_ui_resource("statistics_dashboard.html")
        
        await mcp.add_resource(
            uri="ui://os-ons/statistics-dashboard",
            name="Statistics Dashboard",
            description=(
                "Interactive dashboard for visualizing ONS statistics across selected "
                "geographic areas. Features multiple chart types, comparative analysis, "
                "filtering, and data export capabilities."
            ),
            mime_type="text/html;profile=mcp-app",
            content=dashboard_html,
            annotations={
                "audience": ["user"],
                "priority": 0.8,
                "capabilities": [
                    "data_visualization",
                    "comparison",
                    "filtering",
                    "export"
                ]
            }
        )
        logger.info("✓ Registered: ui://os-ons/statistics-dashboard")
        
    except FileNotFoundError as e:
        logger.warning("Statistics dashboard widget not found, skipping: %s", e)
    
    # 3. Feature Inspector Widget
    try:
        inspector_html = await load_ui_resource("feature_inspector.html")
        
        await mcp.add_resource(
            uri="ui://os-ons/feature-inspector",
            name="Feature Inspector",
            description=(
                "Detailed view of OS NGD features with properties, linked identifiers, "
                "and spatial relationships. Includes navigation between linked features "
                "and export functionality."
            ),
            mime_type="text/html;profile=mcp-app",
            content=inspector_html,
            annotations={
                "audience": ["user"],
                "priority": 0.6,
                "capabilities": [
                    "property_display",
                    "linked_identifier_navigation",
                    "spatial_relationships",
                    "export"
                ]
            }
        )
        logger.info("✓ Registered: ui://os-ons/feature-inspector")
        
    except FileNotFoundError as e:
        logger.warning("Feature inspector widget not found, skipping: %s", e)
    
    logger.info("UI resource registration complete")

# Utility function for dynamic UI resource generation
async def generate_ui_config(
    widget_uri: str,
    config: dict
) -> dict:
    """
    Generate standardized configuration for UI widgets.
    
    Args:
        widget_uri: URI of the UI resource (e.g., 'ui://os-ons/geography-selector')
        config: Widget-specific configuration
    
    Returns:
        Formatted configuration dict for tool response
    """
    return {
        "status": "ui_pending",
        "widget": {
            "uri": widget_uri,
            "config": config
        },
        "_meta": {
            "uiResourceUris": [widget_uri],
            "audience": ["user"]
        }
    }
```

## 4. Geography Tools (with UI Support)

```python
# src/tools/geography_tools.py
"""
Geographic selection tools with MCP-Apps UI support
"""
import logging
from typing import Dict, Any, Optional, List
import aiohttp
from fastmcp import Context

logger = logging.getLogger(__name__)

# ONS Geography API base URL
ONS_GEOGRAPHY_API_BASE = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services"

# Geographic level configuration
GEOGRAPHIC_LEVELS = {
    "parl_const": {
        "name": "Parliamentary Constituencies",
        "service": "WD24_LAD24_PCON24_EW_BFC",
        "code_field": "PCON24CD",
        "name_field": "PCON24NM"
    },
    "local_auth": {
        "name": "Local Authorities",
        "service": "LAD24_BFC",
        "code_field": "LAD24CD",
        "name_field": "LAD24NM"
    },
    "ward": {
        "name": "Wards",
        "service": "WD24_BFC",
        "code_field": "WD24CD",
        "name_field": "WD24NM"
    },
    "lsoa": {
        "name": "Lower Super Output Areas",
        "service": "LSOA21_BFC",
        "code_field": "LSOA21CD",
        "name_field": "LSOA21NM"
    },
    "msoa": {
        "name": "Middle Super Output Areas",
        "service": "MSOA21_BFC",
        "code_field": "MSOA21CD",
        "name_field": "MSOA21NM"
    },
    "oa": {
        "name": "Output Areas",
        "service": "OA21_BFC",
        "code_field": "OA21CD",
        "name_field": "OA21NM"
    }
}

async def fetch_boundary_geojson(
    level: str,
    gss_code: Optional[str] = None,
    bbox: Optional[str] = None,
    simplification: float = 0.001
) -> Dict[str, Any]:
    """
    Fetch boundary GeoJSON from ONS Geography API.
    
    Args:
        level: Geographic level (parl_const, local_auth, ward, lsoa, msoa, oa)
        gss_code: Optional GSS code to fetch specific area
        bbox: Optional bounding box as 'west,south,east,north'
        simplification: Geometry simplification tolerance (smaller = more detail)
    
    Returns:
        GeoJSON FeatureCollection
    """
    if level not in GEOGRAPHIC_LEVELS:
        raise ValueError(f"Invalid geographic level: {level}")
    
    config = GEOGRAPHIC_LEVELS[level]
    service_url = f"{ONS_GEOGRAPHY_API_BASE}/{config['service']}/FeatureServer/0/query"
    
    # Build query parameters
    params = {
        "outFields": "*",
        "f": "geojson",
        "geometryPrecision": 6,
    }
    
    # Add where clause
    if gss_code:
        params["where"] = f"{config['code_field']}='{gss_code}'"
    elif bbox:
        west, south, east, north = map(float, bbox.split(','))
        params["geometry"] = f"{west},{south},{east},{north}"
        params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"
    else:
        params["where"] = "1=1"  # Get all features
    
    # Fetch data
    async with aiohttp.ClientSession() as session:
        async with session.get(service_url, params=params) as resp:
            if resp.status != 200:
                raise Exception(f"ONS API error: {resp.status}")
            
            data = await resp.json()
            logger.info(
                "Fetched %d features for level=%s",
                len(data.get("features", [])),
                level
            )
            return data

async def register_geography_tools(mcp):
    """Register all geography-related tools"""
    
    @mcp.tool(
        description=(
            "Interactively select UK geographic areas using a map widget. "
            "Supports hierarchical selection across multiple administrative levels, "
            "search by name or postcode, and visual boundary display."
        )
    )
    async def select_geographic_area(
        level: str = "local_auth",
        initial_location: Optional[Dict[str, float]] = None,
        search_term: Optional[str] = None,
        multi_select: bool = True
    ) -> Dict[str, Any]:
        """
        Opens interactive map widget for selecting geographic areas.
        
        The widget provides:
        - Visual map with boundary overlays
        - Hierarchical navigation between geographic levels  
        - Search by area name or postcode
        - Multi-select capability
        - Export selected areas
        
        Args:
            level: Geographic level to display. Options: parl_const (Parliamentary 
                   Constituencies), local_auth (Local Authorities), ward, lsoa 
                   (Lower Super Output Areas), msoa (Middle Super Output Areas), 
                   oa (Output Areas). Default: local_auth
            initial_location: Optional starting map position with keys: 
                            lat (latitude), lng (longitude), zoom (zoom level).
                            Default: UK-wide view centered on Birmingham
            search_term: Optional search query to pre-filter areas
            multi_select: Allow selection of multiple areas. Default: True
        
        Returns:
            Configuration for the geography selector widget. When user confirms
            selection, the widget will return selected areas with their GSS codes,
            names, and boundary geometries.
        
        Examples:
            # Open widget at default UK view for Local Authority selection
            select_geographic_area()
            
            # Start at specific location (Coventry) at ward level
            select_geographic_area(
                level="ward",
                initial_location={"lat": 52.4081, "lng": -1.5106, "zoom": 11}
            )
            
            # Pre-filter to areas matching search term
            select_geographic_area(
                level="local_auth",
                search_term="Birmingham"
            )
        """
        # Validate level
        if level not in GEOGRAPHIC_LEVELS:
            return {
                "error": f"Invalid level '{level}'. Must be one of: {', '.join(GEOGRAPHIC_LEVELS.keys())}",
                "available_levels": list(GEOGRAPHIC_LEVELS.keys())
            }
        
        # Default initial view (Birmingham, UK)
        if initial_location is None:
            initial_location = {
                "lat": 52.4862,
                "lng": -1.8904,
                "zoom": 6
            }
        
        # Build widget configuration
        config = {
            "level": level,
            "level_name": GEOGRAPHIC_LEVELS[level]["name"],
            "initial_view": initial_location,
            "search_term": search_term,
            "features": {
                "multi_select": multi_select,
                "show_hierarchy": True,
                "search_enabled": True,
                "show_codes": True
            },
            "available_levels": [
                {"value": k, "label": v["name"]}
                for k, v in GEOGRAPHIC_LEVELS.items()
            ]
        }
        
        return {
            "status": "selection_pending",
            "config": config,
            "instructions": (
                f"An interactive map widget will open showing {GEOGRAPHIC_LEVELS[level]['name']}. "
                "Click on areas to select them, use the dropdown to change geographic levels, "
                "or use the search box to find specific locations. Click 'Confirm Selection' "
                "when you're ready to proceed with your chosen areas."
            ),
            "_meta": {
                "uiResourceUris": ["ui://os-ons/geography-selector"],
                "audience": ["user"]
            }
        }
    
    @mcp.tool()
    async def fetch_boundaries(
        level: str,
        codes: Optional[List[str]] = None,
        bbox: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fetch boundary geometries for geographic areas.
        
        This is a data retrieval tool (not UI) used by widgets or for direct
        data access. Returns GeoJSON with area boundaries.
        
        Args:
            level: Geographic level (parl_const, local_auth, ward, lsoa, msoa, oa)
            codes: Optional list of GSS codes to fetch specific areas
            bbox: Optional bounding box as 'west,south,east,north' to limit query
        
        Returns:
            GeoJSON FeatureCollection with boundary geometries
        """
        try:
            if codes:
                # Fetch specific areas
                features = []
                for code in codes:
                    geojson = await fetch_boundary_geojson(level, gss_code=code)
                    features.extend(geojson.get("features", []))
                
                return {
                    "type": "FeatureCollection",
                    "features": features,
                    "metadata": {
                        "level": level,
                        "count": len(features),
                        "codes": codes
                    }
                }
            else:
                # Fetch by bounding box or all
                return await fetch_boundary_geojson(level, bbox=bbox)
                
        except Exception as e:
            logger.error("Error fetching boundaries: %s", e)
            return {
                "error": str(e),
                "level": level,
                "codes": codes,
                "bbox": bbox
            }
    
    @mcp.tool()
    async def search_geographic_areas(
        query: str,
        level: str = "local_auth",
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Search for geographic areas by name or postcode.
        
        Args:
            query: Search term (area name or postcode)
            level: Geographic level to search within
            limit: Maximum number of results
        
        Returns:
            List of matching areas with codes and names
        """
        if level not in GEOGRAPHIC_LEVELS:
            return {"error": f"Invalid level: {level}"}
        
        config = GEOGRAPHIC_LEVELS[level]
        service_url = f"{ONS_GEOGRAPHY_API_BASE}/{config['service']}/FeatureServer/0/query"
        
        # Build search query
        params = {
            "where": f"{config['name_field']} LIKE '%{query}%'",
            "outFields": f"{config['code_field']},{config['name_field']}",
            "f": "json",
            "resultRecordCount": limit
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(service_url, params=params) as resp:
                    data = await resp.json()
                    
                    results = []
                    for feature in data.get("features", []):
                        attrs = feature.get("attributes", {})
                        results.append({
                            "code": attrs.get(config['code_field']),
                            "name": attrs.get(config['name_field']),
                            "level": level
                        })
                    
                    return {
                        "query": query,
                        "level": level,
                        "count": len(results),
                        "results": results
                    }
                    
        except Exception as e:
            logger.error("Search error: %s", e)
            return {
                "error": str(e),
                "query": query,
                "level": level
            }
    
    logger.info("Geography tools registered: select_geographic_area, fetch_boundaries, search_geographic_areas")
```

## 5. Minimal Geography Selector Widget (MVP)

```html
<!-- src/ui/geography_selector.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Geography Selector</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    #header {
      background: #f8f9fa;
      padding: 1rem;
      border-bottom: 1px solid #dee2e6;
      flex-shrink: 0;
    }
    
    h1 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #212529;
      margin-bottom: 0.5rem;
    }
    
    .controls {
      display: grid;
      grid-template-columns: 1fr 2fr;
      gap: 0.75rem;
    }
    
    .control-group {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }
    
    label {
      font-size: 0.875rem;
      font-weight: 500;
      color: #495057;
    }
    
    select, input {
      padding: 0.5rem;
      border: 1px solid #ced4da;
      border-radius: 0.25rem;
      font-size: 0.875rem;
    }
    
    select:focus, input:focus {
      outline: none;
      border-color: #0d6efd;
      box-shadow: 0 0 0 0.2rem rgba(13, 110, 253, 0.25);
    }
    
    #map {
      flex: 1;
      min-height: 0;
    }
    
    #footer {
      background: white;
      padding: 1rem;
      border-top: 1px solid #dee2e6;
      flex-shrink: 0;
    }
    
    .selection-info {
      margin-bottom: 1rem;
    }
    
    .selection-info h3 {
      font-size: 1rem;
      font-weight: 600;
      margin-bottom: 0.5rem;
    }
    
    .selected-area {
      background: #e7f3ff;
      border: 1px solid #b6d4fe;
      border-radius: 0.25rem;
      padding: 0.5rem;
      margin-bottom: 0.5rem;
      font-size: 0.875rem;
    }
    
    .selected-area-name {
      font-weight: 600;
      color: #0a58ca;
    }
    
    .selected-area-code {
      color: #6c757d;
      font-size: 0.75rem;
    }
    
    .btn {
      padding: 0.5rem 1rem;
      font-size: 0.875rem;
      font-weight: 500;
      border: none;
      border-radius: 0.25rem;
      cursor: pointer;
      transition: all 0.15s ease-in-out;
    }
    
    .btn-primary {
      background: #0d6efd;
      color: white;
    }
    
    .btn-primary:hover:not(:disabled) {
      background: #0b5ed7;
    }
    
    .btn-primary:disabled {
      background: #6c757d;
      cursor: not-allowed;
      opacity: 0.65;
    }
    
    .status-message {
      padding: 0.75rem;
      border-radius: 0.25rem;
      margin-bottom: 1rem;
      font-size: 0.875rem;
    }
    
    .status-info {
      background: #cfe2ff;
      border: 1px solid #b6d4fe;
      color: #084298;
    }
    
    .status-error {
      background: #f8d7da;
      border: 1px solid #f5c2c7;
      color: #842029;
    }
  </style>
</head>
<body>
  <div id="header">
    <h1>Select Geographic Area</h1>
    <div class="controls">
      <div class="control-group">
        <label for="level-select">Geographic Level</label>
        <select id="level-select">
          <!-- Options will be populated dynamically -->
        </select>
      </div>
      <div class="control-group">
        <label for="search-input">Search</label>
        <input 
          type="text" 
          id="search-input" 
          placeholder="Search by name or postcode..."
        />
      </div>
    </div>
  </div>
  
  <div id="map"></div>
  
  <div id="footer">
    <div class="selection-info">
      <h3>Selected Areas (<span id="selection-count">0</span>)</h3>
      <div id="selected-list">
        <p style="color: #6c757d; font-size: 0.875rem;">No areas selected</p>
      </div>
    </div>
    <div id="status-messages"></div>
    <button id="confirm-btn" class="btn btn-primary" disabled>
      Confirm Selection
    </button>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script type="module">
    // Import MCP-Apps SDK
    // For production, use proper CDN or npm package
    // This is a placeholder - actual SDK import will be different
    
    // Mock App class for development (replace with real SDK)
    class MockApp {
      constructor(config) {
        this.config = config;
        this.initialized = false;
      }
      
      async initialize() {
        // Get config from URL params or postMessage
        this.initialized = true;
        console.log('App initialized');
        return {};
      }
      
      getInitialConfig() {
        // For now, return demo config
        return {
          level: 'local_auth',
          level_name: 'Local Authorities',
          initial_view: {
            lat: 52.4862,
            lng: -1.8904,
            zoom: 6
          },
          features: {
            multi_select: true,
            show_hierarchy: true,
            search_enabled: true
          },
          available_levels: [
            { value: 'parl_const', label: 'Parliamentary Constituencies' },
            { value: 'local_auth', label: 'Local Authorities' },
            { value: 'ward', label: 'Wards' },
            { value: 'lsoa', label: 'Lower Super Output Areas' },
            { value: 'msoa', label: 'Middle Super Output Areas' },
            { value: 'oa', label: 'Output Areas' }
          ]
        };
      }
      
      async callTool(toolName, params) {
        console.log('Calling tool:', toolName, params);
        // Mock tool call - in production this goes through MCP
        return {
          type: 'FeatureCollection',
          features: [] // Would contain actual boundary data
        };
      }
      
      async returnResult(data) {
        console.log('Returning result:', data);
        // Mock result return - in production sends via postMessage
        alert('Selection confirmed! Check console for data.');
      }
      
      async sendNotification(notification) {
        console.log('Notification:', notification);
      }
    }
    
    // Initialize app (use real SDK in production)
    const app = new MockApp({
      /* transport config */
    });
    
    // State management
    let map;
    let currentLevel = 'local_auth';
    let selectedAreas = [];
    let boundaryLayer;
    
    // Initialize
    await app.initialize();
    const config = app.getInitialConfig();
    
    // Setup map
    const { lat, lng, zoom } = config.initial_view;
    map = L.map('map').setView([lat, lng], zoom);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18
    }).addTo(map);
    
    // Populate level selector
    const levelSelect = document.getElementById('level-select');
    config.available_levels.forEach(level => {
      const option = document.createElement('option');
      option.value = level.value;
      option.textContent = level.label;
      if (level.value === config.level) {
        option.selected = true;
      }
      levelSelect.appendChild(option);
    });
    
    currentLevel = config.level;
    
    // Load boundaries for current level
    async function loadBoundaries() {
      try {
        // In production, call actual MCP tool
        const bounds = map.getBounds();
        const bbox = `${bounds.getWest()},${bounds.getSouth()},${bounds.getEast()},${bounds.getNorth()}`;
        
        const result = await app.callTool('fetch_boundaries', {
          level: currentLevel,
          bbox: bbox
        });
        
        // Clear existing layer
        if (boundaryLayer) {
          map.removeLayer(boundaryLayer);
        }
        
        // Add new boundaries
        boundaryLayer = L.geoJSON(result, {
          style: {
            fillColor: '#3388ff',
            fillOpacity: 0.2,
            color: '#3388ff',
            weight: 2
          },
          onEachFeature: (feature, layer) => {
            // Click to select
            layer.on('click', () => {
              selectArea(feature, layer);
            });
            
            // Hover effects
            layer.on('mouseover', () => {
              if (!isSelected(feature)) {
                layer.setStyle({ fillOpacity: 0.4 });
              }
            });
            
            layer.on('mouseout', () => {
              if (!isSelected(feature)) {
                layer.setStyle({ fillOpacity: 0.2 });
              }
            });
            
            // Popup with area name
            const name = feature.properties.name || 'Unknown';
            const code = feature.properties.code || 'N/A';
            layer.bindPopup(`<strong>${name}</strong><br/><small>${code}</small>`);
          }
        }).addTo(map);
        
        showStatus(`Loaded ${result.features.length} areas`, 'info');
        
      } catch (error) {
        console.error('Error loading boundaries:', error);
        showStatus('Error loading boundaries: ' + error.message, 'error');
      }
    }
    
    function selectArea(feature, layer) {
      const code = feature.properties.code || feature.properties.gss_code;
      const name = feature.properties.name || feature.properties.area_name;
      
      // Check if already selected
      const existingIndex = selectedAreas.findIndex(a => a.code === code);
      
      if (existingIndex >= 0) {
        // Deselect
        selectedAreas.splice(existingIndex, 1);
        layer.setStyle({
          fillColor: '#3388ff',
          fillOpacity: 0.2
        });
      } else {
        // Select
        selectedAreas.push({
          code: code,
          name: name,
          level: currentLevel,
          geometry: feature.geometry
        });
        layer.setStyle({
          fillColor: '#28a745',
          fillOpacity: 0.5
        });
      }
      
      updateSelectionUI();
    }
    
    function isSelected(feature) {
      const code = feature.properties.code || feature.properties.gss_code;
      return selectedAreas.some(a => a.code === code);
    }
    
    function updateSelectionUI() {
      const countEl = document.getElementById('selection-count');
      const listEl = document.getElementById('selected-list');
      const confirmBtn = document.getElementById('confirm-btn');
      
      countEl.textContent = selectedAreas.length;
      
      if (selectedAreas.length === 0) {
        listEl.innerHTML = '<p style="color: #6c757d; font-size: 0.875rem;">No areas selected</p>';
        confirmBtn.disabled = true;
      } else {
        listEl.innerHTML = selectedAreas.map(area => `
          <div class="selected-area">
            <div class="selected-area-name">${area.name}</div>
            <div class="selected-area-code">${area.code} (${area.level})</div>
          </div>
        `).join('');
        confirmBtn.disabled = false;
      }
    }
    
    function showStatus(message, type = 'info') {
      const statusEl = document.getElementById('status-messages');
      const div = document.createElement('div');
      div.className = `status-message status-${type}`;
      div.textContent = message;
      statusEl.appendChild(div);
      
      // Auto-remove after 5 seconds
      setTimeout(() => div.remove(), 5000);
    }
    
    // Event listeners
    levelSelect.addEventListener('change', (e) => {
      currentLevel = e.target.value;
      selectedAreas = []; // Clear selection when changing levels
      updateSelectionUI();
      loadBoundaries();
    });
    
    let searchTimeout;
    document.getElementById('search-input').addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      const query = e.target.value.trim();
      
      if (query.length >= 3) {
        searchTimeout = setTimeout(async () => {
          // Call search tool
          const results = await app.callTool('search_geographic_areas', {
            query: query,
            level: currentLevel
          });
          
          // TODO: Highlight/filter results on map
          console.log('Search results:', results);
        }, 300);
      }
    });
    
    document.getElementById('confirm-btn').addEventListener('click', async () => {
      if (selectedAreas.length === 0) return;
      
      // Return selection to host
      await app.returnResult({
        status: 'selected',
        areas: selectedAreas,
        count: selectedAreas.length,
        level: currentLevel
      });
    });
    
    // Initial load
    await loadBoundaries();
    
    // Notify ready
    await app.sendNotification({
      level: 'info',
      message: 'Geography selector ready'
    });
  </script>
</body>
</html>
```

## 6. Testing the Integration

```python
# tests/test_mcp_apps_integration.py
"""
Tests for MCP-Apps integration
"""
import pytest
from src.ui_resources import register_ui_resources, load_ui_resource
from src.tools.geography_tools import register_geography_tools
from fastmcp import FastMCP

@pytest.mark.asyncio
async def test_ui_resource_registration():
    """Test that UI resources are properly registered"""
    mcp = FastMCP("test-server")
    
    # Register UI resources
    await register_ui_resources(mcp)
    
    # List resources
    resources = await mcp.list_resources()
    resource_uris = [r.uri for r in resources.resources]
    
    # Check expected UI resources
    assert "ui://os-ons/geography-selector" in resource_uris
    assert "ui://os-ons/statistics-dashboard" in resource_uris
    assert "ui://os-ons/feature-inspector" in resource_uris

@pytest.mark.asyncio
async def test_geography_selector_tool():
    """Test select_geographic_area tool"""
    mcp = FastMCP("test-server")
    await register_geography_tools(mcp)
    
    # Get the tool
    tools = await mcp.list_tools()
    select_tool = next(
        t for t in tools.tools 
        if t.name == "select_geographic_area"
    )
    
    assert select_tool is not None
    assert "ui://os-ons/geography-selector" in str(select_tool.description)
    
    # Call the tool
    result = await mcp.call_tool(
        "select_geographic_area",
        {
            "level": "ward",
            "initial_location": {
                "lat": 52.48,
                "lng": -1.89,
                "zoom": 11
            }
        }
    )
    
    assert result["status"] == "selection_pending"
    assert result["config"]["level"] == "ward"
    assert "_meta" in result
    assert "uiResourceUris" in result["_meta"]

@pytest.mark.asyncio
async def test_fetch_boundaries_tool():
    """Test fetch_boundaries tool"""
    mcp = FastMCP("test-server")
    await register_geography_tools(mcp)
    
    # Call tool
    result = await mcp.call_tool(
        "fetch_boundaries",
        {
            "level": "local_auth",
            "codes": ["E08000026"]  # Coventry
        }
    )
    
    assert result["type"] == "FeatureCollection"
    assert "features" in result
    assert result["metadata"]["level"] == "local_auth"
```

## 7. Next Steps

1. **Create UI directory structure**:
   ```bash
   mkdir -p src/ui src/tools src/clients
   ```

2. **Install new dependencies**:
   ```bash
   pip install aiofiles geojson shapely
   ```

3. **Copy the starter code**:
   - Save `ui_resources.py` to `src/`
   - Save `geography_tools.py` to `src/tools/`
   - Save `geography_selector.html` to `src/ui/`

4. **Update server.py** with integration code

5. **Test basic functionality**:
   ```bash
   python -m server --transport stdio
   ```

6. **Connect with Claude Desktop** and test:
   ```
   @os-mcp list resources
   @os-mcp call select_geographic_area
   ```

7. **Iterate on the widget**: Replace mock `callTool` with real MCP-Apps SDK

## 8. Key Concepts

### UI Resource URI Scheme
- Use `ui://` prefix for all UI resources
- Format: `ui://{server-name}/{widget-name}`
- Example: `ui://os-ons/geography-selector`

### Tool Metadata for UI
```python
{
    "_meta": {
        "uiResourceUris": ["ui://os-ons/geography-selector"],
        "audience": ["user"],  # This indicates user-facing UI
        "capabilities": ["selection", "visualization"]
    }
}
```

### Widget Communication Pattern
1. Tool returns config with `_meta.uiResourceUris`
2. Host renders widget in sandboxed iframe
3. Widget uses MCP-Apps SDK to call tools via postMessage
4. Widget returns results to host when user confirms
5. LLM receives both tool response and user selections

### Security Model
- All widgets run in sandboxed iframes
- No direct API access from widgets
- All external calls go through MCP tools
- postMessage communication is auditable

## 9. Debugging Tips

1. **Widget not showing**: Check browser console for errors
2. **Tool not found**: Verify tool registration in server.py
3. **Boundaries not loading**: Check ONS API responses in network tab
4. **Selection not working**: Add console.log in widget click handlers
5. **MCP errors**: Run server with `LOG_LEVEL=DEBUG`

---

This starter code provides a solid foundation for MCP-Apps integration. Start with the geography selector, test it end-to-end, then expand to other widgets following the same patterns.
