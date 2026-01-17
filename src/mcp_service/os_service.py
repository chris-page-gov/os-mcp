from typing import Optional, List, Dict, Any, Union, Callable, Awaitable, cast, TypedDict, Set
import json
import asyncio
import functools
import re
import os

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
from mcp_service.ui_resources import OSUIResources
from tools.geography_tools import (
    select_geographic_area as _select_geographic_area,
    fetch_boundaries as _fetch_boundaries,
    search_geographic_areas as _search_geographic_areas,
)
from tools.statistics_tools import (
    list_ons_datasets as _list_ons_datasets,
    get_dataset_info as _get_dataset_info,
    get_statistics as _get_statistics,
    compare_areas as _compare_areas,
)
from tools.feature_inspector_tools import (
    inspect_feature as _inspect_feature,
    get_feature_with_linked as _get_feature_with_linked,
    format_linked_identifiers,
)
from tools.route_planner_tools import (
    plan_route as _plan_route,
    get_route_network as _get_route_network,
)
from tools.widget_communication import (
    get_shared_context as _get_shared_context,
    update_shared_context as _update_shared_context,
    share_selection as _share_selection,
)
from pathlib import Path

KNOWLEDGE_INDEX_PATH = Path("data/metadata/knowledge_index_latest.json")

# ---- Constants / Quick-win refactors ----
MAX_SUGGEST_COLLECTION_LIMIT = 25
MAX_SUGGEST_FIELD_LIMIT = 100

