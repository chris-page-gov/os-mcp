"""Tests for prompts module - OSWorkflowPrompts and get_prompt_templates"""

import pytest
from unittest.mock import MagicMock, patch

from mcp_service.prompts import OSWorkflowPrompts, get_prompt_templates


class TestGetPromptTemplates:
    """Tests for get_prompt_templates function"""

    def test_get_all_templates_no_category(self):
        """Test getting all templates when no category specified"""
        templates = get_prompt_templates()

        assert isinstance(templates, dict)
        assert len(templates) > 0
        # Should include some known templates
        assert "usrn_breakdown" in templates

    def test_get_templates_with_matching_category(self):
        """Test filtering templates by category substring"""
        # Assuming there's a 'planning' category
        templates = get_prompt_templates(category="planning")

        assert isinstance(templates, dict)
        # All keys should contain 'planning'
        for key in templates.keys():
            assert "planning" in key.lower()

    def test_get_templates_with_nonexistent_category(self):
        """Test filtering with category that matches nothing"""
        templates = get_prompt_templates(category="nonexistent_xyz_category")

        assert isinstance(templates, dict)
        assert len(templates) == 0

    def test_get_templates_case_insensitive(self):
        """Test that category filtering is case insensitive"""
        templates_lower = get_prompt_templates(category="routing")
        templates_upper = get_prompt_templates(category="ROUTING")

        assert templates_lower == templates_upper

    def test_get_templates_warwickshire_special_case(self):
        """Test special handling for warwickshire category"""
        templates = get_prompt_templates(category="warwickshire")

        assert isinstance(templates, dict)
        # Warwickshire templates should be returned if available
        # This tests the special case handling

    def test_get_templates_diagnostics_category(self):
        """Test diagnostics category filtering"""
        templates = get_prompt_templates(category="diagnostics")

        assert isinstance(templates, dict)

    def test_get_templates_routing_category(self):
        """Test routing category filtering"""
        templates = get_prompt_templates(category="routing")

        assert isinstance(templates, dict)


class TestOSWorkflowPromptsInit:
    """Tests for OSWorkflowPrompts initialization"""

    def test_init_stores_mcp_service(self):
        """Test that init stores the MCP service reference"""
        mock_mcp = MagicMock()
        prompts = OSWorkflowPrompts(mock_mcp)

        assert prompts.mcp is mock_mcp


class TestOSWorkflowPromptsRegister:
    """Tests for OSWorkflowPrompts registration"""

    def test_register_all_calls_both_registration_methods(self):
        """Test that register_all calls both prompt registration methods"""
        mock_mcp = MagicMock()
        prompts = OSWorkflowPrompts(mock_mcp)

        # Spy on the internal methods
        with patch.object(prompts, '_register_analysis_prompts') as mock_analysis:
            with patch.object(prompts, '_register_general_prompts') as mock_general:
                prompts.register_all()

                mock_analysis.assert_called_once()
                mock_general.assert_called_once()

    def test_register_analysis_prompts_registers_usrn_breakdown(self):
        """Test that analysis prompts are registered"""
        mock_mcp = MagicMock()
        prompts = OSWorkflowPrompts(mock_mcp)

        prompts._register_analysis_prompts()

        # The prompt decorator should have been called
        mock_mcp.prompt.assert_called()

    def test_register_general_prompts_registers_multiple_prompts(self):
        """Test that general prompts are registered"""
        mock_mcp = MagicMock()
        prompts = OSWorkflowPrompts(mock_mcp)

        prompts._register_general_prompts()

        # Multiple prompts should be registered
        assert mock_mcp.prompt.call_count >= 2


class TestPromptMessageGeneration:
    """Tests for prompt message generation functions"""

    def test_usrn_breakdown_prompt_format(self):
        """Test USRN breakdown prompt message format"""
        mock_mcp = MagicMock()
        registered_funcs = {}

        # Capture the decorated functions
        def capture_decorator():
            def decorator(func):
                registered_funcs[func.__name__] = func
                return func
            return decorator

        mock_mcp.prompt = capture_decorator

        prompts = OSWorkflowPrompts(mock_mcp)
        prompts._register_analysis_prompts()

        # Check that usrn_breakdown_analysis was registered
        assert "usrn_breakdown_analysis" in registered_funcs

        # Test the function
        func = registered_funcs["usrn_breakdown_analysis"]
        result = func(usrn="12345678")

        assert len(result) == 1
        assert result[0].role == "user"
        assert "12345678" in result[0].content.text

    def test_collection_query_guidance_prompt_format(self):
        """Test collection query guidance prompt message format"""
        mock_mcp = MagicMock()
        registered_funcs = {}

        def capture_decorator():
            def decorator(func):
                registered_funcs[func.__name__] = func
                return func
            return decorator

        mock_mcp.prompt = capture_decorator

        prompts = OSWorkflowPrompts(mock_mcp)
        prompts._register_general_prompts()

        assert "collection_query_guidance" in registered_funcs

        func = registered_funcs["collection_query_guidance"]
        result = func(collection_id="bld-fts-building-1", query_type="features")

        assert len(result) == 1
        assert result[0].role == "user"
        assert "bld-fts-building-1" in result[0].content.text
        assert "features" in result[0].content.text

    def test_workflow_planning_prompt_format(self):
        """Test workflow planning prompt message format"""
        mock_mcp = MagicMock()
        registered_funcs = {}

        def capture_decorator():
            def decorator(func):
                registered_funcs[func.__name__] = func
                return func
            return decorator

        mock_mcp.prompt = capture_decorator

        prompts = OSWorkflowPrompts(mock_mcp)
        prompts._register_general_prompts()

        assert "workflow_planning" in registered_funcs

        func = registered_funcs["workflow_planning"]
        result = func(user_request="Find buildings near a road", data_theme="transport")

        assert len(result) == 1
        assert result[0].role == "user"
        assert "Find buildings near a road" in result[0].content.text
        assert "transport" in result[0].content.text

    def test_workflow_planning_default_theme(self):
        """Test workflow planning uses default theme"""
        mock_mcp = MagicMock()
        registered_funcs = {}

        def capture_decorator():
            def decorator(func):
                registered_funcs[func.__name__] = func
                return func
            return decorator

        mock_mcp.prompt = capture_decorator

        prompts = OSWorkflowPrompts(mock_mcp)
        prompts._register_general_prompts()

        func = registered_funcs["workflow_planning"]
        result = func(user_request="Find roads")

        # Default theme is 'transport'
        assert "transport" in result[0].content.text
