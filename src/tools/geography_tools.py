"""Geographic selection tools with MCP-Apps UI support

This module provides tools for selecting and fetching UK geographic boundaries
at various administrative levels using the ONS Geography API.

Tools in this module:
- select_geographic_area: Opens interactive map widget for area selection
- fetch_boundaries: Fetches boundary GeoJSON from ONS Geography API
- search_geographic_areas: Searches for areas by name or postcode
"""

import json
import logging
from typing import Dict, Any, Optional, List
import aiohttp

from utils.error_envelope import build_error_envelope, ErrorCode

logger = logging.getLogger(__name__)

# ONS Geography API base URL (ArcGIS REST services)
ONS_GEOGRAPHY_API_BASE = "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services"

# Geographic level configuration
# Maps level codes to ONS service names and field mappings
# Service names verified against ONS ArcGIS REST services as of January 2025
GEOGRAPHIC_LEVELS: Dict[str, Dict[str, str]] = {
    "parl_const": {
        "name": "Parliamentary Constituencies",
        "service": "Westminster_Parliamentary_Constituencies_July_2024_Boundaries_UK_BFC",
        "code_field": "PCON24CD",
        "name_field": "PCON24NM",
    },
    "local_auth": {
        "name": "Local Authority Districts",
        "service": "Local_Authority_Districts_December_2024_Boundaries_UK_BFC",
        "code_field": "LAD24CD",
        "name_field": "LAD24NM",
    },
    "ward": {
        "name": "Wards",
        "service": "Wards_December_2024_Boundaries_UK_BFC",
        "code_field": "WD24CD",
        "name_field": "WD24NM",
    },
    "lsoa": {
        "name": "Lower Super Output Areas",
        "service": "Lower_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V10",
        "code_field": "LSOA21CD",
        "name_field": "LSOA21NM",
    },
    "msoa": {
        "name": "Middle Super Output Areas",
        "service": "Middle_layer_Super_Output_Areas_December_2021_Boundaries_EW_BFC_V7",
        "code_field": "MSOA21CD",
        "name_field": "MSOA21NM",
    },
    "oa": {
        "name": "Output Areas",
        "service": "Output_Areas_2021_EW_BFC_V8",
        "code_field": "OA21CD",
        "name_field": "LSOA21NM",  # OA has no name field, use parent LSOA name
    },
}


async def _fetch_from_ons_api(
    service_name: str,
    where_clause: str = "1=1",
    out_fields: str = "*",
    geometry: Optional[str] = None,
    geometry_type: str = "esriGeometryEnvelope",
    return_geometry: bool = True,
    result_record_count: int = 100,
) -> Dict[str, Any]:
    """Internal helper to fetch data from ONS ArcGIS REST API.

    Args:
        service_name: Name of the ArcGIS service
        where_clause: SQL-like where clause for filtering
        out_fields: Fields to return (* for all)
        geometry: Optional geometry filter (bbox as "west,south,east,north")
        geometry_type: Type of geometry filter
        return_geometry: Whether to include geometry in response
        result_record_count: Max features to return

    Returns:
        GeoJSON response from API
    """
    url = f"{ONS_GEOGRAPHY_API_BASE}/{service_name}/FeatureServer/0/query"

    params: Dict[str, str] = {
        "where": where_clause,
        "outFields": out_fields,
        "f": "geojson",
        "returnGeometry": str(return_geometry).lower(),
        "resultRecordCount": str(result_record_count),
    }

    if geometry:
        # Parse bbox string "west,south,east,north"
        params["geometry"] = geometry
        params["geometryType"] = geometry_type
        params["spatialRel"] = "esriSpatialRelIntersects"
        params["inSR"] = "4326"  # WGS84

    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"ONS API error {resp.status}: {text[:200]}")
            data: Dict[str, Any] = await resp.json()
            return data


# ============================================================================
# Tool implementations (to be registered in OSDataHubService)
# ============================================================================


