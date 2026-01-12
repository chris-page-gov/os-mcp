#!/bin/bash
# Claude Code MCP Server launcher
# Usage: claude mcp add os-mcp --scope user -- /path/to/this/script.sh

cd "$(dirname "$0")/.."
exec python -m server --transport stdio
