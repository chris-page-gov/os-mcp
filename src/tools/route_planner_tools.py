"""Route Planner tools with MCP-Apps UI support

This module provides tools for interactive route planning using OS road network data.

Tools in this module:
- plan_route: Opens interactive route planner widget
- get_route_network: Gets road network data for a bounding box
"""

import json
import logging
from typing import Dict, Any, Optional, List

from utils.error_envelope import build_error_envelope, ErrorCode

logger = logging.getLogger(__name__)


async def plan_route(
    start_lat: Optional[float] = None,
    start_lng: Optional[float] = None,
    end_lat: Optional[float] = None,
    end_lng: Optional[float] = None,
    bbox: Optional[str] = None,
    show_network: bool = True,
) -> str:
    """Opens interactive route planner widget.

    This tool triggers a visual interface where users can:
    - Click on the map to set start/end points
    - Add waypoints for multi-stop routes
    - View the road network
    - Get turn-by-turn directions

    Args:
        start_lat: Optional starting latitude
        start_lng: Optional starting longitude
        end_lat: Optional ending latitude
        end_lng: Optional ending longitude
        bbox: Optional bounding box to focus on ("west,south,east,north")
        show_network: Whether to display the road network (default: True)

    Returns:
        JSON with widget configuration and UI resource reference.
        The host will render the route planner widget.

    Examples:
        # Open route planner with no preset points
        plan_route()

        # Open with preset start and end
        plan_route(
            start_lat=52.4081, start_lng=-1.5106,
            end_lat=52.4862, end_lng=-1.8904
        )

        # Focus on a specific area
        plan_route(bbox="-2.0,52.3,-1.5,52.6")
    """
    config: Dict[str, Any] = {
        "show_network": show_network,
        "features": {
            "waypoints_enabled": True,
            "directions_enabled": True,
            "export_enabled": True,
        },
    }

    # Add start point if provided
    if start_lat is not None and start_lng is not None:
        config["start"] = {"lat": start_lat, "lng": start_lng}

    # Add end point if provided
    if end_lat is not None and end_lng is not None:
        config["end"] = {"lat": end_lat, "lng": end_lng}

    # Add bounding box if provided
    if bbox:
        config["bbox"] = bbox

    # Default center if no points provided
    if "start" not in config and "bbox" not in config:
        config["center"] = {"lat": 52.4862, "lng": -1.8904}
        config["zoom"] = 10

    return json.dumps(
        {
            "status": "ready",
            "config": config,
            "instructions": (
                "Opening Route Planner widget. Click on the map to set start (green) "
                "and end (red) points, or use the input fields. Add waypoints by "
                "clicking the '+ Add Waypoint' button. Click 'Calculate Route' to "
                "find the best route and view turn-by-turn directions."
            ),
            "_meta": {
                "uiResourceUris": ["ui://os-ons/route-planner"],
                "audience": ["user"],
            },
        }
    )


async def get_route_network(
    bbox: str,
    include_restrictions: bool = True,
    limit: int = 500,
) -> str:
    """Get road network data for route planning.

    Fetches road links and nodes within a bounding box for use
    in the route planner widget or custom routing implementations.

    Args:
        bbox: Bounding box as "west,south,east,north" in WGS84
        include_restrictions: Include traffic restrictions (default: True)
        limit: Maximum road links to return (default: 500, max: 1000)

    Returns:
        JSON with network data ready for the route planner widget.

    Note:
        This tool prepares a request for the routing service.
        The actual data fetching is done by get_routing_data.
    """
    # Validate bbox
    if not bbox or not bbox.strip():
        return json.dumps(
            build_error_envelope(
                tool="get_route_network",
                code=ErrorCode.INVALID_INPUT,
                message="bbox is required (format: 'west,south,east,north')",
            )
        )

    parts = bbox.split(",")
    if len(parts) != 4:
        return json.dumps(
            build_error_envelope(
                tool="get_route_network",
                code=ErrorCode.INVALID_INPUT,
                message="bbox must have 4 values: west,south,east,north",
            )
        )

    try:
        west, south, east, north = [float(p.strip()) for p in parts]
    except ValueError:
        return json.dumps(
            build_error_envelope(
                tool="get_route_network",
                code=ErrorCode.INVALID_INPUT,
                message="bbox values must be valid numbers",
            )
        )

    # Validate coordinate ranges
    if not (-180 <= west <= 180 and -180 <= east <= 180):
        return json.dumps(
            build_error_envelope(
                tool="get_route_network",
                code=ErrorCode.INVALID_INPUT,
                message="Longitude must be between -180 and 180",
            )
        )

    if not (-90 <= south <= 90 and -90 <= north <= 90):
        return json.dumps(
            build_error_envelope(
                tool="get_route_network",
                code=ErrorCode.INVALID_INPUT,
                message="Latitude must be between -90 and 90",
            )
        )

    # Cap limit
    limit = min(max(1, limit), 1000)

    return json.dumps(
        {
            "status": "pending",
            "request": {
                "bbox": bbox,
                "include_restrictions": include_restrictions,
                "limit": limit,
            },
            "message": (
                f"Ready to fetch road network for bbox: {bbox}. "
                "Use get_routing_data to execute the request."
            ),
        }
    )


def format_route_directions(
    edges: List[Dict[str, Any]],
    include_geometry: bool = True,
) -> List[Dict[str, Any]]:
    """Format route edges into turn-by-turn directions.

    Args:
        edges: List of route edges from the routing service
        include_geometry: Include geometry for each segment

    Returns:
        List of direction objects with instruction, distance, and road name
    """
    directions = []

    for i, edge in enumerate(edges):
        instruction = "Continue"

        # Determine instruction based on position
        if i == 0:
            instruction = "Start on"
        elif i == len(edges) - 1:
            instruction = "Arrive at destination via"

        road_name = edge.get("road_name") or "unnamed road"

        direction = {
            "step": i + 1,
            "instruction": f"{instruction} {road_name}",
            "road_name": road_name,
            "distance": edge.get("cost", 0),
            "road_id": edge.get("road_id"),
        }

        if include_geometry and edge.get("geometry"):
            direction["geometry"] = edge["geometry"]

        directions.append(direction)

    return directions


def calculate_route_summary(edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate summary statistics for a route.

    Args:
        edges: List of route edges

    Returns:
        Summary with total distance, segment count, and road names
    """
    total_distance = sum(edge.get("cost", 0) for edge in edges)

    road_names = set()
    for edge in edges:
        name = edge.get("road_name")
        if name:
            road_names.add(name)

    return {
        "total_distance_meters": total_distance,
        "total_distance_km": round(total_distance / 1000, 2),
        "segment_count": len(edges),
        "unique_roads": len(road_names),
        "road_names": sorted(road_names),
    }
