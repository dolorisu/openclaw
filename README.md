# doloris-openclaw

Fresh minimal repository for Doloris OpenClaw runtime policy and patch workflow.

## Scope
- Core workspace policy files under `workspace/custom/`
- Runtime multi-bubble patch tooling under `patches/`

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
python3 ~/.openclaw/patches/apply-multibubble-dist-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-dist-patch.py --strict
systemctl --user restart openclaw-gateway
```

## Collaboration model
- Private working repo: `self` (`dolorisu/doloris`)
- Upstream review repo: `origin` (`rifuki/doloris-openclaw`)
- Sensitive iterative context stays in `self`
- Stable updates go to `origin` via branch + PR

## Notes
- Repository is intentionally minimal and reliability-first.
- Host-local runtime files and secrets are excluded by `.gitignore`.
