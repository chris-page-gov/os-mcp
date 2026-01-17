"""Cross-widget communication utilities for MCP-Apps

This module provides tools and utilities for sharing state and selections
between different MCP-Apps widgets (geography selector, statistics dashboard,
feature inspector, route planner).

The communication model uses a shared selection context that can be:
1. Updated by any widget
2. Queried by tools to get current selections
3. Used to initialize widgets with pre-selected data
"""

import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime

from utils.error_envelope import build_error_envelope, ErrorCode

logger = logging.getLogger(__name__)


@dataclass
class WidgetSelection:
    """Represents a selection from a widget"""
    widget_type: str  # geography, statistics, feature, route
    selection_type: str  # area, feature, point, route
    selection_id: str
    selection_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SharedContext:
    """Shared context for cross-widget communication"""
    selected_areas: List[Dict[str, Any]] = field(default_factory=list)
    selected_features: List[Dict[str, Any]] = field(default_factory=list)
    selected_datasets: List[Dict[str, Any]] = field(default_factory=list)
    route_points: List[Dict[str, Any]] = field(default_factory=list)
    active_bbox: Optional[str] = None
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# Global shared context (in-memory for this session)
_shared_context = SharedContext()


async def get_shared_context() -> str:
    """Get the current shared widget context.

    Returns the current state of shared selections across widgets,
    including selected areas, features, datasets, and route points.

    Returns:
        JSON with current shared context
    """
    return json.dumps({
        "status": "ok",
        "context": asdict(_shared_context),
        "summary": {
            "selected_areas_count": len(_shared_context.selected_areas),
            "selected_features_count": len(_shared_context.selected_features),
            "selected_datasets_count": len(_shared_context.selected_datasets),
            "route_points_count": len(_shared_context.route_points),
            "has_bbox": _shared_context.active_bbox is not None,
        }
    })


