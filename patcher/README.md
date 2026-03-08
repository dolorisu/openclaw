# OpenClaw Runtime Patcher

Patch scripts in this folder target installed OpenClaw `dist` bundles and are designed to be portable across:

- Homebrew installs
- nvm / mise / volta / asdf
- npm global installs

Discovery order prioritizes `npm root -g` and then falls back to binary-path and common manager paths.

## Scripts

- `patcher` (single entrypoint, mandatory)
  - The only operator command.
  - Orchestrates sequence: multi-bubble -> progressive mode -> WA tail guard -> WA outbound dedupe -> WA reset prompt -> restart.

- `modules/` (internal)
  - Contains implementation scripts used by `patcher`.
  - Do not run module scripts directly during normal operations.

- `modules/apply-multibubble-patch.py`
  - Canonical multi-bubble patch implementation.

- `modules/apply-progressive.sh`
  - Canonical progressive-updates patch implementation.

- `verify-multibubble.sh`
  - Sends real test prompts to WhatsApp and Telegram.
  - Validates outbound message count from gateway logs.
  - Returns pass/fail for multi-bubble behavior.

- `verify/wa-quality-regression.sh`
  - Strict WhatsApp quality gate for daily engineering behavior.
  - Runs `/reset`, smoke, fenced-block, ops, and search checks.
  - Validates structure/evidence constraints (and still checks WA outbound delta).
  - Supports `--complex` for an additional heavy scenario.
  - Use `--no-strict-format` only for diagnostics.

- `modules/apply-wa-progress-tail-guard.py`
  - Prevents WhatsApp progress streaming from splitting short trailing sentence fragments into a separate bubble.
  - Skips short non-final preview updates to avoid transient duplicate/typing-only UX.
  - Keeps multi-bubble (`\n\n`) behavior unchanged.

## Usage

```bash
# 0) After `openclaw update`, patch state is reset. Re-apply immediately.

# 1) Check current status
~/.openclaw/patcher/patcher --status

# 2) Recommended daily apply (stable WhatsApp delivery)
~/.openclaw/patcher/patcher --force-multibubble --no-progressive

# 3) Optional modes
~/.openclaw/patcher/patcher --force-multibubble
~/.openclaw/patcher/patcher --no-restart
~/.openclaw/patcher/patcher --progressive
~/.openclaw/patcher/patcher --no-progressive

# 4) Verify patch state
~/.openclaw/patcher/patcher --status

# real end-to-end verification (sends test messages)
~/.openclaw/patcher/verify-multibubble.sh --wa-to +6289669848875 --tg-to @rifuki

# strict WA quality gate (recommended before handoff)
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300 --complex

# 5) If changing runtime behavior, reset chat session once
openclaw agent --to 120363425302186820@g.us --message "/reset" --deliver --timeout 240
```

### Recommended defaults
- Daily/stable mode (recommended): `--no-progressive`
- Use `--progressive` only when you explicitly need live streaming previews and can tolerate occasional WhatsApp delivery flakiness.
- Always use the orchestrator entrypoint (`patcher`), not direct module scripts.

Use `~/.openclaw/patcher/` as the only script location and prefer `patcher` as the default entrypoint.

Extended docs moved from `patches/` are available in `~/.openclaw/patcher/PATCHES.md`, `~/.openclaw/patcher/docs/`, and `~/.openclaw/patcher/archive/`.
