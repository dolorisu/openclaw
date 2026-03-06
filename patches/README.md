# OpenClaw Patches (WhatsApp + Telegram)

Multi-bubble responses and progressive updates patches for better UX.

---

## 🚀 Quick Start

**Apply both patches (WhatsApp + Telegram):**
```bash
# Recommended: run orchestrator (correct sequence + restart)
~/.openclaw/patcher/run-openclaw-patches.sh
```

**Check status:**
```bash
~/.openclaw/patcher/run-openclaw-patches.sh --status
```

See **[ACTIVE.md](ACTIVE.md)** for quick reference.

For sequence-safe auto-runner, see `~/.openclaw/patcher/run-openclaw-patches.sh`.

---

## 📁 File Structure

```
patches/
├── README.md                          ← You are here
├── ACTIVE.md                          ← Quick command reference
│
├── apply-multibubble-patch.py         ← Multi-bubble patch script
├── apply-progressive-patch.sh         ← Progressive updates patch script
│
├── docs/                              ← Documentation
│   ├── TESTING_GUIDE.md               ← Testing methodology (both patches)
│   ├── TESTING_MATRIX.md              ← Valid vs misleading test methods
│   ├── DEPLOYMENT_CHECKLIST.md        ← VPS deployment guide (both patches)
│   ├── LOCAL_TEST_RESULTS.md          ← Test results (both patches, 2026-03-07)
│   │
│   ├── MULTIBUBBLE_COMMANDS.md        ← Multi-bubble: CLI command reference
│   │
│   ├── PROGRESSIVE_UPDATES.md         ← Progressive: Technical deep dive
│   └── PROGRESSIVE_VPS_EVIDENCE.md    ← Progressive: Real VPS evidence (batching)
│
└── archive/                           ← Old/deprecated files
    ├── apply-multibubble-dist-patch.py
    ├── DEBUG_ANALYSIS.md
    └── QUICKSTART.txt
```

---

## 📚 Documentation Guide

### For First-Time Users
1. **[README.md](README.md)** (this file) - Start here
2. **[ACTIVE.md](ACTIVE.md)** - Quick commands

### For Testing (AI Assistants)
1. **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Methodology for both patches
2. **[docs/TESTING_MATRIX.md](docs/TESTING_MATRIX.md)** - What methods are valid vs misleading
3. **[docs/MULTIBUBBLE_COMMANDS.md](docs/MULTIBUBBLE_COMMANDS.md)** - CLI command examples
4. **[docs/LOCAL_TEST_RESULTS.md](docs/LOCAL_TEST_RESULTS.md)** - Latest test results (2026-03-07)

### For VPS Deployment
1. **[docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)** - Complete guide (both patches)

### For Technical Deep Dive

**Progressive updates patch:**
1. **[docs/PROGRESSIVE_UPDATES.md](docs/PROGRESSIVE_UPDATES.md)** - Root cause analysis & solution
2. **[docs/PROGRESSIVE_VPS_EVIDENCE.md](docs/PROGRESSIVE_VPS_EVIDENCE.md)** - Real VPS chat logs (before patch)

**Multi-bubble patch:**
- See inline documentation in `apply-multibubble-patch.py`

---

## 🔧 Patch Details

### 1. Multi-Bubble Patch (`apply-multibubble-patch.py`)

**What it does:** Splits conversational responses on `\n\n` (double newline) into separate message bubbles.

**Files patched:**
- `dist/deliver-*.js` (4 files)
- `dist/channel-web-*.js` + `dist/web-*.js` (4 files)
- `dist/pi-embedded-*.js` (Telegram bot delivery path)

**Features:**
- Cross-platform (macOS, Linux, any node manager)
- Multi-channel support (`--channels whatsapp,telegram`)
- `--force` mode for upgrading existing patches
- Automatic backup with rollback on failure
- Syntax validation with `--strict`

**Example:**
```bash
# Default (WhatsApp + Telegram)
python3 apply-multibubble-patch.py --strict

# Custom channels
python3 apply-multibubble-patch.py --strict --channels whatsapp
```

