"""Tests for WorkflowPlanner class"""

import pytest
from unittest.mock import MagicMock

from workflow_generator.workflow_planner import WorkflowPlanner


class TestWorkflowPlannerInit:
    """Tests for WorkflowPlanner initialization"""

    def test_init_with_openapi_spec(self):
        """Test initialization with OpenAPI spec"""
        mock_spec = MagicMock()
        planner = WorkflowPlanner(openapi_spec=mock_spec)

        assert planner.spec is mock_spec
        assert planner.basic_collections_info == {}
        assert planner.detailed_collections_cache == {}

    def test_init_with_basic_collections(self):
        """Test initialization with basic collections info"""
        mock_spec = MagicMock()
        collections = {"coll1": {"title": "Collection 1"}}
        planner = WorkflowPlanner(
            openapi_spec=mock_spec,
            basic_collections_info=collections
        )

        assert planner.basic_collections_info == collections

    def test_init_with_none_spec(self):
        """Test initialization with None spec"""
        planner = WorkflowPlanner(openapi_spec=None)

        assert planner.spec is None
        assert planner.basic_collections_info == {}

    def test_init_with_none_collections_defaults_to_empty(self):
        """Test that None collections defaults to empty dict"""
        planner = WorkflowPlanner(openapi_spec=None, basic_collections_info=None)

        assert planner.basic_collections_info == {}


class TestGetBasicContext:
    """Tests for get_basic_context method"""

    def test_get_basic_context_returns_collections_and_spec(self):
        """Test basic context contains collections and spec"""
        mock_spec = MagicMock()
        collections = {"coll1": {"title": "Collection 1"}}
        planner = WorkflowPlanner(
            openapi_spec=mock_spec,
            basic_collections_info=collections
        )

        context = planner.get_basic_context()

        assert context["available_collections"] == collections
        assert context["openapi_spec"] is mock_spec

    def test_get_basic_context_with_empty_collections(self):
        """Test basic context with empty collections"""
        planner = WorkflowPlanner(openapi_spec=None)

        context = planner.get_basic_context()

        assert context["available_collections"] == {}
        assert context["openapi_spec"] is None


class TestGetDetailedContext:
    """Tests for get_detailed_context method"""

    def test_get_detailed_context_returns_cached_collections(self):
        """Test detailed context returns cached collection data"""
        mock_spec = MagicMock()
        planner = WorkflowPlanner(openapi_spec=mock_spec)

        # Pre-populate cache
        planner.detailed_collections_cache = {
            "coll1": {"queryables": ["field1", "field2"]},
            "coll2": {"queryables": ["field3"]},
        }

        context = planner.get_detailed_context(["coll1", "coll2"])

        assert "coll1" in context["available_collections"]
        assert "coll2" in context["available_collections"]
        assert context["openapi_spec"] is mock_spec

    def test_get_detailed_context_filters_to_requested_collections(self):
        """Test detailed context only includes requested collections"""
        planner = WorkflowPlanner(openapi_spec=None)

        planner.detailed_collections_cache = {
            "coll1": {"queryables": ["field1"]},
            "coll2": {"queryables": ["field2"]},
            "coll3": {"queryables": ["field3"]},
        }

        context = planner.get_detailed_context(["coll1", "coll3"])

        assert "coll1" in context["available_collections"]
        assert "coll2" not in context["available_collections"]
        assert "coll3" in context["available_collections"]

    def test_get_detailed_context_missing_collection_excluded(self):
        """Test that requested but non-cached collections are excluded"""
        planner = WorkflowPlanner(openapi_spec=None)

        planner.detailed_collections_cache = {
            "coll1": {"queryables": ["field1"]},
        }

        context = planner.get_detailed_context(["coll1", "nonexistent"])

        assert "coll1" in context["available_collections"]
        assert "nonexistent" not in context["available_collections"]
        assert context["available_collections"]["coll1"] == {"queryables": ["field1"]}

    def test_get_detailed_context_empty_request(self):
        """Test detailed context with empty collection list"""
        planner = WorkflowPlanner(openapi_spec=None)

        planner.detailed_collections_cache = {
            "coll1": {"queryables": ["field1"]},
        }

        context = planner.get_detailed_context([])

        assert context["available_collections"] == {}

    def test_get_detailed_context_all_missing(self):
        """Test detailed context when all requested collections are missing"""
        planner = WorkflowPlanner(openapi_spec=None)

        planner.detailed_collections_cache = {}

        context = planner.get_detailed_context(["coll1", "coll2"])

        assert context["available_collections"] == {}


class TestWorkflowPlannerCacheManagement:
    """Tests for cache management behavior"""

    def test_cache_can_be_updated_externally(self):
        """Test that the cache can be updated after initialization"""
        planner = WorkflowPlanner(openapi_spec=None)

        assert planner.detailed_collections_cache == {}

        # Simulate external update (as done by OSDataHubService)
        planner.detailed_collections_cache["new_coll"] = {"data": "value"}

        context = planner.get_detailed_context(["new_coll"])
        assert context["available_collections"]["new_coll"] == {"data": "value"}

    def test_cache_preserves_complex_structures(self):
        """Test that cache preserves nested data structures"""
        planner = WorkflowPlanner(openapi_spec=None)

        complex_data = {
            "queryables": [
                {"name": "field1", "type": "string", "enum": ["a", "b"]},
                {"name": "field2", "type": "integer"},
            ],
            "metadata": {"version": 1},
        }
        planner.detailed_collections_cache["coll1"] = complex_data

        context = planner.get_detailed_context(["coll1"])
        assert context["available_collections"]["coll1"] == complex_data
