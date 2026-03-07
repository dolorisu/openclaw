# DOLORIS_REPO_WORKFLOW.md

Canonical git collaboration flow for this project (single-branch model).

## Repositories
- `origin` = `https://github.com/dolorisu/doloris.git`

## Policy
- Use `main` as the only active branch for normal operations.
- Push directly to `origin/main` after validation.
- Use temporary feature branches only when explicitly requested.

## Standard update flow
1. Commit scoped changes on `main`.
2. Validate behavior (runtime checks/benchmarks).
3. Push to `origin/main`.

## Safety checklist before push to origin/main
- No secrets, tokens, host-local configs, or private dumps.
- No accidental runtime state files.
- Changes are scoped and clearly described.
- Multi-bubble behavior verified.

## Quick commands
```bash
git remote -v
git checkout main
git pull --ff-only origin main
git add -A
git commit -m "chore: update workspace and patch policies"
git push origin main
```

## Notes for AI agents
- Do not change remote strategy unless owner explicitly asks.
- Default to `origin/main` for this repository.

## Scope guard
- This workflow applies only to the `~/.openclaw` repository (Doloris OpenClaw workspace).
- Do not reuse this remote strategy for unrelated projects.
- For any other repository, follow the user's instructions for remotes/branching/PR flow.
