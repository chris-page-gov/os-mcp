import asyncio
import logging
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()  # This loads variables from .env into the environment
OS_API_KEY = os.environ.get("OS_API_KEY")
if not OS_API_KEY:
    raise RuntimeError("OS_API_KEY is not set in the environment.")

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_mcp():
    # Set headers for dev testing authentication
    headers = {"Authorization": "Bearer dev-token"}

    logger.debug(f"Connecting with headers: {headers}")

    # Connect to server
    async with streamablehttp_client("http://127.0.0.1:8000/mcp/", headers=headers) as (
        read_stream,
        write_stream,
        get_session_id,
    ):
        logger.debug("Connection established")
        async with ClientSession(read_stream, write_stream) as session:
            # Initialise
            logger.debug("Sending initialize request")
            init_result = await session.initialize()
            print(f"Initialized: {init_result}")
            # TODO: This current returns None - need to fix this and understand why this happens
            print(f"Session ID: {get_session_id()}")

            # List tools
            logger.debug("Listing tools")
            tools = await session.list_tools()
            print(f"Available tools: {tools}")

            try:
                logger.debug("Calling hello_world tool")
                result = await session.call_tool("hello_world", {"name": "MCP User"})
                print(f"Tool result: {result}")
            except Exception as e:
                print(f"Error calling tool: {e}")


if __name__ == "__main__":
    asyncio.run(test_mcp())
