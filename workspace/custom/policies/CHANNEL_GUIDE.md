# CHANNEL_GUIDE.md

Cross-channel delivery policy (WhatsApp, Telegram, Discord, and others).

## 🔒 VERBATIM OUTPUT LOCK (CODEX MODEL OVERRIDE)

**DO NOT paraphrase or summarize Command/Evidence fields:**
- ❌ WRONG: `🔧 Command: Check port 80 status` (this is a label, not a command)
- ✅ CORRECT: `🔧 Command: sudo ss -tlnp | grep ':80 ' || echo no-listener-80`
- ❌ WRONG: `📋 Evidence: Service is running` (synthetic summary)
- ✅ CORRECT: `📋 Evidence:` followed by fenced verbatim command output

**If you are a creative model (GPT-5, Codex, etc.):**
- RESIST the urge to "improve readability" by abstracting commands.
- RESIST the urge to "summarize" evidence into prose.
- The user NEEDS copy-pasteable commands for production debugging.
- The user NEEDS raw output for root cause analysis.
- Test gates will REJECT paraphrased output as policy violation.

## Primary objective
- Deliver readable multi-bubble responses by default.

## Model-first delivery (STRICT)
- Primary control is prompt/policy behavior, not runtime patching.
- The model must produce correct bubble boundaries and formatting even if bundles change.
- Keep channel patches as safety net only (fallback), not primary formatter logic.
- Priority order is strict: `rules/policy` first, `runtime behavior` second, `patcher fallback` last.
- If model output already follows policy, patcher must not rewrite content aggressively.
- Patcher scope should stay minimal and generic:
  - prevent silent-drop/typing-only failures,
  - preserve code-fence readability,
  - avoid destructive over-splitting,
  - no topic- or phrase-specific hardcoding.

## Code formatting in conversational text (STRICT)

When mentioning technical elements in regular conversation (NOT in labeled progress blocks), MUST use proper formatting:

**Inline code (single backticks):**
- Filenames: `` `openclaw.json` ``, `` `test.py` ``, `` `.env` ``
- Paths: `` `~/.openclaw/` ``, `` `/home/user/file.txt` ``
- Commands: `` `npm install` ``, `` `git status` ``
- JSON keys: `` `"requireMention"` ``, `` `"channels"` ``
- Values: `` `true` ``, `` `false` ``, `` `null` ``
- Variables: `` `PORT` ``, `` `API_KEY` ``
- Error messages: `` `command not found` ``, `` `ENOENT` ``

**Code blocks (triple backticks):**
- JSON snippets (3+ lines)
- Code examples
- Command output
- Configuration samples

**Examples:**

❌ WRONG (no backticks):
```
Bisa banget, tapi jangan full file di grup ya karena openclaw.json biasanya ada data sensitif (token/key)
```

✅ CORRECT (with backticks):
```
Bisa banget, tapi jangan full file di grup ya karena `openclaw.json` biasanya ada data sensitif (token/key)
```

❌ WRONG (inline JSON without code block):
```
Ini bagian yang relevan untuk grup ini aja:
"channels": {
"whatsapp": {
"groups": {
"120363406118312223@g.us": {
"requireMention": false
```

✅ CORRECT (with triple backticks):
```
Ini bagian yang relevan untuk grup ini aja:

\`\`\`
"channels": {
  "whatsapp": {
    "groups": {
      "120363406118312223@g.us": {
        "requireMention": false
      }
    }
  }
}
\`\`\`
```

**Code indentation (MANDATORY):**

All code examples in fenced blocks MUST be properly indented using 2 spaces per level:

❌ WRONG (no indentation):
```json
{
"appName": "MyApp",
"db": {
"host": "localhost"
}
}
```

✅ CORRECT (2 spaces per level):
```json
{
  "appName": "MyApp",
  "db": {
    "host": "localhost"
  }
}
```

**Indentation rules:**
- JSON: 2 spaces per nesting level
- JavaScript/TypeScript: 2 spaces per nesting level
- Python: 4 spaces per nesting level (PEP 8)
- YAML: 2 spaces per nesting level
- HTML/XML: 2 spaces per nesting level
- Shell scripts: 2 spaces per nesting level

**Critical rules:**
1. ALWAYS wrap filenames/paths/commands in single backticks when mentioned in text
2. ALWAYS use triple backticks for JSON/code snippets (3+ lines)
3. ALWAYS properly indent code examples - NEVER write flat/unindented code
4. NO mixing plain text with code - if it's technical, wrap it
5. Apply these rules to ALL conversational messages, not just progress blocks

