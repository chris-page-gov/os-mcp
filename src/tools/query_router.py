"""Query Router for OS/ONS MCP Server

This module provides intelligent query routing to help Claude select the right
tool for each user query. The route_query tool should be called FIRST for any
natural language query to determine the appropriate approach.

The router classifies queries into intents:
- place_lookup: Finding places by name (→ search_geographic_areas)
- statistics: Getting statistics for areas (→ get_statistics)
- area_comparison: Comparing multiple areas (→ compare_areas)
- feature_search: Finding mapping features (→ OS NGD workflow)
- boundary_fetch: Getting boundary geometry (→ fetch_boundaries)
- interactive_selection: User wants to pick on map (→ select_geographic_area)
- route_planning: Planning a journey (→ plan_route)
- dataset_discovery: Exploring available datasets (→ list_ons_datasets)
"""

import json
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class QueryIntent(str, Enum):
    """Classification of user query intents"""
    PLACE_LOOKUP = "place_lookup"
    STATISTICS = "statistics"
    AREA_COMPARISON = "area_comparison"
    FEATURE_SEARCH = "feature_search"
    BOUNDARY_FETCH = "boundary_fetch"
    INTERACTIVE_SELECTION = "interactive_selection"
    ROUTE_PLANNING = "route_planning"
    DATASET_DISCOVERY = "dataset_discovery"
    UNKNOWN = "unknown"


@dataclass
class RoutingResult:
    """Result of query routing"""
    intent: QueryIntent
    confidence: float
    recommended_tool: str
    recommended_parameters: Dict[str, Any]
    explanation: str
    alternative_tools: List[str]
    workflow_steps: List[str]


# Patterns for intent classification
PLACE_LOOKUP_PATTERNS = [
    r'\b(find|search|locate|where is|look up|get|show me)\b.*\b(birmingham|manchester|london|coventry|leeds|liverpool|sheffield|bristol|edinburgh|glasgow|cardiff|belfast|city|town|council|authority|district|borough|area)\b',
    r'\b(birmingham|manchester|london|coventry|leeds|liverpool|sheffield|bristol|edinburgh|glasgow|cardiff|belfast)\b',
    r'\barea code\b',
    r'\bgss code\b',
    r'\bwhat is the code for\b',
    r'\bfind.*council\b',
    r'\blocal authority.*for\b',
]

STATISTICS_PATTERNS = [
    r'\b(statistics|stats|data|wellbeing|population|house prices?|gdp|life expectancy|census|employment|health)\b.*\b(for|in|of)\b',
    r'\bget (statistics|stats|data)\b',
    r'\b(wellbeing|happiness|anxiety|life satisfaction)\b',
    r'\bhow (many|much)\b.*\bin\b',
]

COMPARISON_PATTERNS = [
    r'\bcompare\b',
    r'\bcomparison\b',
    r'\bvs\.?\b',
    r'\bversus\b',
    r'\bbetter than\b',
    r'\bworse than\b',
    r'\branking\b',
    r'\brank\b',
    r'\bbetween.*and\b',
    r'\bwhich is better\b',
    r'\bor\b.*\bbetter\b',
]

FEATURE_SEARCH_PATTERNS = [
    r'\b(buildings?|roads?|streets?|railway|rail station|cinema|school|hospital|park|shop|restaurant|pub|church|museum|library|hotel)\b',
    r'\bfind (all|the)\b.*\bnear\b',
    r'\bland use\b',
    r'\bwhat\'s (at|near)\b',
    r'\bshow.*on map\b',
    r'\bmapping data\b',
    r'\bos ngd\b',
    r'\bfeatures?\b',
]

BOUNDARY_PATTERNS = [
    r'\bboundary\b',
    r'\bboundaries\b',
    r'\bgeojson\b',
    r'\bpolygon\b',
    r'\bshape\b',
    r'\boutline\b',
    r'\bgeometry\b',
]

