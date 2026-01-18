"""Tool Search Configuration for OS-MCP Server

This module defines tool categories, defer_loading settings, and enhanced
descriptions for Anthropic's Tool Search facility.

Tool search enables dynamic tool discovery for large tool catalogs (36+ tools).
Tools marked with defer_loading=True are only loaded into context when Claude
discovers them via search.

Two search variants are supported:
- Regex (tool_search_tool_regex_20251119): Claude constructs regex patterns
- BM25 (tool_search_tool_bm25_20251119): Claude uses natural language queries

Required beta headers:
- advanced-tool-use-2025-11-20
- mcp-client-2025-11-20

Supported models: Claude Opus 4.5, Claude Sonnet 4.5
"""

from typing import Dict, List, Set, TypedDict, Any
from enum import Enum


class ToolCategory(str, Enum):
    """Categories for tool organization"""
    CORE = "core"  # Always loaded - essential tools
    WORKFLOW = "workflow"  # Workflow management tools
    GEOGRAPHY = "geography"  # UK geographic boundary tools
    STATISTICS = "statistics"  # ONS statistics tools
    FEATURES = "features"  # OS NGD feature tools
    ROUTING = "routing"  # Route planning tools
    WIDGET = "widget"  # Cross-widget communication
    SEARCH = "search"  # Search and suggestion tools
    LINKED = "linked"  # Linked identifiers tools
    UTILITY = "utility"  # Utility and diagnostic tools


class ToolConfig(TypedDict, total=False):
    """Configuration for a single tool"""
    defer_loading: bool
    category: str
    keywords: List[str]  # Additional keywords for searchability
    description_enhanced: str  # Enhanced description for better search
    # MCP Tool Annotations (hints for clients)
    read_only_hint: bool  # True if tool doesn't modify state (default: True for most tools)
    destructive_hint: bool  # True if tool may perform destructive updates (default: False)
    idempotent_hint: bool  # True if repeated calls have no additional effect
    open_world_hint: bool  # True if tool interacts with external APIs


# Tools that should ALWAYS be loaded (defer_loading=False)
# MINIMAL SET - only the most essential tools for fast, simple responses
ALWAYS_LOADED_TOOLS: Set[str] = {
    # ========================================
    # PRIMARY TOOLS - These handle 90% of queries
    # ========================================
    "search_geographic_areas",  # THE primary tool - finds places by name, returns codes
    "get_statistics",           # Get stats for an area (wellbeing, population, etc.)

    # ========================================
    # ROUTING - Helps choose the right tool
    # ========================================
    "route_query",  # Classifies intent, recommends tool

    # ========================================
    # CORE - Server health/info only
    # ========================================
    "hello_world",
    "version_info",
}


# Tools that should be DEFERRED (defer_loading=True)
# These are discovered via tool search when needed
DEFERRED_TOOLS: Set[str] = {
    # ========================================
    # OS NGD MAPPING - Specialized for topographic data (NOT place lookups!)
    # ========================================
    "os_ngd_init_mapping_workflow",    # RENAMED: Only for OS NGD mapping features
    "os_ngd_list_mapping_collections", # RENAMED: Browse OS NGD mapping collections
    "fetch_detailed_collections",
    "get_single_collection",
    "get_single_collection_queryables",
    "search_features",            # Search OS NGD (buildings, roads, etc.)
    "get_feature",
    "get_bulk_features",

    # ========================================
    # GEOGRAPHY - Secondary tools
    # ========================================
    "select_geographic_area",     # MOVED: Interactive map widget
    "fetch_boundaries",           # Get GeoJSON boundaries

    # ========================================
    # STATISTICS - Secondary tools
    # ========================================
    "list_ons_datasets",          # MOVED: Browse available datasets
    "get_dataset_info",           # Dataset metadata
    "compare_areas",              # Compare multiple areas

    # ========================================
    # FEATURE INSPECTION
    # ========================================
    "inspect_feature",
    "get_feature_with_linked",
    "get_linked_identifiers",
    "get_bulk_linked_features",

    # ========================================
    # ROUTING
    # ========================================
    "plan_route",                 # MOVED: Route planner widget
    "get_route_network",
    "get_routing_data",

    # ========================================
    # WIDGETS & UTILITIES
    # ========================================
    "get_shared_context",         # MOVED: Cross-widget state
    "update_shared_context",
    "share_selection",
    "check_api_key",              # MOVED: API key validation
    "get_tool_search_config",     # MOVED: Tool search config
    "suggest_collections",
    "suggest_fields",
    "get_knowledge_index_overview",
    "lookup_addresses",
    "diagnose_address_fields",
    "summarise_buildings_by_road",
    "get_prompt_templates",
    "chat",
}