async def update_shared_context(
    context_type: str,
    action: str,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """Update the shared widget context.

    Args:
        context_type: Type of context to update:
                     - "areas": Geographic area selections
                     - "features": OS NGD feature selections
                     - "datasets": ONS dataset selections
                     - "route_points": Route planner waypoints
                     - "bbox": Active bounding box
        action: Action to perform:
               - "add": Add item to selection
               - "remove": Remove item from selection
               - "clear": Clear all items of this type
               - "set": Replace all items with provided data
        data: Data for the action (required for add/set)

    Returns:
        JSON with updated context summary

    Examples:
        # Add a selected area
        update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry", "level": "local_auth"}
        )

        # Clear all route points
        update_shared_context(context_type="route_points", action="clear")
    """
    global _shared_context

    valid_types = {"areas", "features", "datasets", "route_points", "bbox"}
    if context_type not in valid_types:
        return json.dumps(
            build_error_envelope(
                tool="update_shared_context",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid context_type. Must be one of: {', '.join(valid_types)}",
            )
        )

    valid_actions = {"add", "remove", "clear", "set"}
    if action not in valid_actions:
        return json.dumps(
            build_error_envelope(
                tool="update_shared_context",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid action. Must be one of: {', '.join(valid_actions)}",
            )
        )

    # Handle bbox separately (it's a string, not a list)
    if context_type == "bbox":
        if action == "clear":
            _shared_context.active_bbox = None
        elif action in ("add", "set"):
            if data and "bbox" in data:
                _shared_context.active_bbox = data["bbox"]
            else:
                return json.dumps(
                    build_error_envelope(
                        tool="update_shared_context",
                        code=ErrorCode.INVALID_INPUT,
                        message="data.bbox is required for bbox add/set",
                    )
                )
    else:
        # Get the appropriate list
        list_map = {
            "areas": _shared_context.selected_areas,
            "features": _shared_context.selected_features,
            "datasets": _shared_context.selected_datasets,
            "route_points": _shared_context.route_points,
        }
        target_list = list_map[context_type]

        if action == "clear":
            target_list.clear()
        elif action == "set":
            if data and "items" in data:
                target_list.clear()
                target_list.extend(data["items"])
            else:
                return json.dumps(
                    build_error_envelope(
                        tool="update_shared_context",
                        code=ErrorCode.INVALID_INPUT,
                        message="data.items is required for set action",
                    )
                )
        elif action == "add":
            if data:
                target_list.append(data)
            else:
                return json.dumps(
                    build_error_envelope(
                        tool="update_shared_context",
                        code=ErrorCode.INVALID_INPUT,
                        message="data is required for add action",
                    )
                )
        elif action == "remove":
            if data and "id" in data:
                # Remove by ID
                _id = data["id"]
                for i, item in enumerate(target_list):
                    if item.get("id") == _id or item.get("code") == _id:
                        target_list.pop(i)
                        break
            else:
                return json.dumps(
                    build_error_envelope(
                        tool="update_shared_context",
                        code=ErrorCode.INVALID_INPUT,
                        message="data.id is required for remove action",
                    )
                )

    _shared_context.last_updated = datetime.utcnow().isoformat()

    return json.dumps({
        "status": "ok",
        "action": action,
        "context_type": context_type,
        "summary": {
            "selected_areas_count": len(_shared_context.selected_areas),
            "selected_features_count": len(_shared_context.selected_features),
            "selected_datasets_count": len(_shared_context.selected_datasets),
            "route_points_count": len(_shared_context.route_points),
            "has_bbox": _shared_context.active_bbox is not None,
        },
        "last_updated": _shared_context.last_updated,
    })


async def share_selection(
    source_widget: str,
    target_widget: str,
    selection_data: Dict[str, Any],
) -> str:
    """Share a selection from one widget to another.

    This is a convenience tool for directly passing selections between widgets
    without manually updating the shared context.

    Args:
        source_widget: Widget sending the selection (geography, statistics, feature, route)
        target_widget: Widget receiving the selection
        selection_data: The selection to share

    Returns:
        JSON with configuration for the target widget to use the selection

    Examples:
        # Share area selection from geography to statistics
        share_selection(
            source_widget="geography",
            target_widget="statistics",
            selection_data={"areas": [{"code": "E08000026", "name": "Coventry"}]}
        )
    """
    valid_widgets = {"geography", "statistics", "feature", "route"}

    if source_widget not in valid_widgets:
        return json.dumps(
            build_error_envelope(
                tool="share_selection",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid source_widget. Must be one of: {', '.join(valid_widgets)}",
            )
        )

    if target_widget not in valid_widgets:
        return json.dumps(
            build_error_envelope(
                tool="share_selection",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid target_widget. Must be one of: {', '.join(valid_widgets)}",
            )
        )

    # Determine which UI resource to reference
    widget_uri_map = {
        "geography": "ui://os-ons/geography-selector",
        "statistics": "ui://os-ons/statistics-dashboard",
        "feature": "ui://os-ons/feature-inspector",
        "route": "ui://os-ons/route-planner",
    }

    # Build initialization config based on target widget
    init_config: Dict[str, Any] = {}

    if target_widget == "statistics":
        # Pass areas to statistics dashboard
        if "areas" in selection_data:
            init_config["area_codes"] = ",".join(
                a.get("code", "") for a in selection_data["areas"]
            )
    elif target_widget == "feature":
        # Pass feature ID to inspector
        if "feature_id" in selection_data:
            init_config["feature_id"] = selection_data["feature_id"]
        if "collection_id" in selection_data:
            init_config["collection_id"] = selection_data["collection_id"]
    elif target_widget == "route":
        # Pass points to route planner
        if "points" in selection_data:
            points = selection_data["points"]
            if len(points) >= 1:
                init_config["start_lat"] = points[0].get("lat")
                init_config["start_lng"] = points[0].get("lng")
            if len(points) >= 2:
                init_config["end_lat"] = points[-1].get("lat")
                init_config["end_lng"] = points[-1].get("lng")
    elif target_widget == "geography":
        # Pass bbox or center point
        if "bbox" in selection_data:
            init_config["bbox"] = selection_data["bbox"]
        if "center" in selection_data:
            init_config["initial_lat"] = selection_data["center"].get("lat")
            init_config["initial_lng"] = selection_data["center"].get("lng")

    return json.dumps({
        "status": "ok",
        "source": source_widget,
        "target": target_widget,
        "selection": selection_data,
        "init_config": init_config,
        "_meta": {
            "uiResourceUris": [widget_uri_map[target_widget]],
            "audience": ["user"],
        },
        "message": f"Selection shared from {source_widget} to {target_widget}",
    })


def reset_shared_context() -> None:
    """Reset the shared context to initial state (for testing)."""
    global _shared_context
    _shared_context = SharedContext()
