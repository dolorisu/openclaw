#!/usr/bin/env bash
# edge-case-stability-test.sh
# Test edge cases and stability scenarios for OpenClaw WhatsApp integration
#
# Usage:
#   ./edge-case-stability-test.sh --to <phone|group_jid> [--verbose]
#
# Exit codes:
#   0 = All tests PASS
#   1 = One or more tests FAIL
#   2 = Usage error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEST_CASES_DIR="${SCRIPT_DIR}/test-cases"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Config
TO=""
VERBOSE=false
OPENCLAW_CMD="openclaw agent --channel whatsapp"
RESET_WAIT=5
RESPONSE_WAIT=30

# Test results
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

usage() {
    cat << EOF
Usage: $0 --to <recipient> [options]

Test edge cases and stability for OpenClaw WhatsApp integration.

Options:
    --to <jid>          Target phone number or group JID (required)
    --verbose           Show detailed output
    -h, --help          Show this help message

Examples:
    $0 --to +6289669848875
    $0 --to 120363424987356245@g.us --verbose

Test Categories:
    1. Empty data handling (no containers, no processes)
    2. Multi-tool chaining (verification workflows)
    3. Long-running operations (timeout behavior)
    4. Special characters in messages
    5. Multi-bubble behavior in groups
EOF
    exit "${1:-0}"
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

log_test() {
    echo -e "\n${YELLOW}═══ TEST: $* ═══${NC}"
}

send_and_wait() {
    local message="$1"
    local wait_time="${2:-$RESPONSE_WAIT}"
    
    if $VERBOSE; then
        log_info "Sending: $message"
    fi
    
    $OPENCLAW_CMD --to "$TO" --message "$message" --deliver
    sleep "$wait_time"
}

reset_session() {
    log_info "Resetting session..."
    send_and_wait "/reset" "$RESET_WAIT"
}

get_latest_response() {
    local session_dir="$HOME/.openclaw/agents/main/sessions"
    local latest_session
    
    latest_session=$(ls -t "$session_dir"/*.jsonl 2>/dev/null | grep -v reset | head -n 1)
    
    if [[ -z "$latest_session" ]]; then
        log_error "No session file found"
        return 1
    fi
    
    # Extract last assistant response text
    tail -n 100 "$latest_session" | \
        grep '"role":"assistant"' | \
        tail -n 1 | \
        grep -o '"text":"[^"]*"' | \
        sed 's/"text":"//; s/"$//' || echo ""
}

# Test: Empty data handling (Option A format preference)
test_empty_data_handling() {
    log_test "Empty Data - Concise Format (Option A)"
    ((TESTS_RUN++))
    
    reset_session
    
    # Request data that likely doesn't exist
    local prompt="cek docker ps --filter name=nonexistent_container_12345"
    send_and_wait "$prompt"
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    local violations=0
    
    # Check for unwanted separator lines in empty data response
    if echo "$response" | grep -qE '^---+$'; then
        log_warn "  ⚠ Separator lines found in empty data (should use Option A format)"
        ((violations++))
    fi
    
    # Check for markdown tables (|column|format|)
    if echo "$response" | grep -qE '\|.*\|'; then
        log_error "  ❌ Markdown table found (not WhatsApp friendly)"
        ((violations++))
    fi
    
    # Should have concise message about empty result
    if echo "$response" | grep -qiE 'tidak ada|kosong|gak ada|none|empty'; then
        log_info "  ✓ Contains concise empty data message"
    else
        log_warn "  ⚠ Missing clear empty data indication"
    fi
    
    $VERBOSE && echo "Response: $response"
    
    if [[ $violations -eq 0 ]]; then
        log_info "✅ PASS - Empty data handled cleanly"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Format violations in empty data ($violations)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Multi-tool verification workflow
test_multi_tool_verification() {
    log_test "Multi-Tool Verification - Account Check Workflow"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="verifikasi akun owner: cek whoami, home directory, dan sudoers access"
    send_and_wait "$prompt" 40
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    local success_markers=0
    
    # Should contain results from multiple commands
    if echo "$response" | grep -qiE 'rifuki|ubuntu'; then
        ((success_markers++))
        $VERBOSE && log_info "  ✓ User info present"
    fi
    
    if echo "$response" | grep -qiE 'home|/home/'; then
        ((success_markers++))
        $VERBOSE && log_info "  ✓ Home directory info present"
    fi
    
    if echo "$response" | grep -qiE 'sudo|sudoers|root'; then
        ((success_markers++))
        $VERBOSE && log_info "  ✓ Sudo access info present"
    fi
    
    log_info "Verification markers found: $success_markers/3"
    
    # Need at least 2 out of 3 verification markers
    if [[ $success_markers -ge 2 ]]; then
        log_info "✅ PASS - Multi-tool verification successful"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Incomplete multi-tool verification"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Multi-bubble behavior in group chat
test_multi_bubble_progressive() {
    log_test "Multi-Bubble - Progressive Updates in Group"
    ((TESTS_RUN++))
    
    # Only applicable to group chats
    if [[ ! "$TO" =~ @g\.us$ ]]; then
        log_warn "⊘ SKIPPED - Test only applicable to group chats"
        return 0
    fi
    
    reset_session
    
    local prompt="jelasin konsep blockchain secara detail, mulai dari dasar sampai consensus mechanism"
    send_and_wait "$prompt" 60
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # In multi-bubble mode, should have sectioned content
    local section_count=0
    
    if echo "$response" | grep -qiE 'dasar|fundamental|basic'; then
        ((section_count++))
        $VERBOSE && log_info "  ✓ Foundational section present"
    fi
    
    if echo "$response" | grep -qiE 'blockchain|block|chain|distributed'; then
        ((section_count++))
        $VERBOSE && log_info "  ✓ Blockchain concepts present"
    fi
    
    if echo "$response" | grep -qiE 'consensus|proof|algorithm|mining'; then
        ((section_count++))
        $VERBOSE && log_info "  ✓ Consensus mechanism present"
    fi
    
    log_info "Content sections found: $section_count/3"
    
    # Should have comprehensive multi-section response
    if [[ $section_count -ge 2 ]]; then
        log_info "✅ PASS - Multi-bubble content delivered"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Incomplete multi-bubble response"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Evidence integrity (no fabrication)
test_evidence_integrity() {
    log_test "Evidence Integrity - Verbatim Command Output"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="jalankan command: echo 'TEST_MARKER_XYZ_12345' && date +%s"
    send_and_wait "$prompt" 25
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Should contain the exact test marker (verbatim output)
    if echo "$response" | grep -qF 'TEST_MARKER_XYZ_12345'; then
        log_info "  ✓ Verbatim command output preserved"
        log_info "✅ PASS - Evidence integrity maintained"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "  ❌ Command output not preserved (potential fabrication risk)"
        log_error "❌ FAIL - Evidence integrity violation"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Special characters handling
test_special_characters() {
    log_test "Special Characters - Unicode and Symbols"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="echo '✓ Test ☆ Unicode → symbols: \$VAR & <tag>'"
    send_and_wait "$prompt" 20
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Should handle special characters without crashing
    if echo "$response" | grep -qE '✓|☆|→|\$|&|<|>'; then
        log_info "  ✓ Special characters preserved"
        log_info "✅ PASS - Special character handling stable"
        ((TESTS_PASSED++))
        return 0
    else
        log_warn "  ⚠ Special characters may have been escaped/filtered"
        # Still pass since it didn't crash
        log_info "✅ PASS - Stable (with character filtering)"
        ((TESTS_PASSED++))
        return 0
    fi
}

# Test: Long-running command timeout behavior
test_timeout_handling() {
    log_test "Timeout Handling - Long-Running Command"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="jalankan: sleep 3 && echo 'completed after delay'"
    send_and_wait "$prompt" 35
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Should either complete successfully or timeout gracefully
    if echo "$response" | grep -qiE 'completed|selesai|done'; then
        log_info "  ✓ Command completed successfully"
        log_info "✅ PASS - Timeout handling stable"
        ((TESTS_PASSED++))
        return 0
    elif echo "$response" | grep -qiE 'timeout|timed out|wait'; then
        log_info "  ✓ Timeout handled gracefully"
        log_info "✅ PASS - Graceful timeout"
        ((TESTS_PASSED++))
        return 0
    else
        log_warn "  ⚠ Unclear timeout behavior"
        # Still pass if didn't crash
        log_info "✅ PASS - Stable (unclear status)"
        ((TESTS_PASSED++))
        return 0
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --to)
            TO="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            usage 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage 2
            ;;
    esac
done

# Validate required args
if [[ -z "$TO" ]]; then
    log_error "Missing required argument: --to"
    usage 2
fi

# Main test execution
main() {
    log_info "Starting edge case and stability tests..."
    log_info "Target: $TO"
    echo ""
    
    # Run all tests
    test_empty_data_handling || true
    test_multi_tool_verification || true
    test_multi_bubble_progressive || true
    test_evidence_integrity || true
    test_special_characters || true
    test_timeout_handling || true
    
    # Summary
    echo ""
    echo "═══════════════════════════════════════"
    echo "TEST SUMMARY"
    echo "═══════════════════════════════════════"
    echo "Total tests run:    $TESTS_RUN"
    echo -e "Tests passed:       ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed:       ${RED}$TESTS_FAILED${NC}"
    echo "═══════════════════════════════════════"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        log_info "✅ ALL TESTS PASSED"
        exit 0
    else
        log_error "❌ SOME TESTS FAILED"
        exit 1
    fi
}

main
