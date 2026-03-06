# DOLORIS_REPO_WORKFLOW.md

Canonical git collaboration flow for this project.

## Repositories
- `self` = `https://github.com/dolorisu/doloris.git` (private, includes sensitive operational context)
- `origin` = `git@github-rifuki-doloris:rifuki/doloris-openclaw.git` (upstream for reviewed updates)

## Policy
- Daily/experimental work happens in `self`.
- Sensitive operational context stays in `self`.
- Stable updates are proposed to `origin` via branch + PR.

## Standard update flow
1. Work on a feature branch.
2. Push branch to `self` first.
3. Validate behavior.
4. Push same branch to `origin` when ready.
5. Open PR to `origin/main`.

## Safety checklist before PR to origin
- No secrets, tokens, host-local configs, or private dumps.
- No accidental runtime state files.
- Changes are scoped and clearly described.
- Multi-bubble behavior verified.

## Quick commands
```bash
git remote -v
git checkout -b feature/<name>
git push -u self feature/<name>
git push -u origin feature/<name>
# then open PR to rifuki/doloris-openclaw:main
```

## Notes for AI agents
- Do not change remote strategy unless owner explicitly asks.
- Treat `self` as private working source and `origin` as reviewed publication target.

## Scope guard
- This workflow applies only to the `~/.openclaw` repository (Doloris OpenClaw workspace).
- Do not reuse these remotes (`self`/`origin`) for unrelated projects.
- For any other repository, follow the user's instructions for remotes/branching/PR flow.

