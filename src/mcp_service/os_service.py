from typing import Optional, List, Dict, Any, Union, Callable, Awaitable, cast
import json
import asyncio
import functools
import re

# (Local typing imports moved to header section)
from api_service.protocols import APIClient  # type: ignore[import-untyped]
from prompt_templates.prompt_templates import PROMPT_TEMPLATES  # type: ignore[import-untyped]
from mcp_service.protocols import MCPService
from mcp_service.guardrails import ToolGuardrails
from workflow_generator.workflow_planner import WorkflowPlanner
from utils.logging_config import get_logger
from utils.error_envelope import build_error_envelope, ErrorCode
from models import LinkedIdentifier
from mcp_service.resources import OSDocumentationResources
from mcp_service.prompts import OSWorkflowPrompts
from mcp_service.routing_service import OSRoutingService

logger = get_logger(__name__)


class OSDataHubService:
    """Implementation of the OS NGD API service with MCP"""

    def __init__(
        self,
        api_client: APIClient,
        mcp_service: MCPService,
        stdio_middleware: Optional[Any] = None,
    ) -> None:
        """Initialise the OS NGD service"""
        self.api_client = api_client
        self.mcp = mcp_service
        self.stdio_middleware = stdio_middleware
        self.workflow_planner: Optional[WorkflowPlanner] = None
        self.guardrails = ToolGuardrails()
        self.routing_service = OSRoutingService(api_client)
        self.register_tools()
        self.register_resources()
        self.register_prompts()

    # Register all the resources, tools, and prompts
    def register_resources(self) -> None:
        """Register all MCP resources"""
        doc_resources = OSDocumentationResources(self.mcp, self.api_client)
        doc_resources.register_all()

    def register_tools(self) -> None:
        """Register all MCP tools with guardrails and middleware without broad ignores."""

        def apply_middleware(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
            base: Callable[..., Awaitable[Any]] = self.guardrails.basic_guardrails(func)
            base = self._require_workflow_context(base)
            if self.stdio_middleware:
                base = self.stdio_middleware.require_auth_and_rate_limit(base)
            # FastMCP decorator expects an async callable signature; we trust guardrails preserves it.
            return base

        tool_names = [
            "get_workflow_context",
            "hello_world",
            "check_api_key",
            "list_collections",
            "get_single_collection",
            "get_single_collection_queryables",
            "search_features",
            "get_feature",
            "get_linked_identifiers",
            "get_bulk_features",
            "get_bulk_linked_features",
            "get_prompt_templates",
            "fetch_detailed_collections",
            "get_routing_data",
        ]
        for name in tool_names:
            original = getattr(self, name)
            wrapped = apply_middleware(original)
            tool_wrapped = self.mcp.tool()(wrapped)
            setattr(self, name, cast(Callable[..., Awaitable[Any]], tool_wrapped))

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

    async def _cleanup(self) -> None:
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
        """Get basic workflow context - no detailed queryables yet"""
        try:
            if self.workflow_planner is None:
                collections_cache = await self.api_client.cache_collections()
                basic_collections_info = {
                    coll.id: {
                        "id": coll.id,
                        "title": coll.title,
                        "description": coll.description,
                        # No queryables here - will be fetched on-demand
                    }
                    for coll in collections_cache.collections
                }

                self.workflow_planner = WorkflowPlanner(
                    await self.api_client.cache_openapi_spec(), basic_collections_info
                )

            context = self.workflow_planner.get_basic_context()
            return json.dumps(
                {
                    "CRITICAL_COLLECTION_LIST": sorted(
                        context["available_collections"].keys()
                    ),
                    "MANDATORY_PLANNING_REQUIREMENT": {
                        "CRITICAL": "You MUST follow the 2-step planning process:",
                        "step_1": "Explain your complete plan listing which specific collections you will use and why",
                        "step_2": "Call fetch_detailed_collections('collection-id-1,collection-id-2') to get queryables for those collections BEFORE making search calls",
                        "required_explanation": {
                            "1": "Which collections you will use and why",
                            "2": "What you expect to find in those collections",
                            "3": "What your search strategy will be",
                        },
                        "workflow_enforcement": "Do not proceed with search_features until you have fetched detailed queryables",
                        "example_planning": "I will use 'lus-fts-site-1' for finding cinemas. Let me fetch its detailed queryables first...",
                    },
                    "available_collections": context[
                        "available_collections"
                    ],  # Basic info only - no queryables yet - this is to reduce the size of the context for the LLM
                    "openapi_spec": context["openapi_spec"].model_dump()
                    if context["openapi_spec"]
                    else None,
                    "TWO_STEP_WORKFLOW": {
                        "step_1": "Plan with basic collection info (no detailed queryables available yet)",
                        "step_2": "Use fetch_detailed_collections() to get queryables for your chosen collections",
                        "step_3": "Execute search_features with proper filters using the fetched queryables",
                    },
                    "AVAILABLE_TOOLS": {
                        "fetch_detailed_collections": "Get detailed queryables for specific collections: fetch_detailed_collections('lus-fts-site-1,trn-ntwk-street-1')",
                        "search_features": "Search features (requires detailed queryables first)",
                    },
                    "QUICK_FILTERING_GUIDE": {
                        "primary_tool": "search_features",
                        "key_parameter": "filter",
                        "enum_fields": "Use exact values from collection's enum_queryables (fetch these first!)",
                        "simple_fields": "Use direct values (e.g., usrn = 12345678)",
                    },
                    "COMMON_EXAMPLES": {
                        "workflow_example": "1) Explain plan → 2) fetch_detailed_collections('lus-fts-site-1') → 3) search_features with proper filter",
                        "cinema_search": "After fetching queryables: search_features(collection_id='lus-fts-site-1', filter=\"oslandusetertiarygroup = 'Cinema'\")",
                    },
                    "CRITICAL_RULES": {
                        "1": "ALWAYS explain your plan first",
                        "2": "ALWAYS call fetch_detailed_collections() before search_features",
                        "3": "Use exact enum values from the fetched enum_queryables",
                        "4": "Quote string values in single quotes",
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error getting workflow context: {e}")
            return json.dumps(
                {"error": str(e), "instruction": "Proceed with available tools"}
            )

    def _require_workflow_context(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        # Functions that don't need workflow context
        skip_functions = {"get_workflow_context", "hello_world", "check_api_key"}

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    # Legacy retry helper kept for backward compat in tests referencing guidance keys (now replaced by build_error_envelope)
    def _add_retry_context(self, response_data: Dict[str, Any], tool_name: str) -> Dict[str, Any]:  # pragma: no cover - maintained for legacy
        if "error" in response_data and "retry_guidance" not in response_data:
            new_env = build_error_envelope(tool=tool_name, message=response_data.get("error", "Error"))
            response_data.update(new_env)
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
                return json.dumps(
                    build_error_envelope(
                        tool="list_collections",
                        code=ErrorCode.NOT_FOUND,
                        message="No collections found",
                    )
                )

            collections = [
                {"id": col.get("id"), "title": col.get("title")}
                for col in data.get("collections", [])
            ]

            return json.dumps({"collections": collections})
        except Exception as e:
            return json.dumps(
                build_error_envelope(
                    tool="list_collections",
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=str(e),
                )
            )

    async def get_single_collection(
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
            return json.dumps(
                build_error_envelope(
                    tool="get_single_collection",
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=str(e),
                )
            )

    async def get_single_collection_queryables(
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
            return json.dumps(
                build_error_envelope(
                    tool="get_single_collection_queryables",
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=str(e),
                )
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
                valid_collections = set(
                    self.workflow_planner.basic_collections_info.keys()
                )
                if collection_id not in valid_collections:
                    return json.dumps(
                        build_error_envelope(
                            tool="search_features",
                            code=ErrorCode.INVALID_COLLECTION,
                            message=(
                                f"Invalid collection '{collection_id}'. Valid collections (sample): {sorted(valid_collections)[:10]}..."
                            ),
                            details={
                                "suggestion": "Call get_workflow_context() to see all available collections",
                                "provided_collection": collection_id,
                            },
                        )
                    )

            data = await self.api_client.make_request(
                "COLLECTION_FEATURES", params=params, path_params=[collection_id]
            )

            return json.dumps(data)
        except ValueError as ve:
            return json.dumps(
                build_error_envelope(
                    tool="search_features",
                    code=ErrorCode.INVALID_INPUT,
                    message=f"Invalid input: {str(ve)}",
                )
            )
        except Exception as e:
            return json.dumps(
                build_error_envelope(
                    tool="search_features", code=ErrorCode.GENERAL_ERROR, message=str(e)
                )
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
            return json.dumps(
                build_error_envelope(
                    tool="get_feature",
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=f"Error getting feature: {str(e)}",
                )
            )

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
                raw = data.get("results", [])
                linked: List[LinkedIdentifier] = []
                if isinstance(raw, list):
                    for item in raw:
                        if isinstance(item, dict) and isinstance(item.get("featureType"), str):
                            linked.append(cast(LinkedIdentifier, item))
                filtered = [li for li in linked if li.get("featureType") == feature_type]
                return json.dumps({"results": filtered})

            return json.dumps(data)
        except Exception as e:
            return json.dumps(
                build_error_envelope(
                    tool="get_linked_identifiers", code=ErrorCode.UPSTREAM_ERROR, message=str(e)
                )
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
            return json.dumps(
                build_error_envelope(tool="get_bulk_features", code=ErrorCode.UPSTREAM_ERROR, message=str(e))
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
            return json.dumps(
                build_error_envelope(
                    tool="get_bulk_linked_features", code=ErrorCode.UPSTREAM_ERROR, message=str(e)
                )
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

    async def fetch_detailed_collections(self, collection_ids: str | List[str]) -> str:
        """
        Fetch detailed queryables for specific collections mentioned in LLM workflow plan.

        This is mainly to reduce the size of the context for the LLM.

        Only fetch what you really need.

        Args:
            collection_ids: Comma-separated list of collection IDs (e.g., "lus-fts-site-1,trn-ntwk-street-1")

        Returns:
            JSON string with detailed queryables for the specified collections
        """
        try:
            if not self.workflow_planner:
                return json.dumps(
                    build_error_envelope(
                        tool="fetch_detailed_collections",
                        code=ErrorCode.WORKFLOW_CONTEXT_REQUIRED,
                        message="Workflow planner not initialized. Call get_workflow_context() first.",
                    )
                )

            if isinstance(collection_ids, str):
                requested_collections = [cid.strip() for cid in collection_ids.split(",")]
            else:
                requested_collections = [cid.strip() for cid in collection_ids]

            valid_collections = set(self.workflow_planner.basic_collections_info.keys())
            invalid_collections = [
                cid for cid in requested_collections if cid not in valid_collections
            ]

            if invalid_collections:
                return json.dumps(
                    build_error_envelope(
                        tool="fetch_detailed_collections",
                        code=ErrorCode.INVALID_COLLECTION,
                        message=f"Invalid collection IDs: {invalid_collections}",
                        details={"valid_collections": sorted(valid_collections)},
                    )
                )

            # Hint type for mypy (the workflow planner sets this as Dict[str, Dict[str, Any]])
            detailed_cache: Dict[str, Dict[str, Any]] = getattr(
                self.workflow_planner, "detailed_collections_cache", {}
            )
            cached_collections = [cid for cid in requested_collections if cid in detailed_cache]

            collections_to_fetch = [cid for cid in requested_collections if cid not in detailed_cache]

            if collections_to_fetch:
                logger.info(f"Fetching detailed queryables for: {collections_to_fetch}")
                detailed_queryables = (
                    await self.api_client.fetch_collections_queryables(
                        collections_to_fetch
                    )
                )

                for coll_id, queryables in detailed_queryables.items():
                    detailed_cache[coll_id] = {
                        "id": queryables.id,
                        "title": queryables.title,
                        "description": queryables.description,
                        "all_queryables": queryables.all_queryables,
                        "enum_queryables": queryables.enum_queryables,
                        "has_enum_filters": queryables.has_enum_filters,
                        "total_queryables": queryables.total_queryables,
                        "enum_count": queryables.enum_count,
                    }

            context = self.workflow_planner.get_detailed_context(requested_collections)

            return json.dumps(
                {
                    "success": True,
                    "collections_processed": requested_collections,
                    "collections_fetched_from_api": collections_to_fetch,
                    "collections_from_cache": cached_collections,
                    "detailed_collections": context["available_collections"],
                    "message": f"Detailed queryables now available for: {', '.join(requested_collections)}",
                }
            )

        except Exception as e:
            logger.error(f"Error fetching detailed collections: {e}")
            return json.dumps(
                build_error_envelope(
                    tool="fetch_detailed_collections",
                    code=ErrorCode.UPSTREAM_ERROR,
                    message=str(e),
                    details={"suggestion": "Check collection IDs and try again"},
                )
            )

    async def get_routing_data(
        self,
        bbox: Optional[str] = None,
        limit: int = 100,
        include_nodes: bool = True,
        include_edges: bool = True,
        build_network: bool = True,
    ) -> str:
        """
        Get routing data - builds network and returns nodes/edges as flat tables.

        Args:
            bbox: Optional bounding box (format: "minx,miny,maxx,maxy")
            limit: Maximum number of road links to process (default: 1000)
            include_nodes: Whether to include nodes in response (default: True)
            include_edges: Whether to include edges in response (default: True)
            build_network: Whether to build network first (default: True)

        Returns:
            JSON string with routing network data
        """
        try:
            result = {}

            if build_network:
                build_result = await self.routing_service.build_routing_network(
                    bbox, limit
                )
                result["build_status"] = build_result

                if build_result.get("status") != "success":
                    return json.dumps(result)

            if include_nodes:
                nodes_result = self.routing_service.get_flat_nodes()
                result["nodes"] = nodes_result.get("nodes", [])

            if include_edges:
                edges_result = self.routing_service.get_flat_edges()
                result["edges"] = edges_result.get("edges", [])

            summary = self.routing_service.get_network_info()
            result["summary"] = summary.get("network", {})
            result["status"] = "success"

            return json.dumps(result)
        except Exception as e:
            return json.dumps(
                build_error_envelope(tool="get_routing_data", code=ErrorCode.UPSTREAM_ERROR, message=str(e))
            )
