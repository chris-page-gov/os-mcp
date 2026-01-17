"""Feature Inspector tools with MCP-Apps UI support

This module provides tools for inspecting OS NGD feature details with
interactive visualization through the feature inspector widget.

Tools in this module:
- inspect_feature: Opens interactive widget for feature inspection
- get_feature_with_linked: Gets feature details with linked identifiers
"""

import json
import logging
from typing import Dict, Any, Optional, List

from utils.error_envelope import build_error_envelope, ErrorCode

logger = logging.getLogger(__name__)


async def inspect_feature(
    feature_id: str,
    collection_id: str,
    include_linked: bool = True,
    include_geometry: bool = True,
) -> str:
    """Opens interactive feature inspector widget for OS NGD feature.

    This tool triggers a visual interface where users can:
    - View all feature properties in a formatted table
    - Navigate linked identifiers (TOID, UPRN, USRN)
    - Visualize feature geometry on a map
    - Export data as JSON or CSV

    Args:
        feature_id: The feature ID (e.g., TOID)
        collection_id: The OS NGD collection ID (e.g., "bld-fts-building-1")
        include_linked: Fetch linked identifiers (default: True)
        include_geometry: Include geometry in response (default: True)

    Returns:
        JSON with widget configuration and UI resource reference.
        The host will render the feature inspector widget.

    Examples:
        # Inspect a building feature
        inspect_feature(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1"
        )

        # Inspect without linked identifiers (faster)
        inspect_feature(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1",
            include_linked=False
        )
    """
    # Validate inputs
    if not feature_id or not feature_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="inspect_feature",
                code=ErrorCode.INVALID_INPUT,
                message="feature_id is required",
            )
        )

    if not collection_id or not collection_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="inspect_feature",
                code=ErrorCode.INVALID_INPUT,
                message="collection_id is required",
            )
        )

    config = {
        "feature_id": feature_id.strip(),
        "collection_id": collection_id.strip(),
        "options": {
            "include_linked": include_linked,
            "include_geometry": include_geometry,
            "show_map": include_geometry,
            "enable_navigation": True,
            "enable_export": True,
        },
    }

    return json.dumps(
        {
            "status": "loading",
            "config": config,
            "instructions": (
                f"Opening Feature Inspector for {feature_id} from {collection_id}. "
                "The widget will display feature properties, linked identifiers, "
                "and a map visualization. You can export the data or navigate to "
                "related features from within the widget."
            ),
            "_meta": {
                "uiResourceUris": ["ui://os-ons/feature-inspector"],
                "audience": ["user"],
            },
        }
    )


async def get_feature_with_linked(
    feature_id: str,
    collection_id: str,
    identifier_type: str = "TOID",
    include_geometry: bool = True,
) -> str:
    """Get feature details with linked identifiers for the feature inspector.

    This is a data preparation tool that fetches feature data along with
    its linked identifiers in a format ready for the feature inspector widget.

    Args:
        feature_id: The feature ID
        collection_id: The OS NGD collection ID
        identifier_type: Type of identifier (TOID, UPRN, USRN - default: TOID)
        include_geometry: Include geometry in response (default: True)

    Returns:
        JSON with feature data, properties, and linked identifiers.
        Suitable for direct consumption by the feature inspector widget.

    Note:
        This tool prepares data but does not render the widget.
        Use inspect_feature to trigger the visual interface.
    """
    # Validate inputs
    if not feature_id or not feature_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="get_feature_with_linked",
                code=ErrorCode.INVALID_INPUT,
                message="feature_id is required",
            )
        )

    if not collection_id or not collection_id.strip():
        return json.dumps(
            build_error_envelope(
                tool="get_feature_with_linked",
                code=ErrorCode.INVALID_INPUT,
                message="collection_id is required",
            )
        )

    valid_types = {"TOID", "UPRN", "USRN"}
    if identifier_type.upper() not in valid_types:
        return json.dumps(
            build_error_envelope(
                tool="get_feature_with_linked",
                code=ErrorCode.INVALID_INPUT,
                message=f"Invalid identifier_type. Must be one of: {', '.join(valid_types)}",
            )
        )

    # Return configuration for fetching
    # The actual API calls will be made by the service layer
    return json.dumps(
        {
            "status": "pending",
            "request": {
                "feature_id": feature_id.strip(),
                "collection_id": collection_id.strip(),
                "identifier_type": identifier_type.upper(),
                "include_geometry": include_geometry,
            },
            "message": (
                f"Ready to fetch feature {feature_id} from {collection_id} "
                f"with linked identifiers via {identifier_type}"
            ),
        }
    )


# ============================================================================
# Linked Identifiers Helper Functions
# ============================================================================


def format_linked_identifiers(
    raw_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Format linked identifiers for the feature inspector widget.

    Takes raw API response and normalizes it for consistent widget display.

    Args:
        raw_results: List of linked identifier records from API

    Returns:
        List of formatted identifier objects with standardized keys:
        - identifierType: The type (TOID, UPRN, USRN, etc.)
        - identifier: The identifier value
        - featureType: The type of feature this links to
        - collection: The collection containing the linked feature (if known)
    """
    formatted = []

    for item in raw_results:
        if not isinstance(item, dict):
            continue

        formatted_item = {
            "identifierType": (
                item.get("identifierType")
                or item.get("type")
                or item.get("identifier_type")
                or "Unknown"
            ),
            "identifier": (
                item.get("identifier")
                or item.get("value")
                or item.get("id")
                or "N/A"
            ),
            "featureType": (
                item.get("featureType")
                or item.get("feature_type")
                or item.get("collection")
                or None
            ),
        }

        # Add version date if present
        if item.get("versiondate") or item.get("version_date"):
            formatted_item["versionDate"] = (
                item.get("versiondate") or item.get("version_date")
            )

        formatted.append(formatted_item)

    return formatted


def group_linked_by_type(
    linked_identifiers: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """Group linked identifiers by their type.

    Args:
        linked_identifiers: List of formatted identifier objects

    Returns:
        Dictionary mapping identifier types to lists of identifiers
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for item in linked_identifiers:
        id_type = item.get("identifierType", "Unknown").upper()
        if id_type not in grouped:
            grouped[id_type] = []
        grouped[id_type].append(item)

    return grouped


def summarize_linked_identifiers(
    linked_identifiers: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Create a summary of linked identifiers.

    Args:
        linked_identifiers: List of formatted identifier objects

    Returns:
        Summary with counts by type and total
    """
    grouped = group_linked_by_type(linked_identifiers)

    return {
        "total": len(linked_identifiers),
        "by_type": {id_type: len(items) for id_type, items in grouped.items()},
        "types": list(grouped.keys()),
    }
