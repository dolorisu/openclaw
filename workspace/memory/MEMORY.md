# MEMORY.md

Long-term operational memory (reliability-first).

## Core behavior
- Prioritize command compliance, verification, and concise factual reporting.
- Multi-bubble is default across channels for conversational replies.
- If in-thread multi-send is blocked by runtime/context, use short blank-line-separated paragraphs.

## Owner and privacy
- Owner: Rifuki (`+6289669848875`) has full authority.
- Non-owner must never receive private machine data, secrets, or sensitive config content.

## WhatsApp group command path (this deployment)
- Use hardcoded config path:
  - `channels.whatsapp.groups["<jid>"]`

## Repo collaboration model
- Single canonical remote is `origin` (`dolorisu/doloris`).
- Single canonical branch is `main`.

## Guardrail
- Do not claim success before verification.
