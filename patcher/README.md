# OpenClaw Patcher v2.0

Unified patch management system with modular architecture.

## 🎯 What This Does

Patches OpenClaw runtime to enable:
- **Progressive updates**: Real-time progress messages (no more "typing forever")
- **Multi-bubble**: Split messages on `\n\n` for better readability
- **Channel fixes**: WhatsApp & Telegram improvements

## 🚀 Quick Start

```bash
# Check status
~/.openclaw/patcher/patcher status

# Apply all patches (recommended after openclaw update)
~/.openclaw/patcher/patcher apply --all

# Apply specific patch
~/.openclaw/patcher/patcher apply progressive
```

## 📋 Available Commands

```bash
patcher status              # Show patch status
patcher status -v           # Verbose (with descriptions)

patcher apply --all         # Apply all patches
patcher apply PATCH_NAME    # Apply specific patch
patcher apply --all --force # Force reapply

patcher check PATCH_NAME    # Check patch details
patcher rollback PATCH_NAME # Rollback a patch
```

## 🔧 Available Patches

| Patch | Status | Description |
|-------|--------|-------------|
| **progressive** | ✅ Ready | Real-time progress updates + blocker fix |
| **multibubble** | ✅ Ready | Split messages on `\n\n` |
| tail_guard | 🚧 Stub | Prevent short fragment splitting |
| outbound_dedupe | 🚧 Stub | Deduplicate messages |
| reset_prompt | 🚧 Stub | Harden `/reset` command |
| media_roots | 🚧 Stub | Allow local media files |

## ⭐ What's New in v2.0

### FIXED: Progressive Mode Delivery Issue

**The problem:**
- Bot showed "typing" indicator
- No messages sent (dropped silently)
- Progress updates never arrived

**Root cause found:**
```javascript
// Line 1727 in channel-web-*.js
deliver: async (payload, info) => {
    if (info.kind !== "final") return;  // ← BLOCKER!
    // ... delivery code
}
```

**The fix:**
- Removed blocker
- Added smart filtering (skip empty/tiny updates)
- Messages now sent in real-time

### Unified Architecture

**Before (v1.x):**
- 6+ separate scripts (2338 lines)
- Manual dependency tracking
- No rollback support
- Hard to maintain

**After (v2.0):**
- Single Python package (`openclaw_patcher/`)
- Automatic dependency resolution
- Built-in rollback
- Clean modular design

## 📁 Structure

```
patcher/
├── src/                    # Python package
│   ├── __init__.py
│   ├── __main__.py         # python -m src
│   ├── core.py             # Patch engine
│   ├── cli.py              # CLI interface
│   └── patches/            # Patch plugins
│       ├── progressive.py  # ✅ With blocker fix
│       └── multibubble.py  # ✅ Message splitting
│
├── patcher                 # Convenience wrapper
├── legacy/                 # Archived v1.x scripts
└── docs/                   # Technical documentation
```

## 🔄 After OpenClaw Update

OpenClaw updates reset patches. Re-apply immediately:

```bash
# 1. Update OpenClaw
npm update -g openclaw  # or: openclaw update

# 2. Re-apply patches
~/.openclaw/patcher/patcher apply --all --force

# 3. Restart gateway
systemctl --user restart openclaw-gateway  # or: openclaw gateway restart
```

## 🧪 Testing Progressive Fix

```bash
# Apply the fix
patcher apply progressive

# Test with real message
openclaw agent --channel whatsapp --to +YOUR_NUMBER \
  --message "Create 3 test files, show progress after each" \
  --deliver

# Expected: Progress messages arrive in real-time (not batched at end)
```

## 🐛 Troubleshooting

### Patch shows "partially_applied"

Some files may not match expected patterns (different OpenClaw version). This is usually fine if core files are patched.

Check details:
```bash
patcher apply progressive --force  # See which files were patched
```

### "Dependency not met"

Some patches require others first:

```bash
# tail_guard requires progressive
patcher apply progressive
patcher apply tail_guard
```

### "OpenClaw directory not found"

Specify manually:
```bash
patcher --openclaw-dir /path/to/openclaw apply --all
```

## 📦 Direct Execution

The patcher is a Python package and can be executed directly:

```bash
# Using wrapper (recommended)
~/.openclaw/patcher/patcher status

# Direct execution
cd ~/.openclaw/patcher
python3 -m src status

# Both work identically
```

## 🔙 Rollback to v1.x

Old scripts are archived in `legacy/`:

```bash
# Use old orchestrator
~/.openclaw/patcher/legacy/patcher.old --status
~/.openclaw/patcher/legacy/patcher.old --progressive

# Old patches still functional (reference only)
```

## 🛠️ For Developers

### Adding a New Patch

1. Create `src/patches/your_patch.py`:

```python
from ..core import Patch, PatchStatus, PatchResult

class YourPatch(Patch):
    name = "your_patch"
    description = "What it does"
    dependencies = []  # or ["other_patch"]
    
    def check(self) -> PatchStatus:
        # Check if applied
        ...
    
    def apply(self) -> PatchResult:
        # Apply the patch
        ...
```

2. Register in `src/patches/__init__.py`:

```python
from .your_patch import YourPatch

ALL_PATCHES = [
    ...,
    YourPatch,
]
```

3. Test:

```bash
patcher check your_patch
patcher apply your_patch
```

## 📚 Documentation

- **Technical deep dive**: `docs/PROGRESSIVE_UPDATES.md`
- **Testing guide**: `docs/TESTING_GUIDE.md`
- **Deployment**: `docs/DEPLOYMENT_CHECKLIST.md`
- **Legacy docs**: `legacy/ACTIVE.md`, `legacy/PATCHES.md`

## 📝 Version History

### v2.0.0 (2026-03-09)
- Complete rewrite with modular architecture
- **FIXED** progressive mode WhatsApp delivery (line 1727 blocker)
- Single Python package replaces 6+ scripts
- Built-in dependency tracking and rollback
- Clean CLI interface

### v1.x (archived in `legacy/`)
- Original bash/python scripts
- Manual orchestration
- No rollback support

## 🙏 Credits

- **Root cause analysis**: Deep investigation found line 1727 blocker
- **Unified architecture**: Modular plugin system
- **Progressive fix**: First version to actually solve delivery issue

---

**Author**: dolorisu <misumi.doloris@gmail.com>  
**Co-author**: rifuki <rifuki.dev@gmail.com>  
**License**: Same as OpenClaw
