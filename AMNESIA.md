# AMNESIA.md

Quick self-reminder file after context compaction.

## Paths and host
- Local repo path: `/Users/rifuki/.openclaw`
- VPS alias: `rifuki-amazon-id-ubuntu24-2c2g`
- VPS repo path: `/home/rifuki/.openclaw`
- Main WA group target: `120363424987356245@g.us`

## VPS command baseline
- For OpenClaw CLI on VPS (bash path setup):
  - `source ~/.bashrc 2>/dev/null; export PATH="$HOME/.local/share/mise/shims:$PATH"`
- For env/profile-dependent tools, run via login shell:
  - `zsh -lic '<command>'`

## Tool/auth gotchas
- `wrangler`, `rustc`, `cargo` may look missing unless using login shell (`zsh -lic`).
- GitHub check should prefer `gh auth status` (repo protocol is HTTPS).
- `ssh -T git@github.com` may fail and is not a blocker for HTTPS git flow.

## Commit contract (owner preference)
- Commit author must be:
  - `dolorisu <misumi.doloris@gmail.com>`
- Commit must include trailer:
  - `Co-authored-by: rifuki <rifuki.dev@gmail.com>`

## Regression commands
- Strict:
  - `bash /home/rifuki/.openclaw/patcher/verify/wa-quality-regression.sh --to 120363424987356245@g.us --timeout 300 --complex`
- Comprehensive:
  - `bash /home/rifuki/.openclaw/patcher/verify/wa-quality-regression.sh --to 120363424987356245@g.us --timeout 240 --comprehensive`

## Format priorities
- Empty data: use concise summary/plain text (Option A), no table separators.
- Ban default markdown table and separator-only lines (`---`) in ops output.
- Bold headings allowed, but required phase labels stay plain: `Progress:`, `Path:`, `Command:`, `Evidence:`, `Hasil:`.
