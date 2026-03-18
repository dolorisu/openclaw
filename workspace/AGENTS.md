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
- **Generated files stay under `~/.openclaw/artifacts/*` (NEVER in bare workspace) EXCEPT for media files to be sent via WhatsApp - those go to `/tmp/openclaw/downloads/`**
- For owner daily ops/tasks (apt/nginx/caddy/docker/searching/file/folder), default to labeled blocks:
  - `⏳ Progress:`, `📁 Path:`, `🔧 Command:`, `📋 Evidence:`, `✅ Hasil:`.
- Concise mode may shorten lines but must keep labels, command, and concrete evidence.
- Never replace labeled blocks with one fenced summary unless user explicitly requests full raw block.

## 📁 FILE LOCATION POLICY (READ FIRST!)

### ⚠️ BEFORE Writing ANY File - CHECK This:

**Is this a generated code project?** → `~/.openclaw/artifacts/generated/projects/<project-name>/`
**Is this a one-off script/utility?** → `~/.openclaw/artifacts/generated/scripts/`
**Is this a config/template?** → `~/.openclaw/artifacts/generated/configs/`
**Is this a report/export?** → `~/.openclaw/artifacts/generated/reports/`
**Is this an image/media file FOR DOWNLOAD ONLY (will be sent via WhatsApp/Telegram)?** → `/tmp/openclaw/downloads/` ⚠️ WAJIB path ini agar gateway bisa kirim!
**Is this an image/media file FOR ARCHIVE ONLY?** → `~/.openclaw/artifacts/generated/assets/` (subfolder: images/video/audio)
**Is this a temporary/scratch file?** → `~/.openclaw/artifacts/scratch/`
**Is this for sending via WhatsApp/Telegram?** → `~/.openclaw/media/` (but prefer `/tmp/openclaw/downloads/` for downloaded images)
**ONLY if user explicitly requests workspace** → `~/.openclaw/workspace/`

### 🚫 FORBIDDEN:
- Writing generated files directly to `~/.openclaw/workspace/` (unless explicitly requested)
- Writing to bare home `~/` unless user explicitly asks
- Placing coding projects in workspace instead of artifacts

### ✅ REQUIRED:
- Always state final path in response: `Path: ~/.openclaw/artifacts/...`
- If user doesn't specify path, auto-route using rules above
- If file exists, append `-v2`, `-v3` suffix instead of overwrite

### Example Decision Tree:
```
User: "buatkan program calculator python"
└─ Is this a coding project? YES
   └─ Path: ~/.openclaw/artifacts/generated/projects/calculator/

User: "buat script backup sederhana"
└─ Is this one-off script? YES
   └─ Path: ~/.openclaw/artifacts/generated/scripts/backup.sh

User: "buat config nginx"
└─ Is this config? YES
   └─ Path: ~/.openclaw/artifacts/generated/configs/nginx.conf
```

## Safety
- No secrets/private data leakage.
- No destructive actions without explicit owner approval.
- Never claim success before verification.
