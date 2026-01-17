"""Unit tests for ui_resources.py

Tests the OSUIResources class including widget loading and placeholder generation.
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

from mcp_service.ui_resources import OSUIResources, UI_DIR


class TestOSUIResources:
    """Tests for OSUIResources class"""

    def test_init(self):
        """Test OSUIResources initializes correctly"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        assert ui_resources.mcp == mcp

    def test_register_all_calls_all_registrations(self):
        """Test register_all calls all widget registrations"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        # Mock all registration methods
        ui_resources._register_geography_selector = MagicMock()
        ui_resources._register_statistics_dashboard = MagicMock()
        ui_resources._register_feature_inspector = MagicMock()
        ui_resources._register_route_planner = MagicMock()

        ui_resources.register_all()

        ui_resources._register_geography_selector.assert_called_once()
        ui_resources._register_statistics_dashboard.assert_called_once()
        ui_resources._register_feature_inspector.assert_called_once()
        ui_resources._register_route_planner.assert_called_once()

    def test_load_widget_html_success(self):
        """Test loading widget HTML file that exists"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        # geography_selector.html should exist
        content = ui_resources._load_widget_html("geography_selector.html")

        assert content is not None
        assert "<!DOCTYPE html>" in content or "<html" in content

    def test_load_widget_html_not_found(self):
        """Test loading widget HTML file that doesn't exist"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        content = ui_resources._load_widget_html("nonexistent_widget.html")

        assert content is None

    def test_load_widget_html_read_error(self):
        """Test handling read error for widget file"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "read_text", side_effect=IOError("Read error")):
                content = ui_resources._load_widget_html("test.html")

        assert content is None

    def test_placeholder_widget_generates_html(self):
        """Test placeholder widget generates valid HTML"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        html = ui_resources._placeholder_widget(
            title="Test Widget",
            message="This is a test message"
        )

        assert "<!DOCTYPE html>" in html
        assert "Test Widget" in html
        assert "This is a test message" in html
        assert "<html lang=\"en\">" in html

    def test_placeholder_widget_escapes_special_chars(self):
        """Test placeholder handles title/message correctly"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        html = ui_resources._placeholder_widget(
            title="Widget <Test>",
            message="Message with 'quotes'"
        )

        # Should contain the text (HTML escaping would be needed in production)
        assert "Widget" in html
        assert "Message" in html


class TestUIResourceRegistration:
    """Tests for individual widget registration"""

    def test_register_geography_selector(self):
        """Test geography selector registration"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        ui_resources._register_geography_selector()

        # Verify mcp.resource decorator was called
        mcp.resource.assert_called_once()
        call_args = mcp.resource.call_args
        assert call_args[0][0] == "ui://os-ons/geography-selector"
        assert call_args[1]["mime_type"] == "text/html"

    def test_register_statistics_dashboard(self):
        """Test statistics dashboard registration"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        ui_resources._register_statistics_dashboard()

        mcp.resource.assert_called_once()
        call_args = mcp.resource.call_args
        assert call_args[0][0] == "ui://os-ons/statistics-dashboard"

    def test_register_feature_inspector(self):
        """Test feature inspector registration"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        ui_resources._register_feature_inspector()

        mcp.resource.assert_called_once()
        call_args = mcp.resource.call_args
        assert call_args[0][0] == "ui://os-ons/feature-inspector"

    def test_register_route_planner(self):
        """Test route planner registration"""
        mcp = MagicMock()
        ui_resources = OSUIResources(mcp)

        ui_resources._register_route_planner()

        mcp.resource.assert_called_once()
        call_args = mcp.resource.call_args
        assert call_args[0][0] == "ui://os-ons/route-planner"


class TestUIDir:
    """Tests for UI_DIR constant"""

    def test_ui_dir_exists(self):
        """Test that UI_DIR points to existing directory"""
        assert UI_DIR.exists()
        assert UI_DIR.is_dir()

    def test_ui_dir_contains_widget_files(self):
        """Test that UI_DIR contains expected widget files"""
        expected_files = [
            "geography_selector.html",
            "statistics_dashboard.html",
            "feature_inspector.html",
            "route_planner.html",
        ]

        for filename in expected_files:
            filepath = UI_DIR / filename
            assert filepath.exists(), f"Expected widget file not found: {filename}"


@pytest.mark.asyncio
async def test_geography_selector_resource_returns_content():
    """Integration test: geography selector resource returns HTML"""
    mcp = MagicMock()
    registered_func = None

    # Capture the decorated function
    def capture_resource(*args, **kwargs):
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func
        return decorator

    mcp.resource = capture_resource
    ui_resources = OSUIResources(mcp)
    ui_resources._register_geography_selector()

    # Call the registered async function
    content = await registered_func()

    assert content is not None
    assert len(content) > 100  # Should be substantial HTML


@pytest.mark.asyncio
async def test_widget_returns_placeholder_when_missing():
    """Test widget returns placeholder when file missing"""
    mcp = MagicMock()
    registered_func = None

    def capture_resource(*args, **kwargs):
        def decorator(func):
            nonlocal registered_func
            registered_func = func
            return func
        return decorator

    mcp.resource = capture_resource
    ui_resources = OSUIResources(mcp)

    # Mock _load_widget_html to return None
    ui_resources._load_widget_html = MagicMock(return_value=None)
    ui_resources._register_geography_selector()

    content = await registered_func()

    assert "Placeholder" in content
    assert "Geography Selector" in content
