"""Tests for MCP-Apps widget communication tools"""

import json
import pytest

from tools.widget_communication import (
    get_shared_context,
    update_shared_context,
    share_selection,
    reset_shared_context,
)


@pytest.fixture(autouse=True)
def reset_context():
    """Reset shared context before each test"""
    reset_shared_context()
    yield
    reset_shared_context()


class TestGetSharedContext:
    """Tests for get_shared_context tool"""

    @pytest.mark.asyncio
    async def test_initial_context(self):
        """Test initial context is empty"""
        result = await get_shared_context()
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["selected_areas_count"] == 0
        assert data["summary"]["selected_features_count"] == 0
        assert data["summary"]["selected_datasets_count"] == 0
        assert data["summary"]["route_points_count"] == 0
        assert data["summary"]["has_bbox"] is False

    @pytest.mark.asyncio
    async def test_context_after_updates(self):
        """Test context reflects updates"""
        # Add an area
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry"}
        )

        result = await get_shared_context()
        data = json.loads(result)

        assert data["summary"]["selected_areas_count"] == 1
        assert data["context"]["selected_areas"][0]["code"] == "E08000026"


class TestUpdateSharedContext:
    """Tests for update_shared_context tool"""

    @pytest.mark.asyncio
    async def test_add_area(self):
        """Test adding an area"""
        result = await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry"}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["selected_areas_count"] == 1

    @pytest.mark.asyncio
    async def test_add_multiple_areas(self):
        """Test adding multiple areas"""
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry"}
        )
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000025", "name": "Birmingham"}
        )

        result = await get_shared_context()
        data = json.loads(result)

        assert data["summary"]["selected_areas_count"] == 2

    @pytest.mark.asyncio
    async def test_remove_area(self):
        """Test removing an area"""
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry"}
        )
        result = await update_shared_context(
            context_type="areas",
            action="remove",
            data={"id": "E08000026"}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["selected_areas_count"] == 0

    @pytest.mark.asyncio
    async def test_clear_areas(self):
        """Test clearing all areas"""
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry"}
        )
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000025", "name": "Birmingham"}
        )

        result = await update_shared_context(
            context_type="areas",
            action="clear"
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["selected_areas_count"] == 0

    @pytest.mark.asyncio
    async def test_set_areas(self):
        """Test replacing all areas with set action"""
        await update_shared_context(
            context_type="areas",
            action="add",
            data={"code": "E08000026", "name": "Coventry"}
        )

        result = await update_shared_context(
            context_type="areas",
            action="set",
            data={"items": [
                {"code": "E08000025", "name": "Birmingham"},
                {"code": "E08000027", "name": "Dudley"}
            ]}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["selected_areas_count"] == 2

    @pytest.mark.asyncio
    async def test_set_bbox(self):
        """Test setting bounding box"""
        result = await update_shared_context(
            context_type="bbox",
            action="add",
            data={"bbox": "-2.0,52.3,-1.5,52.6"}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["has_bbox"] is True

    @pytest.mark.asyncio
    async def test_clear_bbox(self):
        """Test clearing bounding box"""
        await update_shared_context(
            context_type="bbox",
            action="add",
            data={"bbox": "-2.0,52.3,-1.5,52.6"}
        )

        result = await update_shared_context(
            context_type="bbox",
            action="clear"
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["has_bbox"] is False

    @pytest.mark.asyncio
    async def test_add_feature(self):
        """Test adding a feature"""
        result = await update_shared_context(
            context_type="features",
            action="add",
            data={"id": "osgb123", "collection": "bld-fts-building-1"}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["selected_features_count"] == 1

    @pytest.mark.asyncio
    async def test_add_route_point(self):
        """Test adding a route point"""
        result = await update_shared_context(
            context_type="route_points",
            action="add",
            data={"lat": 52.4081, "lng": -1.5106, "type": "start"}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["summary"]["route_points_count"] == 1

    @pytest.mark.asyncio
    async def test_invalid_context_type(self):
        """Test with invalid context type returns error"""
        result = await update_shared_context(
            context_type="invalid",
            action="add",
            data={}
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_invalid_action(self):
        """Test with invalid action returns error"""
        result = await update_shared_context(
            context_type="areas",
            action="invalid",
            data={}
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_add_without_data(self):
        """Test add without data returns error"""
        result = await update_shared_context(
            context_type="areas",
            action="add",
            data=None
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_remove_without_id(self):
        """Test remove without id returns error"""
        result = await update_shared_context(
            context_type="areas",
            action="remove",
            data={}
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]


class TestShareSelection:
    """Tests for share_selection tool"""

    @pytest.mark.asyncio
    async def test_share_to_statistics(self):
        """Test sharing areas to statistics dashboard"""
        result = await share_selection(
            source_widget="geography",
            target_widget="statistics",
            selection_data={"areas": [
                {"code": "E08000026", "name": "Coventry"},
                {"code": "E08000025", "name": "Birmingham"}
            ]}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["source"] == "geography"
        assert data["target"] == "statistics"
        assert "E08000026" in data["init_config"]["area_codes"]
        assert "ui://os-ons/statistics-dashboard" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_share_to_feature_inspector(self):
        """Test sharing feature to inspector"""
        result = await share_selection(
            source_widget="geography",
            target_widget="feature",
            selection_data={
                "feature_id": "osgb123",
                "collection_id": "bld-fts-building-1"
            }
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["init_config"]["feature_id"] == "osgb123"
        assert data["init_config"]["collection_id"] == "bld-fts-building-1"
        assert "ui://os-ons/feature-inspector" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_share_to_route_planner(self):
        """Test sharing points to route planner"""
        result = await share_selection(
            source_widget="geography",
            target_widget="route",
            selection_data={"points": [
                {"lat": 52.4081, "lng": -1.5106},
                {"lat": 52.4862, "lng": -1.8904}
            ]}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["init_config"]["start_lat"] == 52.4081
        assert data["init_config"]["end_lat"] == 52.4862
        assert "ui://os-ons/route-planner" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_share_to_geography(self):
        """Test sharing bbox to geography selector"""
        result = await share_selection(
            source_widget="route",
            target_widget="geography",
            selection_data={"bbox": "-2.0,52.3,-1.5,52.6"}
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["init_config"]["bbox"] == "-2.0,52.3,-1.5,52.6"
        assert "ui://os-ons/geography-selector" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_invalid_source_widget(self):
        """Test with invalid source widget returns error"""
        result = await share_selection(
            source_widget="invalid",
            target_widget="statistics",
            selection_data={}
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_invalid_target_widget(self):
        """Test with invalid target widget returns error"""
        result = await share_selection(
            source_widget="geography",
            target_widget="invalid",
            selection_data={}
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
