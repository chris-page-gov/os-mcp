"""Tests for knowledge/index_builder.py"""

import json
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import os

from knowledge.index_builder import (
    load_latest_snapshot,
    build_indices,
    write_indices,
)


class TestLoadLatestSnapshot:
    """Tests for load_latest_snapshot function"""

    def test_load_snapshot_file_not_found(self):
        """Test that FileNotFoundError is raised when latest.json missing"""
        with patch.object(Path, 'exists', return_value=False):
            with pytest.raises(FileNotFoundError) as exc_info:
                load_latest_snapshot()

            assert "latest.json" in str(exc_info.value)

    def test_load_snapshot_success(self):
        """Test successful loading of snapshot"""
        mock_data = {"collections": [{"id": "test-collection"}]}

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create the data/metadata structure
            snap_dir = Path(tmpdir) / "data" / "metadata"
            snap_dir.mkdir(parents=True)
            latest_file = snap_dir / "latest.json"
            latest_file.write_text(json.dumps(mock_data))

            # Patch SNAP_DIR to our temp directory
            with patch('knowledge.index_builder.SNAP_DIR', snap_dir):
                result = load_latest_snapshot()

            assert result == mock_data


class TestBuildIndices:
    """Tests for build_indices function"""

    def test_build_indices_empty_snapshot(self):
        """Test building indices from empty snapshot"""
        snapshot = {"collections": []}

        indices = build_indices(snapshot)

        assert indices["field_to_collections"] == {}
        assert indices["enum_value_to_fields"] == {}
        assert indices["collection_prefix_groups"] == {}
        assert indices["collection_stats"] == {}
        assert indices["high_cardinality_fields"] == []

    def test_build_indices_single_collection(self):
        """Test building indices from single collection"""
        snapshot = {
            "collections": [
                {
                    "id": "bld-fts-building-1",
                    "enum_count": 5,
                    "total_queryables": 10,
                    "queryables": [
                        {"name": "osid", "is_enum": False},
                        {"name": "status", "is_enum": True, "enum_values": ["active", "demolished"]},
                    ],
                }
            ]
        }

        indices = build_indices(snapshot)

        # Check field_to_collections
        assert "osid" in indices["field_to_collections"]
        assert "status" in indices["field_to_collections"]
        assert "bld-fts-building-1" in indices["field_to_collections"]["osid"]

        # Check enum_value_to_fields
        assert "active" in indices["enum_value_to_fields"]
        assert "demolished" in indices["enum_value_to_fields"]
        assert indices["enum_value_to_fields"]["active"][0]["field"] == "status"
        assert indices["enum_value_to_fields"]["active"][0]["collection"] == "bld-fts-building-1"

        # Check collection_prefix_groups
        assert "bld-fts" in indices["collection_prefix_groups"]
        assert "bld-fts-building-1" in indices["collection_prefix_groups"]["bld-fts"]

        # Check collection_stats
        assert indices["collection_stats"]["bld-fts-building-1"]["enum_count"] == 5
        assert indices["collection_stats"]["bld-fts-building-1"]["total_queryables"] == 10

    def test_build_indices_multiple_collections_same_field(self):
        """Test field appearing in multiple collections"""
        snapshot = {
            "collections": [
                {
                    "id": "coll-1",
                    "queryables": [{"name": "shared_field"}],
                },
                {
                    "id": "coll-2",
                    "queryables": [{"name": "shared_field"}],
                },
                {
                    "id": "coll-3",
                    "queryables": [{"name": "shared_field"}],
                },
                {
                    "id": "coll-4",
                    "queryables": [{"name": "shared_field"}],
                },
                {
                    "id": "coll-5",
                    "queryables": [{"name": "shared_field"}],
                },
            ]
        }

        indices = build_indices(snapshot, multi_field_threshold=5)

        # shared_field appears in 5 collections, should be high cardinality
        assert "shared_field" in indices["high_cardinality_fields"]
        assert len(indices["field_to_collections"]["shared_field"]) == 5

    def test_build_indices_high_cardinality_threshold(self):
        """Test high cardinality field detection with custom threshold"""
        snapshot = {
            "collections": [
                {"id": f"coll-{i}", "queryables": [{"name": "common"}]}
                for i in range(10)
            ]
        }

        # With threshold of 10, should include common
        indices = build_indices(snapshot, multi_field_threshold=10)
        assert "common" in indices["high_cardinality_fields"]

        # With threshold of 11, should not include common
        indices = build_indices(snapshot, multi_field_threshold=11)
        assert "common" not in indices["high_cardinality_fields"]

    def test_build_indices_collection_prefix_single_part(self):
        """Test prefix grouping with single-part collection ID"""
        snapshot = {
            "collections": [
                {"id": "simple", "queryables": []},
            ]
        }

        indices = build_indices(snapshot)

        # Single-part ID should use itself as prefix
        assert "simple" in indices["collection_prefix_groups"]
        assert "simple" in indices["collection_prefix_groups"]["simple"]

    def test_build_indices_queryable_without_name_skipped(self):
        """Test that queryables without name are skipped"""
        snapshot = {
            "collections": [
                {
                    "id": "test-coll",
                    "queryables": [
                        {"name": "valid_field"},
                        {"type": "string"},  # No name
                        {},  # Empty
                    ],
                }
            ]
        }

        indices = build_indices(snapshot)

        assert "valid_field" in indices["field_to_collections"]
        assert len(indices["field_to_collections"]) == 1

    def test_build_indices_enum_values_limited_to_50(self):
        """Test that enum values are limited to 50"""
        snapshot = {
            "collections": [
                {
                    "id": "test-coll",
                    "queryables": [
                        {
                            "name": "big_enum",
                            "is_enum": True,
                            "enum_values": [f"value_{i}" for i in range(100)],
                        }
                    ],
                }
            ]
        }

        indices = build_indices(snapshot)

        # Only first 50 enum values should be indexed
        indexed_values = [k for k in indices["enum_value_to_fields"].keys() if k.startswith("value_")]
        assert len(indexed_values) == 50

    def test_build_indices_source_field(self):
        """Test that source field is included in indices"""
        snapshot = {"collections": []}

        indices = build_indices(snapshot)

        assert indices["source_generated_from"] == "latest.json"