async def select_geographic_area(
    level: str = "local_auth",
    initial_lat: Optional[float] = None,
    initial_lng: Optional[float] = None,
    initial_zoom: Optional[int] = None,
    search_term: Optional[str] = None,
    multi_select: bool = True,
) -> str:
    """Opens interactive map widget for selecting UK geographic areas.

    This tool triggers a visual map interface where users can:
    - Click on areas to select them
    - Switch between geographic levels (constituencies, councils, wards, etc.)
    - Search by area name or postcode
    - Select multiple areas for comparison

    Args:
        level: Geographic level to display. Options:
               - parl_const: Parliamentary Constituencies (650 in UK)
               - local_auth: Local Authority Districts (default)
               - ward: Electoral Wards
               - lsoa: Lower Super Output Areas (~35,000)
               - msoa: Middle Super Output Areas (~7,000)
               - oa: Output Areas (~180,000)
        initial_lat: Starting latitude (default: 52.4862 - central UK)
        initial_lng: Starting longitude (default: -1.8904 - central UK)
        initial_zoom: Starting zoom level (default: 6 for UK overview)
        search_term: Optional search query to pre-filter areas
        multi_select: Allow selection of multiple areas (default: True)

    Returns:
        JSON with widget configuration and UI resource reference.
        The host will render the geography selector widget.

    Examples:
        # Open at default UK view for Local Authority selection
        select_geographic_area()

        # Start at Coventry, zoom to ward level
        select_geographic_area(
            level="ward",
            initial_lat=52.4081,
            initial_lng=-1.5106,
            initial_zoom=11
        )

        # Pre-filter to areas matching "Birmingham"
        select_geographic_area(level="local_auth", search_term="Birmingham")
    """
    # Validate level
    if level not in GEOGRAPHIC_LEVELS:
        return json.dumps(
            build_error_envelope(
                tool="select_geographic_area",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid level '{level}'. Must be one of: {', '.join(GEOGRAPHIC_LEVELS.keys())}",
                details={"available_levels": list(GEOGRAPHIC_LEVELS.keys())},
            )
        )

    # Default initial view (Birmingham, UK - central position)
    config = {
        "level": level,
        "level_name": GEOGRAPHIC_LEVELS[level]["name"],
        "initial_view": {
            "lat": initial_lat if initial_lat is not None else 52.4862,
            "lng": initial_lng if initial_lng is not None else -1.8904,
            "zoom": initial_zoom if initial_zoom is not None else 6,
        },
        "search_term": search_term,
        "features": {
            "multi_select": multi_select,
            "show_hierarchy": True,
            "search_enabled": True,
            "show_codes": True,
        },
        "available_levels": [
            {"value": k, "label": v["name"]} for k, v in GEOGRAPHIC_LEVELS.items()
        ],
    }

    return json.dumps(
        {
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
                "audience": ["user"],
            },
        }
    )


