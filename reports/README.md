# reports

Generated benchmark/smoke outputs for local validation.

- `BENCHMARK_REPORT.md` / `.json`
- `SMOKE_NATURAL_REPORT.md` / `.json`

These are operational artifacts and can be regenerated anytime.

Recommended gate before publishing a new quality claim:

```bash
bash ~/.openclaw/patcher/verify/wa-quality-regression.sh --to +6289669848875 --timeout 300
```

Keep only summarized pass/fail reports in git when needed; raw temporary captures can stay in `/tmp`.
