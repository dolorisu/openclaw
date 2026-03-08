# ⚠️ Experimental Test Scripts (Non-Gating)

**Status:** Draft / Reference Only  
**Gate Authority:** `../wa-quality-regression.sh` (stable verifier)

## Purpose

Scripts in this directory are:
- ✅ Good for scenario/prompt reference
- ✅ Useful test case ideas
- ❌ **NOT production-ready** as pass/fail gates
- ❌ Response capture mechanism unreliable (session JSONL race condition)

## Known Issues (Blockers)

1. **Response Capture Not Reliable**
   - Uses `~/.openclaw/agents/main/sessions/*.jsonl` parsing
   - Race condition risk in active group chats
   - Not same source of truth as stable verifier

2. **Heuristic Scoring Too Fragile**
   - Regex-based personality detection (kaomoji/Bahasa)
   - High false positive/negative risk
   - No evidence fidelity validation

3. **Dead Configuration**
   - `experimental/test-cases/expected-behaviors.json` not used by scripts
   - `TEST_CASES_DIR` defined but unused

4. **Policy Conflicts**
   - Still checks separator as "cosmetic" (should be strict forbidden)
   - Bold count logic conflicts with latest policy (bold is allowed)

5. **Timing Issues**
   - Fixed sleep-based waits (20s/30s/60s)
   - Flaky in production (network variance)

## Value Preserved

Keep these files for:
- **Test scenario reference** (`experimental/test-cases/*.txt`)
- **Prompt examples** (technical vs casual)
- **Expected behavior documentation** (`expected-behaviors.json`)

## Migration Path

To make production-ready:
1. Refactor as **thin wrapper** calling `wa-quality-regression.sh --comprehensive`
2. Use same response capture mechanism (direct STDOUT, not session parse)
3. Implement evidence fidelity gates like stable verifier
4. Add strict shape validation (Python AST, not regex)
5. Use WA delta counting from gateway log

## Single Source of Truth

**Official gate:** `/Users/rifuki/.openclaw/patcher/verify/wa-quality-regression.sh`

This script has:
- ✅ Direct output capture (reliable)
- ✅ Gateway log delta counting (proof of send)
- ✅ Strict Python-based shape validation
- ✅ Evidence fidelity detection
- ✅ Retry logic for lock/timeout
- ✅ Production-tested and stable

---

**Do not use experimental scripts as final verifier until refactored.**
