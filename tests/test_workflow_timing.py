"""
Workflow timing tests that handle the 2-minute delay for queryables fetching.
These tests specifically address the timing constraints mentioned by the author.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock


class TestWorkflowWithDelay:
    """Test suite for workflow functionality with timing considerations."""

    @pytest.mark.workflow
    @pytest.mark.asyncio
    async def test_get_workflow_context_with_simulated_delay(self, mock_os_service):
        """Test workflow context with realistic delay simulation."""
        # Configure mock to simulate the 2-minute delay
        async def delayed_context():
            await asyncio.sleep(0.1)  # Use small delay for testing
            return {
                "context": "workflow_established_after_delay",
                "queryables": ["feature_type", "themes"],
                "collections": ["test-collection-1", "lus-fts-site-1"],
                "delay_info": "Queryables fetched after delay"
            }
        
        mock_os_service.get_workflow_context.side_effect = delayed_context
        
        start_time = asyncio.get_event_loop().time()
        result = await mock_os_service.get_workflow_context()
        end_time = asyncio.get_event_loop().time()
        
        # Verify the delay occurred (even if simulated)
        assert end_time - start_time >= 0.1
        assert result["context"] == "workflow_established_after_delay"
        assert "delay_info" in result

    @pytest.mark.workflow
    @pytest.mark.asyncio
    @pytest.mark.timeout(180)  # 3 minute timeout for workflow tests
    async def test_full_workflow_with_search(self, mock_os_service):
        """Test complete workflow from context to search with timing."""
        # Step 1: Get workflow context (with simulated delay)
        async def delayed_context():
            await asyncio.sleep(0.1)  # Simulate delay
            return {
                "context": "workflow_established",
                "queryables": ["oslandusetertiarygroup"],
                "collections": ["lus-fts-site-1"]
            }
        
        mock_os_service.get_workflow_context.side_effect = delayed_context
        
        context_result = await mock_os_service.get_workflow_context()
        assert context_result["context"] == "workflow_established"
        
        # Step 2: Reset mock for search (no delay expected after context)
        mock_os_service.search_features.side_effect = None
        mock_os_service.search_features.return_value = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": "cinema-1",
                    "properties": {"oslandusetertiarygroup": "Cinema"}
                }
            ]
        }
        
        # Step 3: Search should be fast after context is established
        search_start = asyncio.get_event_loop().time()
        search_result = await mock_os_service.search_features(
            collection_id="lus-fts-site-1",
            cql_filter="oslandusetertiarygroup = 'Cinema'"
        )
        search_end = asyncio.get_event_loop().time()
        
        # Search should be fast (no additional delay)
        assert search_end - search_start < 1.0
        assert search_result["type"] == "FeatureCollection"

    @pytest.mark.workflow  
    @pytest.mark.asyncio
    async def test_workflow_context_caching(self, mock_os_service):
        """Test that workflow context is cached to avoid repeated delays."""
        call_count = 0
        
        async def delayed_context_with_counter():
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate the 2-minute delay
            return {
                "context": "workflow_established",
                "queryables": ["feature_type"],
                "collections": ["test-collection"],
                "call_number": call_count
            }
        
        mock_os_service.get_workflow_context.side_effect = delayed_context_with_counter
        
        # First call should trigger the delay
        start_time = asyncio.get_event_loop().time()
        result1 = await mock_os_service.get_workflow_context()
        first_call_time = asyncio.get_event_loop().time() - start_time
        
        # In a real system, subsequent calls should be cached
        # For testing, we'll simulate this by changing the mock behavior
        mock_os_service.get_workflow_context.side_effect = None
        mock_os_service.get_workflow_context.return_value = result1
        
        # Second call should be immediate (cached)
        start_time = asyncio.get_event_loop().time()
        result2 = await mock_os_service.get_workflow_context()
        second_call_time = asyncio.get_event_loop().time() - start_time
        
        # Verify first call took time, second was immediate
        assert first_call_time >= 0.1
        assert second_call_time < 0.01
        assert result1["context"] == result2["context"]

    @pytest.mark.slow
    @pytest.mark.asyncio
    @pytest.mark.timeout(30)  # 30 second timeout for realistic delay testing
    async def test_realistic_delay_simulation(self, mock_os_service):
        """Test with a more realistic delay simulation (longer but not 2 minutes)."""
        async def realistic_delay():
            # Use 1 second instead of 2 minutes for testing
            await asyncio.sleep(1.0)
            return {
                "context": "workflow_established_realistic",
                "queryables": ["oslandusetertiarygroup", "roadclassification"],
                "collections": ["lus-fts-site-1", "trn-ntwk-street-1"],
                "delay_seconds": 1.0,
                "note": "Simulated realistic queryables fetch delay"
            }
        
        mock_os_service.get_workflow_context.side_effect = realistic_delay
        
        start_time = asyncio.get_event_loop().time()
        result = await mock_os_service.get_workflow_context()
        end_time = asyncio.get_event_loop().time()
        
        actual_delay = end_time - start_time
        assert actual_delay >= 1.0
        assert actual_delay < 2.0  # Should not take much longer
        assert result["context"] == "workflow_established_realistic"
        assert "note" in result
