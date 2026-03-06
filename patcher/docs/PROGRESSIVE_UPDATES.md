# Progressive Updates Fix - Technical Documentation

## Problem Statement

Users were experiencing batched responses during long tasks instead of incremental progress updates. All progress messages were held back and sent together at the end of task completion.

**Expected behavior (from WORKFLOW.md):**
- "Use incremental updates for multi-step tasks"
- "Do not batch all checkpoints at the end"
- "One checkpoint = max 1 short bubble"
- Heartbeat every 5-15 seconds during long tasks

**Observed behavior:**
- All progress updates batched at the end
- No interim messages during task execution
- Users left hanging during heavy operations

## Root Cause Analysis

### Investigation Path

1. **Initially suspected:** `queuedFinal` logic blocking non-final messages
   - **Finding:** This was NOT the blocker
   - The check at line 1786-1793 only returns false if NO messages sent at all
   - If any progress was sent, function continues normally

2. **Dispatcher infrastructure:**
   - **Finding:** Already working correctly
   - `createReplyDispatcher()` has separate queues for "tool", "block", and "final"
   - `deliver()` function is called for all message types
   - Previous AI already patched to allow `info.kind !== "final"` messages through

3. **Actual blocker discovered:**
   - **Location:** `channel-web-*.js` and `web-*.js` files
   - **Line:** `disableBlockStreaming: true,` in `replyOptions`
   - **Effect:** Prevents interim text blocks from being sent immediately

## Solution

### The Fix

Change in 4 files:
- `dist/channel-web-k1Tb8tGz.js`
- `dist/channel-web-sl83aqDv.js`
- `dist/web-pFdwPQ7y.js`
- `dist/web-CSq0l9pG.js`

**Patch:**
```javascript
// BEFORE
replyOptions: {
    disableBlockStreaming: true,
    onModelSelected
}

// AFTER
replyOptions: {
    disableBlockStreaming: false,
    onModelSelected
}
```

### What This Enables

With `disableBlockStreaming: false`:

1. **Text blocks sent immediately:** When the model outputs text between tool calls, those text blocks are now sent as separate messages immediately instead of being held back

2. **Progress checkpoints work:** Status updates like:
   ```
   Status mulai: Analyzing codebase
   ```
   are sent right away instead of queued until final response

3. **Interactive experience:** Users see progress in real-time:
   ```
   Progress: Found 15 files to patch
   Progress: Patching file 1/15
   Progress: Patching file 5/15
   Progress: Patching file 10/15
   Status selesai: All files patched
   ```

## How It Works

### Message Flow (After Fix)

1. Model starts processing user request
2. Model outputs: "Status mulai: Starting task"
   - → Dispatcher enqueues as "block" kind
   - → `deliver()` called immediately (kind !== "final")
   - → User receives message #1
3. Model executes tool call
   - → Tool result queued but not delivered to user
4. Model outputs: "Progress: Step 1 complete"
   - → Dispatcher enqueues as "block" kind
   - → `deliver()` called immediately
   - → User receives message #2
5. More tool calls and progress updates...
6. Model outputs final response
   - → Dispatcher enqueues as "final" kind
   - → `deliver()` called
   - → User receives final message

### Previous AI's Work

The previous AI correctly patched the delivery functions to:
1. Detect progress updates: `const isProgressUpdate = info.kind !== "final"`
2. Normalize WhatsApp text: `normalizeProgressTextForWhatsApp()` helper
3. Allow delivery of non-final messages

However, these messages were never being CREATED because block streaming was disabled.

## Testing

### Manual Test

Send multi-step task via WhatsApp/Telegram:
```
Please create 5 demo files with different content:
1. demo1.txt - about AI
2. demo2.txt - about programming
3. demo3.txt - about DevOps
4. demo4.txt - about databases
5. demo5.txt - about networking

Show me progress for each file.
```

**Expected outcome:**
- See "Status mulai:" message first
- See "Progress: Created demo1.txt" immediately after file creation
- See "Progress: Created demo2.txt" immediately after second file
- etc.
- See "Status selesai:" at the end

**Without patch (batched):**
- Silence during execution
- All progress messages arrive together at the end

### Benchmark Tests (Reported Issues)

From previous context:
- `dm/interactive_progress` - format inconsistent
- `group_z/interactive_progress` - timeout
- `group_z/todo_tracking` - timeout
- `dm/todo_tracking` - passes

After applying progressive updates patch, these should improve.

## Deployment

### Patch Script Robustness

The `apply-progressive.sh` script is **cross-platform** and works with any node installation:

**Supported environments:**
- ✅ macOS (Homebrew, mise, nvm, volta, asdf)
- ✅ Linux (system node, mise, nvm, volta, asdf, npm global)
- ✅ Any environment with `npm` available

**Discovery methods (in order):**
1. `npm root -g` (most reliable)
2. Walk up from `openclaw` binary path
3. Glob patterns for common node managers
4. Fallback to standard paths

**OS detection:**
- Automatically detects GNU sed (Linux) vs BSD sed (macOS)
- Uses `sed -i` on Linux, `sed -i ''` on macOS

### VPS Deployment
```bash
# On VPS
cd ~/.openclaw/patcher
~/.openclaw/patcher/apply-progressive.sh --status
~/.openclaw/patcher/apply-progressive.sh
sudo systemctl restart openclaw

# Verify
~/.openclaw/patcher/apply-progressive.sh --status
```

### Local Development
```bash
cd ~/.openclaw/patcher
~/.openclaw/patcher/apply-progressive.sh --status
~/.openclaw/patcher/apply-progressive.sh
openclaw gateway restart
```

### Important Notes

1. **Combine with multi-bubble patch:** Progressive updates work best when combined with multi-bubble patch for conversational responses

2. **Workspace MD files matter:** Ensure `WORKFLOW.md` has clear instructions for the model to output progress checkpoints

3. **Model must cooperate:** The patch enables the infrastructure, but the model must actually output interim text. If the model batches all tool calls without outputting status text, there's nothing to stream.

4. **Session reload required:** After updating workspace MD files, send `/reset` to reload system prompt

## Files Modified

```
/opt/homebrew/lib/node_modules/openclaw/dist/
├── channel-web-k1Tb8tGz.js  (line 1782)
├── channel-web-sl83aqDv.js  (line 1781)
├── web-pFdwPQ7y.js          (line 1823)
└── web-CSq0l9pG.js          (line 1827)
```

## Related Documentation

- `workspace/custom/policies/WORKFLOW.md` - Interactive progress protocol
- `workspace/custom/policies/CHANNEL_GUIDE.md` - Multi-bubble instructions
- `patcher/PATCHES.md` - Patch overview
- `patcher/ACTIVE.md` - Quick reference
