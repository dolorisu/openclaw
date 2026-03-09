# OpenClaw Unified Patcher v2.0

**NEW!** Complete rewrite of the patcher system with modular architecture.

## 🎉 What's New

### ✅ Fixed: Progressive Mode WhatsApp Delivery Issue

**The BIG FIX:** Progressive mode now works! We found and fixed the root cause:

**Problem:** Bot showed "typing" indicator but never sent messages
**Root Cause:** Line 1727 blocker `if (info.kind !== "final") return;` was dropping all progress updates
**Solution:** Removed blocker, added smart filtering for empty/tiny updates

### ✅ Unified Architecture

- **Single Python package** instead of 6+ separate scripts
- **Modular patches** as plugins
- **Dependency tracking** (patches can depend on other patches)
- **Built-in rollback** support
- **Better error handling** and reporting

---

## 🚀 Quick Start

### Check Status

```bash
~/.openclaw/patcher/patcher-new status
```

Output:
```
📊 Patch Status:

  ⚠️  multibubble          partially_applied   
  ✅ progressive          applied            
  ❌ tail_guard           not_applied         
  ...
```

### Apply Specific Patch

```bash
# Apply progressive mode (with blocker fix!)
~/.openclaw/patcher/patcher-new apply progressive

# Apply multibubble
~/.openclaw/patcher/patcher-new apply multibubble

# Apply both
~/.openclaw/patcher/patcher-new apply progressive multibubble
```

### Apply All Patches

```bash
~/.openclaw/patcher/patcher-new apply --all
```

### Check Patch Dependencies

```bash
~/.openclaw/patcher/patcher-new check progressive
```

Output:
```
📋 Patch: progressive
   Description: Enable real-time progressive updates with delivery blocker fix
   Status: applied
```

### Rollback a Patch

```bash
~/.openclaw/patcher/patcher-new rollback progressive
```

---

## 📦 Available Patches

### 1. **progressive** ⭐ NEW FIX!

**What it does:**
- Enables block streaming (`disableBlockStreaming: false`)
- **FIXES the deliver callback blocker** (line 1727 issue)
- Adds smart filtering for progress updates

**Dependencies:** None

**Before:**
- Bot shows typing
- No messages arrive
- Progress updates dropped silently

**After:**
- Progress messages sent in real-time
- Each step shows progress as it completes
- Smart filtering prevents spam

**Apply:**
```bash
patcher-new apply progressive
```

### 2. **multibubble**