INTERACTIVE_PATTERNS = [
    r'\bselect\b.*\bmap\b',
    r'\bmap\b.*\bselect\b',
    r'\bopen\b.*\bmap\b',
    r'\binteractive\b',
    r'\blet me (choose|pick|select)\b',
    r'\bclick\b.*\bareas?\b',
    r'\bshow.*widget\b',
    r'\bpick\b.*\bareas?\b',
    r'\bselect\b.*\bareas?\b',
    r'\bchoose\b.*\bareas?\b',
]

ROUTE_PATTERNS = [
    r'\broute\b',
    r'\bdirections?\b',
    r'\bhow (do i|to|can i) get\b',
    r'\bfrom\b.*\bto\b',
    r'\bjourney\b',
    r'\bnavigat\w+\b',
    r'\bdriving\b',
    r'\bwalking\b',
    r'\bget from\b',
    r'\btravel\b.*\bto\b',
]

DATASET_PATTERNS = [
    r'\bwhat (datasets?|data) (are|is) available\b',
    r'\blist.*datasets?\b',
    r'\bbrowse.*data\b',
    r'\bwhat (statistics|stats) can\b',
    r'\bavailable.*data\b',
    r'\bdatasets?\b',
    r'\bshow.*datasets?\b',
]


def _match_patterns(query: str, patterns: List[str]) -> float:
    """Calculate match score for a list of patterns"""
    query_lower = query.lower()
    matches = 0
    for pattern in patterns:
        if re.search(pattern, query_lower, re.IGNORECASE):
            matches += 1
    return min(matches / max(len(patterns) * 0.3, 1), 1.0)  # Cap at 1.0


def _extract_place_name(query: str) -> Optional[str]:
    """Extract a likely place name from the query"""
    # Known UK places
    known_places = [
        'birmingham', 'manchester', 'london', 'coventry', 'leeds', 'liverpool',
        'sheffield', 'bristol', 'edinburgh', 'glasgow', 'cardiff', 'belfast',
        'nottingham', 'newcastle', 'leicester', 'brighton', 'southampton',
        'portsmouth', 'oxford', 'cambridge', 'york', 'bath', 'exeter',
        'norwich', 'plymouth', 'stoke', 'wolverhampton', 'derby', 'swansea',
        'aberdeen', 'dundee', 'reading', 'luton', 'bolton', 'sunderland',
    ]

    query_lower = query.lower()
    for place in known_places:
        if place in query_lower:
            return place.title()

    # Try to extract capitalized words that might be place names
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
    for word in words:
        if word.lower() not in ['find', 'search', 'get', 'show', 'where', 'what', 'the']:
            return word

    return None


