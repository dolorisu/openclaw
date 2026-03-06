# ACTIVE.md (What this file is for)

This is the pointer file for the active multi-bubble patch script.

**Use this script:** `~/.openclaw/patches/apply-multibubble-patch.py`

## Standard Run Order

**For WhatsApp + Telegram:**
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram
openclaw gateway restart
```

**For WhatsApp only (default):**
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict
openclaw gateway restart
```

**Test:** Send `/reset` then ask conversational questions. Verify multi-bubble response.

If docs conflict, trust `README.md` + script `--help` output.
