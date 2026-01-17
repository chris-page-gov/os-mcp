# OS/ONS MCP Server Skills

This document describes how to effectively use the Ordnance Survey / Office for National Statistics MCP server for UK geospatial and statistical analysis.

## Overview

This MCP server provides access to:
- **Ordnance Survey Data Hub** - UK mapping and geospatial data (NGD Features API)
- **ONS Statistics API** - UK government statistics (wellbeing, population, economy, census)
- **ONS Geography API** - UK administrative boundaries (local authorities, wards, constituencies)
- **Interactive Widgets** - Map-based selection, statistics dashboards, feature inspection, route planning

## Key Concepts

### Two-Step Workflow (OS Data Hub)

For OS NGD data queries, follow the required workflow:

1. **Initialize context**: Call `get_workflow_context()` to get available collections
2. **Get queryables**: Call `fetch_detailed_collections(collection_ids=[...])` for specific collections
3. **Search data**: Now you can call `search_features()`, `get_feature()`, etc.

**Exception**: Geography, statistics, widget, and diagnostic tools bypass this requirement.

### Geographic Hierarchy (UK)

The UK has multiple administrative levels (largest to smallest):

| Level | Code | Count | Example |
|-------|------|-------|---------|
| Parliamentary Constituencies | `parl_const` | ~650 | "Coventry South" |
| Local Authority Districts | `local_auth` | ~350 | "Birmingham", "Coventry" |
| Electoral Wards | `ward` | ~8,000 | "Longford (Coventry)" |
| Middle Super Output Areas | `msoa` | ~7,000 | "Coventry 001" |
| Lower Super Output Areas | `lsoa` | ~35,000 | "Coventry 001A" |
| Output Areas | `oa` | ~180,000 | "E00043001" |

### Area Codes

UK geographic areas use standard codes:
- **Local Authorities**: E09000001 (London boroughs), E08000026 (metropolitan districts), E07000001 (shire districts)
- **Constituencies**: E14000001 format
- **Wards**: E05000001 format
- **LSOA/MSOA/OA**: E01000001, E02000001, E00000001 formats

## Common Workflows

### 1. Find and Analyze a Local Area

```
User: "What's the wellbeing like in Coventry?"

Steps:
1. search_geographic_areas(query="Coventry", level="local_auth")
   → Returns: {code: "E08000026", name: "Coventry"}

2. get_statistics(dataset_id="wellbeing-local-authority", area_codes=["E08000026"])
   → Returns: life satisfaction, happiness, anxiety scores

3. compare_areas(area_codes=["E08000026", "E08000025"], dataset_id="wellbeing-local-authority")
   → Compare Coventry with Birmingham
```

### 2. Interactive Area Selection

```
User: "Help me select some areas on a map"

Steps:
1. select_geographic_area(level="local_auth", multi_select=true)
   → Opens interactive map widget
   → User clicks to select areas
   → Returns: [{code: "E08000026", name: "Coventry"}, ...]

2. Use returned codes for further analysis
```

### 3. Census Data Analysis

```
User: "What are the qualification levels in my area?"

Steps:
1. list_ons_datasets(category="census", include_census=true)
   → Lists Census 2021 datasets

2. get_dataset_info(dataset_id="TS067")
   → Shows dimensions: geography, highest qualification level

3. get_statistics(dataset_id="TS067", area_codes=["E08000026"])
   → Returns qualification breakdown
```

### 4. Feature Inspection

```
User: "Tell me about this building"

Steps:
1. search_features(collection_id="bld-fts-buildingpart-1", bbox=[...], limit=1)
   → Returns building feature

2. inspect_feature(collection_id="bld-fts-buildingpart-1", feature_id="...")
   → Opens feature inspector widget
   → Shows: properties, map, linked identifiers (TOID, UPRN, USRN)

3. Click linked UPRN to see associated addresses
```

### 5. Route Planning

```
User: "How do I walk from point A to point B?"

Steps:
1. plan_route(start_lat=52.4, start_lng=-1.5, end_lat=52.41, end_lng=-1.48, mode="walk")
   → Opens route planner widget
   → Shows turn-by-turn directions
   → Displays distance and estimated time
```

## Available Tools

### Geography Tools (No workflow context required)

| Tool | Purpose |
|------|---------|
| `select_geographic_area` | Open interactive map for area selection |
| `fetch_boundaries` | Get GeoJSON boundary for an area |
| `search_geographic_areas` | Search areas by name or postcode |

### Statistics Tools (No workflow context required)

| Tool | Purpose |
|------|---------|
| `list_ons_datasets` | Discover available ONS datasets |
| `get_dataset_info` | Get dataset metadata and dimensions |
| `get_statistics` | Fetch observations for areas |
| `compare_areas` | Compare statistics across areas |

### Feature Tools (No workflow context required)

| Tool | Purpose |
|------|---------|
| `inspect_feature` | Open feature inspector widget |
| `get_feature_with_linked` | Get feature data with linked identifiers |

### Route Tools (No workflow context required)

| Tool | Purpose |
|------|---------|
| `plan_route` | Open route planner widget |
| `get_route_network` | Get road network for a bbox |