def _classify_query(query: str) -> Tuple[QueryIntent, float, Dict[str, Any]]:
    """Classify a query into an intent with confidence score"""

    query_lower = query.lower()

    # Calculate scores for each intent
    scores = {
        QueryIntent.PLACE_LOOKUP: _match_patterns(query, PLACE_LOOKUP_PATTERNS),
        QueryIntent.STATISTICS: _match_patterns(query, STATISTICS_PATTERNS),
        QueryIntent.AREA_COMPARISON: _match_patterns(query, COMPARISON_PATTERNS),
        QueryIntent.FEATURE_SEARCH: _match_patterns(query, FEATURE_SEARCH_PATTERNS),
        QueryIntent.BOUNDARY_FETCH: _match_patterns(query, BOUNDARY_PATTERNS),
        QueryIntent.INTERACTIVE_SELECTION: _match_patterns(query, INTERACTIVE_PATTERNS),
        QueryIntent.ROUTE_PLANNING: _match_patterns(query, ROUTE_PATTERNS),
        QueryIntent.DATASET_DISCOVERY: _match_patterns(query, DATASET_PATTERNS),
    }

    # Extract place name for potential boosting
    place_name = _extract_place_name(query)

    # Priority rules - certain patterns should take precedence

    # 1. Comparison queries take precedence
    if re.search(r'\b(compare|vs\.?|versus|between.*and)\b', query_lower):
        scores[QueryIntent.AREA_COMPARISON] = max(scores[QueryIntent.AREA_COMPARISON], 0.9)

    # 2. Feature-specific words indicate OS NGD search (includes plurals via regex)
    # These words OVERRIDE place lookup - user is asking about mapping features, not the place itself
    feature_patterns = [
        r'\bcinemas?\b', r'\bbuildings?\b', r'\broads?\b', r'\bschools?\b',
        r'\bhospitals?\b', r'\bparks?\b', r'\bshops?\b', r'\brestaurants?\b',
        r'\bpubs?\b', r'\bchurch(es)?\b', r'\bmuseums?\b', r'\blibrari(es|y)\b',
        r'\bhotels?\b', r'\bstations?\b', r'\brailway\b', r'\bsupermarkets?\b',
        r'\boffices?\b', r'\bfactori(es|y)\b', r'\bwarehouses?\b',
    ]
    has_feature_word = False
    for pattern in feature_patterns:
        if re.search(pattern, query_lower):
            has_feature_word = True
            scores[QueryIntent.FEATURE_SEARCH] = 0.95  # High confidence
            # REDUCE place_lookup since we're looking for features, not the place
            scores[QueryIntent.PLACE_LOOKUP] = min(scores[QueryIntent.PLACE_LOOKUP], 0.3)
            break

    # 3. Statistics keywords take precedence over place lookup
    stats_words = ['wellbeing', 'population', 'statistics', 'stats', 'census',
                   'house price', 'gdp', 'employment', 'life expectancy', 'data for']
    for word in stats_words:
        if word in query_lower:
            scores[QueryIntent.STATISTICS] = max(scores[QueryIntent.STATISTICS], 0.9)
            scores[QueryIntent.PLACE_LOOKUP] = min(scores[QueryIntent.PLACE_LOOKUP], 0.4)
            break

    # 4. Interactive selection keywords take precedence
    interactive_keywords = [
        r'\bopen\b.*\bmap\b',
        r'\bmap\b.*\bselect\b',
        r'\bselect\b.*\bareas?\b',
        r'\bpick\b.*\bareas?\b',
        r'\bchoose\b.*\bareas?\b',
        r'\binteractive\b',
        r'\bclick\b.*\bselect\b',
        r'\blet me\b.*\b(select|pick|choose)\b',
    ]
    for pattern in interactive_keywords:
        if re.search(pattern, query_lower):
            scores[QueryIntent.INTERACTIVE_SELECTION] = 0.95
            scores[QueryIntent.PLACE_LOOKUP] = min(scores[QueryIntent.PLACE_LOOKUP], 0.3)
            break

    # 5. Route planning keywords - "from X to Y" patterns
    route_keywords = [
        r'\bfrom\b.*\bto\b',
        r'\broute\b',
        r'\bhow (do i|to|can i) get\b',
        r'\bdirections?\b',
        r'\bjourney\b',
    ]
    for pattern in route_keywords:
        if re.search(pattern, query_lower):
            scores[QueryIntent.ROUTE_PLANNING] = 0.9
            scores[QueryIntent.PLACE_LOOKUP] = min(scores[QueryIntent.PLACE_LOOKUP], 0.3)
            break

    # 6. Comparison keywords - "compare", "vs", "which is better"
    comparison_keywords = [
        r'\bcompare\b',
        r'\bvs\.?\b',
        r'\bwhich is better\b',
        r'\bbetween\b.*\band\b',
    ]
    for pattern in comparison_keywords:
        if re.search(pattern, query_lower):
            scores[QueryIntent.AREA_COMPARISON] = 0.95
            scores[QueryIntent.STATISTICS] = min(scores[QueryIntent.STATISTICS], 0.5)
            scores[QueryIntent.PLACE_LOOKUP] = min(scores[QueryIntent.PLACE_LOOKUP], 0.3)
            break

    # 7. Boundary keywords - "boundary", "shape", "outline"
    boundary_keywords = [
        r'\bboundary\b',
        r'\bboundaries\b',
        r'\bshape\b',
        r'\boutline\b',
        r'\bgeojson\b',
        r'\bpolygon\b',
    ]
    for pattern in boundary_keywords:
        if re.search(pattern, query_lower):
            scores[QueryIntent.BOUNDARY_FETCH] = 0.9
            scores[QueryIntent.PLACE_LOOKUP] = min(scores[QueryIntent.PLACE_LOOKUP], 0.3)
            break

    # 8. Dataset discovery - explicit "datasets" keyword
    if re.search(r'\bdatasets?\b', query_lower):
        scores[QueryIntent.DATASET_DISCOVERY] = 0.9
        scores[QueryIntent.STATISTICS] = min(scores[QueryIntent.STATISTICS], 0.5)

    # 9. Only boost place_lookup if no other strong signals
    if place_name and not has_feature_word:
        # Don't boost if we have other high-confidence signals
        other_high = any(
            scores[intent] >= 0.5
            for intent in [
                QueryIntent.FEATURE_SEARCH,
                QueryIntent.AREA_COMPARISON,
                QueryIntent.INTERACTIVE_SELECTION,
                QueryIntent.ROUTE_PLANNING,
                QueryIntent.BOUNDARY_FETCH,
                QueryIntent.DATASET_DISCOVERY,
            ]
        )
        if not other_high:
            scores[QueryIntent.PLACE_LOOKUP] = max(scores[QueryIntent.PLACE_LOOKUP], 0.8)

    # Find highest scoring intent
    best_intent = max(scores, key=lambda k: scores[k])
    best_score = scores[best_intent]

    # If no clear match, default to UNKNOWN
    if best_score < 0.3:
        return QueryIntent.UNKNOWN, 0.0, {}

    # Extract parameters based on intent
    params: Dict[str, Any] = {}
    if best_intent == QueryIntent.PLACE_LOOKUP and place_name:
        params = {"query": place_name, "level": "local_auth"}
    elif best_intent == QueryIntent.FEATURE_SEARCH and place_name:
        # Include place context for feature searches
        params = {"location_hint": place_name}
    elif best_intent == QueryIntent.AREA_COMPARISON:
        # Try to extract multiple place names
        places = []
        for place in ['birmingham', 'manchester', 'london', 'coventry', 'leeds', 'liverpool']:
            if place in query_lower:
                places.append(place.title())
        if places:
            params = {"areas": places}

    return best_intent, best_score, params


