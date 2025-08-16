#!/usr/bin/env bash
# Convenience examples for interacting with the streamable HTTP MCP endpoint.
# Usage: source or run directly. Requires curl + (optional) jq.
set -euo pipefail

HOST=${HOST:-127.0.0.1}
PORT=${PORT:-8000}
TOKEN=${TOKEN:-dev-token}
SESSION_ID=${SESSION_ID:-$(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)}
ENDPOINT="http://${HOST}:${PORT}/mcp"

hdr(){ echo -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -H "mcp-session-id: ${SESSION_ID}"; }

call(){ local payload=$1; echo "--> ${payload}"; curl -sS $(hdr) --data "${payload}" "${ENDPOINT}" | tee /dev/stderr; echo; }

# 1. Initialize (must be first)
call '{"jsonrpc":"2.0","id":"0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{}}}'
# 2. get_workflow_context
call '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"get_workflow_context","arguments":{}}}'

# Subsequent calls can be appended here.
