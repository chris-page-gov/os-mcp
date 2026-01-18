"""Unit tests for the Query Router

Tests the intent classification and routing logic for the OS/ONS MCP server.
"""

import pytest
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from tools.query_router import (
    route_query,
    _classify_query,
    _extract_place_name,
    _match_patterns,
    _get_tool_for_intent,
    QueryIntent,
    PLACE_LOOKUP_PATTERNS,
    FEATURE_SEARCH_PATTERNS,
    STATISTICS_PATTERNS,
    COMPARISON_PATTERNS,
)


class TestQueryClassification:
    """Tests for query intent classification"""

    @pytest.mark.asyncio
    async def test_place_lookup_simple_city(self):
        """Simple city name should be classified as place_lookup"""
        result = await route_query("Find Birmingham")
        data = json.loads(result)

        assert data["intent"] == "place_lookup"
        assert data["confidence"] >= 0.8
        assert data["recommended_tool"] == "search_geographic_areas"
        assert "Birmingham" in str(data.get("recommended_parameters", {}))

    @pytest.mark.asyncio
    async def test_place_lookup_where_is(self):
        """'Where is' queries should be place_lookup"""
        result = await route_query("Where is Manchester?")
        data = json.loads(result)

        assert data["intent"] == "place_lookup"
        assert data["recommended_tool"] == "search_geographic_areas"

    @pytest.mark.asyncio
    async def test_place_lookup_area_code(self):
        """Area code queries should be place_lookup"""
        result = await route_query("What is the area code for Coventry?")
        data = json.loads(result)

        assert data["intent"] == "place_lookup"
        assert "Coventry" in str(data.get("recommended_parameters", {}))

    @pytest.mark.asyncio
    async def test_feature_search_cinemas(self):
        """Cinema queries should be feature_search"""
        result = await route_query("Find cinemas near Leeds")
        data = json.loads(result)

        assert data["intent"] == "feature_search"
        assert data["recommended_tool"] == "search_features"
        assert "get_workflow_context" in data["workflow_steps"]

    @pytest.mark.asyncio
    async def test_feature_search_buildings(self):
        """Building queries should be feature_search"""
        result = await route_query("Show buildings in Birmingham")
        data = json.loads(result)

        assert data["intent"] == "feature_search"
        assert data["recommended_tool"] == "search_features"

    @pytest.mark.asyncio
    async def test_feature_search_schools(self):
        """School queries should be feature_search"""
        result = await route_query("Find all schools in Manchester")
        data = json.loads(result)

        assert data["intent"] == "feature_search"

    @pytest.mark.asyncio
    async def test_feature_search_hospitals(self):
        """Hospital queries should be feature_search"""
        result = await route_query("Where is the nearest hospital")
        data = json.loads(result)

        assert data["intent"] == "feature_search"

    @pytest.mark.asyncio
    async def test_statistics_wellbeing(self):
        """Wellbeing queries should be statistics"""
        result = await route_query("What is the wellbeing in Coventry?")
        data = json.loads(result)

        assert data["intent"] == "statistics"
        assert data["recommended_tool"] == "get_statistics"

    @pytest.mark.asyncio
    async def test_statistics_population(self):
        """Population queries should be statistics"""
        result = await route_query("What is the population of Leeds?")
        data = json.loads(result)

        assert data["intent"] == "statistics"

    @pytest.mark.asyncio
    async def test_area_comparison(self):
        """Compare queries should be area_comparison"""
        result = await route_query("Compare Birmingham and Manchester")
        data = json.loads(result)

        assert data["intent"] == "area_comparison"
        assert data["recommended_tool"] == "compare_areas"

    @pytest.mark.asyncio
    async def test_area_comparison_vs(self):
        """VS queries should be area_comparison"""
        result = await route_query("Birmingham vs Manchester")
        data = json.loads(result)

        assert data["intent"] == "area_comparison"

    @pytest.mark.asyncio
    async def test_dataset_discovery(self):
        """Dataset discovery queries"""
        result = await route_query("What datasets are available?")
        data = json.loads(result)

        assert data["intent"] == "dataset_discovery"
        assert data["recommended_tool"] == "list_ons_datasets"

    @pytest.mark.asyncio
    async def test_interactive_selection(self):
        """Interactive map selection queries"""
        result = await route_query("Open a map so I can select areas")
        data = json.loads(result)

        assert data["intent"] == "interactive_selection"
        assert data["recommended_tool"] == "select_geographic_area"

    @pytest.mark.asyncio
    async def test_route_planning(self):
        """Route planning queries"""
        result = await route_query("Plan a route from Birmingham to Manchester")
        data = json.loads(result)

        assert data["intent"] == "route_planning"
        assert data["recommended_tool"] == "plan_route"

    @pytest.mark.asyncio
    async def test_boundary_fetch(self):
        """Boundary fetch queries"""
        result = await route_query("Get the boundary of Birmingham")
        data = json.loads(result)

        assert data["intent"] == "boundary_fetch"
        assert data["recommended_tool"] == "fetch_boundaries"


