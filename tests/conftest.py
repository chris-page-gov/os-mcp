"""
Test configuration and fixtures for OS MCP Server tests.
"""

import pytest
import asyncio
import os
import json
from typing import AsyncGenerator, Dict, Any
from unittest.mock import AsyncMock, MagicMock

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService
from mcp.server.fastmcp import FastMCP


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "OS_API_KEY": "test_api_key_12345",
        "STDIO_KEY": "test_stdio_key",
        "BEARER_TOKEN": "dev-token",
        "PYTHONPATH": "src",
    }
    for key, value in test_env.items():
        monkeypatch.setenv(key, value)
    return test_env


@pytest.fixture
def mock_openapi_spec():
    """Mock OpenAPI specification for testing."""
    return {
        "openapi": "3.0.0",
        "info": {"title": "OS NGD API", "version": "1.0"},
        "paths": {
            "/collections": {
                "get": {
                    "summary": "Get collections",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        }
    }


@pytest.fixture
def mock_collections():
    """Mock collections data for testing."""
    return {
        "collections": [
            {
                "id": "test-collection-1",
                "title": "Test Collection 1",
                "description": "A test collection for unit tests"
            },
            {
                "id": "lus-fts-site-1", 
                "title": "Land Use Sites",
                "description": "Land use site features"
            },
            {
                "id": "trn-ntwk-street-1",
                "title": "Street Network", 
                "description": "Street network features"
            }
        ]
    }


@pytest.fixture
def mock_queryables():
    """Mock queryables data for testing."""
    return {
        "properties": {
            "oslandusetertiarygroup": {
                "type": "string",
                "description": "Land use tertiary group",
                "enumeration": True,
                "enum": ["Cinema", "Restaurant", "Shop", "Hospital"]
            },
            "roadclassification": {
                "type": "string", 
                "description": "Road classification",
                "enumeration": True,
                "enum": ["A Road", "B Road", "Minor Road", "Motorway"]
            },
            "usrn": {
                "type": "integer",
                "description": "Unique Street Reference Number"
            }
        }
    }


@pytest.fixture
def mock_features():
    """Mock feature search results."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "id": "test-feature-1",
                "properties": {
                    "usrn": 12345678,
                    "roadclassification": "A Road",
                    "designatedname1_text": "High Street"
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [-1.0, 51.0]
                }
            }
        ]
    }


@pytest.fixture
async def mock_api_client():
    """Create a mocked API client."""
    client = AsyncMock(spec=OSAPIClient)
    client.get_api_key.return_value = "test_api_key_12345"
    return client


@pytest.fixture  
def mock_mcp_server():
    """Create a mocked FastMCP server."""
    server = MagicMock(spec=FastMCP)
    return server


@pytest.fixture
def mock_os_service():
    """Create a mock OS service for testing."""
    service = AsyncMock(spec=OSDataHubService)
    
    # Set up common async method returns
    service.hello_world.return_value = "Hello, OS DataHub MCP Server!"
    service.check_api_key.return_value = {"status": "valid", "message": "API key is valid"}
    service.get_workflow_context.return_value = {
        "context": "workflow_established", 
        "queryables": ["feature_type", "themes"],
        "collections": ["test-collection-1", "lus-fts-site-1"]
    }
    service.search_features.return_value = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "id": "test-1"}]
    }
    service.get_feature.return_value = {
        "type": "Feature", 
        "id": "test-feature-1",
        "properties": {"name": "Test Feature"}
    }
    service.get_collection_info.return_value = {
        "id": "test-collection",
        "title": "Test Collection",
        "description": "A test collection"
    }
    
    return service


@pytest.fixture
async def os_service(mock_api_client, mock_mcp_server):
    """Create an OS service instance with mocked dependencies."""
    service = OSDataHubService(mock_api_client, mock_mcp_server)
    return service


@pytest.fixture
def sample_bbox():
    """Sample bounding box for testing."""
    return "-1.1,50.9,-0.9,51.1"  # Small area around London


@pytest.fixture
def timeout_config():
    """Timeout configuration for different test types."""
    return {
        "unit": 5,      # 5 seconds for unit tests
        "integration": 30,   # 30 seconds for integration tests  
        "workflow": 180,     # 3 minutes for workflow tests (includes 2min delay)
        "api": 60,          # 1 minute for API tests
    }