async def fetch_boundaries(
    level: str,
    codes: Optional[str] = None,
    bbox: Optional[str] = None,
    limit: int = 100,
) -> str:
    """Fetch boundary geometries for UK geographic areas from ONS.

    This is a data retrieval tool that returns GeoJSON boundaries.
    Use select_geographic_area for interactive selection.

    Args:
        level: Geographic level (parl_const, local_auth, ward, lsoa, msoa, oa)
        codes: Optional comma-separated GSS codes to fetch specific areas
               (e.g., "E08000026,E08000025" for Coventry and Birmingham)
        bbox: Optional bounding box as "west,south,east,north" in WGS84
              (e.g., "-2.0,52.3,-1.7,52.6" for an area around Coventry)
        limit: Maximum number of features to return (default: 100, max: 500)

    Returns:
        GeoJSON FeatureCollection with boundary geometries and properties:
        - GSS code (e.g., E08000026)
        - Area name (e.g., Coventry)
        - Geometry (polygon/multipolygon)

    Examples:
        # Get all Local Authorities in a bounding box
        fetch_boundaries(level="local_auth", bbox="-2.5,52.0,-1.0,53.0")

        # Get specific areas by code
        fetch_boundaries(level="local_auth", codes="E08000026,E08000025")

        # Get all Parliamentary Constituencies (limited)
        fetch_boundaries(level="parl_const", limit=50)
    """
    # Validate level
    if level not in GEOGRAPHIC_LEVELS:
        return json.dumps(
            build_error_envelope(
                tool="fetch_boundaries",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid level '{level}'",
                details={"available_levels": list(GEOGRAPHIC_LEVELS.keys())},
            )
        )

    config = GEOGRAPHIC_LEVELS[level]
    service_name = config["service"]
    code_field = config["code_field"]
    name_field = config["name_field"]

    # Cap limit
    limit = min(max(1, limit), 500)

    try:
        if codes:
            # Fetch specific areas by code
            code_list = [c.strip() for c in codes.split(",") if c.strip()]
            if not code_list:
                return json.dumps(
                    build_error_envelope(
                        tool="fetch_boundaries",
                        code=ErrorCode.INVALID_INPUT,
                        message="No valid codes provided",
                    )
                )

            # Build SQL IN clause
            quoted_codes = ",".join(f"'{c}'" for c in code_list)
            where_clause = f"{code_field} IN ({quoted_codes})"

            result = await _fetch_from_ons_api(
                service_name=service_name,
                where_clause=where_clause,
                out_fields=f"{code_field},{name_field}",
                result_record_count=len(code_list),
            )
        elif bbox:
            # Fetch by bounding box
            result = await _fetch_from_ons_api(
                service_name=service_name,
                geometry=bbox,
                out_fields=f"{code_field},{name_field}",
                result_record_count=limit,
            )
        else:
            # Fetch all (limited)
            result = await _fetch_from_ons_api(
                service_name=service_name,
                out_fields=f"{code_field},{name_field}",
                result_record_count=limit,
            )

        # Normalize property names for consistency
        if "features" in result:
            for feature in result["features"]:
                props = feature.get("properties", {})
                # Add standardized fields
                props["gss_code"] = props.get(code_field)
                props["name"] = props.get(name_field)
                props["level"] = level

        feature_count = len(result.get("features", []))
        logger.info(f"Fetched {feature_count} boundaries for level={level}")

        return json.dumps(
            {
                "type": "FeatureCollection",
                "features": result.get("features", []),
                "metadata": {
                    "level": level,
                    "level_name": config["name"],
                    "count": feature_count,
                    "codes": codes,
                    "bbox": bbox,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error fetching boundaries: {e}")
        return json.dumps(
            build_error_envelope(
                tool="fetch_boundaries",
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(e),
                details={"level": level, "codes": codes, "bbox": bbox},
            )
        )


async def search_geographic_areas(
    query: str,
    level: str = "local_auth",
    limit: int = 10,
) -> str:
    """Search for UK geographic areas by name.

    Args:
        query: Search term (area name, minimum 2 characters)
        level: Geographic level to search within
               (parl_const, local_auth, ward, lsoa, msoa, oa)
        limit: Maximum number of results (default: 10, max: 50)

    Returns:
        JSON with matching areas including GSS codes and names.

    Examples:
        # Search for councils containing "Birmingham"
        search_geographic_areas(query="Birmingham", level="local_auth")

        # Search for wards containing "Central"
        search_geographic_areas(query="Central", level="ward", limit=20)
    """
    # Validate inputs
    if level not in GEOGRAPHIC_LEVELS:
        return json.dumps(
            build_error_envelope(
                tool="search_geographic_areas",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid level '{level}'",
            )
        )

    query = query.strip()
    if len(query) < 2:
        return json.dumps(
            build_error_envelope(
                tool="search_geographic_areas",
                code=ErrorCode.INVALID_INPUT,
                message="Query must be at least 2 characters",
            )
        )

    config = GEOGRAPHIC_LEVELS[level]
    service_name = config["service"]
    code_field = config["code_field"]
    name_field = config["name_field"]

    # Cap limit
    limit = min(max(1, limit), 50)

    try:
        # SQL LIKE query (case-insensitive via UPPER)
        # Escape single quotes in query
        safe_query = query.replace("'", "''")
        where_clause = f"UPPER({name_field}) LIKE UPPER('%{safe_query}%')"

        result = await _fetch_from_ons_api(
            service_name=service_name,
            where_clause=where_clause,
            out_fields=f"{code_field},{name_field}",
            return_geometry=False,
            result_record_count=limit,
        )

        # Extract results
        results = []
        for feature in result.get("features", []):
            props = feature.get("properties", {})
            results.append(
                {
                    "code": props.get(code_field),
                    "name": props.get(name_field),
                    "level": level,
                }
            )

        return json.dumps(
            {
                "query": query,
                "level": level,
                "level_name": config["name"],
                "count": len(results),
                "results": results,
            }
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        return json.dumps(
            build_error_envelope(
                tool="search_geographic_areas",
                code=ErrorCode.UPSTREAM_ERROR,
                message=str(e),
                details={"query": query, "level": level},
            )
        )


# ============================================================================
# Helper to get available levels (useful for documentation/discovery)
# ============================================================================


def get_available_levels() -> Dict[str, Dict[str, str]]:
    """Return the available geographic levels configuration."""
    return GEOGRAPHIC_LEVELS
