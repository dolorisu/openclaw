#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MULTIBUBBLE_SCRIPT="$SCRIPT_DIR/apply-multibubble-patch.py"
PROGRESSIVE_SCRIPT="$SCRIPT_DIR/apply-progressive-patch.sh"
TAIL_GUARD_SCRIPT="$SCRIPT_DIR/apply-wa-progress-tail-guard.py"

MODE="apply"
RESTART_GATEWAY=1
FORCE_MULTIBUBBLE=0

usage() {
  cat <<'EOF'
Usage:
  run-openclaw-patches.sh [--status] [--no-restart] [--force-multibubble]

Options:
  --status             Show status only, do not apply patches
  --no-restart         Skip gateway restart (apply mode only)
  --force-multibubble  Add --force to multi-bubble patcher
  -h, --help           Show this help

Sequence (apply mode):
  1) Multi-bubble patch (WA + Telegram + Telegram bot path)
  2) Progressive updates patch
  3) WA progress tail guard patch
  4) Restart gateway (unless --no-restart)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --status)
      MODE="status"
      shift
      ;;
    --no-restart)
      RESTART_GATEWAY=0
      shift
      ;;
    --force-multibubble)
      FORCE_MULTIBUBBLE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! -f "$MULTIBUBBLE_SCRIPT" ]]; then
  echo "Missing script: $MULTIBUBBLE_SCRIPT" >&2
  exit 1
fi
if [[ ! -f "$PROGRESSIVE_SCRIPT" ]]; then
  echo "Missing script: $PROGRESSIVE_SCRIPT" >&2
  exit 1
fi
if [[ ! -f "$TAIL_GUARD_SCRIPT" ]]; then
  echo "Missing script: $TAIL_GUARD_SCRIPT" >&2
  exit 1
fi

if [[ "$MODE" == "status" ]]; then
  echo "== Multi-bubble status =="
  python3 "$MULTIBUBBLE_SCRIPT" --status
  echo
  echo "== Progressive updates status =="
  "$PROGRESSIVE_SCRIPT" --status
  echo
  echo "== WA tail guard status =="
  python3 "$TAIL_GUARD_SCRIPT" --status
  exit 0
fi

MULTIBUBBLE_ARGS=(--strict --channels whatsapp,telegram)
if [[ "$FORCE_MULTIBUBBLE" -eq 1 ]]; then
  MULTIBUBBLE_ARGS+=(--force)
fi

echo "== Step 1/4: Multi-bubble patch =="
python3 "$MULTIBUBBLE_SCRIPT" "${MULTIBUBBLE_ARGS[@]}"

echo
echo "== Step 2/4: Progressive updates patch =="
"$PROGRESSIVE_SCRIPT"

echo
echo "== Step 3/4: WA progress tail guard =="
python3 "$TAIL_GUARD_SCRIPT" --strict

if [[ "$RESTART_GATEWAY" -eq 1 ]]; then
  echo
  echo "== Step 4/4: Restart gateway =="
  openclaw gateway restart
else
  echo
  echo "Skipped gateway restart (--no-restart)."
fi

echo
echo "Done."
