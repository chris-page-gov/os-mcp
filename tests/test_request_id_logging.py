import logging
import pytest
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.testclient import TestClient
from utils.logging_config import configure_logging
from middleware.request_id_middleware import RequestIDMiddleware, REQUEST_ID_HEADER


@pytest.mark.unit
def test_request_id_header_and_log() -> None:
    logs: list[logging.LogRecord] = []

    class ListHandler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:  # pragma: no cover - trivial
            logs.append(record)

    logger = configure_logging(debug=True, json_logs=True)
    handler = ListHandler()
    logger.addHandler(handler)

    from starlette.requests import Request

    async def endpoint(request: Request) -> JSONResponse:  # pragma: no cover - simple
        return JSONResponse({"ok": True})

    app = Starlette(
        routes=[Route("/ping", endpoint=endpoint)],
        middleware=[Middleware(RequestIDMiddleware)],
    )
    client = TestClient(app)
    r = client.get("/ping")
    assert r.status_code == 200
    assert REQUEST_ID_HEADER in r.headers
    # Ensure at least one log entry was captured (middleware debug line)
    assert any(getattr(rec, 'msg', '').startswith('Request ') for rec in logs)
