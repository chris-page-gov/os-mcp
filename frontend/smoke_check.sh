#!/usr/bin/env bash
set -euo pipefail
URL="${1:-http://localhost:5173}"
html=$(curl -s "$URL/")
if ! grep -q '<div id="root">' <<<"$html"; then
  echo "[FAIL] root div missing" >&2; exit 1; fi
if ! curl -sf "$URL/src/main.tsx" >/dev/null; then
  echo "[FAIL] main.tsx unreachable" >&2; exit 1; fi
if ! curl -sf "$URL/@vite/client" >/dev/null; then
  echo "[FAIL] vite client unreachable" >&2; exit 1; fi
echo "[OK] Frontend smoke test passed for $URL";
