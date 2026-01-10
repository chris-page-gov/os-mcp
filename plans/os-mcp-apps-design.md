# Exemplar MCP-Apps Design: OS & ONS Geographic Data Server

## Executive Summary

This document outlines the design for an exemplary Model Context Protocol (MCP) server that provides comprehensive access to Ordnance Survey and Office of National Statistics data through both traditional MCP tools and innovative MCP-Apps interactive UI components.

**Key Goals:**
1. Demonstrate best-in-class MCP-Apps implementation with geographic visualization
2. Provide intuitive UI for geographic selection at multiple administrative levels
3. Excellent context building through skills and tool composition
4. Showcase the full spectrum of MCP capabilities (tools, resources, prompts, UI)

## Architecture Overview

### Current State (from repository analysis)
- ✅ FastMCP-based server with OS NGD API integration
- ✅ Two-step workflow enforcement (planner → execution)
- ✅ Prompt templates with categorization
- ✅ Basic React frontend (Leaflet-based)
- ✅ HTTP and STDIO transports
- ✅ Tool-based search and retrieval

### Proposed MCP-Apps Enhancement

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Host (Claude/ChatGPT)               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │   Chat Context  │  │  UI Iframe       │  │  Tool      │ │
│  │   (LLM-facing)  │  │  (User-facing)   │  │  Results   │ │
│  └────────┬────────┘  └────────┬─────────┘  └─────┬──────┘ │
└───────────┼────────────────────┼──────────────────┼────────┘
            │                    │                  │
            │ MCP JSON-RPC       │ postMessage      │
            │                    │                  │
┌───────────▼────────────────────▼──────────────────▼────────┐
│                    OS/ONS MCP Server                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   UI         │  │   Tools      │  │   Resources      │  │
│  │   Resources  │  │              │  │   (Metadata)     │  │
│  │   (ui://)    │  │   (search,   │  │   (queryables,   │  │
│  │              │  │    retrieve, │  │    collections)  │  │
│  │  - Map       │  │    analyze)  │  │                  │  │
│  │  - Selectors │  │              │  │                  │  │
│  │  - Dashboards│  │              │  │                  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     API Integration Layer                    │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │  OS Data Hub     │          │  ONS API         │         │
│  │  - NGD Features  │          │  - Geographies   │         │
│  │  - Places        │          │  - Statistics    │         │
│  │  - Routing       │          │  - Boundaries    │         │
│  └──────────────────┘          └──────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

## MCP-Apps UI Resources Design

### 1. Geographic Boundary Selector Widget

**URI:** `ui://os-ons/geography-selector`

**Purpose:** Interactive map-based selector for choosing geographic areas at different administrative levels.

**Features:**
- Multi-level hierarchy selector (Parliamentary Constituencies, Local Authorities, Wards, Output Areas, Postcodes)
- Leaflet map with GeoJSON boundary overlays
- Search by name or postcode
- Click-to-select areas
- Visual feedback with different colors for selected/hovered areas
- Breadcrumb navigation showing geographic hierarchy

**Tool Association:**
```json
{
  "name": "select_geographic_area",
  "description": "Interactive widget for selecting UK geographic areas",
  "_meta": {
    "uiResourceUris": ["ui://os-ons/geography-selector"]
  }
}
```

**UI Implementation Pattern:**
```html
<!DOCTYPE html>
<html>
<head>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script type="module">
    import { App, postMessageTransport } from 'https://esm.sh/@modelcontextprotocol/ext-apps';
    
    const app = new App({
      transport: postMessageTransport()
    });
    
    // Initialize map
    const map = L.map('map').setView([52.4862, -1.8904], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
    
    // Load boundary data and enable selection
    async function loadBoundaries(level) {
      const result = await app.callTool('fetch_boundaries', { 
        geographic_level: level 
      });
      // Render GeoJSON boundaries...
    }
  </script>
</head>
<body>
  <div id="controls">
    <select id="level-selector">
      <option value="parl_const">Parliamentary Constituencies</option>
      <option value="local_auth">Local Authorities</option>
      <option value="ward">Wards</option>
      <option value="lsoa">Lower Super Output Areas</option>
      <option value="msoa">Middle Super Output Areas</option>
      <option value="oa">Output Areas</option>
    </select>
    <input type="text" id="search" placeholder="Search by name or postcode..." />
  </div>
  <div id="map" style="height: 500px;"></div>
  <div id="selection-info">
    <h3>Selected Area</h3>
    <div id="area-details"></div>
    <button id="confirm-btn">Use This Area</button>
  </div>
</body>
</html>
```

### 2. Statistical Dashboard Widget

**URI:** `ui://os-ons/statistics-dashboard`

**Purpose:** Interactive dashboard showing ONS statistics for selected geographic areas.

**Features:**
- Multiple visualization types (charts, tables, heatmaps)
- Comparative analysis across areas
- Time series data with sliders
- Export functionality
- Drill-down capabilities

**Associated Tools:**
- `query_ons_statistics`
- `compare_areas`
- `generate_report`

### 3. Feature Inspector Widget

**URI:** `ui://os-ons/feature-inspector`

**Purpose:** Detailed view of OS NGD features with linked identifiers.

**Features:**
- Property table with rich formatting
- Linked identifier navigation
- Spatial relationship visualization
- Change history (if available)
- Export to various formats

### 4. Route Planner Widget

**URI:** `ui://os-ons/route-planner`

**Purpose:** Interactive route planning with OS routing data.

