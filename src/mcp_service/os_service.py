import json
import asyncio

from typing import Optional, List, Dict, Any, Union
from api_service.protocols import APIClient
from .protocols import MCPService, FeatureService
from .guardrails import ToolGuardrails
from utils.logging_config import get_logger

logger = get_logger(__name__)


class OSDataHubService(FeatureService):
    """Implementation of the OS NGD API service with MCP"""

    def __init__(
        self, api_client: APIClient, mcp_service: MCPService, stdio_middleware=None
    ):
        """
        Initialise the OS NGD service

        Args:
            api_client: API client implementation
            mcp_service: MCP service implementation
            stdio_middleware: Optional STDIO middleware for rate limiting
        """
        self.api_client = api_client
        self.mcp = mcp_service
        self.stdio_middleware = stdio_middleware

        self.guardrails = ToolGuardrails()

        self.register_tools()

    async def _ensure_openapi_cached(self):
        """Ensure OpenAPI spec gets cached exactly once"""
        if not hasattr(self, "_openapi_cached"):
            self._openapi_cached = True
            try:
                logger.info("Caching OpenAPI spec for LLM context...")
                await self.api_client.cache_openapi_spec()
                logger.info(
                    "OpenAPI spec cached successfully - LLM now has full API context"
                )
            except Exception as e:
                logger.warning(f"Failed to cache OpenAPI spec: {e}")
                logger.info("OpenAPI spec will be fetched on-demand when requested")

    def register_tools(self) -> None:
        """Register all MCP tools with guardrails and STDIO middleware"""

        def apply_middleware(func):
            """Apply both guardrails and STDIO middleware if available"""
            wrapped = self.guardrails.basic_guardrails(func)

            if self.stdio_middleware:
                wrapped = self.stdio_middleware.require_auth_and_rate_limit(wrapped)

            return wrapped

        self.hello_world = self.mcp.tool()(apply_middleware(self.hello_world))
        self.check_api_key = self.mcp.tool()(apply_middleware(self.check_api_key))
        self.get_api_specification = self.mcp.tool()(
            apply_middleware(self.get_api_specification)
        )
        self.list_collections = self.mcp.tool()(apply_middleware(self.list_collections))
        self.get_collection_info = self.mcp.tool()(
            apply_middleware(self.get_collection_info)
        )
        self.get_collection_queryables = self.mcp.tool()(
            apply_middleware(self.get_collection_queryables)
        )
        self.search_features = self.mcp.tool()(apply_middleware(self.search_features))
        self.get_feature = self.mcp.tool()(apply_middleware(self.get_feature))
        self.get_linked_identifiers = self.mcp.tool()(
            apply_middleware(self.get_linked_identifiers)
        )
        self.get_bulk_features = self.mcp.tool()(
            apply_middleware(self.get_bulk_features)
        )
        self.get_bulk_linked_features = self.mcp.tool()(
            apply_middleware(self.get_bulk_linked_features)
        )
        self.get_prompt_templates = self.mcp.tool()(
            apply_middleware(self.get_prompt_templates)
        )

    async def hello_world(self, name: str) -> str:
        """Simple hello world tool for testing"""
        await self._ensure_openapi_cached()
        return f"Hello, {name}! 👋"

    def check_api_key(self) -> str:
        """Check if the OS API key is available."""
        try:
            self.api_client.get_api_key()
            return "OS_API_KEY is set!"
        except ValueError as e:
            return str(e)

    async def get_api_specification(self) -> str:
        """
        Get the cached OpenAPI specification for the OS NGD API.
        This provides the LLM with comprehensive context about available endpoints,
        parameters, and data schemas.

        Returns:
            JSON string with the complete OpenAPI specification
        """
        await self._ensure_openapi_cached()
        try:
            cached_spec = self.api_client.get_cached_openapi_spec()

            if cached_spec is None:
                # If not cached yet, try to cache it now
                logger.info("OpenAPI spec not cached yet, fetching now...")
                cached_spec = await self.api_client.cache_openapi_spec()

            return json.dumps(cached_spec)
        except Exception as e:
            logger.error(f"Error getting API specification: {e}")
            return json.dumps(
                {"error": "Failed to retrieve API specification", "message": str(e)}
            )

    async def list_collections(
        self,
    ) -> str:
        """
        List all available feature collections in the OS NGD API.

        Returns:
            JSON string with collection info (id, title only)
        """
        await self._ensure_openapi_cached()
        try:
            data = await self.api_client.make_request("COLLECTIONS")

            if not data or "collections" not in data:
                return json.dumps({"error": "No collections found"})

            collections = [
                {"id": col.get("id"), "title": col.get("title")}
                for col in data.get("collections", [])
            ]

            return json.dumps({"collections": collections})
        except Exception as e:
            logger.error("Error listing collections")
            return json.dumps({"error": str(e)})

    async def get_collection_info(
        self,
        collection_id: str,
    ) -> str:
        """
        Get detailed information about a specific collection.

        Args:
            collection_id: The collection ID

        Returns:
            JSON string with collection information
        """
        await self._ensure_openapi_cached()
        try:
            data = await self.api_client.make_request(
                "COLLECTION_INFO", path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_collection_queryables(
        self,
        collection_id: str,
    ) -> str:
        """
        Get the list of queryable properties for a collection.

        Args:
            collection_id: The collection ID

        Returns:
            JSON string with queryable properties
        """
        await self._ensure_openapi_cached()
        try:
            data = await self.api_client.make_request(
                "COLLECTION_QUERYABLES", path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def search_features(
        self,
        collection_id: str,
        bbox: Optional[str] = None,
        crs: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        query_attr: Optional[str] = None,
        query_attr_value: Optional[str] = None,
    ) -> str:
        """
        Search for features in a collection with simplified parameters.
        """
        await self._ensure_openapi_cached()
        try:
            params: Dict[str, Union[str, int]] = {}

            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset

            if bbox:
                params["bbox"] = bbox
            if crs:
                params["crs"] = crs

            if query_attr and query_attr_value:
                params["filter"] = f"{query_attr}={query_attr_value}"

            data = await self.api_client.make_request(
                "COLLECTION_FEATURES", params=params, path_params=[collection_id]
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_feature(
        self,
        collection_id: str,
        feature_id: str,
        crs: Optional[str] = None,
    ) -> str:
        """
        Get a specific feature by ID.

        Args:
            collection_id: The collection ID
            feature_id: The feature ID
            crs: Coordinate reference system for the response

        Returns:
            JSON string with feature data
        """
        await self._ensure_openapi_cached()
        try:
            params: Dict[str, str] = {}
            if crs:
                params["crs"] = crs

            data = await self.api_client.make_request(
                "COLLECTION_FEATURE_BY_ID",
                params=params,
                path_params=[collection_id, feature_id],
            )

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": f"Error getting feature: {str(e)}"})

    async def get_linked_identifiers(
        self,
        identifier_type: str,
        identifier: str,
        feature_type: Optional[str] = None,
    ) -> str:
        """
        Get linked identifiers for a specified identifier.

        Args:
            identifier_type: The type of identifier (e.g., 'TOID', 'UPRN')
            identifier: The identifier value
            feature_type: Optional feature type to filter results

        Returns:
            JSON string with linked identifiers or filtered results
        """
        await self._ensure_openapi_cached()
        try:
            data = await self.api_client.make_request(
                "LINKED_IDENTIFIERS", path_params=[identifier_type, identifier]
            )

            if feature_type:
                # Filter results by feature type
                filtered_results = []
                for item in data.get("results", []):
                    if item.get("featureType") == feature_type:
                        filtered_results.append(item)
                return json.dumps({"results": filtered_results})

            return json.dumps(data)
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_bulk_features(
        self,
        collection_id: str,
        identifiers: List[str],
        query_by_attr: Optional[str] = None,
    ) -> str:
        """
        Get multiple features in a single call.

        Args:
            collection_id: The collection ID
            identifiers: List of feature identifiers
            query_by_attr: Attribute to query by (if not provided, assumes feature IDs)

        Returns:
            JSON string with features data
        """
        await self._ensure_openapi_cached()
        try:
            tasks: List[Any] = []
            for identifier in identifiers:
                if query_by_attr:
                    # Query by specific attribute
                    task = self.search_features(
                        collection_id=collection_id,
                        query_attr=query_by_attr,
                        query_attr_value=identifier,
                        limit=1,
                    )
                else:
                    # Query by feature ID
                    task = self.get_feature(collection_id, identifier)

                tasks.append(task)

            results = await asyncio.gather(*tasks)

            parsed_results = [json.loads(result) for result in results]

            return json.dumps({"results": parsed_results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    async def get_bulk_linked_features(
        self,
        identifier_type: str,
        identifiers: List[str],
        feature_type: Optional[str] = None,
    ) -> str:
        """
        Get linked features for multiple identifiers in a single call.

        Args:
            identifier_type: The type of identifier (e.g., 'TOID', 'UPRN')
            identifiers: List of identifier values
            feature_type: Optional feature type to filter results

        Returns:
            JSON string with linked features data
        """
        await self._ensure_openapi_cached()
        try:
            tasks = [
                self.get_linked_identifiers(identifier_type, identifier, feature_type)
                for identifier in identifiers
            ]

            results = await asyncio.gather(*tasks)

            parsed_results = [json.loads(result) for result in results]

            return json.dumps({"results": parsed_results})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_prompt_templates(
        self,
        category: Optional[str] = None,
    ) -> str:
        """
        Get standard prompt templates for interacting with this service.

        Args:
            category: Optional category of templates to return
                     (general, collections, features, linked_identifiers)

        Returns:
            JSON string containing prompt templates
        """
        from promp_templates.prompt_templates import PROMPT_TEMPLATES

        if category and category in PROMPT_TEMPLATES:
            return json.dumps({category: PROMPT_TEMPLATES[category]})

        return json.dumps(PROMPT_TEMPLATES)

    def run(self) -> None:
        """Run the MCP service"""
        try:
            self.mcp.run()
        finally:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.api_client.close())
            except Exception as e:
                logger.error(f"Error closing API client: {e}")
                pass
