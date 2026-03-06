# Deployment Checklist - VPS Production

**Target:** doloris VPS server  
**Status:** Ready to deploy (tested on local macOS 2026-03-07)

---

## Pre-Deployment Verification (Local - DONE ✅)

- [x] Multi-bubble patch applied and tested on WhatsApp
- [x] Multi-bubble patch applied and tested on Telegram  
- [x] Progressive updates patch applied and tested
- [x] Session log analysis confirms incremental delivery (3-8 second intervals)
- [x] File creation verification passed (all demo files created)
- [x] No regressions detected (multi-bubble still works after progressive patch)
- [x] All changes committed and pushed to `self` remote (git@github.doloris:dolorisu/doloris.git)

**Latest commits:**
```
23d5171 - docs(patches): add documentation index to README
3a4a6c4 - docs(patches): add comprehensive testing methodology guide
95119f4 - test(patches): verify multi-bubble and progressive updates functionality
bb72b8b - feat(patch): add progressive updates patch to enable block streaming
```

---

## VPS Deployment Steps

### 1. Backup Current State (Critical!)

```bash
# SSH to VPS
ssh user@doloris-vps

# Backup current dist directory
sudo cp -r /opt/homebrew/lib/node_modules/openclaw/dist /opt/homebrew/lib/node_modules/openclaw/dist.backup-$(date +%Y%m%d-%H%M%S)

# Or for Linux paths:
sudo cp -r ~/.local/share/mise/installs/node/*/lib/node_modules/openclaw/dist ~/.local/share/mise/installs/node/*/lib/node_modules/openclaw/dist.backup-$(date +%Y%m%d-%H%M%S)
```

### 2. Pull Latest Changes

```bash
cd ~/.openclaw
git status  # Check for local changes
git pull    # Pull from remote

# Verify patches directory
ls -lh patches/
```

**Expected files:**
- `apply-multibubble-patch.py`
- `apply-progressive-patch.sh`
- `HOW_TO_TEST.md`
- `TESTING.md`
- `TEST_RESULTS.md`
- `PROGRESSIVE_UPDATES.md`
- `README.md`
- `ACTIVE.md`

### 3. Check Current Patch Status

```bash
# Multi-bubble status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status

# Progressive updates status
~/.openclaw/patches/apply-progressive-patch.sh --status
```

**Possible outcomes:**
- ✅ Already patched (safe to skip)
- ❌ Unpatched (need to apply)
- ⚠️  Unknown (check OpenClaw version, might need patch adjustment)

### 4. Apply Multi-Bubble Patch

```bash
# For both WhatsApp and Telegram
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram

# Verify
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
```

**Expected output:**
```
Summary:
- deliver files: 4 (patched: 4, unpatched: 0, unknown: 0)
- web files: 4 (patched: 4, unpatched: 0, unknown: 0)

✅ All files patched successfully
```

### 5. Apply Progressive Updates Patch

```bash
~/.openclaw/patches/apply-progressive-patch.sh

# Verify
~/.openclaw/patches/apply-progressive-patch.sh --status
```

**Expected output:**
```
  channel-web-k1Tb8tGz.js: ✅ patched
  channel-web-sl83aqDv.js: ✅ patched
  web-pFdwPQ7y.js: ✅ patched
  web-CSq0l9pG.js: ✅ patched

✅ Progressive updates enabled!
```

### 6. Restart OpenClaw Service

```bash
# If using systemd
sudo systemctl restart openclaw
sudo systemctl status openclaw

# If using openclaw CLI
openclaw gateway restart

# Verify running
pgrep -fl openclaw
```

### 7. Post-Deployment Testing

**Test 1: Multi-bubble (regression test)**
```bash
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "jelaskan quantum computing dalam 3 poin singkat" \
  --deliver
```

Expected: 3 paragraphs separated by blank lines in CLI output.

**Test 2: Progressive updates (new feature)**
```bash
openclaw agent --channel telegram --to 849612359 \
  --message "buat 3 file test di ~/.openclaw/artifacts/scratch/vps-test/ (v1.txt, v2.txt, v3.txt). kasih progress setiap file selesai." \
  --deliver
```

Expected: Progress messages shown in CLI, files created.

**Test 3: Timestamp verification (critical!)**
```bash
# Find latest session
SESSION=$(ls -t ~/.openclaw/agents/main/sessions/*.jsonl | head -1)

# Check message timestamps
tail -30 "$SESSION" | jq -c 'select(.type=="message" and ((.message.content[]?.text // .event.text // "") | contains("Progress:"))) | {ts:.timestamp, text:(.message.content[]?.text // .event.text // "")[0:60]}'
```

Expected: Timestamps show 2-8 second intervals between progress messages.

**Test 4: Manual app verification**
- Open WhatsApp on phone
- Check if multi-bubble response received as separate messages
- Open Telegram on phone  
- Check if progressive updates received incrementally (not batched)

### 8. Verify Files Created

```bash
ls -lh ~/.openclaw/artifacts/scratch/vps-test/*.txt
cat ~/.openclaw/artifacts/scratch/vps-test/v1.txt
```

Expected: 3 files with reasonable sizes and content.

### 9. Send /reset to Reload Workspace

```bash
openclaw agent --channel whatsapp --to +6289669848875 --message "/reset" --deliver
```

