"""Tests for MCP-Apps geography tools (ONS boundaries)"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from tools.geography_tools import (
    select_geographic_area,
    fetch_boundaries,
    search_geographic_areas,
    GEOGRAPHIC_LEVELS,
)


class TestSelectGeographicArea:
    """Tests for select_geographic_area tool"""

    @pytest.mark.asyncio
    async def test_default_parameters(self):
        """Test with default parameters returns valid config"""
        result = await select_geographic_area()
        data = json.loads(result)

        assert data["status"] == "selection_pending"
        assert data["config"]["level"] == "local_auth"
        assert data["config"]["level_name"] == "Local Authority Districts"
        assert data["config"]["initial_view"]["lat"] == 52.4862
        assert data["config"]["initial_view"]["lng"] == -1.8904
        assert data["config"]["initial_view"]["zoom"] == 6
        assert data["config"]["features"]["multi_select"] is True
        assert "_meta" in data
        assert "ui://os-ons/geography-selector" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_custom_level(self):
        """Test with custom geographic level"""
        result = await select_geographic_area(level="ward")
        data = json.loads(result)

        assert data["config"]["level"] == "ward"
        assert data["config"]["level_name"] == "Wards"

    @pytest.mark.asyncio
    async def test_custom_initial_view(self):
        """Test with custom initial map view"""
        result = await select_geographic_area(
            initial_lat=51.5074,
            initial_lng=-0.1278,
            initial_zoom=10
        )
        data = json.loads(result)

        assert data["config"]["initial_view"]["lat"] == 51.5074
        assert data["config"]["initial_view"]["lng"] == -0.1278
        assert data["config"]["initial_view"]["zoom"] == 10

    @pytest.mark.asyncio
    async def test_invalid_level(self):
        """Test with invalid geographic level returns error"""
        result = await select_geographic_area(level="invalid_level")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_invalid_focus_level(self):
        """Test with invalid focus_level returns error"""
        result = await select_geographic_area(level="oa", focus_level="bad_level", focus_name="Coventry West")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_focus_area_config(self):
        """Test focus area config is included"""
        result = await select_geographic_area(level="oa", focus_level="parl_const", focus_name="Coventry West")
        data = json.loads(result)

        assert data["config"]["focus_area"]["level"] == "parl_const"
        assert data["config"]["focus_area"]["name"] == "Coventry West"
        assert data["config"]["focus_area"]["level_name"] == "Parliamentary Constituencies"

    @pytest.mark.asyncio
    async def test_all_levels_available(self):
        """Test that all levels are in available_levels config"""
        result = await select_geographic_area()
        data = json.loads(result)

        level_values = [l["value"] for l in data["config"]["available_levels"]]
        for level in GEOGRAPHIC_LEVELS.keys():
            assert level in level_values


class TestFetchBoundaries:
    """Tests for fetch_boundaries tool"""

    @pytest.mark.asyncio
    async def test_invalid_level(self):
        """Test with invalid level returns error"""
        result = await fetch_boundaries(level="invalid")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_empty_codes(self):
        """Test with empty codes string returns error"""
        result = await fetch_boundaries(level="local_auth", codes="  ,  ")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_fetch_by_codes(self, mock_fetch):
        """Test fetching boundaries by GSS codes"""
        mock_fetch.return_value = {
            "features": [
                {
                    "properties": {"LAD24CD": "E08000026", "LAD24NM": "Coventry"},
                    "geometry": {"type": "Polygon", "coordinates": []}
                }
            ]
        }

        result = await fetch_boundaries(level="local_auth", codes="E08000026")
        data = json.loads(result)

        assert data["type"] == "FeatureCollection"
        assert len(data["features"]) == 1
        assert data["metadata"]["level"] == "local_auth"
        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_fetch_by_bbox(self, mock_fetch):
        """Test fetching boundaries by bounding box"""
        mock_fetch.return_value = {"features": []}

        result = await fetch_boundaries(
            level="local_auth",
            bbox="-2.0,52.3,-1.7,52.6"
        )
        data = json.loads(result)

        assert data["type"] == "FeatureCollection"
        assert data["metadata"]["bbox"] == "-2.0,52.3,-1.7,52.6"


class TestSearchGeographicAreas:
    """Tests for search_geographic_areas tool"""

    @pytest.mark.asyncio
    async def test_invalid_level(self):
        """Test with invalid level returns error"""
        result = await search_geographic_areas(query="test", level="invalid")
        data = json.loads(result)

        assert "error_code" in data

    @pytest.mark.asyncio
    async def test_short_query(self):
        """Test with too short query returns error"""
        result = await search_geographic_areas(query="a")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_search_success(self, mock_fetch):
        """Test successful search"""
        mock_fetch.return_value = {
            "features": [
                {"properties": {"LAD24CD": "E08000025", "LAD24NM": "Birmingham"}},
                {"properties": {"LAD24CD": "E08000026", "LAD24NM": "Coventry"}}
            ]
        }

        result = await search_geographic_areas(query="Birmingham")
        data = json.loads(result)

        assert data["query"] == "Birmingham"
        assert data["level"] == "local_auth"
        assert data["count"] == 2
        assert len(data["results"]) == 2


class TestGeographicLevelsConfig:
    """Tests for GEOGRAPHIC_LEVELS configuration"""

    def test_all_levels_have_required_fields(self):
        """Test that all levels have required configuration fields"""
        required_fields = ["name", "service", "code_field", "name_field"]

        for level_id, config in GEOGRAPHIC_LEVELS.items():
            for field in required_fields:
                assert field in config, f"Level {level_id} missing {field}"

    def test_expected_levels_present(self):
        """Test that expected geographic levels are present"""
        expected = ["parl_const", "local_auth", "ward", "lsoa", "msoa", "oa"]

        for level in expected:
            assert level in GEOGRAPHIC_LEVELS


class TestFetchBoundariesAdditional:
    """Additional tests for fetch_boundaries to improve coverage"""

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_fetch_all_limited(self, mock_fetch):
        """Test fetching all boundaries with limit"""
        mock_fetch.return_value = {"features": []}

        result = await fetch_boundaries(level="local_auth", limit=50)
        data = json.loads(result)

        assert data["type"] == "FeatureCollection"
        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_fetch_normalizes_properties(self, mock_fetch):
        """Test that fetch_boundaries normalizes property names"""
        mock_fetch.return_value = {
            "features": [
                {
                    "properties": {"LAD24CD": "E08000026", "LAD24NM": "Coventry"},
                    "geometry": {"type": "Polygon"}
                }
            ]
        }

        result = await fetch_boundaries(level="local_auth", codes="E08000026")
        data = json.loads(result)

        feature = data["features"][0]
        # Should have standardized fields added
        assert feature["properties"]["gss_code"] == "E08000026"
        assert feature["properties"]["name"] == "Coventry"
        assert feature["properties"]["level"] == "local_auth"

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_fetch_handles_api_error(self, mock_fetch):
        """Test that fetch_boundaries handles API errors gracefully"""
        mock_fetch.side_effect = Exception("API connection failed")

        result = await fetch_boundaries(level="local_auth", codes="E08000026")
        data = json.loads(result)

        assert "error_code" in data
        assert "UPSTREAM_ERROR" in data["error_code"]

    @pytest.mark.asyncio
    async def test_fetch_limit_capped(self):
        """Test that limit is capped at 500"""
        with patch("tools.geography_tools._fetch_from_ons_api") as mock_fetch:
            mock_fetch.return_value = {"features": []}

            await fetch_boundaries(level="local_auth", limit=1000)

            # Verify limit was capped
            call_kwargs = mock_fetch.call_args
            assert call_kwargs[1]["result_record_count"] <= 500

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_fetch_multiple_codes(self, mock_fetch):
        """Test fetching multiple area codes"""
        mock_fetch.return_value = {
            "features": [
                {"properties": {"LAD24CD": "E08000025", "LAD24NM": "Birmingham"}},
                {"properties": {"LAD24CD": "E08000026", "LAD24NM": "Coventry"}}
            ]
        }

        result = await fetch_boundaries(
            level="local_auth",
            codes="E08000025,E08000026"
        )
        data = json.loads(result)

        assert data["metadata"]["count"] == 2


class TestSearchGeographicAreasAdditional:
    """Additional tests for search_geographic_areas"""

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_search_handles_api_error(self, mock_fetch):
        """Test that search handles API errors gracefully"""
        mock_fetch.side_effect = Exception("API error")

        result = await search_geographic_areas(query="Birmingham")
        data = json.loads(result)

        assert "error_code" in data
        assert "UPSTREAM_ERROR" in data["error_code"]

    @pytest.mark.asyncio
    async def test_search_limit_capped(self):
        """Test that search limit is capped at 50"""
        with patch("tools.geography_tools._fetch_from_ons_api") as mock_fetch:
            mock_fetch.return_value = {"features": []}

            await search_geographic_areas(query="test", limit=100)

            call_kwargs = mock_fetch.call_args
            assert call_kwargs[1]["result_record_count"] <= 50

    @pytest.mark.asyncio
    @patch("tools.geography_tools._fetch_from_ons_api")
    async def test_search_escapes_quotes(self, mock_fetch):
        """Test that search escapes single quotes in query"""
        mock_fetch.return_value = {"features": []}

        await search_geographic_areas(query="King's Lynn")

        # Verify the query was made with escaped quotes
        call_kwargs = mock_fetch.call_args
        where_clause = call_kwargs[1]["where_clause"]
        assert "King''s Lynn" in where_clause


class TestGetAvailableLevels:
    """Tests for get_available_levels helper"""

    def test_get_available_levels(self):
        """Test get_available_levels returns config"""
        from tools.geography_tools import get_available_levels

        levels = get_available_levels()

        assert levels == GEOGRAPHIC_LEVELS
        assert "local_auth" in levels
        assert "ward" in levels


class TestSelectGeographicAreaAdditional:
    """Additional tests for select_geographic_area"""

    @pytest.mark.asyncio
    async def test_search_term_passed(self):
        """Test that search_term is included in config"""
        result = await select_geographic_area(search_term="Birmingham")
        data = json.loads(result)

        assert data["config"]["search_term"] == "Birmingham"

    @pytest.mark.asyncio
    async def test_multi_select_false(self):
        """Test with multi_select disabled"""
        result = await select_geographic_area(multi_select=False)
        data = json.loads(result)

        assert data["config"]["features"]["multi_select"] is False

    @pytest.mark.asyncio
    async def test_all_geographic_levels(self):
        """Test selecting each geographic level"""
        for level in GEOGRAPHIC_LEVELS.keys():
            result = await select_geographic_area(level=level)
            data = json.loads(result)

            assert data["status"] == "selection_pending"
            assert data["config"]["level"] == level
