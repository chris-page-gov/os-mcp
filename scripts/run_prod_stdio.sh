#!/usr/bin/env bash
set -euo pipefail

# Launch the production (wheel-installed) STDIO server.
# Requires prior execution of scripts/build_prod_stdio.sh which creates a venv
# at ~/.local/share/os-ngd-prod (override via PROD_VENV).

PROD_VENV_DEFAULT="${HOME}/.local/share/os-ngd-prod"
PROD_VENV="${PROD_VENV:-$PROD_VENV_DEFAULT}"

usage() {
  cat <<'EOF'
Usage: scripts/run_prod_stdio.sh [--debug] [--venv PATH] [--server-name NAME] [--key STDIO_KEY] [--] [extra os-mcp args]

Environment variables:
  PROD_VENV          Override production venv path (default: ~/.local/share/os-ngd-prod)
  STDIO_KEY          Shared secret for stdio auth (default: dev-key if unset)
  OS_API_KEY         Ordnance Survey DataHub API key (required for real data tools)
  OS_MCP_SERVER_NAME Optional display name (e.g. os-ngd-prod)

Examples:
  ./scripts/run_prod_stdio.sh
  STDIO_KEY=mykey OS_API_KEY=abc123 ./scripts/run_prod_stdio.sh --debug
  PROD_VENV=~/.local/share/os-ngd-prod-alt ./scripts/run_prod_stdio.sh

This script ensures:
  * OS_MCP_MODE=prod is set
  * A usable STDIO_KEY is present
  * The console entrypoint 'os-mcp' exists in the production venv
EOF
}

DEBUG_FLAG=""
EXTRA_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) DEBUG_FLAG="--debug"; shift ;;
    --venv) [[ $# -lt 2 ]] && { echo "--venv requires PATH" >&2; exit 1; }; PROD_VENV="$2"; shift 2 ;;
    --server-name) [[ $# -lt 2 ]] && { echo "--server-name requires value" >&2; exit 1; }; export OS_MCP_SERVER_NAME="$2"; shift 2 ;;
    --key) [[ $# -lt 2 ]] && { echo "--key requires value" >&2; exit 1; }; export STDIO_KEY="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    --) shift; EXTRA_ARGS+=("$@"); break ;;
    *) EXTRA_ARGS+=("$1"); shift ;;
  esac
done

if [[ ! -x "${PROD_VENV}/bin/os-mcp" ]]; then
  echo "[run_prod_stdio] ERROR: ${PROD_VENV}/bin/os-mcp not found. Run scripts/build_prod_stdio.sh first." >&2
  exit 1
fi

if [[ -z "${STDIO_KEY:-}" ]]; then
  export STDIO_KEY="dev-key"
  echo "[run_prod_stdio] WARNING: STDIO_KEY not set; defaulting to 'dev-key'." >&2
fi

if [[ -z "${OS_API_KEY:-}" ]]; then
  echo "[run_prod_stdio] NOTE: OS_API_KEY not set; most data tools will return upstream auth errors." >&2
fi

export OS_MCP_MODE=prod
export PROD_VENV

echo "[run_prod_stdio] Launching production STDIO server from ${PROD_VENV}" >&2
echo "[run_prod_stdio] Mode: $OS_MCP_MODE  ServerName: ${OS_MCP_SERVER_NAME:-os-ngd-api}" >&2
echo "[run_prod_stdio] Extra args: ${EXTRA_ARGS[*]:-(none)}" >&2

exec "${PROD_VENV}/bin/os-mcp" --transport stdio ${DEBUG_FLAG} "${EXTRA_ARGS[@]}"
