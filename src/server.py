import sys
from mcp.server.fastmcp import FastMCP

from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSNGDService


def main():
    """Main entry point"""
    # Print startup message to stderr
    print("OS NGD API MCP Server starting...", file=sys.stderr)
    print("Waiting for requests...", file=sys.stderr)

    # Initialise OS NGD API
    api_client = OSAPIClient()

    # Create MCP server
    mcp = FastMCP("os-ngd-api")

    # Create and run service
    service = OSNGDService(api_client, mcp)
    service.run()


if __name__ == "__main__":
    main()
