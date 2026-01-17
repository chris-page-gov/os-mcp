"""Tests for MCP-Apps route planner tools"""

import json
import pytest

from tools.route_planner_tools import (
    plan_route,
    get_route_network,
    format_route_directions,
    calculate_route_summary,
)


class TestPlanRoute:
    """Tests for plan_route tool"""

    @pytest.mark.asyncio
    async def test_default_parameters(self):
        """Test with default parameters returns valid config"""
        result = await plan_route()
        data = json.loads(result)

        assert data["status"] == "ready"
        assert data["config"]["show_network"] is True
        assert data["config"]["features"]["waypoints_enabled"] is True
        assert data["config"]["center"]["lat"] == 52.4862
        assert "_meta" in data
        assert "ui://os-ons/route-planner" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_with_start_point(self):
        """Test with start point only"""
        result = await plan_route(start_lat=51.5074, start_lng=-0.1278)
        data = json.loads(result)

        assert data["config"]["start"]["lat"] == 51.5074
        assert data["config"]["start"]["lng"] == -0.1278
        assert "end" not in data["config"]

    @pytest.mark.asyncio
    async def test_with_start_and_end(self):
        """Test with both start and end points"""
        result = await plan_route(
            start_lat=51.5074, start_lng=-0.1278,
            end_lat=52.4862, end_lng=-1.8904
        )
        data = json.loads(result)

        assert data["config"]["start"]["lat"] == 51.5074
        assert data["config"]["end"]["lat"] == 52.4862

    @pytest.mark.asyncio
    async def test_with_bbox(self):
        """Test with bounding box"""
        result = await plan_route(bbox="-2.0,52.3,-1.5,52.6")
        data = json.loads(result)

        assert data["config"]["bbox"] == "-2.0,52.3,-1.5,52.6"

    @pytest.mark.asyncio
    async def test_show_network_false(self):
        """Test with show_network=False"""
        result = await plan_route(show_network=False)
        data = json.loads(result)

        assert data["config"]["show_network"] is False

    @pytest.mark.asyncio
    async def test_has_instructions(self):
        """Test that response includes instructions"""
        result = await plan_route()
        data = json.loads(result)

        assert "instructions" in data
        assert "Route Planner" in data["instructions"]


class TestGetRouteNetwork:
    """Tests for get_route_network tool"""

    @pytest.mark.asyncio
    async def test_valid_bbox(self):
        """Test with valid bounding box"""
        result = await get_route_network(bbox="-2.0,52.3,-1.5,52.6")
        data = json.loads(result)

        assert data["status"] == "pending"
        assert data["request"]["bbox"] == "-2.0,52.3,-1.5,52.6"
        assert data["request"]["include_restrictions"] is True
        assert data["request"]["limit"] == 500

    @pytest.mark.asyncio
    async def test_custom_limit(self):
        """Test with custom limit"""
        result = await get_route_network(bbox="-2.0,52.3,-1.5,52.6", limit=100)
        data = json.loads(result)

        assert data["request"]["limit"] == 100

    @pytest.mark.asyncio
    async def test_limit_capped_at_1000(self):
        """Test that limit is capped at 1000"""
        result = await get_route_network(bbox="-2.0,52.3,-1.5,52.6", limit=5000)
        data = json.loads(result)

        assert data["request"]["limit"] == 1000

    @pytest.mark.asyncio
    async def test_without_restrictions(self):
        """Test without restrictions"""
        result = await get_route_network(
            bbox="-2.0,52.3,-1.5,52.6",
            include_restrictions=False
        )
        data = json.loads(result)

        assert data["request"]["include_restrictions"] is False

    @pytest.mark.asyncio
    async def test_empty_bbox(self):
        """Test with empty bbox returns error"""
        result = await get_route_network(bbox="")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_invalid_bbox_format(self):
        """Test with invalid bbox format returns error"""
        result = await get_route_network(bbox="invalid")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_bbox_wrong_count(self):
        """Test with wrong number of bbox values returns error"""
        result = await get_route_network(bbox="-2.0,52.3,-1.5")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "4 values" in data["message"]

    @pytest.mark.asyncio
    async def test_bbox_non_numeric(self):
        """Test with non-numeric bbox values returns error"""
        result = await get_route_network(bbox="a,b,c,d")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_bbox_invalid_longitude(self):
        """Test with invalid longitude returns error"""
        result = await get_route_network(bbox="-200,52.3,-1.5,52.6")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "Longitude" in data["message"]

    @pytest.mark.asyncio
    async def test_bbox_invalid_latitude(self):
        """Test with invalid latitude returns error"""
        result = await get_route_network(bbox="-2.0,100,-1.5,52.6")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "Latitude" in data["message"]


class TestFormatRouteDirections:
    """Tests for format_route_directions helper"""

    def test_formats_directions(self):
        """Test formatting route edges into directions"""
        edges = [
            {"road_name": "High Street", "cost": 500, "road_id": "R1"},
            {"road_name": "Main Road", "cost": 1200, "road_id": "R2"},
            {"road_name": "Park Lane", "cost": 300, "road_id": "R3"},
        ]

        result = format_route_directions(edges)

        assert len(result) == 3
        assert result[0]["step"] == 1
        assert "Start on" in result[0]["instruction"]
        assert result[0]["road_name"] == "High Street"
        assert result[1]["step"] == 2
        assert "Continue" in result[1]["instruction"]
        assert result[2]["step"] == 3
        assert "Arrive" in result[2]["instruction"]

    def test_handles_unnamed_roads(self):
        """Test formatting with unnamed roads"""
        edges = [
            {"cost": 500},
            {"road_name": None, "cost": 300},
        ]

        result = format_route_directions(edges)

        assert "unnamed road" in result[0]["instruction"]
        assert "unnamed road" in result[1]["instruction"]

    def test_empty_edges(self):
        """Test with empty edge list"""
        result = format_route_directions([])
        assert result == []

    def test_includes_geometry_by_default(self):
        """Test that geometry is included by default"""
        edges = [
            {
                "road_name": "Test Road",
                "cost": 100,
                "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
            }
        ]

        result = format_route_directions(edges)
        assert "geometry" in result[0]

    def test_excludes_geometry_when_disabled(self):
        """Test that geometry is excluded when disabled"""
        edges = [
            {
                "road_name": "Test Road",
                "cost": 100,
                "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
            }
        ]

        result = format_route_directions(edges, include_geometry=False)
        assert "geometry" not in result[0]


class TestCalculateRouteSummary:
    """Tests for calculate_route_summary helper"""

    def test_calculates_summary(self):
        """Test summary calculation"""
        edges = [
            {"road_name": "High Street", "cost": 500},
            {"road_name": "Main Road", "cost": 1200},
            {"road_name": "High Street", "cost": 300},  # Duplicate road name
        ]

        result = calculate_route_summary(edges)

        assert result["total_distance_meters"] == 2000
        assert result["total_distance_km"] == 2.0
        assert result["segment_count"] == 3
        assert result["unique_roads"] == 2
        assert "High Street" in result["road_names"]
        assert "Main Road" in result["road_names"]

    def test_empty_edges(self):
        """Test summary with empty edge list"""
        result = calculate_route_summary([])

        assert result["total_distance_meters"] == 0
        assert result["total_distance_km"] == 0
        assert result["segment_count"] == 0
        assert result["unique_roads"] == 0

    def test_handles_missing_cost(self):
        """Test summary handles missing cost values"""
        edges = [
            {"road_name": "Test Road"},  # No cost
            {"road_name": "Other Road", "cost": 100},
        ]

        result = calculate_route_summary(edges)
        assert result["total_distance_meters"] == 100