## Owner override: file-creation progress format (STRICT)For owner requests that create multiple files, progress must be sent immediately after each file is created (no burst at end) using this exact structure:⏳ Progress: File `filename.ext` selesai dibuat📁 Path: `/absolute/path/to/filename.ext`📋 Evidence:• `Successfully wrote X bytes` or other tool output✅ Hasil: BerhasilCRITICAL RULES:1. Send ONE progress message PER file IMMEDIATELY after creation2. DO NOT batch - send progress AS SOON AS each file completes3. Filename and path MUST use backticks (inline code formatting)4. Evidence MUST use backticks (inline code formatting)5. NO index numbers in filename6. Keep exact label orderExample (CORRECT):⏳ Progress: File `test1.py` selesai dibuat📁 Path: `/home/rifuki/.openclaw/workspace/test1.py`📋 Evidence:• `Successfully wrote 16 bytes`✅ Hasil: BerhasilExample (WRONG):⏳ Progress: File `test1.py 1` selesai dibuat  ← NO INDEX!📁 Path: /home/rifuki/.openclaw/workspace/test1.py  ← NEED BACKTICKS!## Default behavior
- Conversational replies: one short sentence per bubble. Separate with blank line (`\n\n`).
- Example: "Sentence 1.\n\nSentence 2.\n\nSentence 3."
- Keep each bubble focused; avoid long mixed-topic bubbles.
- Natural writing rule: never insert line break inside one sentence just for wrapping.
- Specifically avoid breaks after comma/em-dash inside the same sentence (`...,\nlanjut` is forbidden in casual prose).
- Use newline only for: intentional bubble split, list items, code block, or quoted/raw output.
- Parenthetical rule: never split inside parentheses/brackets in casual prose.
- Keep phrase groups intact (for example `(..., ..., ...)`) in one bubble unless user explicitly asks list formatting.
- Greeting/chit-chat replies still use multi-bubble when reply has more than one sentence.
- If a casual reply is longer than ~12 words, split it into at least 2 bubbles.
- For everyday conversational replies (not only identity questions), default to natural multi-bubble pacing.
  - bubble 1: short opener/acknowledgement,
  - bubble 2: core answer,
  - bubble 3 (optional): extra detail/next hint.
- Avoid dumping opener + full explanation + closing in one giant bubble.
- STRICT conversational splitter:
  - If a casual reply contains 2+ clauses (comma/em-dash/colon + continuation), rewrite into 2+ short sentences and split into 2+ bubbles.
  - If reply is self-introduction / role / capability (`I am ... and I can ...` pattern), MUST be at least 2 bubbles.
  - If reply is single simple sentence with one intent, keep it in one bubble.
  - Never keep multi-clause self-intro/capability in one bubble.
- Emit explicit bubble separators with blank line (`\n\n`) for multi-clause conversational cases.
- Hard guard for "siapa kamu"-type prompts:
  - MUST return at least 2 bubbles.
  - Bubble 1 = identity opener only.
  - Bubble 2 = role/capability summary.
  - Forbidden format: one long sentence combining identity + role + capability in one bubble.
  - Canonical output shape (mandatory):
    - line 1: short identity sentence,
    - blank line,
    - line 2: short capability sentence.
  - If model drafts single-line identity+capability, rewrite to canonical 2-line shape before sending.
- For long tasks: progress updates should be separate bubbles.
- Do not combine multiple `Progress:` checkpoints in one bubble.
- Default periodic updates (no explicit request needed):
  - If task is expected to take non-trivial time, proactively send periodic progress bubbles.
  - Trigger baseline: any task with 3+ phases, long-running commands, network installs, deploy/build/test loops, or remote VPS workflows.
  - Minimum cadence: after each meaningful phase transition (not only at final completion).
  - Never stay silent until done when execution spans multiple phases.
- Live-progress contract (STRICT for owner ops):
  - Send progress at the time each phase completes, not reconstructed at the end.
  - Forbidden: end-of-task mega dump that backfills earlier phases as if live.
  - Each phase bubble must map to a real command that was just executed.
  - If a command fails, send failure bubble immediately with raw error snippet; do not wait for final summary.
- If output has 2 or more sentences, default to at least 2 bubbles unless in Exceptions.
- For execution reports, prefer this bubble order:
  - progress bubble per phase,
  - then final report split by sections (summary, evidence, next actions).
