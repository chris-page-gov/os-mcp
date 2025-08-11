import os
import pytest
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.testclient import TestClient
from middleware.http_middleware import HTTPMiddleware


def make_app(requests_per_minute: int = 10):
    async def endpoint(_):  # pragma: no cover - trivial
        return Response("ok")

    return Starlette(
        routes=[Route("/secure", endpoint=endpoint, methods=["GET"])],
        middleware=[Middleware(HTTPMiddleware, requests_per_minute=requests_per_minute)],
    )


@pytest.mark.unit
def test_valid_token_allows_request():
    os.environ["BEARER_TOKENS"] = "tok123"
    app = make_app()
    client = TestClient(app)
    r = client.get("/secure", headers={"Authorization": "Bearer tok123"})
    assert r.status_code == 200


@pytest.mark.unit
def test_invalid_token_rejected():
    os.environ["BEARER_TOKENS"] = "tok123"
    app = make_app()
    client = TestClient(app)
    r = client.get("/secure", headers={"Authorization": "Bearer bad"})
    assert r.status_code == 401


@pytest.mark.unit
def test_origin_whitelist_allows():
    os.environ["BEARER_TOKENS"] = "tok123"
    os.environ["ALLOWED_ORIGINS"] = "example.com"
    app = make_app()
    client = TestClient(app)
    r = client.get(
        "/secure",
        headers={
            "Authorization": "Bearer tok123",
            "Origin": "http://example.com",
        },
    )
    assert r.status_code == 200


@pytest.mark.unit
def test_invalid_origin_blocked():
    os.environ["BEARER_TOKENS"] = "tok123"
    os.environ.pop("ALLOWED_ORIGINS", None)
    app = make_app()
    client = TestClient(app)
    r = client.get(
        "/secure",
        headers={
            "Authorization": "Bearer tok123",
            "Origin": "http://evil.com",
        },
    )
    assert r.status_code == 403


@pytest.mark.unit
def test_browser_plugin_user_agent_blocked():
    os.environ["BEARER_TOKENS"] = "tok123"
    app = make_app()
    client = TestClient(app)
    r = client.get(
        "/secure",
        headers={
            "Authorization": "Bearer tok123",
            "User-Agent": "Chrome-Extension Something",
        },
    )
    assert r.status_code == 403
