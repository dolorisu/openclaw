# CHANNEL_GUIDE.md

Cross-channel delivery policy (WhatsApp, Telegram, Discord, and others).

## Primary objective
- Deliver readable multi-bubble responses by default.

## Default behavior (all channels)
- Conversational replies: one short sentence per bubble.
- Keep each bubble focused; avoid long mixed-topic bubbles.
- For long tasks: progress updates should be separate bubbles.

## List block exception (important)
- If response includes checklist/numbered steps, keep the bullet/numbered list in ONE bubble block with its heading.
- Do not split heading and list into separate bubbles.
- Format list block as:
  - `Heading:` then list items on next lines (single newline, not blank-line split).
- Example:
  - `Checklist malam ini:\n- item 1\n- item 2\n- item 3`

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
