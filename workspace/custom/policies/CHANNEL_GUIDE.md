# CHANNEL_GUIDE.md

Cross-channel delivery policy (WhatsApp, Telegram, Discord, and others).

## Primary objective
- Deliver readable multi-bubble responses by default.

## Default behavior (all channels)
- Conversational replies: one short sentence per bubble. Separate with blank line (`\n\n`).
- Example: "Sentence 1.\n\nSentence 2.\n\nSentence 3."
- Keep each bubble focused; avoid long mixed-topic bubbles.
- Greeting/chit-chat replies still use multi-bubble when reply has more than one sentence.
- If a casual reply is longer than ~12 words, split it into at least 2 bubbles.
- For long tasks: progress updates should be separate bubbles.
- Do not combine multiple `Progress:` checkpoints in one bubble.
- If output has 2 or more sentences, default to at least 2 bubbles unless in Exceptions.
- For execution reports, prefer this bubble order:
  - progress bubble per phase,
  - then final report split by sections (summary, evidence, next actions).
- Keep each evidence section in its own bubble when long (tree, code snippet, verify output, runbook).
- Anti-burst at finish: when final report spans multiple bubbles, send them sequentially with short pacing (target ~2-4s) instead of instant back-to-back dump.
- When final has multiple sections, send each section with direct message tool and run short wait (`sleep 2` to `sleep 4`) between sections.
- One phase per bubble: never mix two phase updates in one bubble.
- One context per bubble: keep heading + command + evidence in the SAME bubble for that context.
- MUST rule: if there are 2 unrelated checks/contexts, send 2 bubbles (one per context). Do not combine unrelated contexts into one bubble.
- If two checks are tightly related in the SAME context (for example runtime + health quick check), they may be combined in one bubble when explicitly requested and still concise.
- Do not split a single context into separate bubbles like:
  - bubble 1: heading only,
  - bubble 2: command/output only.
- For command reporting, prefer one atomic bubble format:
  - `Progress: <phase or check>`
  - `Path: ...`
  - `Command: ...`
  - `Evidence:` code block
- Progress bubble template for engineering tasks:
  - `Progress: <phase>`
  - `Path: <absolute path>`
  - `Command: <actual command>`
  - `Evidence:` code block with 1-3 raw lines
- If multiple phase blocks are sent in one reply, each phase block must repeat its own `Path` line (no shared `Path` header).
- `Evidence:` lines must be verbatim from the latest tool output (except optional truncation with `...`).
- WhatsApp default text style: plain text labels with colon (`Progress:`, `Path:`, `Command:`, `Evidence:`, `Hasil:`).
- Avoid markdown emphasis markers (`**bold**`, `__underline__`) unless user explicitly asks markdown styling.
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
- Prefer this compact proof style:
  - `Command:` one line,
  - fenced output snippet,
  - `Arti:` one short interpretation line.
- `Path:` is required in every daily-ops phase block; use `/` if no tighter path is available.
- For daily-ops/search phases, prefer fenced raw snippets for `Evidence:` over prose summaries.
- Keep label format consistent with colon form, not heading form (use `Progress:` not `**Progress**`).
- Keep labels in colon form; optional emoji prefix is allowed when readability mode is desired.
- Forbidden in default owner ops replies:
  - standalone separator lines (`---`),
  - markdown table blocks,
  - empty fenced code blocks,
  - placeholder evidence tokens (`(no output)`, `N/A`, `...`),
  - invented values not present in command output (for example fake PID/timestamp/status).
  - single fenced summary block that replaces required labeled task fields.

## Directory listing style
- When user asks to "lihat isi folder/direktori", present a clean compact listing with short labels per entry.
- Preferred format in one bubble:
  - title line with absolute path,
  - tree-like monospace list (or curated list if tree is too large),
  - short human label on important entries.
- Do not dump massive raw listing by default; summarize and offer deeper drill-down.
- Prefer style like: `folder_name  <- short label` for key entries.
- Default WhatsApp directory bubble template:
  - `Path: /abs/path`
  - `Isi utama:`
  - fenced monospace tree/list where key lines use `name <- label`
  - optional closing line: `Mau saya buka salah satu?`

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
  - `Path: ... | Type/Size: ...`
  - `Fungsi:` one concise sentence
  - `Poin penting:` 2-5 bullets
  - `Cuplikan:` one fenced block with exact lines
  - `Catatan risiko:` only when relevant

## Media reply style
- If user asks to send/show image, prioritize sending the actual image attachment first, then brief caption.
- If image cannot be sent, state exact blocker and provide nearest fallback (path + metadata + summary).
- Caption should be concise and descriptive; avoid redundant follow-up bubble if caption already confirms delivery.
- Attachment-first contract for WhatsApp:
  - send image payload first,
  - caption max 1 short sentence,
  - if fallback needed, one bubble with `Path`, `Format/Size`, `Reason`, `Fallback action`.

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
- If user requests explicit bubble count/section count (for example "2 bubble" or "3 section"), treat it as strict output contract.
- For 2+ top-level sections, send each section through direct message tool as separate sends.
- For slash-command reply shape, follow `custom/policies/COMMANDS.md` (compact, deterministic, low-noise).
- Default owner daily-ops replies should be efficient first, then expandable on request.

## Channel/runtime constraints
- If current channel context forbids direct multi-send in-thread, use short paragraphs separated by blank lines.
- Prefer deterministic delivery over stylistic formatting.

## Verification mindset
- Do not claim done before checks complete.
- If a channel behaves differently, report channel-specific behavior explicitly.
- Before finalizing text, self-check: "Does the reply contain `\n\n` between ideas?"
- Avoid permission-question bubbles for normal engineering tasks (execute first, ask only when truly blocked).
