import json
import asyncio
import functools
import re

from typing import Optional, List, Dict, Any, Union
from api_service.protocols import APIClient
from prompt_templates.prompt_templates import PROMPT_TEMPLATES
from mcp_service.protocols import MCPService, FeatureService
from mcp_service.guardrails import ToolGuardrails
from workflow_generator.workflow_planner import WorkflowPlanner
from utils.logging_config import get_logger
from mcp_service.resources import OSDocumentationResources
from mcp_service.prompts import OSWorkflowPrompts

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
        self.register_resources()
        self.register_prompts()

    # Register all the resources, tools, and prompts
    def register_resources(self) -> None:
        """Register all MCP resources"""
        doc_resources = OSDocumentationResources(self.mcp, self.api_client)
        doc_resources.register_all()

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

    def register_prompts(self) -> None:
        """Register all MCP prompts"""
        workflow_prompts = OSWorkflowPrompts(self.mcp)
        workflow_prompts.register_all()

    # Run the MCP service
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

    # Get the workflow context from the cached API client data
    # TODO: Lots of work to do here to reduce the size of the context and make it more readable for the LLM but not sacrificing the information
    async def get_workflow_context(self) -> str:
        """Get workflow context from cached API client data"""
        try:
            if self.workflow_planner is None:
                workflow_context = await self.api_client.cache_workflow_context()
                collections_info = {
                    coll_id: {
                        "id": coll.id,
                        "title": coll.title,
                        "all_queryables": coll.all_queryables,
                        "enum_queryables": coll.enum_queryables,
                        "has_enum_filters": coll.has_enum_filters,
                        "total_queryables": coll.total_queryables,
                        "enum_count": coll.enum_count,
                    }
                    for coll_id, coll in workflow_context.collections_info.items()
                }

                self.workflow_planner = WorkflowPlanner(
                    workflow_context.openapi_spec, collections_info
                )

            context = self.workflow_planner.get_context()
            return json.dumps(
                {
                    "CRITICAL_COLLECTION_LIST": sorted(
                        context["available_collections"].keys()
                    ),
                    "MANDATORY_PLANNING_REQUIREMENT": {
                        "CRITICAL": "You MUST explain your complete plan to the user BEFORE making any tool calls. You MUST read the available_collections queryables information correctly and use them in your plan.",
                        "required_explanation": {
                            "1": "Which collection you will use and why",
                            "2": "What specific filters you will apply (show the exact filter string)",
                            "3": "What steps you will take",
                        },
                        "workflow_enforcement": "Do not proceed with tool calls until you have clearly explained your plan to the user",
                        "example_planning": "I will search the 'lus-fts-site-1' collection using the filter 'oslandusetertiarygroup = \"Cinema\"' to find all cinema locations in your specified area.",
                    },
                    "available_collections": context["available_collections"],
                    # "openapi_spec": context["openapi_spec"].model_dump() if context["openapi_spec"] else None,
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
                        "street_name": "search_features(collection_id='trn-ntwk-street-1', filter=\"designatedname1_text LIKE '%high%'\")",
                    },
                    "CRITICAL_RULES": {
                        "1": "ALWAYS explain your plan first",
                        "2": "Use exact enum values from the specific collection's enum_queryables",
                        "3": "Use the 'filter' parameter for all filtering",
                        "4": "Quote string values in single quotes",
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error getting workflow context: {e}")
            return json.dumps(
                {"error": str(e), "instruction": "Proceed with available tools"}
            )

    def _require_workflow_context(self, func):
        # Functions that don't need workflow context
        skip_functions = {"get_workflow_context", "hello_world", "check_api_key"}

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if self.workflow_planner is None:
                if func.__name__ in skip_functions:
                    return await func(*args, **kwargs)
                else:
                    return json.dumps(
                        {
                            "error": "WORKFLOW CONTEXT REQUIRED",
                            "blocked_tool": func.__name__,
                            "required_action": "You must call 'get_workflow_context' first",
                            "message": "No tools are available until you get the workflow context. Please call get_workflow_context() now.",
                        }
                    )
            return await func(*args, **kwargs)

        return wrapper

    # TODO: This is a bit of a hack - we need to improve the error handling and retry logic
    # TODO: Could we actually spawn a seperate AI agent to handle the retry logic and return the result to the main agent?
    def _add_retry_context(self, response_data: dict, tool_name: str) -> dict:
        """Add retry guidance to tool responses"""
        if "error" in response_data:
            response_data["retry_guidance"] = {
                "tool": tool_name,
                "MANDATORY_INSTRUCTION 1": "Review the error message and try again with corrected parameters",
                "MANDATORY_INSTRUCTION 2": "YOU MUST call get_workflow_context() if you need to see available options again",
            }
        return response_data

    # All the tools
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
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "list_collections")
            )

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
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "get_collection_info")
            )

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
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "get_collection_queryables")
            )

    async def search_features(
        self,
        collection_id: str,
        bbox: Optional[str] = None,
        crs: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filter: Optional[str] = None,
        filter_lang: Optional[str] = "cql-text",
        query_attr: Optional[str] = None,
        query_attr_value: Optional[str] = None,
    ) -> str:
        """Search for features in a collection with full CQL2 filter support."""
        try:
            params: Dict[str, Union[str, int]] = {}

            if limit:
                params["limit"] = min(limit, 100)
            if offset:
                params["offset"] = max(0, offset)
            if bbox:
                params["bbox"] = bbox
            if crs:
                params["crs"] = crs
            if filter:
                if len(filter) > 1000:
                    raise ValueError("Filter too long")
                dangerous_patterns = [
                    r";\s*--",
                    r";\s*/\*",
                    r"\bUNION\b",
                    r"\bSELECT\b",
                    r"\bINSERT\b",
                    r"\bUPDATE\b",
                    r"\bDELETE\b",
                    r"\bDROP\b",
                    r"\bCREATE\b",
                    r"\bALTER\b",
                    r"\bTRUNCATE\b",
                    r"\bEXEC\b",
                    r"\bEXECUTE\b",
                    r"\bSP_\b",
                    r"\bXP_\b",
                    r"<script\b",
                    r"javascript:",
                    r"vbscript:",
                    r"onload\s*=",
                    r"onerror\s*=",
                    r"onclick\s*=",
                    r"\beval\s*\(",
                    r"document\.",
                    r"window\.",
                    r"location\.",
                    r"cookie",
                    r"innerHTML",
                    r"outerHTML",
                    r"alert\s*\(",
                    r"confirm\s*\(",
                    r"prompt\s*\(",
                    r"setTimeout\s*\(",
                    r"setInterval\s*\(",
                    r"Function\s*\(",
                    r"constructor",
                    r"prototype",
                    r"__proto__",
                    r"process\.",
                    r"require\s*\(",
                    r"import\s+",
                    r"from\s+.*import",
                    r"\.\./",
                    r"file://",
                    r"ftp://",
                    r"data:",
                    r"blob:",
                    r"\\x[0-9a-fA-F]{2}",
                    r"%[0-9a-fA-F]{2}",
                    r"&#x[0-9a-fA-F]+;",
                    r"&[a-zA-Z]+;",
                    r"\$\{",
                    r"#\{",
                    r"<%",
                    r"%>",
                    r"{{",
                    r"}}",
                    r"\\\w+",
                    r"\0",
                    r"\r\n",
                    r"\n\r",
                ]

                for pattern in dangerous_patterns:
                    if re.search(pattern, filter, re.IGNORECASE):
                        raise ValueError("Invalid filter content")

                if filter.count("'") % 2 != 0:
                    raise ValueError("Unmatched quotes in filter")

                params["filter"] = filter.strip()
                if filter_lang:
                    params["filter-lang"] = filter_lang

            elif query_attr and query_attr_value:
                if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", query_attr):
                    raise ValueError("Invalid field name")

                escaped_value = str(query_attr_value).replace("'", "''")
                params["filter"] = f"{query_attr} = '{escaped_value}'"
                if filter_lang:
                    params["filter-lang"] = filter_lang

            if self.workflow_planner:
                valid_collections = set(self.workflow_planner.collections_info.keys())
                if collection_id not in valid_collections:
                    return json.dumps(
                        {
                            "error": f"Invalid collection '{collection_id}'. Valid collections: {sorted(valid_collections)[:10]}...",
                            "suggestion": "Call get_workflow_context() to see all available collections",
                        }
                    )

            data = await self.api_client.make_request(
                "COLLECTION_FEATURES", params=params, path_params=[collection_id]
            )

            return json.dumps(data)
        except ValueError as ve:
            error_response = {"error": f"Invalid input: {str(ve)}"}
            return json.dumps(
                self._add_retry_context(error_response, "search_features")
            )
        except Exception as e:
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "search_features")
            )

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
            error_response = {"error": f"Error getting feature: {str(e)}"}
            return json.dumps(self._add_retry_context(error_response, "get_feature"))

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
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "get_linked_identifiers")
            )

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
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "get_bulk_features")
            )

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
            error_response = {"error": str(e)}
            return json.dumps(
                self._add_retry_context(error_response, "get_bulk_linked_features")
            )

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
