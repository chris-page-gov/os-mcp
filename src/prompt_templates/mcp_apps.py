"""MCP-Apps Widget Prompt Templates

Prompts for using interactive MCP-Apps widgets effectively:
- Geography selection workflow
- Statistics exploration workflow
- Feature inspection workflow
- Route planning workflow
- Cross-widget workflows
"""

from typing import Dict

MCP_APPS_PROMPTS: Dict[str, str] = {
    # =========================================================================
    # Geography Selection Workflows
    # =========================================================================
    "select_uk_areas": (
        "Help the user select UK geographic areas using the interactive map widget. "
        "Step 1: Call select_geographic_area(level='{level}') to open the geography selector widget. "
        "Available levels: parl_const (constituencies), local_auth (local authorities), ward (wards), "
        "lsoa (lower super output areas), msoa (middle super output areas), oa (output areas). "
        "Step 2: The widget returns selected area codes and names. "
        "Step 3: Use the returned codes with fetch_boundaries() to get GeoJSON boundaries, "
        "or with get_statistics() to retrieve ONS data for those areas. "
        "Tip: For large-scale analysis, start with local_auth or parl_const level."
    ),
    "find_area_by_postcode": (
        "Find UK geographic areas near a postcode. "
        "Step 1: Call search_geographic_areas(query='{postcode}') to find areas containing the postcode. "
        "This uses postcodes.io to resolve the postcode to coordinates and returns matching areas. "
        "Step 2: Results include area name, code, level, and distance from the postcode. "
        "Step 3: Use the area codes with get_statistics() for ONS data or fetch_boundaries() for GeoJSON."
    ),
    "compare_local_authorities": (
        "Compare statistics across multiple UK local authority areas. "
        "Step 1: Call select_geographic_area(level='local_auth', multi_select=True) to select areas. "
        "Step 2: Once areas are selected, call compare_areas(area_codes=[codes], dataset_id='wellbeing-local-authority'). "
        "Step 3: Review the comparison table showing values, rankings, and differences. "
        "Popular datasets: wellbeing-local-authority, house-prices-local-authority, mid-year-pop-est, "
        "life-expectancy-by-local-authority, gdp-by-local-authority."
    ),

    # =========================================================================
    # Statistics Exploration Workflows
    # =========================================================================
    "explore_ons_statistics": (
        "Explore ONS statistics for UK areas using the dashboard widget. "
        "Step 1: Call list_ons_datasets(category='{category}') to discover available datasets. "
        "Categories: wellbeing, economy, housing, population, health, employment, census. "
        "Step 2: Call get_dataset_info(dataset_id='...') to understand dimensions and available filters. "
        "Step 3: Call get_statistics(dataset_id='...', area_codes=[...]) to fetch data. "
        "The statistics dashboard widget displays charts, summary cards, and comparison tables."
    ),
    "census_2021_analysis": (
        "Analyze Census 2021 data for UK areas. "
        "Step 1: Call list_ons_datasets(category='census', include_census=True) to list Census datasets. "
        "Census datasets have codes like TS063 (Occupation), TS067 (Qualifications), TS061 (Travel to work). "
        "Step 2: Call get_dataset_info(dataset_id='..') to see available dimensions (age, sex, etc.). "
        "Step 3: Call get_statistics(dataset_id='..',area_codes=[...], dimensions={...}) for specific breakdowns. "
        "Note: Census data requires ALL dimensions to be specified; use get_dataset_info to understand them."
    ),
    "area_wellbeing_profile": (
        "Create a wellbeing profile for a UK area. "
        "Step 1: Get the area code - either call select_geographic_area() or use a known code. "
        "Step 2: Fetch wellbeing data: get_statistics(dataset_id='wellbeing-local-authority', area_codes=['E09000001']). "
        "Step 3: The dashboard shows life satisfaction, happiness, anxiety, and worthwhile measures. "
        "Step 4: Compare with national average or nearby areas using compare_areas(). "
        "Wellbeing measures: life-satisfaction, worthwhile, happiness, anxiety (on 0-10 scale)."
    ),

    # =========================================================================
    # Feature Inspection Workflows
    # =========================================================================
    "inspect_os_feature": (
        "Inspect a feature from the OS NGD and explore linked identifiers. "
        "Step 1: Search for features using search_features() or get_feature(). "
        "Step 2: Call inspect_feature(collection_id='..', feature_id='..') to open the inspector widget. "
        "Step 3: The widget displays: properties table, map view, and linked identifiers (TOID, UPRN, USRN). "
        "Step 4: Click linked identifiers to navigate to related features. "
        "Example: Inspect a building to see its UPRN addresses, or a road to see its USRN street records."
    ),
    "explore_linked_identifiers": (
        "Explore linked identifiers for an OS NGD feature. "
        "Step 1: Call get_feature_with_linked(collection_id='bld-fts-buildingpart-1', feature_id='..') "
        "Step 2: Review the linked identifiers in the response: "
        "  - TOID: Topographic identifiers linking to other map features "
        "  - UPRN: Unique Property Reference Numbers for addressable locations "
        "  - USRN: Unique Street Reference Numbers for road/street records "
        "Step 3: Use the linked IDs to fetch related features: "
        "  get_feature(collection_id='lnk-ids-toid', identifier='osgb1000000123456') "
        "This enables traversing the OS linked data graph."
    ),

    # =========================================================================
    # Route Planning Workflows
    # =========================================================================
    "plan_walking_route": (
        "Plan a walking route between two points in the UK. "
        "Step 1: Call plan_route(start_lat=51.5, start_lng=-0.1, end_lat=51.51, end_lng=-0.09, mode='walk') "
        "Step 2: The route planner widget opens with the start/end markers placed on the map. "
        "Step 3: Drag markers to adjust points, or add waypoints for multi-stop routes. "
        "Step 4: Review turn-by-turn directions and route summary (distance, estimated time). "
        "Step 5: Export the route as GeoJSON for use in other applications."
    ),
    "plan_driving_route": (
        "Plan a driving route between two points in the UK. "
        "Step 1: Call plan_route(start_lat=..., start_lng=..., end_lat=..., end_lng=..., mode='drive') "
        "Step 2: The widget displays the route with driving directions. "
        "Step 3: Add waypoints by clicking on the map for multi-stop routes. "
        "Step 4: Review route summary including distance and estimated driving time. "
        "Note: Driving routes follow UK road rules and consider road classifications."
    ),
    "analyze_road_network": (
        "Analyze the road network in a specific area. "
        "Step 1: Define a bounding box: [min_lng, min_lat, max_lng, max_lat] "
        "Step 2: Call get_route_network(bbox=[-0.15, 51.5, -0.1, 51.52]) to fetch road network data. "
        "Step 3: Review the returned network including: "
        "  - Road links with classifications (A-road, B-road, motorway, etc.) "
        "  - Road nodes (junctions, roundabouts) "
        "  - Street names and USRN references "
        "Step 4: Use with get_routing_data() for turn restrictions and traffic regulations."
    ),

    # =========================================================================
    # Cross-Widget Workflows
    # =========================================================================
    "area_to_statistics_workflow": (
        "Select geographic areas and analyze their statistics. "
        "Step 1: Call select_geographic_area(level='local_auth', multi_select=True) to select areas. "
        "Step 2: Call update_shared_context(action='add', selection_type='area', items=[...]) to share selections. "
        "Step 3: Call get_statistics(dataset_id='...', area_codes=[...]) with the selected area codes. "
        "Step 4: The statistics dashboard automatically receives the shared context. "
        "This workflow connects the geography selector with the statistics dashboard."
    ),
    "feature_to_route_workflow": (
        "Find a feature and plan a route to it. "
        "Step 1: Search for a feature: search_features(collection_id='bld-fts-buildingpart-1', query='..') "
        "Step 2: Call inspect_feature() to view the feature details and get its coordinates. "
        "Step 3: Call share_selection(source_widget='feature-inspector', target_widget='route-planner', "
        "selection_data={lat, lng}) to share the location. "
        "Step 4: The route planner opens with the feature as the destination. "
        "Step 5: Set your starting point and get directions."
    ),
    "multi_widget_analysis": (
        "Perform comprehensive analysis using multiple widgets. "
        "Step 1: Select areas: select_geographic_area() "
        "Step 2: Share to statistics: update_shared_context(action='add', selection_type='area', items=[...]) "
        "Step 3: Fetch statistics: get_statistics() for each area "
        "Step 4: Fetch boundaries: fetch_boundaries() for mapping "
        "Step 5: Inspect features within areas: search_features() then inspect_feature() "
        "Use get_shared_context() at any time to see current cross-widget selections."
    ),
}
