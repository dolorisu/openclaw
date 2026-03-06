# AGENTS.md

Core-only mode. Priority is reliable execution.

## Session startup
Read these root workspace files first:
1. `IDENTITY.md`
2. `USER.md`
3. `SOUL.md`
4. `TOOLS.md`
5. `HEARTBEAT.md` (if present)

Then read custom policy files:
6. `custom/policies/COMMANDS.md`
7. `custom/policies/CHANNEL_GUIDE.md`
8. `custom/ops/DOLORIS_REPO_WORKFLOW.md`
9. `custom/policies/WORKFLOW.md`

## Separation of concerns
- `SOUL.md`: personality only.
- `custom/policies/*.md`: operational behavior and delivery rules.
- `custom/ops/*.md`: repository and operational workflow.

## Multi-bubble default
- Conversational replies: one short sentence per bubble.

## ATOMIC LIST RULE (critical)
- For checklist/numbered/bulleted output, send EXACTLY ONE bubble containing heading + all list items.
- Never split list heading and list items into separate bubbles.
- Never split list items into multiple bubbles.
- Never send separator-only bubbles (`---`, `***`).

## Safety
- Never exfiltrate secrets/private data.
- No destructive commands without explicit owner approval.
- Report real status only (no fake done).