# =============================================================================
# TOOL ANNOTATIONS (MCP hints for client permission handling)
# =============================================================================

# Tools that MODIFY state (readOnlyHint=False)
# All other tools are read-only by default
STATEFUL_TOOLS: Set[str] = {
    "update_shared_context",  # Modifies shared widget context
    "share_selection",  # Modifies shared widget context
}

# Tools that interact with EXTERNAL APIs (openWorldHint=True)
# These call OS Data Hub, ONS APIs, or OpenAI
EXTERNAL_API_TOOLS: Set[str] = {
    # OS Data Hub API tools (OS NGD mapping)
    "os_ngd_init_mapping_workflow",
    "os_ngd_list_mapping_collections",
    "fetch_detailed_collections",
    "get_single_collection",
    "get_single_collection_queryables",
    "search_features",
    "get_feature",
    "get_linked_identifiers",
    "get_bulk_features",
    "get_bulk_linked_features",
    "get_routing_data",
    "get_route_network",
    "lookup_addresses",
    "diagnose_address_fields",
    "summarise_buildings_by_road",
    # ONS Geography API tools
    "fetch_boundaries",
    "search_geographic_areas",
    # ONS Statistics API tools
    "list_ons_datasets",
    "get_dataset_info",
    "get_statistics",
    "compare_areas",
    # OpenAI API
    "chat",
}

# Tools that are idempotent (calling multiple times has same effect)
IDEMPOTENT_TOOLS: Set[str] = {
    "hello_world",
    "check_api_key",
    "version_info",
    "get_tool_search_config",
    "route_query",
    "get_shared_context",
    "get_prompt_templates",
    "get_knowledge_index_overview",
    "suggest_collections",
    "suggest_fields",
}


def get_tool_annotations(tool_name: str) -> Dict[str, bool]:
    """Get MCP tool annotation hints for a specific tool.

    These hints help MCP clients make better permission decisions:
    - readOnlyHint: True if tool doesn't modify state (most tools)
    - destructiveHint: True if tool may perform destructive updates (none currently)
    - idempotentHint: True if repeated calls have no additional effect
    - openWorldHint: True if tool interacts with external APIs

    Args:
        tool_name: Name of the tool

    Returns:
        Dict with annotation hints (only includes True values)
    """
    annotations: Dict[str, bool] = {}

    # Read-only hint (default True, False only for stateful tools)
    if tool_name not in STATEFUL_TOOLS:
        annotations["readOnlyHint"] = True

    # Idempotent hint
    if tool_name in IDEMPOTENT_TOOLS:
        annotations["idempotentHint"] = True

    # Open world hint (calls external APIs)
    if tool_name in EXTERNAL_API_TOOLS:
        annotations["openWorldHint"] = True

    return annotations


