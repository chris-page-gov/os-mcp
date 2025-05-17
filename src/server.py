import argparse
import uvicorn
import os

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.middleware import Middleware
from starlette.routing import Mount, Route
from contextlib import asynccontextmanager

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService
from mcp.server.fastmcp import FastMCP
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from middleware.stdio_middleware import StdioMiddleware
from middleware.http_middleware import HTTPMiddleware
from utils.logging_config import configure_logging

logger = configure_logging()


def create_streamable_http_app(mcp: FastMCP, debug: bool = False) -> Starlette:
    """Create a Starlette application for Streamable HTTP transport."""

    session_manager = StreamableHTTPSessionManager(
        app=mcp._mcp_server,
        json_response=False,
        stateless=False,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette):
        """Manages the lifecycle of the StreamableHTTP session manager."""
        async with session_manager.run():
            yield

    async def handle_mcp_endpoint(scope, receive, send):
        """Handle MCP endpoint requests by delegating to session manager."""
        await session_manager.handle_request(scope, receive, send)

    async def auth_discovery(_):
        """Return authentication methods."""
        auth_methods = {"authMethods": [{"type": "http", "scheme": "bearer"}]}
        return JSONResponse(content=auth_methods)

    # Create Starlette app with routes for Streamable HTTP
    return Starlette(
        debug=debug,
        routes=[
            Route("/.well-known/mcp-auth", endpoint=auth_discovery, methods=["GET"]),
            Mount("/message", app=handle_mcp_endpoint),
        ],
        middleware=[Middleware(HTTPMiddleware)],
        lifespan=lifespan,
    )


def main():
    """Main entry point"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="OS DataHub API MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="Transport protocol to use (stdio or http)",
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Configure logging level
    configure_logging(debug=args.debug)

    # Print startup message
    logger.info(
        f"OS DataHub API MCP Server starting with {args.transport} transport..."
    )

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
            stdio_auth = StdioMiddleware()

            # Handle authentication
            stdio_api_key = os.environ.get("STDIO_API_KEY")
            if not stdio_api_key or not stdio_auth.authenticate(stdio_api_key):
                logger.error("Authentication failed")
                return

            service.run()
        case "http":
            logger.info(f"Starting Streamable HTTP server on {args.host}:{args.port}")
            # Create Starlette app with Streamable HTTP support
            starlette_app = create_streamable_http_app(mcp, debug=args.debug)
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
