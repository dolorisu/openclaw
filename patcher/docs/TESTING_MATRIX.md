# Testing Matrix: Valid vs Misleading Methods

Purpose: prevent false conclusions when validating multi-bubble and progressive delivery behavior.

---

## Quick Rule

- Use chat-app prompts (WhatsApp/Telegram) for UX truth.
- Use `openclaw agent --deliver` for smoke checks only.

---

## Matrix

| Method | Use case | Trust level | Notes |
|---|---|---|---|
| Human prompt from WhatsApp app | Realtime progressive UX | High | Canonical for WhatsApp user experience |
| Human prompt from Telegram app | Realtime progressive UX | High | Canonical for Telegram user experience |
| Chat export from app | Delivery timing audit | High | Best for sender-receive timeline evidence |
| Session `.jsonl` timestamps | Backend sequencing evidence | Medium-High | Good supporting evidence, not final UX truth |
| `openclaw message send` with manual delay | Transport sanity check | Medium | Isolates channel send path from agent behavior |
| `openclaw agent --channel ... --deliver` | Functional smoke test | Medium-Low for UX timing | Can appear bursty; do not treat as final UX verdict |
| CLI stdout timing alone | Progressive UX validation | Low | Easily misleading |

---

## Why `openclaw agent` can mislead

- It runs through a CLI execution path that may not mirror live inbound-user pacing exactly.
- Progress bubbles can look delayed/batched even when real user-initiated prompts behave correctly.
- It is still useful to verify format, correctness, and patch presence.

---

## Standard Validation Flow (Recommended)

1. Apply patches and restart gateway.
2. Send `/reset` from the real chat app.
3. Trigger heavy multi-step task from the app (not CLI).
4. Observe arrival pattern directly in app.
5. Export chat and compare with session timestamps for audit.

Pass criteria:
- Progress bubbles arrive during execution, not only after completion.
- No multi-progress merge in a single bubble unless explicitly requested.
- Conversational text with `\n\n` appears as separate bubbles (WA/TG).

---

## Anti-Patterns (Do Not Use As Final Proof)

- Declaring failure only from `openclaw agent --deliver` burst appearance.
- Declaring success only from session timestamps without app-side confirmation.
- Using minute-only chat labels as sole timing evidence when second-level evidence exists.

---

## Recommended Test Prompts

- Progressive test: "Buat mini app 6 langkah, kirim progress per langkah saat selesai."
- Multi-bubble test: "Jelaskan X dalam 3 kalimat terpisah."

---

## Final Decision Rule

- If app-side user test and CLI test conflict, trust app-side user test.
- Use CLI/session evidence only to diagnose root cause, not to override observed user UX.
