# OpenClaw Runtime Patcher

Patch scripts in this folder target installed OpenClaw `dist` bundles and are designed to be portable across:

- Homebrew installs
- nvm / mise / volta / asdf
- npm global installs

Discovery order prioritizes `npm root -g` and then falls back to binary-path and common manager paths.

## Scripts

- `openclaw-patcher.sh` (main gateway)
  - Primary `.sh` entrypoint for day-to-day use.
  - Orchestrates sequence: multi-bubble -> progressive mode -> WA tail guard -> restart.

- `apply-multibubble-patch.py`
  - Canonical multi-bubble patcher (WhatsApp + Telegram paths).

- `apply-progressive.sh`
  - Canonical progressive-updates patcher.
  - Supports `--enable`, `--disable`, and `--status`.

- `verify-multibubble.sh`
  - Sends real test prompts to WhatsApp and Telegram.
  - Validates outbound message count from gateway logs.
  - Returns pass/fail for multi-bubble behavior.

- `apply-wa-progress-tail-guard.py`
  - Prevents WhatsApp progress streaming from splitting short trailing sentence fragments into a separate bubble.
  - Skips short non-final preview updates to avoid transient duplicate/typing-only UX.
  - Keeps multi-bubble (`\n\n`) behavior unchanged.

## Usage

```bash
~/.openclaw/patcher/openclaw-patcher.sh --status
~/.openclaw/patcher/openclaw-patcher.sh

# optional flags
~/.openclaw/patcher/openclaw-patcher.sh --force-multibubble
~/.openclaw/patcher/openclaw-patcher.sh --no-restart
~/.openclaw/patcher/openclaw-patcher.sh --progressive
~/.openclaw/patcher/openclaw-patcher.sh --no-progressive

# real end-to-end verification (sends test messages)
~/.openclaw/patcher/verify-multibubble.sh --wa-to +6289669848875 --tg-to @rifuki

# direct tail-guard only
python3 ~/.openclaw/patcher/apply-wa-progress-tail-guard.py --status
python3 ~/.openclaw/patcher/apply-wa-progress-tail-guard.py --strict
openclaw gateway restart
```

Use `~/.openclaw/patcher/` as the only script location and prefer `openclaw-patcher.sh` as the default entrypoint.

Extended docs moved from `patches/` are available in `~/.openclaw/patcher/PATCHES.md`, `~/.openclaw/patcher/docs/`, and `~/.openclaw/patcher/archive/`.
