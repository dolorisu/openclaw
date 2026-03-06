# Testing Guide (Both Patches)

**Scope:** Multi-bubble + Progressive updates patches  
**Target audience:** AI assistants testing OpenClaw patches  
**Purpose:** Comprehensive testing methodology and analysis techniques

Dokumen ini menjelaskan cara testing yang BENAR untuk verify multi-bubble dan progressive updates patches. Jangan sampai salah pakai command seperti `openclaw message` (yang salah!) atau method yang tidak efektif.

---

## Prerequisites

1. OpenClaw gateway harus running
2. Patches sudah diapply
3. Tahu target ID:
   - WhatsApp: E.164 phone number (contoh: `+6289669848875`)
   - Telegram: Numeric user ID (contoh: `849612359`)

**PENTING:** Lihat file `TESTING.md` untuk command reference yang lengkap, tapi dokumen ini fokus ke **methodology** testing dan **analysis**.

---

## Command yang BENAR untuk Send Message

### ❌ SALAH (Jangan pakai ini!)
```bash
openclaw message send --target +15555550123 --message "Hi"
```
Ini untuk send message biasa, BUKAN untuk trigger agent response.

### ✅ BENAR (Pakai ini!)
```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "test message" --deliver
```

**Penjelasan:**
- `openclaw agent` = Trigger agent untuk process dan respond
- `--channel whatsapp` atau `--channel telegram` = Channel target
- `--to <ID>` = Target user (phone number atau Telegram ID)
- `--message "text"` = Message yang akan diproses agent
- `--deliver` = Flag untuk actually deliver response ke user

**Output:** CLI akan print response text yang digenerate agent.

## IMPORTANT: Realtime Test Caveat

`openclaw agent --channel ... --deliver` berguna untuk functional smoke test, **TAPI** tidak selalu representatif untuk realtime progressive UX di chat app.

Pada beberapa runtime path, command ini bisa terlihat seperti progress dibuffer lalu delivered beruntun saat run selesai.

Untuk validasi realtime end-user behavior, gunakan metode berikut:
1. Kirim prompt langsung dari WhatsApp/Telegram app (human-initiated inbound)
2. Observasi arrival pattern di app
3. Cocokkan dengan session timestamps sebagai supporting evidence

**Rule:**
- `openclaw agent` = valid untuk smoke test format/output
- Prompt dari app = valid untuk realtime/progressive UX verification

---

## Testing Strategy: 3-Layer Verification

Untuk memastikan patch works, kita perlu verify di 3 layer:

1. **CLI Output** - Apakah ada `\n\n` atau progress messages?
2. **Session Logs** - Apakah messages punya timestamps berbeda (incremental)?
3. **Files Created** - Apakah task execution actually success?

### Layer 1: CLI Output Verification

**Test command:**
```bash
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "jelaskan neural network dalam 3 poin singkat" \
  --deliver 2>&1 | tee /tmp/test-output.txt
```

**What to look for:**
```
Neural network adalah model komputasi...

Model ini belajar dengan menyesuaikan...

Digunakan untuk berbagai aplikasi...
```

✅ **Good sign:** Ada blank lines (`\n\n`) antara paragraphs  
❌ **Bad sign:** Single continuous text tanpa blank lines

**Save output ke file** dengan `| tee /tmp/test-output.txt` untuk analysis nanti.

### Layer 2: Session Log Analysis (CRITICAL!)

Ini **MOST IMPORTANT** untuk verify progressive updates. CLI output bisa misleading - yang penting adalah **KAPAN** messages actually dikirim.

#### Step 1: Find Latest Session File

```bash
ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -2
```

Output example:
```
-rw-------  89733 Mar  7 02:02 /.../.openclaw/agents/main/sessions/64249fed-06d1-42ee-9ea3-a7cfaa6865a2.jsonl
-rw-------  27132 Mar  7 01:24 /.../.openclaw/agents/main/sessions/ed0eb9b1-0196-41ef-9c78-84383f45cbac.jsonl
```

Session paling baru (timestamp terbaru) adalah yang kita mau. Copy full path-nya.

#### Step 2: Extract Message Timestamps

```bash
SESSION_FILE=~/.openclaw/agents/main/sessions/64249fed-06d1-42ee-9ea3-a7cfaa6865a2.jsonl

tail -30 "$SESSION_FILE" | jq -c 'select(.type=="message") | {ts:.timestamp, text:(.event.text // .message.content[]?.text // "n/a")[0:70]}'
```

**Penjelasan command:**
- `tail -30` = Ambil 30 baris terakhir (cukup untuk lihat recent messages)
- `jq -c` = Parse JSON, output compact
- `select(.type=="message")` = Filter hanya events bertipe "message"
- Extract `timestamp` dan `text` (first 70 chars)

