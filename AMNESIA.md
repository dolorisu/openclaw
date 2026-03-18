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

## Git Push Notes
- **From VPS**: Push langsung ke `origin main` (SSH key sudah setup)
- **From Local (macOS)**: Check `~/.ssh/config`, gunakan `github.doloris` untuk push ke repo dolorisu

## Commit Contract
**ONLY commit when owner explicitly says "commit"!**

### Rules:
1. **Commit trigger**: ONLY when owner says "commit", "gas commit", or similar explicit command
2. **Commit message**: MUST be in English ONLY (no Indonesian words)
3. **Author**: `dolorisu <misumi.doloris@gmail.com>`
4. **Trailer**: MUST include `Co-authored-by: rifuki <rifuki.dev@gmail.com>`

### Example correct commit:
```bash
git -c user.name='dolorisu' -c user.email='misumi.doloris@gmail.com' commit -m 'feat: add new feature' -m 'Co-authored-by: rifuki <rifuki.dev@gmail.com>'
```

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

## Testing & Benchmark Procedures

### IMPORTANT: Testing MUST be done via Script or openclaw agent
**Never use `openclaw message send` for testing Doloris responses!** That bypasses the AI agent.

### 🚨 MANDATORY: Reset Before Testing
**WAJIB kirim `/reset` dulu sebelum mulai testing!** Ini untuk memastikan session steril dan hasil valid (tidak terpengaruh context sebelumnya).

**Workflow testing:**
```bash
# 1. RESET DULU (WAJIB!)
openclaw agent --channel whatsapp --to "120363406118312223@g.us" --timeout 30 --message "/reset" --deliver

# Tunggu 5 detik biar reset selesai
sleep 5

# 2. Baru test prompt
openclaw agent --channel whatsapp --to "120363406118312223@g.us" --timeout 180 --message "PROMPT_DISINI" --deliver
```

**Kenapa wajib /reset?**
- Bersihkan context/session sebelumnya
- Hasil test valid & reproducible
- Mencegah interferensi dari percakapan sebelumnya
- Memastikan policy terbaru di-load

### Correct Testing Method
```bash
# Prompt ke Doloris, response masuk WhatsApp
openclaw agent --channel whatsapp --to "120363406118312223@g.us" --timeout 180 --message "PROMPT_DISINI" --deliver
```

### Complete Benchmark Script
**Location**: `/home/rifuki/.openclaw/benchmark.sh`

**Features**:
- 8 comprehensive tests (natural prompts, multibubble, coding, images, etc.)
- Automatic log analysis
- Quality scoring for each response
- Results saved with timestamps

**Run benchmark**:
```bash
ssh rifuki-amazon-id-ubuntu24-2c2g
cd ~/.openclaw
./benchmark.sh
```

**What it tests**:
1. **Basic greeting** - Personality & emoji check
2. **Multibubble** - Split on `\n\n` verification
3. **Creative** - Puisi/content generation
4. **Math** - Calculations & formatting
5. **Technical** - Complex explanations (ERC-8128, etc.)
6. **Coding** - Python/code generation
7. **Images** - Media search/send capability
8. **Memory** - Conversation summary

### Manual Testing with Log Analysis

**Step 1: Send prompt**
```bash
export PATH="$HOME/.npm-global/bin:$PATH"
openclaw agent --channel whatsapp --to "120363406118312223@g.us" --timeout 120 --message "TEST_PROMPT" --deliver 2>&1 | tee /tmp/test-response.log
```

**Step 2: Read & analyze gateway logs**
```bash
# Get latest log
LOGFILE=$(ls -1t /tmp/openclaw/openclaw-*.log | head -1)

# Check recent messages
tail -50 "$LOGFILE" | grep -E "(Sent message|Sending message)"

# Check for multibubble (should see multiple "Sent message" for one prompt)
grep -c "Sent message" "$LOGFILE"

# Check response content
tail -100 "$LOGFILE" | grep -v "^{" | grep -v "^}" | grep -v '^\s*"' | tail -20
```

### Quality Checklist (MUST verify in logs/responses)

**Patcher Compliance**:
- ✅ **multibubble**: Messages with `\n\n` split into separate bubbles
- ✅ **progressive**: Real-time updates (not batched at end)
- ✅ **tail_guard**: Short fragments handled correctly
- ✅ **outbound_dedupe**: No duplicate messages

**Character/Human-like**:
- ✅ Uses "Rifuki~", "dong", "ya", "nih" (Indonesian casual)
- ✅ Friendly tone, not robotic
- ✅ Consistent personality (Doloris/Misumi character)

**Emojis**:
- ✅ Must have: ✨ (primary), (◕‿◕), (⌒‿⌒)
- ✅ Optional: ☕, ✅, 🎉, 📊, etc.
- ✅ Not overused (balance text:emoji)

**Formatting**:
- ✅ Bold with `**text**`
- ✅ Lists with `- ` or `1. `
- ✅ Code blocks with ``` for technical content
- ✅ NO markdown tables
- ✅ NO separator lines `---`

**Heavy Tasks** (for stress testing):
- ✅ Coding: Python, bash scripts
- ✅ Images: Search & send from internet
- ✅ Long outputs: System commands with full output
- ✅ Multi-step: Sequential operations
- ✅ Error handling: Graceful failures with recovery

### Log Analysis Commands

**Quick status**:
```bash
# Messages sent count
grep -c "Sent message" /tmp/openclaw/openclaw-*.log

# Recent activity
tail -30 /tmp/openclaw/openclaw-*.log | grep -E "(outbound|Sent|Sending)"

# Check for errors
grep -i "error\|failed\|timeout" /tmp/openclaw/openclaw-*.log | tail -10
```

**Response quality check**:
```bash
# Extract actual response content (non-JSON)
tail -100 /tmp/openclaw/openclaw-*.log | \
  grep -v "^{" | grep -v "^}" | \
  grep -v '^\s*"' | grep -v '^\s*\[' | \
  grep -v '^\s*\]' | grep -v '^\s*$' | \
  tail -20
```

## WhatsApp Groups - IMPORTANT

### Registered Groups (in OpenClaw config)
**These groups are configured and can receive messages:**
- **Production**: `120363424987356245@g.us` ✅
- **Secondary**: `120363425302186820@g.us` ✅

### Troubleshooting: Message Not Received
**If Doloris says "sent" but you don't see messages:**

1. **Check if group is registered:**
   ```bash
   openclaw config get channels.whatsapp.groups
   ```

2. **Group not in list?** Get the correct JID:
   - Open WhatsApp → Group Info
   - Look for "Group Invite Link" or ask admin for JID
   - JID format: `123456789@g.us`

3. **Add group to config:**
   ```bash
   # Edit config
   nano ~/.openclaw/openclaw.json
   
   # Add under channels.whatsapp.groups:
   "120363406118312223@g.us": {
     "requireMention": false
   }
   ```

4. **Restart gateway after config change:**
   ```bash
   systemctl --user restart openclaw-gateway
   ```

### Test Groups
- **Group C (Mujica Procedere)**: `120363406118312223@g.us` ⚠️ NOT REGISTERED
- **Main Group**: `120363424987356245@g.us` ✅ REGISTERED

**Note**: If testing to an unregistered group, messages will appear "sent" in logs but won't actually deliver to WhatsApp!
