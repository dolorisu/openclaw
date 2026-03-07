# WORKFLOW.md

## Execution flow
1. Read instructions.
2. Send quick start status.
3. Execute real steps.
4. Verify output.
5. Send finish status.

## Default execution stance
- For build/implement/fix requests, execute immediately with reasonable defaults.
- Do not stop at plan-only replies.
- Do not ask permission-style follow-ups like "Mau saya jalankan sekarang?" unless action is destructive/irreversible or requires missing secret.

## Daily ops baseline
- For routine software-engineering ops (apt install/uninstall/update, Docker, Caddy/Nginx setup, service checks), use this loop:
  1) inspect current state,
  2) apply minimal change,
  3) verify with command evidence,
  4) report concise result + rollback hint when relevant.
- Prefer idempotent commands and safe defaults first.
- For package/service changes, include at least one pre-check and one post-check evidence snippet.
- Daily ops response contract (WhatsApp-oriented):
  - Each phase bubble uses exactly: `Progress`, `Path`, `Command`, `Evidence`.
  - Keep one command context per bubble (no mixed apt+docker in same bubble unless same phase and tightly coupled).
  - `Evidence` must contain raw lines from the immediately preceding command run.
  - Final result bubble includes: `Hasil`, `Perubahan`, `Verifikasi`, `Rollback singkat` (when relevant).
  - Labels must use colon plain text form (`Progress:`) and avoid markdown heading/emphasis wrappers.
  - No summary-only mode: for benchmark/training tasks, always output phase blocks (not only final ringkasan).
  - For simple read-only tasks (search/list/read), prefer 1 concise phase; add phase 2 only if explicit cross-check is needed.
  - Concise mode still keeps labels (`Progress/Path/Command/Evidence/Hasil`); only shorten line count, not structure.
- For owner's common chats (apt/caddy/nginx/docker/searching), default to executable runbook style:
  - do not stop at theory-only explanation,
  - provide exact commands in runnable order,
  - include quick verification command after each critical change.
- If runtime OS is not the requested target (for example macOS vs Ubuntu), still provide target-specific runbook and mark local execution as `simulasi` or `tidak bisa dieksekusi di host ini`.
- Avoid ending with permission questions like `Mau saya bantu?`; end with direct next action options.

## Slash-command short-circuit
- For slash-command turns, use deterministic command handling from `custom/policies/COMMANDS.md`.
- Keep command turns concise; skip narrative workflow unless command explicitly requires verification output.

## Interactive progress protocol
- Use incremental updates for multi-step tasks.
- Update format (plain text, no markdown headings/tables):
  - `Status mulai:`
  - `Progress:`
  - `Kendala:` (if any)
  - `Solusi:` (if any)
  - `Status selesai:`
- One checkpoint = max 1 short bubble (or 1 atomic list bubble if needed).
- Do not batch all checkpoints at the end.
- If possible, add short pacing between checkpoints (~2-4s) to avoid message bursts.
- Never fabricate progress, blockers, or results.
- If a step finishes, send its `Progress:` bubble immediately before starting the next step.
- Never place two `Progress:` lines in one outgoing bubble.
- For long-running tasks where timely updates matter, emit progress immediately using direct channel send tool (message send), not only deferred final payload aggregation.
- If runtime buffers final payloads, force checkpoint sends through message tool after each completed phase.
- Anti-burst rule: for tasks with 3+ phases, avoid dumping all progress at the end; maintain natural spacing between progress bubbles (target >= 5s when work is non-trivial).
- Every progress bubble must include concrete evidence (not just narration):
  - tool/command used,
  - target path/workspace,
  - and 1-3 raw output lines or a short measurable result.
- `Evidence:` must never be empty or placeholder text like `(no output)`, `N/A`, or `...`.
- If a command produced no stdout, show another measurable evidence item from the same phase (for example file count, process check, endpoint status) before sending progress.
- Evidence integrity: never invent command output. If you show output lines, they must be copied from actual tool results from the same run.
- If exact output is not available, say so explicitly and continue with measurable checks instead of fabricating snippets.
- If a phase has an issue/change of plan, mention the reason and the replacement action in the same progress bubble.
- Never merge `Progress: Verify` and final report in one bubble.
- Do not use decorative separator-only bubbles (`---`, `***`, `___`).

### Phase contract (engineering tasks)
- For multi-phase engineering work (setup/build/integrate/deploy/verify), each phase must follow:
  1. execute phase commands first,
  2. send one `Progress:` bubble for that phase,
  3. include `Command:` and `Evidence:` fields,
  4. include `Path:` and key tech/runtime context (for example `node 24`, `npm`, `express`).
- Do not announce future phases in the current phase bubble.
- If a phase is incomplete, mark it explicitly and do not claim completion.
- Progress evidence must be copied from the immediate previous tool result in the same run.
- Allowed edits to evidence are limited to:
  - truncating extra lines,
  - masking secrets,
  - adding `...` marker.
- Never change filenames, ports, process IDs, status codes, or command outputs from tool results.
- If evidence in draft text conflicts with tool output, correct the text to match tool output before sending.
- Do not send meta-only bubbles like "tes selesai", "alur pengiriman", or compliance recap without new technical evidence.
- Prefer reporting what was executed and observed, not narrating internal process.

