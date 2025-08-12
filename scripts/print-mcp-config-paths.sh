#!/usr/bin/env bash
set -euo pipefail

echo "[MCP Config Path Probe]"

platform="$(uname -s)"
case "$platform" in
  Linux)   CODE_BASE="$HOME/.config" ; CHATGPT_DIR="$HOME/.config/ChatGPT" ; CLAUDE_MAC_BASE="" ;;
  Darwin)  CODE_BASE="$HOME/Library/Application Support" ; CHATGPT_DIR="$HOME/Library/Application Support/ChatGPT" ; CLAUDE_MAC_BASE="$HOME/Library/Application Support/Claude" ;;
  *)       CODE_BASE="$HOME/.config" ; CHATGPT_DIR="$HOME/.config/ChatGPT" ; CLAUDE_MAC_BASE="" ;;
 esac

# Map label -> path
declare -A PATHS
PATHS["VS Code servers.json"]="$CODE_BASE/Code/User/mcp/servers.json"
PATHS["VS Code Insiders servers.json"]="$CODE_BASE/'Code - Insiders'/User/mcp/servers.json"
PATHS["Claude Desktop config (Linux)"]="$HOME/.config/Claude/claude_desktop_config.json"
if [[ -n "$CLAUDE_MAC_BASE" ]]; then
  PATHS["Claude Desktop config (macOS)"]="$CLAUDE_MAC_BASE/claude_desktop_config.json"
fi
PATHS["ChatGPT mcp.json (Linux/macOS expected)"]="$CHATGPT_DIR/mcp.json"
PATHS["ChatGPT mcp.json (Windows pattern)"]="%APPDATA%\\ChatGPT\\mcp.json"

for label in "${!PATHS[@]}"; do
  p="${PATHS[$label]}"
  if [[ "$p" == %APPDATA%* ]]; then
    echo "$label: $p (check on Windows host)"
    continue
  fi
  eval exp_path="$p"
  if [[ -f "$exp_path" ]]; then
    echo "$label: $exp_path (FOUND)"
  else
    echo "$label: $exp_path (missing)"
  fi
 done

dc_file=".devcontainer/devcontainer.json"
if [[ -f $dc_file ]]; then
  echo "\nDevcontainer config: $(realpath "$dc_file")"
else
  echo "\nDevcontainer config: (missing)"
fi

echo -e "\nTip: Create or edit the appropriate config file, then restart the corresponding client (VS Code / Claude / ChatGPT)."
