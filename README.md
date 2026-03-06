# doloris-openclaw

Fresh minimal repository for Doloris OpenClaw runtime policy and patch workflow.

## Scope
- Core workspace policy files (`workspace/*.md`)
- Runtime multi-bubble patch tooling (`patches/`)

## Key files
- `workspace/AGENTS.md`
- `workspace/CHANNEL_GUIDE.md`
- `workspace/COMMANDS.md`
- `workspace/IDENTITY.md`
- `workspace/USER.md`
- `workspace/WORKFLOW.md`
- `patches/apply-multibubble-dist-patch.py`

## Multi-bubble runtime patch
```bash
python3 ~/.openclaw/patches/apply-multibubble-dist-patch.py --status
python3 ~/.openclaw/patches/apply-multibubble-dist-patch.py --strict
systemctl --user restart openclaw-gateway
```

## Notes
- Repository is intentionally minimal and reliability-first.
- Host-local runtime files and secrets are excluded by `.gitignore`.
