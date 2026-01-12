"""Tests for ONS Statistics tools (MCP-Apps)"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from tools.statistics_tools import (
    list_ons_datasets,
    get_dataset_info,
    get_statistics,
    compare_areas,
    DATASET_CATEGORIES,
)
from clients.ons_client import ONSAPIClient, ONSAPIError


# Helper to create a properly mocked client
def create_mock_client():
    """Create a mock ONS API client with async context manager support"""
    mock_client = AsyncMock(spec=ONSAPIClient)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    return mock_client


class TestListOnsDatasets:
    """Tests for list_ons_datasets tool"""

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_default_list(self, mock_client_class):
        """Test listing datasets with default parameters"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.list_local_authority_datasets.return_value = [
            {
                "id": "wellbeing-local-authority",
                "title": "Personal well-being estimates",
                "description": "Local authority data on life satisfaction",
                "keywords": ["wellbeing", "happiness"],
                "last_updated": "2024-01-15",
                "release_frequency": "annual",
            }
        ]

        result = await list_ons_datasets()
        data = json.loads(result)

        assert data["count"] == 1
        assert len(data["datasets"]) == 1
        assert data["datasets"][0]["id"] == "wellbeing-local-authority"
        assert data["category"] is None
        assert data["search"] is None

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_search_datasets(self, mock_client_class):
        """Test searching datasets by keyword"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.search_datasets.return_value = [
            {"id": "house-prices-local-authority", "title": "House price statistics"}
        ]

        result = await list_ons_datasets(search="house")
        data = json.loads(result)

        assert data["count"] == 1
        assert data["search"] == "house"
        mock_client.search_datasets.assert_called_once_with("house")

    @pytest.mark.asyncio
    async def test_invalid_category(self):
        """Test with invalid category returns error"""
        result = await list_ons_datasets(category="invalid_category")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "available_categories" in data.get("details", {})

    @pytest.mark.asyncio
    async def test_census_without_flag(self):
        """Test census category without include_census flag returns info"""
        result = await list_ons_datasets(category="census", include_census=False)
        data = json.loads(result)

        assert data["status"] == "info"
        assert "include_census=True" in data["message"]

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_census_with_flag(self, mock_client_class):
        """Test census category with include_census flag"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.list_census_datasets.return_value = [
            {"id": "TS063", "title": "Occupation"},
            {"id": "TS067", "title": "Qualifications"},
        ]

        result = await list_ons_datasets(category="census", include_census=True)
        data = json.loads(result)

        assert data["count"] == 2
        assert data["category"] == "census"

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_category_wellbeing(self, mock_client_class):
        """Test wellbeing category fetches specific datasets"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {
            "id": "wellbeing-local-authority",
            "title": "Personal well-being",
        }

        result = await list_ons_datasets(category="wellbeing")
        data = json.loads(result)

        # Should have called get_dataset for each dataset in category
        assert mock_client.get_dataset.called


class TestGetDatasetInfo:
    """Tests for get_dataset_info tool"""

    @pytest.mark.asyncio
    async def test_empty_dataset_id(self):
        """Test with empty dataset_id returns error"""
        result = await get_dataset_info(dataset_id="")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_whitespace_dataset_id(self):
        """Test with whitespace dataset_id returns error"""
        result = await get_dataset_info(dataset_id="   ")
        data = json.loads(result)

        assert "error_code" in data

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_get_dataset_info_success(self, mock_client_class):
        """Test successful dataset info retrieval"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {
            "id": "wellbeing-local-authority",
            "title": "Personal well-being estimates",
            "description": "Survey data on life satisfaction",
            "contacts": [{"name": "ONS", "email": "test@ons.gov.uk"}],
            "keywords": ["wellbeing"],
            "release_frequency": "annual",
            "last_updated": "2024-01-15",
            "national_statistic": True,
            "links": {"self": {"href": "https://api.ons.gov.uk/v1/datasets/wellbeing"}},
        }
        mock_client.list_editions.return_value = {
            "items": [{"edition": "time-series"}]
        }
        mock_client.get_latest_version.return_value = {
            "dimensions": [
                {"name": "geography", "label": "Geography"},
                {"name": "time", "label": "Time Period"},
            ]
        }

        result = await get_dataset_info(dataset_id="wellbeing-local-authority")
        data = json.loads(result)

        assert data["id"] == "wellbeing-local-authority"
        assert data["title"] == "Personal well-being estimates"
        assert "time-series" in data["editions"]
        assert len(data["dimensions"]) == 2

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_dataset_not_found(self, mock_client_class):
        """Test with non-existent dataset returns error"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.side_effect = ONSAPIError("Not found", status_code=404)

        result = await get_dataset_info(dataset_id="nonexistent")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "not found" in data["message"].lower()


class TestGetStatistics:
    """Tests for get_statistics tool"""

    @pytest.mark.asyncio
    async def test_empty_dataset_id(self):
        """Test with empty dataset_id returns error"""
        result = await get_statistics(dataset_id="")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_get_wellbeing_statistics(self, mock_client_class):
        """Test getting wellbeing statistics for an area"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {
            "id": "wellbeing-local-authority",
            "title": "Personal well-being estimates",
        }
        mock_client.get_latest_version.return_value = {
            "dimensions": [
                {"name": "geography"},
                {"name": "time"},
                {"name": "estimate"},
                {"name": "measureofwellbeing"},
            ]
        }
        mock_client.get_observations.return_value = {
            "observations": [
                {"value": "7.5", "dimensions": {"time": {"label": "2022-23"}}},
                {"value": "7.4", "dimensions": {"time": {"label": "2021-22"}}},
            ]
        }

        result = await get_statistics(
            dataset_id="wellbeing-local-authority",
            area_code="E08000026",
            time_period="*",
            measure="life-satisfaction",
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["dataset_id"] == "wellbeing-local-authority"
        assert data["area_code"] == "E08000026"
        assert len(data["observations"]) == 2
        assert "_meta" in data
        assert "ui://os-ons/statistics-dashboard" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_get_statistics_api_error(self, mock_client_class):
        """Test handling of API error in observations"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {"id": "test", "title": "Test Dataset"}
        mock_client.get_latest_version.return_value = {"dimensions": [{"name": "geography"}]}
        mock_client.get_observations.side_effect = ONSAPIError("Bad request", status_code=400)

        result = await get_statistics(dataset_id="test", area_code="E08000026")
        data = json.loads(result)

        assert data["status"] == "error"
        assert "available_dimensions" in data
        assert "hint" in data

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_get_statistics_single_observation(self, mock_client_class):
        """Test handling single observation response"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {"id": "test", "title": "Test"}
        mock_client.get_latest_version.return_value = {"dimensions": [{"name": "geography"}]}
        mock_client.get_observations.return_value = {
            "observation": "7.5",
            "dimensions": {"geography": {"label": "Coventry"}},
        }

        result = await get_statistics(dataset_id="test", area_code="E08000026")
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["observation"] == "7.5"


class TestCompareAreas:
    """Tests for compare_areas tool"""

    @pytest.mark.asyncio
    async def test_empty_dataset_id(self):
        """Test with empty dataset_id returns error"""
        result = await compare_areas(dataset_id="", area_codes="E08000026,E08000025")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_empty_area_codes(self):
        """Test with empty area_codes returns error"""
        result = await compare_areas(dataset_id="wellbeing-local-authority", area_codes="")
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_single_area_code(self):
        """Test with only one area code returns error"""
        result = await compare_areas(
            dataset_id="wellbeing-local-authority",
            area_codes="E08000026"
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "2 area codes" in data["message"]

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_compare_areas_success(self, mock_client_class):
        """Test successful area comparison"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {
            "id": "wellbeing-local-authority",
            "title": "Personal well-being estimates",
        }
        mock_client.get_observations.return_value = {
            "observations": [{"value": "7.5"}]
        }

        result = await compare_areas(
            dataset_id="wellbeing-local-authority",
            area_codes="E08000026,E08000025,E08000027"
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert data["area_count"] == 3
        assert len(data["comparison"]) == 3
        assert "_meta" in data

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_compare_areas_partial_failure(self, mock_client_class):
        """Test comparison with some areas failing"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {"id": "test", "title": "Test"}

        # First call succeeds, second fails
        mock_client.get_observations.side_effect = [
            {"observations": [{"value": "7.5"}]},
            ONSAPIError("Not found", 404),
        ]

        result = await compare_areas(
            dataset_id="test",
            area_codes="E08000026,INVALID"
        )
        data = json.loads(result)

        assert data["status"] == "ok"
        assert len(data["comparison"]) == 2
        # One should have error
        errors = [c for c in data["comparison"] if "error" in c]
        assert len(errors) == 1

    @pytest.mark.asyncio
    @patch("tools.statistics_tools.ONSAPIClient")
    async def test_compare_areas_with_time_period(self, mock_client_class):
        """Test comparison with time period filter"""
        mock_client = create_mock_client()
        mock_client_class.return_value = mock_client
        mock_client.get_dataset.return_value = {"id": "test", "title": "Test"}
        mock_client.get_observations.return_value = {"observations": []}

        result = await compare_areas(
            dataset_id="test",
            area_codes="E08000026,E08000025",
            time_period="2022-23"
        )
        data = json.loads(result)

        assert data["time_period"] == "2022-23"


class TestDatasetCategories:
    """Tests for DATASET_CATEGORIES configuration"""

    def test_all_categories_have_list(self):
        """Test that all categories have a list value"""
        for category, datasets in DATASET_CATEGORIES.items():
            assert isinstance(datasets, list), f"Category {category} should have list"

    def test_expected_categories_present(self):
        """Test that expected categories are present"""
        expected = ["wellbeing", "economy", "housing", "population", "health", "employment", "census"]
        for category in expected:
            assert category in DATASET_CATEGORIES, f"Expected category {category}"

    def test_wellbeing_category_has_datasets(self):
        """Test wellbeing category has expected datasets"""
        assert "wellbeing-local-authority" in DATASET_CATEGORIES["wellbeing"]