**Features:**
- Map-based origin/destination selection
- Multiple route options
- Turn-by-turn directions
- Elevation profile
- Points of interest along route

## Tool Design Enhancements

### Tool Categories

1. **Discovery Tools** (Planner Required)
   - `discover_geographic_levels` - List available geographic hierarchies
   - `query_available_statistics` - Find available ONS datasets
   - `fetch_collection_metadata` - Get queryable properties

2. **Selection Tools** (With UI Support)
   - `select_geographic_area` (→ `ui://os-ons/geography-selector`)
   - `search_features_by_location` 
   - `find_nearest_features`

3. **Data Retrieval Tools**
   - `get_feature_details`
   - `get_ons_statistics`
   - `fetch_boundaries_geojson`
   - `get_linked_identifiers`

4. **Analysis Tools**
   - `compare_geographic_areas`
   - `calculate_statistics_summary`
   - `analyze_spatial_relationships`

5. **Visualization Tools** (With UI Support)
   - `render_statistical_dashboard` (→ `ui://os-ons/statistics-dashboard`)
   - `visualize_route` (→ `ui://os-ons/route-planner`)
   - `inspect_feature` (→ `ui://os-ons/feature-inspector`)

### Tool-to-UI Linking Pattern

```python
from fastmcp import FastMCP
from typing import Dict, Any

mcp = FastMCP("os-ons-api")

@mcp.tool(
    description="Select a geographic area interactively",
    _meta={
        "uiResourceUris": ["ui://os-ons/geography-selector"],
        "audience": ["user"],  # UI is for user interaction
        "preferredView": "modal"  # Suggestion for host display
    }
)
async def select_geographic_area(
    level: str = "local_auth",
    initial_bounds: Dict[str, float] | None = None
) -> Dict[str, Any]:
    """
    Opens an interactive map widget for selecting geographic areas.
    
    Args:
        level: Geographic level (parl_const, local_auth, ward, lsoa, msoa, oa)
        initial_bounds: Optional initial map bounds (west, south, east, north)
    
    Returns:
        Selected area details with code, name, and boundary GeoJSON
    """
    # Tool returns both machine-readable data AND UI resource reference
    return {
        "status": "awaiting_selection",
        "widget_config": {
            "level": level,
            "initial_bounds": initial_bounds or {
                "west": -8.62, "south": 49.86,
                "east": 1.76, "north": 60.86
            }
        },
        # This will trigger the UI rendering in compatible hosts
        "_ui_state": "selection_pending"
    }
```

## Resource Design

### Static Resources (Metadata)

1. **Geographic Hierarchies**
   - URI: `os-ons://hierarchies/uk-geography`
   - Description: Complete UK administrative geography hierarchy
   - MIME: `application/json`

2. **Collection Metadata**
   - URI: `os-ons://collections/{collection_id}/metadata`
   - Description: Queryable properties and constraints for OS collections

3. **ONS Dataset Catalog**
   - URI: `os-ons://ons/datasets`
   - Description: Available ONS statistical datasets with metadata

### UI Resources

All UI resources follow the pattern:
- URI scheme: `ui://os-ons/{widget-name}`
- MIME type: `text/html;profile=mcp-app`
- Sandboxed iframe with restricted permissions
- Communication via postMessage using MCP JSON-RPC protocol

## Context Building Strategy

### 1. Layered Context Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: Geographic Metadata Context                   │
│  - Available geographic levels                          │
│  - Hierarchy relationships                              │
│  - Boundary coverage information                        │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│  Layer 2: Feature Collection Context                    │
│  - Queryable properties                                 │
│  - Feature types available                              │
│  - Linked identifier types                              │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│  Layer 3: Statistical Context                           │
│  - Available ONS datasets                               │
│  - Time periods covered                                 │
│  - Granularity levels                                   │
└───────────────────┬─────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────┐
│  Layer 4: User Selection Context                        │
│  - Selected geographic areas                            │
│  - Active features                                      │
│  - Query history                                        │
└─────────────────────────────────────────────────────────┘
```

### 2. Skills-Based Context Enhancement

**Skill:** `/mnt/skills/user/os-ons-geography/SKILL.md`

```markdown
# OS & ONS Geography Skill

## Overview
Expert knowledge for working with UK Ordnance Survey and Office of National Statistics geographic data.

## Key Concepts

### Geographic Hierarchy Levels
1. **Parliamentary Constituencies** - Electoral districts (650 in UK)
2. **Local Authorities** - Counties, unitary authorities, districts
3. **Wards** - Electoral wards within local authorities
4. **Output Areas (OA)** - Census geography (~300 households)
5. **Lower Super Output Areas (LSOA)** - 4-6 OAs (~1,500 households)
6. **Middle Super Output Areas (MSOA)** - 4-6 LSOAs (~7,500 households)
7. **Postcodes** - Mail delivery points

### Identifier Systems
- **GSS Codes** - Official Government Statistical Service codes
- **UPRN** - Unique Property Reference Number
- **USRN** - Unique Street Reference Number
- **TOID** - Topographic Identifier

## Workflow Patterns

### Pattern 1: Geographic Area Selection
1. Use `select_geographic_area` with UI widget
2. Confirm selection and extract GSS code
3. Use code for subsequent data queries

### Pattern 2: Statistical Analysis
1. Identify geographic area(s) of interest
2. Query available ONS datasets for that geography
3. Retrieve specific statistics
4. Visualize with dashboard widget

### Pattern 3: Spatial Search
1. Establish bounding box or reference point
2. Search for features of interest
3. Apply filters based on properties
4. Retrieve detailed feature information

