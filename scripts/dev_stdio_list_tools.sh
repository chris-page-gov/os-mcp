#!/usr/bin/env bash
set -euo pipefail

# Simple smoke test: start a transient stdio MCP server and list tools
# Uses a dummy OS_API_KEY if none is exported (network calls that require a real key may fail later; listing tools is fine)

: "${STDIO_KEY:=dev-key}"
: "${OS_API_KEY:=dummy-key}" # safe placeholder for tool listing

python - <<'PY'
import os, sys, asyncio
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp import ClientSession

async def main():
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m","server","--transport","stdio"],
        env={
            "STDIO_KEY": os.environ.get("STDIO_KEY", "dev-key"),
            "OS_API_KEY": os.environ.get("OS_API_KEY", "dummy-key"),
            "OS_MCP_SERVER_NAME": "os-mcp-dev"
        }
    )
    async with stdio_client(params) as (r,w):
        async with ClientSession(r,w) as session:
            await session.initialize()
            tools = await session.list_tools()
            print(f"Tool count: {len(tools.tools)}")
            for t in tools.tools:
                print(" -", t.name)

if __name__ == "__main__":
    asyncio.run(main())
PY
