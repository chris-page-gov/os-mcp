"""MCP-Apps UI Resources for OS/ONS Geographic Data

This module handles registration of interactive UI widgets that provide
visual interfaces for geographic selection and data visualization.

UI resources use the 'ui://' URI scheme and are rendered in sandboxed
iframes by MCP hosts that support the MCP-Apps extension.
"""

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Base directory for UI widget HTML files
UI_DIR = Path(__file__).parent.parent / "ui"


class OSUIResources:
    """Handles registration of MCP-Apps UI resources (interactive widgets)"""

    def __init__(self, mcp_service: Any) -> None:
        self.mcp = mcp_service

    def register_all(self) -> None:
        """Register all UI resources"""
        self._register_geography_selector()
        self._register_statistics_dashboard()
        self._register_feature_inspector()
        logger.info("UI resources registration complete")

    def _load_widget_html(self, filename: str) -> Optional[str]:
        """Load UI widget HTML file from disk.

        Args:
            filename: Name of HTML file (e.g., 'geography_selector.html')

        Returns:
            HTML content as string, or None if file not found
        """
        filepath = UI_DIR / filename
        if not filepath.exists():
            logger.warning(f"UI widget file not found: {filepath}")
            return None

        try:
            return filepath.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"Error reading UI widget {filename}: {e}")
            return None

    def _register_geography_selector(self) -> None:
        """Register the geography selector widget"""

        @self.mcp.resource(
            "ui://os-ons/geography-selector",
            name="Geographic Area Selector",
            description=(
                "Interactive map widget for selecting UK geographic areas at various "
                "administrative levels (Parliamentary Constituencies, Local Authorities, "
                "Wards, Output Areas, etc.). Features hierarchical selection, search by "
                "name or postcode, and visual boundary display."
            ),
            mime_type="text/html",
        )
        async def geography_selector() -> str:
            content = self._load_widget_html("geography_selector.html")
            if content is None:
                return self._placeholder_widget(
                    "Geography Selector",
                    "Widget file not found. Create src/ui/geography_selector.html",
                )
            return content

        logger.info("Registered: ui://os-ons/geography-selector")

    def _register_statistics_dashboard(self) -> None:
        """Register the statistics dashboard widget"""

        @self.mcp.resource(
            "ui://os-ons/statistics-dashboard",
            name="Statistics Dashboard",
            description=(
                "Interactive dashboard for visualizing ONS statistics across selected "
                "geographic areas. Features multiple chart types, comparative analysis, "
                "filtering, and data export capabilities."
            ),
            mime_type="text/html",
        )
        async def statistics_dashboard() -> str:
            content = self._load_widget_html("statistics_dashboard.html")
            if content is None:
                return self._placeholder_widget(
                    "Statistics Dashboard",
                    "Widget file not found. Create src/ui/statistics_dashboard.html",
                )
            return content

        logger.info("Registered: ui://os-ons/statistics-dashboard")

    def _register_feature_inspector(self) -> None:
        """Register the feature inspector widget"""

        @self.mcp.resource(
            "ui://os-ons/feature-inspector",
            name="Feature Inspector",
            description=(
                "Detailed view of OS NGD features with properties, linked identifiers, "
                "and spatial relationships. Includes navigation between linked features "
                "and export functionality."
            ),
            mime_type="text/html",
        )
        async def feature_inspector() -> str:
            content = self._load_widget_html("feature_inspector.html")
            if content is None:
                return self._placeholder_widget(
                    "Feature Inspector",
                    "Widget file not found. Create src/ui/feature_inspector.html",
                )
            return content

        logger.info("Registered: ui://os-ons/feature-inspector")

    def _placeholder_widget(self, title: str, message: str) -> str:
        """Generate a placeholder HTML widget when the actual file is missing"""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Placeholder</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: #f5f5f5;
        }}
        .placeholder {{
            text-align: center;
            padding: 2rem;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; font-size: 1.5rem; }}
        p {{ color: #666; }}
    </style>
</head>
<body>
    <div class="placeholder">
        <h1>{title}</h1>
        <p>{message}</p>
    </div>
</body>
</html>"""