## Best Practices

### Always Start With Metadata
Before searching features, fetch collection metadata to understand:
- What properties are queryable
- What feature types exist
- What filters are available

### Use Appropriate Geographic Levels
- **Large-scale analysis** → Local Authorities, MSOAs
- **Neighborhood analysis** → Wards, LSOAs
- **Precise location work** → OAs, Postcodes

### Combine OS and ONS Data
- OS provides spatial features and geometry
- ONS provides statistics and demographics
- Link via GSS codes or spatial joins

## Common Use Cases

### 1. Property Development Analysis
```
1. Select ward/LSOA using geography selector
2. Get population demographics from ONS
3. Search for existing amenities (schools, shops) from OS
4. Analyze transport links via routing
5. Generate comparative dashboard
```

### 2. Infrastructure Planning
```
1. Define study area boundaries
2. Extract all features of specific types (roads, buildings)
3. Calculate density and distribution
4. Compare with ONS statistics
5. Identify gaps or opportunities
```

### 3. Constituency Profiling
```
1. Select parliamentary constituency
2. Get demographic data from ONS
3. Map geographic features and amenities
4. Calculate accessibility metrics
5. Generate comprehensive profile
```

## Error Handling

### Common Issues
1. **No features found** → Check bbox/filters, try broader search
2. **Invalid GSS code** → Verify code format and geographic level
3. **Rate limits** → Implement pagination, batch requests
4. **Missing statistics** → Check data availability for time period/geography

## Integration Points

### OS Data Hub APIs
- **NGD Features API** - Spatial features with properties
- **Places API** - Address and location search
- **Routing API** - Route calculation and navigation

### ONS APIs  
- **Geography API** - Boundary data and hierarchies
- **Cantabular API** - Census and survey statistics
- **Statistical Bulletins** - Published reports and data

## Tips for Effective Queries

1. **Start broad, refine narrow** - Begin with larger areas, drill down
2. **Use UI widgets for exploration** - Visual selection reduces errors
3. **Cache metadata** - Collection properties rarely change
4. **Batch operations** - Group related queries when possible
5. **Validate inputs** - Check codes and coordinates before querying
```

### 3. Intelligent Prompt Templates

Enhance existing prompts to leverage MCP-Apps:

```json
{
  "name": "explore_constituency",
  "category": "political",
  "description": "Interactive exploration of a parliamentary constituency",
  "workflow": [
    {
      "step": 1,
      "tool": "select_geographic_area",
      "params": {"level": "parl_const"},
      "description": "Open interactive map to select constituency",
      "ui_mode": true
    },
    {
      "step": 2,
      "tool": "get_ons_statistics",
      "params": {"dataset": "census_demographics"},
      "description": "Fetch demographic statistics for selected area"
    },
    {
      "step": 3,
      "tool": "render_statistical_dashboard",
      "params": {"visualizations": ["population_pyramid", "deprivation_map"]},
      "description": "Display interactive dashboard",
      "ui_mode": true
    }
  ]
}
```

## Implementation Roadmap

### Phase 1: Core UI Resources (Week 1-2)
- [ ] Implement `ui://os-ons/geography-selector` widget
- [ ] Add boundary fetching tools with caching
- [ ] Integrate with existing FastMCP server
- [ ] Test with Claude Desktop

### Phase 2: Statistical Dashboard (Week 3-4)
- [ ] Implement `ui://os-ons/statistics-dashboard` widget
- [ ] Add ONS API integration for statistics
- [ ] Create visualization components (charts, tables)
- [ ] Add comparison and filtering features

### Phase 3: Advanced Widgets (Week 5-6)
- [ ] Implement `ui://os-ons/feature-inspector` widget
- [ ] Implement `ui://os-ons/route-planner` widget
- [ ] Add export and sharing capabilities
- [ ] Enhanced error handling and loading states

### Phase 4: Context & Skills (Week 7-8)
- [ ] Create comprehensive skills documentation
- [ ] Implement smart prompt templates
- [ ] Add contextual help and guidance
- [ ] Performance optimization and caching

### Phase 5: Testing & Documentation (Week 9-10)
- [ ] Comprehensive test suite for all widgets
- [ ] User documentation and examples
- [ ] Video tutorials and demos
- [ ] Performance benchmarking

## Technical Specifications

### Security Model
- All UI resources rendered in sandboxed iframes
- Restricted iframe permissions: no scripts, forms, popups
- Communication only via postMessage/JSON-RPC
- No direct access to OS API keys from UI code

### Performance Considerations
- Lazy loading of boundary geometries
- Client-side caching of frequently accessed data
- Progressive enhancement (works without UI)
- Optimized GeoJSON with simplified geometries

### Browser Compatibility
- Modern browsers with ES modules support
- Leaflet 1.9.4+ for mapping
- Chart.js or D3.js for visualizations
- Responsive design for various screen sizes

## Example Usage Scenarios

### Scenario 1: Urban Planner Using Claude Desktop

```
User: I need to analyze housing development opportunities in Birmingham

Claude: I'll help you explore Birmingham's geography and statistics. Let me open 
an interactive map where you can select specific areas of interest.

[Calls select_geographic_area tool → UI widget renders]

[User selects Edgbaston ward on map]

Claude: You've selected Edgbaston ward. Let me fetch the demographic and housing
statistics for this area.

[Calls get_ons_statistics → Retrieves data]

Claude: Here's an interactive dashboard showing Edgbaston's demographics, housing
stock, and development patterns.

[Calls render_statistical_dashboard → UI widget renders with charts]

[User explores dashboard, applies filters]

Claude: Based on the data, I can see several potential development areas. Would 
you like me to map existing amenities like schools and transport links?

[Continues with spatial analysis using OS features...]
```