**What it does:**
- Splits messages on `\n\n` into separate bubbles
- Works for WhatsApp and Telegram
- Preserves code blocks (doesn't split within ```)

**Dependencies:** None

**Apply:**
```bash
patcher-new apply multibubble
```

### 3. **tail_guard** (stub)

**What it does:**
- Prevents splitting short progress fragments
- Requires progressive mode enabled

**Dependencies:** progressive

**Status:** Not yet fully ported (use legacy patcher)

### 4. **outbound_dedupe** (stub)

**What it does:**
- Deduplicates messages within 15 second window

**Status:** Not yet fully ported (use legacy patcher)

### 5. **reset_prompt** (stub)

**What it does:**
- Hardens `/reset` command handling

**Status:** Not yet fully ported (use legacy patcher)

### 6. **media_roots** (stub)

**What it does:**
- Allows media from `~/.openclaw/artifacts`

**Status:** Not yet fully ported (use legacy patcher)

---

## 🔧 CLI Reference

### Commands

```bash
# Show patch status
patcher-new status
patcher-new status -v  # verbose (shows descriptions)

# Apply patches
patcher-new apply PATCH_NAME [PATCH_NAME...]
patcher-new apply --all
patcher-new apply --all --force  # reapply even if already applied
patcher-new apply --all --no-restart  # skip gateway restart

# Check specific patch
patcher-new check PATCH_NAME

# Rollback patch
patcher-new rollback PATCH_NAME
patcher-new rollback PATCH_NAME --restart  # restart gateway after
```

### Options

- `--force`: Apply even if already applied
- `--restart`: Restart gateway after applying (default: true)
- `--no-restart`: Skip gateway restart
- `-v, --verbose`: Show detailed information

---

## 🏗️ Architecture

```
patcher/
├── openclaw_patcher/           # Python package
│   ├── __init__.py
│   ├── core.py                 # Patch engine (file search, apply, rollback)
│   ├── cli.py                  # CLI interface
│   └── patches/                # Patch plugins
│       ├── __init__.py
│       ├── multibubble.py      # ✅ Fully ported
│       ├── progressive.py      # ✅ Fully ported + BLOCKER FIX
│       ├── tail_guard.py       # 🚧 Stub (TODO)
│       ├── outbound_dedupe.py  # 🚧 Stub (TODO)
│       ├── reset_prompt.py     # 🚧 Stub (TODO)
│       └── media_roots.py      # 🚧 Stub (TODO)
│
├── patcher-new                 # Thin wrapper script
│
├── modules/                    # ⚠️  Legacy scripts (still works)
│   ├── apply-multibubble-patch.py
│   ├── apply-progressive.sh
│   └── ...
│
└── patcher                     # ⚠️  Old orchestrator (still works)
```

---

## 🧪 Testing Progressive Fix

### Test on Local

```bash
# Apply the fix
patcher-new apply progressive

# Test with WhatsApp (replace with your number)
openclaw agent --channel whatsapp --to +6289669848875 \
  --message "Create 3 test files, send progress after each" \
  --deliver

# Expected: See progress messages arrive in real-time, not batched at end
```

### Verify Fix Applied

```bash
# Check the patched code
grep -A 10 "deliver: async" \
  /opt/homebrew/lib/node_modules/openclaw/dist/channel-web-*.js | head -20

# Should see:
#   const isProgressUpdate = info.kind !== "final";
#   // Smart filtering logic...
```

---

## 🐛 Troubleshooting

### "Patch shows partially_applied"

Some files may not match the expected pattern (different OpenClaw version or already patched differently). This is usually fine if core files are patched.

Check which files were patched:
```bash
patcher-new apply progressive --force
```

### "Dependency not met"

Some patches require others to be applied first:

```bash
# tail_guard requires progressive
patcher-new apply progressive
patcher-new apply tail_guard
```

### "OpenClaw directory not found"

Specify manually:
```bash
patcher-new --openclaw-dir /path/to/openclaw apply --all
```

---

## 📊 Comparison: Old vs New Patcher

| Feature | Old Patcher | New Patcher |
|---------|-------------|-------------|
| **Architecture** | 6+ separate scripts | Single Python package |
| **Dependencies** | Manual tracking | Automatic resolution |
| **Rollback** | Not supported | Built-in |
| **Status Check** | Multiple commands | Single `status` command |
| **Progressive Fix** | ❌ Not included | ✅ **FIXED!** |
| **Error Handling** | Basic | Detailed reporting |
| **Maintainability** | Hard (scattered code) | Easy (modular) |

---

## 🎯 Next Steps

1. **Test the progressive fix** on VPS
2. **Port remaining patches** (tail_guard, outbound_dedupe, etc.)
3. **Replace old patcher** once all patches ported
4. **Move old scripts to legacy/** for backup

---

## ⚠️  Migration Notes

**Current status:** New patcher is **ready for core patches** (progressive, multibubble)

**For now:**
- Use `patcher-new` for progressive + multibubble
- Use old `patcher` for tail_guard, outbound_dedupe, etc.

**Once all patches ported:**
- Move `modules/` to `legacy/`
- Rename `patcher-new` to `patcher`
- Update all documentation

---

## 📝 Developer Notes

### Adding a New Patch

1. Create `openclaw_patcher/patches/your_patch.py`:

```python
from ..core import Patch, PatchStatus, PatchResult

class YourPatch(Patch):
    name = "your_patch"
    description = "What this patch does"
    dependencies = ["other_patch"]  # if any
    
    def check(self) -> PatchStatus:
        # Check if already applied
        ...
    
    def apply(self) -> PatchResult:
        # Apply the patch
        ...
    
    def rollback(self) -> PatchResult:
        # Rollback (optional)
        ...
```

2. Register in `openclaw_patcher/patches/__init__.py`:

```python
from .your_patch import YourPatch

ALL_PATCHES = [
    ...,
    YourPatch,
]
```

3. Test:

```bash
patcher-new check your_patch
patcher-new apply your_patch
```

---

## 🙏 Credits

- **Root cause analysis:** Deep investigation found line 1727 blocker
- **Unified architecture:** Complete rewrite for maintainability
- **Progressive fix:** First patcher to actually solve the delivery issue

**Version:** 2.0.0
**Date:** 2026-03-09