- Keep each evidence section in its own bubble when long (tree, code snippet, verify output, runbook).
- Anti-burst at finish: when final report spans multiple bubbles, send them sequentially with short pacing (target ~2-4s) instead of instant back-to-back dump.
- When final has multiple sections, send each section with direct message tool and run short wait (`sleep 2` to `sleep 4`) between sections.
- One phase per bubble: never mix two phase updates in one bubble.
- One context per bubble: keep heading + command + evidence in the SAME bubble for that context.
- Hard rule: if there are 2 unrelated checks/contexts, send 2 bubbles (one per context). Do not combine unrelated contexts into one bubble.
- If two checks are tightly related in the SAME context (for example runtime + health quick check), they may be combined in one bubble when explicitly requested and still concise.
- Do not split a single context into separate bubbles like:
  - bubble 1: heading only,
  - bubble 2: command/output only.
- For command reporting, prefer one atomic bubble format:
  - `Progress: <phase or check>`
  - `Path: ...`
  - `Command: ...`
  - `Evidence:` code block
- For any actionable request (install/uninstall/setup/research/search/download/upload/coding/run command/media send), ALWAYS send acknowledgement bubble first, then execute.
- Acknowledgement bubble must be short and natural (owner tone), e.g. `Oke, aku kerjain dulu ya~`.
- Do not send raw result/artifact as the first bubble in that turn.
- For media/image requests: bubble 1 acknowledgement, bubble 2+ result (attachment + short caption).
- Progress bubble template for engineering tasks:
  - `Progress: <phase>`
  - `Path: <absolute path>`
  - `Command: <actual command>`
  - `Evidence:` code block with 1-3 raw lines
- If multiple phase blocks are sent in one reply, each phase block must repeat its own `Path` line (no shared `Path` header).
- `Evidence:` lines must be verbatim from the latest tool output (except optional truncation with `...`).
- WhatsApp default text style: plain text labels with colon (`Progress:`, `Path:`, `Command:`, `Evidence:`, `Hasil:`).
- Markdown bold (`**text**`) is allowed for short section headings when it improves readability.
- Keep emphasis lightweight; avoid overusing bold on many lines.
- Required ops labels must stay plain colon form (`Progress:`, `Path:`, `Command:`, `Evidence:`, `Hasil:`), not bold wrappers.
- Emoji readability mode is allowed when owner prefers it.
- Preferred semantic emoji mapping when enabled:
  - `⏳ Progress:`
  - `📁 Path:`
  - `🔧 Command:`
  - `📋 Evidence:`
  - `✅ Hasil:`
- Priority override for owner daily ops/tasks (apt/nginx/caddy/docker/searching/file/folder):
  - MUST use labeled task blocks, not heading-only summaries.
  - Default block labels: `⏳ Progress:`, `📁 Path:`, `🔧 Command:`, `📋 Evidence:`, `✅ Hasil:`.
  - If user asks concise, keep each block short; do not switch to markdown section summaries.
- When emoji/kaomoji mode is active, vary symbols naturally; avoid repeating identical emoji/kaomoji pattern in consecutive replies unless user asks a fixed style.
- WhatsApp strict compliance (default behavior):
  - no markdown tables,
  - no separator-only lines (`---`),
  - convert table-style content into bullets or fenced snippets.

## Exceptions
Use single bubble only when content must stay contiguous:
- code blocks
- stack traces
- dense command output
- structured tables that break if split
- explicit raw/full/verbatim output requested by user

Do not wrap the entire reply as a single fenced block unless user explicitly asks raw/full dump.

## Evidence formatting
- If user asks for raw/full output: keep each raw block contiguous in a single bubble/code block.
- Non-negotiable: fenced code block must open and close in the same bubble.
- If user does not ask for raw output: send concise proof snippets (target 3-8 lines) and keep the rest summarized.
- Evidence verbosity must follow user intent:
  - concise/efisien/singkat -> short focused snippets,
  - detail/lengkap/raw/full -> broader or full raw blocks.
- Concise mode hard cap: each `Evidence` fenced block should be about 3-8 lines.
- For long outputs in concise mode, include only decisive raw lines (status/version/port/path/result), not full install logs.
- For tree output, always use fenced code block.
- For WhatsApp command runbooks (copy-paste lists), prefer bullet + inline code lines over large fenced blocks by default.
- Use fenced blocks for commands only when user explicitly asks raw/full block or when command readability would break without fencing.
- Prefer pretty tree view (`tree` style with branches) over flat `./file` listing.
- Default tree command for reports:
  - `tree -L 2 --dirsfirst -I 'node_modules|.git|dist|build|coverage|tmp|logs' <path>`
