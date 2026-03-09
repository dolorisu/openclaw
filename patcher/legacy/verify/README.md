# OpenClaw WhatsApp MEDIUM Personality Test Suite

Comprehensive automated testing for MEDIUM personality implementation and format compliance.

## 📋 Test Coverage

### Suite 1: Adaptive Personality Tests (`personality-adaptive-test.sh`)
Tests the core adaptive personality behavior:
- ✅ Technical prompts → 0-10% personality (minimal, functional)
- ✅ Casual prompts → 40-60% personality (kaomoji, natural Bahasa)
- ✅ Format compliance (no markdown tables, bold allowed)
- ✅ Context switching (technical → casual → technical)
- ✅ Error handling consistency

**Tests:** 5 | **Estimated time:** ~3-4 minutes

### Suite 2: Edge Case & Stability Tests (`edge-case-stability-test.sh`)
Tests edge cases and stability scenarios:
- ✅ Empty data handling (Option A format preference)
- ✅ Multi-tool verification workflows
- ✅ Multi-bubble behavior in group chats
- ✅ Evidence integrity (verbatim command output)
- ✅ Special characters handling
- ✅ Timeout behavior for long commands

**Tests:** 6 | **Estimated time:** ~4-5 minutes

## 🚀 Quick Start

### Prerequisites
```bash
# Ensure OpenClaw CLI is installed and configured
openclaw --version

# SSH to VPS (recommended environment)
ssh rifuki-amazon-id-ubuntu24-2c2g

# Navigate to test directory
cd ~/.openclaw/patcher/verify
```

### Run All Tests (Recommended)
```bash
# Full test suite on GROUP chat (safest, avoids DM ban risk)
./run-all-tests.sh --to 120363424987356245@g.us

# With verbose output for debugging
./run-all-tests.sh --to 120363424987356245@g.us --verbose

# Quick mode (skip long-running tests)
./run-all-tests.sh --to 120363424987356245@g.us --quick
```

### Run Individual Test Suites
```bash
# Only adaptive personality tests
./personality-adaptive-test.sh --to 120363424987356245@g.us --verbose

# Only edge case tests
./edge-case-stability-test.sh --to 120363424987356245@g.us --verbose
```

## 📊 Expected Results

### Success Criteria
```
══════════════════════════════════════════════════════════
  FINAL TEST SUMMARY
══════════════════════════════════════════════════════════
Test suites run:    2
Suites passed:      2
Suites failed:      0
══════════════════════════════════════════════════════════

[INFO] 🎉 ALL TEST SUITES PASSED!
[INFO] MEDIUM personality implementation: STABLE ✓
```

### Failure Investigation
If tests fail:
1. **Rerun with `--verbose`** to see detailed output
2. **Check session logs:** `~/.openclaw/agents/main/sessions/*.jsonl`
3. **Verify gateway status:** `systemctl status openclaw-gateway`
4. **Review test assertions:** `experimental/test-cases/expected-behaviors.json`

## 📁 File Structure

```
~/.openclaw/patcher/verify/
├── experimental/
│   ├── run-all-tests.sh                # Master test runner (draft/non-gating)
│   ├── personality-adaptive-test.sh    # Suite 1: Adaptive personality (draft)
│   ├── edge-case-stability-test.sh     # Suite 2: Edge cases & stability (draft)
│   └── test-cases/
│       ├── technical-ops.txt           # Technical prompt samples
│       ├── casual-chat.txt             # Casual prompt samples
│       └── expected-behaviors.json     # Test assertions & thresholds
└── README.md                           # This file
```

## 🔬 Testing Protocol

### CRITICAL: Reset Before Each Test
**MANDATORY:** Send `/reset` and wait 5 seconds before each test prompt to ensure clean session state.

This is **automatically handled** by test scripts via `reset_session()` function.

### Recommended Environment
- **Target:** GROUP chat (`120363424987356245@g.us`) instead of DM
- **Reason:** Avoids WhatsApp ban risk from too many DM messages
- **Location:** VPS (`rifuki-amazon-id-ubuntu24-2c2g`)
- **VPS Benefits:**
  - Closer to production environment
  - Persistent gateway connection
  - Real session logs available

### Response Time Expectations
| Test Type | Expected Response Time |
|-----------|------------------------|
| Simple command | < 5 seconds |
| Multi-tool chain | < 20 seconds |
| Complex explanation | < 30 seconds |

## 🎯 Test Assertions

### Adaptive Personality Markers

**Technical Mode (0-10% personality):**
- Kaomoji: 0-1 occurrences
- Natural Bahasa (nih/dong/aja): 0-1 occurrences
- Pauses (...): 0-1 occurrences
- Bold usage: minimal (section headers only)
- Tone: functional, concise, professional