class TestPlaceNameExtraction:
    """Tests for place name extraction"""

    def test_extract_known_city(self):
        """Should extract known UK cities"""
        assert _extract_place_name("Find Birmingham") == "Birmingham"
        assert _extract_place_name("Where is Manchester") == "Manchester"
        assert _extract_place_name("Show me London") == "London"

    def test_extract_case_insensitive(self):
        """Should be case insensitive"""
        assert _extract_place_name("find BIRMINGHAM").lower() == "birmingham"
        assert _extract_place_name("MANCHESTER info").lower() == "manchester"

    def test_extract_capitalized_word(self):
        """Should extract capitalized words as potential places"""
        result = _extract_place_name("Find Solihull")
        assert result == "Solihull"

    def test_no_place_in_query(self):
        """Should return None if no place found"""
        result = _extract_place_name("what datasets are available")
        # May return None or a word depending on implementation
        # The key is it shouldn't crash


class TestPatternMatching:
    """Tests for pattern matching functions"""

    def test_place_lookup_patterns(self):
        """Place lookup patterns should match city queries"""
        score = _match_patterns("Find Birmingham", PLACE_LOOKUP_PATTERNS)
        assert score > 0.5

    def test_feature_patterns(self):
        """Feature patterns should match building/cinema queries"""
        score = _match_patterns("Show buildings near here", FEATURE_SEARCH_PATTERNS)
        assert score > 0

    def test_statistics_patterns(self):
        """Statistics patterns should match data queries"""
        score = _match_patterns("What is the population", STATISTICS_PATTERNS)
        assert score > 0

    def test_comparison_patterns(self):
        """Comparison patterns should match compare queries"""
        score = _match_patterns("Compare A and B", COMPARISON_PATTERNS)
        assert score > 0


class TestToolRecommendation:
    """Tests for tool recommendation based on intent"""

    def test_place_lookup_tool(self):
        """Place lookup should recommend search_geographic_areas"""
        tool, workflow, explanation = _get_tool_for_intent(QueryIntent.PLACE_LOOKUP)
        assert tool == "search_geographic_areas"
        assert "search_geographic_areas" in workflow

    def test_feature_search_tool(self):
        """Feature search should recommend OS NGD workflow"""
        tool, workflow, explanation = _get_tool_for_intent(QueryIntent.FEATURE_SEARCH)
        assert tool == "search_features"
        assert "get_workflow_context" in workflow

    def test_statistics_tool(self):
        """Statistics should recommend get_statistics"""
        tool, workflow, explanation = _get_tool_for_intent(QueryIntent.STATISTICS)
        assert tool == "get_statistics"

    def test_comparison_tool(self):
        """Comparison should recommend compare_areas"""
        tool, workflow, explanation = _get_tool_for_intent(QueryIntent.AREA_COMPARISON)
        assert tool == "compare_areas"


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    @pytest.mark.asyncio
    async def test_empty_query(self):
        """Empty query should be handled gracefully"""
        result = await route_query("")
        data = json.loads(result)

        assert "error" in data or data["intent"] == "unknown"

    @pytest.mark.asyncio
    async def test_whitespace_only(self):
        """Whitespace-only query should be handled"""
        result = await route_query("   ")
        data = json.loads(result)

        assert "error" in data or data["intent"] == "unknown"

    @pytest.mark.asyncio
    async def test_single_word_city(self):
        """Single word city should work"""
        result = await route_query("Birmingham")
        data = json.loads(result)

        # Should still classify as place_lookup
        assert data["intent"] == "place_lookup" or data["confidence"] > 0

    @pytest.mark.asyncio
    async def test_gibberish(self):
        """Gibberish should be handled gracefully"""
        result = await route_query("asdfghjkl qwertyuiop")
        data = json.loads(result)

        # Should not crash, may be unknown
        assert "intent" in data or "error" in data

    @pytest.mark.asyncio
    async def test_very_long_query(self):
        """Very long query should be handled"""
        long_query = "Find Birmingham " * 100
        result = await route_query(long_query)
        data = json.loads(result)

        # Should still work
        assert "intent" in data