# Enhanced tool descriptions with keywords for better search discovery
TOOL_DESCRIPTIONS: Dict[str, ToolConfig] = {
    # ========================================
    # PRIMARY ENTRY POINT - Call this FIRST!
    # ========================================
    "route_query": {
        "defer_loading": False,
        "category": ToolCategory.CORE,
        "keywords": ["route", "query", "intent", "classify", "recommend", "start", "first", "help", "find", "search", "what tool"],
        "description_enhanced": "PRIMARY ENTRY POINT - Call this FIRST for any natural language query. Analyzes intent and recommends the right tool. Examples: 'Find Birmingham' → search_geographic_areas, 'Wellbeing in Coventry' → get_statistics, 'Show cinemas' → OS NGD workflow.",
    },

    # === CORE TOOLS ===
    "hello_world": {
        "defer_loading": False,
        "category": ToolCategory.CORE,
        "keywords": ["test", "health", "status", "ping"],
        "description_enhanced": "Test server connectivity.",
    },
    "check_api_key": {
        "defer_loading": True,  # Deferred - only needed for diagnostics
        "category": ToolCategory.CORE,
        "keywords": ["api", "key", "authentication", "credentials", "validate"],
        "description_enhanced": "Validate OS Data Hub API key.",
    },
    "version_info": {
        "defer_loading": False,
        "category": ToolCategory.CORE,
        "keywords": ["version", "info", "mode", "environment", "debug"],
        "description_enhanced": "Get server version and runtime mode.",
    },
    "get_tool_search_config": {
        "defer_loading": True,  # Deferred - only for tool search integration
        "category": ToolCategory.CORE,
        "keywords": ["tool", "search", "config", "defer", "loading", "categories"],
        "description_enhanced": "Get tool search configuration for defer_loading support.",
    },

    # === OS NGD MAPPING TOOLS (DEFERRED) ===
    # ⛔ SPECIALIZED for topographic mapping data. NOT for place lookups!
    "os_ngd_init_mapping_workflow": {
        "defer_loading": True,  # DEFERRED - only for OS NGD mapping features
        "category": ToolCategory.WORKFLOW,
        "keywords": ["os_ngd", "mapping", "topographic", "buildings", "roads", "land"],
        "description_enhanced": "⛔ SPECIALIZED - OS NGD mapping data only. ❌ WRONG for place lookups (use search_geographic_areas) or map widgets (use select_geographic_area).",
    },
    "os_ngd_list_mapping_collections": {
        "defer_loading": True,  # DEFERRED - only for browsing OS NGD mapping collections
        "category": ToolCategory.WORKFLOW,
        "keywords": ["os_ngd", "collections", "mapping", "topographic"],
        "description_enhanced": "⛔ SPECIALIZED - Lists OS NGD mapping collections. ❌ WRONG for place lookups (use search_geographic_areas).",
    },
    "fetch_detailed_collections": {
        "defer_loading": True,
        "category": ToolCategory.WORKFLOW,
        "keywords": ["collections", "queryables", "fields", "schema", "filters", "detailed", "NGD"],
        "description_enhanced": "Fetch queryables for OS NGD collections. REQUIRED before search_features for mapping data. For place name lookups, use search_geographic_areas instead.",
    },
    "get_single_collection": {
        "defer_loading": True,
        "category": ToolCategory.WORKFLOW,
        "keywords": ["collection", "metadata", "details", "single"],
        "description_enhanced": "Get metadata for a single OS NGD collection. Returns detailed information about collection schema, CRS, and capabilities.",
    },
    "get_single_collection_queryables": {
        "defer_loading": True,
        "category": ToolCategory.WORKFLOW,
        "keywords": ["queryables", "fields", "schema", "single", "collection"],
        "description_enhanced": "Get queryable fields for a single collection. Returns field names, types, descriptions, and enum values for filtering.",
    },

    # === GEOGRAPHY TOOLS ===
    # search_geographic_areas is THE PRIMARY TOOL for finding places by name!
    "search_geographic_areas": {
        "defer_loading": False,  # ALWAYS LOADED - primary tool for place lookups
        "category": ToolCategory.GEOGRAPHY,
        "keywords": ["search", "find", "city", "town", "council", "local authority", "Birmingham", "Manchester", "London", "Leeds", "Coventry", "Sheffield", "ward", "constituency", "where", "code", "GSS"],
        "description_enhanced": "★ PRIMARY TOOL ★ Find UK places by name (cities, towns, councils). Returns GSS area codes. Use for: 'find Birmingham', 'where is Manchester', 'local authority code for Coventry'. Direct lookup - no workflow needed.",
    },
    "select_geographic_area": {
        "defer_loading": True,  # Deferred - interactive widget
        "category": ToolCategory.GEOGRAPHY,
        "keywords": ["map", "select", "area", "widget", "interactive", "click"],
        "description_enhanced": "Interactive map widget for visual area selection. Use when user wants to click/browse rather than search by name.",
    },
    "fetch_boundaries": {
        "defer_loading": True,
        "category": ToolCategory.GEOGRAPHY,
        "keywords": ["boundary", "geojson", "polygon", "geometry", "shape"],
        "description_enhanced": "Get GeoJSON boundaries for areas. Use after search_geographic_areas to get shapes.",
    },

    # === STATISTICS TOOLS ===
    # get_statistics is PRIMARY - use after search_geographic_areas
    "get_statistics": {
        "defer_loading": False,  # ALWAYS LOADED - primary stats tool
        "category": ToolCategory.STATISTICS,
        "keywords": ["statistics", "data", "wellbeing", "population", "house prices", "GDP", "employment", "health", "ONS"],
        "description_enhanced": "★ PRIMARY TOOL ★ Get statistics for an area (wellbeing, population, house prices, etc.). Use after search_geographic_areas gives you the area code.",
    },
    "list_ons_datasets": {
        "defer_loading": True,  # Deferred - only for browsing datasets
        "category": ToolCategory.STATISTICS,
        "keywords": ["ONS", "datasets", "catalog", "browse", "available"],
        "description_enhanced": "Browse available ONS datasets. Use when exploring what statistics exist.",
    },
    "get_dataset_info": {
        "defer_loading": True,
        "category": ToolCategory.STATISTICS,
        "keywords": ["dataset", "metadata", "dimensions", "info"],
        "description_enhanced": "Get metadata for a specific dataset.",
    },
    "compare_areas": {
        "defer_loading": True,
        "category": ToolCategory.STATISTICS,
        "keywords": ["compare", "areas", "ranking", "benchmark"],
        "description_enhanced": "Compare statistics across multiple areas side-by-side.",
    },

    # === FEATURE TOOLS ===
    "search_features": {
        "defer_loading": True,
        "category": ToolCategory.FEATURES,
        "keywords": ["search", "features", "query", "filter", "bbox", "buildings", "roads"],
        "description_enhanced": "Search OS NGD features with filters and bounding box. Query buildings, roads, addresses, land use, water features using CQL filters. Requires fetch_detailed_collections first.",
    },
    "get_feature": {
        "defer_loading": True,
        "category": ToolCategory.FEATURES,
        "keywords": ["feature", "get", "single", "id", "details"],
        "description_enhanced": "Get a single feature by ID from OS NGD collection. Returns complete feature properties, geometry, and linked identifiers (TOID, UPRN, USRN).",
    },
    "get_bulk_features": {
        "defer_loading": True,
        "category": ToolCategory.FEATURES,
        "keywords": ["bulk", "features", "multiple", "batch", "ids"],
        "description_enhanced": "Get multiple features by IDs in a single request. Efficiently retrieve batch of features from OS NGD collection with full properties.",
    },
    "inspect_feature": {
        "defer_loading": True,
        "category": ToolCategory.FEATURES,
        "keywords": ["inspect", "feature", "widget", "properties", "map", "details"],
        "description_enhanced": "Open feature inspector widget for detailed view. Interactive UI showing properties table, geometry map, linked identifiers, and export options.",
    },
    "get_feature_with_linked": {
        "defer_loading": True,
        "category": ToolCategory.FEATURES,
        "keywords": ["feature", "linked", "identifiers", "TOID", "UPRN", "USRN"],
        "description_enhanced": "Get feature with all linked identifiers. Returns feature properties plus related TOIDs, UPRNs, and USRNs for cross-referencing buildings, addresses, and streets.",
    },

    # === LINKED IDENTIFIERS TOOLS ===
    "get_linked_identifiers": {
        "defer_loading": True,
        "category": ToolCategory.LINKED,
        "keywords": ["linked", "identifiers", "TOID", "UPRN", "USRN", "cross-reference"],
        "description_enhanced": "Get linked identifiers for a feature. Find related TOIDs (topographic IDs), UPRNs (property IDs), and USRNs (street IDs) for a given OS feature.",
    },
    "get_bulk_linked_features": {
        "defer_loading": True,
        "category": ToolCategory.LINKED,
        "keywords": ["bulk", "linked", "features", "batch", "relationships"],
        "description_enhanced": "Get linked features in bulk. Retrieve multiple features with their linked identifiers efficiently for relationship analysis.",
    },

    # === ROUTING TOOLS (DEFERRED) ===
    "plan_route": {
        "defer_loading": True,  # Deferred - interactive widget
        "category": ToolCategory.ROUTING,
        "keywords": ["route", "directions", "navigation", "path", "journey"],
        "description_enhanced": "Interactive route planner widget. Set start/end points, get directions.",
    },
    "get_route_network": {
        "defer_loading": True,
        "category": ToolCategory.ROUTING,
        "keywords": ["network", "roads", "streets", "topology", "bbox"],
        "description_enhanced": "Get road network data for a bounding box. Returns street network topology for custom routing analysis and visualization.",
    },
    "get_routing_data": {
        "defer_loading": True,
        "category": ToolCategory.ROUTING,
        "keywords": ["routing", "path", "calculation", "API", "directions"],
        "description_enhanced": "Calculate route using OS Routing API. Get optimized path between points with distance, duration, and turn-by-turn instructions.",
    },

    # === WIDGET COMMUNICATION TOOLS (DEFERRED) ===
    "get_shared_context": {
        "defer_loading": True,  # Deferred - only for multi-widget workflows
        "category": ToolCategory.WIDGET,
        "keywords": ["shared", "context", "state", "selections"],
        "description_enhanced": "Get cross-widget shared state. For multi-widget workflows only.",
    },
    "update_shared_context": {
        "defer_loading": True,
        "category": ToolCategory.WIDGET,
        "keywords": ["update", "shared", "context", "modify", "state"],
        "description_enhanced": "Update cross-widget shared context. Add, remove, or clear selections in the shared state accessible by all widgets.",
    },
    "share_selection": {
        "defer_loading": True,
        "category": ToolCategory.WIDGET,
        "keywords": ["share", "selection", "transfer", "widget", "communicate"],
        "description_enhanced": "Share selection from one widget to another. Transfer selected areas, features, or routes between geography, statistics, and inspector widgets.",
    },

    # === SEARCH AND SUGGESTION TOOLS ===
    "suggest_collections": {
        "defer_loading": True,
        "category": ToolCategory.SEARCH,
        "keywords": ["suggest", "collections", "recommend", "find", "match"],
        "description_enhanced": "Get collection suggestions based on keywords. AI-assisted recommendation of relevant OS NGD collections for your query intent.",
    },
    "suggest_fields": {
        "defer_loading": True,
        "category": ToolCategory.SEARCH,
        "keywords": ["suggest", "fields", "attributes", "recommend", "filter"],
        "description_enhanced": "Get field suggestions for filtering. AI-assisted recommendation of queryable fields and filter values for effective searches.",
    },
    "get_knowledge_index_overview": {
        "defer_loading": True,
        "category": ToolCategory.SEARCH,
        "keywords": ["knowledge", "index", "overview", "metadata", "summary"],
        "description_enhanced": "Get knowledge index overview. Returns summary of indexed collections, fields, enum values, and high-cardinality attributes for query planning.",
    },

    # === UTILITY TOOLS ===
    "lookup_addresses": {
        "defer_loading": True,
        "category": ToolCategory.UTILITY,
        "keywords": ["address", "lookup", "postcode", "find", "location"],
        "description_enhanced": "Look up addresses by postcode or search term. Find UK addresses with full details including UPRN, coordinates, and classification.",
    },
    "diagnose_address_fields": {
        "defer_loading": True,
        "category": ToolCategory.UTILITY,
        "keywords": ["diagnose", "address", "fields", "debug", "troubleshoot"],
        "description_enhanced": "Diagnose address field issues. Analyze address data quality, identify missing fields, and troubleshoot query problems.",
    },
    "summarise_buildings_by_road": {
        "defer_loading": True,
        "category": ToolCategory.UTILITY,
        "keywords": ["buildings", "road", "summary", "count", "aggregate"],
        "description_enhanced": "Summarize buildings along a road. Get counts, types, and statistics for buildings associated with a USRN (street reference).",
    },
    "get_prompt_templates": {
        "defer_loading": True,
        "category": ToolCategory.UTILITY,
        "keywords": ["prompts", "templates", "workflows", "examples", "guidance"],
        "description_enhanced": "Get workflow prompt templates. Returns pre-built prompts for common OS NGD queries including planning, routing, and diagnostics workflows.",
    },
    "chat": {
        "defer_loading": True,
        "category": ToolCategory.UTILITY,
        "keywords": ["chat", "conversation", "OpenAI", "assistant"],
        "description_enhanced": "Experimental chat tool using OpenAI. Enables conversational interaction for complex query planning (requires OPENAI_API_KEY).",
    },
}


