# OpenClaw Patches (WhatsApp + Telegram)

This directory contains patches to improve OpenClaw's WhatsApp and Telegram experience.

## Patches

### 1. Multi-Bubble Patch (`apply-multibubble-patch.py`)
Enables multi-bubble responses for WhatsApp and Telegram when text contains blank-line separators (`\n\n`).

It patches both runtime paths:
- `dist/deliver-*.js` (message tool / direct delivery)
- `dist/channel-web-*.js` + `dist/web-*.js` (auto-reply, including group mentions)

### 2. Progressive Updates Patch (`apply-progressive-patch.sh`)
Enables block streaming to send interim text updates during long tasks instead of batching at the end.

Changes: `disableBlockStreaming: true` → `false` in web channel files

## Quick Start (Both Channels)
```bash
# Multi-bubble
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram

# Progressive updates
~/.openclaw/patches/apply-progressive-patch.sh --status
~/.openclaw/patches/apply-progressive-patch.sh

# Restart
openclaw gateway restart
```

## Quick Start (WhatsApp Only)
```bash
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict
~/.openclaw/patches/apply-progressive-patch.sh
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

## Testing

**Quick CLI Test (no manual typing needed):**
```bash
# WhatsApp
openclaw agent --channel whatsapp --to +6289669848875 --message "/reset" --deliver
openclaw agent --channel whatsapp --to +6289669848875 --message "jelaskan tentang AI dalam beberapa kalimat" --deliver

# Telegram  
openclaw agent --channel telegram --to 849612359 --message "/reset" --deliver
openclaw agent --channel telegram --to 849612359 --message "jelaskan tentang neural network dalam beberapa kalimat" --deliver
```

**Expected:** CLI output shows paragraphs separated by blank lines. App shows multiple bubbles.

**Detailed Testing Guide:** See [TESTING.md](./TESTING.md) for comprehensive testing procedures, debugging, and automated scripts.

## Legacy Script

Old script name `apply-multibubble-dist-patch.py` is deprecated. Use `apply-multibubble-patch.py` instead.
