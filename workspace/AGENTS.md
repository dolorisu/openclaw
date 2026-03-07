# AGENTS.md

Core-only mode. Priority is reliable execution.

## Startup order
1. `IDENTITY.md`
2. `USER.md`
3. `SOUL.md`
4. `TOOLS.md`
5. `HEARTBEAT.md` (if present)
6. `custom/policies/COMMANDS.md`
7. `custom/policies/CHANNEL_GUIDE.md`
8. `custom/ops/DOLORIS_REPO_WORKFLOW.md`
9. `custom/policies/WORKFLOW.md`

## Scope split
- `SOUL.md`: personality only.
- `custom/policies/*.md`: behavior rules.
- `custom/ops/*.md`: repo workflow.

## Non-negotiables
- Incremental progress updates for multi-step work (no end-batch dump).
- Atomic checklist bubble (heading + list together).
- Generated files stay under `~/.openclaw/artifacts/*`.
- For owner daily ops/tasks (apt/nginx/caddy/docker/searching/file/folder), default to labeled blocks:
  - `⏳ Progress:`, `📁 Path:`, `🔧 Command:`, `📋 Evidence:`, `✅ Hasil:`.
- Concise mode may shorten lines but must keep labels, command, and concrete evidence.
- Never replace labeled blocks with one fenced summary unless user explicitly requests full raw block.

## Safety
- No secrets/private data leakage.
- No destructive actions without explicit owner approval.
- Never claim success before verification.
