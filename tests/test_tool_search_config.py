"""Tests for tool search configuration module"""

import pytest
from mcp_service.tool_search_config import (
    ToolCategory,
    ToolConfig,
    ALWAYS_LOADED_TOOLS,
    DEFERRED_TOOLS,
    TOOL_DESCRIPTIONS,
    get_tool_config,
    should_defer_loading,
    get_tools_by_category,
    get_always_loaded_tools,
    get_deferred_tools,
    get_tool_search_system_prompt,
    generate_mcp_toolset_config,
)


class TestToolCategory:
    """Tests for ToolCategory enum"""

    def test_all_categories_defined(self):
        """Test that all expected categories are defined"""
        expected = [
            "CORE", "WORKFLOW", "GEOGRAPHY", "STATISTICS",
            "FEATURES", "ROUTING", "WIDGET", "SEARCH",
            "LINKED", "UTILITY"
        ]
        actual = [c.name for c in ToolCategory]
        assert set(expected) == set(actual)

    def test_category_values_are_lowercase(self):
        """Test that category values are lowercase strings"""
        for category in ToolCategory:
            assert category.value == category.value.lower()
            assert isinstance(category.value, str)


class TestAlwaysLoadedTools:
    """Tests for always-loaded tools set"""

    def test_always_loaded_not_empty(self):
        """Test that always loaded set is not empty"""
        assert len(ALWAYS_LOADED_TOOLS) > 0

    def test_core_tools_always_loaded(self):
        """Test that core tools are always loaded"""
        core_tools = ["hello_world", "version_info", "route_query"]
        for tool in core_tools:
            assert tool in ALWAYS_LOADED_TOOLS

    def test_workflow_entry_point_always_loaded(self):
        """Test that routing entry point is always loaded"""
        assert "route_query" in ALWAYS_LOADED_TOOLS

    def test_primary_widget_tools_always_loaded(self):
        """Test that primary widget entry points are always loaded"""
        assert "select_geographic_area" in ALWAYS_LOADED_TOOLS


class TestDeferredTools:
    """Tests for deferred tools set"""

    def test_deferred_not_empty(self):
        """Test that deferred set is not empty"""
        assert len(DEFERRED_TOOLS) > 0

    def test_secondary_tools_are_deferred(self):
        """Test that secondary/specialized tools are deferred"""
        secondary_tools = [
            "fetch_boundaries",
            "list_ons_datasets",
            "plan_route",
            "search_features",
            "get_feature",
        ]
        for tool in secondary_tools:
            assert tool in DEFERRED_TOOLS

    def test_no_overlap_between_sets(self):
        """Test that no tool is in both always-loaded and deferred"""
        overlap = ALWAYS_LOADED_TOOLS & DEFERRED_TOOLS
        assert len(overlap) == 0, f"Overlap found: {overlap}"


