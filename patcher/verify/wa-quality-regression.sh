#!/usr/bin/env bash

set -euo pipefail

WA_TO=""
SESSION_ID=""
LOG_FILE=""
TIMEOUT=360
RUN_COMPLEX=0
RUN_COMPREHENSIVE=0
RETRY_ON_LOCK=1
STRICT_FORMAT=1

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
  --comprehensive            Run extended edge/stability suite (includes --complex)
  --no-strict-format         Skip strict output-shape checks (delta only)
  --no-retry-lock            Do not auto-retry when lock/timeout detected
  -h, --help                 Show this help

Behavior:
  1) Sends /reset first
  2) Runs minimal gated tests (smoke + fenced block)
  3) Optionally runs one complex scenario
  4) Optionally runs comprehensive edge/stability scenarios
  5) Reports WA delta for each step
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
    --comprehensive)
      RUN_COMPREHENSIVE=1
      RUN_COMPLEX=1
      shift
      ;;
    --no-strict-format)
      STRICT_FORMAT=0
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

FAILURES=0

count_sent() {
  rg -c "Sent message" "$LOG_FILE" 2>/dev/null || true
}

has_meaningful_output() {
  local out_file="$1"
  if [[ ! -s "$out_file" ]]; then
    return 1
  fi
  if rg -q "session file locked|gateway timeout|command failed|No route to host|ECONNREFUSED|ETIMEDOUT" "$out_file"; then
    return 1
  fi
  return 0
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
    if (( RETRY_ON_LOCK == 1 )) && rg -q "session file locked|gateway timeout|rate-overlimit" "$out_file"; then
      echo "[$name] lock/timeout detected -> restarting gateway and retry once"
      if rg -q "rate-overlimit" "$out_file"; then
        sleep 8
      fi
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
    if has_meaningful_output "$out_file"; then
      echo "[$name] WA_DELTA=0 but meaningful output captured (log probe fallback)"
    else
      echo "[$name] no outbound message detected"
      sed -n '1,30p' "$out_file"
      FAILURES=$((FAILURES + 1))
      return
    fi
  fi

  if (( STRICT_FORMAT == 1 )); then
    if ! validate_shape "$name" "$out_file"; then
      FAILURES=$((FAILURES + 1))
      return
    fi
  fi
}

validate_shape() {
  local name="$1"
  local out_file="$2"

  case "$name" in
    00_reset)
      if ! rg -q '✅ New session started\.' "$out_file"; then
        echo "[$name] invalid reset acknowledgement"
        sed -n '1,40p' "$out_file"
        return 1
      fi
      return 0
      ;;
    02_fenced_tree)
      if ! python3 - "$out_file" <<'PY'
import sys
text=open(sys.argv[1],encoding='utf-8',errors='ignore').read().strip()
if not text:
    raise SystemExit(1)
if not text.startswith('```') or not text.endswith('```'):
    raise SystemExit(1)
if text.count('```') != 2:
    raise SystemExit(1)
PY
      then
        echo "[$name] fenced block shape invalid"
        sed -n '1,60p' "$out_file"
        return 1
      fi
      return 0
      ;;
    03_ops_apt|04_search|05_complex|06_tech_lane|08_error_handling|09_multistep_ops|10_long_output|11_mixed_context|12_stability_rapid|13_recovery)
      ;;
    *)
      return 0
      ;;
  esac

if ! python3 - "$name" "$out_file" <<'PY'
import re,sys
name=sys.argv[1]
text=open(sys.argv[2],encoding='utf-8',errors='ignore').read()

def has(label):
    return re.search(label, text, re.I|re.M) is not None

def pass_claim_conflicts_with_evidence(payload):
    negative=re.compile(r'command not found|not authenticated|permission denied|\berror\b|\bfailed\b', re.I)
    evidence_markers=list(re.finditer(r'(^|\n)\s*(?:📋\s*)?Evidence\s*:\s*', payload, re.I))
    for marker in evidence_markers:
        remaining=payload[marker.end():]
        block=re.match(r'\s*```[^\n]*\n([\s\S]*?)\n\s*```', remaining)
        if not block:
            continue
        evidence_block=block.group(1)
        tail=remaining[block.end():]
        status_window='\n'.join(tail.splitlines()[:6])
        pass_only=bool(re.search(r'\bPASS\b', status_window, re.I)) and not bool(re.search(r'\bFAIL\b', status_window, re.I))
        if pass_only and negative.search(evidence_block):
            return True
    return False