**Casual Mode (40-60% personality):**
- Kaomoji: 2-4 occurrences
- Natural Bahasa: 3-5 occurrences
- Pauses (...): 2-3 occurrences
- Bold usage: moderate (emphasis)
- Tone: warm, friendly, natural Bahasa

### Format Compliance

| Element | Status | Notes |
|---------|--------|-------|
| Markdown tables (`\|col\|`) | ❌ FORBIDDEN | Breaks WhatsApp rendering |
| Markdown bold (`**text**`) | ✅ ALLOWED | Renders correctly (confirmed by screenshot) |
| Separator lines (`---`) | ⚠️ DISCOURAGED | Cosmetic issue, prefer Option A for empty data |
| Functional emojis (✓ ❌ ⚠️) | ✅ ALLOWED | Improves readability |
| Code blocks | ✅ ALLOWED | Monospace rendering works |

### Empty Data Format Preference

**Option A (Preferred):**
```
Status Docker:
Tidak ada container yang running saat ini ✓
```

**Option B (Avoid):**
```
Status Docker:
---
(no data)
---
```

## 🐛 Debugging Failed Tests

### Check Test Logs
```bash
# View latest test run output
tail -f ~/.openclaw/patcher/verify/test-output.log

# Search for failed assertions
grep "FAIL" ~/.openclaw/patcher/verify/test-output.log
```

### Check Session Logs
```bash
# Find latest session
ls -lt ~/.openclaw/agents/main/sessions/*.jsonl | head -n 5

# View session content
tail -n 100 ~/.openclaw/agents/main/sessions/<session-id>.jsonl | jq .
```

### Manual Testing
```bash
# Send test prompt manually
openclaw agent --channel whatsapp \
  --to 120363424987356245@g.us \
  --message "cek docker ps" \
  --deliver

# Reset session
openclaw agent --channel whatsapp \
  --to 120363424987356245@g.us \
  --message "/reset" \
  --deliver
```

## 📈 Regression Testing

Run this test suite after:
- ✅ Any changes to `SOUL.md` (personality config)
- ✅ Updates to `CHANNEL_GUIDE.md` (format policies)
- ✅ Modifications to agent prompts or system instructions
- ✅ Model version changes (e.g., GPT-5.3 → GPT-6)
- ✅ Before production deployments

## 🎓 Test Maintenance

### Adding New Test Cases

**1. Add to test case files:**
```bash
# Technical prompts
echo "your new technical prompt" >> experimental/test-cases/technical-ops.txt

# Casual prompts
echo "your new casual prompt" >> experimental/test-cases/casual-chat.txt
```

**2. Add test function in script:**
```bash
test_your_new_scenario() {
    log_test "Your Test Description"
    ((TESTS_RUN++))
    
    reset_session
    send_and_wait "your test prompt"
    
    local response
    response=$(get_latest_response)
    
    # Your assertions here
    if [[ condition ]]; then
        log_info "✅ PASS - Test passed"
        ((TESTS_PASSED++))
    else
        log_error "❌ FAIL - Test failed"
        ((TESTS_FAILED++))
    fi
}
```

**3. Call in main():**
```bash
main() {
    test_your_new_scenario || true
    # ... other tests
}
```

## 📝 Change Log

### 2026-03-08 - Initial Test Suite
- Created comprehensive test automation framework
- Implemented adaptive personality testing (5 tests)
- Added edge case and stability tests (6 tests)
- Documented expected behaviors and assertions
- Validated on VPS with group chat target

## 🔗 Related Documentation

- **Personality Config:** `~/.openclaw/workspace/SOUL.md`
- **Format Policies:** `~/.openclaw/workspace/custom/policies/CHANNEL_GUIDE.md`
- **Workflow Guide:** `~/.openclaw/workspace/custom/policies/WORKFLOW.md`
- **Identity:** `~/.openclaw/workspace/IDENTITY.md`

## ⚠️ Important Notes

1. **Bold is ALLOWED:** User confirmed via screenshot that `**bold**` renders correctly in WhatsApp. The previous "bold ban" policy was overly strict.

2. **Separator lines:** Minor cosmetic issue, not critical violation. Prefer concise format (Option A) for empty data instead of tables with separators.

3. **Multi-bubble patch:** Works in GROUP chat (verified with 3-bubble blockchain explanation). Not applicable to DMs.

4. **Test target preference:** Always use GROUP chat for testing to avoid DM ban risk.

5. **Evidence integrity:** Tests verify verbatim command output is preserved (no fabrication).

## 📧 Support

Issues or questions? Check:
- Session logs: `~/.openclaw/agents/main/sessions/`
- Gateway logs: `journalctl -u openclaw-gateway -n 100`
- Test output: Rerun with `--verbose` flag