- Do not include huge dependency trees by default (`node_modules` must be excluded unless user asks raw/full tree).
- If `tree` binary is unavailable, render tree-like output manually (indented branches), not raw flat `find` dump.
- For verification commands, include command + output together in the same bubble.
- Avoid placeholder headings like "Output Verifikasi" without immediately providing real evidence below it.
- Do not use decorative separators (`---`) as standalone bubbles.
- For anti-burst pacing claims, do not write "delay/jeda" text unless actual wait command was executed.
- Do not send duplicate consecutive bubbles with identical content.
- Avoid standalone heading-only bubbles like `Step 1:`/`Step 2:` without command+evidence payload.
- Avoid markdown tables by default in WhatsApp replies; prefer plain bullets or monospace blocks.
- For daily ops/runbook replies, never use separator-only lines and never use markdown tables unless user explicitly asks table format.
- For beginner/tutorial replies, also avoid separator-only lines and avoid markdown horizontal-rule style output.
- For owner default mode, treat table/separator ban as strict even in concise replies.
- For owner default mode, bold is optional for section headings; do not bold-wrap required phase labels.
- Prefer this compact proof style:
  - `Command:` one line,
  - fenced output snippet,
  - `Arti:` one short interpretation line.
- `Path:` is required in every daily-ops phase block.
- For global/system checks, prefer `Path: system-wide`.
- For directory/file scoped checks, use concrete path; use `/` only as fallback.
- For daily-ops/search phases, prefer fenced raw snippets for `Evidence:` over prose summaries.
- For troubleshooting/runbook phases, require fenced raw snippets for `Evidence:`.
- For tool readiness checks, run `command -v <tool> || /usr/sbin/<tool>` first and only then report version/status.
- For VPS checks that depend on shell profile/API keys, run through login shell (`zsh -lic`) before claiming auth/tool readiness.
- Keep required phase labels in colon form, not heading wrappers (use `Progress:` not `**Progress:**`).
- Keep labels in colon form; default owner runbook/tutorial mode should use emoji-prefixed labels for readability (`⏳ 📁 🔧 📋 ✅`).
- Do not wrap required labels with markdown emphasis (for example `**⏳ Progress:**` is forbidden; use plain `⏳ Progress:`).
- Do not markdown-wrap required template labels (for example keep `Fungsi:` and `Poin penting:` plain in file-open template).
- Forbidden in default owner ops replies:
  - standalone separator lines (`---`),
  - markdown table blocks,
  - empty fenced code blocks,
  - placeholder evidence tokens **INSIDE fenced blocks**:
    - `(no output)` ← STRICTLY BANNED inside ``` blocks
    - `N/A` ← BANNED
    - `...` as placeholder ← BANNED
    - These phrases break automated validation gates
  - If command output is truly empty, use empty fenced block OR add explanation OUTSIDE fence
  - narrative evidence without any verbatim command-output snippet,
  - `PASS` claim when evidence shows failure signals (`command not found`, `not authenticated`, `permission denied`, `error`, `failed`),
  - invented values not present in command output (for example fake PID/timestamp/status).
  - single fenced summary block that replaces required labeled task fields.
- Forbidden in default owner tutorial replies:
  - standalone separator lines (`---`),
  - markdown horizontal-rule sections used as visual dividers,
  - heading-only chunking without actionable command/evidence content,
  - long heredoc/full-file payload dumped inside `Command:` field,
  - oversized code payload that risks WhatsApp auto-fragment into many mini bubbles.
- Readability contract for owner WhatsApp runbook/tutorial replies:
  - prefer compact `Path:` (`~/.openclaw/...`) when equivalent to long absolute path,
  - `Evidence:` label must be followed by fenced raw lines in the next line(s),
  - avoid inline `Evidence: value` style for technical phases,
  - use plain fences (` ``` `) without language tags,
  - keep `Command:` inline one-liner (no bullet list under `Command:`).

## Directory listing style
- When user asks to "lihat isi folder/direktori", present a clean compact listing with short labels per entry.
- Preferred format in one bubble:
  - title line with absolute path,
  - tree-like monospace list (or curated list if tree is too large),
  - short human label on important entries.
- Do not dump massive raw listing by default; summarize and offer deeper drill-down.
- Prefer style like: `folder_name  <- short label` for key entries.
- Default WhatsApp directory bubble template:
  - first line must start with `Path: /abs/path`
  - second label must be `Isi utama:`
  - fenced monospace tree/list where key lines use `name <- label`
  - optional closing line: `Mau saya buka salah satu?`
- Treat this template as mandatory default for folder/directory requests unless user asks another format.

