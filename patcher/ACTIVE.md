# Quick Reference - Active Patches

**Canonical scripts:** `~/.openclaw/patcher/`

---

## 🎯 One-Liner Deploy (Most Common)

```bash
~/.openclaw/patcher/openclaw-patcher.sh
```

**Status all patchers:**
```bash
~/.openclaw/patcher/openclaw-patcher.sh --status
```

---

## 📋 Step-by-Step Commands

### 1. Check Status
```bash
~/.openclaw/patcher/openclaw-patcher.sh --status
```

### 2. Apply Multi-Bubble Patch
```bash
# Default: WhatsApp + Telegram
python3 ~/.openclaw/patcher/apply-multibubble-patch.py --strict

# Custom single channel
python3 ~/.openclaw/patcher/apply-multibubble-patch.py --strict --channels whatsapp
```

### 3. Apply Progressive Updates Patch
```bash
~/.openclaw/patcher/apply-progressive-patch.sh
```

### 4. Restart Gateway
```bash
# Using CLI
openclaw gateway restart

# Using systemd (VPS)
sudo systemctl restart openclaw
```

### 5. Verify
```bash
# Check patch status
~/.openclaw/patcher/openclaw-patcher.sh --status

# Check gateway running
pgrep -fl openclaw
```

---

## 🧪 Quick Test

```bash
# Multi-bubble test
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "jelaskan AI dalam 3 paragraf" --deliver

# Progressive updates test
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "buat 3 file demo, kasih progress tiap selesai" --deliver
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `README.md` | Complete guide with examples |
| `ACTIVE.md` | This file (quick reference) |
| `../patcher/apply-multibubble-patch.py` | Canonical multi-bubble patch script |
| `../patcher/apply-progressive-patch.sh` | Canonical progressive updates script |
| `docs/TESTING_GUIDE.md` | Testing methodology (both patches) |
| `docs/DEPLOYMENT_CHECKLIST.md` | VPS deployment guide (both patches) |
| `docs/LOCAL_TEST_RESULTS.md` | Latest test results (2026-03-07) |

---

## 🔄 Common Tasks

### Update After OpenClaw Upgrade
```bash
npm update -g openclaw
~/.openclaw/patcher/openclaw-patcher.sh --force-multibubble
```

### Rollback Patches
```bash
# Find backup files
ls -lt /opt/homebrew/lib/node_modules/openclaw/dist/*.bak* | head -10

# Restore from backup (example)
sudo cp /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-k1Tb8tGz.js.bak.20260307_020000 \
     /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-k1Tb8tGz.js

openclaw gateway restart
```

### Force Re-patch
```bash
~/.openclaw/patcher/openclaw-patcher.sh --force-multibubble
```

---

## 🆘 Troubleshooting One-Liners

```bash
# Check OpenClaw dist location
npm root -g

# Check if patches applied
grep "disableBlockStreaming: false" $(npm root -g)/openclaw/dist/channel-web-*.js
grep 'channel === "telegram"' $(npm root -g)/openclaw/dist/deliver-*.js

# View gateway logs
openclaw logs --lines 50

# Reload session after workspace changes
openclaw agent --channel whatsapp --to +6289669848875 --message "/reset" --deliver
```

---

**Last updated:** 2026-03-07  
**For detailed docs:** See `README.md` and `docs/` folder
