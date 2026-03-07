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
- If user does not ask for raw output: send concise proof snippets (3-8 lines) and keep the rest summarized.
- For tree output, always use fenced code block.
- For verification commands, include command + output together in the same bubble.
- Avoid placeholder headings like "Output Verifikasi" without immediately providing real evidence below it.
- Do not use decorative separators (`---`) as standalone bubbles.
- For anti-burst pacing claims, do not write "delay/jeda" text unless actual wait command was executed.

## Channel/runtime constraints
- If current channel context forbids direct multi-send in-thread, use short paragraphs separated by blank lines.
- Prefer deterministic delivery over stylistic formatting.

## Verification mindset
- Do not claim done before checks complete.
- If a channel behaves differently, report channel-specific behavior explicitly.
- Before finalizing text, self-check: "Does the reply contain `\n\n` between ideas?"