checks=[]
if name in ("03_ops_apt", "05_complex"):
    progress=len(re.findall(r'(^|\n)\s*(?:⏳\s*)?Progress\s*:', text, re.I))
    path=len(re.findall(r'(^|\n)\s*(?:📁\s*)?Path\s*:', text, re.I))
    cmd=len(re.findall(r'(^|\n)\s*(?:🔧\s*)?Command\s*:', text, re.I))
    ev=len(re.findall(r'(^|\n)\s*(?:📋\s*)?Evidence\s*:', text, re.I))
    checks += [progress >= 1, path >= progress, cmd >= progress, ev >= progress, has(r'(?:✅\s*)?Hasil\s*:')]
    checks += ['```' in text]

    if name == "05_complex":
        # Evidence fidelity gate: each Evidence label should be followed by a fenced raw excerpt.
        evidence_blocks=[]
        evidence_markers=list(re.finditer(r'(^|\n)\s*(?:📋\s*)?Evidence\s*:\s*', text, re.I))
        for marker in evidence_markers:
            remaining=text[marker.end():]
            block=re.match(r'\s*```[^\n]*\n([\s\S]*?)\n\s*```', remaining)
            if block:
                evidence_blocks.append(block.group(1).strip())

        raw_token=re.compile(
            r'(?:\b(?:tcp|udp|LISTEN|ESTAB|HTTP/[0-9.]+|http/[0-9.]+|Active:|Main PID|PID|ii\s|Hit:|Get:|Err:|failed|running|Port\s+free|still\s+in\s+use|Exit\s+code|Operation\s+not\s+permitted|permission\s+denied)\b|/[^\s]+|:[0-9]{1,5}|\b[0-9]{2,7}\b|\b(?:0\.0\.0\.0|127\.0\.0\.1|localhost)\b)',
            re.I,
        )
        synthetic_phrase=re.compile(
            r'output\s+menunjukkan|status\s+(?:active|inactive)|terlihat\s+bahwa|berhasil\s+dijalankan|ringkasan\s+hasil|secara\s+garis\s+besar|intinya',
            re.I,
        )

        checks += [progress >= 2, len(evidence_blocks) >= progress]
        for block in evidence_blocks:
            lines=[ln.strip() for ln in block.splitlines() if ln.strip()]
            checks += [len(lines) >= 1, len(lines) <= 8]
            checks += [not synthetic_phrase.search(block)]
            checks += [any(raw_token.search(ln) for ln in lines)]
elif name == "04_search":
    checks += [has(r'(?:🔧\s*)?Command\s*:'), has(r'(?:📋\s*)?Evidence\s*:'), has(r'(?:✅\s*)?Hasil\s*:')]
elif name == "06_tech_lane":
    checks += [has(r'(?:🔧\s*)?Command\s*:'), has(r'(?:📋\s*)?Evidence\s*:'), has(r'(?:✅\s*)?Hasil\s*:')]
elif name in ("08_error_handling", "09_multistep_ops", "10_long_output", "11_mixed_context", "12_stability_rapid", "13_recovery"):
    checks += [has(r'(?:🔧\s*)?Command\s*:'), has(r'(?:📋\s*)?Evidence\s*:'), has(r'(?:✅\s*)?Hasil\s*:')]

forbidden=[
    re.search(r'^\|.*\|\s*$', text, re.M),
    re.search(r'^---+\s*$', text, re.M),
    re.search(r'\(no output\)|\bN/A\b', text, re.I),
]
checks += [not any(forbidden)]

if name in ("03_ops_apt", "04_search", "05_complex", "06_tech_lane", "08_error_handling", "09_multistep_ops", "10_long_output", "11_mixed_context", "12_stability_rapid", "13_recovery"):
    checks += [not pass_claim_conflicts_with_evidence(text)]

if not all(checks):
    raise SystemExit(1)
PY
  then
    echo "[$name] strict shape check failed"
    sed -n '1,100p' "$out_file"
    return 1
  fi
  return 0
}

echo "Using log: $LOG_FILE"
echo "Target: $WA_TO"
if [[ -n "$SESSION_ID" ]]; then
  echo "Session: $SESSION_ID"
fi

