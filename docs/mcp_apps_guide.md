# MCP-Apps User Guide

This guide covers the interactive widget features available in the OS/ONS MCP server. These widgets run in MCP-Apps compatible hosts (like Claude Desktop) and provide visual, interactive interfaces for geographic analysis.

## Quick Start

### 1. Select a Geographic Area

Open the geography selector to choose UK areas interactively:

```
select_geographic_area(level="local_auth")
```

This opens a map widget where you can:
- Click areas to select/deselect them
- Use the dropdown to change geographic levels
- Search by name or postcode
- Multi-select for comparisons

### 2. Get Statistics for Selected Areas

Once you have area codes, fetch ONS statistics:

```
get_statistics(
    dataset_id="wellbeing-local-authority",
    area_codes=["E08000026"]  # Coventry
)
```

### 3. Compare Multiple Areas

Compare statistics across areas:

```
compare_areas(
    area_codes=["E08000026", "E08000025"],  # Coventry, Birmingham
    dataset_id="wellbeing-local-authority"
)
```

## Interactive Widgets

### Geography Selector (`ui://os-ons/geography-selector`)

An interactive Leaflet map for selecting UK geographic areas.

**Open the widget:**
```
select_geographic_area(level="local_auth")
```

**Widget features:**
- **Area selection**: Click to select, click again to deselect
- **Level switching**: Dropdown to change geographic level
- **Search**: Search by area name or postcode
- **Multi-select**: Select multiple areas for comparison
- **Visual feedback**: Selected areas highlighted in blue

**Geographic levels:**
| Level | Description | Approx. Count |
|-------|-------------|---------------|
| `parl_const` | Parliamentary Constituencies | 650 |
| `local_auth` | Local Authority Districts | 350 |
| `ward` | Electoral Wards | 8,000 |
| `msoa` | Middle Super Output Areas | 7,000 |
| `lsoa` | Lower Super Output Areas | 35,000 |
| `oa` | Output Areas | 180,000 |

**Example: Start zoomed to Birmingham**
```
select_geographic_area(
    level="ward",
    initial_lat=52.4862,
    initial_lng=-1.8904,
    initial_zoom=12
)
```

**Example: Focus on a larger area and select output areas**
```
select_geographic_area(
    level="oa",
    focus_level="parl_const",
    focus_name="Coventry West"
)
```

### Statistics Dashboard (`ui://os-ons/statistics-dashboard`)

Interactive visualizations for ONS statistics.

**Triggered automatically** when fetching statistics with area codes.

**Dashboard features:**
- **Summary cards**: Latest value, average, range
- **Charts**: Line and bar charts (Chart.js)
- **Comparison table**: Multi-area rankings
- **Data table**: Full observation data
- **Export**: CSV, JSON, clipboard

### Feature Inspector (`ui://os-ons/feature-inspector`)

Detailed view of OS NGD features with linked identifiers.

**Open the widget:**
```
inspect_feature(
    collection_id="bld-fts-buildingpart-1",
    feature_id="osgb1000000123456"
)
```

**Inspector features:**
- **Properties table**: Filterable, type-aware formatting
- **Map view**: Feature geometry on Leaflet map
- **Linked identifiers**: Tabs for TOID, UPRN, USRN
- **Navigation**: Click linked IDs to navigate
- **Export**: JSON, CSV, clipboard

### Route Planner (`ui://os-ons/route-planner`)

Interactive route planning with directions.

**Open the widget:**
```
plan_route(
    start_lat=52.4081,
    start_lng=-1.5106,
    end_lat=52.4862,
    end_lng=-1.8904
)
```

**Or open with no preset points:**
```
plan_route()
```

**Route planner features:**
- **Map selection**: Click to set start (green) and end (red)
- **Drag markers**: Adjust point positions
- **Waypoints**: Add intermediate stops
- **Directions**: Turn-by-turn instructions
- **Summary**: Distance and estimated time

## Working with Statistics

### Discover Datasets

List available ONS datasets:

```
list_ons_datasets()                              # All datasets
list_ons_datasets(category="wellbeing")          # Wellbeing datasets
list_ons_datasets(search="house price")          # Search by keyword
list_ons_datasets(category="census", include_census=True)  # Census 2021
```

**Dataset categories:**
- `wellbeing` - Life satisfaction, happiness, anxiety
- `economy` - GDP, regional economic data
- `housing` - House prices
- `population` - Population estimates
- `health` - Life expectancy, mortality
- `employment` - Earnings, businesses
- `census` - Census 2021 tables (30+ datasets)

### Get Dataset Details

Understand a dataset's structure:

```
get_dataset_info(dataset_id="wellbeing-local-authority")
```

Returns: dimensions, available filters, latest edition, value labels.

### Fetch Statistics

Get observations for specific areas:

```
get_statistics(
    dataset_id="wellbeing-local-authority",
    area_codes=["E08000026"],
    measure="life-satisfaction"  # Optional filter
)
```

### Compare Areas

Side-by-side comparison:

