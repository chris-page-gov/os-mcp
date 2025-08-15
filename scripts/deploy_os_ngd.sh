#!/usr/bin/env bash
set -euo pipefail

# Deploy production (wheel-installed) os-ngd entry for VS Code MCP.
# Creates/updates a dedicated venv and updates servers.json.
# Usage:
#   ./scripts/deploy_os_ngd.sh
#   ./scripts/deploy_os_ngd.sh --python /usr/bin/python3
#   ./scripts/deploy_os_ngd.sh --servers-json ~/.config/vscode/mcp/servers.json

PYTHON_BIN=${PYTHON:-python}
SERVERS_JSON_DEFAULT="$HOME/.config/vscode/mcp/servers.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --python)
      PYTHON_BIN=$2; shift 2;;
    --servers-json)
      SERVERS_JSON_DEFAULT=$2; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

SERVERS_JSON="$SERVERS_JSON_DEFAULT"
VENVDIR="$HOME/.local/share/os-ngd-venv"

# Placeholder token for VS Code env substitution (avoid raw \${env:...} with set -u)
OS_API_PLACEHOLDER='${env:OS_API_KEY}'

echo "[deploy] Python: $(command -v "$PYTHON_BIN")"
"$PYTHON_BIN" -m pip install --quiet --upgrade pip build

echo "[deploy] Building wheel..."
"$PYTHON_BIN" -m build --wheel > /dev/null
LATEST_WHEEL=$(ls -t dist/os_mcp-*.whl 2>/dev/null | head -1 || true)
if [[ -z "$LATEST_WHEEL" ]]; then
  echo "[deploy] ERROR: No os_mcp wheel found in dist/." >&2
  exit 1
fi

echo "[deploy] Ensuring venv: $VENVDIR"
"$PYTHON_BIN" -m venv "$VENVDIR" 2>/dev/null || true
"$VENVDIR/bin/pip" install --quiet --upgrade pip
"$VENVDIR/bin/pip" install --quiet "$LATEST_WHEEL"

CMD_PATH="$VENVDIR/bin/python"
echo "[deploy] Installed wheel -> $CMD_PATH"

mkdir -p "$(dirname "$SERVERS_JSON")"
if [[ ! -f "$SERVERS_JSON" ]]; then
  echo '{"servers":{}}' > "$SERVERS_JSON"
fi

if command -v jq >/dev/null 2>&1; then
  tmp=$(mktemp)
  jq --arg cmd "$CMD_PATH" --arg api "$OS_API_PLACEHOLDER" '.servers["os-ngd"] = {"command": $cmd, "args":["-m","server","--transport","stdio"], "env": {"OS_API_KEY":$api, "STDIO_KEY":"prod-key"}}' "$SERVERS_JSON" > "$tmp"
  mv "$tmp" "$SERVERS_JSON"
  echo "[deploy] Updated os-ngd entry in $SERVERS_JSON (jq)."
else
  echo "[deploy] jq not found; performing minimal text patch (verify JSON manually)."
  cp "$SERVERS_JSON" "$SERVERS_JSON.bak"
  # Remove any existing os-ngd object (best-effort)
  grep -v '"os-ngd"' "$SERVERS_JSON.bak" > "$SERVERS_JSON.tmp" || true
  mv "$SERVERS_JSON.tmp" "$SERVERS_JSON"
  # Insert just after opening servers object
  sed -i "s|{\"servers\":{|{\"servers\":{\"os-ngd\":{\"command\":\"$CMD_PATH\",\"args\":[\"-m\",\"server\",\"--transport\",\"stdio\"],\"env\":{\"OS_API_KEY\":\"$OS_API_PLACEHOLDER\",\"STDIO_KEY\":\"prod-key\"}},|" "$SERVERS_JSON"
fi

echo "[deploy] Done. Restart VS Code or run '@os-ngd list tools' to verify."
