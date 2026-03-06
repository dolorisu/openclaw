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
- Before finalizing text, self-check: "Does the reply contain `\n\n` between ideas?"
