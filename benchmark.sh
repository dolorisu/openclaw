#!/bin/bash
#
# OpenClaw WhatsApp Benchmark - Complete Test Suite
# Target: 120363406118312223@g.us
# 
# Features:
# - Natural human-like prompts
# - Log analysis for quality check
# - Tests: multibubble, progressive, emoji, personality, heavy tasks
#

set -e

TARGET_GROUP="120363406118312223@g.us"
LOG_DIR="/tmp/openclaw"
RESULTS_DIR="/tmp/benchmark-results-$(date +%Y%m%d-%H%M%S)"
TIMEOUT=180
DELAY=20

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test prompts (natural, human-like)
declare -a TEST_PROMPTS=(
    "Halo Doloris, gimana kabarnya hari ini?"
    "Ini test paragraf pertama.

Ini paragraf kedua, coba dipisah jadi bubble terpisah ya"
    "Coba tulis puisi pendek tentang kopi"
    "Bantu hitung: 123 + 456 berapa?"
    "Coba jelasin apa itu ERC-8128 dalam 3 poin"
    "Bantu aku bikin kode Python simple: print hello world"
    "Test kirim gambar: cariin aku gambar kucing lucu dari internet"
    "Terakhir, rangkum percakapan kita hari ini"
)

declare -a TEST_NAMES=(
    "sapaan-basic"
    "multibubble-test"
    "kreatif-puisi"
    "kalkulasi"
    "penjelasan-teknis"
    "coding-task"
    "image-request"
    "memory-summary"
)

mkdir -p "$RESULTS_DIR"

echo "========================================"
echo "🚀 OpenClaw Benchmark - Complete Suite"
echo "========================================"
echo "Target: $TARGET_GROUP"
echo "Total Tests: ${#TEST_PROMPTS[@]}"
echo "Results: $RESULTS_DIR"
echo "Timeout: ${TIMEOUT}s per test"
echo "Delay: ${DELAY}s antar test"
echo "Start: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# Setup PATH
export PATH="$HOME/.npm-global/bin:$PATH"

# Verify openclaw
if ! command -v openclaw &> /dev/null; then
    echo -e "${RED}❌ openclaw not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ OpenClaw v$(openclaw --version) ready${NC}"

# Verify gateway
if ! systemctl --user is-active --quiet openclaw-gateway; then
    echo -e "${RED}❌ Gateway not running${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Gateway active${NC}"
echo ""

# Get current log file
LOG_FILE=$(ls -1t "$LOG_DIR"/openclaw-*.log 2>/dev/null | head -1)
echo -e "${BLUE}📁 Log file: $LOG_FILE${NC}"
echo ""

# Counters
PASSED=0
FAILED=0
START_TIME=$(date +%s)

# Function to analyze response
analyze_response() {
    local test_num=$1
    local test_name=$2
    local log_file=$3
    local response_file=$4
    
    echo ""
    echo -e "${BLUE}📊 Analyzing Response $test_num: $test_name${NC}"
    echo "========================================"
    
    # Check if response exists
    if [ ! -s "$response_file" ]; then
        echo -e "${RED}❌ No response content${NC}"
        return 1
    fi
    
    # Read response
    local response=$(cat "$response_file")
    
    # Check 1: Emoji presence
    if echo "$response" | grep -qE '[✨☕✅❌🎉📊🔧📋🤖🦞]|\(◕‿◕\)|\(⌒‿⌒\)'; then
        echo -e "${GREEN}✅ Emojis: Present${NC}"
    else
        echo -e "${YELLOW}⚠️  Emojis: Missing${NC}"
    fi
    
    # Check 2: Personality (human-like markers)
    if echo "$response" | grep -qiE '(Rifuki|rifuki|~|dong|ya|nih|sih|lho|kok)'; then
        echo -e "${GREEN}✅ Personality: Human-like tone detected${NC}"
    else
        echo -e "${YELLOW}⚠️  Personality: Could be more natural${NC}"
    fi
    
    # Check 3: Formatting
    if echo "$response" | grep -qE '(\*\*|\- |\d+\.|```)'; then
        echo -e "${GREEN}✅ Formatting: Bold/list/code blocks present${NC}"
    else
        echo -e "${BLUE}ℹ️  Formatting: Plain text (OK for casual)${NC}"
    fi
    
    # Check 4: Content quality (length check)
    local char_count=$(echo -n "$response" | wc -c)
    if [ $char_count -lt 50 ]; then
        echo -e "${YELLOW}⚠️  Length: Very short ($char_count chars)${NC}"
    elif [ $char_count -gt 2000 ]; then
        echo -e "${YELLOW}⚠️  Length: Very long ($char_count chars)${NC}"
    else
        echo -e "${GREEN}✅ Length: Good ($char_count chars)${NC}"
    fi
    
    # Check 5: Multibubble (for test #2)
    if [ "$test_name" == "multibubble-test" ]; then
        # Check log for split messages
        local msg_count=$(grep -c "Sent message" "$log_file" | tail -20 || echo "0")
        if [ "$msg_count" -gt "1" ]; then
            echo -e "${GREEN}✅ Multibubble: Messages split correctly${NC}"
        else
            echo -e "${YELLOW}⚠️  Multibubble: Check WhatsApp for split bubbles${NC}"
        fi
    fi
    
    # Show preview
    echo ""
    echo "📝 Response Preview:"
    echo "${response:0:200}${#response}..."
    echo ""
}