class TestToolDescriptions:
    """Tests for tool descriptions"""

    def test_all_tools_have_descriptions(self):
        """Test that all categorized tools have descriptions"""
        all_tools = ALWAYS_LOADED_TOOLS | DEFERRED_TOOLS
        for tool in all_tools:
            assert tool in TOOL_DESCRIPTIONS, f"Missing description for {tool}"

    def test_descriptions_have_required_fields(self):
        """Test that descriptions have required fields"""
        for name, config in TOOL_DESCRIPTIONS.items():
            assert "defer_loading" in config, f"{name} missing defer_loading"
            assert "category" in config, f"{name} missing category"
            assert "keywords" in config, f"{name} missing keywords"
            assert "description_enhanced" in config, f"{name} missing description_enhanced"

    def test_defer_loading_matches_sets(self):
        """Test that defer_loading in descriptions matches tool sets"""
        for name, config in TOOL_DESCRIPTIONS.items():
            expected_deferred = name in DEFERRED_TOOLS
            actual_deferred = config.get("defer_loading", False)
            assert actual_deferred == expected_deferred, \
                f"{name}: expected defer_loading={expected_deferred}, got {actual_deferred}"

    def test_descriptions_are_non_empty(self):
        """Test that enhanced descriptions are non-empty"""
        for name, config in TOOL_DESCRIPTIONS.items():
            desc = config.get("description_enhanced", "")
            assert len(desc) > 10, f"{name} has too short description: {desc}"

    def test_keywords_are_lists(self):
        """Test that keywords are lists"""
        for name, config in TOOL_DESCRIPTIONS.items():
            keywords = config.get("keywords", None)
            assert isinstance(keywords, list), f"{name} keywords not a list"

    def test_descriptions_contain_keywords(self):
        """Test that descriptions contain at least some keywords"""
        # Spot check a few tools
        test_cases = [
            ("fetch_boundaries", ["boundary", "geojson"]),
            ("get_statistics", ["statistics", "population"]),
            ("plan_route", ["route", "directions"]),
        ]
        for tool_name, expected_keywords in test_cases:
            config = TOOL_DESCRIPTIONS.get(tool_name, {})
            desc = config.get("description_enhanced", "").lower()
            for keyword in expected_keywords:
                assert keyword in desc, \
                    f"{tool_name} description should contain '{keyword}'"


class TestGetToolConfig:
    """Tests for get_tool_config function"""

    def test_get_known_tool_config(self):
        """Test getting config for a known tool"""
        config = get_tool_config("hello_world")

        assert config["defer_loading"] is False
        assert config["category"] == ToolCategory.CORE
        assert isinstance(config["keywords"], list)

    def test_get_deferred_tool_config(self):
        """Test getting config for a deferred tool"""
        config = get_tool_config("search_features")

        assert config["defer_loading"] is True
        assert config["category"] == ToolCategory.FEATURES

    def test_get_unknown_tool_config(self):
        """Test getting config for an unknown tool"""
        config = get_tool_config("unknown_tool_xyz")

        assert config["defer_loading"] is False  # Default to not deferred
        assert config["category"] == ToolCategory.UTILITY


class TestShouldDeferLoading:
    """Tests for should_defer_loading function"""

    def test_always_loaded_returns_false(self):
        """Test that always-loaded tools return False"""
        for tool in ALWAYS_LOADED_TOOLS:
            assert should_defer_loading(tool) is False

    def test_deferred_returns_true(self):
        """Test that deferred tools return True"""
        for tool in DEFERRED_TOOLS:
            assert should_defer_loading(tool) is True

    def test_unknown_tool_returns_false(self):
        """Test that unknown tools return False (safe default)"""
        assert should_defer_loading("unknown_tool_xyz") is False


class TestGetToolsByCategory:
    """Tests for get_tools_by_category function"""

    def test_get_core_tools(self):
        """Test getting core category tools"""
        tools = get_tools_by_category(ToolCategory.CORE)

        assert "hello_world" in tools
        assert "check_api_key" in tools
        assert "version_info" in tools

    def test_get_geography_tools(self):
        """Test getting geography category tools"""
        tools = get_tools_by_category(ToolCategory.GEOGRAPHY)

        assert "select_geographic_area" in tools
        assert "fetch_boundaries" in tools
        assert "search_geographic_areas" in tools

    def test_get_statistics_tools(self):
        """Test getting statistics category tools"""
        tools = get_tools_by_category(ToolCategory.STATISTICS)

        assert "list_ons_datasets" in tools
        assert "get_statistics" in tools
        assert "compare_areas" in tools

    def test_get_features_tools(self):
        """Test getting features category tools"""
        tools = get_tools_by_category(ToolCategory.FEATURES)

        assert "search_features" in tools
        assert "get_feature" in tools
        assert "inspect_feature" in tools

    def test_all_tools_have_category(self):
        """Test that all tools are assigned to a category"""
        all_categorized = set()
        for category in ToolCategory:
            tools = get_tools_by_category(category)
            all_categorized.update(tools)

        # All tools in TOOL_DESCRIPTIONS should be categorized
        assert set(TOOL_DESCRIPTIONS.keys()) == all_categorized