def _get_tool_for_intent(intent: QueryIntent) -> Tuple[str, List[str], str]:
    """Get the recommended tool and workflow for an intent"""

    INTENT_TO_TOOL = {
        QueryIntent.PLACE_LOOKUP: (
            "search_geographic_areas",
            ["search_geographic_areas"],
            "Use search_geographic_areas to find UK places by name. Returns area codes (GSS codes) for use with other tools."
        ),
        QueryIntent.STATISTICS: (
            "get_statistics",
            ["search_geographic_areas", "get_statistics"],
            "First find area codes with search_geographic_areas, then get_statistics for those codes."
        ),
        QueryIntent.AREA_COMPARISON: (
            "compare_areas",
            ["search_geographic_areas", "compare_areas"],
            "First find area codes with search_geographic_areas, then compare_areas to compare statistics."
        ),
        QueryIntent.FEATURE_SEARCH: (
            "search_features",
            ["os_ngd_init_mapping_workflow", "fetch_detailed_collections", "search_features"],
            "For OS mapping features (buildings, roads, etc.), use the OS NGD workflow: initialize mapping workflow, get queryables, then search."
        ),
        QueryIntent.BOUNDARY_FETCH: (
            "fetch_boundaries",
            ["search_geographic_areas", "fetch_boundaries"],
            "First find area codes with search_geographic_areas, then fetch_boundaries for GeoJSON geometry."
        ),
        QueryIntent.INTERACTIVE_SELECTION: (
            "select_geographic_area",
            ["select_geographic_area"],
            "Opens an interactive map widget where you can click to select areas."
        ),
        QueryIntent.ROUTE_PLANNING: (
            "plan_route",
            ["plan_route"],
            "Opens route planner widget. You can specify start/end coordinates or let user click on map."
        ),
        QueryIntent.DATASET_DISCOVERY: (
            "list_ons_datasets",
            ["list_ons_datasets"],
            "Lists available ONS datasets. Use category parameter to filter (wellbeing, economy, housing, etc.)."
        ),
        QueryIntent.UNKNOWN: (
            "search_geographic_areas",
            ["search_geographic_areas"],
            "Intent unclear. Starting with place lookup as it's the most common need. If this isn't right, try being more specific."
        ),
    }

    return INTENT_TO_TOOL.get(intent, INTENT_TO_TOOL[QueryIntent.UNKNOWN])