```
compare_areas(
    area_codes=["E08000026", "E08000025", "E08000027"],
    dataset_id="wellbeing-local-authority"
)
```

Returns: comparison table with rankings.

## Working with OS Features

### Search for Features

Find features using the OS NGD API:

```
# First initialize workflow
os_ngd_init_mapping_workflow()

# Then get queryables
fetch_detailed_collections(collection_ids=["bld-fts-buildingpart-1"])

# Now search
search_features(
    collection_id="bld-fts-buildingpart-1",
    bbox="-1.6,52.4,-1.5,52.5",
    limit=10
)
```

### Inspect a Feature

View feature details in the inspector:

```
inspect_feature(
    collection_id="bld-fts-buildingpart-1",
    feature_id="osgb1000000123456"
)
```

### Explore Linked Identifiers

Get feature data with links:

```
get_feature_with_linked(
    collection_id="bld-fts-buildingpart-1",
    feature_id="osgb1000000123456",
    identifier_type="UPRN"
)
```

**Linked identifier types:**
- `TOID` - Topographic identifiers
- `UPRN` - Unique Property Reference Numbers
- `USRN` - Unique Street Reference Numbers

## Cross-Widget Communication

Widgets can share selections using the shared context.

### Get Current Context

```
get_shared_context()
```

Returns: all current selections (areas, features, datasets, route points).

### Update Context

```
# Add selected area
update_shared_context(
    context_type="areas",
    action="add",
    data={"code": "E08000026", "name": "Coventry"}
)

# Clear all route points
update_shared_context(
    context_type="route_points",
    action="clear"
)
```

**Context types:** `areas`, `features`, `datasets`, `route_points`, `bbox`

**Actions:** `add`, `remove`, `clear`, `set`

### Share Between Widgets

```
share_selection(
    source_widget="geography",
    target_widget="statistics",
    selection_data={"areas": [{"code": "E08000026", "name": "Coventry"}]}
)
```

## Common Workflows

### Workflow 1: Local Area Analysis

1. Search for your area:
   ```
   search_geographic_areas(query="Coventry")
   ```

2. Get wellbeing statistics:
   ```
   get_statistics(
       dataset_id="wellbeing-local-authority",
       area_codes=["E08000026"]
   )
   ```

3. Compare with neighboring areas:
   ```
   compare_areas(
       area_codes=["E08000026", "E08000025"],
       dataset_id="wellbeing-local-authority"
   )
   ```

### Workflow 2: Interactive Selection to Analysis

1. Open map selector:
   ```
   select_geographic_area(level="local_auth", multi_select=True)
   ```

2. User selects areas on map...

3. Use returned codes for statistics:
   ```
   get_statistics(
       dataset_id="house-prices-local-authority",
       area_codes=["E08000026", "E08000025"]
   )
   ```

### Workflow 3: Feature Exploration

1. Initialize workflow:
   ```
   os_ngd_init_mapping_workflow()
   fetch_detailed_collections(collection_ids=["bld-fts-buildingpart-1"])
   ```

2. Search for buildings:
   ```
   search_features(
       collection_id="bld-fts-buildingpart-1",
       bbox="-1.52,52.4,-1.5,52.42",
       limit=5
   )
   ```

3. Inspect a building:
   ```
   inspect_feature(
       collection_id="bld-fts-buildingpart-1",
       feature_id="..."
   )
   ```

### Workflow 4: Route Planning

1. Open route planner:
   ```
   plan_route()
   ```

2. Or preset the endpoints:
   ```
   plan_route(
       start_lat=52.4081, start_lng=-1.5106,
       end_lat=52.4862, end_lng=-1.8904
   )
   ```

3. Get road network data:
   ```
   get_route_network(bbox="-1.6,52.4,-1.5,52.5")
   ```

## Troubleshooting

### "Workflow context required" error

For OS NGD data tools, you must first call:
```
os_ngd_init_mapping_workflow()
```

Then for specific collections:
```
fetch_detailed_collections(collection_ids=["your-collection"])
```

### No statistics returned

1. Check the area code format (should be like `E08000026`)
2. Verify the dataset exists: `list_ons_datasets()`
3. Check dataset dimensions: `get_dataset_info(dataset_id="...")`

### Widget not rendering

1. Ensure your MCP host supports MCP-Apps (`ui://` resources)
2. Check the `_meta.uiResourceUris` in the tool response
3. Try a simpler call first: `select_geographic_area()`

### Rate limiting

ONS API has limits: 120 requests/10 seconds. If you hit limits:
1. Wait a few seconds
2. Reduce batch sizes
3. Use caching where available

## Tips

1. **Start broad, then narrow**: Use `local_auth` level first, then drill into `ward` or `lsoa`

2. **Use search**: `search_geographic_areas()` is faster than browsing

3. **Check dataset info**: Always call `get_dataset_info()` before `get_statistics()` to understand dimensions

4. **Export data**: All widgets support export (JSON, CSV, clipboard)

5. **Share context**: Use `share_selection()` to pass data between widgets without manual re-entry
