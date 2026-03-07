#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

MULTIBUBBLE_SCRIPT="$SCRIPT_DIR/apply-multibubble-patch.py"
PROGRESSIVE_SCRIPT="$SCRIPT_DIR/apply-progressive.sh"
TAIL_GUARD_SCRIPT="$SCRIPT_DIR/apply-wa-progress-tail-guard.py"
OUTBOUND_DEDUPE_SCRIPT="$SCRIPT_DIR/apply-wa-outbound-dedupe.py"
RESET_PROMPT_SCRIPT="$SCRIPT_DIR/apply-wa-reset-prompt.py"

MODE="apply"
RESTART_GATEWAY=1
FORCE_MULTIBUBBLE=0
PROGRESSIVE_MODE="enable"

usage() {
  cat <<'EOF'
Usage:
  openclaw-patcher.sh [--status] [--no-restart] [--force-multibubble]
                      [--progressive|--no-progressive]

Options:
  --status             Show status only, do not apply patches
  --no-restart         Skip gateway restart (apply mode only)
  --force-multibubble  Add --force to multi-bubble patcher
  --progressive        Enable progressive mode (default)
  --no-progressive     Disable progressive mode (final-only replies)
  -h, --help           Show this help

Sequence (apply mode):
  1) Multi-bubble patch (WA + Telegram + Telegram bot path)
  2) Progressive updates patch (enable or disable)
  3) WA progress tail guard patch (progressive mode only)
  4) WA outbound dedupe/fence patch
  5) WA reset prompt hardening patch
  6) Restart gateway (unless --no-restart)
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
    --progressive)
      PROGRESSIVE_MODE="enable"
      shift
      ;;
    --no-progressive)
      PROGRESSIVE_MODE="disable"
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
if [[ ! -f "$OUTBOUND_DEDUPE_SCRIPT" ]]; then
  echo "Missing script: $OUTBOUND_DEDUPE_SCRIPT" >&2
  exit 1
fi
if [[ ! -f "$RESET_PROMPT_SCRIPT" ]]; then
  echo "Missing script: $RESET_PROMPT_SCRIPT" >&2
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
  echo
  echo "== WA outbound dedupe status =="
  python3 "$OUTBOUND_DEDUPE_SCRIPT" --status
  echo
  echo "== WA reset prompt status =="
  python3 "$RESET_PROMPT_SCRIPT" --status
  exit 0
fi

MULTIBUBBLE_ARGS=(--strict --channels whatsapp,telegram)
if [[ "$FORCE_MULTIBUBBLE" -eq 1 ]]; then
  MULTIBUBBLE_ARGS+=(--force)
fi

echo "== Step 1/6: Multi-bubble patch =="
python3 "$MULTIBUBBLE_SCRIPT" "${MULTIBUBBLE_ARGS[@]}"

echo
echo "== Step 2/6: Progressive updates patch ($PROGRESSIVE_MODE) =="
if [[ "$PROGRESSIVE_MODE" == "disable" ]]; then
  "$PROGRESSIVE_SCRIPT" --disable
else
  "$PROGRESSIVE_SCRIPT" --enable
fi

echo
if [[ "$PROGRESSIVE_MODE" == "disable" ]]; then
  echo "== Step 3/6: WA progress tail guard =="
  echo "Skipped (progressive mode disabled)."
else
  echo "== Step 3/6: WA progress tail guard =="
  python3 "$TAIL_GUARD_SCRIPT" --strict
fi

echo
echo "== Step 4/6: WA outbound dedupe/fence patch =="
python3 "$OUTBOUND_DEDUPE_SCRIPT"

echo
echo "== Step 5/6: WA reset prompt hardening patch =="
python3 "$RESET_PROMPT_SCRIPT"

if [[ "$RESTART_GATEWAY" -eq 1 ]]; then
  echo
  echo "== Step 6/6: Restart gateway =="
  openclaw gateway restart
else
  echo
  echo "Skipped gateway restart (--no-restart)."
fi

echo
echo "Done."
