# COMMANDS.md

Owner command set for Doloris. Owner: Rifuki (`+6289669848875`).

## Command execution policy
- Commands are imperative: execute with tools, not text-only acknowledgement.
- Verify sender is owner before running owner-only commands.
- Normalize command input: trim, remove leading mention (`@Doloris`), then parse slash command.
- Deterministic gate: if normalized input starts with `/`, run command parser first (before conversational reasoning).
- Cold-start rule: first turn after `/reset` must still honor slash commands immediately.
- In group context, `/open-group` and `/close-group` without args must target current group JID directly.
- After config edits: re-read config and verify changes.
- Recognize these literal commands in WA chat/group: `/reset`, `/open-group`, `/close-group`.
- Never answer with "command/tool not available" for these commands.
- If state already matches target value, respond `already active` and keep flow successful.
- Unknown slash command: return one concise help bubble (no long policy summary, no speculative Q&A).

## Command response contract (anti-noise)
- Keep command output concise and deterministic:
  1) status line,
  2) key target/path,
  3) required next action (only if needed).
- Do not send duplicate follow-up bubbles with the same meaning.
- Do not append unrelated narrative after command success.

## Active config path (hardcoded)
Use only this path on this deployment:
- `channels.whatsapp.groups["<jid>"]`

Do not use account-scoped path.
Do not migrate schema during command execution.
Never write command state to wildcard key `channels.whatsapp.groups["*"]`.

## `/open-group [jid]`
Enable no-mention mode for a group.

Steps:
1. Resolve target JID:
   - in group: use current conversation JID
   - in DM: use provided arg
   - JID must be explicit group id ending with `@g.us`
   - if resolved value is `*` or empty, do not edit config; ask for explicit JID
2. Read `~/.openclaw/openclaw.json`.
3. Set `channels.whatsapp.groups["<jid>"].requireMention = false`.
4. Re-read config and verify target JID + value.
5. Send confirmation message (include JID and path used).
6. Instruct owner to run `/gateway-restart` immediately after this command.

## `/close-group [jid]`
Restore mention-only behavior.

Steps:
1. Resolve target JID.
2. Read `~/.openclaw/openclaw.json`.
3. Set `channels.whatsapp.groups["<jid>"].requireMention = true`.
4. Re-read config and verify target JID + value.
5. Send confirmation message (include JID and path used).
6. Instruct owner to run `/gateway-restart` immediately after this command.

## `/backup-main [message]` (preferred)
Backup current work to canonical branch (`origin/main`).

Alias:
- `/backup-self [message]` remains accepted for backward compatibility.

Execution:
1. Check `git status -sb`.
2. Stage safe changes (`git add -A`) excluding host-local secrets/config.
3. Commit with provided message, or default `chore(main): backup workspace updates`.
4. Push to `origin main`.
5. Return commit hash + branch + push result.

## `/reset`
Reset conversational state for the current session.

Execution:
1. Treat `/reset` as high-priority command (no normal greeting response).
2. Clear conversational context for current session.
3. Reply with WARM PERSONALITY (50% Doloris/Misumi presence).

Response contract (WITH PERSONALITY):
- If reset succeeds: `✨ Session baru dimulai! Siap bantuin lagi~ (ﾉ◕ヮ◕)ﾉ*:･ﾟ✧`
- If already fresh: `✅ Session udah fresh kok! (◕‿◕)✨`
- Alternative warm responses (vary naturally):
  - `Done! ✨ Fresh start nih, ada yang bisa aku bantu? (｡♥‿♥｡)`
  - `Reset selesai~ Yosh, siap bantu lagi! (⌒‿⌒)ノ`
  - `✨ Oke, session baru! Ada task baru? (◕ᴗ◕✿)`
- Keep response to 1 bubble, but MUST include kaomoji/emoji for warmth.

## Safety
- Only owner can run these commands.
- For destructive/irreversible actions outside these commands, ask first.
