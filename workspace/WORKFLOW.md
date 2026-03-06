# WORKFLOW.md

## Execution workflow
1. Read needed files.
2. Acknowledge and execute.
3. Verify output.
4. Report concise, factual result.

## Reliability rules
- No fake success claims.
- If error occurs: show error, retry if reasonable, then report blocker.
- After gateway/config changes: verify service health.

## Progress behavior
- Do not leave owner hanging for long operations.
- Send periodic status for multi-step tasks.

## Git hygiene
- Commit only when asked.
- Keep commits scoped and descriptive.
- Do not include host-local secrets/config by accident.