def _get_alternative_tools(intent: QueryIntent) -> List[str]:
    """Get alternative tools that might also be relevant"""

    ALTERNATIVES = {
        QueryIntent.PLACE_LOOKUP: ["select_geographic_area", "fetch_boundaries"],
        QueryIntent.STATISTICS: ["list_ons_datasets", "compare_areas"],
        QueryIntent.AREA_COMPARISON: ["get_statistics"],
        QueryIntent.FEATURE_SEARCH: ["inspect_feature", "get_feature"],
        QueryIntent.BOUNDARY_FETCH: ["select_geographic_area"],
        QueryIntent.INTERACTIVE_SELECTION: ["search_geographic_areas"],
        QueryIntent.ROUTE_PLANNING: ["get_route_network"],
        QueryIntent.DATASET_DISCOVERY: ["get_dataset_info"],
        QueryIntent.UNKNOWN: ["search_geographic_areas", "route_query"],
    }

    return ALTERNATIVES.get(intent, [])


async def route_query(query: str) -> str:
    """Route a natural language query to the appropriate tool.

    THIS TOOL SHOULD BE CALLED FIRST for any user query. It analyzes the query
    intent and recommends which tool to use, with parameters and workflow steps.

    Args:
        query: The user's natural language query (e.g., "Find Birmingham",
               "What's the population of Coventry?", "Show cinemas near Leeds")

    Returns:
        JSON with routing recommendation:
        {
            "intent": "place_lookup",
            "confidence": 0.95,
            "recommended_tool": "search_geographic_areas",
            "recommended_parameters": {"query": "Birmingham", "level": "local_auth"},
            "explanation": "Use search_geographic_areas to find UK places by name...",
            "workflow_steps": ["search_geographic_areas"],
            "alternative_tools": ["select_geographic_area", "fetch_boundaries"]
        }

    Examples:
        >>> route_query("Find Birmingham")
        → Recommends: search_geographic_areas(query="Birmingham", level="local_auth")

        >>> route_query("What's the wellbeing like in Coventry?")
        → Recommends: search_geographic_areas first, then get_statistics

        >>> route_query("Find cinemas in Leeds")
        → Recommends: OS NGD workflow (os_ngd_init_mapping_workflow → search_features)

    Intent Classification:
        - place_lookup: "Find Birmingham", "Where is Manchester" → search_geographic_areas
        - statistics: "Wellbeing in Coventry", "Population of Leeds" → get_statistics
        - area_comparison: "Compare Birmingham and Manchester" → compare_areas
        - feature_search: "Find cinemas", "Show buildings" → OS NGD mapping workflow
        - boundary_fetch: "Get boundary of Birmingham" → fetch_boundaries
        - interactive_selection: "Let me select on a map" → select_geographic_area
        - route_planning: "Route from A to B" → plan_route
        - dataset_discovery: "What datasets are available?" → list_ons_datasets
    """

    if not query or not query.strip():
        return json.dumps({
            "error": "Empty query provided",
            "hint": "Please provide a natural language query like 'Find Birmingham' or 'Show wellbeing statistics for Coventry'"
        })

    query = query.strip()

    # Classify the query
    intent, confidence, extracted_params = _classify_query(query)

    # Get tool recommendation
    tool, workflow, explanation = _get_tool_for_intent(intent)
    alternatives = _get_alternative_tools(intent)

    # Build result
    result = {
        "query": query,
        "intent": intent.value,
        "confidence": round(confidence, 2),
        "recommended_tool": tool,
        "recommended_parameters": extracted_params,
        "explanation": explanation,
        "workflow_steps": workflow,
        "alternative_tools": alternatives,
        "guidance": _get_guidance_for_intent(intent),
    }

    logger.info(f"Routed query '{query}' to {tool} (intent={intent.value}, confidence={confidence:.2f})")

    return json.dumps(result, indent=2)