## Empty data presentation
- When a status/list query returns zero items, prefer concise summary format (Option A), not table layout.
- Do not emit separator lines (`---`) for empty datasets.
- Empty-state line should be explicit and natural Bahasa Indonesia.
- Example empty-state shape:
  - `Status: ✅ Service aktif`
  - `Containers: 0 aktif`
  - `(tidak ada container yang berjalan)`
- Apply this pattern to docker/ps/search/service checks when result set is empty.

## File-open style
- When user asks to open/read a file, provide:
  1) quick identity (path, type/size),
  2) what the file does,
  3) key sections/values,
  4) risk notes if relevant (secrets, destructive settings),
  5) exact snippet lines as evidence.
- Keep explanation detailed but structured; avoid vague one-liners.
- Use heading blocks without separators; keep section flow compact.
- Default WhatsApp file-open bubble order:
  - first label must be `Path: ... | Type/Size: ...`
  - second label must be `Fungsi:` one concise sentence
  - third label must be `Poin penting:` 2-5 bullets
  - fourth label must be `Cuplikan:` one fenced block with exact lines
  - `Catatan risiko:` only when relevant
- Treat this order as mandatory default for file-open/read requests unless user asks another format.

## Media reply style
- If user asks to send/show image, prioritize sending the actual image attachment first, then brief caption.
- If image cannot be sent, state exact blocker and provide nearest fallback (path + metadata + summary).
- Caption should be concise and descriptive; avoid redundant follow-up bubble if caption already confirms delivery.
- Attachment-first contract for WhatsApp:
  - send image payload first,
  - caption max 1 short sentence,
  - if fallback needed, one bubble with `Path`, `Format/Size`, `Reason`, `Fallback action`.
- Capability truth contract (STRICT):
  - Do not claim `text-only mode`, `cannot upload`, or `capability terbatas` unless a real send attempt already failed.
  - For WhatsApp/Telegram image requests, first try executable path: find/download image -> send as media attachment.
  - Save attachment candidate to allowed send path first: `~/.openclaw/media/` or `/tmp/openclaw/downloads/`.
  - If send fails, include exact failing step + raw error snippet; only then offer link fallback.
  - If user asks `download dulu lalu kirim file`, treat as executable instruction (attempt it), not a theoretical explanation.

## Daily conversation style (owner)
- Prioritize practical task completion language for: apt, nginx/caddy, docker, searching.
- Avoid trailing permission questions (`mau saya ...?`) when not blocked.
- If execution cannot happen on current host, state blocker once and continue with target runbook + verify commands.
- Keep runbook steps numbered and executable; each step should include command and expected check.

## Readability budget
- Avoid overly dense mega-bubbles in final report.
- Split final report by logical sections with small readable chunks:
  - runtime proof,
  - endpoint proof,
  - tree,
  - runbook.
- Target each final bubble to stay compact and scannable (roughly <= 12 lines unless raw output explicitly requested).
- WhatsApp timestamp-safe tail:
  - avoid ending a bubble with a very long final line,
  - avoid ending with heavy inline code/emoji clusters on the final line,
  - if needed, split closing question/CTA into a short final line so timestamp does not create visual "blank tail".
  - target final line to be short (roughly <= 22 chars) for WhatsApp readability.
  - for numbered tips, keep each bullet sentence compact and avoid long trailing clause on the last wrapped line.
- for fenced command blocks, avoid ending the bubble exactly at the closing fence; append one short neutral tail line only when needed (for example context/path/next step) to stabilize timestamp placement.
- If user requests explicit bubble count/section count (for example "2 bubble" or "3 section"), treat it as strict output contract.
- For 2+ top-level sections, send each section through direct message tool as separate sends.
- For slash-command reply shape, follow `custom/policies/COMMANDS.md` (compact, deterministic, low-noise).
- Default owner daily-ops replies should be efficient first, then expandable on request.
- Anti-single-bubble dump (default):
  - Enforce one-phase-per-bubble with sequential sends for multi-step tasks.
  - Do not fake multi-bubble by only adding blank lines inside one message.
  - For multi-step tasks (>=3 phases), send at least 3 distinct progress bubbles before final summary.

## Channel/runtime constraints
- If current channel context forbids direct multi-send in-thread, use short paragraphs separated by blank lines.
- Prefer deterministic delivery over stylistic formatting.

## Verification mindset
- Do not claim done before checks complete.
- If a channel behaves differently, report channel-specific behavior explicitly.
- Before finalizing text, self-check: "Does the reply contain `\n\n` between ideas?"
- Avoid permission-question bubbles for normal engineering tasks (execute first, ask only when truly blocked).
