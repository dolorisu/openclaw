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
- `Evidence:` lines must be verbatim from the latest tool output (except optional truncation with `...`).

## Exceptions
Use single bubble only when content must stay contiguous:
- code blocks
- stack traces
- dense command output
- structured tables that break if split
- explicit raw/full/verbatim output requested by user

## Evidence formatting
- If user asks for raw/full output: keep each raw block contiguous in a single bubble/code block.
- Non-negotiable: fenced code block must open and close in the same bubble.
- If user does not ask for raw output: send concise proof snippets (3-8 lines) and keep the rest summarized.
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

## Channel/runtime constraints
- If current channel context forbids direct multi-send in-thread, use short paragraphs separated by blank lines.
- Prefer deterministic delivery over stylistic formatting.

## Verification mindset
- Do not claim done before checks complete.
- If a channel behaves differently, report channel-specific behavior explicitly.
- Before finalizing text, self-check: "Does the reply contain `\n\n` between ideas?"
- Avoid permission-question bubbles for normal engineering tasks (execute first, ask only when truly blocked).