**Output example (GOOD - Progressive working):**
```json
{"ts":"2026-03-06T19:03:05.488Z","text":"Progress: script1.py selesai dibuat (197 bytes) - fungsi greeting."}
{"ts":"2026-03-06T19:03:11.998Z","text":"Progress: script2.py selesai dibuat (522 bytes) - fungsi calculator."}
{"ts":"2026-03-06T19:03:19.431Z","text":"Progress: script3.py selesai dibuat (604 bytes) - fungsi string utilit"}
{"ts":"2026-03-06T19:03:26.986Z","text":"Progress: script4.py selesai dibuat (829 bytes) - fungsi list utilitie"}
{"ts":"2026-03-06T19:03:29.858Z","text":"Progress: script5.py selesai dibuat (881 bytes) - fungsi date/time uti"}
```

✅ **Good sign:** Timestamps berbeda dengan interval 3-8 detik  
❌ **Bad sign:** Semua timestamps sama (berarti batched)

#### Step 3: Calculate Time Intervals (Optional but Nice)

Manual calculation dari timestamps:
```
19:03:05 → 19:03:11 = 6 seconds
19:03:11 → 19:03:19 = 8 seconds
19:03:19 → 19:03:26 = 7 seconds
19:03:26 → 19:03:29 = 3 seconds
```

Intervals 3-8 detik = **PERFECT** incremental delivery!

#### Step 4: Check for Tool Call Messages (Advanced)

```bash
tail -50 "$SESSION_FILE" | jq -c 'select(.message.content[]?.type == "tool_use") | {ts:.timestamp, tool:.message.content[].name}'
```

Ini akan show kapan tool calls executed. Kalau timestamps tool calls + progress messages interleaved (saling berbaur), artinya progressive updates truly working.

### Layer 3: File Creation Verification

Untuk multi-step tasks yang create files, **ALWAYS verify** files actually created.

```bash
ls -lh ~/.openclaw/artifacts/scratch/demo*.txt
```

**What to check:**
- ✅ File count correct (asked for 3, got 3)
- ✅ File sizes reasonable (not 0 bytes)
- ✅ Timestamps show sequential creation

**Bad signs:**
- ❌ Files missing
- ❌ All files have identical timestamps (might be fake progress)
- ❌ File sizes = 0 bytes (write failed)

**Pro tip:** Check file content juga!
```bash
head -2 ~/.openclaw/artifacts/scratch/demo1.txt
```

---

## Testing Multi-Bubble (Regression Test)

### Test Case: Conversational Response

**Goal:** Verify `\n\n` splits into multiple bubbles.

**Command:**
```bash
openclaw agent --channel telegram --to 849612359 \
  --message "Jelaskan blockchain dalam beberapa paragraf singkat" \
  --deliver 2>&1 | tee /tmp/test-multibubble.txt
```

**Expected CLI output:**
```
Blockchain adalah teknologi...

Setiap blok berisi...

Sistem ini bekerja...

Keunggulan utama...
```

**Analysis:**
```bash
# Count blank lines (should be 3+ for multi-bubble)
grep -c "^$" /tmp/test-multibubble.txt

# Check session log untuk confirm paragraphs sent separately
SESSION_FILE=~/.openclaw/agents/main/sessions/LATEST.jsonl
tail -10 "$SESSION_FILE" | jq -r 'select(.message.role=="assistant") | .message.content[] | select(.type=="text") | .text'
```

**Verification checklist:**
- [ ] CLI output has blank lines (`\n\n`)
- [ ] Session log shows full response text with `\n\n`
- [ ] **Manual check:** Open WhatsApp/Telegram app, verify separate bubbles

**Note:** Session log will show FULL TEXT with `\n\n`. The splitting happens in delivery layer (deliver-*.js), NOT in session storage. So it's normal to see `\n\n` in logs.

---

## Testing Progressive Updates (New Feature)

### Test Case: Multi-Step File Creation

**Goal:** Verify progress messages sent INCREMENTAL, not batched.

**Command:**
```bash
time openclaw agent --channel whatsapp --to +6289669848875 \
  --message "Buat 5 file python di ~/.openclaw/artifacts/scratch/pytest/ (script1.py sampai script5.py). Setiap file beda fungsi. WAJIB kirim progress tiap file selesai." \
  --deliver 2>&1 | tee /tmp/test-progressive.txt
```

**Why `time` command?**
- Shows total execution time
- Helps correlate dengan message intervals

**Expected CLI output:**
```
Progress: script1.py selesai dibuat (197 bytes) - fungsi greeting.
Progress: script2.py selesai dibuat (522 bytes) - fungsi calculator.
Progress: script3.py selesai dibuat (604 bytes) - fungsi string utilities.
Progress: script4.py selesai dibuat (829 bytes) - fungsi list utilities.
Progress: script5.py selesai dibuat (881 bytes) - fungsi date/time utilities.

Status selesai: Semua 5 file berhasil dibuat.
```