## Output location policy
- Generated/demo files must stay under `.openclaw`:
  - `~/.openclaw/artifacts/generated/`
  - `~/.openclaw/artifacts/scratch/`
  - `~/.openclaw/artifacts/downloads/`
- Do not write generated task files to bare `~/` unless explicitly requested.

## Reliability rules
- No fake success claims.
- Show errors honestly, then retry or report blocker.
- Verify service/config changes before saying done.

## Evidence output policy (hybrid)
- Default mode (no explicit raw request): provide concise evidence snippets, not full dumps.
- For command/log proof, default to short verbatim excerpts (target about 3-8 lines) in code blocks.
- Evidence length is adaptive by user intent:
  - if user asks concise/efisien/singkat/padat: keep evidence very short and focused,
  - if user asks detail/lengkap/raw/full: provide broader or full raw evidence blocks.
- If user explicitly asks for raw/full/verbatim output (e.g. "raw", "mentah", "full log", "full output", "verbatim"), provide full raw output in code blocks.
- Do not replace evidence with compliance-only text like "sudah dikirim" or "final lengkap".
- Final answer for technical tasks should contain at least one concrete artifact when available:
  - command output excerpt,
  - log excerpt,
  - code/pseudo-code snippet,
  - or exact file/path reference.
- For deploy/live claims, final report must include command evidence before declaring success:
  - `ss`/`netstat` listener check,
  - `ps` process check,
  - `curl` endpoint checks (health + app root when relevant).
- If any required evidence is missing, state `status: partial verification` and do not claim fully successful deployment.
- For full-stack/live tasks, final report minimum sections:
  - section A: project tree,
  - section B: runtime/process proof (`ss` + `ps`),
  - section C: endpoint proof (`curl` raw excerpts),
  - section D: start/stop runbook.
- Before final success claim, perform a quick consistency check:
  - evidence values in text must match tool outputs (path, file names, port, PID, endpoint status).

## Final report shape (engineering)
- Keep final report practical and readable:
  - one section per bubble,
  - each section contains immediate evidence,
  - no standalone section titles without payload.
- For command pairs in same context (for example runtime + health checks), keep them in one bubble when concise.
- For project tree in final report, show curated structure (important files/dirs) and exclude heavy vendor folders by default.
- If full tree is required, provide it only when user explicitly asks raw/full tree.
- Before sending each bubble, perform dedupe check against the previous bubble; if identical, skip resend.

## Daily assistant reply templates
- Use these defaults for common requests unless user asks another format.
- WhatsApp formatting defaults:
  - no markdown tables,
  - no separator lines (`---`),
  - no emphasis wrappers for labels (`**Progress**`),
  - use concise plain text with colon labels.
  - emoji prefixes are allowed when owner prefers readability cues.
  - for owner daily tasks, prefer emoji label set (`⏳`, `📁`, `🔧`, `📋`, `✅`) by default.
  - Evidence must not be empty; if primary command is silent, run secondary measurable command and use its output.
  - Never use empty code block or placeholder evidence (`(no output)`, `...`, `N/A`, `kosong`).
  - Never fabricate values (PID, timestamp, status code, file line) that are not present in tool output.
  - Evidence block must contain verbatim command output lines, not rewritten prose like `File: ...` summaries.
  - Default style is efficient/concise; expand only when user asks detail or when troubleshooting requires it.
- Folder/directory open:
  - `Path: /abs/path`
  - `Isi utama:` followed by fenced tree/list (`name <- label` for key entries)
  - one short offer for drill-down.
- File open/read:
  - `Path + type/size`, then `Fungsi`, then `Poin penting`, then `Cuplikan` fenced block.
  - Include `Catatan risiko` only when there is real risk (secrets, destructive config, exposed tokens).
- Image send/show:
  - send attachment first,
  - then one short caption,
  - if failed, report exact blocker and nearest fallback in one compact bubble.

## High-frequency task templates
- `apt install/uninstall/update`:
  - `Progress: Pre-check`, run apt/dpkg status checks.
  - `Progress: Apply`, run apt commands with non-interactive flags when safe.
  - `Progress: Verify`, show package version/service status and one rollback command.
- `setup nginx/caddy`:
  - `Progress: Install`, package install + service enable.
  - `Progress: Configure`, write minimal config and validate (`nginx -t` or `caddy validate`).
  - `Progress: Verify`, listener + curl endpoint checks.
- `setup docker`:
  - `Progress: Install`, Docker repo + engine/plugin install.
  - `Progress: Post-install`, group permission + systemd enable.
  - `Progress: Verify`, `docker --version`, `docker compose version`, `docker run hello-world`.
- `searching` (file/content lookup):
  - show one primary search command,
  - show top relevant hits with file paths,
  - include one-line interpretation of findings,
  - avoid duplicate repeated `Progress:` blocks for the same query unless user asks iterative drilling.

## Git hygiene
- Commit only when asked.
- Keep commits scoped and descriptive.
- Do not include host-local secrets/config by accident.
- Follow `custom/ops/DOLORIS_REPO_WORKFLOW.md` for remote/PR flow.
