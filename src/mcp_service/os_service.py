import json
import asyncio
import functools

from typing import Optional, List, Dict, Any, Union
from api_service.protocols import APIClient
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
        self.create_workflow_plan = self.mcp.tool()(apply_middleware(self.create_workflow_plan))
        self.hello_world = self.mcp.tool()(apply_middleware(self.hello_world))
        self.check_api_key = self.mcp.tool()(apply_middleware(self.check_api_key))
        self.list_collections = self.mcp.tool()(apply_middleware(self.list_collections))
        self.get_collection_info = self.mcp.tool()(apply_middleware(self.get_collection_info))
        self.get_collection_queryables = self.mcp.tool()(apply_middleware(self.get_collection_queryables))
        self.search_features = self.mcp.tool()(apply_middleware(self.search_features))
        self.get_feature = self.mcp.tool()(apply_middleware(self.get_feature))
        self.get_linked_identifiers = self.mcp.tool()(apply_middleware(self.get_linked_identifiers))
        self.get_bulk_features = self.mcp.tool()(apply_middleware(self.get_bulk_features))
        self.get_bulk_linked_features = self.mcp.tool()(apply_middleware(self.get_bulk_linked_features))
        self.get_prompt_templates = self.mcp.tool()(apply_middleware(self.get_prompt_templates))

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

    async def create_workflow_plan(self) -> str:
        """
        Get OpenAPI specification and collections information to help plan your approach.
        Call this FIRST before making any other tool calls.
        """
        try:
            if self.workflow_planner is None:
                cached_spec = await self.api_client.cache_openapi_spec()
                cached_collections = await self.api_client.cache_collections()
                
                collections_info = {}
                if cached_collections and hasattr(cached_collections, 'collections'):
                    collections_list = getattr(cached_collections, 'collections', [])
                    if collections_list and hasattr(collections_list, '__iter__'):
                        for collection in collections_list:
                            collections_info[collection.id] = {
                                "id": collection.id,
                                "title": collection.title,
                                "description": collection.description,
                            }
            
                self.workflow_planner = WorkflowPlanner(cached_spec, collections_info)
                logger.info("Workflow planner initialized for context provision")
        
            context = self.workflow_planner.get_context()
        
            return json.dumps({
                "instruction": "Use this information to plan your approach. Follow these steps: 1) Select appropriate collection(s), 2) Get collection queryables, 3) Execute your query with proper parameters",
                "available_collections": context["available_collections"],
                "openapi_endpoints": context["openapi_endpoints"],
                "guidance": "Start by identifying the most relevant collection for the user's request, then query its queryables to understand available parameters, then execute the appropriate search."
            })
        
        except Exception as e:
            logger.error(f"Error getting workflow context: {e}")
            return json.dumps({"error": str(e), "instruction": "Proceed with available tools"})

    def _require_workflow_context(self, func):
        """Middleware to ensure workflow context is provided before any tool execution"""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if func.__name__ == 'create_workflow_plan':
                return await func(*args, **kwargs)
                
            if self.workflow_planner is None:
                logger.info(f"Auto-calling create_workflow_plan before {func.__name__}")
                context_result = await self.create_workflow_plan()
                
                tool_result = await func(*args, **kwargs)
                
                try:
                    context_data = json.loads(context_result)
                    tool_data = json.loads(tool_result) if isinstance(tool_result, str) else tool_result
                    
                    combined_result = {
                        "workflow_context": context_data,
                        "tool_result": tool_data,
                        "message": "Workflow context was automatically provided before tool execution"
                    }
                    return json.dumps(combined_result)
                except Exception as e:
                    logger.error(f"Error combining workflow context and tool result: {e}")
                    raise ValueError(f"Error combining workflow context and tool result: {e}")
            else:
                return await func(*args, **kwargs)
        return wrapper

    async def hello_world(self, name: str) -> str:
        """Simple hello world tool for testing"""
        return f"Hello, {name}! 👋"

    async def check_api_key(self) -> str:
        """Check if the OS API key is available."""
        try:
            await self.api_client.get_api_key()
            return "OS_API_KEY is set!"
        except ValueError as e:
            return str(e)

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
        query_attr: Optional[str] = None,
        query_attr_value: Optional[str] = None,
    ) -> str:
        """
        Search for features in a collection with simplified parameters.
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
