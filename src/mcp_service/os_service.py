import json
import asyncio
import functools

from typing import Optional, List, Dict, Any, Union
from api_service.protocols import APIClient
from promp_templates.prompt_templates import PROMPT_TEMPLATES
from mcp_service.protocols import MCPService, FeatureService
from mcp_service.guardrails import ToolGuardrails
from workflow_generator.workflow_planner import WorkflowPlanner
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
        self.workflow_planner: Optional[WorkflowPlanner] = None
        self.guardrails = ToolGuardrails()
        self.register_tools()

    def register_tools(self) -> None:
        """Register all MCP tools with guardrails and middleware"""

        def apply_middleware(func):
            wrapped = self.guardrails.basic_guardrails(func)
            wrapped = self._require_workflow_context(wrapped)
            if self.stdio_middleware:
                wrapped = self.stdio_middleware.require_auth_and_rate_limit(wrapped)
            return wrapped

        # Apply middleware to ALL tools
        self.get_workflow_context = self.mcp.tool()(
            apply_middleware(self.get_workflow_context)
        )
        self.hello_world = self.mcp.tool()(apply_middleware(self.hello_world))
        self.check_api_key = self.mcp.tool()(apply_middleware(self.check_api_key))
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

    def run(self) -> None:
        """Run the MCP service"""
        try:
            self.mcp.run()
        finally:
            try:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self._cleanup())
                except RuntimeError:
                    asyncio.run(self._cleanup())
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

    async def _cleanup(self):
        """Async cleanup method"""
        try:
            if hasattr(self, "api_client") and self.api_client:
                await self.api_client.close()
                logger.debug("API client closed successfully")
        except Exception as e:
            logger.error(f"Error closing API client: {e}")

    async def get_workflow_context(self) -> str:
        """Get workflow context and initialise planner if needed"""
        try:
            if self.workflow_planner is None:
                cached_spec = await self.api_client.cache_openapi_spec()
                cached_collections = await self.api_client.cache_collections()

                collections_info = {}
                if cached_collections and hasattr(cached_collections, "collections"):
                    collections_list = getattr(cached_collections, "collections", [])
                    if collections_list and hasattr(collections_list, "__iter__"):
                        for collection in collections_list:
                            try:
                                # TODO: This needs to be split into async tasks and run in parallel
                                # TODO: This also needs to be shifted into the api_client and cached like the rest of the data
                                queryables_data = await self.api_client.make_request(
                                    "COLLECTION_QUERYABLES", path_params=[collection.id]
                                )
                                
                                all_queryables = {}
                                enum_queryables = {}
                                properties = queryables_data.get("properties", {})
                                
                                for prop_name, prop_details in properties.items():
                                    prop_type = prop_details.get("type", ["string"])
                                    if isinstance(prop_type, list):
                                        main_type = prop_type[0] if prop_type else "string"
                                        is_nullable = "null" in prop_type
                                    else:
                                        main_type = prop_type
                                        is_nullable = False
                                
                                    all_queryables[prop_name] = {
                                        "type": main_type,
                                        "nullable": is_nullable,
                                        "description": prop_details.get("description", ""),
                                        "max_length": prop_details.get("maxLength"),
                                        "format": prop_details.get("format"),
                                        "pattern": prop_details.get("pattern"),
                                        "minimum": prop_details.get("minimum"),
                                        "maximum": prop_details.get("maximum"),
                                        "is_enum": prop_details.get("enumeration", False)
                                    }
                                    
                                    if prop_details.get("enumeration") and "enum" in prop_details:
                                        enum_queryables[prop_name] = {
                                            "values": prop_details["enum"],
                                            "type": main_type,
                                            "nullable": is_nullable,
                                            "description": prop_details.get("description", ""),
                                            "max_length": prop_details.get("maxLength")
                                        }
                                        all_queryables[prop_name]["enum_values"] = prop_details["enum"]
                                    
                                    all_queryables[prop_name] = {
                                        k: v for k, v in all_queryables[prop_name].items() 
                                        if v is not None
                                    }
                                
                                collections_info[collection.id] = {
                                    "id": collection.id,
                                    "title": collection.title,
                                    "description": collection.description,
                                    "all_queryables": all_queryables,
                                    "enum_queryables": enum_queryables,
                                    "has_enum_filters": len(enum_queryables) > 0,
                                    "total_queryables": len(all_queryables),
                                    "enum_count": len(enum_queryables)
                                }
                                
                            except Exception as e:
                                logger.warning(f"Failed to fetch queryables for {collection.id}: {e}")

                                collections_info[collection.id] = {
                                    "id": collection.id,
                                    "title": collection.title,
                                    "description": collection.description,
                                    "all_queryables": {},
                                    "enum_queryables": {},
                                    "has_enum_filters": False,
                                    "total_queryables": 0,
                                    "enum_count": 0
                                }

                self.workflow_planner = WorkflowPlanner(cached_spec, collections_info)

            context = self.workflow_planner.get_context()
            return json.dumps(
                {
                    "MANDATORY_PLANNING_REQUIREMENT": {
                        "CRITICAL": "You MUST explain your complete plan to the user BEFORE making any tool calls",
                        "required_explanation": {
                            "1": "Which collection you will use and why",
                            "2": "What specific filters you will apply (show the exact filter string)",
                            "3": "What steps you will take"
                        },
                        "workflow_enforcement": "Do not proceed with tool calls until you have clearly explained your plan to the user",
                        "example_planning": "I will search the 'lus-fts-site-1' collection using the filter 'oslandusetertiarygroup = \"Cinema\"' to find all cinema locations in your specified area."
                    },

                    "available_collections": context["available_collections"],
                    "openapi_endpoints": context["openapi_endpoints"],

                    "QUICK_FILTERING_GUIDE": {
                        "primary_tool": "search_features",
                        "key_parameter": "filter",
                        "enum_fields": "Use exact values from collection's enum_queryables (e.g., 'Cinema', 'A Road')",
                        "simple_fields": "Use direct values (e.g., usrn = 12345678)",
                    },

                    "COMMON_EXAMPLES": {
                        "cinema_search": "search_features(collection_id='lus-fts-site-1', bbox='...', filter=\"oslandusetertiarygroup = 'Cinema'\")",
                        "a_road_search": "search_features(collection_id='trn-ntwk-street-1', bbox='...', filter=\"roadclassification = 'A Road'\")",
                        "usrn_search": "search_features(collection_id='trn-ntwk-street-1', filter='usrn = 12345678')",
                        "street_name": "search_features(collection_id='trn-ntwk-street-1', filter=\"designatedname1_text LIKE '%high%'\")"
                    },

                    "CRITICAL_RULES": {
                        "1": "ALWAYS explain your plan first",
                        "2": "Use exact enum values from the specific collection's enum_queryables",
                        "3": "Use the 'filter' parameter for all filtering",
                        "4": "Quote string values in single quotes"
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error getting workflow context: {e}")
            return json.dumps(
                {"error": str(e), "instruction": "Proceed with available tools"}
            )

    def _require_workflow_context(self, func):
        """Middleware to ensure workflow context is provided before any tool execution"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Only allow get_workflow_context when workflow_planner is None
            if self.workflow_planner is None:
                if func.__name__ == "get_workflow_context":
                    return await func(*args, **kwargs)
                else:
                    return json.dumps({
                        "error": "WORKFLOW CONTEXT REQUIRED",
                        "blocked_tool": func.__name__,
                        "required_action": "You must call 'get_workflow_context' first",
                        "message": "No tools are available until you get the workflow context. Please call get_workflow_context() now."
                    })
            return await func(*args, **kwargs)

        return wrapper

    async def hello_world(self, name: str) -> str:
        """Simple hello world tool for testing"""
        return f"Hello, {name}! 👋"

    async def check_api_key(self) -> str:
        """Check if the OS API key is available."""
        try:
            await self.api_client.get_api_key()
            return json.dumps({"status": "success", "message": "OS_API_KEY is set!"})
        except ValueError as e:
            return json.dumps({"status": "error", "message": str(e)})

    async def list_collections(
        self,
    ) -> str:
        """
        List all available feature collections in the OS NGD API.

        Returns:
            JSON string with collection info (id, title only)
        """
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
        filter: Optional[str] = None,
        filter_lang: Optional[str] = "cql-text",
        # Keep legacy parameters for backward compatibility
        # TODO: Remove these parameters in future? 
        query_attr: Optional[str] = None,
        query_attr_value: Optional[str] = None,
    ) -> str:
        """
        Search for features in a collection with full CQL2 filter support.
        
        Args:
            collection_id: The collection ID to search in
            bbox: Bounding box as "min_lon,min_lat,max_lon,max_lat"
            crs: Coordinate reference system for the response
            limit: Maximum number of features to return (default: 10)
            offset: Number of features to skip (default: 0)
            filter: CQL2 filter expression (e.g., "oslandusetiera = 'Cinema'" or "roadclassification = 'A Road'")
            filter_lang: Filter language, defaults to "cql-text"
            query_attr: [DEPRECATED] Legacy simple attribute name for filtering
            query_attr_value: [DEPRECATED] Legacy simple attribute value for filtering
        
        Returns:
            JSON string with feature collection data
            
        Examples:
            # Using enum values from workflow context
            search_features("lus-fts-site-1", bbox="...", filter="oslandusetiera = 'Cinema'")
            search_features("trn-ntwk-street-1", bbox="...", filter="roadclassification = 'A Road'")
            
            # Complex filters
            search_features("trn-ntwk-street-1", filter="roadclassification = 'A Road' AND operationalstate = 'Open'")
            
            # Text matching
            search_features("trn-ntwk-street-1", filter="designatedname1_text LIKE '%high%'")
        """
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

            # Handle CQL filter (preferred method)
            if filter:
                params["filter"] = filter
                if filter_lang:
                    params["filter-lang"] = filter_lang
            # Legacy support for simple query_attr/query_attr_value
            # TODO: Remove these parameters in future? 
            elif query_attr and query_attr_value:
                params["filter"] = f"{query_attr} = '{query_attr_value}'"
                if filter_lang:
                    params["filter-lang"] = filter_lang

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
        try:
            tasks: List[Any] = []
            for identifier in identifiers:
                if query_by_attr:
                    task = self.search_features(
                        collection_id=collection_id,
                        query_attr=query_by_attr,
                        query_attr_value=identifier,
                        limit=1,
                    )
                else:
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

    async def get_prompt_templates(
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
        if category and category in PROMPT_TEMPLATES:
            return json.dumps({category: PROMPT_TEMPLATES[category]})

        return json.dumps(PROMPT_TEMPLATES)
