import argparse
import os
import uvicorn
from typing import Any
from utils.logging_config import configure_logging
import importlib.metadata
import pathlib
import sys

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSDataHubService
from mcp.server.fastmcp import FastMCP
from middleware.stdio_middleware import StdioMiddleware
from middleware.http_middleware import HTTPMiddleware
from middleware.request_id_middleware import RequestIDMiddleware
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
from starlette.responses import JSONResponse, Response
import base64

logger = configure_logging()


def _compute_mode(file_path: str) -> str:
    """Determine runtime mode.

    Precedence:
    1. Explicit override via OS_MCP_MODE env var ("dev" or "prod").
    2. If module file resides inside an installed site-packages directory (prod).
    3. Else dev.
    This avoids fragile substring checks (previously "/src/").
    """
    override = os.environ.get("OS_MCP_MODE")
    if override in {"dev", "prod"}:
        return override

    p = pathlib.Path(file_path).resolve()
    # Heuristic: any sys.path entry containing "site-packages" or dist-packages marks prod install
    site_like = [pathlib.Path(sp).resolve() for sp in sys.path if "site-packages" in sp or "dist-packages" in sp]
    for root in site_like:
        try:
            # If server file is within site-packages tree -> prod
            p.relative_to(root)
            return "prod"
        except Exception:
            continue
    return "dev"


def _resolve_server_name() -> str:
    """Return the MCP server name (env override)"""
    return os.environ.get("OS_MCP_SERVER_NAME", "os-ngd-api")


def build_streamable_http_app(host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Factory that builds the FastMCP streamable HTTP app (used by tests)."""
    mcp = FastMCP(
        _resolve_server_name(),
        host=host,
        port=port,
        debug=debug,
        json_response=True,
        stateless_http=False,
        log_level="DEBUG" if debug else "INFO",
    )
    api_client = OSAPIClient()
    service = OSDataHubService(api_client, mcp)

    async def auth_discovery(_: Any):  # pragma: no cover - trivial
        return JSONResponse(content={"authMethods": [{"type": "http", "scheme": "bearer"}]})

    # Derive version & mode
    try:
        _pkg_version = importlib.metadata.version("os-mcp")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover - dev fallback
        _pkg_version = "0.0.0+unknown"
    _mode = _compute_mode(__file__)

    async def health(_: Any):  # pragma: no cover - trivial simple status
        return JSONResponse(content={"status": "ok", "version": _pkg_version, "mode": _mode})

    # Tiny 16x16 transparent PNG favicon
    _FAVICON_PNG_B64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAAHElEQVQ4T2NkoBAwUqifgYGB4T8GGgKjBpgGhgEAX0kCCVYq0nIAAAAASUVORK5CYII="
    )

    async def favicon(_: Any):  # pragma: no cover - trivial
        return Response(base64.b64decode(_FAVICON_PNG_B64), media_type="image/png")

    app = mcp.streamable_http_app()
    app.routes.append(Route("/.well-known/mcp-auth", endpoint=auth_discovery, methods=["GET"]))
    app.routes.append(Route("/health", endpoint=health, methods=["GET"]))
    app.routes.append(Route("/favicon.ico", endpoint=favicon, methods=["GET"]))
    middlewares = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["*"],
        ),
        Middleware(RequestIDMiddleware),
    ]
    # Skip auth middleware when explicit bypass flag set (used in tests)
    if os.environ.get("OS_MCP_AUTH_BYPASS", "").lower() not in {"1", "true", "yes"}:
        middlewares.append(Middleware(HTTPMiddleware))
    else:
        logger.info("Auth middleware bypassed due to OS_MCP_AUTH_BYPASS")
    app.user_middleware.extend(middlewares)
    return app, service


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
    args = parser.parse_args()

    configure_logging(debug=args.debug)

    # Version & mode logging
    try:
        pkg_version = importlib.metadata.version("os-mcp")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        pkg_version = "0.0.0+unknown"
    mode = _compute_mode(__file__)
    logger.info(
        f"OS DataHub API MCP Server v{pkg_version} ({mode}) starting with {args.transport} transport..."
    )

    api_client = OSAPIClient()

    match args.transport:
        case "stdio":
            logger.info("Starting with stdio transport")

            mcp = FastMCP(
                _resolve_server_name(),
                debug=args.debug,
                log_level="DEBUG" if args.debug else "INFO",
            )

            stdio_auth = StdioMiddleware()

            service = OSDataHubService(api_client, mcp, stdio_middleware=stdio_auth)

            stdio_api_key = os.environ.get("STDIO_KEY")
            if not stdio_api_key or not stdio_auth.authenticate(stdio_api_key):
                # Provide clear stderr message and non-zero exit so MCP client surfaces cause
                logger.error(
                    "STDIO_KEY missing or empty: set STDIO_KEY env var (e.g. export STDIO_KEY=dev-key) before launching stdio transport."
                )
                raise SystemExit(1)

            service.run()

        case "streamable-http":
            logger.info(f"Starting Streamable HTTP server on {args.host}:{args.port}")

            # Warn early if bearer tokens not configured (unless explicit bypass)
            if os.environ.get("OS_MCP_AUTH_BYPASS", "").lower() not in {"1", "true", "yes"}:
                bearer_tokens_env = os.environ.get("BEARER_TOKENS") or os.environ.get("BEARER_TOKEN")
                if not bearer_tokens_env:
                    logger.warning(
                        "BEARER_TOKENS not set (all /mcp HTTP requests will return 401). "
                        "Export BEARER_TOKENS=<token> before starting the server for frontend access."
                    )

            mcp = FastMCP(
                _resolve_server_name(),
                host=args.host,
                port=args.port,
                debug=args.debug,
                json_response=True,
                stateless_http=False,
                log_level="DEBUG" if args.debug else "INFO",
            )

            OSDataHubService(api_client, mcp)

            async def auth_discovery(_: Any) -> JSONResponse:
                """Return authentication methods."""
                return JSONResponse(
                    content={"authMethods": [{"type": "http", "scheme": "bearer"}]}
                )

            async def health(_: Any) -> JSONResponse:  # pragma: no cover - trivial
                return JSONResponse(content={"status": "ok"})

            _FAVICON_PNG_B64 = (
                "iVBORw0KGgoAAAANSUhEUgAAAA4AAAAOCAYAAAAfSC3RAAAAHElEQVQ4T2NkoBAwUqifgYGB4T8GGgKjBpgGhgEAX0kCCVYq0nIAAAAASUVORK5CYII="
            )

            async def favicon(_: Any) -> Response:  # pragma: no cover - trivial
                return Response(base64.b64decode(_FAVICON_PNG_B64), media_type="image/png")

            app = mcp.streamable_http_app()

            app.routes.append(
                Route(
                    "/.well-known/mcp-auth",
                    endpoint=auth_discovery,
                    methods=["GET"],
                )
            )
            app.routes.append(Route("/health", endpoint=health, methods=["GET"]))
            app.routes.append(Route("/favicon.ico", endpoint=favicon, methods=["GET"]))

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
                    Middleware(RequestIDMiddleware),
                    Middleware(HTTPMiddleware),
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
