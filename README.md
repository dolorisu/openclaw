# doloris-openclaw

Private backup repository for Doloris OpenClaw workspace, config, and policies.  
Designed for seamless sync between deployments (VPS ↔ local).

## Scope
- Core workspace policy files under `workspace/custom/`
- Runtime patch tooling under `patcher/`
- **Config backup:** `openclaw.json` tracked for deployment sync (private repo only)

## Workspace structure
- `workspace/AGENTS.md` (entrypoint)
- `workspace/custom/profile/IDENTITY.md`
- `workspace/custom/profile/USER.md`
- `workspace/custom/policies/CHANNEL_GUIDE.md`
- `workspace/custom/policies/COMMANDS.md`
- `workspace/custom/policies/WORKFLOW.md`
- `workspace/custom/ops/DOLORIS_REPO_WORKFLOW.md`

## Artifact directories (non-policy files)
- `~/.openclaw/artifacts/downloads/`
- `~/.openclaw/artifacts/generated/`
- `~/.openclaw/artifacts/scratch/`

## Runtime patching
```bash
# Recommended: orchestrated sequence
~/.openclaw/patcher/openclaw-patcher.sh --status
~/.openclaw/patcher/openclaw-patcher.sh

# Direct multi-bubble patcher
python3 ~/.openclaw/patcher/apply-multibubble-patch.py --strict --channels whatsapp,telegram
openclaw gateway restart
```

## Quality Gate (handoff-safe)
Use this gate before handing tasks to another AI agent.

```bash
# Strict WhatsApp regression (real delivery)
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300

# Optional: add complex scenario
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300 --complex
```

Pass criteria (strict mode default):
- `/reset` returns concise reset acknowledgment.
- Fenced-block test remains one contiguous fenced block.
- Ops/search tests preserve labeled structure and evidence quality.
- No default markdown table, no `---` separator-only line, no placeholder evidence.

If needed for diagnosis only:
```bash
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --no-strict-format
```

## Rating rubric (core quality)
Use this practical rubric to rate current behavior for daily engineering use:

- `9.5-10.0`: deterministic across repeated runs; ops/search format stable; evidence clean.
- `9.0-9.4`: strong and usable; minor drift can still appear in edge prompts.
- `8.0-8.9`: generally works but formatting/evidence drift is noticeable.
- `<8.0`: not ready for production handoff.

Current target for handoff readiness: `>= 9.5` on strict regression passes.

## AI handoff notes
When delegating to another AI agent, share these constraints explicitly:
- For daily ops tasks, keep per-phase labels: `⏳ Progress`, `📁 Path`, `🔧 Command`, `📋 Evidence`, `✅ Hasil`.
- Default mode is efficient; evidence concise (about 3-8 lines) unless user asks raw/full detail.
- Never claim success without concrete evidence from command output.
- Run regression gate after changes and include pass/fail summary in handoff message.

Copy-paste template is available at `HANDOFF_TEMPLATE.md`.

## Collaboration model
- Single canonical remote: `origin` (`dolorisu/doloris`)
- Single canonical branch: `main`
- Day-to-day updates go directly to `origin/main`

## Deployment Setup (Fresh Install)

1. **Clone repo:**
   ```bash
   cd ~ && git clone git@github.doloris:dolorisu/doloris.git .openclaw
   cd ~/.openclaw
   ```

2. **Apply runtime patches:**
   ```bash
   ~/.openclaw/patcher/openclaw-patcher.sh
   ```

3. **Configure OpenClaw:**
   - Edit `openclaw.json` if needed (ports, auth token, model config)
   - Or keep synced config from repo

4. **Start gateway:**
   ```bash
   openclaw gateway restart
   ```

5. **Verify multi-bubble working:**
   ```bash
   openclaw status
   
   # IMPORTANT: Send /reset to load workspace files into session
   openclaw agent --channel whatsapp --to YOUR_NUMBER --message "/reset" --deliver
   
   # Test conversational → should be multi-bubble
   openclaw agent --channel whatsapp --to YOUR_NUMBER --message "jelaskan AI dalam 3 kalimat" --deliver
   ```
   
   Expected: CLI shows paragraphs with blank lines. App shows separate bubbles.

## Sync Between Deployments

**Push changes from current deployment:**
```bash
cd ~/.openclaw
git add -A
git commit -m "chore: sync config and workspace updates"
git push origin main
```

**Pull changes to another deployment:**
```bash
cd ~/.openclaw
git pull origin main
openclaw gateway restart
```

## Notes
- Repository is intentionally minimal and reliability-first.
- Runtime state (sessions, logs, credentials) excluded by `.gitignore`.
- `openclaw.json` is tracked for backup/sync (private repo only, never push to public).

## Reports
- Generated validation outputs are stored in `reports/`.
- Primary runtime docs remain in `patcher/` and `workspace/`.
