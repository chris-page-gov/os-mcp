"""Integration tests for HTTP streamable MCP client.

Ported from src/http_client_test.py with pytest-asyncio fixtures.
"""
import asyncio
import os
import threading
import time
import socket
import pytest
from mcp.client.streamable_http import streamablehttp_client
from server import build_streamable_http_app
import uvicorn
from mcp import ClientSession
from mcp.types import TextContent
from typing import Any

pytestmark = pytest.mark.integration


def extract_text(result: Any) -> str:
    if not result.content:
        return "No content"
    for item in result.content:
        if isinstance(item, TextContent):
            return item.text
    return "Unsupported content"


@pytest.mark.asyncio
async def test_http_search_two_sessions():
    os.environ["BEARER_TOKENS"] = "dev-token"
    headers = {"Authorization": "Bearer dev-token"}

    # Start server in-thread if not already listening
    def port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    # Allocate a free ephemeral port each run to avoid collisions with background dev servers
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        free_port = s.getsockname()[1]

    app, _ = build_streamable_http_app(host="127.0.0.1", port=free_port, debug=False)

    def run():  # pragma: no cover - server loop
        uvicorn.run(app, host="127.0.0.1", port=free_port, log_level="error")

    t = threading.Thread(target=run, daemon=True)
    t.start()
    # Wait until port listens
    for _ in range(100):
        if port_in_use(free_port):
            break
        time.sleep(0.02)

    async def run_session(label: str, usrns: list[str]):
        out: list[tuple[str, str]] = []
        async with streamablehttp_client(f"http://127.0.0.1:{free_port}/mcp", headers=headers) as (
            read_stream,
            write_stream,
            get_session_id,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                sid = get_session_id()
                for u in usrns:
                    try:
                        result = await session.call_tool(
                            "search_features",
                            {
                                "collection_id": "trn-ntwk-street-1",
                                "query_attr": "usrn",
                                "query_attr_value": str(u),
                                "limit": 1,
                            },
                        )
                        extract_text(result)
                        out.append((u, "SUCCESS"))
                        await asyncio.sleep(0.05)
                    except Exception as e:  # pragma: no cover - network variability
                        out.append((u, f"ERROR:{e}"))
                return sid, out

    sess_a, res_a = await run_session("A", ["24501091", "24502114"])  # sample values
    await asyncio.sleep(0.2)
    sess_b, res_b = await run_session("B", ["24502114", "24501091"])  # reversed

    assert sess_a != sess_b
    # Ensure at least one success in each session to assert basic connectivity
    assert any(r[1] == "SUCCESS" for r in res_a)
    assert any(r[1] == "SUCCESS" for r in res_b)
