"""Tests for MCP discovery endpoints and error envelope schema."""
import json
import pytest
from starlette.testclient import TestClient
from server import create_streamable_http_app


@pytest.mark.unit
@pytest.mark.asyncio
async def test_discovery_and_schema_endpoints():
    app, _ = create_streamable_http_app(debug=False, stateless_http=True)
    client = TestClient(app)

    # Auth discovery
    r = client.get("/.well-known/mcp-auth")
    assert r.status_code == 200
    assert r.json()["authMethods"][0]["scheme"] == "bearer"

    # Metadata
    meta = client.get("/.well-known/mcp.json")
    assert meta.status_code == 200
    body = meta.json()
    assert body["name"] == "os-ngd-api"
    assert "errorEnvelope" in body
    assert body["errorEnvelope"]["schema"] == "/schemas/error-envelope.json"

    # Tools list
    tools = client.get("/mcp/tools")
    assert tools.status_code == 200
    assert "tools" in tools.json()

    # Status
    status = client.get("/mcp/status")
    assert status.status_code == 200
    assert status.json()["status"] == "ok"

    # Schema retrieval
    schema_resp = client.get("/schemas/error-envelope.json")
    assert schema_resp.status_code == 200
    schema = schema_resp.json()
    assert schema["type"] == "object"
    assert "error" in schema["required"]
    assert "retry_guidance" in schema["required"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_error_envelope_schema_negative():
    app, _ = create_streamable_http_app(debug=False, stateless_http=True)
    client = TestClient(app)

    schema_resp = client.get("/schemas/error-envelope.json")
    assert schema_resp.status_code == 200
    schema = schema_resp.json()

    # Create object missing required field 'retry_guidance'
    invalid_obj = {"error": "Something broke"}

    # Perform manual validation check (simple)
    missing = [f for f in schema["required"] if f not in invalid_obj]
    assert "retry_guidance" in missing