# Run tests
for i in "${!TEST_PROMPTS[@]}"; do
    NUM=$((i+1))
    NAME="${TEST_NAMES[$i]}"
    PROMPT="${TEST_PROMPTS[$i]}"
    
    echo "========================================"
    echo -e "${BLUE}Test [$NUM/${#TEST_PROMPTS[@]}]: $NAME${NC}"
    echo "Prompt: ${PROMPT:0:60}${#PROMPT}..."
    echo "========================================"
    
    # Record log position before
    LOG_POS_BEFORE=$(wc -l < "$LOG_FILE")
    
    # Send prompt
    RESPONSE_FILE="$RESULTS_DIR/${NUM}-${NAME}.txt"
    LOG_CAPTURE="$RESULTS_DIR/${NUM}-${NAME}.log"
    
    if openclaw agent --channel whatsapp --to "$TARGET_GROUP" --timeout "$TIMEOUT" --message "$PROMPT" --deliver > "$RESPONSE_FILE" 2>> "$LOG_CAPTURE"; then
        echo -e "${GREEN}✅ Prompt delivered${NC}"
        
        # Wait for response to be logged
        sleep 3
        
        # Extract response from log
        tail -n +$((LOG_POS_BEFORE + 1)) "$LOG_FILE" | grep -v '^[[:space:]]*{' | grep -v '^[[:space:]]*}' | grep -v '^[[:space:]]*\"' | grep -v '^[[:space:]]*\[' | grep -v '^[[:space:]]*\]' | grep -v '^[[:space:]]*$' | tail -5 > "$RESPONSE_FILE.extracted" 2>/dev/null || true
        
        # Use original response file if extracted is empty
        if [ ! -s "$RESPONSE_FILE.extracted" ]; then
            cp "$RESPONSE_FILE" "$RESPONSE_FILE.extracted"
        fi
        
        # Analyze
        analyze_response "$NUM" "$NAME" "$LOG_CAPTURE" "$RESPONSE_FILE.extracted"
        
        ((PASSED++))
    else
        echo -e "${RED}❌ Failed to deliver${NC}"
        ((FAILED++))
    fi
    
    # Delay
    if [ $NUM -lt ${#TEST_PROMPTS[@]} ]; then
        echo "⏳ Waiting ${DELAY}s..."
        sleep $DELAY
    fi
    echo ""
done

END_TIME=$(date +%s)
TOTAL_TIME=$((END_TIME - START_TIME))

# Summary
echo "========================================"
echo "📊 BENCHMARK SUMMARY"
echo "========================================"
echo "Total Tests: ${#TEST_PROMPTS[@]}"
echo -e "Passed: ${GREEN}$PASSED ✅${NC}"
echo -e "Failed: ${RED}$FAILED ${FAILED} ❌${NC}"
echo "Success Rate: $(( PASSED * 100 / ${#TEST_PROMPTS[@]} ))%"
echo "Total Time: ${TOTAL_TIME}s"
echo "Results Saved: $RESULTS_DIR"
echo "End: $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️  $FAILED test(s) failed${NC}"
fi

echo ""
echo "📁 Check detailed results in: $RESULTS_DIR"
echo ""