def get_tool_config(tool_name: str) -> ToolConfig:
    """Get configuration for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        ToolConfig with defer_loading, category, keywords, and enhanced description
    """
    if tool_name in TOOL_DESCRIPTIONS:
        return TOOL_DESCRIPTIONS[tool_name]

    # Default config for unknown tools - always load
    return {
        "defer_loading": False,
        "category": ToolCategory.UTILITY,
        "keywords": [],
        "description_enhanced": f"Tool: {tool_name}",
    }


def should_defer_loading(tool_name: str) -> bool:
    """Check if a tool should have defer_loading=True.

    Args:
        tool_name: Name of the tool

    Returns:
        True if tool should be deferred, False if always loaded
    """
    if tool_name in ALWAYS_LOADED_TOOLS:
        return False
    if tool_name in DEFERRED_TOOLS:
        return True
    # Default to not deferred for unknown tools
    return False


def get_tools_by_category(category: ToolCategory) -> List[str]:
    """Get list of tools in a specific category.

    Args:
        category: The category to filter by

    Returns:
        List of tool names in that category
    """
    return [
        name for name, config in TOOL_DESCRIPTIONS.items()
        if config.get("category") == category
    ]


def get_always_loaded_tools() -> Set[str]:
    """Get set of tools that should always be loaded.

    Returns:
        Set of tool names that should never be deferred
    """
    return ALWAYS_LOADED_TOOLS.copy()


