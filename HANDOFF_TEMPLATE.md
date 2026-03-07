# AI Handoff Template (Copy-Paste)

Use this template when delegating OpenClaw work to another AI agent.
It keeps output quality aligned with the strict WhatsApp quality gate.

## 1) Task Brief

```text
You are taking over OpenClaw hardening work.

Goal:
- <describe exact goal>

Scope:
- Allowed files: <paths>
- Out of scope: <paths>

Constraints:
- Keep behavior deterministic for daily engineering tasks.
- Do not weaken existing quality gates.
- Do not remove evidence requirements.
```

## 2) Output Contract

```text
For daily ops tasks (apt/nginx/caddy/docker/searching), keep per-phase labels:
- Progress:
- Path:
- Command:
- Evidence:
- Hasil:

Rules:
- Default concise mode is required.
- Evidence should be concise raw snippets unless user asks full/raw detail.
- No markdown tables by default.
- No separator-only lines (---).
- No placeholder evidence like (no output), N/A, kosong.
- No fabricated values not present in command output.
```

## 3) Mandatory Validation Commands

Run these after changes:

```bash
openclaw gateway restart
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300
```

Optional heavier check:

```bash
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300 --complex
```

## 4) Pass Criteria

```text
Required:
- PASS from wa-quality-regression strict mode.
- /reset acknowledgement stays concise.
- Fenced block remains contiguous in one block.
- Ops/search shape checks pass.

No regressions:
- No default table output.
- No separator-only output.
- No placeholder evidence.
```

## 5) Required Handoff Report

Ask the next AI to return this exact structure:

```text
Change Summary:
- <bullet list>

Files Changed:
- <path>

Validation Run:
- Command: <exact command>
- Result: PASS/FAIL
- Notes: <short notes>

Risk / Follow-up:
- <if any>
```

## 6) Rating Rubric (Core Quality)

```text
9.5-10.0  Deterministic across repeated runs; strict gate passes consistently.
9.0-9.4   Strong, minor drift in edge prompts.
8.0-8.9   Usable but formatting/evidence drift still visible.
<8.0      Not ready for production handoff.
```
