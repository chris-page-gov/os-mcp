import argparse
import os
from utils.logging_config import configure_logging

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService
from mcp.server.fastmcp import FastMCP
from middleware.stdio_middleware import StdioMiddleware
from middleware.http_middleware import HTTPMiddleware
from starlette.middleware import Middleware
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager

logger = configure_logging()


def main():
    """Main entry point"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description="OS DataHub API MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="Transport protocol to use (stdio or streamable-http)",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind to (default: 8000)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args()

    # Configure logging level
    configure_logging(debug=args.debug)

    logger.info(
        f"OS DataHub API MCP Server starting with {args.transport} transport..."
    )

    # Initialise API client
    api_client = OSAPIClient()

    # Create MCP server with settings
    mcp = FastMCP(
        "os-ngd-api",
        host=args.host,
        port=args.port,
        debug=args.debug,
        json_response=True,
        log_level="DEBUG" if args.debug else "INFO",
    )

    # Create service (this registers all tools with the MCP server)
    service = OSDataHubService(api_client, mcp)

    # Run with the specified transport
    match args.transport:
        case "stdio":
            logger.info("Starting with stdio transport")

            # Initialise stdio authenticator
            stdio_auth = StdioMiddleware()

            # Handle authentication
            stdio_api_key = os.environ.get("STDIO_KEY")
            if not stdio_api_key or not stdio_auth.authenticate(stdio_api_key):
                logger.error("Authentication failed")
                return

            # Run the service using stdio transport
            service.run()  # This works because the default in FastMCP.run() is "stdio"
        case "streamable-http":
            logger.info(f"Starting Streamable HTTP server on {args.host}:{args.port}")

            # Instead of using mcp.run(), create our own Starlette app with our middleware
            if mcp._session_manager is None:
                from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
                mcp._session_manager = StreamableHTTPSessionManager(
                    app=mcp._mcp_server,
                    event_store=mcp._event_store,
                    json_response=mcp.settings.json_response,
                    stateless=mcp.settings.stateless_http,
                )

            @asynccontextmanager
            async def lifespan(app: Starlette):
                """Manages the lifecycle of the StreamableHTTP session manager."""
                async with mcp.session_manager.run():
                    yield

            async def handle_mcp_endpoint(scope, receive, send):
                """Handle MCP endpoint requests by delegating to session manager."""
                await mcp.session_manager.handle_request(scope, receive, send)

            async def auth_discovery(_):
                """Return authentication methods."""
                auth_methods = {"authMethods": [{"type": "http", "scheme": "bearer"}]}
                return JSONResponse(content={"authMethods": [{"type": "http", "scheme": "bearer"}]})

            # Create Starlette app with routes for Streamable HTTP and our middleware
            app = Starlette(
                debug=args.debug,
                routes=[
                    Route("/.well-known/mcp-auth", endpoint=auth_discovery, methods=["GET"]),
                    Mount("/mcp/", app=handle_mcp_endpoint),
                ],
                middleware=[Middleware(HTTPMiddleware)],
                lifespan=lifespan,
            )

            # Run using uvicorn!!
            import uvicorn
            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                log_level="debug" if args.debug else "info"
            )

        case _:
            logger.error(f"Unknown transport: {args.transport}")
            return


if __name__ == "__main__":
    main()