def get_deferred_tools() -> Set[str]:
    """Get set of tools that should be deferred.

    Returns:
        Set of tool names that should have defer_loading=True
    """
    return DEFERRED_TOOLS.copy()


def get_tool_search_system_prompt() -> str:
    """Get system prompt section for tool search.

    This should be added to system prompts when using tool search
    to help Claude understand available tool categories.

    Returns:
        System prompt text describing tool categories
    """
    return """## PRIMARY TOOLS (Use These First!)

★ search_geographic_areas - Find places by name (cities, towns, councils)
★ get_statistics - Get statistics for an area
★ select_geographic_area - Show interactive map to select areas

### IMPORTANT: Tool Selection

**For finding places by NAME** (e.g., "find Birmingham", "show map of Coventry"):
→ Use `search_geographic_areas(query="Birmingham", level="local_auth")`
→ Use `select_geographic_area(level="oa", search_term="Coventry")` for map widget

**For statistics** (e.g., "wellbeing in Coventry", "population of Leeds"):
→ First: `search_geographic_areas` to get area code
→ Then: `get_statistics` with the area code

**⛔ os_ngd_* tools are SPECIALIZED** for OS topographic mapping data:
→ Only use for buildings, roads, land use features
→ NOT for finding places or showing map widgets

### Quick Decision Guide

| User Question | Tool to Use |
|---------------|-------------|
| "Find Birmingham" | search_geographic_areas |
| "Show map of Coventry to select areas" | select_geographic_area |
| "Get statistics for Coventry" | search_geographic_areas → get_statistics |
| "Find buildings on High Street" | os_ngd_init_mapping_workflow → search_features |"""


