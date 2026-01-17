"""Performance tests for boundary handling and large datasets

These tests verify the server can handle large boundary data efficiently.
They are marked as slow and should be run separately.
"""

import json
import time
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# Mark all tests in this file as slow
pytestmark = [pytest.mark.slow, pytest.mark.performance]


class TestBoundaryPerformance:
    """Performance tests for boundary handling"""

    def test_large_geojson_parsing_performance(self):
        """Test parsing of large GeoJSON data"""
        # Create a large GeoJSON with many coordinates
        num_points = 10000
        coordinates = [[i * 0.001, 51.0 + (i * 0.0001)] for i in range(num_points)]

        large_geojson = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            },
            "properties": {"name": "Large boundary"}
        }

        start = time.time()
        json_str = json.dumps(large_geojson)
        parsed = json.loads(json_str)
        elapsed = time.time() - start

        # Should complete in under 1 second
        assert elapsed < 1.0, f"Large GeoJSON parsing took {elapsed:.2f}s"
        assert len(parsed["geometry"]["coordinates"][0]) == num_points

    def test_large_feature_collection_performance(self):
        """Test handling of FeatureCollection with many features"""
        num_features = 1000

        features = []
        for i in range(num_features):
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [i * 0.01, 51.0 + (i * 0.001)]
                },
                "properties": {
                    "id": f"feature_{i}",
                    "name": f"Feature {i}",
                    "description": "A test feature with some data"
                }
            })

        feature_collection = {
            "type": "FeatureCollection",
            "features": features
        }

        start = time.time()
        json_str = json.dumps(feature_collection)
        parsed = json.loads(json_str)
        elapsed = time.time() - start

        # Should complete in under 2 seconds
        assert elapsed < 2.0, f"Large FeatureCollection took {elapsed:.2f}s"
        assert len(parsed["features"]) == num_features

    def test_boundary_simplification_candidates(self):
        """Test identification of boundaries needing simplification"""
        # Simulate boundary complexity analysis

        def calculate_complexity(num_points):
            """Simple complexity score"""
            return num_points / 100

        # Test different boundary sizes
        test_cases = [
            (100, False),      # Simple - no simplification needed
            (1000, False),     # Medium - borderline
            (5000, True),      # Complex - simplification recommended
            (10000, True),     # Very complex - definitely simplify
        ]

        for num_points, should_simplify in test_cases:
            complexity = calculate_complexity(num_points)
            needs_simplification = complexity > 10  # Threshold

            assert needs_simplification == should_simplify, \
                f"Boundary with {num_points} points: expected {should_simplify}, got {needs_simplification}"


class TestCachePerformance:
    """Performance tests for caching mechanisms"""

    def test_cache_lookup_performance(self):
        """Test cache lookup performance with many entries"""
        from functools import lru_cache

        @lru_cache(maxsize=1000)
        def cached_lookup(key):
            return f"value_{key}"

        # Populate cache
        for i in range(1000):
            cached_lookup(f"key_{i}")

        # Measure lookup time
        start = time.time()
        for i in range(10000):
            cached_lookup(f"key_{i % 1000}")
        elapsed = time.time() - start

        # 10000 cache lookups should be very fast
        assert elapsed < 0.5, f"Cache lookups took {elapsed:.2f}s"

    def test_dict_based_cache_performance(self):
        """Test dict-based cache performance"""
        cache = {}

        # Populate
        for i in range(10000):
            cache[f"key_{i}"] = {"data": f"value_{i}", "metadata": {"index": i}}

        # Measure access time
        start = time.time()
        for i in range(100000):
            key = f"key_{i % 10000}"
            _ = cache.get(key)
        elapsed = time.time() - start

        # 100000 dict lookups should be fast
        assert elapsed < 1.0, f"Dict lookups took {elapsed:.2f}s"


class TestRateLimiterPerformance:
    """Performance tests for rate limiter"""

    def test_rate_limiter_high_volume(self):
        """Test rate limiter performance under high volume"""
        from middleware.http_middleware import RateLimiter

        limiter = RateLimiter(requests_per_minute=1000, window_seconds=60)

        start = time.time()

        # Simulate many clients making requests
        for client_id in range(100):
            for _ in range(50):
                limiter.check_rate_limit(f"client_{client_id}")

        elapsed = time.time() - start

        # 5000 rate limit checks should be fast
        assert elapsed < 1.0, f"Rate limiter checks took {elapsed:.2f}s"


class TestWorkflowPlannerPerformance:
    """Performance tests for workflow planner"""

    def test_detailed_context_many_collections(self):
        """Test detailed context retrieval with many collections"""
        from workflow_generator.workflow_planner import WorkflowPlanner

        planner = WorkflowPlanner(openapi_spec=None)

        # Populate cache with many collections
        for i in range(500):
            planner.detailed_collections_cache[f"collection_{i}"] = {
                "queryables": [{"name": f"field_{j}"} for j in range(20)],
                "metadata": {"index": i}
            }

        start = time.time()

        # Request context for subset of collections
        for _ in range(100):
            collection_ids = [f"collection_{i}" for i in range(50)]
            _ = planner.get_detailed_context(collection_ids)

        elapsed = time.time() - start

        # 100 context retrievals should be fast
        assert elapsed < 1.0, f"Context retrieval took {elapsed:.2f}s"


class TestErrorEnvelopePerformance:
    """Performance tests for error envelope generation"""

    def test_error_envelope_generation_volume(self):
        """Test error envelope generation at volume"""
        from utils.error_envelope import build_error_envelope, ErrorCode

        start = time.time()

        for i in range(10000):
            _ = build_error_envelope(
                tool=f"tool_{i}",
                message=f"Error message {i}",
                code=ErrorCode.GENERAL_ERROR,
                details={"index": i, "data": "some additional context"}
            )

        elapsed = time.time() - start

        # 10000 envelope generations should be fast
        assert elapsed < 2.0, f"Envelope generation took {elapsed:.2f}s"


class TestJSONSerializationPerformance:
    """Performance tests for JSON serialization"""

    def test_nested_structure_serialization(self):
        """Test serialization of deeply nested structures"""
        def create_nested(depth, width):
            if depth == 0:
                return {"value": "leaf"}
            return {
                f"child_{i}": create_nested(depth - 1, width)
                for i in range(width)
            }

        # Create moderately nested structure
        nested = create_nested(5, 3)  # 3^5 = 243 leaf nodes

        start = time.time()
        for _ in range(1000):
            json_str = json.dumps(nested)
            _ = json.loads(json_str)
        elapsed = time.time() - start

        # 1000 serialize/deserialize cycles should be reasonable
        assert elapsed < 5.0, f"Nested JSON roundtrip took {elapsed:.2f}s"
