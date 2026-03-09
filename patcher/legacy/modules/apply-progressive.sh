#!/usr/bin/env bash
#
# Progressive updates patch for OpenClaw WhatsApp/Telegram channels
# Enables block streaming to send interim text updates during long tasks
#
# This patch changes:
#   disableBlockStreaming: true  →  disableBlockStreaming: false
#
# in web channel files so progress updates are sent incrementally
# instead of batched at the end.
#
# Cross-platform: Works on macOS, Linux with any node manager
# (Homebrew, mise, nvm, volta, asdf, npm global)
#

set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
MODE="enable"

# Detect OS for sed compatibility
detect_sed_inplace() {
    if sed --version >/dev/null 2>&1; then
        # GNU sed (Linux)
        echo "sed -i"
    else
        # BSD sed (macOS)
        echo "sed -i ''"
    fi
}

SED_INPLACE=$(detect_sed_inplace)

# Find OpenClaw dist directory
find_openclaw_dist() {
    local candidates=()
    
    # Try npm root -g first (most reliable)
    if command -v npm >/dev/null 2>&1; then
        local npm_root
        npm_root=$(npm root -g 2>/dev/null || echo "")
        if [[ -n "$npm_root" && -d "$npm_root/openclaw/dist" ]]; then
            echo "$npm_root/openclaw/dist"
            return 0
        fi
    fi
    
    # Try finding from openclaw binary
    if command -v openclaw >/dev/null 2>&1; then
        local openclaw_bin
        openclaw_bin=$(command -v openclaw)
        openclaw_bin=$(readlink -f "$openclaw_bin" 2>/dev/null || realpath "$openclaw_bin" 2>/dev/null || echo "$openclaw_bin")
        
        # Walk up to find node_modules/openclaw/dist
        local dir="$openclaw_bin"
        while [[ "$dir" != "/" ]]; do
            dir=$(dirname "$dir")
            if [[ -d "$dir/openclaw/dist" ]] && [[ $(basename "$(dirname "$dir")") == "node_modules" ]]; then
                echo "$dir/openclaw/dist"
                return 0
            fi
            if [[ -d "$dir/lib/node_modules/openclaw/dist" ]]; then
                echo "$dir/lib/node_modules/openclaw/dist"
                return 0
            fi
        done
    fi
    
    # Fallback to common paths (with glob expansion)
    candidates=(
        "$HOME/.local/share/mise/installs/node"/*/lib/node_modules/openclaw/dist
        "$HOME/.nvm/versions/node"/*/lib/node_modules/openclaw/dist
        "$HOME/.volta/tools/image/node"/*/lib/node_modules/openclaw/dist
        "$HOME/.asdf/installs/nodejs"/*/.npm/lib/node_modules/openclaw/dist
        "/opt/homebrew/lib/node_modules/openclaw/dist"
        "/usr/local/lib/node_modules/openclaw/dist"
        "$HOME/.npm-global/lib/node_modules/openclaw/dist"
    )
    
    for pattern in "${candidates[@]}"; do
        # Expand glob and check if exists
        for dir in $pattern; do
            if [[ -d "$dir" ]]; then
                echo "$dir"
                return 0
            fi
        done
    done
    
    echo "Error: Could not find openclaw/dist directory" >&2
    echo "  Tried: npm root -g, openclaw binary path, common node manager paths" >&2
    return 1
}

DIST_DIR=$(find_openclaw_dist)
if [[ $? -ne 0 ]]; then
    exit 1
fi

echo "OpenClaw dist: $DIST_DIR"
echo

# Target files (version-agnostic discovery)
discover_target_files() {
    local files=()
    shopt -s nullglob
    for f in "$DIST_DIR"/channel-web-*.js "$DIST_DIR"/web-*.js; do
        [[ -f "$f" ]] || continue
        if grep -q "disableBlockStreaming:\s*\(true\|false\)," "$f" 2>/dev/null; then
            files+=("$f")
        fi
    done
    if [[ -d "$DIST_DIR/plugin-sdk" ]]; then
        for f in "$DIST_DIR"/plugin-sdk/channel-web-*.js "$DIST_DIR"/plugin-sdk/web-*.js; do
            [[ -f "$f" ]] || continue
            if grep -q "disableBlockStreaming:\s*\(true\|false\)," "$f" 2>/dev/null; then
                files+=("$f")
            fi
        done
    fi
    shopt -u nullglob
    printf "%s\n" "${files[@]}"
}

FILES=()
while IFS= read -r line; do
    [[ -n "$line" ]] && FILES+=("$line")
done < <(discover_target_files)

# Check if already patched
check_patch_status() {
    local file="$1"
    if grep -q "disableBlockStreaming: false," "$file" 2>/dev/null; then
        echo "✅ patched"
        return 0
    elif grep -q "disableBlockStreaming: true," "$file" 2>/dev/null; then
        echo "❌ unpatched"
        return 1
    else
        echo "⚠️  unknown"
        return 2
    fi
}

