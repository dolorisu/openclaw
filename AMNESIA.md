# AMNESIA.md

Quick self-reminder file after context compaction.

## What is OpenClaw
- **Personal AI Assistant** - open-source agent that runs on YOUR machine/VPS
- Access via WhatsApp, Telegram, Discord, Slack, iMessage, or any chat app
- Features: clear inbox, send emails, manage calendar, flight check-in, computer control (browse, click, type)
- **Self-hosted**: Your data stays on your machine, not in the cloud
- Persistent memory, customizable skills/plugins
- Website: https://openclaw.ai/
- GitHub: https://github.com/openclaw/openclaw
- Latest version: v2026.3.13-1 (released 14 Mar 2026)
- Created by: @steipete (Peter Steinberger)
- **IMPORTANT: NOT OpenCode!** OpenCode is a different IDE coding agent tool

## Paths and Host - CRITICAL
- **Local path** `/Users/rifuki/.openclaw`: 
  - **EMPTY - NOTHING HERE!** Only contains this AMNESIA.md file
  - Used ONLY for running AI agents (like me) to maintain OpenClaw on VPS
  - NO patcher, NO config, NO OpenClaw installation
  
- **VPS alias**: `rifuki-amazon-id-ubuntu24-2c2g`
  - **THIS IS WHERE EVERYTHING LIVES!**
  - Active OpenClaw instance running here
  - Full patcher system here
  - All configs, backups, everything
  
- **VPS path**: `/home/rifuki/.openclaw`
- **Main WA group**: `120363424987356245@g.us`

## AMNESIA.md Sync Policy - MANDATORY
**ALWAYS keep local and VPS versions in sync!**

- **Local**: `/Users/rifuki/.openclaw/AMNESIA.md`
- **VPS**: `/home/rifuki/.openclaw/AMNESIA.md`

**Copy local to VPS**:
```bash
scp /Users/rifuki/.openclaw/AMNESIA.md rifuki-amazon-id-ubuntu24-2c2g:/home/rifuki/.openclaw/AMNESIA.md
```

**Copy VPS to local**:
```bash
scp rifuki-amazon-id-ubuntu24-2c2g:/home/rifuki/.openclaw/AMNESIA.md /Users/rifuki/.openclaw/AMNESIA.md
```

**Rule**: After EVERY edit, sync BOTH locations immediately!

## Patcher Status (on VPS ONLY)
**Location**: `/home/rifuki/.openclaw/patcher/`

**Check status**:
```bash
ssh rifuki-amazon-id-ubuntu24-2c2g "cd /home/rifuki/.openclaw && ./patcher/patcher status"
```

**All patches applied** (v2.0):
- multibubble: Split messages on \n\n
- progressive: Real-time progress updates  
- tail_guard: Prevent short fragment splitting
- outbound_dedupe: Deduplicate messages
- reset_prompt: Harden /reset command
- media_roots: Allow local media files
- media_send_paths: Media send path support

**Backups**: `/home/rifuki/.openclaw/patcher/backups/`

**Regression script**: `/home/rifuki/.openclaw/patcher/legacy/verify/wa-quality-regression.sh`

## VPS Command Baseline
- For OpenClaw CLI on VPS (bash path setup):
  - `source ~/.bashrc 2>/dev/null; export PATH="$HOME/.local/share/mise/shims:$PATH"`
- For env/profile-dependent tools, run via login shell:
  - `zsh -lic '<command>'`

## Tool/Auth Gotchas
- `wrangler`, `rustc`, `cargo` may look missing unless using login shell (`zsh -lic`)
- GitHub check should prefer `gh auth status` (repo protocol is HTTPS)
- `ssh -T git@github.com` may fail and is not a blocker for HTTPS git flow

## Commit Contract
- Commit author: `dolorisu <misumi.doloris@gmail.com>`
- Must include trailer: `Co-authored-by: rifuki <rifuki.dev@gmail.com>`

## Regression Commands
Run ON VPS (not locally!):

**Strict**:
```bash
bash /home/rifuki/.openclaw/patcher/legacy/verify/wa-quality-regression.sh --to 120363424987356245@g.us --timeout 300 --complex
```

**Comprehensive**:
```bash
bash /home/rifuki/.openclaw/patcher/legacy/verify/wa-quality-regression.sh --to 120363424987356245@g.us --timeout 240 --comprehensive
```

## Format Priorities
- Empty data: use concise summary/plain text (Option A), no table separators
- Ban default markdown table and separator-only lines (`---`) in ops output
- Bold headings allowed, but required phase labels stay plain: `Progress:`, `Path:`, `Command:`, `Evidence:`, `Hasil:`
