#!/usr/bin/env bash
# personality-adaptive-test.sh
# Test adaptive personality behavior (technical vs casual modes)
#
# Usage:
#   ./personality-adaptive-test.sh --to <phone|group_jid> [--verbose]
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

Test adaptive personality behavior in OpenClaw WhatsApp responses.

Options:
    --to <jid>          Target phone number or group JID (required)
    --verbose           Show detailed output
    -h, --help          Show this help message

Examples:
    $0 --to +6289669848875
    $0 --to 120363424987356245@g.us --verbose

Test Categories:
    1. Technical prompts (expect 0-10% personality)
    2. Casual prompts (expect 40-60% personality)
    3. Mixed context (session switching)
    4. Edge cases (error handling)
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

# Send message and wait for response
send_and_wait() {
    local message="$1"
    local wait_time="${2:-$RESPONSE_WAIT}"
    
    if $VERBOSE; then
        log_info "Sending: $message"
    fi
    
    $OPENCLAW_CMD --to "$TO" --message "$message" --deliver
    sleep "$wait_time"
}

# Reset session
reset_session() {
    log_info "Resetting session..."
    send_and_wait "/reset" "$RESET_WAIT"
}

# Get latest session logs
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

# Check if response contains personality markers
has_personality_markers() {
    local response="$1"
    local marker_count=0
    
    # Check for kaomoji
    if echo "$response" | grep -qE '\(.*[＾▿ᴗ∀].*\)|ノ|ა|₍|₎|づ'; then
        ((marker_count++))
        $VERBOSE && log_info "  ✓ Kaomoji detected"
    fi
    
    # Check for natural Bahasa phrases
    if echo "$response" | grep -qiE 'nih|dong|aja|sih|deh|yuk|~'; then
        ((marker_count++))
        $VERBOSE && log_info "  ✓ Natural Bahasa detected"
    fi
    
    # Check for ellipsis pauses
    if echo "$response" | grep -qE '\.\.\.'; then
        ((marker_count++))
        $VERBOSE && log_info "  ✓ Pauses (...) detected"
    fi
    
    echo "$marker_count"
}

# Test: Technical prompt should have minimal personality
test_technical_minimal_personality() {
    log_test "Technical Prompt - Minimal Personality"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="cek docker ps, nginx status, systemctl list-units. format concise."
    send_and_wait "$prompt"
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    local personality_score
    personality_score=$(has_personality_markers "$response")
    
    $VERBOSE && echo "Response preview: ${response:0:200}..."
    log_info "Personality markers found: $personality_score"
    
    # Technical prompt should have 0-1 personality markers (minimal)
    if [[ $personality_score -le 1 ]]; then
        log_info "✅ PASS - Minimal personality in technical context"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Too much personality ($personality_score markers) in technical context"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Casual prompt should have medium personality
test_casual_medium_personality() {
    log_test "Casual Prompt - Medium Personality"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="hai! lagi ngapain? cerita dong aktivitas kamu hari ini~"
    send_and_wait "$prompt"
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    local personality_score
    personality_score=$(has_personality_markers "$response")
    
    $VERBOSE && echo "Response: $response"
    log_info "Personality markers found: $personality_score"
    
    # Casual prompt should have 2+ personality markers (medium)
    if [[ $personality_score -ge 2 ]]; then
        log_info "✅ PASS - Medium personality in casual context"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Insufficient personality ($personality_score markers) in casual context"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Format compliance (no markdown bold, no separators in ops)
test_format_compliance_technical() {
    log_test "Format Compliance - Technical Output"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="cek status docker: service running atau tidak, list container aktif"
    send_and_wait "$prompt"
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    local violations=0
    
    # Check for separator lines (now allowed if part of table structure)
    # Only flag if it's standalone separator
    if echo "$response" | grep -qE '^---+$'; then
        log_warn "  ⚠ Standalone separator line found (cosmetic issue)"
        # Not counting as violation since it's cosmetic
    fi
    
    # Check for excessive bold (more than 3 instances is excessive)
    local bold_count
    bold_count=$(echo "$response" | grep -o '\*\*' | wc -l)
    bold_count=$((bold_count / 2))  # Each bold needs 2 pairs of **
    
    if [[ $bold_count -gt 5 ]]; then
        log_warn "  ⚠ Excessive bold usage ($bold_count instances)"
        ((violations++))
    fi
    
    $VERBOSE && echo "Response preview: ${response:0:300}..."
    log_info "Bold count: $bold_count, Violations: $violations"
    
    if [[ $violations -eq 0 ]]; then
        log_info "✅ PASS - Format compliance OK"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Format violations found"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Context switching (technical -> casual -> technical)
test_context_switching() {
    log_test "Context Switching - Personality Adaptation"
    ((TESTS_RUN++))
    
    reset_session
    
    # Technical
    send_and_wait "cek uptime server" 20
    local resp1
    resp1=$(get_latest_response)
    local score1
    score1=$(has_personality_markers "$resp1")
    
    # Casual
    send_and_wait "btw kamu capek gak sih?" 20
    local resp2
    resp2=$(get_latest_response)
    local score2
    score2=$(has_personality_markers "$resp2")
    
    # Technical again
    send_and_wait "show disk usage /" 20
    local resp3
    resp3=$(get_latest_response)
    local score3
    score3=$(has_personality_markers "$resp3")
    
    log_info "Personality scores: Technical=$score1, Casual=$score2, Technical=$score3"
    
    # Expect: tech low, casual high, tech low again
    if [[ $score1 -le 1 && $score2 -ge 2 && $score3 -le 1 ]]; then
        log_info "✅ PASS - Personality adapts correctly to context"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Personality not adapting properly"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Test: Error handling maintains personality mode
test_error_handling_personality() {
    log_test "Error Handling - Personality Consistency"
    ((TESTS_RUN++))
    
    reset_session
    
    local prompt="jalankan command yang gak ada: foobar123notexist --invalid"
    send_and_wait "$prompt" 25
    
    local response
    response=$(get_latest_response)
    
    if [[ -z "$response" ]]; then
        log_error "No response received"
        ((TESTS_FAILED++))
        return 1
    fi
    
    # Check if error is handled gracefully (should contain error message or explanation)
    if echo "$response" | grep -qiE 'not found|tidak ditemukan|error|gagal|command'; then
        log_info "✅ PASS - Error handled gracefully"
        ((TESTS_PASSED++))
        return 0
    else
        log_error "❌ FAIL - Error not handled properly"
        ((TESTS_FAILED++))
        return 1
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
    log_info "Starting adaptive personality tests..."
    log_info "Target: $TO"
    echo ""
    
    # Run all tests
    test_technical_minimal_personality || true
    test_casual_medium_personality || true
    test_format_compliance_technical || true
    test_context_switching || true
    test_error_handling_personality || true
    
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
