# CHANNEL_GUIDE.md

Cross-channel message delivery policy.

## Defaults
- Conversational mode: one short sentence per bubble.
- Keep bubbles focused and readable.

## Atomic list mode
- Checklist/steps must be one bubble: heading + all items.
- Header ends with colon (e.g., `Checklist malam ini:`).
- Use plain list style (`1.` / `-`).
- Task-list markdown (`- [ ]`, `- [x]`) only when user explicitly asks todo/progress tracking.

## Progress-update style
- For interactive progress, use plain text labels only.
- Avoid markdown headings (`##`), tables, and separators.
- Keep each checkpoint concise to avoid burst splitting.

## Avoid
- No separator-only bubbles (`---`, `***`).
- No decorative bullets that break spacing.

## Single-bubble exceptions
Keep one bubble for contiguous content:
- code blocks
- stack traces
- dense command output
- structured tables
