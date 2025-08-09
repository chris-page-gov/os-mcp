import argparse
import os
import uvicorn
import time
import json
import inspect
from typing import Any, List, Dict
from importlib import metadata
from utils.logging_config import configure_logging

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService
from mcp.server.fastmcp import FastMCP
from middleware.stdio_middleware import StdioMiddleware
from middleware.http_middleware import HTTPMiddleware
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.responses import JSONResponse

logger = configure_logging()


def main():
    """Main entry point"""
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
    parser.add_argument(
        "--stateless-http",
        action="store_true",
        help="Enable stateless HTTP mode (no session requirement)",
    )
    args = parser.parse_args()

    configure_logging(debug=args.debug)

    logger.info(
        f"OS DataHub API MCP Server starting with {args.transport} transport..."
    )

    api_client = OSAPIClient()

    start_time = time.time()
    pkg_version = "0.0.0"
    try:
        pkg_version = metadata.version("os-mcp")
    except Exception:
        pkg_version = os.environ.get("OS_MCP_VERSION", "0.0.0")

    match args.transport:
        case "stdio":
            logger.info("Starting with stdio transport")

            mcp = FastMCP(
                "os-ngd-api",
                debug=args.debug,
                log_level="DEBUG" if args.debug else "INFO",
            )

            stdio_auth = StdioMiddleware()

            service = OSDataHubService(api_client, mcp, stdio_middleware=stdio_auth)

            # For VS Code MCP integration, skip authentication requirement
            stdio_api_key = os.environ.get("STDIO_KEY", "vscode-mcp")
            if not stdio_auth.authenticate(stdio_api_key):
                logger.warning("Using default authentication for VS Code MCP")
                stdio_auth.authenticate("vscode-mcp")

            service.run()
        case "streamable-http":
            logger.info(f"Starting Streamable HTTP server on {args.host}:{args.port}")

            mcp = FastMCP(
                "os-ngd-api",
                host=args.host,
                port=args.port,
                debug=args.debug,
                json_response=True,
                stateless_http=args.stateless_http,
                log_level="DEBUG" if args.debug else "INFO",
            )

            service = OSDataHubService(api_client, mcp)

            async def auth_discovery(_: Any) -> JSONResponse:
                """Return authentication methods."""
                return JSONResponse(
                    content={"authMethods": [{"type": "http", "scheme": "bearer"}]}
                )

            app = mcp.streamable_http_app()

            app.routes.append(
                Route(
                    "/.well-known/mcp-auth",
                    endpoint=auth_discovery,
                    methods=["GET"],
                )
            )

            async def well_known_metadata(_: Any) -> JSONResponse:
                """Return MCP capability metadata (experimental)."""
                tools_meta: List[Dict[str, Any]] = []
                try:
                    if hasattr(service, "get_tool_metadata"):
                        tools_meta = service.get_tool_metadata()
                except Exception as e:  # pragma: no cover - defensive
                    logger.debug(f"Tool metadata error: {e}")
                content = {
                    "name": "os-ngd-api",
                    "version": pkg_version,
                    "capabilities": {
                        "tools": {"list": True, "call": True},
                        "resources": True,
                        "prompts": True,
                    },
                    "errorEnvelope": {
                        "version": 1,
                        "fields": [
                            "status",
                            "version",
                            "tool",
                            "error_code",
                            "message",
                            "error",
                            "details",
                            "retry_guidance"
                        ],
                        "codes": ["INVALID_INPUT", "GENERAL_ERROR"],
                        "backwardCompatibility": {
                            "legacyErrorField": True,
                            "description": "Top-level 'error' preserved alongside 'message'"
                        }
                    },
                    "preferredModels": {
                        "embedding": ["text-embedding-3-large"],
                        "reasoning": ["gpt-4.1", "claude-3.5-sonnet"],
                        "fast": ["gpt-4o-mini"],
                    },
                    "toolCount": len(tools_meta),
                }
                return JSONResponse(content=content)

            async def list_tools(_: Any) -> JSONResponse:
                """Return a simple list of available tools and their parameters."""
                try:
                    tools_meta = service.get_tool_metadata() if hasattr(service, "get_tool_metadata") else []
                    return JSONResponse(content={"tools": tools_meta})
                except Exception as e:  # pragma: no cover
                    return JSONResponse(
                        status_code=500,
                        content={
                            "error": {"code": "internal_error", "message": str(e)}
                        },
                    )

            async def status(_: Any) -> JSONResponse:
                """Return lightweight service status."""
                uptime = int(time.time() - start_time)
                return JSONResponse(
                    content={
                        "status": "ok",
                        "service": "os-ngd-api",
                        "version": pkg_version,
                        "uptime_seconds": uptime,
                        "transport": "streamable-http",
                        "stateless": args.stateless_http,
                    }
                )

            # Additional discovery/status endpoints
            app.routes.extend(
                [
                    Route(
                        "/.well-known/mcp.json",
                        endpoint=well_known_metadata,
                        methods=["GET"],
                    ),
                    Route("/mcp/tools", endpoint=list_tools, methods=["GET"]),
                    Route("/mcp/status", endpoint=status, methods=["GET"]),
                ]
            )

            # Add custom middleware to FastMCP's app
            app.user_middleware.extend(
                [
                    Middleware(
                        CORSMiddleware,
                        allow_origins=["*"],
                        allow_credentials=True,
                        allow_methods=["GET", "POST", "OPTIONS"],
                        allow_headers=["*"],
                        expose_headers=["*"],
                    ),
                    Middleware(HTTPMiddleware, requests_per_minute=25),
                ]
            )

            uvicorn.run(
                app,
                host=args.host,
                port=args.port,
                log_level="debug" if args.debug else "info",
            )

        case _:
            logger.error(f"Unknown transport: {args.transport}")
            return


if __name__ == "__main__":
    main()
