#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/../patcher/apply-progressive-patch.sh"

if [[ ! -f "$TARGET_SCRIPT" ]]; then
  echo "Missing canonical script: $TARGET_SCRIPT" >&2
  exit 1
fi

echo "[compat] forwarding to $TARGET_SCRIPT" >&2
exec "$TARGET_SCRIPT" "$@"
