#!/usr/bin/env bash
# run-all-tests.sh
# Master test runner for OpenClaw WhatsApp MEDIUM personality validation
#
# Usage:
#   ./run-all-tests.sh --to <phone|group_jid> [--quick] [--verbose]
#
# Exit codes:
#   0 = All test suites PASS
#   1 = One or more test suites FAIL
#   2 = Usage error

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Config
TO=""
QUICK=false
VERBOSE=false

# Test suite results
SUITES_RUN=0
SUITES_PASSED=0
SUITES_FAILED=0

usage() {
    cat << EOF
Usage: $0 --to <recipient> [options]

Master test runner for OpenClaw WhatsApp MEDIUM personality validation.

Options:
    --to <jid>          Target phone number or group JID (required)
    --quick             Run quick subset of tests (skip long-running tests)
    --verbose           Show detailed output from test scripts
    -h, --help          Show this help message

Examples:
    $0 --to 120363424987356245@g.us
    $0 --to +6289669848875 --quick --verbose

Test Suites:
    1. personality-adaptive-test.sh    - Adaptive personality behavior (5 tests)
    2. edge-case-stability-test.sh     - Edge cases and stability (6 tests)

Recommended:
    - Use GROUP chat (e.g., 120363424987356245@g.us) to avoid DM ban risk
    - Use --verbose to see detailed test output and debug failures
    - Run on VPS via: ssh rifuki-amazon-id-ubuntu24-2c2g
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

log_suite() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC} $*"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
}

run_test_suite() {
    local suite_name="$1"
    local suite_script="$2"
    
    log_suite "Running: $suite_name"
    ((SUITES_RUN++))
    
    local verbose_flag=""
    if $VERBOSE; then
        verbose_flag="--verbose"
    fi
    
    if bash "$suite_script" --to "$TO" $verbose_flag; then
        log_info "✅ SUITE PASSED: $suite_name"
        ((SUITES_PASSED++))
        return 0
    else
        log_error "❌ SUITE FAILED: $suite_name"
        ((SUITES_FAILED++))
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
        --quick)
            QUICK=true
            shift
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

# Validate target format
if [[ "$TO" =~ @g\.us$ ]]; then
    log_info "Target: GROUP chat (recommended)"
elif [[ "$TO" =~ ^[+0-9]+$ ]]; then
    log_warn "Target: DM chat (risk of ban if too many messages)"
else
    log_error "Invalid target format. Expected: +phone or jid@g.us"
    exit 2
fi

# Main execution
main() {
    echo "══════════════════════════════════════════════════════════"
    echo "  OpenClaw WhatsApp MEDIUM Personality Test Suite"
    echo "══════════════════════════════════════════════════════════"
    log_info "Target: $TO"
    log_info "Mode: $(if $QUICK; then echo 'QUICK'; else echo 'FULL'; fi)"
    log_info "Verbose: $(if $VERBOSE; then echo 'YES'; else echo 'NO'; fi)"
    echo ""
    
    # Suite 1: Adaptive personality tests
    run_test_suite \
        "Adaptive Personality Tests" \
        "$SCRIPT_DIR/personality-adaptive-test.sh" || true
    
    # Suite 2: Edge case and stability tests
    if ! $QUICK; then
        run_test_suite \
            "Edge Case & Stability Tests" \
            "$SCRIPT_DIR/edge-case-stability-test.sh" || true
    else
        log_info "⊘ SKIPPED: Edge case tests (--quick mode)"
    fi
    
    # Final summary
    echo ""
    echo "══════════════════════════════════════════════════════════"
    echo "  FINAL TEST SUMMARY"
    echo "══════════════════════════════════════════════════════════"
    echo "Test suites run:    $SUITES_RUN"
    echo -e "Suites passed:      ${GREEN}$SUITES_PASSED${NC}"
    echo -e "Suites failed:      ${RED}$SUITES_FAILED${NC}"
    echo "══════════════════════════════════════════════════════════"
    
    if [[ $SUITES_FAILED -eq 0 ]]; then
        echo ""
        log_info "🎉 ALL TEST SUITES PASSED!"
        log_info "MEDIUM personality implementation: STABLE ✓"
        echo ""
        echo "Next steps:"
        echo "  - Review detailed logs if needed"
        echo "  - Deploy to production with confidence"
        echo "  - Run regression tests after future changes"
        exit 0
    else
        echo ""
        log_error "⚠️  SOME TEST SUITES FAILED"
        log_error "Review failed tests and fix issues before production deployment"
        echo ""
        echo "Debugging tips:"
        echo "  - Rerun with --verbose to see detailed output"
        echo "  - Check session logs: ~/.openclaw/agents/main/sessions/"
        echo "  - Verify VPS gateway is running: systemctl status openclaw-gateway"
        exit 1
    fi
}

main
