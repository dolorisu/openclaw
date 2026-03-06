# WORKFLOW.md

## Execution flow
1. Read instructions.
2. Send quick start status.
3. Execute real steps.
4. Verify output.
5. Send finish status.

## Interactive progress protocol
- Use incremental updates for multi-step tasks.
- Update format (plain text, no markdown headings/tables):
  - `Status mulai:`
  - `Progress:`
  - `Kendala:` (if any)
  - `Solusi:` (if any)
  - `Status selesai:`
- One checkpoint = max 1 short bubble (or 1 atomic list bubble if needed).
- Do not batch all checkpoints at the end.
- If possible, add short pacing between checkpoints (~2-4s) to avoid message bursts.
- Never fabricate progress, blockers, or results.
- If a step finishes, send its `Progress:` bubble immediately before starting the next step.
- Never place two `Progress:` lines in one outgoing bubble.

## Output location policy
- Generated/demo files must stay under `.openclaw`:
  - `~/.openclaw/artifacts/generated/`
  - `~/.openclaw/artifacts/scratch/`
  - `~/.openclaw/artifacts/downloads/`
- Do not write generated task files to bare `~/` unless explicitly requested.

## Reliability rules
- No fake success claims.
- Show errors honestly, then retry or report blocker.
- Verify service/config changes before saying done.

## Git hygiene
- Commit only when asked.
- Keep commits scoped and descriptive.
- Do not include host-local secrets/config by accident.
- Follow `custom/ops/DOLORIS_REPO_WORKFLOW.md` for remote/PR flow.