This forces session reload with updated workspace MD files (WORKFLOW.md, CHANNEL_GUIDE.md).

---

## Rollback Plan (If Something Goes Wrong)

### Quick Rollback

```bash
# Stop service
sudo systemctl stop openclaw
# or
openclaw gateway stop

# Restore backup
sudo cp -r /opt/homebrew/lib/node_modules/openclaw/dist.backup-TIMESTAMP /opt/homebrew/lib/node_modules/openclaw/dist

# Restart
sudo systemctl start openclaw
```

### Patch-Specific Rollback

If only one patch is problematic, restore from `.backup-*` files created by scripts:

```bash
# Find backup files
ls -lt /opt/homebrew/lib/node_modules/openclaw/dist/*.backup-*

# Example: Restore specific file
sudo cp /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-k1Tb8tGz.js.backup-progressive-20260307_020345 \
     /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-k1Tb8tGz.js

# Restart
openclaw gateway restart
```

---

## Monitoring Post-Deployment

### Log Monitoring

```bash
# Follow gateway logs
openclaw logs --lines 50

# Check for errors
openclaw logs --lines 100 | grep -i "error\|fail\|exception"

# Check message delivery
openclaw logs --lines 100 | grep -i "deliver\|sent\|reply"
```

### Health Check

```bash
openclaw health
openclaw status
```

Expected: All channels show "healthy" or "connected".

### Session Inspection (Random Sampling)

```bash
# List recent sessions
ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -5

# Check a random session for multi-bubble patterns
RANDOM_SESSION=$(ls ~/.openclaw/agents/main/sessions/*.jsonl | shuf -n 1)
tail -20 "$RANDOM_SESSION" | jq -r 'select(.message.role=="assistant") | .message.content[] | select(.type=="text") | .text' | grep -c "\\n\\n" || echo "No blank lines found"
```

---

## Success Criteria

Deployment considered successful if:

- [x] Multi-bubble patch status shows "patched" for all files
- [x] Progressive updates patch status shows "✅ patched" for all files
- [x] Gateway restarts without errors
- [x] Test messages send successfully
- [x] CLI output shows expected format (blank lines for multi-bubble, progress messages)
- [x] Session log timestamps show incremental delivery (2-8 second intervals)
- [x] Files created from test task exist and have correct content
- [x] Manual app check confirms separate bubbles and incremental progress
- [x] `/reset` command works and reloads workspace
- [x] No errors in gateway logs
- [x] Health check passes

---

## Troubleshooting Common Issues

### Issue 1: Patch Status Shows "Unknown"

**Cause:** OpenClaw version on VPS different from local (different dist file hashes).

**Solution:**
1. Check OpenClaw version: `openclaw --version`
2. Check dist file signatures manually:
   ```bash
   grep -n "const textChunks = chunkMarkdownTextWithMode" /opt/homebrew/lib/node_modules/openclaw/dist/web-*.js
   grep -n "disableBlockStreaming" /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-*.js
   ```
3. If signatures different, adjust patch script or update OpenClaw to match local version

### Issue 2: Gateway Won't Restart

**Cause:** Syntax error from patch or service configuration issue.

**Solution:**
1. Check service logs: `journalctl -u openclaw -n 50`
2. Test node syntax: `node --check /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-k1Tb8tGz.js`
3. If syntax error, restore from backup
4. If service issue, check systemd config

### Issue 3: Multi-Bubble Not Working After Patch

**Symptoms:** CLI shows `\n\n` but app shows single message.

**Debug steps:**
1. Verify patch applied: `--status` should show "patched"
2. Check channel in dist file:
   ```bash
   grep 'channel === "telegram"' /opt/homebrew/lib/node_modules/openclaw/dist/deliver-*.js
   ```
3. Verify gateway restarted: `pgrep -a openclaw`
4. Send `/reset` to reload session
5. Test again with fresh message

### Issue 4: Progressive Updates Still Batched

**Symptoms:** All progress messages arrive at once, same timestamps.

**Debug steps:**
1. Verify patch applied: `apply-progressive-patch.sh --status`
2. Check `disableBlockStreaming` value:
   ```bash
   grep -n "disableBlockStreaming" /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-*.js
   ```
   Should show: `disableBlockStreaming: false,`
3. Verify gateway restarted after patch
4. Check model thinking (might not output interim text)

### Issue 5: Model Not Outputting Progress

**Symptoms:** Infrastructure works but no progress messages.

**Cause:** Model not following WORKFLOW.md instructions or session not reloaded.

**Solution:**
1. Send `/reset` to force session reload
2. Check workspace MD files in sync:
   ```bash
   grep -A3 "Interactive progress protocol" ~/.openclaw/workspace/custom/policies/WORKFLOW.md
   ```
3. Test with explicit instruction: "WAJIB kirim progress setiap file selesai"

---

## Post-Deployment Documentation

After successful deployment, update this file with:
- [ ] Actual VPS deployment date/time
- [ ] Any issues encountered and how resolved
- [ ] VPS-specific adjustments needed
- [ ] Performance observations (message delivery speed, etc.)

---

**Prepared by:** AI Assistant (Claude)  
**Preparation date:** 2026-03-07  
**Local testing:** ✅ Completed (see TEST_RESULTS.md)  
**VPS deployment:** ⏳ Pending  
**Deployment contact:** rifuki
