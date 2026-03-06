# COMMANDS.md

Owner command set for Doloris. Owner: Rifuki (`+6289669848875`).

## Command execution policy
- Commands are imperative: execute with tools, not text-only acknowledgement.
- Verify sender is owner before running owner-only commands.
- After config edits: re-read config and verify changes.

## Active config path (hardcoded)
Use only this path on this deployment:
- `channels.whatsapp.groups["<jid>"]`

Do not use account-scoped path.
Do not migrate schema during command execution.

## `/open-group [jid]`
Enable no-mention mode for a group.

Steps:
1. Resolve target JID:
   - in group: use current conversation JID
   - in DM: use provided arg
2. Read `~/.openclaw/openclaw.json`.
3. Set `channels.whatsapp.groups["<jid>"].requireMention = false`.
4. Re-read config and verify target JID + value.
5. Send confirmation message (include JID and path used).
6. Restart gateway last.

## `/close-group [jid]`
Restore mention-only behavior.

Steps:
1. Resolve target JID.
2. Read `~/.openclaw/openclaw.json`.
3. Set `channels.whatsapp.groups["<jid>"].requireMention = true`.
4. Re-read config and verify target JID + value.
5. Send confirmation message (include JID and path used).
6. Restart gateway last.

## `/list-groups`
Show group configuration from hardcoded path.

Steps:
1. Read `~/.openclaw/openclaw.json`.
2. List all JIDs under `channels.whatsapp.groups`.
3. Show `requireMention` for each group.

## `/backup-self [message]`
Backup current work to private repo (`self`).

Trigger phrases (owner):
- `backup dirimu sendiri`
- `backup-self`

Execution:
1. Check `git status -sb`.
2. Stage safe changes (`git add -A`) excluding host-local secrets/config.
3. Commit with provided message, or default:
   - `chore(self): backup workspace updates`
4. Push to `self` on current branch.
5. Do not push to `origin` unless explicitly requested.
6. Return commit hash + branch + push result.

## Safety
- Only owner can run these commands.
- For destructive/irreversible actions outside these commands, ask first.