# Parse options
if [[ "${1:-}" == "--status" ]]; then
    echo "Progressive updates patch status:"
    echo
    if [[ ${#FILES[@]} -eq 0 ]]; then
        echo "  ⚠️  no version-matching files with disableBlockStreaming token found"
        exit 0
    fi
    for file in "${FILES[@]}"; do
        status=$(check_patch_status "$file" || true)
        basename=$(basename "$file")
        echo "  $basename: $status"
    done
    exit 0
fi

if [[ "${1:-}" == "--disable" ]]; then
    MODE="disable"
elif [[ -n "${1:-}" && "${1:-}" != "--enable" ]]; then
    echo "Usage: $0 [--status|--enable|--disable]" >&2
    exit 2
fi

if [[ "$MODE" == "disable" ]]; then
    SEARCH_TOKEN='disableBlockStreaming: false,'
    REPLACE_TOKEN='disableBlockStreaming: true,'
    ACTION_LABEL='disable progressive updates'
    SUCCESS_LABEL='Progressive updates disabled'
else
    SEARCH_TOKEN='disableBlockStreaming: true,'
    REPLACE_TOKEN='disableBlockStreaming: false,'
    ACTION_LABEL='enable progressive updates'
    SUCCESS_LABEL='Progressive updates enabled'
fi

# Apply patch
echo "Applying patch to $ACTION_LABEL..."
echo "Detected sed mode: $SED_INPLACE"
echo

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "⚠️  No target files with disableBlockStreaming token found in: $DIST_DIR"
    echo "   (bundle may have changed or progressive mode unsupported in this build)"
    exit 0
fi

patched_count=0
skipped_count=0
error_count=0

for file in "${FILES[@]}"; do
    basename=$(basename "$file")
    
    if [[ ! -f "$file" ]]; then
        echo "  ⚠️  $basename: not found"
        error_count=$((error_count + 1))
        continue
    fi
    
    # Check current status
    if grep -q "$REPLACE_TOKEN" "$file"; then
        echo "  ⏭️  $basename: already patched"
        skipped_count=$((skipped_count + 1))
        continue
    fi

    if ! grep -q "$SEARCH_TOKEN" "$file"; then
        echo "  ❌ $basename: expected token not found"
        error_count=$((error_count + 1))
        continue
    fi
    
    # Backup
    backup="$file.backup-progressive-$TIMESTAMP"
    cp "$file" "$backup"
    
    # Apply patch (cross-platform sed)
    if [[ "$SED_INPLACE" == "sed -i" ]]; then
        # GNU sed (Linux)
        if sed -i "s/$SEARCH_TOKEN/$REPLACE_TOKEN/g" "$file"; then
            # Verify patch applied
            if grep -q "$REPLACE_TOKEN" "$file"; then
                echo "  ✅ $basename: patched (backup: $(basename "$backup"))"
                patched_count=$((patched_count + 1))
            else
                echo "  ❌ $basename: patch failed (no change detected)"
                cp "$backup" "$file"
                error_count=$((error_count + 1))
            fi
        else
            echo "  ❌ $basename: sed failed"
            cp "$backup" "$file"
            error_count=$((error_count + 1))
        fi
    else
        # BSD sed (macOS)
        if sed -i '' "s/$SEARCH_TOKEN/$REPLACE_TOKEN/g" "$file"; then
            # Verify patch applied
            if grep -q "$REPLACE_TOKEN" "$file"; then
                echo "  ✅ $basename: patched (backup: $(basename "$backup"))"
                patched_count=$((patched_count + 1))
            else
                echo "  ❌ $basename: patch failed (no change detected)"
                cp "$backup" "$file"
                error_count=$((error_count + 1))
            fi
        else
            echo "  ❌ $basename: sed failed"
            cp "$backup" "$file"
            error_count=$((error_count + 1))
        fi
    fi
done

echo
echo "Summary:"
echo "  Patched: $patched_count"
echo "  Skipped: $skipped_count"
echo "  Errors:  $error_count"
echo

if [[ $patched_count -gt 0 ]]; then
    echo "✅ $SUCCESS_LABEL!"
    echo
    echo "Next steps:"
    echo "  1. Restart OpenClaw: openclaw gateway restart (or sudo systemctl restart openclaw)"
    if [[ "$MODE" == "disable" ]]; then
        echo "  2. Test long tasks to verify replies arrive as final/full messages"
    else
        echo "  2. Test multi-step task to verify progress updates are sent incrementally"
    fi
    echo "  3. Remember to send /reset to reload system prompt after workspace changes"
    exit 0
elif [[ $skipped_count -gt 0 && $error_count -eq 0 ]]; then
    echo "✅ All files already patched"
    exit 0
else
    echo "❌ Patch failed"
    exit 1
fi
