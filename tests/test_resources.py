"""Tests for MCP documentation resources"""

import json
import pytest
from unittest.mock import MagicMock, AsyncMock

from mcp_service.resources import OSDocumentationResources


class TestOSDocumentationResources:
    """Tests for OSDocumentationResources class"""

    def test_init(self):
        """Test resources initializes correctly"""
        mcp = MagicMock()
        api_client = MagicMock()

        resources = OSDocumentationResources(mcp, api_client)

        assert resources.mcp == mcp
        assert resources.api_client == api_client

    def test_register_all_calls_transport_resources(self):
        """Test register_all calls transport network registration"""
        mcp = MagicMock()
        api_client = MagicMock()
        resources = OSDocumentationResources(mcp, api_client)

        resources._register_transport_network_resources = MagicMock()

        resources.register_all()

        resources._register_transport_network_resources.assert_called_once()

    def test_register_transport_network_resources(self):
        """Test transport network resources are registered"""
        mcp = MagicMock()
        api_client = MagicMock()
        resources = OSDocumentationResources(mcp, api_client)

        resources._register_transport_network_resources()

        # Should register 6 resources
        assert mcp.resource.call_count == 6

        # Check URIs
        uris = [call[0][0] for call in mcp.resource.call_args_list]
        expected_uris = [
            "os-docs://street",
            "os-docs://road",
            "os-docs://tram-on-road",
            "os-docs://road-node",
            "os-docs://road-link",
            "os-docs://road-junction",
        ]
        assert uris == expected_uris


class TestFetchDocResource:
    """Tests for _fetch_doc_resource method"""

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test successful documentation fetch"""
        mcp = MagicMock()
        api_client = AsyncMock()
        api_client.make_request_no_auth.return_value = "# Street Documentation\n\nThis is markdown."

        resources = OSDocumentationResources(mcp, api_client)

        result = await resources._fetch_doc_resource(
            "street",
            "https://example.com/street.md"
        )

        data = json.loads(result)

        assert data["feature_type"] == "street"
        assert data["content"] == "# Street Documentation\n\nThis is markdown."
        assert data["content_type"] == "markdown"
        assert data["source_url"] == "https://example.com/street.md"
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_fetch_error_handling(self):
        """Test error handling in documentation fetch"""
        mcp = MagicMock()
        api_client = AsyncMock()
        api_client.make_request_no_auth.side_effect = Exception("Network error")

        resources = OSDocumentationResources(mcp, api_client)

        result = await resources._fetch_doc_resource(
            "road",
            "https://example.com/road.md"
        )

        data = json.loads(result)

        assert data["feature_type"] == "road"
        assert "error" in data
        assert "Network error" in data["error"]


@pytest.mark.asyncio
async def test_street_docs_resource():
    """Integration test for street docs resource"""
    mcp = MagicMock()
    api_client = AsyncMock()
    api_client.make_request_no_auth.return_value = "Street markdown content"

    resources = OSDocumentationResources(mcp, api_client)

    # Capture the registered function
    registered_func = None

    def capture_resource(uri):
        def decorator(func):
            nonlocal registered_func
            if uri == "os-docs://street":
                registered_func = func
            return func
        return decorator

    mcp.resource = capture_resource
    resources._register_transport_network_resources()

    # Call the registered function
    result = await registered_func()
    data = json.loads(result)

    assert data["feature_type"] == "street"
    assert data["content"] == "Street markdown content"


@pytest.mark.asyncio
async def test_all_transport_resources_registered():
    """Test all transport resources are properly registered"""
    mcp = MagicMock()
    api_client = AsyncMock()
    api_client.make_request_no_auth.return_value = "Test content"

    resources = OSDocumentationResources(mcp, api_client)

    registered_funcs = {}

    def capture_resource(uri):
        def decorator(func):
            registered_funcs[uri] = func
            return func
        return decorator

    mcp.resource = capture_resource
    resources._register_transport_network_resources()

    # Check all expected resources were registered
    expected = [
        "os-docs://street",
        "os-docs://road",
        "os-docs://tram-on-road",
        "os-docs://road-node",
        "os-docs://road-link",
        "os-docs://road-junction",
    ]

    for uri in expected:
        assert uri in registered_funcs, f"Missing resource: {uri}"

    # Call each one to ensure they work
    for uri, func in registered_funcs.items():
        result = await func()
        data = json.loads(result)
        assert "content" in data or "error" in data
