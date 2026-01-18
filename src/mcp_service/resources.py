"""MCP Resources for OS NGD documentation"""

import json
import time
from pathlib import Path
from models import NGDAPIEndpoint
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Path to SKILL.md from project root
SKILL_MD_PATH = Path(__file__).parent.parent.parent / "SKILL.md"


# TODO: Do this for
class OSDocumentationResources:
    """Handles registration of OS NGD documentation resources"""

    def __init__(self, mcp_service, api_client):
        self.mcp = mcp_service
        self.api_client = api_client

    def register_all(self) -> None:
        """Register all documentation resources"""
        self._register_skills_resource()
        self._register_transport_network_resources()
        # Future: self._register_land_resources()
        # Future: self._register_building_resources()

    def _register_skills_resource(self) -> None:
        """Register SKILL.md as an MCP resource for client guidance.

        IMPORTANT: Clients should read this resource to understand how to use the server.
        It explains to call route_query FIRST for any natural language query.
        """

        @self.mcp.resource("skills://os-ons/getting-started")
        async def skills_guide() -> str:
            """Server usage guide - READ THIS FIRST.

            Contains critical guidance:
            - Call route_query FIRST for any query
            - When to use ONS Geography vs OS NGD
            - Tool selection decision tables
            - Common workflow patterns
            """
            try:
                if SKILL_MD_PATH.exists():
                    content = SKILL_MD_PATH.read_text(encoding="utf-8")
                    return json.dumps({
                        "resource": "skills://os-ons/getting-started",
                        "content": content,
                        "content_type": "markdown",
                        "description": "Server usage guide - explains how to use route_query and select the right tools",
                        "priority": "READ_FIRST",
                    })
                else:
                    return json.dumps({
                        "error": "SKILL.md not found",
                        "expected_path": str(SKILL_MD_PATH),
                    })
            except Exception as e:
                logger.error(f"Error reading SKILL.md: {e}")
                return json.dumps({"error": str(e)})

    def _register_transport_network_resources(self) -> None:
        """Register transport network documentation resources"""

        @self.mcp.resource("os-docs://street")
        async def street_docs() -> str:
            return await self._fetch_doc_resource(
                "street", NGDAPIEndpoint.MARKDOWN_STREET.value
            )

        @self.mcp.resource("os-docs://road")
        async def road_docs() -> str:
            return await self._fetch_doc_resource(
                "road", NGDAPIEndpoint.MARKDOWN_ROAD.value
            )

        @self.mcp.resource("os-docs://tram-on-road")
        async def tram_on_road_docs() -> str:
            return await self._fetch_doc_resource(
                "tram-on-road", NGDAPIEndpoint.TRAM_ON_ROAD.value
            )

        @self.mcp.resource("os-docs://road-node")
        async def road_node_docs() -> str:
            return await self._fetch_doc_resource(
                "road-node", NGDAPIEndpoint.ROAD_NODE.value
            )

        @self.mcp.resource("os-docs://road-link")
        async def road_link_docs() -> str:
            return await self._fetch_doc_resource(
                "road-link", NGDAPIEndpoint.ROAD_LINK.value
            )

        @self.mcp.resource("os-docs://road-junction")
        async def road_junction_docs() -> str:
            return await self._fetch_doc_resource(
                "road-junction", NGDAPIEndpoint.ROAD_JUNCTION.value
            )

    async def _fetch_doc_resource(self, feature_type: str, url: str) -> str:
        """Generic method to fetch documentation resources"""
        try:
            content = await self.api_client.make_request_no_auth(url)

            return json.dumps(
                {
                    "feature_type": feature_type,
                    "content": content,
                    "content_type": "markdown",
                    "source_url": url,
                    "timestamp": time.time(),
                }
            )

        except Exception as e:
            logger.error(f"Error fetching {feature_type} documentation: {e}")
            return json.dumps({"error": str(e), "feature_type": feature_type})
