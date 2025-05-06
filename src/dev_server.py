import sys
from mcp.server.fastmcp import FastMCP
from api_service.os_api import OSAPIClient
from mcp_service.os_service import OSNGDService

# Print startup message
# THIS IS FOR DEV TESTING ONLY
print("Initializing OS NGD API MCP Server for dev...", file=sys.stderr)

# Create the MCP server at module level with a standard name
# IMPORTANT: This variable name must be 'mcp', 'server', or 'app'
# This is a dev server that can be used with mcp dev
server = FastMCP("os-ngd-api")

# Initialise components
api_client = OSAPIClient()

# Initialise service
service = OSNGDService(api_client, server)
