import argparse
import uvicorn
import logging
import os

from starlette.applications import Starlette
from starlette.responses import Response, JSONResponse
from starlette.requests import Request
from starlette.routing import Mount, Route
from starlette.middleware import Middleware
from mcp.server.sse import SseServerTransport

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService
from mcp.server.fastmcp import FastMCP
from auth.sse_auth import AuthMiddleware
from auth.stdio_auth import StdioAuthenticator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sse_app(mcp: FastMCP, debug: bool = False) -> Starlette:
    """Create a Starlette application for SSE transport."""

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> Response:
        """Handle SSE connections and return a response when done."""
        # Authentication is handled by middleware
        logger.info(f"SSE connection established from {request.client}")

        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            mcp_server = mcp._mcp_server
            await mcp_server.run(
                streams[0], streams[1], mcp_server.create_initialization_options()
            )

        return Response()

    async def auth_discovery(request: Request) -> Response:
        """Return authentication methods."""
        auth_methods = {
            "authMethods": [
                {"type": "apiKey", "name": "x-api-key", "in": "header"},
                {
                    "type": "oauth2",
                    "flows": {
                        "password": {
                            "tokenUrl": "/token",
                            "scopes": {
                                "read": "Read access",
                                "execute": "Execute tools",
                            },
                        }
                    },
                },
            ]
        }
        return JSONResponse(content=auth_methods)

    # Create Starlette app with routes for SSE and messages
    return Starlette(
        debug=debug,
        routes=[
            Route("/.well-known/mcp-auth", endpoint=auth_discovery, methods=["GET"]),
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        middleware=[Middleware(AuthMiddleware)],
    )


def main():
    """Main entry point"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="OS NGD API MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol to use (stdio or sse)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to for SSE (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to for SSE (default: 8000)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Configure logging level
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=log_level)

    # Print startup message
    logger.info(f"OS NGD API MCP Server starting with {args.transport} transport...")

    # Initialise API client
    api_client = OSAPIClient()

    # Create MCP server
    mcp = FastMCP("os-ngd-api")

    # Create service
    service = OSDataHubService(api_client, mcp)

    # Run with the specified transport
    match args.transport:
        case "stdio":
            logger.info("Starting with stdio transport")

            # Initialise stdio authenticator
            stdio_auth = StdioAuthenticator()

            # Always require an API key
            stdio_api_key = os.environ.get("STDIO_API_KEY")
            if not stdio_api_key:
                logger.error(
                    "Authentication required: STDIO_API_KEY environment variable not set"
                )
                return

            # For now, just check that the key is not empty
            if not stdio_auth.authenticate(stdio_api_key):
                logger.error("Authentication failed: Empty API key")
                return

            service.run()
        case "sse":
            logger.info(f"Starting SSE server on {args.host}:{args.port}")
            # Create Starlette app with SSE support
            starlette_app = create_sse_app(mcp, debug=args.debug)
            # Run with uvicorn
            uvicorn.run(
                starlette_app,
                host=args.host,
                port=args.port,
                log_level="debug" if args.debug else "info",
            )
        case _:
            logger.error(f"Unknown transport: {args.transport}")
            return


if __name__ == "__main__":
    main()