# Extract dangerous filter patterns to a module-level constant for clarity & reuse/testing
DANGEROUS_FILTER_PATTERNS: List[str] = [
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

logger = get_logger(__name__)


class OSDataHubService:
    """Implementation of the OS NGD API service with MCP"""

    # Attribute annotations for type checking clarity
    api_client: APIClient
    mcp: MCPService
    stdio_middleware: Optional[Any]
    workflow_planner: Optional[WorkflowPlanner]
    guardrails: ToolGuardrails
    routing_service: OSRoutingService
    _knowledge_index: Optional[Dict[str, Any]]
    class _EnumFieldRef(TypedDict, total=False):
        field: str
        collection: str

    class _KnowledgeIndex(TypedDict, total=False):
        generated_at: str
        field_to_collections: Dict[str, List[str]]
        enum_value_to_fields: Dict[str, List["OSDataHubService._EnumFieldRef"]]
        collection_prefix_groups: Dict[str, List[str]]
        high_cardinality_fields: List[str]
        collection_stats: Dict[str, Dict[str, Any]]
        source_generated_from: str

    class ChatMessage(TypedDict):
        role: str
        content: str

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
        self.workflow_planner = None
        self.guardrails = ToolGuardrails()
        self.routing_service = OSRoutingService(api_client)
        self._knowledge_index = None  # lazy loaded knowledge index
        # (Quick win) Removed lock complexity; simple lazy load is sufficient for current scale
        self.register_tools()
        self.register_resources()
        self.register_prompts()

    # Register all the resources, tools, and prompts
    def register_resources(self) -> None:
        """Register all MCP resources"""
        doc_resources = OSDocumentationResources(self.mcp, self.api_client)
        doc_resources.register_all()

        # Register UI resources (MCP-Apps widgets)
        ui_resources = OSUIResources(self.mcp)
        ui_resources.register_all()

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
            "version_info",
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
            "chat",
            "get_knowledge_index_overview",
            "suggest_collections",
            "suggest_fields",
            "lookup_addresses",
            "diagnose_address_fields",
            "summarise_buildings_by_road",
            # MCP-Apps geography tools (ONS boundaries)
            "select_geographic_area",
            "fetch_boundaries",
            "search_geographic_areas",
            # MCP-Apps statistics tools (ONS statistics)
            "list_ons_datasets",
            "get_dataset_info",
            "get_statistics",
            "compare_areas",
            # MCP-Apps feature inspector tools
            "inspect_feature",
            "get_feature_with_linked",
            # MCP-Apps route planner tools
            "plan_route",
            "get_route_network",
            # MCP-Apps cross-widget communication tools
            "get_shared_context",
            "update_shared_context",
            "share_selection",
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
                    "status": "ok",
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

    # Knowledge index utilities
    def _load_knowledge_index(self) -> Optional["OSDataHubService._KnowledgeIndex"]:
        if self._knowledge_index is not None:
            return cast(OSDataHubService._KnowledgeIndex, self._knowledge_index)
        try:
            if KNOWLEDGE_INDEX_PATH.exists():
                with KNOWLEDGE_INDEX_PATH.open("r", encoding="utf-8") as f:
                    self._knowledge_index = json.load(f)
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Failed loading knowledge index: {e}")
        return cast(Optional[OSDataHubService._KnowledgeIndex], self._knowledge_index)

    async def get_knowledge_index_overview(self) -> str:
        """Summarise the loaded knowledge index.

        Returns:
            JSON string with keys:
              - status: "ok" if index loaded else "unavailable"
              - field_count: number of distinct field names (when available)
              - enum_literal_count: number of distinct enum literal values indexed
              - high_cardinality_fields: sample list (<=25) of high-cardinality fields
              - collection_groups: mapping of prefix/group name -> collection count
              - message / expected_path present only when unavailable
        """
        try:
            idx = self._load_knowledge_index()
            if not idx:
                return json.dumps({
                    "status": "unavailable",
                    "message": "Knowledge index not found. Run harvester & index builder first.",
                    "expected_path": str(KNOWLEDGE_INDEX_PATH)
                })
            field_map: Dict[str, List[str]] = idx.get("field_to_collections", {}) or {}
            enum_value_map: Dict[str, List[OSDataHubService._EnumFieldRef]] = idx.get("enum_value_to_fields", {}) or {}
            high_cards: List[str] = idx.get("high_cardinality_fields", []) or []
            group_map: Dict[str, List[str]] = idx.get("collection_prefix_groups", {}) or {}
            overview: Dict[str, Union[str, int, List[str], Dict[str, int]]] = {
                "status": "ok",
                "field_count": len(field_map),
                "enum_literal_count": len(enum_value_map),
                "high_cardinality_fields": high_cards[:25],
                "collection_groups": {k: len(v) for k, v in group_map.items()},
            }
            return json.dumps(overview)
        except Exception as e:
            return json.dumps(build_error_envelope(tool="get_knowledge_index_overview", code=ErrorCode.GENERAL_ERROR, message=str(e)))

    async def suggest_collections(self, keyword: str, limit: int = 15) -> str:
        """Suggest collection IDs relevant to a keyword.

        Args:
            keyword: Partial or approximate field/name keyword to search across indexed fields.
            limit: Max number of ranked collection matches to return (capped internally at 25).

        Returns:
            JSON string with:
              - keyword (echo)
              - matches: list[{collection_id, score}] sorted by descending score
              - total_candidates: number of returned matches
            If knowledge index unavailable returns standard error envelope with error_code INVALID_INPUT.
        """
        try:
            idx = self._load_knowledge_index()
            if not idx:
                return json.dumps(build_error_envelope(tool="suggest_collections", code=ErrorCode.INVALID_INPUT, message="Knowledge index unavailable"))
            kw = keyword.lower().strip()
            field_map: Dict[str, List[str]] = idx.get("field_to_collections", {}) or {}
            hits: Dict[str, float] = {}
            for field, cols in field_map.items():
                fl = field.lower()
                if kw in fl:
                    # basic score: substring bonus inversely proportional to span length
                    span_score = 1.0 / (1 + (len(fl) - len(kw)))
                    for c in cols:
                        hits[c] = hits.get(c, 0.0) + span_score
                else:
                    # fuzzy: allow 1 edit (very small) using simple heuristic
                    if abs(len(fl) - len(kw)) <= 1:
                        mismatches = sum(1 for a, b in zip(fl, kw) if a != b)
                        if mismatches <= 1 and kw[0:1] == fl[0:1]:
                            for c in cols:
                                hits[c] = hits.get(c, 0.0) + 0.2
            ranked = sorted(hits.items(), key=lambda x: x[1], reverse=True)[: max(1, min(limit, MAX_SUGGEST_COLLECTION_LIMIT))]
            return json.dumps({
                "keyword": keyword,
                "matches": [{"collection_id": cid, "score": score} for cid, score in ranked],
                "total_candidates": len(ranked)
            })
        except Exception as e:
            return json.dumps(build_error_envelope(tool="suggest_collections", code=ErrorCode.GENERAL_ERROR, message=str(e)))

    async def suggest_fields(self, token: str, limit: int = 50) -> str:
        """Suggest field names relevant to a token.

        Args:
            token: Partial or approximate fragment of a field name.
            limit: Maximum number of field names to return (capped internally at 100).

        Ranking:
            Direct substring hits receive a strong base score (1.0 + span bonus). Light fuzzy matches
            (prefix + <=2 mismatches) receive a smaller fixed score (0.3).

        Returns:
            JSON string with:
              - token (echo)
              - field_matches: ordered list of field names
              - example_collections: mapping of up to first 10 fields -> up to first 5 example collections
            If knowledge index unavailable returns error envelope (INVALID_INPUT).
        """
        try:
            idx = self._load_knowledge_index()
            if not idx:
                return json.dumps(build_error_envelope(tool="suggest_fields", code=ErrorCode.INVALID_INPUT, message="Knowledge index unavailable"))
            t = token.lower().strip()
            field_map: Dict[str, List[str]] = idx.get("field_to_collections", {}) or {}
            # collect candidate scores
            scored: List[tuple[str, float]] = []
            for f in field_map:
                fl = f.lower()
                if t in fl:
                    span_score = 1.0 / (1 + (len(fl) - len(t)))
                    scored.append((f, 1.0 + span_score))  # direct substring strong
                else:
                    # very light fuzzy (prefix + one mismatch tolerance)
                    if fl.startswith(t[: max(1, len(t)-1)]) and abs(len(fl) - len(t)) <= 2:
                        mismatches = sum(1 for a, b in zip(fl, t) if a != b)
                        if mismatches <= 2:
                            scored.append((f, 0.3))
            scored.sort(key=lambda x: x[1], reverse=True)
            matches = [f for f, _ in scored[: max(1, min(limit, MAX_SUGGEST_FIELD_LIMIT))]]
            return json.dumps({
                "token": token,
                "field_matches": matches,
                "example_collections": {m: field_map[m][:5] for m in matches[:10]}
            })
        except Exception as e:
            return json.dumps(build_error_envelope(tool="suggest_fields", code=ErrorCode.GENERAL_ERROR, message=str(e)))

    def _require_workflow_context(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        # Functions that don't need workflow context
        skip_functions = {
            "get_workflow_context",
            "hello_world",
            "check_api_key",
            "chat",
            "version_info",
            "list_collections",
            "get_knowledge_index_overview",
            "suggest_collections",
            "suggest_fields",
            "lookup_addresses",
            # MCP-Apps geography tools (standalone ONS API access)
            "select_geographic_area",
            "fetch_boundaries",
            "search_geographic_areas",
            # MCP-Apps statistics tools (standalone ONS API access)
            "list_ons_datasets",
            "get_dataset_info",
            "get_statistics",
            "compare_areas",
            # MCP-Apps feature inspector tools
            "inspect_feature",
            "get_feature_with_linked",
            # MCP-Apps route planner tools
            "plan_route",
            "get_route_network",
            # MCP-Apps cross-widget communication tools
            "get_shared_context",
            "update_shared_context",
            "share_selection",
        }

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.workflow_planner is None and func.__name__ not in skip_functions:
                return json.dumps(
                    build_error_envelope(
                        tool=func.__name__,
                        code=ErrorCode.WORKFLOW_CONTEXT_REQUIRED,
                        message="Call get_workflow_context then fetch_detailed_collections before using this tool",
                        details={"blocked_tool": func.__name__},
                    )
                )
            return await func(*args, **kwargs)

        return wrapper

    # ---------------- LLM CHAT TOOL -----------------
    async def chat(self, messages: Optional[Union[str, Dict[str, Any], List[Dict[str, Any]]]] = None, model: Optional[str] = None) -> str:
        """LLM chat interface (experimental).

        Parameters:
          messages: Either
            - A JSON string of [{"role": "user"|"assistant"|"system", "content": "..."}],
            - A list in that format, or
            - A dict with a top-level key 'messages'.
          model: Optional model override (defaults to env OPENAI_MODEL or 'gpt-4o-mini').

        Returns: JSON string containing {"model", "output", "raw"?, "usage"?}

        Notes:
          - Requires OPENAI_API_KEY in environment.
          - If OpenAI SDK not installed or key missing, returns structured error envelope.
        """
        try:
            if messages is None:
                return json.dumps({"error": "NO_MESSAGES", "message": "Provide messages list"})

            # Normalise input
            parsed: List[Dict[str, Any]]
            if isinstance(messages, str):
                try:
                    data = json.loads(messages)
                except json.JSONDecodeError as e:
                    return json.dumps({"error": "INVALID_JSON", "message": str(e)})
                if isinstance(data, dict) and "messages" in data:
                    parsed = data["messages"]  # type: ignore[assignment]
                else:
                    parsed = data  # type: ignore[assignment]
            elif isinstance(messages, dict):
                if "messages" in messages:
                    parsed = messages["messages"]  # type: ignore[assignment]
                else:
                    return json.dumps({"error": "INVALID_PAYLOAD", "message": "Dict must contain 'messages'"})
            else:
                parsed = messages  # type: ignore[assignment]

            if not isinstance(parsed, list) or not all(isinstance(m, dict) for m in parsed):
                return json.dumps({"error": "INVALID_FORMAT", "message": "Messages must be list[dict]"})
            # Hint to type checker
            parsed = [m for m in parsed if isinstance(m, dict)]  # type: ignore[assignment]

            # Validate roles & content quickly (quick-win hardening)
            allowed_roles: Set[str] = {"user", "assistant", "system"}
            for i, m in enumerate(parsed):
                role = m.get("role")
                content = m.get("content")
                if role not in allowed_roles or not isinstance(content, str):
                    return json.dumps({
                        "error": "INVALID_MESSAGE",
                        "message": f"Invalid message at index {i}: role must be one of {sorted(allowed_roles)} and content must be string"
                    })

            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return json.dumps({"error": "MISSING_OPENAI_API_KEY", "message": "Set OPENAI_API_KEY to use chat tool"})

            selected_model = model or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

            # Invoke underlying LLM (isolated for test mocking)
            llm_response = await self._invoke_llm(parsed, selected_model, api_key)
            return json.dumps(llm_response)
        except Exception as e:  # pragma: no cover - defensive
            logger.error(f"Chat tool error: {e}")
            return json.dumps(build_error_envelope(tool="chat", message=str(e)))

    async def _invoke_llm(self, messages: List[Dict[str, Any]], model: str, api_key: str) -> Dict[str, Any]:
        """Internal helper to call OpenAI (async friendly). Separated for mocking in tests."""
        try:
            # Lazy import so tests can monkeypatch without dependency or to handle absence gracefully
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
                client = OpenAI(api_key=api_key)
                resp = client.chat.completions.create(model=model, messages=messages, temperature=0.2)
                content = resp.choices[0].message.content if resp.choices else ""
                usage = getattr(resp, "usage", None)
                return {"model": model, "output": content, "usage": getattr(usage, 'model_dump', lambda: usage)() if usage else None}
            except ImportError:
                import openai  # type: ignore[import-not-found]
                openai.api_key = api_key
                legacy = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.2)
                content = legacy['choices'][0]['message']['content'] if legacy.get('choices') else ""
                return {"model": model, "output": content, "usage": legacy.get('usage')}
        except ModuleNotFoundError:
            return {"error": "OPENAI_SDK_NOT_INSTALLED", "message": "Install openai package to use chat tool"}
        except Exception as e:  # pragma: no cover
            return {"error": "LLM_CALL_FAILED", "message": str(e)}

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

    async def version_info(self) -> str:
        """Return package version and runtime mode (dev vs prod).

        Heuristic:
          - If running from editable source: presence of top-level 'src/' in __file__ path.
          - If installed as wheel: absence of '/src/' component.
        Also returns select env flags useful for diagnostics.
        """
        import importlib.metadata, sys, pathlib
        try:
            version = importlib.metadata.version("os-mcp")
        except importlib.metadata.PackageNotFoundError:  # pragma: no cover - fallback
            version = "0.0.0+unknown"
        this_file = pathlib.Path(__file__).as_posix()
        mode = "dev" if "/src/" in this_file else "prod"
        data = {
            "package": "os-mcp",
            "version": version,
            "mode": mode,
            "python": sys.version.split()[0],
            "env": {
                k: os.environ.get(k)
                for k in ["OS_API_KEY", "STDIO_KEY", "BEARER_TOKENS", "OPENAI_API_KEY"]
                if os.environ.get(k)
            },
        }
        return json.dumps(data)

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
                for pattern in DANGEROUS_FILTER_PATTERNS:
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
                        if not isinstance(item, dict):
                            continue
                        ft = item.get("featureType")
                        if isinstance(ft, str):
                            linked.append(cast(LinkedIdentifier, item))
                filtered: List[LinkedIdentifier] = [li for li in linked if li.get("featureType") == feature_type]
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
        if category:
            needle = category.lower()
            filtered = {k: v for k, v in PROMPT_TEMPLATES.items() if needle in k.lower()}
            return json.dumps(filtered)
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

    # ---------------- Address / Road lookup (AddressBase-inspired) -----------------
    async def lookup_addresses(self, road: str, postcode: Optional[str] = None, limit: int = 50) -> str:
        """Lightweight address lookup by road (and optional postcode fragment).

        Strategy:
          1. Requires workflow context (planner) so we know available collections.
          2. Heuristically identify an address collection id (contains 'addr' or 'address').
          3. Use knowledge index (if present) to find a field in that collection containing 'street' or 'road'.
          4. Perform a constrained equality search via existing search_features using query_attr/query_attr_value.

        Returns JSON:
          {
            "road": <input road>,
            "address_collection": <collection id>,
            "field_used": <field name>,
            "raw": <raw API response from search_features parsed>,
            "status": "ok" | "error",
            ...error envelope fields when failing...
          }
        """
        try:
            if not self.workflow_planner:
                return json.dumps(build_error_envelope(
                    tool="lookup_addresses",
                    code=ErrorCode.WORKFLOW_CONTEXT_REQUIRED,
                    message="Call get_workflow_context first."
                ))

            clean_road = road.strip()
            if not clean_road or len(clean_road) < 3:
                return json.dumps(build_error_envelope(
                    tool="lookup_addresses",
                    code=ErrorCode.INVALID_INPUT,
                    message="Road must be at least 3 characters"
                ))
            if not re.match(r"^[A-Za-z0-9 .'-]+$", clean_road):
                return json.dumps(build_error_envelope(
                    tool="lookup_addresses",
                    code=ErrorCode.INVALID_INPUT,
                    message="Road contains unsupported characters"
                ))

            # Identify address collection
            addr_collections = [cid for cid in self.workflow_planner.basic_collections_info.keys() if ("addr" in cid.lower() or "address" in cid.lower())]
            if not addr_collections:
                return json.dumps(build_error_envelope(
                    tool="lookup_addresses",
                    code=ErrorCode.NOT_FOUND,
                    message="No address collection detected in available collections"
                ))
            address_collection_id = addr_collections[0]

            # Use knowledge index to find candidate field
            idx = self._load_knowledge_index()
            candidate_field = None
            if idx:
                field_map: Dict[str, List[str]] = idx.get("field_to_collections", {}) or {}
                for field_name, cols in field_map.items():
                    if address_collection_id in cols and any(token in field_name.lower() for token in ["street", "road"]):
                        candidate_field = field_name
                        break
            # Fallback generic guess list if not found
            if candidate_field is None:
                for guess in ["streetName", "streetname", "roadName", "roadname", "name", "addressLine1", "addressline1", "addressLine", "addressline"]:
                    candidate_field = guess
                    break

            # Invoke existing search via query_attr pathway
            raw_json = await self.search_features(
                collection_id=address_collection_id,
                query_attr=candidate_field,
                query_attr_value=clean_road,
                limit=min(limit, 100)
            )
            parsed = json.loads(raw_json)

            # Optionally filter further by postcode fragment if provided and present in properties
            if postcode and isinstance(parsed, dict):
                pc_norm = postcode.replace(" ", "").lower()
                feats = parsed.get("features")
                if isinstance(feats, list):
                    filtered = []
                    for f in feats:
                        if not isinstance(f, dict):
                            continue
                        props = f.get("properties", {})
                        for _, val in list(props.items()):
                            if isinstance(val, str) and pc_norm in val.replace(" ", "").lower():
                                filtered.append(f)
                                break
                    parsed["features"] = filtered

            return json.dumps({
                "status": "ok",
                "road": clean_road,
                "address_collection": address_collection_id,
                "field_used": candidate_field,
                "raw": parsed,
            })
        except Exception as e:
            return json.dumps(build_error_envelope(tool="lookup_addresses", code=ErrorCode.GENERAL_ERROR, message=str(e)))

    async def diagnose_address_fields(self, sample_road: str, limit: int = 5) -> str:
        """Diagnose which address/street field names are plausible for equality lookups.

        Produces a structured report listing:
          - address_collection chosen
          - candidate_fields considered (ordered)
          - attempts: per candidate field variant tested (original, Title, upper, suffix-abbrev if applied)
            each attempt has: field, value_variant, feature_count, notes, optional upstream_error_code, exception
          - summary with first_field_with_hits, total_attempts, total_with_hits

        This does NOT guarantee matches; it is purely diagnostic to aid refining lookup heuristics.
        """
        try:
            if not self.workflow_planner:
                return json.dumps(build_error_envelope(tool="diagnose_address_fields", code=ErrorCode.WORKFLOW_CONTEXT_REQUIRED, message="Call get_workflow_context first."))

            clean = sample_road.strip()
            if not clean or len(clean) < 3:
                return json.dumps(build_error_envelope(tool="diagnose_address_fields", code=ErrorCode.INVALID_INPUT, message="sample_road must be at least 3 characters"))

            addr_cols = [cid for cid in self.workflow_planner.basic_collections_info.keys() if ("addr" in cid.lower() or "address" in cid.lower())]
            if not addr_cols:
                return json.dumps(build_error_envelope(tool="diagnose_address_fields", code=ErrorCode.NOT_FOUND, message="No address collection detected"))
            collection_id = addr_cols[0]

            idx = self._load_knowledge_index()
            candidates: List[str] = []
            if idx:
                fmap: Dict[str, List[str]] = idx.get("field_to_collections", {}) or {}
                for fname, cols in fmap.items():
                    if collection_id in cols and any(tok in fname.lower() for tok in ["street", "road", "name"]):
                        candidates.append(fname)
            # add fallback guesses (keep order but avoid duplicates)
            for guess in ["streetName", "roadName", "name", "addressLine1", "addressLine", "streetname", "roadname", "addressline1"]:
                if guess not in candidates:
                    candidates.append(guess)
            if not candidates:
                candidates = ["streetName"]

            attempts: List[Dict[str, Any]] = []
            ABBREV_MAP = {"street": ["st"], "road": ["rd"], "avenue": ["ave"], "lane": ["ln"], "drive": ["dr"]}

            def gen_variants(base: str) -> List[str]:
                variants = [base]
                if base.lower() != base:
                    variants.append(base.lower())
                title = base.title()
                if title not in variants:
                    variants.append(title)
                upper = base.upper()
                if upper not in variants:
                    variants.append(upper)
                # suffix abbreviation: replace last word if in map
                parts = base.split()
                if len(parts) > 1:
                    last = parts[-1].lower()
                    for k, repls in ABBREV_MAP.items():
                        if last == k:
                            for r in repls:
                                abbr = " ".join(parts[:-1] + [r.title() if parts[-1][0].isupper() else r])
                                if abbr not in variants:
                                    variants.append(abbr)
                return variants

            for field in candidates[: max(1, limit)]:
                for variant in gen_variants(clean):
                    attempt: Dict[str, Any] = {"field": field, "value_variant": variant}
                    try:
                        raw_json = await self.search_features(
                            collection_id=collection_id,
                            query_attr=field,
                            query_attr_value=variant,
                            limit=5,
                        )
                        parsed = json.loads(raw_json)
                        if (
                            isinstance(parsed, dict)
                            and "features" in parsed
                            and isinstance(parsed.get("features"), list)
                        ):
                            attempt["feature_count"] = len(parsed.get("features", []) or [])
                        else:
                            if isinstance(parsed, dict) and parsed.get("error_code"):
                                attempt["upstream_error_code"] = parsed.get("error_code")
                                attempt["notes"] = parsed.get("message")
                            else:
                                attempt["feature_count"] = 0
                        attempts.append(attempt)
                    except Exception as ex:  # pragma: no cover - defensive
                        attempt["exception"] = str(ex)
                        attempts.append(attempt)

            first_hit = next((a for a in attempts if a.get("feature_count", 0) > 0), None)
            total_with_hits = sum(1 for a in attempts if a.get("feature_count", 0) > 0)

            return json.dumps({
                "status": "ok",
                "address_collection": collection_id,
                "candidate_fields": candidates,
                "sample_road": clean,
                "attempts": attempts,
                "summary": {
                    "first_field_with_hits": first_hit.get("field") if first_hit else None,
                    "total_attempts": len(attempts),
                    "attempts_with_hits": total_with_hits,
                }
            })
        except Exception as e:
            return json.dumps(build_error_envelope(tool="diagnose_address_fields", code=ErrorCode.GENERAL_ERROR, message=str(e)))

    async def summarise_buildings_by_road(self, road: str, postcode: Optional[str] = None) -> str:
        """Return a lightweight summary of buildings associated with a road (and optional postcode fragment).

        Flow:
          1. Use lookup_addresses to get address features (and candidate field used)
          2. Extract building identifier property candidates (mainBuildingId, buildingId)
          3. Fetch building collection features matching those IDs (one batch search per id via search_features)
          4. Aggregate basic counts by 'buildinguse' (or fallback property name variants) and return summary

        Returns JSON with keys: status, road, postcode(optional), address_hits, total_buildings, aggregates{by_use{}, total_buildings}, building_ids, notes
        """
        try:
            if not self.workflow_planner:
                return json.dumps(build_error_envelope(tool="summarise_buildings_by_road", code=ErrorCode.WORKFLOW_CONTEXT_REQUIRED, message="Call get_workflow_context first."))

            # Step 1: address lookup (reuse existing logic, parse result)
            lookup_raw = await self.lookup_addresses(road, postcode=postcode, limit=200)
            lookup = json.loads(lookup_raw)
            if lookup.get("error_code"):
                return json.dumps({"status": "error", "phase": "lookup", **lookup})
            address_features = (lookup.get("raw", {}) or {}).get("features", []) if isinstance(lookup.get("raw"), dict) else []
            if not isinstance(address_features, list):
                address_features = []

            # Step 2: extract building ids
            building_id_fields = ["mainBuildingId", "buildingId", "mainbuildingid", "buildingid"]
            building_ids: Set[str] = set()
            for feat in address_features:
                if not isinstance(feat, dict):
                    continue
                props = feat.get("properties", {})
                if not isinstance(props, dict):
                    continue
                for bf in building_id_fields:
                    val = props.get(bf)
                    if isinstance(val, str) and val.strip():
                        building_ids.add(val.strip())
            if not building_ids:
                return json.dumps({
                    "status": "ok",
                    "road": road,
                    "postcode": postcode,
                    "address_hits": len(address_features),
                    "building_ids": [],
                    "aggregates": {"total_buildings": 0, "by_use": {}},
                    "notes": "No building ids found in address features"
                })

            # Step 3: identify building collection
            bld_collections = [cid for cid in self.workflow_planner.basic_collections_info.keys() if ("bld" in cid.lower() or "build" in cid.lower())]
            if not bld_collections:
                return json.dumps(build_error_envelope(tool="summarise_buildings_by_road", code=ErrorCode.NOT_FOUND, message="No building collection detected"))
            building_collection_id = bld_collections[0]

            # Fetch each building record (limit 1 per id)
            building_features: List[Dict[str, Any]] = []
            for bid in list(building_ids)[:200]:  # cap
                resp_raw = await self.search_features(collection_id=building_collection_id, query_attr="mainBuildingId", query_attr_value=bid, limit=1)
                resp = json.loads(resp_raw)
                if isinstance(resp, dict) and isinstance(resp.get("features"), list):
                    for f in resp.get("features", []):
                        if isinstance(f, dict):
                            building_features.append(f)

            # Step 4: aggregate by use (attempt several candidate property names)
            use_fields = ["buildinguse", "buildingUse", "primaryUse", "use", "function"]
            by_use: Dict[str, int] = {}
            total = 0
            for bf in building_features:
                if not isinstance(bf, dict):
                    continue
                props = bf.get("properties", {})
                if not isinstance(props, dict):
                    continue
                use_val = None
                for uf in use_fields:
                    val = props.get(uf)
                    if isinstance(val, str) and val.strip():
                        use_val = val.strip()
                        break
                if not use_val:
                    use_val = "(unknown)"
                by_use[use_val] = by_use.get(use_val, 0) + 1
                total += 1

            return json.dumps({
                "status": "ok",
                "road": road,
                "postcode": postcode,
                "address_hits": len(address_features),
                "building_ids": sorted(list(building_ids)),
                "aggregates": {"total_buildings": total, "by_use": by_use},
                "building_collection": building_collection_id,
            })
        except Exception as e:
            return json.dumps(build_error_envelope(tool="summarise_buildings_by_road", code=ErrorCode.GENERAL_ERROR, message=str(e)))

    # ============================================================================
    # MCP-Apps Geography Tools (ONS Boundaries)
    # ============================================================================

    async def select_geographic_area(
        self,
        level: str = "local_auth",
        initial_lat: Optional[float] = None,
        initial_lng: Optional[float] = None,
        initial_zoom: Optional[int] = None,
        search_term: Optional[str] = None,
        multi_select: bool = True,
    ) -> str:
        """Opens interactive map widget for selecting UK geographic areas.

        This tool triggers a visual map interface where users can click on areas
        to select them, switch between geographic levels, and search by name.

        Args:
            level: Geographic level (parl_const, local_auth, ward, lsoa, msoa, oa)
            initial_lat: Starting latitude (default: 52.4862)
            initial_lng: Starting longitude (default: -1.8904)
            initial_zoom: Starting zoom level (default: 6)
            search_term: Optional search query to pre-filter areas
            multi_select: Allow multiple area selection (default: True)

        Returns:
            JSON with widget configuration and UI resource reference
        """
        return await _select_geographic_area(
            level=level,
            initial_lat=initial_lat,
            initial_lng=initial_lng,
            initial_zoom=initial_zoom,
            search_term=search_term,
            multi_select=multi_select,
        )

    async def fetch_boundaries(
        self,
        level: str,
        codes: Optional[str] = None,
        bbox: Optional[str] = None,
        limit: int = 100,
    ) -> str:
        """Fetch boundary geometries for UK geographic areas from ONS.

        Args:
            level: Geographic level (parl_const, local_auth, ward, lsoa, msoa, oa)
            codes: Optional comma-separated GSS codes for specific areas
            bbox: Optional bounding box as "west,south,east,north"
            limit: Maximum features to return (default: 100, max: 500)

        Returns:
            GeoJSON FeatureCollection with boundary geometries
        """
        return await _fetch_boundaries(
            level=level,
            codes=codes,
            bbox=bbox,
            limit=limit,
        )

    async def search_geographic_areas(
        self,
        query: str,
        level: str = "local_auth",
        limit: int = 10,
    ) -> str:
        """Search for UK geographic areas by name.

        Args:
            query: Search term (area name, minimum 2 characters)
            level: Geographic level to search within
            limit: Maximum results (default: 10, max: 50)

        Returns:
            JSON with matching areas including GSS codes and names
        """
        return await _search_geographic_areas(
            query=query,
            level=level,
            limit=limit,
        )

    # ============================================================================
    # MCP-Apps Statistics Tools (ONS Statistics API)
    # ============================================================================

    async def list_ons_datasets(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None,
        include_census: bool = False,
        limit: int = 50,
    ) -> str:
        """List available ONS datasets.

        Discover datasets from the Office for National Statistics API.

        Args:
            category: Filter by category (wellbeing, economy, housing, population, health, employment, census)
            search: Search term to filter datasets
            include_census: Include Census 2021 datasets (default: False)
            limit: Maximum datasets to return (default: 50)

        Returns:
            JSON with list of datasets including id, title, description
        """
        return await _list_ons_datasets(
            category=category,
            search=search,
            include_census=include_census,
            limit=limit,
        )

    async def get_dataset_info(self, dataset_id: str) -> str:
        """Get detailed information about a specific ONS dataset.

        Args:
            dataset_id: The dataset identifier (e.g., "wellbeing-local-authority")

        Returns:
            JSON with dataset metadata, dimensions, and data structure
        """
        return await _get_dataset_info(dataset_id=dataset_id)

    async def get_statistics(
        self,
        dataset_id: str,
        area_codes: Optional[str] = None,
        time_period: Optional[str] = None,
        limit: int = 100,
    ) -> str:
        """Get statistical observations from an ONS dataset.

        Retrieves data values for specified geographic areas. Returns data
        linked to the statistics dashboard widget for visualization.

        Args:
            dataset_id: The dataset identifier (e.g., "wellbeing-local-authority")
            area_codes: Comma-separated GSS codes (e.g., "E08000026,E08000025")
            time_period: Time filter (e.g., "2023")
            limit: Maximum observations (default: 100)

        Returns:
            JSON with observations and UI resource reference
        """
        return await _get_statistics(
            dataset_id=dataset_id,
            area_codes=area_codes,
            time_period=time_period,
            limit=limit,
        )

    async def compare_areas(
        self,
        dataset_id: str,
        area_codes: str,
        time_period: Optional[str] = None,
    ) -> str:
        """Compare statistics across multiple geographic areas.

        Args:
            dataset_id: The dataset identifier
            area_codes: Comma-separated GSS codes (2-10 areas)
            time_period: Optional time filter

        Returns:
            JSON with comparison data for visualization
        """
        return await _compare_areas(
            dataset_id=dataset_id,
            area_codes=area_codes,
            time_period=time_period,
        )

    # ============================================================================
    # MCP-Apps Feature Inspector Tools
    # ============================================================================

    async def inspect_feature(
        self,
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
            JSON with widget configuration and UI resource reference
        """
        return await _inspect_feature(
            feature_id=feature_id,
            collection_id=collection_id,
            include_linked=include_linked,
            include_geometry=include_geometry,
        )

    async def get_feature_with_linked(
        self,
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
            JSON with feature data, properties, and linked identifiers
        """
        return await _get_feature_with_linked(
            feature_id=feature_id,
            collection_id=collection_id,
            identifier_type=identifier_type,
            include_geometry=include_geometry,
        )

    # ============================================================================
    # MCP-Apps Route Planner Tools
    # ============================================================================

    async def plan_route(
        self,
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
            JSON with widget configuration and UI resource reference
        """
        return await _plan_route(
            start_lat=start_lat,
            start_lng=start_lng,
            end_lat=end_lat,
            end_lng=end_lng,
            bbox=bbox,
            show_network=show_network,
        )

    async def get_route_network(
        self,
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
            JSON with network data request configuration
        """
        return await _get_route_network(
            bbox=bbox,
            include_restrictions=include_restrictions,
            limit=limit,
        )

    # ============================================================================
    # MCP-Apps Cross-Widget Communication Tools
    # ============================================================================

    async def get_shared_context(self) -> str:
        """Get the current shared widget context.

        Returns the current state of shared selections across widgets,
        including selected areas, features, datasets, and route points.

        Returns:
            JSON with current shared context and summary
        """
        return await _get_shared_context()

    async def update_shared_context(
        self,
        context_type: str,
        action: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Update the shared widget context.

        Args:
            context_type: Type of context (areas, features, datasets, route_points, bbox)
            action: Action to perform (add, remove, clear, set)
            data: Data for the action

        Returns:
            JSON with updated context summary
        """
        return await _update_shared_context(
            context_type=context_type,
            action=action,
            data=data,
        )

    async def share_selection(
        self,
        source_widget: str,
        target_widget: str,
        selection_data: Dict[str, Any],
    ) -> str:
        """Share a selection from one widget to another.

        Args:
            source_widget: Widget sending the selection (geography, statistics, feature, route)
            target_widget: Widget receiving the selection
            selection_data: The selection to share

        Returns:
            JSON with configuration for the target widget
        """
        return await _share_selection(
            source_widget=source_widget,
            target_widget=target_widget,
            selection_data=selection_data,
        )
