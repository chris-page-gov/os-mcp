#!/usr/bin/env bash
set -euo pipefail
# Install / trust a corporate root CA inside the container.
# Usage: scripts/setup_corp_ca.sh certs/corp-root.pem
# The script copies the PEM to /usr/local/share/ca-certificates/ and updates the trust store.

if [ "${1:-}" = "" ]; then
  echo "Usage: $0 path/to/corp-root.pem" >&2
  exit 1
fi
SRC=$1
if [ ! -f "$SRC" ]; then
  echo "File not found: $SRC" >&2
  exit 1
fi
BASENAME=$(basename "$SRC")
DEST="/usr/local/share/ca-certificates/${BASENAME%.pem}.crt"
cp "$SRC" "$DEST"
update-ca-certificates
echo "Installed corporate CA: $DEST"
