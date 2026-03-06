# Multi-Bubble Patch Testing Guide

This guide shows how to test multi-bubble functionality via CLI without manual user interaction.

## Prerequisites

1. OpenClaw gateway running
2. Patch applied with desired channels
3. Know your channel IDs:
   - WhatsApp: E.164 phone number (e.g., `+6289669848875`)
   - Telegram: Numeric user ID (e.g., `849612359`)

## Testing Commands

### WhatsApp Testing

**Reset session:**
```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "/reset" --deliver
```

**Test conversational multi-bubble:**
```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "jelaskan tentang quantum computing dalam beberapa kalimat" --deliver
```

**Expected output (CLI):**
```
Quantum computing adalah paradigma komputasi yang memanfaatkan qubit...

Hal ini memungkinkan komputer kuantum memecahkan masalah tertentu...

Meski masih dalam tahap pengembangan, potensinya signifikan...
```

**Expected behavior (WhatsApp app):**
- 3 separate bubbles (one per paragraph)
- Timestamps may be same or sequential

**Test progress task (multi-message):**
```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "buatkan 3 file python sederhana di ~/.openclaw/artifacts/generated/test-bubble/ dengan laporan progress interaktif" --deliver
```

**Expected behavior:**
- Multiple bubbles sent in real-time
- Each progress step = separate bubble

### Telegram Testing

**Reset session:**
```bash
sleep 3 && openclaw agent --channel telegram --to 849612359 --message "/reset" --deliver
```

**Test conversational multi-bubble:**
```bash
openclaw agent --channel telegram --to 849612359 --message "jelaskan tentang neural network dalam beberapa kalimat" --deliver
```

**Expected output (CLI):**
```
Neural network adalah model komputasi yang terinspirasi dari cara kerja otak manusia.

Model ini terdiri dari lapisan node (neuron) yang saling terhubung...

Setiap koneksi memiliki bobot yang disesuaikan selama proses pelatihan...

Neural network digunakan untuk berbagai tugas seperti pengenalan gambar...
```

**Expected behavior (Telegram app):**
- 4 separate messages
- Each paragraph = separate message

**Test with longer context:**
```bash
openclaw agent --channel telegram --to 849612359 --message "ceritakan tentang sejarah internet dalam beberapa paragraf" --deliver
```

## Verification Checklist

### After Fresh Patch Application

- [ ] Run `--status` to confirm all files patched
- [ ] Restart gateway: `openclaw gateway restart`
- [ ] Test WhatsApp reset + conversational response
- [ ] Test Telegram reset + conversational response
- [ ] Check app UI: confirm multiple bubbles visible
- [ ] Check session logs for `\n\n` in raw response

### After Patch Upgrade (--force)

- [ ] Backup files created (`.bak.TIMESTAMP`)
- [ ] Run `--status` to confirm upgrade
- [ ] Node syntax check passed (if `--strict` used)
- [ ] Test both channels with conversational queries
- [ ] Verify old single-channel patch replaced

## Debugging Failed Multi-Bubble

### Symptom: Single bubble despite `\n\n` in CLI output

**Check 1: Patch applied?**
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
```

**Check 2: Session loaded new CHANNEL_GUIDE.md?**
```bash
# Send /reset to force session reload
openclaw agent --channel whatsapp --to YOUR_NUMBER --message "/reset" --deliver
```

**Check 3: Check raw session log for `\n\n`:**
```bash
# Find latest session
ls -lht ~/.openclaw/agents/main/sessions/*.jsonl | head -3

# Check for double newlines in response
tail -10 ~/.openclaw/agents/main/sessions/SESSION_ID.jsonl | \
  jq -r 'select(.message.content[].text) | .message.content[] | select(.type=="text") | @json'
```

Look for `\n\n` in the JSON output. If present, patch should split it.

**Check 4: Verify channel in dist file:**
```bash
grep 'channel === "telegram"' /opt/homebrew/lib/node_modules/openclaw/dist/deliver-*.js
# or for Linux:
grep 'channel === "telegram"' ~/.local/share/mise/installs/node/*/lib/node_modules/openclaw/dist/deliver-*.js
```

Should show matches if Telegram patched.

### Symptom: CLI shows paragraphs but patch status says "unpatched"

**Solution:** Apply patch
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram
openclaw gateway restart
```

### Symptom: Only WhatsApp works, Telegram still single bubble

**Solution:** Upgrade patch with --force
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --force --channels whatsapp,telegram
openclaw gateway restart
```

## Automated Testing Script

Create `test-multibubble.sh`:
```bash
#!/bin/bash
set -e

echo "=== Multi-Bubble Test ==="

# Config
WA_NUMBER="+6289669848875"
TG_ID="849612359"

# Test WhatsApp
echo -e "\n[WhatsApp] Testing..."
openclaw agent --channel whatsapp --to "$WA_NUMBER" \
  --message "jelaskan AI dalam 3 kalimat" --deliver | \
  grep -c "^$" && echo "✅ WhatsApp has blank lines (multi-bubble likely working)"

# Test Telegram
echo -e "\n[Telegram] Testing..."
sleep 2
openclaw agent --channel telegram --to "$TG_ID" \
  --message "jelaskan blockchain dalam 3 kalimat" --deliver | \
  grep -c "^$" && echo "✅ Telegram has blank lines (multi-bubble likely working)"

echo -e "\n✅ Test complete. Check app UI to confirm separate bubbles."
```

Run: `bash test-multibubble.sh`

## Session Log Analysis

**Find response with thinking:**
```bash
SESSION_FILE=~/.openclaw/agents/main/sessions/YOUR_SESSION_ID.jsonl

tail -50 "$SESSION_FILE" | jq -r '
  select(.type=="message" and .message.role=="assistant") |
  "=== THINKING ===\n" +
  ((.message.content // []) | map(select(.type == "thinking") | .thinking) | join("\n") | .[0:500]) +
  "\n\n=== RESPONSE ===\n" +
  ((.message.content // []) | map(select(.type == "text") | .text) | join("\n"))
' | tail -60
```

**Look for:**
- Thinking should mention "one short sentence per bubble" or "Separate with blank line"
- Response should have `\n\n` between sentences

## Common Issues

### "Response has `\n\n` in CLI but single bubble in app"

**Cause:** Patch not applied for that channel.

**Fix:**
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
# If unpatched or wrong channels:
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --force --channels whatsapp,telegram
openclaw gateway restart
```

### "Model thinking doesn't mention multi-bubble"

**Cause:** Session not reloaded after CHANNEL_GUIDE.md update.

**Fix:** Send `/reset` command to force new session with updated system prompt.

### "Patch status shows patched but still single bubble"

**Cause:** Gateway not restarted after patch.

**Fix:** `openclaw gateway restart`

## Platform-Specific Notes

### macOS (Homebrew install)
- Dist path: `/opt/homebrew/lib/node_modules/openclaw/dist`
- Backup path: Same as dist path, `.bak.TIMESTAMP` suffix

### Linux (mise/nvm install)
- Dist path: `~/.local/share/mise/installs/node/VERSION/lib/node_modules/openclaw/dist`
- Backup path: Same as dist path, `.bak.TIMESTAMP` suffix

### VPS Deploy
- Always run `--status` after `git pull` to check if OpenClaw version changed
- Reapply patch after OpenClaw updates: `npm update -g openclaw && python3 patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram`