class TestGetToolSets:
    """Tests for get_always_loaded_tools and get_deferred_tools"""

    def test_get_always_loaded_returns_copy(self):
        """Test that get_always_loaded_tools returns a copy"""
        tools1 = get_always_loaded_tools()
        tools2 = get_always_loaded_tools()

        assert tools1 is not tools2
        assert tools1 == tools2

    def test_get_deferred_returns_copy(self):
        """Test that get_deferred_tools returns a copy"""
        tools1 = get_deferred_tools()
        tools2 = get_deferred_tools()

        assert tools1 is not tools2
        assert tools1 == tools2

    def test_modifying_copy_doesnt_affect_original(self):
        """Test that modifying returned set doesn't affect original"""
        tools = get_always_loaded_tools()
        original_len = len(ALWAYS_LOADED_TOOLS)

        tools.add("fake_tool")

        assert len(ALWAYS_LOADED_TOOLS) == original_len


class TestGetToolSearchSystemPrompt:
    """Tests for get_tool_search_system_prompt function"""

    def test_returns_non_empty_string(self):
        """Test that system prompt is non-empty"""
        prompt = get_tool_search_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 100

    def test_contains_category_descriptions(self):
        """Test that system prompt mentions primary tools"""
        prompt = get_tool_search_system_prompt()

        assert "PRIMARY TOOLS" in prompt
        assert "search_geographic_areas" in prompt
        assert "select_geographic_area" in prompt

    def test_contains_search_guidance(self):
        """Test that system prompt has search guidance"""
        prompt = get_tool_search_system_prompt()

        assert "search" in prompt.lower()


class TestGenerateMcpToolsetConfig:
    """Tests for generate_mcp_toolset_config function"""

    def test_returns_valid_structure(self):
        """Test that config has required structure"""
        config = generate_mcp_toolset_config()

        assert config["type"] == "mcp_toolset"
        assert "mcp_server_name" in config
        assert "default_config" in config
        assert "configs" in config

    def test_default_config_has_defer_loading(self):
        """Test that default config sets defer_loading to True"""
        config = generate_mcp_toolset_config()

        assert config["default_config"]["defer_loading"] is True

    def test_always_loaded_tools_have_overrides(self):
        """Test that always-loaded tools have defer_loading=False override"""
        config = generate_mcp_toolset_config()
        configs = config["configs"]

        for tool in ALWAYS_LOADED_TOOLS:
            assert tool in configs, f"Missing override for {tool}"
            assert configs[tool]["defer_loading"] is False

    def test_deferred_tools_use_default(self):
        """Test that deferred tools don't have overrides (use default)"""
        config = generate_mcp_toolset_config()
        configs = config["configs"]

        for tool in DEFERRED_TOOLS:
            # Deferred tools should NOT be in configs (use default)
            assert tool not in configs, f"Unexpected override for {tool}"


class TestToolCounts:
    """Tests for tool count consistency"""

    def test_total_tool_count(self):
        """Test that total tools match expectations"""
        total_categorized = len(ALWAYS_LOADED_TOOLS) + len(DEFERRED_TOOLS)
        total_described = len(TOOL_DESCRIPTIONS)

        assert total_categorized == total_described

    def test_reasonable_split(self):
        """Test that split between always-loaded and deferred is reasonable"""
        # Always loaded should be a small subset (< 50%)
        always_count = len(ALWAYS_LOADED_TOOLS)
        deferred_count = len(DEFERRED_TOOLS)
        total = always_count + deferred_count

        always_ratio = always_count / total
        assert always_ratio < 0.5, f"Too many always-loaded tools: {always_ratio:.0%}"

        # Should have at least some always-loaded tools
        assert always_count >= 5, "Too few always-loaded tools"