def generate_mcp_toolset_config() -> Dict[str, Any]:
    """Generate MCP toolset configuration for tool search.

    This configuration is used with the mcp_toolset tool type
    to specify default defer_loading and per-tool overrides.

    Returns:
        Dict suitable for mcp_toolset configuration
    """
    # Per-tool overrides for always-loaded tools
    configs = {}
    for tool_name in ALWAYS_LOADED_TOOLS:
        configs[tool_name] = {"defer_loading": False}

    return {
        "type": "mcp_toolset",
        "mcp_server_name": "os-ngd-api",
        "default_config": {
            "defer_loading": True  # Default to deferred
        },
        "configs": configs  # Override for always-loaded tools
    }


__all__ = [
    "ToolCategory",
    "ToolConfig",
    "ALWAYS_LOADED_TOOLS",
    "DEFERRED_TOOLS",
    "STATEFUL_TOOLS",
    "EXTERNAL_API_TOOLS",
    "IDEMPOTENT_TOOLS",
    "TOOL_DESCRIPTIONS",
    "get_tool_config",
    "should_defer_loading",
    "get_tools_by_category",
    "get_always_loaded_tools",
    "get_deferred_tools",
    "get_tool_annotations",
    "get_tool_search_system_prompt",
    "generate_mcp_toolset_config",
]