### Scenario 2: Researcher Comparing Multiple Constituencies

```
User: Compare the demographics of Coventry North East and Coventry South constituencies

Claude: I'll help you compare these constituencies. First, let me fetch their 
boundaries and statistics.

[Calls select_geographic_area twice, or batch tool]

Claude: Here's an interactive dashboard comparing the two constituencies across
multiple demographic dimensions.

[Calls render_statistical_dashboard with comparison mode → UI renders side-by-side]

[Dashboard shows population pyramids, deprivation indices, education levels, etc.]

User: Can you show me the boundary overlap with wards?

Claude: [Calls fetch_boundaries_geojson with both constituencies and ward level]

[Updates map widget to show constituency boundaries with ward subdivisions colored]
```

### Scenario 3: Transport Analyst Planning Routes

```
User: Find optimal locations for new bus stops in Leamington Spa

Claude: I'll help you analyze this systematically. Let me start by showing you
Leamington Spa with existing transport infrastructure.

[Opens geography selector focused on Leamington Spa]

Claude: Now let me overlay existing bus stops and routes.

[Searches for bus stop features using OS Places API]

Claude: Here's a route planner widget where you can explore different route 
options and measure distances to existing infrastructure.

[Opens route planner widget with existing stops marked]

[User clicks potential locations, widget calculates coverage areas]

Claude: Let me fetch population density data to help identify underserved areas.

[Retrieves LSOA-level statistics and renders heatmap]
```

## Code Examples

### 1. Registering UI Resources

```python
# src/ui_resources.py

from fastmcp import FastMCP
from pathlib import Path

async def register_ui_resources(mcp: FastMCP):
    """Register all UI resources with the MCP server"""
    
    ui_dir = Path(__file__).parent / "ui"
    
    # Geography Selector Widget
    geography_selector_html = (ui_dir / "geography_selector.html").read_text()
    
    await mcp.add_resource(
        uri="ui://os-ons/geography-selector",
        name="Geographic Area Selector",
        description="Interactive map widget for selecting UK geographic areas at various administrative levels",
        mime_type="text/html;profile=mcp-app",
        content=geography_selector_html,
        annotations={
            "audience": ["user"],
            "priority": 1.0
        }
    )
    
    # Statistical Dashboard Widget  
    dashboard_html = (ui_dir / "statistics_dashboard.html").read_text()
    
    await mcp.add_resource(
        uri="ui://os-ons/statistics-dashboard",
        name="Statistics Dashboard",
        description="Interactive dashboard for visualizing ONS statistics",
        mime_type="text/html;profile=mcp-app",
        content=dashboard_html,
        annotations={
            "audience": ["user"],
            "priority": 0.8
        }
    )
    
    # Feature Inspector Widget
    inspector_html = (ui_dir / "feature_inspector.html").read_text()
    
    await mcp.add_resource(
        uri="ui://os-ons/feature-inspector",
        name="Feature Inspector",
        description="Detailed view of OS features with linked identifiers",
        mime_type="text/html;profile=mcp-app",
        content=inspector_html,
        annotations={
            "audience": ["user"],
            "priority": 0.6
        }
    )
```

### 2. Tool with UI Support

```python
# src/tools/geography_tools.py

from fastmcp import FastMCP
from typing import Dict, Any, Optional
import aiohttp

async def fetch_boundary_geojson(
    geographic_code: str,
    level: str,
    simplification: float = 0.001
) -> Dict[str, Any]:
    """
    Fetch GeoJSON boundary for a geographic area.
    
    Args:
        geographic_code: GSS code for the area
        level: Geographic level (parl_const, local_auth, ward, etc.)
        simplification: Geometry simplification tolerance (smaller = more detail)
    
    Returns:
        GeoJSON FeatureCollection with boundary geometry
    """
    # Implementation using ONS Geography API
    async with aiohttp.ClientSession() as session:
        url = f"https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/{level}/FeatureServer/0/query"
        params = {
            "where": f"GSS_CODE='{geographic_code}'",
            "outFields": "*",
            "f": "geojson",
            "geometryPrecision": 6,
            "simplification": simplification
        }
        async with session.get(url, params=params) as resp:
            return await resp.json()

@mcp.tool(
    description="Interactively select a UK geographic area using a map widget",
    _meta={
        "uiResourceUris": ["ui://os-ons/geography-selector"],
        "audience": ["user"],
        "capabilities": ["boundary_display", "hierarchical_selection", "search"]
    }
)
async def select_geographic_area(
    level: str = "local_auth",
    initial_location: Optional[Dict[str, float]] = None,
    search_term: Optional[str] = None
) -> Dict[str, Any]:
    """
    Opens interactive map widget for selecting geographic areas.
    
    The widget supports:
    - Hierarchical selection (constituencies → wards → output areas)
    - Search by name or postcode
    - Visual boundary display
    - Multi-select for comparisons
    
    Args:
        level: Geographic level to display (parl_const, local_auth, ward, lsoa, msoa, oa)
        initial_location: Optional {lat, lng, zoom} to center map
        search_term: Optional search query to pre-filter areas
    
    Returns:
        {
            "status": "selection_pending" | "selected",
            "config": {...configuration for widget...},
            "selected_areas": [...when status is "selected"...]
        }
    """
    
    config = {
        "level": level,
        "initial_view": initial_location or {
            "lat": 52.4862,
            "lng": -1.8904,
            "zoom": 6
        },
        "search_term": search_term,
        "features": {
            "multi_select": True,
            "show_hierarchy": True,
            "search_enabled": True
        }
    }
    
    return {
        "status": "selection_pending",
        "config": config,
        "instructions": (
            "An interactive map widget will open. "
            "Click on areas to select them, use the search box to find specific locations, "
            "or change the geographic level to explore different administrative divisions."
        )
    }

@mcp.tool(
    description="Render interactive statistical dashboard for selected areas"
)
async def render_statistical_dashboard(
    areas: list[Dict[str, Any]],
    datasets: list[str],
    visualizations: list[str],
    comparison_mode: bool = False
) -> Dict[str, Any]:
    """
    Creates an interactive dashboard displaying ONS statistics.
    
    Args:
        areas: List of selected geographic areas with codes
        datasets: ONS datasets to include (e.g., ["census_demographics", "crime", "health"])
        visualizations: Types of charts to render (e.g., ["bar", "line", "heatmap"])
        comparison_mode: If True, show areas side-by-side for comparison
    
    Returns:
        Configuration for dashboard widget
    """
    
    # Fetch actual data from ONS APIs
    dashboard_data = {}
    for dataset in datasets:
        dashboard_data[dataset] = await fetch_ons_data(areas, dataset)
    
    return {
        "status": "rendering",
        "config": {
            "areas": areas,
            "data": dashboard_data,
            "visualizations": visualizations,
            "comparison_mode": comparison_mode,
            "interactive_features": ["filtering", "export", "drill_down"]
        },
        "_meta": {
            "uiResourceUris": ["ui://os-ons/statistics-dashboard"]
        }
    }
```

