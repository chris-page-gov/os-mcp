from server import build_streamable_http_app
from starlette.testclient import TestClient


def test_favicon_public_access():
    """Favicon should be served publicly without auth and be a PNG payload."""
    app, _service = build_streamable_http_app(debug=False)

    with TestClient(app) as client:
        resp = client.get("/favicon.ico")
        assert resp.status_code == 200
        # Content type should indicate PNG image
        assert resp.headers.get("content-type", "").startswith("image/png")
        # Ensure some bytes returned
        assert len(resp.content) > 0
