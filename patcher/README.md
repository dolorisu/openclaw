# OpenClaw Unified Patcher v2.0 🚀

**NEW!** Complete rewrite with modular plugin architecture and critical progressive mode fix.

## What's New in v2.0

### ✅ FIXED: Progressive Mode WhatsApp Delivery

**The problem that plagued us for months is now SOLVED!**

- **Before:** Bot shows "typing" but never sends messages
- **Root cause:** Line 1727 blocker `if (info.kind !== "final") return;` dropped all progress updates
- **After:** Messages sent in real-time with smart filtering

### ✅ Unified Architecture

- Single Python package (`openclaw_patcher/`) instead of 6+ separate scripts
- Modular patches as plugins with dependency tracking
- Built-in rollback support
- Clean CLI with detailed status reporting

## Quick Start

```bash
# Check patch status
~/.openclaw/patcher/patcher status

# Apply progressive fix (enables real-time updates!)
~/.openclaw/patcher/patcher apply progressive

# Apply multi-bubble splitting
~/.openclaw/patcher/patcher apply multibubble

# Apply all patches
~/.openclaw/patcher/patcher apply --all
```

See **[README-NEW-PATCHER.md](README-NEW-PATCHER.md)** for complete documentation.

## Architecture

```
patcher/
├── openclaw_patcher/        # Python package (NEW)
│   ├── core.py             # Patch engine
│   ├── cli.py              # CLI interface
│   └── patches/            # Modular patches
│       ├── progressive.py  # ✅ WITH BLOCKER FIX
│       └── multibubble.py  # ✅ Message splitting
│
├── patcher                 # Main CLI (NEW)
├── legacy/                 # Old scripts (archived)
│   ├── modules/            # Old patch scripts
│   └── patcher.old         # Old orchestrator
└── docs/                   # Documentation
```

## Migration from v1.x

**Old command:**
```bash
~/.openclaw/patcher/patcher --progressive
```

**New command (same result, better implementation):**
```bash
~/.openclaw/patcher/patcher apply --all
```

Old scripts are still available in `legacy/` for reference.

## Usage (v2.0)

```bash
# 0) After `openclaw update`, patch state is reset. Re-apply immediately.

# 1) Check current status
~/.openclaw/patcher/patcher status

# 2) Apply all patches (recommended - includes progressive fix!)
~/.openclaw/patcher/patcher apply --all

# 3) Apply specific patches
~/.openclaw/patcher/patcher apply progressive      # Real-time progress updates
~/.openclaw/patcher/patcher apply multibubble      # Message splitting

# 4) Force reapply (after OpenClaw update)
~/.openclaw/patcher/patcher apply --all --force

# 5) Check specific patch
~/.openclaw/patcher/patcher check progressive

# 6) Rollback a patch (if needed)
~/.openclaw/patcher/patcher rollback progressive

# 7) Apply without gateway restart (for testing)
~/.openclaw/patcher/patcher apply --all --no-restart
```

### Legacy Commands (still work, in legacy/)

```bash
# Old orchestrator (archived but functional)
~/.openclaw/patcher/legacy/patcher.old --status
~/.openclaw/patcher/legacy/patcher.old --progressive

# Old verification (archived)
~/.openclaw/patcher/legacy/verify-multibubble.sh --wa-to +6289669848875
```

## Direct channel smoke tests (recommended)

```bash
# WhatsApp direct/group
openclaw agent --channel whatsapp --to 120363425302186820@g.us --message "WA smoke: reply 1 line" --deliver --timeout 240

# Telegram direct (prefer numeric user ID)
openclaw agent --channel telegram --to 849612359 --message "TG smoke: reply 1 line" --deliver --timeout 240
```

Notes:
- Telegram `--to` is more reliable with numeric user ID than `@username`.
- For multi-bubble proof on Telegram, ask explicit 3-paragraph response with markers (`BUBBLE-1/2/3`).

### Recommended defaults
- Daily/stable mode (recommended): `--no-progressive`
- Use `--progressive` only when you explicitly need live streaming previews and can tolerate occasional WhatsApp delivery flakiness.
- Always use the orchestrator entrypoint (`patcher`), not direct module scripts.

Use `~/.openclaw/patcher/` as the only script location and prefer `patcher` as the default entrypoint.

Extended docs moved from `patches/` are available in `~/.openclaw/patcher/PATCHES.md`, `~/.openclaw/patcher/docs/`, and `~/.openclaw/patcher/archive/`.
