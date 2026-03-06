# ACTIVE.md (What this file is for)

This is the pointer file for active patch scripts.

**Patches:**
1. `apply-multibubble-patch.py` - Multi-bubble conversational responses
2. `apply-progressive-patch.sh` - Progressive updates during long tasks

## Standard Run Order

**Full patch (WhatsApp + Telegram):**
```bash
# 1. Multi-bubble patch
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram

# 2. Progressive updates patch
~/.openclaw/patches/apply-progressive-patch.sh --status
~/.openclaw/patches/apply-progressive-patch.sh

# 3. Restart
openclaw gateway restart
```

**For WhatsApp only:**
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict
~/.openclaw/patches/apply-progressive-patch.sh
openclaw gateway restart
```

**Test:**
1. Multi-bubble: Send `/reset` then ask conversational questions. Verify multi-bubble response.
2. Progressive: Give multi-step task and verify interim progress updates are sent during execution.

If docs conflict, trust `README.md` + script `--help` output.