**CRITICAL Analysis Step:**

```bash
# 1. Find session file
SESSION_FILE=$(ls -t ~/.openclaw/agents/main/sessions/*.jsonl | head -1)

# 2. Extract timestamps for progress messages
tail -50 "$SESSION_FILE" | \
  jq -c 'select(.type=="message" and (.message.content[]?.text // .event.text // "") | contains("Progress:")) | 
  {ts:.timestamp, text:(.message.content[]?.text // .event.text // "n/a")[0:70]}'
```

**Expected output (GOOD):**
```json
{"ts":"2026-03-06T19:03:05.488Z","text":"Progress: script1.py selesai"}
{"ts":"2026-03-06T19:03:11.998Z","text":"Progress: script2.py selesai"}  
{"ts":"2026-03-06T19:03:19.431Z","text":"Progress: script3.py selesai"}
{"ts":"2026-03-06T19:03:26.986Z","text":"Progress: script4.py selesai"}
{"ts":"2026-03-06T19:03:29.858Z","text":"Progress: script5.py selesai"}
```

**Analysis:**
- Interval: 6s, 7s, 7s, 3s between messages
- Total span: ~24 seconds
- ✅ **INCREMENTAL DELIVERY CONFIRMED**

**Expected output (BAD - Batched):**
```json
{"ts":"2026-03-06T19:03:29.858Z","text":"Progress: script1.py selesai"}
{"ts":"2026-03-06T19:03:29.859Z","text":"Progress: script2.py selesai"}  
{"ts":"2026-03-06T19:03:29.860Z","text":"Progress: script3.py selesai"}
{"ts":"2026-03-06T19:03:29.861Z","text":"Progress: script4.py selesai"}
{"ts":"2026-03-06T19:03:29.862Z","text":"Progress: script5.py selesai"}
```
All same second, microsecond diff = batched at end ❌

**File verification:**
```bash
ls -lh ~/.openclaw/artifacts/scratch/pytest/*.py

# Check timestamps (should be sequential)
ls -lt ~/.openclaw/artifacts/scratch/pytest/*.py

# Sample content
head -5 ~/.openclaw/artifacts/scratch/pytest/script1.py
```

---

## Advanced: Checking Model Thinking

Kadang perlu check apakah model AWARE tentang multi-bubble atau progressive protocol.

### Extract Thinking from Session

```bash
SESSION_FILE=~/.openclaw/agents/main/sessions/LATEST.jsonl

tail -50 "$SESSION_FILE" | jq -r '
  select(.type=="message" and .message.role=="assistant") |
  (.message.content // []) | 
  map(select(.type == "thinking") | .thinking) | 
  join("\n")
' | tail -100
```

**What to look for:**

**For multi-bubble awareness:**
```
Model thinking should mention:
- "separate bubbles"
- "blank line" or "\n\n"
- "one short sentence per bubble"
- CHANNEL_GUIDE.md instructions
```

**For progressive updates awareness:**
```
Model thinking should mention:
- "send progress updates"
- "incremental" or "step by step"
- "Status mulai" / "Progress:" / "Status selesai"
- WORKFLOW.md instructions
```

**Bad signs:**
- No mention of multi-bubble protocol
- No mention of progress updates
- Thinking says "will create all files then report" (means batch mode)

**Solution if bad:**
Send `/reset` command untuk reload system prompt:
```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "/reset" --deliver
```

---

## Common Pitfalls & How to Avoid

### Pitfall 1: Using Wrong Command

❌ **Wrong:**
```bash
openclaw message send --target +123 --message "test"
```
This sends message but doesn't trigger agent processing.

✅ **Correct:**
```bash
openclaw agent --channel whatsapp --to +123 --message "test" --deliver
```

### Pitfall 2: Not Checking Timestamps

❌ **Insufficient test:**
"CLI output shows progress messages, so progressive updates works!"

✅ **Proper test:**
Check session log timestamps. CLI output bisa sama walaupun messages dibatch.

### Pitfall 3: Forgetting File Verification

❌ **Assuming:**
"Model said files created, so they exist"

✅ **Verify:**
```bash
ls -lh ~/.openclaw/artifacts/scratch/*.txt
cat ~/.openclaw/artifacts/scratch/demo1.txt
```

### Pitfall 4: Wrong Session File

❌ **Using old session:**
Analyzing session dari 1 jam lalu, bukan test yang baru saja run.

✅ **Find latest:**
```bash
ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -1
```
Always sort by time (`-t`) dan ambil paling baru.

### Pitfall 5: Misinterpreting Log Format

❌ **Confusion:**
"Session log shows full text with \n\n, apakah ini batched?"

