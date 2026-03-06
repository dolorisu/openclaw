# CHANNEL_GUIDE.md

Cross-channel delivery policy (WhatsApp, Telegram, Discord, and others).

## Primary objective
- Deliver readable multi-bubble responses by default.

## Default behavior (all channels)
- Conversational replies: one short sentence per bubble.
- Keep each bubble focused; avoid long mixed-topic bubbles.
- For long tasks: progress updates should be separate bubbles.

## List block exception (important)
- Checklist/list responses are ATOMIC blocks.
- Keep heading + full list in ONE bubble.
- Use single newlines between lines inside that bubble.
- Do not split heading/list items into separate bubbles.

## List style (visual best-practice)
- Header must end with colon: `Checklist malam ini:` / `Prioritas besok:`
- Use plain ASCII numbering or hyphen bullets only:
  - `1. ...` `2. ...` `3. ...`
  - or `- ...`
- Do not use markdown task-list markers (`- [ ]`) in chat output.
- Do not use decorative Unicode bullets that produce odd spacing (`•\u2060` artifacts).
- Keep list concise: 3-5 items max per block.

## Forbidden formatting artifacts
- Never send standalone separator bubbles like `---` or `***`.
- Avoid markdown horizontal rules in chat delivery.

## Exceptions
Use single bubble only when content must stay contiguous:
- code blocks
- stack traces
- dense command output
- structured tables that break if split

## Channel/runtime constraints
- If current channel context forbids direct multi-send in-thread, use short paragraphs separated by blank lines.
- Prefer deterministic delivery over stylistic formatting.

## Verification mindset
- Do not claim done before checks complete.
- If a channel behaves differently, report channel-specific behavior explicitly.