class TestWriteIndices:
    """Tests for write_indices function"""

    def test_write_indices_creates_file(self):
        """Test that write_indices creates output file"""
        indices = {
            "field_to_collections": {"field1": ["coll1"]},
            "enum_value_to_fields": {},
            "collection_prefix_groups": {},
            "collection_stats": {},
            "high_cardinality_fields": [],
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            snap_dir = Path(tmpdir)
            output_file = snap_dir / "knowledge_index_latest.json"

            with patch('knowledge.index_builder.SNAP_DIR', snap_dir):
                write_indices(indices)

            assert output_file.exists()

            # Verify content
            written_data = json.loads(output_file.read_text())
            assert written_data == indices

    def test_write_indices_overwrites_existing(self):
        """Test that write_indices overwrites existing file"""
        old_data = {"old": "data"}
        new_indices = {"new": "indices"}

        with tempfile.TemporaryDirectory() as tmpdir:
            snap_dir = Path(tmpdir)
            output_file = snap_dir / "knowledge_index_latest.json"

            # Write old data
            output_file.write_text(json.dumps(old_data))

            with patch('knowledge.index_builder.SNAP_DIR', snap_dir):
                write_indices(new_indices)

            written_data = json.loads(output_file.read_text())
            assert written_data == new_indices

    def test_write_indices_unicode_handling(self):
        """Test that unicode characters are preserved"""
        indices = {
            "field_to_collections": {"field_with_émojis_🏠": ["coll1"]},
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            snap_dir = Path(tmpdir)
            output_file = snap_dir / "knowledge_index_latest.json"

            with patch('knowledge.index_builder.SNAP_DIR', snap_dir):
                write_indices(indices)

            written_data = json.loads(output_file.read_text(encoding="utf-8"))
            assert "field_with_émojis_🏠" in written_data["field_to_collections"]