### 3. Widget Implementation (Simplified)

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
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
    #container { display: flex; flex-direction: column; height: 100vh; }
    #controls { padding: 1rem; background: #f5f5f5; border-bottom: 1px solid #ddd; }
    #map { flex: 1; }
    #selection-panel { padding: 1rem; background: white; border-top: 1px solid #ddd; }
    .control-group { margin-bottom: 0.5rem; }
    label { display: block; margin-bottom: 0.25rem; font-size: 0.875rem; font-weight: 500; }
    select, input { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
    button { padding: 0.5rem 1rem; background: #0066cc; color: white; border: none; border-radius: 4px; cursor: pointer; }
    button:hover { background: #0052a3; }
    .selected-area { padding: 0.5rem; margin: 0.5rem 0; background: #e6f2ff; border-radius: 4px; }
  </style>
</head>
<body>
  <div id="container">
    <div id="controls">
      <div class="control-group">
        <label for="level">Geographic Level</label>
        <select id="level">
          <option value="parl_const">Parliamentary Constituencies</option>
          <option value="local_auth" selected>Local Authorities</option>
          <option value="ward">Wards</option>
          <option value="lsoa">Lower Super Output Areas</option>
          <option value="msoa">Middle Super Output Areas</option>
          <option value="oa">Output Areas</option>
        </select>
      </div>
      <div class="control-group">
        <label for="search">Search</label>
        <input type="text" id="search" placeholder="Search by name or postcode..." />
      </div>
    </div>
    
    <div id="map"></div>
    
    <div id="selection-panel">
      <h3>Selected Areas</h3>
      <div id="selected-list"></div>
      <button id="confirm-btn" style="margin-top: 1rem;">Confirm Selection</button>
    </div>
  </div>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script type="module">
    // Import MCP Apps SDK
    import { App, postMessageTransport } from 'https://esm.sh/@modelcontextprotocol/ext-apps';
    
    // Initialize MCP App
    const app = new App({
      transport: postMessageTransport()
    });
    
    // State
    let selectedAreas = [];
    let currentLevel = 'local_auth';
    let boundaryLayers = {};
    
    // Initialize Leaflet map
    const map = L.map('map').setView([52.4862, -1.8904], 6);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);
    
    // Load boundaries for current level
    async function loadBoundaries(level) {
      try {
        // Call MCP tool to fetch boundary data
        const result = await app.callTool('fetch_boundaries_geojson', {
          level: level,
          bbox: map.getBounds().toBBoxString()
        });
        
        // Clear existing layers
        if (boundaryLayers[level]) {
          map.removeLayer(boundaryLayers[level]);
        }
        
        // Add GeoJSON layer
        boundaryLayers[level] = L.geoJSON(result.geojson, {
          style: {
            fillColor: '#3388ff',
            fillOpacity: 0.2,
            color: '#3388ff',
            weight: 2
          },
          onEachFeature: (feature, layer) => {
            layer.on({
              click: () => selectArea(feature, layer),
              mouseover: () => layer.setStyle({ fillOpacity: 0.4 }),
              mouseout: () => {
                if (!isSelected(feature)) {
                  layer.setStyle({ fillOpacity: 0.2 });
                }
              }
            });
            
            layer.bindPopup(`
              <strong>${feature.properties.name}</strong><br/>
              ${feature.properties.gss_code}
            `);
          }
        }).addTo(map);
        
      } catch (error) {
        console.error('Error loading boundaries:', error);
        app.sendLog('error', `Failed to load boundaries: ${error.message}`);
      }
    }
    
    function selectArea(feature, layer) {
      const areaData = {
        gss_code: feature.properties.gss_code,
        name: feature.properties.name,
        level: currentLevel,
        geometry: feature.geometry
      };
      
      // Toggle selection
      const existingIndex = selectedAreas.findIndex(
        a => a.gss_code === areaData.gss_code
      );
      
      if (existingIndex >= 0) {
        selectedAreas.splice(existingIndex, 1);
        layer.setStyle({ fillOpacity: 0.2, fillColor: '#3388ff' });
      } else {
        selectedAreas.push(areaData);
        layer.setStyle({ fillOpacity: 0.6, fillColor: '#00cc44' });
      }
      
      updateSelectionList();
    }
    
    function isSelected(feature) {
      return selectedAreas.some(a => a.gss_code === feature.properties.gss_code);
    }
    
    function updateSelectionList() {
      const listEl = document.getElementById('selected-list');
      if (selectedAreas.length === 0) {
        listEl.innerHTML = '<p style="color: #666;">No areas selected</p>';
      } else {
        listEl.innerHTML = selectedAreas.map(area => `
          <div class="selected-area">
            <strong>${area.name}</strong><br/>
            <small>${area.gss_code} (${area.level})</small>
          </div>
        `).join('');
      }
    }
    
    // Event listeners
    document.getElementById('level').addEventListener('change', (e) => {
      currentLevel = e.target.value;
      loadBoundaries(currentLevel);
    });
    
    let searchTimeout;
    document.getElementById('search').addEventListener('input', (e) => {
      clearTimeout(searchTimeout);
      searchTimeout = setTimeout(async () => {
        const term = e.target.value;
        if (term.length >= 3) {
          // Call search tool and filter/highlight results
          const results = await app.callTool('search_geographic_areas', {
            query: term,
            level: currentLevel
          });
          // Update map with search results...
        }
      }, 300);
    });
    
    document.getElementById('confirm-btn').addEventListener('click', async () => {
      if (selectedAreas.length === 0) {
        await app.sendNotification({
          level: 'warning',
          message: 'Please select at least one area'
        });
        return;
      }
      
      // Return selection to host via MCP protocol
      await app.returnResult({
        status: 'selected',
        areas: selectedAreas,
        count: selectedAreas.length,
        level: currentLevel
      });
    });
    
    // Initialize with config from tool call
    await app.initialize();
    const config = app.getInitialConfig();
    
    if (config) {
      currentLevel = config.level || 'local_auth';
      if (config.initial_view) {
        map.setView([config.initial_view.lat, config.initial_view.lng], config.initial_view.zoom);
      }
      if (config.search_term) {
        document.getElementById('search').value = config.search_term;
      }
    }
    
    // Load initial boundaries
    await loadBoundaries(currentLevel);
    
    // Notify host that widget is ready
    await app.sendNotification({
      level: 'info',
      message: 'Geography selector ready'
    });
  </script>
</body>
</html>
```

## Testing Strategy

### 1. Unit Tests
```python
# tests/test_ui_resources.py

import pytest
from src.ui_resources import register_ui_resources
from fastmcp import FastMCP

@pytest.mark.asyncio
async def test_geography_selector_registration():
    mcp = FastMCP("test")
    await register_ui_resources(mcp)
    
    # Verify resource was registered
    resources = await mcp.list_resources()
    geo_selector = next(
        r for r in resources 
        if r.uri == "ui://os-ons/geography-selector"
    )
    
    assert geo_selector is not None
    assert geo_selector.mime_type == "text/html;profile=mcp-app"
    assert "Interactive map widget" in geo_selector.description

@pytest.mark.asyncio  
async def test_select_geographic_area_tool():
    from src.tools.geography_tools import select_geographic_area
    
    result = await select_geographic_area(
        level="ward",
        initial_location={"lat": 52.48, "lng": -1.89, "zoom": 12}
    )
    
    assert result["status"] == "selection_pending"
    assert result["config"]["level"] == "ward"
    assert "instructions" in result
```

### 2. Integration Tests
```python
# tests/integration/test_widget_interaction.py

import pytest
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_geography_selector_widget_flow():
    """Test complete user flow through geography selector widget"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        # Load widget (simulated host environment)
        await page.goto("http://localhost:8000/widgets/geography-selector")
        
        # Wait for map to load
        await page.wait_for_selector("#map")
        
        # Change geographic level
        await page.select_option("#level", "ward")
        
        # Verify boundaries loaded
        await page.wait_for_function(
            "() => document.querySelectorAll('.leaflet-interactive').length > 0"
        )
        
        # Click on a boundary
        await page.click(".leaflet-interactive:first-child")
        
        # Verify selection appears in list
        selected_areas = await page.locator(".selected-area").count()
        assert selected_areas == 1
        
        # Click confirm button
        await page.click("#confirm-btn")
        
        # Verify MCP message was sent (check postMessage calls)
        # This would require message interception setup
        
        await browser.close()
```

### 3. End-to-End Tests
```python
# tests/e2e/test_claude_integration.py

import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_geography_selection_with_claude():
    """Test full workflow with MCP client"""
    
    # Start MCP server
    params = StdioServerParameters(
        command="python",
        args=["-m", "server"],
        env={"OS_API_KEY": os.getenv("OS_API_KEY")}
    )
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            assert any(t.name == "select_geographic_area" for t in tools.tools)
            
            # List UI resources
            resources = await session.list_resources()
            geo_selector = next(
                r for r in resources.resources
                if r.uri == "ui://os-ons/geography-selector"
            )
            assert geo_selector is not None
            
            # Call tool that uses UI
            result = await session.call_tool(
                "select_geographic_area",
                {"level": "local_auth"}
            )
            
            assert result.content[0].type == "text"
            data = json.loads(result.content[0].text)
            assert data["status"] == "selection_pending"
            
            # Verify _meta contains UI resource reference
            assert "_meta" in result.content[0]
            assert "uiResourceUris" in result.content[0]._meta
```

## Performance Optimization

### 1. Boundary Simplification Strategy
```python
SIMPLIFICATION_LEVELS = {
    "parl_const": {
        "zoom_0_5": 0.01,    # Very simplified for national view
        "zoom_6_9": 0.005,   # Medium detail
        "zoom_10_plus": 0.001 # High detail
    },
    "local_auth": {
        "zoom_0_6": 0.01,
        "zoom_7_10": 0.003,
        "zoom_11_plus": 0.0005
    },
    # ... other levels
}

async def fetch_boundaries_optimized(
    level: str,
    bbox: tuple[float, float, float, float],
    zoom: int
) -> Dict[str, Any]:
    """Fetch boundaries with appropriate simplification for zoom level"""
    
    simplification = get_simplification_for_zoom(level, zoom)
    
    # Use spatial index to only fetch features in viewport
    features = await spatial_query(level, bbox)
    
    # Simplify geometries
    simplified_features = [
        simplify_feature(f, simplification)
        for f in features
    ]
    
    return {
        "type": "FeatureCollection",
        "features": simplified_features,
        "metadata": {
            "simplification": simplification,
            "feature_count": len(simplified_features)
        }
    }
```

### 2. Caching Strategy
```python
from functools import lru_cache
from datetime import datetime, timedelta

class BoundaryCache:
    """Cache for boundary GeoJSON data"""
    
    def __init__(self, ttl_seconds=3600):
        self.ttl = timedelta(seconds=ttl_seconds)
        self.cache = {}
    
    def get(self, key: str) -> Optional[Dict]:
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, data: Dict):
        self.cache[key] = (data, datetime.now())
    
    def invalidate(self, pattern: str = None):
        if pattern:
            keys_to_delete = [k for k in self.cache if pattern in k]
            for k in keys_to_delete:
                del self.cache[k]
        else:
            self.cache.clear()

# Global cache instance
boundary_cache = BoundaryCache(ttl_seconds=3600)

async def fetch_boundaries_cached(level: str, bbox: str) -> Dict:
    cache_key = f"{level}:{bbox}"
    cached = boundary_cache.get(cache_key)
    
    if cached:
        return cached
    
    data = await fetch_boundaries_from_api(level, bbox)
    boundary_cache.set(cache_key, data)
    return data
```

### 3. Progressive Loading
```javascript
// In widget: Load visible features first, then surrounding area

class ProgressiveBoundaryLoader {
  constructor(map, level) {
    this.map = map;
    this.level = level;
    this.loadedTiles = new Set();
    this.loading = false;
  }
  
  async loadVisibleBoundaries() {
    const bounds = this.map.getBounds();
    const center = this.map.getCenter();
    const zoom = this.map.getZoom();
    
    // Load center tile first
    await this.loadTile(center, zoom, 'high-priority');
    
    // Load surrounding tiles
    const surroundingTiles = this.getSurroundingTiles(center, zoom);
    for (const tile of surroundingTiles) {
      await this.loadTile(tile.center, zoom, 'low-priority');
    }
  }
  
  async loadTile(center, zoom, priority) {
    const tileKey = `${center.lat.toFixed(2)},${center.lng.toFixed(2)},${zoom}`;
    
    if (this.loadedTiles.has(tileKey)) {
      return;
    }
    
    this.loadedTiles.add(tileKey);
    
    const bbox = this.calculateTileBbox(center, zoom);
    const boundaries = await app.callTool('fetch_boundaries_geojson', {
      level: this.level,
      bbox: bbox,
      zoom: zoom,
      priority: priority
    });
    
    this.renderBoundaries(boundaries);
  }
}
```

## Monitoring & Analytics

### 1. Usage Metrics
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ToolUsageMetric:
    tool_name: str
    timestamp: datetime
    duration_ms: float
    status: str
    user_id: Optional[str]
    error: Optional[str]

class MetricsCollector:
    def __init__(self):
        self.metrics = []
    
    async def record_tool_call(
        self,
        tool_name: str,
        duration_ms: float,
        status: str,
        error: Optional[str] = None
    ):
        metric = ToolUsageMetric(
            tool_name=tool_name,
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            status=status,
            user_id=None,  # Optional user tracking
            error=error
        )
        self.metrics.append(metric)
        
        # Send to analytics service if configured
        if os.getenv("ANALYTICS_ENDPOINT"):
            await self.send_to_analytics(metric)
    
    def get_summary(self, time_window_hours: int = 24) -> Dict:
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        return {
            "total_calls": len(recent),
            "unique_tools": len(set(m.tool_name for m in recent)),
            "average_duration_ms": sum(m.duration_ms for m in recent) / len(recent),
            "error_rate": len([m for m in recent if m.status == "error"]) / len(recent),
            "most_used_tools": self.get_top_tools(recent, limit=5)
        }

# Global collector
metrics = MetricsCollector()
```

### 2. Error Tracking
```python
import logging
import traceback
from typing import Any

class ErrorTracker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_counts = {}
    
    async def track_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        tool_name: Optional[str] = None
    ):
        error_type = type(error).__name__
        
        # Increment counter
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Log with full context
        self.logger.error(
            f"Error in {tool_name or 'unknown'}: {error_type}",
            extra={
                "error_type": error_type,
                "error_message": str(error),
                "context": context,
                "traceback": traceback.format_exc()
            }
        )
        
        # Send to error tracking service if configured
        if os.getenv("SENTRY_DSN"):
            import sentry_sdk
            sentry_sdk.capture_exception(error)
    
    def get_error_summary(self) -> Dict[str, int]:
        return dict(sorted(
            self.error_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ))

error_tracker = ErrorTracker()
```

## Documentation

### 1. API Documentation (OpenAPI)
```yaml
openapi: 3.0.0
info:
  title: OS/ONS MCP Server
  version: 1.0.0
  description: Exemplar MCP server for UK geographic and statistical data

components:
  schemas:
    GeographicArea:
      type: object
      properties:
        gss_code:
          type: string
          example: "E14000639"
        name:
          type: string
          example: "Coventry North East"
        level:
          type: string
          enum: [parl_const, local_auth, ward, lsoa, msoa, oa]
        geometry:
          type: object
          description: GeoJSON geometry
    
    UIConfig:
      type: object
      properties:
        level:
          type: string
        initial_view:
          type: object
          properties:
            lat: { type: number }
            lng: { type: number }
            zoom: { type: integer }

paths:
  /mcp/tools/select_geographic_area:
    post:
      summary: Select geographic area with interactive widget
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                level:
                  type: string
                  default: local_auth
                initial_location:
                  $ref: '#/components/schemas/UIConfig/properties/initial_view'
      responses:
        '200':
          description: Widget configuration
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [selection_pending, selected]
                  config:
                    $ref: '#/components/schemas/UIConfig'
```

### 2. User Guide
Create comprehensive documentation in `docs/user_guide.md`:
- Getting started tutorials
- Widget interaction guides
- Common use cases with examples
- Troubleshooting section
- FAQ

### 3. Developer Guide  
Create technical documentation in `docs/developer_guide.md`:
- Architecture overview
- Adding new tools
- Creating new UI widgets
- Testing guidelines
- Deployment instructions

## Deployment Considerations

### 1. Environment Configuration
```bash
# .env.production
OS_API_KEY=your_production_key
ONS_API_KEY=your_ons_key  # If required
BEARER_TOKENS=secure_token_1,secure_token_2
ALLOWED_ORIGINS=https://claude.ai,https://chatgpt.com
SENTRY_DSN=https://...
ANALYTICS_ENDPOINT=https://...
BOUNDARY_CACHE_TTL=3600
LOG_LEVEL=INFO
```

### 2. Docker Production Build
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .[prod]

# Copy application
COPY src/ ./src/
COPY ui/ ./ui/

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run server
CMD ["python", "-m", "server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8000"]
```

### 3. Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: os-ons-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: os-ons-mcp
  template:
    metadata:
      labels:
        app: os-ons-mcp
    spec:
      containers:
      - name: mcp-server
        image: ghcr.io/chris-page-gov/os-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: OS_API_KEY
          valueFrom:
            secretKeyRef:
              name: os-mcp-secrets
              key: os-api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: os-ons-mcp-service
spec:
  selector:
    app: os-ons-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Future Enhancements

### Phase 6: Advanced Features (Future)
- [ ] Real-time collaborative selection (multiple users)
- [ ] Saved workspaces and favorite areas
- [ ] Custom geographic hierarchies
- [ ] Integration with external GIS tools (QGIS, ArcGIS)
- [ ] Mobile-optimized widgets
- [ ] Offline mode with local caching
- [ ] Voice interaction support
- [ ] Augmented reality boundary visualization

### Phase 7: AI Enhancements
- [ ] LLM-powered area recommendations
- [ ] Automated insights from statistical analysis
- [ ] Natural language query generation
- [ ] Predictive models for planning scenarios
- [ ] Anomaly detection in geographic data

### Phase 8: Community Features
- [ ] Share maps and analyses publicly
- [ ] Community-contributed boundary definitions
- [ ] Discussion forums per geographic area
- [ ] Wiki-style area information pages

## Success Metrics

### Technical Metrics
- Widget load time < 2s (p95)
- Tool response time < 1s (p95)
- Boundary rendering time < 500ms (p95)
- Cache hit rate > 80%
- Error rate < 0.1%
- Test coverage > 85%

### User Experience Metrics
- Time to first selection < 30s
- Successful completion rate > 90%
- User satisfaction score > 4.5/5
- Feature discovery rate (users finding UI widgets) > 70%

### Business Metrics
- Tool usage growth month-over-month
- Number of geographic areas explored
- Variety of use cases (planning, research, analysis)
- Integration by other MCP servers (if open-sourced)

## Conclusion

This design creates an exemplar MCP server that demonstrates:

1. **Best-in-class MCP-Apps implementation** - Full use of interactive UI resources with proper security sandboxing
2. **Excellent context building** - Layered architecture with skills, metadata resources, and intelligent tool composition  
3. **Comprehensive geographic coverage** - All major UK administrative levels from constituencies to output areas
4. **Production-ready architecture** - Caching, monitoring, testing, and deployment strategies
5. **Extensibility** - Clear patterns for adding new widgets, tools, and data sources

The server serves as both a practical tool for working with UK geographic data and a reference implementation for other MCP server developers looking to incorporate interactive UI elements.

By combining Ordnance Survey's detailed spatial features with ONS statistical data and presenting them through intuitive interactive widgets, this MCP server enables LLMs to help users with complex geographic analysis tasks that would otherwise require specialized GIS knowledge and tools.