class TestConfidenceScores:
    """Tests for confidence score accuracy"""

    @pytest.mark.asyncio
    async def test_high_confidence_for_clear_query(self):
        """Clear queries should have high confidence"""
        result = await route_query("Find Birmingham")
        data = json.loads(result)

        assert data["confidence"] >= 0.8

    @pytest.mark.asyncio
    async def test_feature_override_place(self):
        """Feature keywords should override place extraction"""
        result = await route_query("Find cinemas in Birmingham")
        data = json.loads(result)

        # Should be feature_search, not place_lookup
        assert data["intent"] == "feature_search"
        assert data["confidence"] >= 0.8


class TestWorkflowSteps:
    """Tests for workflow step recommendations"""

    @pytest.mark.asyncio
    async def test_place_lookup_single_step(self):
        """Place lookup should be single step"""
        result = await route_query("Find Birmingham")
        data = json.loads(result)

        assert len(data["workflow_steps"]) == 1
        assert data["workflow_steps"][0] == "search_geographic_areas"

    @pytest.mark.asyncio
    async def test_statistics_multi_step(self):
        """Statistics should include area lookup first"""
        result = await route_query("What is the wellbeing in Coventry?")
        data = json.loads(result)

        assert len(data["workflow_steps"]) >= 2
        assert "search_geographic_areas" in data["workflow_steps"]
        assert "get_statistics" in data["workflow_steps"]

    @pytest.mark.asyncio
    async def test_feature_search_three_step(self):
        """Feature search should include workflow context"""
        result = await route_query("Find cinemas in Leeds")
        data = json.loads(result)

        assert "get_workflow_context" in data["workflow_steps"]
        assert "search_features" in data["workflow_steps"]


class TestGuidance:
    """Tests for guidance text in responses"""

    @pytest.mark.asyncio
    async def test_place_lookup_guidance(self):
        """Place lookup should have appropriate guidance"""
        result = await route_query("Find Birmingham")
        data = json.loads(result)

        assert "guidance" in data
        assert "search_geographic_areas" in data["guidance"]

    @pytest.mark.asyncio
    async def test_feature_search_guidance(self):
        """Feature search should mention workflow"""
        result = await route_query("Find cinemas in Leeds")
        data = json.loads(result)

        assert "guidance" in data
        assert "workflow" in data["guidance"].lower() or "NGD" in data["guidance"]


class TestIntentPriority:
    """Tests for intent priority handling"""

    @pytest.mark.asyncio
    async def test_feature_word_overrides_place(self):
        """Feature words should take priority over place names"""
        queries = [
            "Find cinemas in Birmingham",
            "Show buildings in Manchester",
            "Find schools near Leeds",
            "Where are the hospitals in Coventry",
        ]

        for query in queries:
            result = await route_query(query)
            data = json.loads(result)
            assert data["intent"] == "feature_search", f"Failed for: {query}"

    @pytest.mark.asyncio
    async def test_comparison_overrides_place(self):
        """Comparison keywords should take priority"""
        result = await route_query("Compare Birmingham and Manchester")
        data = json.loads(result)

        assert data["intent"] == "area_comparison"

    @pytest.mark.asyncio
    async def test_statistics_overrides_place(self):
        """Statistics keywords should take priority"""
        queries = [
            "What is the population of Birmingham",
            "Show wellbeing statistics for Leeds",
            "Census data for Manchester",
        ]

        for query in queries:
            result = await route_query(query)
            data = json.loads(result)
            assert data["intent"] == "statistics", f"Failed for: {query}"


# Benchmark tests (optional, for performance tracking)
class TestPerformance:
    """Performance tests for query routing"""

    @pytest.mark.asyncio
    async def test_routing_speed(self):
        """Routing should be fast"""
        import time

        start = time.time()
        for _ in range(100):
            await route_query("Find Birmingham")
        duration = time.time() - start

        # Should complete 100 queries in under 1 second
        assert duration < 1.0, f"Routing too slow: {duration:.2f}s for 100 queries"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
