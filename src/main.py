import sys
from mcp.server.fastmcp import FastMCP

from api_service.os_ngd_api import OSNGDAPIClient
from mcp_service.os_ngd_service import OSNGDService


def main():
    """Main entry point"""
    # Print startup message to stderr
    print("OS NGD API MCP Server starting...", file=sys.stderr)
    print("Waiting for requests...", file=sys.stderr)

    # Initialise components
    api_client = OSNGDAPIClient()
    mcp_service = FastMCP("os-ngd-api")

    # Create and run service
    service = OSNGDService(api_client, mcp_service)
    service.run()


if __name__ == "__main__":
    main()