### Cross-Widget Tools (No workflow context required)

| Tool | Purpose |
|------|---------|
| `get_shared_context` | Get current shared selections |
| `update_shared_context` | Add/remove shared selections |
| `share_selection` | Share between widgets |

### OS Data Tools (Require workflow context)

| Tool | Purpose |
|------|---------|
| `get_workflow_context` | Initialize workflow planner |
| `fetch_detailed_collections` | Get queryables for collections |
| `search_features` | Search NGD features with filters |
| `get_feature` | Get single feature by ID |
| `get_bulk_features` | Get multiple features |
| `get_linked_identifiers` | Get TOID/UPRN/USRN links |

## Dataset Categories

### ONS Statistics Categories

| Category | Key Datasets | Description |
|----------|--------------|-------------|
| `wellbeing` | wellbeing-local-authority | Life satisfaction, happiness, anxiety |
| `economy` | gdp-by-local-authority | Regional GDP |
| `housing` | house-prices-local-authority | House price indices |
| `population` | mid-year-pop-est | Population estimates |
| `health` | life-expectancy-by-local-authority | Life expectancy |
| `employment` | ashe-tables-7-and-8 | Earnings data |
| `census` | TS063, TS067, TS061... | Census 2021 tables |

### OS NGD Collections

| Collection | Description |
|------------|-------------|
| `bld-fts-buildingpart-1` | Building footprints |
| `trn-ntwk-roadlink-4` | Road network links |
| `trn-ntwk-roadnode-1` | Road network nodes |
| `trn-ntwk-street-1` | Street records |
| `lnk-ids-toid` | TOID linked identifiers |
| `lnk-ids-uprn` | UPRN linked identifiers |
| `lnk-ids-usrn` | USRN linked identifiers |

## Best Practices

### 1. Start with Discovery
- Use `list_ons_datasets()` to find relevant statistics
- Use `get_workflow_context()` to see available OS collections
- Use `search_geographic_areas()` to find area codes

### 2. Be Specific with Geographic Levels
- Use `local_auth` for city/district level analysis
- Use `ward` for neighborhood comparisons
- Use `lsoa` for detailed socioeconomic analysis (Index of Multiple Deprivation)

### 3. Handle Large Result Sets
- Always use `limit` parameter to control response size
- For boundaries, consider using higher-level geographies first
- Use `bbox` filters to constrain spatial queries

### 4. Combine Data Sources
- Select areas with geography tools → analyze with statistics tools
- Search OS features → inspect with feature inspector
- Get statistics → visualize in dashboard widget

### 5. Use Cross-Widget Communication
- Share area selections from geography selector to statistics dashboard
- Share feature locations from inspector to route planner
- Use `get_shared_context()` to see current state

## Error Handling

### Common Errors

| Error Code | Meaning | Resolution |
|------------|---------|------------|
| `WORKFLOW_CONTEXT_REQUIRED` | Must initialize workflow first | Call `get_workflow_context()` |
| `INVALID_COLLECTION` | Collection ID not found | Check collection ID spelling |
| `UPSTREAM_ERROR` | OS/ONS API error | Check API status, retry |
| `RATE_LIMITED` | Too many requests | Wait and retry |

### Rate Limits

- OS Data Hub: Varies by API key tier
- ONS Statistics API: 120 requests/10 seconds, 200 requests/minute

## Interactive Widgets

### Geography Selector (`ui://os-ons/geography-selector`)
- Click areas on map to select
- Use dropdown to change geographic level
- Search by name or postcode
- Multi-select mode for comparing areas

### Statistics Dashboard (`ui://os-ons/statistics-dashboard`)
- View charts (line, bar) of time series data
- Summary cards show latest value, average, range
- Comparison table ranks multiple areas
- Export to CSV, JSON, or clipboard

### Feature Inspector (`ui://os-ons/feature-inspector`)
- Properties table with filtering
- Map view of feature geometry
- Linked identifiers tabs (TOID, UPRN, USRN)
- Click to navigate between linked features

### Route Planner (`ui://os-ons/route-planner`)
- Click map to set start/end points
- Drag markers to adjust
- Add waypoints for multi-stop routes
- View turn-by-turn directions

## Prompt Templates

Use `get_prompt_templates(category="mcp_apps")` to access pre-built workflows:

- `select_uk_areas` - Interactive area selection
- `explore_ons_statistics` - Statistics exploration
- `inspect_os_feature` - Feature inspection with linked IDs
- `plan_walking_route` / `plan_driving_route` - Route planning
- `area_to_statistics_workflow` - Cross-widget workflow

## Quick Reference

```
# Find area code
search_geographic_areas(query="Birmingham")

# Get statistics
get_statistics(dataset_id="wellbeing-local-authority", area_codes=["E08000025"])

# Compare areas
compare_areas(area_codes=["E08000025", "E08000026"], dataset_id="wellbeing-local-authority")

# Open map selector
select_geographic_area(level="local_auth")

# Open feature inspector
inspect_feature(collection_id="bld-fts-buildingpart-1", feature_id="...")

# Plan route
plan_route(start_lat=52.4, start_lng=-1.5, end_lat=52.5, end_lng=-1.4)
```