def _get_guidance_for_intent(intent: QueryIntent) -> str:
    """Get additional guidance based on intent"""

    GUIDANCE = {
        QueryIntent.PLACE_LOOKUP: (
            "For place lookups, search_geographic_areas is the fastest path. "
            "It searches the ONS Geography database directly - no workflow initialization needed. "
            "DO NOT use OS NGD collections (gnm-fts-namedarea, etc.) for finding cities/towns."
        ),
        QueryIntent.STATISTICS: (
            "For statistics, first get the area code(s) using search_geographic_areas, "
            "then call get_statistics with the area_codes parameter. "
            "Use list_ons_datasets to discover available datasets if unsure what's available."
        ),
        QueryIntent.AREA_COMPARISON: (
            "For comparisons, first get area codes for all areas you want to compare, "
            "then use compare_areas with the dataset_id and area_codes parameters."
        ),
        QueryIntent.FEATURE_SEARCH: (
            "For OS mapping features (buildings, roads, land use), you MUST use the 2-step workflow: "
            "1) os_ngd_init_mapping_workflow, 2) fetch_detailed_collections, 3) search_features. "
            "This is the ONLY case where the os_ngd_ tools are required."
        ),
        QueryIntent.BOUNDARY_FETCH: (
            "For boundary geometry, first get the area code using search_geographic_areas, "
            "then call fetch_boundaries with the codes parameter."
        ),
        QueryIntent.INTERACTIVE_SELECTION: (
            "select_geographic_area opens an interactive map widget. "
            "Users can click to select areas. The widget returns area codes when done."
        ),
        QueryIntent.ROUTE_PLANNING: (
            "plan_route opens the route planner widget. You can optionally provide "
            "start_lat/lng and end_lat/lng coordinates, or let the user click on the map."
        ),
        QueryIntent.DATASET_DISCOVERY: (
            "list_ons_datasets shows available ONS datasets. "
            "Use category='wellbeing'/'economy'/'housing'/'census' to filter."
        ),
        QueryIntent.UNKNOWN: (
            "Query intent is unclear. Try being more specific. Examples:\n"
            "- 'Find Birmingham' for place lookup\n"
            "- 'Wellbeing in Coventry' for statistics\n"
            "- 'Compare Manchester and Leeds' for comparison\n"
            "- 'Find cinemas near Birmingham' for feature search"
        ),
    }

    return GUIDANCE.get(intent, GUIDANCE[QueryIntent.UNKNOWN])


# For direct testing
if __name__ == "__main__":
    import asyncio

    test_queries = [
        "Find Birmingham",
        "Where is Manchester",
        "What's the wellbeing like in Coventry?",
        "Compare Birmingham and Manchester",
        "Show me cinemas near Leeds",
        "Find all buildings in this area",
        "Get the boundary of Coventry",
        "Let me select areas on a map",
        "How do I get from Birmingham to Manchester?",
        "What datasets are available?",
    ]

    async def test():
        for q in test_queries:
            result = await route_query(q)
            print(f"\nQuery: {q}")
            print(result)

    asyncio.run(test())
