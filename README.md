# doloris-openclaw

Private backup repository for Doloris OpenClaw workspace, config, and policies.  
Designed for seamless sync between deployments (VPS ↔ local).

## Scope
- Core workspace policy files under `workspace/custom/`
- Runtime multi-bubble patch tooling under `patches/`
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

## Multi-bubble runtime patch
```bash
# WhatsApp + Telegram (recommended)
python3 ~/.openclaw/patches/apply-multibubble-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram
openclaw gateway restart

# WhatsApp only (default)
python3 ~/.openclaw/patches/apply-multibubble-patch.py --strict
openclaw gateway restart
```

## Collaboration model
- Private working repo: `self` (`dolorisu/doloris`)
- Upstream review repo: `origin` (`rifuki/doloris-openclaw`)
- Sensitive iterative context stays in `self`
- Stable updates go to `origin` via branch + PR

## Deployment Setup (Fresh Install)

1. **Clone repo:**
   ```bash
   cd ~ && git clone git@github.doloris:dolorisu/doloris.git .openclaw
   cd ~/.openclaw
   ```

2. **Apply multi-bubble patch:**
   ```bash
   python3 patches/apply-multibubble-patch.py --strict --channels whatsapp,telegram
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
git push self main
```

**Pull changes to another deployment:**
```bash
cd ~/.openclaw
git pull self main
openclaw gateway restart
```

## Notes
- Repository is intentionally minimal and reliability-first.
- Runtime state (sessions, logs, credentials) excluded by `.gitignore`.
- `openclaw.json` is tracked for backup/sync (private repo only, never push to public).

## Reports
- Generated validation outputs are stored in `reports/`.
- Primary runtime docs remain in `patches/` and `workspace/`.

