"""Evaluation Question Suite for OS/ONS MCP Server

This module defines a comprehensive set of test questions to evaluate the
effectiveness of the MCP server in answering user queries.

Questions are categorized by:
- Intent type (place_lookup, statistics, feature_search, etc.)
- Difficulty (basic, intermediate, advanced)
- Expected tool path and outcomes
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class Difficulty(str, Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class Intent(str, Enum):
    PLACE_LOOKUP = "place_lookup"
    STATISTICS = "statistics"
    AREA_COMPARISON = "area_comparison"
    FEATURE_SEARCH = "feature_search"
    BOUNDARY_FETCH = "boundary_fetch"
    INTERACTIVE_SELECTION = "interactive_selection"
    ROUTE_PLANNING = "route_planning"
    DATASET_DISCOVERY = "dataset_discovery"
    MULTI_STEP = "multi_step"


@dataclass
class ExpectedOutcome:
    """What we expect from a successful answer"""
    # Required fields in the response
    required_fields: List[str] = field(default_factory=list)
    # Expected values (partial match)
    expected_values: Dict[str, Any] = field(default_factory=dict)
    # Tools that MUST be called
    required_tools: List[str] = field(default_factory=list)
    # Tools that MUST NOT be called (anti-patterns)
    forbidden_tools: List[str] = field(default_factory=list)
    # Maximum acceptable tool calls
    max_tool_calls: Optional[int] = None
    # Keywords that should appear in the response
    required_keywords: List[str] = field(default_factory=list)
    # Keywords that should NOT appear (error indicators)
    forbidden_keywords: List[str] = field(default_factory=list)


@dataclass
class EvaluationQuestion:
    """A question for evaluation with expected outcomes"""
    id: str
    question: str
    intent: Intent
    difficulty: Difficulty
    description: str
    expected: ExpectedOutcome
    tags: List[str] = field(default_factory=list)


# =============================================================================
# BASIC QUESTIONS - Single tool, straightforward queries
# =============================================================================

BASIC_QUESTIONS = [
    # Place Lookups
    EvaluationQuestion(
        id="B001",
        question="Find Birmingham",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Simple city lookup - should return Birmingham's GSS code",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            forbidden_tools=["get_workflow_context", "list_collections", "search_features"],
            max_tool_calls=2,  # route_query + search_geographic_areas
            expected_values={"code": "E08000025"},
            required_keywords=["Birmingham", "E08000025"],
        ),
        tags=["place", "city", "core"],
    ),
    EvaluationQuestion(
        id="B002",
        question="Where is Manchester?",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Location query for major city",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            forbidden_tools=["get_workflow_context"],
            max_tool_calls=2,
            expected_values={"code": "E08000003"},
            required_keywords=["Manchester"],
        ),
        tags=["place", "city"],
    ),
    EvaluationQuestion(
        id="B003",
        question="What is the area code for Coventry?",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Explicit request for area code",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            forbidden_tools=["get_workflow_context"],
            max_tool_calls=2,
            expected_values={"code": "E08000026"},
            required_keywords=["E08000026", "Coventry"],
        ),
        tags=["place", "code"],
    ),
    EvaluationQuestion(
        id="B004",
        question="Find Leeds local authority",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Explicit local authority lookup",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            max_tool_calls=2,
            required_keywords=["Leeds"],
        ),
        tags=["place", "local_auth"],
    ),
    EvaluationQuestion(
        id="B005",
        question="Search for Edinburgh",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Scottish city lookup",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            max_tool_calls=2,
            required_keywords=["Edinburgh"],
        ),
        tags=["place", "scotland"],
    ),

    # Dataset Discovery
    EvaluationQuestion(
        id="B006",
        question="What datasets are available?",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="List available ONS datasets",
        expected=ExpectedOutcome(
            required_tools=["list_ons_datasets"],
            forbidden_tools=["get_workflow_context"],
            max_tool_calls=2,
            required_keywords=["dataset"],
        ),
        tags=["datasets", "ons"],
    ),
    EvaluationQuestion(
        id="B007",
        question="Show me wellbeing datasets",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Filtered dataset discovery",
        expected=ExpectedOutcome(
            required_tools=["list_ons_datasets"],
            max_tool_calls=2,
            required_keywords=["wellbeing"],
        ),
        tags=["datasets", "wellbeing"],
    ),

    # Interactive Selection
    EvaluationQuestion(
        id="B008",
        question="Open a map so I can select some areas",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.BASIC,
        description="Request for interactive map widget",
        expected=ExpectedOutcome(
            required_tools=["select_geographic_area"],
            max_tool_calls=2,
            required_keywords=["map", "select"],
        ),
        tags=["widget", "interactive"],
    ),
    EvaluationQuestion(
        id="B009",
        question="Let me pick local authorities on a map",
        intent=Intent.INTERACTIVE_SELECTION,
        difficulty=Difficulty.BASIC,
        description="Explicit interactive selection request",
        expected=ExpectedOutcome(
            required_tools=["select_geographic_area"],
            max_tool_calls=2,
        ),
        tags=["widget", "interactive"],
    ),
]

# =============================================================================
# INTERMEDIATE QUESTIONS - May require multiple tools or context
# =============================================================================

INTERMEDIATE_QUESTIONS = [
    # Statistics Queries
    EvaluationQuestion(
        id="I001",
        question="What is the wellbeing score for Birmingham?",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="Statistics for a named place - requires place lookup first",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas", "get_statistics"],
            forbidden_tools=["get_workflow_context"],
            max_tool_calls=4,
            required_keywords=["wellbeing", "Birmingham"],
        ),
        tags=["statistics", "wellbeing", "multi-step"],
    ),
    EvaluationQuestion(
        id="I002",
        question="Show me population data for Coventry",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="Population statistics query",
        expected=ExpectedOutcome(
            required_tools=["get_statistics"],
            max_tool_calls=4,
            required_keywords=["population", "Coventry"],
        ),
        tags=["statistics", "population"],
    ),
    EvaluationQuestion(
        id="I003",
        question="What are the house prices in Manchester?",
        intent=Intent.STATISTICS,
        difficulty=Difficulty.INTERMEDIATE,
        description="Housing statistics query",
        expected=ExpectedOutcome(
            required_tools=["get_statistics"],
            max_tool_calls=4,
            required_keywords=["house", "price", "Manchester"],
        ),
        tags=["statistics", "housing"],
    ),

    # Area Comparisons
    EvaluationQuestion(
        id="I004",
        question="Compare wellbeing between Birmingham and Manchester",
        intent=Intent.AREA_COMPARISON,
        difficulty=Difficulty.INTERMEDIATE,
        description="Direct comparison of two cities",
        expected=ExpectedOutcome(
            required_tools=["compare_areas"],
            max_tool_calls=5,
            required_keywords=["Birmingham", "Manchester"],
        ),
        tags=["comparison", "wellbeing"],
    ),
    EvaluationQuestion(
        id="I005",
        question="Which is better, Leeds or Sheffield?",
        intent=Intent.AREA_COMPARISON,
        difficulty=Difficulty.INTERMEDIATE,
        description="Implicit comparison query",
        expected=ExpectedOutcome(
            required_tools=["compare_areas"],
            max_tool_calls=5,
            required_keywords=["Leeds", "Sheffield"],
        ),
        tags=["comparison"],
    ),

    # Boundary Queries
    EvaluationQuestion(
        id="I006",
        question="Get the boundary of Birmingham",
        intent=Intent.BOUNDARY_FETCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="Boundary geometry request",
        expected=ExpectedOutcome(
            required_tools=["fetch_boundaries"],
            max_tool_calls=4,
            required_keywords=["boundary", "Birmingham"],
        ),
        tags=["boundary", "geojson"],
    ),
    EvaluationQuestion(
        id="I007",
        question="Show me the shape of Coventry council area",
        intent=Intent.BOUNDARY_FETCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="Alternative boundary request phrasing",
        expected=ExpectedOutcome(
            required_tools=["fetch_boundaries"],
            max_tool_calls=4,
            required_keywords=["Coventry"],
        ),
        tags=["boundary"],
    ),

    # Feature Search (OS NGD)
    EvaluationQuestion(
        id="I008",
        question="Find cinemas in Leeds",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="Feature search requiring OS NGD workflow",
        expected=ExpectedOutcome(
            required_tools=["get_workflow_context", "search_features"],
            forbidden_tools=[],  # Workflow context IS needed here
            max_tool_calls=6,
            required_keywords=["cinema"],
        ),
        tags=["features", "land_use", "os_ngd"],
    ),
    EvaluationQuestion(
        id="I009",
        question="Show buildings near Birmingham city centre",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="Building feature search",
        expected=ExpectedOutcome(
            required_tools=["get_workflow_context", "search_features"],
            max_tool_calls=6,
            required_keywords=["building"],
        ),
        tags=["features", "buildings", "os_ngd"],
    ),
    EvaluationQuestion(
        id="I010",
        question="Find all schools in Manchester",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.INTERMEDIATE,
        description="Educational facility search",
        expected=ExpectedOutcome(
            required_tools=["get_workflow_context", "search_features"],
            max_tool_calls=6,
            required_keywords=["school"],
        ),
        tags=["features", "education", "os_ngd"],
    ),

    # Route Planning
    EvaluationQuestion(
        id="I011",
        question="Plan a route from Birmingham to Manchester",
        intent=Intent.ROUTE_PLANNING,
        difficulty=Difficulty.INTERMEDIATE,
        description="Route planning between two cities",
        expected=ExpectedOutcome(
            required_tools=["plan_route"],
            max_tool_calls=4,
            required_keywords=["route"],
        ),
        tags=["routing"],
    ),
    EvaluationQuestion(
        id="I012",
        question="How do I get from Coventry to London?",
        intent=Intent.ROUTE_PLANNING,
        difficulty=Difficulty.INTERMEDIATE,
        description="Direction query",
        expected=ExpectedOutcome(
            required_tools=["plan_route"],
            max_tool_calls=4,
        ),
        tags=["routing", "directions"],
    ),
]

# =============================================================================
# ADVANCED QUESTIONS - Complex multi-step workflows
# =============================================================================

ADVANCED_QUESTIONS = [
    EvaluationQuestion(
        id="A001",
        question="Find Birmingham, get its wellbeing statistics, and compare it with Manchester",
        intent=Intent.MULTI_STEP,
        difficulty=Difficulty.ADVANCED,
        description="Multi-step query combining place lookup, statistics, and comparison",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas", "get_statistics", "compare_areas"],
            max_tool_calls=8,
            required_keywords=["Birmingham", "Manchester", "wellbeing"],
        ),
        tags=["multi-step", "comparison", "statistics"],
    ),
    EvaluationQuestion(
        id="A002",
        question="Show me all the hospitals in the Birmingham area and their locations on a map",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.ADVANCED,
        description="Feature search with mapping",
        expected=ExpectedOutcome(
            required_tools=["get_workflow_context", "search_features"],
            max_tool_calls=8,
            required_keywords=["hospital", "Birmingham"],
        ),
        tags=["features", "healthcare", "mapping"],
    ),
    EvaluationQuestion(
        id="A003",
        question="Which West Midlands council has the highest life satisfaction?",
        intent=Intent.MULTI_STEP,
        difficulty=Difficulty.ADVANCED,
        description="Regional comparison requiring multiple lookups",
        expected=ExpectedOutcome(
            required_tools=["get_statistics"],
            max_tool_calls=10,
            required_keywords=["life", "satisfaction"],
        ),
        tags=["statistics", "regional", "ranking"],
    ),
    EvaluationQuestion(
        id="A004",
        question="Find all railway stations within 5km of Birmingham New Street",
        intent=Intent.FEATURE_SEARCH,
        difficulty=Difficulty.ADVANCED,
        description="Spatial feature query with distance constraint",
        expected=ExpectedOutcome(
            required_tools=["get_workflow_context", "search_features"],
            max_tool_calls=8,
            required_keywords=["railway", "station"],
        ),
        tags=["features", "transport", "spatial"],
    ),
    EvaluationQuestion(
        id="A005",
        question="Compare census data between urban and rural areas in the West Midlands",
        intent=Intent.MULTI_STEP,
        difficulty=Difficulty.ADVANCED,
        description="Complex regional census comparison",
        expected=ExpectedOutcome(
            required_tools=["list_ons_datasets", "get_statistics"],
            max_tool_calls=10,
            required_keywords=["census"],
        ),
        tags=["census", "comparison", "regional"],
    ),
]

# =============================================================================
# EDGE CASES AND ERROR HANDLING
# =============================================================================

EDGE_CASE_QUESTIONS = [
    EvaluationQuestion(
        id="E001",
        question="Find Atlantis",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Non-existent place - should handle gracefully",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            max_tool_calls=2,
            forbidden_keywords=["error", "exception", "traceback"],
        ),
        tags=["error_handling", "edge_case"],
    ),
    EvaluationQuestion(
        id="E002",
        question="",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Empty query - should handle gracefully",
        expected=ExpectedOutcome(
            forbidden_keywords=["traceback", "exception"],
        ),
        tags=["error_handling", "edge_case"],
    ),
    EvaluationQuestion(
        id="E003",
        question="SELECT * FROM users; DROP TABLE users;--",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="SQL injection attempt - should be blocked by guardrails",
        expected=ExpectedOutcome(
            forbidden_keywords=["SELECT", "DROP", "executed"],
        ),
        tags=["security", "injection"],
    ),
    EvaluationQuestion(
        id="E004",
        question="Find the <script>alert('xss')</script> area",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="XSS attempt - should be sanitized",
        expected=ExpectedOutcome(
            forbidden_keywords=["<script>", "alert"],
        ),
        tags=["security", "xss"],
    ),
    EvaluationQuestion(
        id="E005",
        question="asdfghjkl qwertyuiop zxcvbnm",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Gibberish query - should handle gracefully",
        expected=ExpectedOutcome(
            forbidden_keywords=["traceback", "exception"],
        ),
        tags=["error_handling", "gibberish"],
    ),
]

# =============================================================================
# AMBIGUOUS QUESTIONS - Tests intent classification
# =============================================================================

AMBIGUOUS_QUESTIONS = [
    EvaluationQuestion(
        id="X001",
        question="Birmingham",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.BASIC,
        description="Single word - should infer place lookup",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            max_tool_calls=2,
            required_keywords=["Birmingham"],
        ),
        tags=["ambiguous", "minimal"],
    ),
    EvaluationQuestion(
        id="X002",
        question="population",
        intent=Intent.DATASET_DISCOVERY,
        difficulty=Difficulty.BASIC,
        description="Single word statistics term",
        expected=ExpectedOutcome(
            max_tool_calls=3,
        ),
        tags=["ambiguous", "minimal"],
    ),
    EvaluationQuestion(
        id="X003",
        question="Tell me about Birmingham",
        intent=Intent.PLACE_LOOKUP,
        difficulty=Difficulty.INTERMEDIATE,
        description="Vague query about a place",
        expected=ExpectedOutcome(
            required_tools=["search_geographic_areas"],
            max_tool_calls=4,
            required_keywords=["Birmingham"],
        ),
        tags=["ambiguous", "vague"],
    ),
]

# =============================================================================
# ALL QUESTIONS
# =============================================================================

ALL_QUESTIONS = (
    BASIC_QUESTIONS +
    INTERMEDIATE_QUESTIONS +
    ADVANCED_QUESTIONS +
    EDGE_CASE_QUESTIONS +
    AMBIGUOUS_QUESTIONS
)

# Question lookup by ID
QUESTIONS_BY_ID = {q.id: q for q in ALL_QUESTIONS}

# Questions by category
QUESTIONS_BY_INTENT = {}
for q in ALL_QUESTIONS:
    if q.intent not in QUESTIONS_BY_INTENT:
        QUESTIONS_BY_INTENT[q.intent] = []
    QUESTIONS_BY_INTENT[q.intent].append(q)

QUESTIONS_BY_DIFFICULTY = {}
for q in ALL_QUESTIONS:
    if q.difficulty not in QUESTIONS_BY_DIFFICULTY:
        QUESTIONS_BY_DIFFICULTY[q.difficulty] = []
    QUESTIONS_BY_DIFFICULTY[q.difficulty].append(q)


def get_questions(
    intent: Optional[Intent] = None,
    difficulty: Optional[Difficulty] = None,
    tags: Optional[List[str]] = None,
) -> List[EvaluationQuestion]:
    """Get questions filtered by criteria"""
    questions = ALL_QUESTIONS

    if intent:
        questions = [q for q in questions if q.intent == intent]

    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]

    if tags:
        questions = [q for q in questions if any(t in q.tags for t in tags)]

    return questions


def get_question_summary() -> Dict[str, Any]:
    """Get summary statistics about the question suite"""
    return {
        "total_questions": len(ALL_QUESTIONS),
        "by_difficulty": {
            d.value: len([q for q in ALL_QUESTIONS if q.difficulty == d])
            for d in Difficulty
        },
        "by_intent": {
            i.value: len([q for q in ALL_QUESTIONS if q.intent == i])
            for i in Intent
        },
        "all_tags": sorted(set(t for q in ALL_QUESTIONS for t in q.tags)),
    }


if __name__ == "__main__":
    import json
    summary = get_question_summary()
    print(json.dumps(summary, indent=2))
    print(f"\nTotal: {summary['total_questions']} questions")
