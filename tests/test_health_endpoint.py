import os
import threading
import time
import socket
import uvicorn
import pytest
from server import build_streamable_http_app  # type: ignore[import-untyped]
import http.client

pytestmark = pytest.mark.integration

def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def test_health_endpoint() -> None:
    os.environ["BEARER_TOKENS"] = "dev-token"
    port = 8010

    if not port_in_use(port):
        app, _ = build_streamable_http_app(host="127.0.0.1", port=port, debug=False)

        def run() -> None:  # pragma: no cover
            uvicorn.run(app, host="127.0.0.1", port=port, log_level="error")

        t = threading.Thread(target=run, daemon=True)
        t.start()
        for _ in range(50):
            if port_in_use(port):
                break
            time.sleep(0.05)

    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.request("GET", "/health")
    resp = conn.getresponse()
    body = resp.read().decode()
    assert resp.status == 200, body
    assert '"status":"ok"' in body or '"status": "ok"' in body
    conn.close()