run_step "00_reset" "/reset"
run_step "00_lock" "LOCK STRICT: required labels must stay plain colon form (Progress/Path/Command/Evidence/Hasil), no markdown table, no separator lines (---). For runbook/troubleshooting, every phase must include Evidence as fenced raw command output snippet (1-3 lines), no paraphrase-only evidence."
run_step "01_smoke" "Balas satu bubble: OK regression smoke."
run_step "02_fenced_tree" "Balas SATU fenced code block berisi tree mini 5 baris dan footer total. Jangan ada teks di luar code block."

run_step "03_ops_apt" "Task harian: apt update lalu install htop, verifikasi, lalu uninstall bersih. Format wajib per phase: Progress/Path/Command/Evidence/Hasil (plain labels). Untuk command global apt, gunakan Path: system-wide. Evidence harus fenced raw output 1-3 baris dari command yang baru dijalankan. Dilarang separator line (---), dilarang markdown bold labels, dilarang placeholder."
run_step "04_search" "Searching: cari requireMention di ~/.openclaw, tampilkan top hasil dan arti singkat. Gunakan 🔧 Command, 📋 Evidence, ✅ Hasil. Jangan tabel dan jangan separator."

if (( RUN_COMPLEX == 1 )); then
  run_step "05_complex" "Troubleshooting kompleks ringkas: port 80 conflict pada VPS. Beri tepat 3 phase saja (Diagnose -> Resolve -> Verify) dengan format Progress/Path/Command/Evidence/Hasil plain labels. Gunakan command ini agar evidence tidak kosong: Diagnose `sudo ss -tlnp | grep ':80 ' || echo no-listener-80`; Resolve `sudo systemctl stop nginx; sudo systemctl is-active nginx || true`; Verify `sudo ss -tlnp | grep ':80 ' || echo no-listener-80`. Tiap Evidence wajib fenced raw output 1-3 baris (verbatim), tidak boleh empty block. Dilarang markdown bold, separator line, placeholder, dan fake values."
  run_step "06_tech_lane" "Mode technical lane: cek status docker. Jika container list kosong, WAJIB pakai format ringkas Option A (summary plain text) dan JANGAN pakai tabel/separator (---). Tetap gunakan Progress/Path/Command/Evidence/Hasil yang ringkas dan actionable."
  run_step "07_casual_lane" "Mode casual lane: balas sapaan santai tepat 2 kalimat, hangat natural dengan sentuhan personality ringan, tanpa markdown table/separator/bold labels dan tanpa code block."
fi

if (( RUN_COMPREHENSIVE == 1 )); then
  run_step "08_error_handling" "Edge case error handling: lakukan 2 phase check yang sengaja memicu error aman (file not found + permission denied) lalu tunjukkan recovery command. Format wajib Progress/Path/Command/Evidence/Hasil; Evidence raw fenced 1-3 baris; tanpa separator/table."
  run_step "09_multistep_ops" "Multi-step ops test: runbook ringkas setup service web (precheck -> apply -> verify -> rollback hint) dengan command nyata yang aman dibaca. Format wajib Progress/Path/Command/Evidence/Hasil, satu context per phase."
  run_step "10_long_output" "Long output test: lakukan satu command beroutput panjang (misalnya list package/log) lalu tampilkan hanya cuplikan evidence paling menentukan (3-8 baris) plus Hasil ringkas. Jangan dump full output."
  run_step "11_mixed_context" "Mixed context test: kirim 2 bubble. Bubble-1 casual singkat 1 kalimat. Bubble-2 technical ringkas dengan label Progress/Path/Command/Evidence/Hasil. DILARANG separator line seperti --- dan dilarang markdown table."
  run_step "12_stability_rapid" "Stability rapid test: lakukan 3 cek cepat berurutan (contoh node, docker, nginx) dalam phase terpisah. Tiap phase wajib raw evidence snippet dan hasil PASS/FAIL akurat."
  run_step "13_recovery" "Recovery test: mulai dari satu check yang gagal, lalu lanjut fallback/recovery check sampai status akhir jelas. Format wajib Progress/Path/Command/Evidence/Hasil tanpa separator/table."
fi

echo
if (( FAILURES == 0 )); then
  echo "PASS: WA regression checks passed"
  exit 0
fi

echo "FAIL: WA regression checks failures=$FAILURES"
exit 1
