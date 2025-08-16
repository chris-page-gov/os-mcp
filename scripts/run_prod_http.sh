#!/usr/bin/env bash
set -euo pipefail

# Launch the production (wheel-installed) HTTP server (streamable-http transport).
# Assumes scripts/build_prod_stdio.sh has created a prod venv with console script 'os-mcp'
# at ~/.local/share/os-ngd-prod (override via PROD_VENV).
# Exposes host/port 0.0.0.0:8000 by default so host machine (e.g. Claude Desktop, browser)
# can reach it via 127.0.0.1 when using docker run -p 8000:8000 or devcontainer port forwarding.

PROD_VENV_DEFAULT="${HOME}/.local/share/os-ngd-prod"
PROD_VENV="${PROD_VENV:-$PROD_VENV_DEFAULT}"
HOST="0.0.0.0"
PORT="8000"

usage() {
  cat <<'EOF'
Usage: scripts/run_prod_http.sh [--debug] [--venv PATH] [--host HOST] [--port PORT] \
       [--server-name NAME] [--tokens TOKEN[,TOKEN2]] [--auth-bypass] [--] [extra os-mcp args]

Environment variables:
  PROD_VENV           Override production venv path (default: ~/.local/share/os-ngd-prod)
  OS_API_KEY          Ordnance Survey DataHub API key (required for real data tools)
  BEARER_TOKENS       Comma-separated list of accepted Bearer tokens (alt to --tokens)
  OS_MCP_SERVER_NAME  Optional display name (e.g. os-ngd-http)
  OS_MCP_AUTH_BYPASS  If set to 1/true/yes, skips HTTP auth middleware (TESTING ONLY)

Examples:
  ./scripts/run_prod_http.sh
  BEARER_TOKENS=dev-token OS_API_KEY=abc123 ./scripts/run_prod_http.sh --debug
  ./scripts/run_prod_http.sh --tokens dev-token,alt-token --port 9000
  PROD_VENV=~/.local/share/os-ngd-prod-alt ./scripts/run_prod_http.sh --server-name os-ngd-prod-http

This script ensures:
  * OS_MCP_MODE=prod is set
  * A Bearer token is configured unless --auth-bypass is used
  * The console entrypoint 'os-mcp' exists in the production venv
EOF
}

DEBUG_FLAG=""
EXTRA_ARGS=()
TOKENS_FROM_FLAG=""
AUTH_BYPASS="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) DEBUG_FLAG="--debug"; shift ;;
    --venv) [[ $# -lt 2 ]] && { echo "--venv requires PATH" >&2; exit 1; }; PROD_VENV="$2"; shift 2 ;;
    --host) [[ $# -lt 2 ]] && { echo "--host requires value" >&2; exit 1; }; HOST="$2"; shift 2 ;;
    --port) [[ $# -lt 2 ]] && { echo "--port requires value" >&2; exit 1; }; PORT="$2"; shift 2 ;;
    --server-name) [[ $# -lt 2 ]] && { echo "--server-name requires value" >&2; exit 1; }; export OS_MCP_SERVER_NAME="$2"; shift 2 ;;
    --tokens) [[ $# -lt 2 ]] && { echo "--tokens requires value" >&2; exit 1; }; TOKENS_FROM_FLAG="$2"; shift 2 ;;
    --auth-bypass) AUTH_BYPASS="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    --) shift; EXTRA_ARGS+=("$@" ); break ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

if [[ ! -x "${PROD_VENV}/bin/os-mcp" ]]; then
  echo "[run_prod_http] ERROR: ${PROD_VENV}/bin/os-mcp not found. Run scripts/build_prod_stdio.sh first." >&2
  exit 1
fi

# Determine bearer tokens
if [[ "${AUTH_BYPASS}" == "true" ]]; then
  export OS_MCP_AUTH_BYPASS=1
  echo "[run_prod_http] WARNING: Auth bypass enabled (NOT FOR PRODUCTION)." >&2
else
  if [[ -n "${TOKENS_FROM_FLAG}" ]]; then
    export BEARER_TOKENS="${TOKENS_FROM_FLAG}"
  fi
  if [[ -z "${BEARER_TOKENS:-}" ]]; then
    export BEARER_TOKENS="dev-token"
    echo "[run_prod_http] WARNING: BEARER_TOKENS not set; defaulting to 'dev-token'." >&2
  fi
fi

if [[ -z "${OS_API_KEY:-}" ]]; then
  echo "[run_prod_http] NOTE: OS_API_KEY not set; most data tools will return upstream auth errors." >&2
fi

export OS_MCP_MODE=prod
export PROD_VENV

echo "[run_prod_http] Launching production HTTP server from ${PROD_VENV}" >&2
echo "[run_prod_http] Host: ${HOST}  Port: ${PORT}  Mode: $OS_MCP_MODE  ServerName: ${OS_MCP_SERVER_NAME:-os-ngd-api}" >&2
[[ -n "${BEARER_TOKENS:-}" ]] && echo "[run_prod_http] Bearer tokens: ${BEARER_TOKENS}" >&2
[[ -n "${OS_MCP_AUTH_BYPASS:-}" ]] && echo "[run_prod_http] Auth bypass active" >&2
echo "[run_prod_http] Extra args: ${EXTRA_ARGS[*]:-(none)}" >&2

exec "${PROD_VENV}/bin/os-mcp" --transport streamable-http --host "${HOST}" --port "${PORT}" ${DEBUG_FLAG} "${EXTRA_ARGS[@]}"
