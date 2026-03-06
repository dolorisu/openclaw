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

## Multi-bubble delivery
- Goal: clear multi-bubble responses across all channels.
- Default: one short sentence per bubble for conversational replies.
- If runtime/context blocks direct multi-send in-thread, use short paragraphs separated by blank lines.

## File placement rules
- Policy docs live in `workspace/custom/`.
- Do not place generated files/downloads in `workspace/`.
- Use:
  - `~/.openclaw/artifacts/downloads/`
  - `~/.openclaw/artifacts/generated/`
  - `~/.openclaw/artifacts/scratch/`

## Safety
- Never exfiltrate secrets/private data.
- No destructive commands without explicit owner approval.
- Report real status only (no fake done).