### 2. Progressive Updates Patch (`apply-progressive-patch.sh`)

**What it does:** Enables block streaming to send interim text updates during long tasks instead of batching at the end.

**Technical change:**
```javascript
// BEFORE
disableBlockStreaming: true

// AFTER
disableBlockStreaming: false
```

**Files patched:**
- `dist/channel-web-k1Tb8tGz.js`
- `dist/channel-web-sl83aqDv.js`
- `dist/web-pFdwPQ7y.js`
- `dist/web-CSq0l9pG.js`

**Features:**
- Cross-platform (auto-detects GNU sed vs BSD sed)
- `npm root -g` discovery (works with any node manager)
- Automatic backup before patching

**Example:**
```bash
./apply-progressive-patch.sh --status
./apply-progressive-patch.sh
```

---

## ✅ What These Patches Fix

### Before Patches
**Multi-bubble:**
- Long responses sent as single bubble
- Hard to read, requires scrolling

**Progressive updates:**
- Silence during task execution
- All progress messages arrive at once at the end
- User doesn't know if bot is working or stuck

### After Patches
**Multi-bubble:**
```
Bubble 1: Blockchain adalah teknologi...

Bubble 2: Setiap blok berisi data...

Bubble 3: Keunggulan utama adalah...
```

**Progressive updates:**
```
19:03:05 - Progress: script1.py selesai
19:03:11 - Progress: script2.py selesai  [+6s]
19:03:19 - Progress: script3.py selesai  [+7s]
19:03:26 - Progress: script4.py selesai  [+7s]
```
Real-time updates every 3-8 seconds!

---

## 🧪 Testing

**Quick test:**
```bash
# Multi-bubble
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "jelaskan blockchain dalam 3 paragraf" --deliver

# Progressive updates
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "buat 3 file demo, kasih progress tiap file selesai" --deliver
```

**Full testing guide:** See [docs/HOW_TO_TEST.md](docs/HOW_TO_TEST.md)

---

## 🌍 Compatibility

Both scripts work on:
- ✅ macOS (Homebrew, mise, nvm, volta, asdf)
- ✅ Linux (system node, mise, nvm, volta, asdf, npm global)
- ✅ Any environment with `npm` available

**Discovery methods:**
1. `npm root -g` (most reliable)
2. Walk up from `openclaw` binary path
3. Glob patterns for common node managers

---

## 📦 VPS Deployment

**Pre-flight check:**
```bash
cd ~/.openclaw
git pull
python3 patches/apply-multibubble-patch.py --status
patches/apply-progressive-patch.sh --status
```

**Deploy:**
```bash
python3 patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram
patches/apply-progressive-patch.sh
sudo systemctl restart openclaw
```

**Verify:**
- Test with real WhatsApp/Telegram messages
- Check session logs for incremental timestamps
- Send `/reset` to reload workspace

**Full checklist:** See [docs/DEPLOYMENT_CHECKLIST.md](docs/DEPLOYMENT_CHECKLIST.md)

---

## 🆘 Troubleshooting

**Patch status shows "unknown":**
```bash
# Check OpenClaw version
openclaw --version

# Re-apply patches
python3 apply-multibubble-patch.py --strict --force --channels whatsapp,telegram
./apply-progressive-patch.sh
```

**Multi-bubble not working:**
- Verify patch status: `--status` should show "patched"
- Restart gateway: `openclaw gateway restart`
- Send `/reset` to reload session

**Progressive updates still batched:**
- Check `disableBlockStreaming: false` in dist files:
  ```bash
  grep "disableBlockStreaming" /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-*.js
  ```
- Verify gateway restarted after patch

---

## 🗂️ Archive

Old/deprecated files moved to `archive/` for reference:
- `apply-multibubble-dist-patch.py` - Old version (WhatsApp-only)
- `DEBUG_ANALYSIS.md` - Old debugging notes
- `QUICKSTART.txt` - Superseded by this README

---

**Created:** 2026-03-06  
**Last updated:** 2026-03-07  
**Status:** Production-ready, tested on local macOS  
**VPS deployment:** Pending
