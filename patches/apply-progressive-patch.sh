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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Find OpenClaw dist directory
find_openclaw_dist() {
    local candidates=(
        "/opt/homebrew/lib/node_modules/openclaw/dist"
        "/usr/local/lib/node_modules/openclaw/dist"
        "$HOME/.npm-global/lib/node_modules/openclaw/dist"
        "$HOME/.nvm/versions/node/*/lib/node_modules/openclaw/dist"
    )
    
    for dir in "${candidates[@]}"; do
        # Handle glob expansion
        for expanded in $dir; do
            if [[ -d "$expanded" ]]; then
                echo "$expanded"
                return 0
            fi
        done
    done
    
    echo "Error: Could not find openclaw/dist directory" >&2
    return 1
}

DIST_DIR=$(find_openclaw_dist)
if [[ $? -ne 0 ]]; then
    exit 1
fi

echo "OpenClaw dist: $DIST_DIR"
echo

# Target files
FILES=(
    "$DIST_DIR/channel-web-k1Tb8tGz.js"
    "$DIST_DIR/channel-web-sl83aqDv.js"
    "$DIST_DIR/web-pFdwPQ7y.js"
    "$DIST_DIR/web-CSq0l9pG.js"
)

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

# Show status
if [[ "${1:-}" == "--status" ]]; then
    echo "Progressive updates patch status:"
    echo
    for file in "${FILES[@]}"; do
        if [[ -f "$file" ]]; then
            status=$(check_patch_status "$file")
            basename=$(basename "$file")
            echo "  $basename: $status"
        else
            echo "  $(basename "$file"): ⚠️  not found"
        fi
    done
    exit 0
fi

# Apply patch
echo "Applying progressive updates patch..."
echo

patched_count=0
skipped_count=0
error_count=0

for file in "${FILES[@]}"; do
    basename=$(basename "$file")
    
    if [[ ! -f "$file" ]]; then
        echo "  ⚠️  $basename: not found"
        ((error_count++))
        continue
    fi
    
    # Check current status
    if grep -q "disableBlockStreaming: false," "$file"; then
        echo "  ⏭️  $basename: already patched"
        ((skipped_count++))
        continue
    fi
    
    # Backup
    backup="$file.backup-progressive-$TIMESTAMP"
    cp "$file" "$backup"
    
    # Apply patch
    if sed -i '' 's/disableBlockStreaming: true,/disableBlockStreaming: false,/g' "$file"; then
        # Verify patch applied
        if grep -q "disableBlockStreaming: false," "$file"; then
            echo "  ✅ $basename: patched (backup: $(basename "$backup"))"
            ((patched_count++))
        else
            echo "  ❌ $basename: patch failed (no change detected)"
            cp "$backup" "$file"
            ((error_count++))
        fi
    else
        echo "  ❌ $basename: sed failed"
        cp "$backup" "$file"
        ((error_count++))
    fi
done

echo
echo "Summary:"
echo "  Patched: $patched_count"
echo "  Skipped: $skipped_count"
echo "  Errors:  $error_count"
echo

if [[ $patched_count -gt 0 ]]; then
    echo "✅ Progressive updates enabled!"
    echo
    echo "Next steps:"
    echo "  1. Restart OpenClaw service: sudo systemctl restart openclaw"
    echo "  2. Test with multi-step task to verify progress updates are sent incrementally"
    echo "  3. Remember to send /reset to reload system prompt after workspace changes"
    exit 0
elif [[ $skipped_count -gt 0 && $error_count -eq 0 ]]; then
    echo "✅ All files already patched"
    exit 0
else
    echo "❌ Patch failed"
    exit 1
fi