✅ **Understanding:**
Session log stores FULL assistant response. Splitting terjadi di delivery layer. Ini normal dan expected. Yang penting: apakah text punya `\n\n` (yes = good for multi-bubble).

---

## Quick Test Script (Copy-Paste Ready)

Simpan ini sebagai `quick-test.sh`:

```bash
#!/bin/bash
set -euo pipefail

# Config
WA_NUMBER="+6289669848875"
TG_ID="849612359"
CHANNEL="${1:-whatsapp}"  # default whatsapp
TARGET="${2:-$WA_NUMBER}"

echo "=== Testing on $CHANNEL ==="
echo

# Test 1: Multi-bubble
echo "[1/2] Testing multi-bubble..."
openclaw agent --channel "$CHANNEL" --to "$TARGET" \
  --message "jelaskan quantum computing dalam 3 poin singkat" \
  --deliver 2>&1 | tee /tmp/test-multibubble.txt

BLANKS=$(grep -c "^$" /tmp/test-multibubble.txt || echo 0)
echo "   Blank lines found: $BLANKS"
[ "$BLANKS" -gt 1 ] && echo "   ✅ Multi-bubble likely working" || echo "   ❌ No blank lines"
echo

sleep 3

# Test 2: Progressive updates
echo "[2/2] Testing progressive updates..."
openclaw agent --channel "$CHANNEL" --to "$TARGET" \
  --message "buat 3 file test di ~/.openclaw/artifacts/scratch/quick-test/ (t1.txt, t2.txt, t3.txt). kasih progress tiap file selesai." \
  --deliver 2>&1 | tee /tmp/test-progressive.txt

# Check files
echo "   Files created:"
ls -lh ~/.openclaw/artifacts/scratch/quick-test/*.txt 2>/dev/null || echo "   ❌ No files found"

# Check session timestamps
SESSION=$(ls -t ~/.openclaw/agents/main/sessions/*.jsonl | head -1)
echo "   Message timestamps:"
tail -30 "$SESSION" | \
  jq -r 'select(.type=="message" and ((.message.content[]?.text // .event.text // "") | contains("Progress:"))) | .timestamp' | \
  tail -5

echo
echo "✅ Test complete!"
echo "   Manual verification needed:"
echo "   1. Check $CHANNEL app for separate bubbles"
echo "   2. Verify timestamps show 2-8 second intervals"
```

**Usage:**
```bash
chmod +x quick-test.sh

# Test WhatsApp
./quick-test.sh whatsapp +6289669848875

# Test Telegram
./quick-test.sh telegram 849612359
```

---

## Interpreting Test Results

### Scenario 1: Multi-Bubble NOT Working

**Symptoms:**
- CLI output has `\n\n` but session shows single bubble
- Patch status says "unpatched"
- App shows single long message

**Diagnosis:**
```bash
python3 ~/.openclaw/patcher/apply-multibubble-patch.py --status
```

**Fix:**
```bash
python3 ~/.openclaw/patcher/apply-multibubble-patch.py --strict --channels whatsapp,telegram
openclaw gateway restart
```

### Scenario 2: Progressive Updates NOT Working

**Symptoms:**
- CLI shows progress but all messages same timestamp
- Long silence then burst of messages
- Session log shows batched timestamps (all within 1 second)

**Diagnosis:**
```bash
~/.openclaw/patcher/apply-progressive.sh --status
```

**Fix:**
```bash
~/.openclaw/patcher/apply-progressive.sh
openclaw gateway restart
```

### Scenario 3: Model Not Cooperating

**Symptoms:**
- Infrastructure works but model doesn't output progress
- Model thinking doesn't mention WORKFLOW.md
- Responses don't have `\n\n` even for multi-paragraph answers

**Diagnosis:**
Session not reloaded after workspace changes.

**Fix:**
```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "/reset" --deliver
```
Then test again.

---

## Summary: The Right Way to Test

1. **Send message** via `openclaw agent --channel X --to Y --message "..." --deliver`
2. **Check CLI output** for `\n\n` (multi-bubble) or progress text
3. **Find latest session** via `ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -1`
4. **Extract timestamps** via `tail -30 SESSION | jq ... | grep Progress`
5. **Calculate intervals** manually dari timestamps (should be 2-8 seconds apart)
6. **Verify files** jika task create files
7. **Optional:** Check model thinking untuk verify awareness
8. **Manual verify:** Check app (WhatsApp/Telegram) untuk confirm actual user experience

**The timestamp check is THE MOST IMPORTANT step** for progressive updates testing. Don't skip it!

---

**Document created:** 2026-03-07  
**Last updated:** 2026-03-07  
**Tested on:** OpenClaw 2026.3.2 (85377a2), macOS local + VPS (planned)
