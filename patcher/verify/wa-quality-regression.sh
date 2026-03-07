#!/usr/bin/env bash

set -euo pipefail

WA_TO=""
SESSION_ID=""
LOG_FILE=""
TIMEOUT=360
RUN_COMPLEX=0
RETRY_ON_LOCK=1

usage() {
  cat <<'EOF'
Usage:
  wa-quality-regression.sh --to <group-jid-or-e164> [options]

Required:
  --to <target>              WhatsApp target (example: 1203...@g.us or +62...)

Options:
  --session-id <id>          Optional explicit session id
  --log-file <path>          Explicit gateway log file
  --timeout <seconds>        Agent timeout per test (default: 360)
  --complex                  Run one complex software-engineer scenario
  --no-retry-lock            Do not auto-retry when lock/timeout detected
  -h, --help                 Show this help

Behavior:
  1) Sends /reset first
  2) Runs minimal gated tests (smoke + fenced block)
  3) Optionally runs one complex scenario
  4) Reports WA delta for each step
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --to)
      WA_TO="${2:-}"
      shift 2
      ;;
    --session-id)
      SESSION_ID="${2:-}"
      shift 2
      ;;
    --log-file)
      LOG_FILE="${2:-}"
      shift 2
      ;;
    --timeout)
      TIMEOUT="${2:-}"
      shift 2
      ;;
    --complex)
      RUN_COMPLEX=1
      shift
      ;;
    --no-retry-lock)
      RETRY_ON_LOCK=0
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

if [[ -z "$WA_TO" ]]; then
  echo "Error: --to is required." >&2
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

HASH="sha256:58faacefba6e"
FAILURES=0

count_sent() {
  rg -c "Sent message .* -> ${HASH}\\b" "$LOG_FILE" 2>/dev/null || true
}

run_agent_deliver() {
  local msg="$1"
  local out_file="$2"
  if [[ -n "$SESSION_ID" ]]; then
    openclaw agent --channel whatsapp --to "$WA_TO" --session-id "$SESSION_ID" --timeout "$TIMEOUT" --message "$msg" --deliver >"$out_file" 2>&1
  else
    openclaw agent --channel whatsapp --to "$WA_TO" --timeout "$TIMEOUT" --message "$msg" --deliver >"$out_file" 2>&1
  fi
}

run_step() {
  local name="$1"
  local msg="$2"
  local out_file="/tmp/wa_regression_${name}.txt"
  local before after delta
  before="$(count_sent)"

  if ! run_agent_deliver "$msg" "$out_file"; then
    if (( RETRY_ON_LOCK == 1 )) && rg -q "session file locked|gateway timeout" "$out_file"; then
      echo "[$name] lock/timeout detected -> restarting gateway and retry once"
      openclaw gateway restart >/tmp/wa_regression_gateway_restart.txt 2>&1 || true
      if ! run_agent_deliver "$msg" "$out_file"; then
        echo "[$name] command failed after retry"
        sed -n '1,40p' "$out_file"
        FAILURES=$((FAILURES + 1))
        return
      fi
    else
      echo "[$name] command failed"
      sed -n '1,40p' "$out_file"
      FAILURES=$((FAILURES + 1))
      return
    fi
  fi

  after="$(count_sent)"
  delta=$((after - before))
  echo "[$name] WA_DELTA=$delta"
  if (( delta < 1 )); then
    echo "[$name] no outbound message detected"
    sed -n '1,30p' "$out_file"
    FAILURES=$((FAILURES + 1))
  fi
}

echo "Using log: $LOG_FILE"
echo "Target: $WA_TO"
if [[ -n "$SESSION_ID" ]]; then
  echo "Session: $SESSION_ID"
fi

run_step "00_reset" "/reset"
run_step "01_smoke" "Balas satu bubble: OK regression smoke."
run_step "02_fenced_tree" "Balas SATU fenced code block berisi tree mini 5 baris dan footer total. Jangan ada teks di luar code block."

if (( RUN_COMPLEX == 1 )); then
  run_step "03_complex" "Buat task manager fullstack sederhana-menengah (Express+SQLite+frontend) live port 80. Progress per fase format Progress/Path/Command/Evidence (raw 1-3 baris), final ringkas dengan curl+ss+ps tanpa placeholder."
fi

echo
if (( FAILURES == 0 )); then
  echo "PASS: WA regression checks passed"
  exit 0
fi

echo "FAIL: WA regression checks failures=$FAILURES"
exit 1
