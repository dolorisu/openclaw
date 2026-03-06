#!/usr/bin/env bash

set -euo pipefail

EXPECTED=3
WA_TO=""
TG_TO=""
LOG_FILE=""

DEFAULT_PROMPT="Balas tepat 3 paragraf singkat tentang Hatsune Miku. Pisahkan setiap paragraf dengan satu baris kosong."
WA_PROMPT="$DEFAULT_PROMPT"
TG_PROMPT="$DEFAULT_PROMPT"

usage() {
  cat <<'EOF'
Usage:
  verify-multibubble-wa-tg.sh --wa-to <whatsapp-number> --tg-to <telegram-target> [options]

Required:
  --wa-to <number>     WhatsApp target (example: +6289669848875)
  --tg-to <target>     Telegram target (example: @rifuki or 849612359)

Options:
  --expected <n>       Expected new outbound messages per channel (default: 3)
  --wa-prompt <text>   Custom WhatsApp prompt
  --tg-prompt <text>   Custom Telegram prompt
  --log-file <path>    Explicit gateway log file (default: latest /tmp/openclaw/openclaw-*.log)
  -h, --help           Show this help

Exit code:
  0 = both channels pass
  1 = one or both channels fail
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --wa-to)
      WA_TO="${2:-}"
      shift 2
      ;;
    --tg-to)
      TG_TO="${2:-}"
      shift 2
      ;;
    --expected)
      EXPECTED="${2:-}"
      shift 2
      ;;
    --wa-prompt)
      WA_PROMPT="${2:-}"
      shift 2
      ;;
    --tg-prompt)
      TG_PROMPT="${2:-}"
      shift 2
      ;;
    --log-file)
      LOG_FILE="${2:-}"
      shift 2
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

if [[ -z "$WA_TO" || -z "$TG_TO" ]]; then
  echo "Error: --wa-to and --tg-to are required." >&2
  usage
  exit 2
fi

if [[ -z "$LOG_FILE" ]]; then
  LOG_FILE="$(ls -1t /tmp/openclaw/openclaw-*.log 2>/dev/null | head -n 1 || true)"
fi

if [[ -z "$LOG_FILE" || ! -f "$LOG_FILE" ]]; then
  echo "Error: could not find gateway log file." >&2
  exit 2
fi

extract_ids() {
  local channel="$1"
  local log_file="$2"
  python3 - "$channel" "$log_file" <<'PY'
import re
import sys

channel = sys.argv[1]
log_file = sys.argv[2]

if channel == "wa":
    pattern = re.compile(r"Sent message ([A-Z0-9]+) ->")
elif channel == "tg":
    pattern = re.compile(r"telegram sendMessage ok chat=.* message=(\d+)")
else:
    raise SystemExit("unknown channel")

ids = []
with open(log_file, errors="ignore") as handle:
    for line in handle:
        match = pattern.search(line)
        if match:
            ids.append(match.group(1))

for value in ids:
    print(value)
PY
}

run_and_check() {
  local channel="$1"
  local target="$2"
  local prompt="$3"

  local before=()
  local after=()
  while IFS= read -r line; do
    [[ -n "$line" ]] && before+=("$line")
  done < <(extract_ids "$channel" "$LOG_FILE")

  if [[ "$channel" == "wa" ]]; then
    openclaw agent --channel whatsapp --to "$target" --message "$prompt" --deliver
  else
    openclaw agent --channel telegram --to "$target" --message "$prompt" --deliver
  fi

  while IFS= read -r line; do
    [[ -n "$line" ]] && after+=("$line")
  done < <(extract_ids "$channel" "$LOG_FILE")
  local before_len="${#before[@]}"
  local after_len="${#after[@]}"
  local delta=$((after_len - before_len))
  local pass=0

  local new_ids=()
  if (( delta > 0 )); then
    new_ids=("${after[@]:before_len}")
  fi

  if (( delta == EXPECTED )); then
    pass=1
  fi

  if [[ "$channel" == "wa" ]]; then
    echo "[WA] expected=$EXPECTED got=$delta"
  else
    echo "[TG] expected=$EXPECTED got=$delta"
  fi
  if (( ${#new_ids[@]} > 0 )); then
    echo "     ids: ${new_ids[*]}"
  else
    echo "     ids: <none>"
  fi

  if (( pass == 1 )); then
    return 0
  fi
  return 1
}

echo "Using log file: $LOG_FILE"
echo "Running WhatsApp verification..."
wa_ok=0
if run_and_check "wa" "$WA_TO" "$WA_PROMPT"; then
  wa_ok=1
fi

echo
echo "Running Telegram verification..."
tg_ok=0
if run_and_check "tg" "$TG_TO" "$TG_PROMPT"; then
  tg_ok=1
fi

echo
if (( wa_ok == 1 && tg_ok == 1 )); then
  echo "PASS: multi-bubble verification OK on WhatsApp and Telegram"
  exit 0
fi

echo "FAIL: multi-bubble verification failed"
exit 1
