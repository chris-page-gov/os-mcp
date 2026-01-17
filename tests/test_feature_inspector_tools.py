"""Tests for MCP-Apps feature inspector tools"""

import json
import pytest

from tools.feature_inspector_tools import (
    inspect_feature,
    get_feature_with_linked,
    format_linked_identifiers,
    group_linked_by_type,
    summarize_linked_identifiers,
)


class TestInspectFeature:
    """Tests for inspect_feature tool"""

    @pytest.mark.asyncio
    async def test_valid_parameters(self):
        """Test with valid feature_id and collection_id"""
        result = await inspect_feature(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1"
        )
        data = json.loads(result)

        assert data["status"] == "loading"
        assert data["config"]["feature_id"] == "osgb1000000123456"
        assert data["config"]["collection_id"] == "bld-fts-building-1"
        assert data["config"]["options"]["include_linked"] is True
        assert data["config"]["options"]["include_geometry"] is True
        assert "_meta" in data
        assert "ui://os-ons/feature-inspector" in data["_meta"]["uiResourceUris"]

    @pytest.mark.asyncio
    async def test_without_linked(self):
        """Test with include_linked=False"""
        result = await inspect_feature(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1",
            include_linked=False
        )
        data = json.loads(result)

        assert data["config"]["options"]["include_linked"] is False

    @pytest.mark.asyncio
    async def test_without_geometry(self):
        """Test with include_geometry=False"""
        result = await inspect_feature(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1",
            include_geometry=False
        )
        data = json.loads(result)

        assert data["config"]["options"]["include_geometry"] is False
        assert data["config"]["options"]["show_map"] is False

    @pytest.mark.asyncio
    async def test_empty_feature_id(self):
        """Test with empty feature_id returns error"""
        result = await inspect_feature(
            feature_id="",
            collection_id="bld-fts-building-1"
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "feature_id" in data["message"]

    @pytest.mark.asyncio
    async def test_empty_collection_id(self):
        """Test with empty collection_id returns error"""
        result = await inspect_feature(
            feature_id="osgb1000000123456",
            collection_id=""
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]
        assert "collection_id" in data["message"]

    @pytest.mark.asyncio
    async def test_whitespace_feature_id(self):
        """Test with whitespace-only feature_id returns error"""
        result = await inspect_feature(
            feature_id="   ",
            collection_id="bld-fts-building-1"
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_strips_whitespace(self):
        """Test that feature_id and collection_id are stripped"""
        result = await inspect_feature(
            feature_id="  osgb1000000123456  ",
            collection_id="  bld-fts-building-1  "
        )
        data = json.loads(result)

        assert data["config"]["feature_id"] == "osgb1000000123456"
        assert data["config"]["collection_id"] == "bld-fts-building-1"


class TestGetFeatureWithLinked:
    """Tests for get_feature_with_linked tool"""

    @pytest.mark.asyncio
    async def test_valid_parameters(self):
        """Test with valid parameters"""
        result = await get_feature_with_linked(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1"
        )
        data = json.loads(result)

        assert data["status"] == "pending"
        assert data["request"]["feature_id"] == "osgb1000000123456"
        assert data["request"]["collection_id"] == "bld-fts-building-1"
        assert data["request"]["identifier_type"] == "TOID"
        assert data["request"]["include_geometry"] is True

    @pytest.mark.asyncio
    async def test_uprn_identifier_type(self):
        """Test with UPRN identifier type"""
        result = await get_feature_with_linked(
            feature_id="12345678901",
            collection_id="adr-fts-address-1",
            identifier_type="UPRN"
        )
        data = json.loads(result)

        assert data["request"]["identifier_type"] == "UPRN"

    @pytest.mark.asyncio
    async def test_usrn_identifier_type(self):
        """Test with USRN identifier type"""
        result = await get_feature_with_linked(
            feature_id="12345678",
            collection_id="trn-ntwk-street-1",
            identifier_type="USRN"
        )
        data = json.loads(result)

        assert data["request"]["identifier_type"] == "USRN"

    @pytest.mark.asyncio
    async def test_invalid_identifier_type(self):
        """Test with invalid identifier type returns error"""
        result = await get_feature_with_linked(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1",
            identifier_type="INVALID"
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_empty_feature_id(self):
        """Test with empty feature_id returns error"""
        result = await get_feature_with_linked(
            feature_id="",
            collection_id="bld-fts-building-1"
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_empty_collection_id(self):
        """Test with empty collection_id returns error"""
        result = await get_feature_with_linked(
            feature_id="osgb1000000123456",
            collection_id=""
        )
        data = json.loads(result)

        assert "error_code" in data
        assert "INVALID_INPUT" in data["error_code"]

    @pytest.mark.asyncio
    async def test_case_insensitive_identifier_type(self):
        """Test that identifier type is case insensitive"""
        result = await get_feature_with_linked(
            feature_id="osgb1000000123456",
            collection_id="bld-fts-building-1",
            identifier_type="toid"
        )
        data = json.loads(result)

        assert data["request"]["identifier_type"] == "TOID"


class TestFormatLinkedIdentifiers:
    """Tests for format_linked_identifiers helper"""

    def test_standard_format(self):
        """Test formatting standard linked identifiers"""
        raw = [
            {
                "identifierType": "TOID",
                "identifier": "osgb1000000123456",
                "featureType": "Building"
            },
            {
                "identifierType": "UPRN",
                "identifier": "12345678901",
                "featureType": "Address"
            }
        ]

        result = format_linked_identifiers(raw)

        assert len(result) == 2
        assert result[0]["identifierType"] == "TOID"
        assert result[0]["identifier"] == "osgb1000000123456"
        assert result[0]["featureType"] == "Building"
        assert result[1]["identifierType"] == "UPRN"

    def test_alternate_field_names(self):
        """Test formatting with alternate field names"""
        raw = [
            {
                "type": "TOID",
                "value": "osgb1000000123456",
                "collection": "Building"
            }
        ]

        result = format_linked_identifiers(raw)

        assert len(result) == 1
        assert result[0]["identifierType"] == "TOID"
        assert result[0]["identifier"] == "osgb1000000123456"
        assert result[0]["featureType"] == "Building"

    def test_missing_fields(self):
        """Test formatting with missing fields uses defaults"""
        raw = [{"id": "123"}]

        result = format_linked_identifiers(raw)

        assert len(result) == 1
        assert result[0]["identifierType"] == "Unknown"
        assert result[0]["identifier"] == "123"
        assert result[0]["featureType"] is None

    def test_empty_list(self):
        """Test formatting empty list"""
        result = format_linked_identifiers([])
        assert result == []

    def test_non_dict_items_skipped(self):
        """Test that non-dict items are skipped"""
        raw = [
            {"identifierType": "TOID", "identifier": "123"},
            "not a dict",
            None,
            123
        ]

        result = format_linked_identifiers(raw)

        assert len(result) == 1
        assert result[0]["identifierType"] == "TOID"

    def test_version_date_included(self):
        """Test that version date is included when present"""
        raw = [
            {
                "identifierType": "TOID",
                "identifier": "123",
                "versiondate": "2024-01-15"
            }
        ]

        result = format_linked_identifiers(raw)

        assert result[0]["versionDate"] == "2024-01-15"


class TestGroupLinkedByType:
    """Tests for group_linked_by_type helper"""

    def test_groups_by_type(self):
        """Test grouping linked identifiers by type"""
        linked = [
            {"identifierType": "TOID", "identifier": "123"},
            {"identifierType": "TOID", "identifier": "456"},
            {"identifierType": "UPRN", "identifier": "789"},
        ]

        result = group_linked_by_type(linked)

        assert "TOID" in result
        assert "UPRN" in result
        assert len(result["TOID"]) == 2
        assert len(result["UPRN"]) == 1

    def test_empty_list(self):
        """Test grouping empty list"""
        result = group_linked_by_type([])
        assert result == {}

    def test_unknown_type_grouped(self):
        """Test that items without identifierType are grouped as Unknown"""
        linked = [
            {"identifier": "123"},
            {"identifierType": "TOID", "identifier": "456"},
        ]

        result = group_linked_by_type(linked)

        assert "UNKNOWN" in result
        assert len(result["UNKNOWN"]) == 1


class TestSummarizeLinkedIdentifiers:
    """Tests for summarize_linked_identifiers helper"""

    def test_summary_counts(self):
        """Test summary includes correct counts"""
        linked = [
            {"identifierType": "TOID", "identifier": "123"},
            {"identifierType": "TOID", "identifier": "456"},
            {"identifierType": "UPRN", "identifier": "789"},
            {"identifierType": "USRN", "identifier": "abc"},
        ]

        result = summarize_linked_identifiers(linked)

        assert result["total"] == 4
        assert result["by_type"]["TOID"] == 2
        assert result["by_type"]["UPRN"] == 1
        assert result["by_type"]["USRN"] == 1
        assert set(result["types"]) == {"TOID", "UPRN", "USRN"}

    def test_empty_list_summary(self):
        """Test summary of empty list"""
        result = summarize_linked_identifiers([])

        assert result["total"] == 0
        assert result["by_type"] == {}
        assert result["types"] == []
