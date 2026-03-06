# OpenClaw Multi-Bubble Patch (WhatsApp + Telegram)

This patch enables multi-bubble responses for WhatsApp and Telegram when text contains blank-line separators (`\n\n`).

It patches both runtime paths:
- `dist/deliver-*.js` (message tool / direct delivery)
- `dist/channel-web-*.js` + `dist/web-*.js` (auto-reply, including group mentions)

**Canonical script:** `~/.openclaw/patches/apply-multibubble-patch.py`

## Fast Path (Both Channels)
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram
openclaw gateway restart
```

## Fast Path (WhatsApp Only - Default)
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict
openclaw gateway restart
```

## Modes
- `--status`: read-only audit (patched/unpatched/unknown)
- `--dry-run`: shows what would be changed
- `--strict`: syntax-check each changed JS file with `node --check`; rollback everything on first failure
- `--channels <list>`: comma-separated channels (default: `whatsapp`). Example: `--channels whatsapp,telegram`

## When to rerun
- after `openclaw` update
- after reinstall
- after node/toolchain change
- new server setup

## Verify Behavior

**WhatsApp:**
1. Send `/reset`
2. Ask: "jelaskan tentang AI dalam beberapa kalimat"
3. Confirm multiple bubbles (one sentence per bubble)

**Telegram:**
1. Send `/reset`
2. Ask: "jelaskan tentang quantum computing dalam beberapa kalimat"
3. Confirm multiple bubbles

## Legacy Script

Old script name `apply-multibubble-dist-patch.py` is deprecated. Use `apply-multibubble-patch.py` instead.
