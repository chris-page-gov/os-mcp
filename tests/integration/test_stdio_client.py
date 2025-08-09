"""Integration test for STDIO MCP server rate limiting (smoke test)."""
import os
import sys
import pytest
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import TextContent
from typing import Any

pytestmark = pytest.mark.integration


def extract_text(result: Any) -> str:
    if not result.content:
        return "No content"
    for item in result.content:
        if isinstance(item, TextContent):
            return item.text
    return "Unsupported"


@pytest.mark.asyncio
async def test_stdio_hello_world_rate_smoke():
    os.environ.setdefault("STDIO_KEY", "test-stdio-key")
    params = StdioServerParameters(
        command=sys.executable,
        args=["src/server.py", "--transport", "stdio"],
        env=os.environ.copy(),
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            result = await session.call_tool("hello_world", {"name": "RateTest"})
            # Second call (may trigger rate limit depending on config)
            _ = await session.call_tool("hello_world", {"name": "RateTest2"})
            assert extract_text(result).startswith("Hello, RateTest")
