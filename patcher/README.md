# OpenClaw Runtime Patcher

Patch scripts in this folder target installed OpenClaw `dist` bundles and are designed to be portable across:

- Homebrew installs
- nvm / mise / volta / asdf
- npm global installs

Discovery order prioritizes `npm root -g` and then falls back to binary-path and common manager paths.

## Scripts

- `run-openclaw-patches.sh`
  - Orchestrator script with the correct patch sequence.
  - Runs all patchers in safe order, then restarts gateway once.
  - Also supports `--status` to check all patch states in one command.

- `verify-multibubble-wa-tg.sh`
  - Sends real test prompts to WhatsApp and Telegram.
  - Validates outbound message count from gateway logs.
  - Returns pass/fail for multi-bubble behavior.

- `apply-wa-progress-tail-guard.py`
  - Prevents WhatsApp progress streaming from splitting short trailing sentence fragments into a separate bubble.
  - Keeps multi-bubble (`\n\n`) behavior unchanged.

## Usage

```bash
~/.openclaw/patcher/run-openclaw-patches.sh --status
~/.openclaw/patcher/run-openclaw-patches.sh

# optional flags
~/.openclaw/patcher/run-openclaw-patches.sh --force-multibubble
~/.openclaw/patcher/run-openclaw-patches.sh --no-restart

# real end-to-end verification (sends test messages)
~/.openclaw/patcher/verify-multibubble-wa-tg.sh --wa-to +6289669848875 --tg-to @rifuki

# direct tail-guard only
python3 ~/.openclaw/patcher/apply-wa-progress-tail-guard.py --status
python3 ~/.openclaw/patcher/apply-wa-progress-tail-guard.py --strict
openclaw gateway restart
```
