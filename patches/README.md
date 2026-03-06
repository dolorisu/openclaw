# OpenClaw WhatsApp Multi-Bubble Patch

This patch keeps WhatsApp replies split into separate bubbles when text contains blank-line separators (`\n\n`).

It patches both runtime paths:
- `dist/deliver-*.js` (message tool / direct delivery)
- `dist/channel-web-*.js` + `dist/web-*.js` (auto-reply, including group mentions)

Canonical script:
`~/.openclaw/patches/apply-multibubble-dist-patch.py`

## Fast path
```bash
python3 ~/.openclaw/patches/apply-multibubble-dist-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-dist-patch.py --strict
systemctl --user restart openclaw-gateway
```

## Modes
- `--status`: read-only audit (patched/unpatched/unknown)
- `--dry-run`: shows what would be changed
- `--strict`: syntax-check each changed JS file with `node --check`; rollback everything on first failure

## When to rerun
- after `openclaw` update
- after reinstall
- after node/toolchain change
- new server setup

## Verify behavior
1. Send `/reset`
2. Mention bot in group and ask for 3-4 paragraph reply
3. Confirm WhatsApp displays separate bubbles
