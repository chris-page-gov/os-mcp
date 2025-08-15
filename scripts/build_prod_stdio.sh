#!/usr/bin/env bash
set -euo pipefail

# Build and install a production (wheel) copy of the os-mcp package into
# a dedicated virtual environment intended for a "prod" stdio MCP entry.
#
# Usage (inside devcontainer):
#   ./scripts/build_prod_stdio.sh [TARGET_DIR]
# Default TARGET_DIR: $HOME/.local/share/os-ngd-prod
#
# After running, add/update your user MCP config with the printed JSON snippet
# (container path) so VS Code can launch the prod stdio server independently of
# the editable source (os-mcp-dev) entry.

TARGET_DIR="${1:-$HOME/.local/share/os-ngd-prod}"

echo "[build_prod_stdio] Building wheel..."
python -m pip install --upgrade build >/dev/null 2>&1
python -m build

echo "[build_prod_stdio] Creating venv at: $TARGET_DIR"
rm -rf "$TARGET_DIR"
python -m venv "$TARGET_DIR"

echo "[build_prod_stdio] Selecting latest wheel"
LATEST_WHEEL=$(ls -t dist/os_mcp-*.whl 2>/dev/null | head -1 || true)
if [[ -z "$LATEST_WHEEL" ]]; then
  echo "[build_prod_stdio] ERROR: No wheel found in dist/." >&2
  exit 1
fi
echo "[build_prod_stdio] Installing wheel into venv: $LATEST_WHEEL"
# Ensure no developer PYTHONPATH bleeds into production venv resolution (explicitly empty)
env -u PYTHONPATH "${TARGET_DIR}/bin/pip" install --no-cache-dir --force-reinstall "$LATEST_WHEEL" >/dev/null

# Detect accidental editable/source shadowing (pip show Location pointing at workspace src)
LOCATION=$("${TARGET_DIR}/bin/pip" show os-mcp | awk -F': ' '/^Location/{print $2}')
if [[ "$LOCATION" == *"/workspaces/os-mcp/src"* ]]; then
  echo "[build_prod_stdio][warning] Wheel install resolved to source tree (editable path)."
  echo "[build_prod_stdio][hint] A prior editable install inside the venv or global path leakage may exist."
fi

PY_CMD="$TARGET_DIR/bin/python"
echo "[build_prod_stdio] Done. Python executable: $PY_CMD"

# Placeholder for VS Code env substitution used in emitted JSON (avoid direct ${..} in heredoc under set -u)
PLACEHOLDER='${env:OS_API_KEY}'

cat <<EOF

Add this entry to your (container) user MCP config (e.g. /home/vscode/.vscode-server/data/User/mcp.json):
{
  "os-ngd-prod": {
    "command": "$TARGET_DIR/bin/os-mcp-stdio",
    "args": ["--transport", "stdio"],
    "env": {
  # Use VS Code env substitution; resolved by VS Code at launch
  "OS_API_KEY": "$PLACEHOLDER",
      "STDIO_KEY": "prod-key",
      "OS_MCP_SERVER_NAME": "os-ngd-prod"
    }
  }
}

Next steps:
1. Open (or create) your user MCP config at the path shown above and add/update the snippet.
2. Reload the VS Code window so it picks up the change: Command Palette (Ctrl/Cmd+Shift+P) -> Developer: Reload Window.
3. Start the server one of these ways:
  - Command Palette -> Model Context Protocol: Start Server -> select "os-ngd-prod"
  - In the MCP Servers view (if enabled), click the start ▶ button next to os-ngd-prod
  - Open a chat and reference a tool from os-ngd-prod; the extension will auto-start it.
4. Verify it’s running: check the Output panel (View -> Output -> dropdown: Model Context Protocol / os-ngd-prod) for a startup log line.

If it fails to start, confirm OS_API_KEY is set in your container environment or replace $PLACEHOLDER with a literal key in the config for a quick test.
EOF
