"""
Progressive Updates Patch

Enables real-time streaming of progress updates during long-running tasks.

What this patch does:
1. Enables block streaming (disableBlockStreaming: false)
2. FIXES the deliver callback blocker that drops non-final messages
3. Adds progress normalization helpers

Without this patch:
- All progress messages are batched and sent at the end
- Bot shows "typing" indicator but no messages arrive

With this patch:
- Progress messages sent in real-time as tasks complete
- Multi-step operations show incremental updates
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

from ..core import Patch, PatchStatus, PatchResult


class ProgressivePatch(Patch):
    name = "progressive"
    description = "Enable real-time progressive updates with delivery blocker fix"
    dependencies = []  # No dependencies
    
    # Files that need disableBlockStreaming: false
    STREAMING_FILES = [
        "channel-web-*.js",
        "web-*.js",
    ]
    
    # Files that need deliver callback fix
    DELIVER_FILES = [
        "channel-web-*.js",
        "web-*.js",
    ]

    # Files that need no-silent-drop fallback when final payload is missing
    FALLBACK_FILES = [
        "channel-web-*.js",
        "web-*.js",
    ]
    
    def check(self) -> PatchStatus:
        """Check if progressive patch is applied"""
        
        # Check 1: Block streaming enabled?
        streaming_files = []
        for pattern in self.STREAMING_FILES:
            streaming_files.extend(self.find_files(pattern))
        
        if not streaming_files:
            return PatchStatus.NOT_APPLIED
        
        streaming_enabled_count = 0
        streaming_candidates = 0
        for f in streaming_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            if 'disableBlockStreaming:' not in content:
                continue
            streaming_candidates += 1
            # Check if disableBlockStreaming is set to false
            if re.search(r'disableBlockStreaming:\s*false', content):
                streaming_enabled_count += 1
        
        # Check 2: Deliver blocker removed?
        deliver_files = []
        for pattern in self.DELIVER_FILES:
            deliver_files.extend(self.find_files(pattern))
        
        blocker_removed_count = 0
        deliver_candidates = 0
        for f in deliver_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            if 'deliver: async' not in content:
                continue
            deliver_candidates += 1
            # Check if the blocker is removed
            # OLD: if (info.kind !== "final") return;
            # NEW: Should have isProgressUpdate or similar logic
            if re.search(r'if\s*\(\s*info\.kind\s*!==\s*["\']final["\']\s*\)\s*return\s*;', content):
                # Blocker still exists
                pass
            else:
                # Check if replaced with progress logic
                if re.search(r'isProgressUpdate\s*=\s*info\.kind\s*!==\s*["\']final["\']', content):
                    blocker_removed_count += 1
        
        # Check 3: Missing-final fallback present?
        fallback_files = []
        for pattern in self.FALLBACK_FILES:
            fallback_files.extend(self.find_files(pattern))

        fallback_patched_count = 0
        fallback_candidates = 0
        for f in fallback_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            if 'if (!queuedFinal) {' not in content:
                continue
            fallback_candidates += 1
            if 'Auto-reply fallback sent after missing final payload' in content:
                fallback_patched_count += 1

        # Determine status
        if streaming_candidates == 0:
            streaming_candidates = 1
            streaming_enabled_count = 1
        if deliver_candidates == 0:
            deliver_candidates = 1
            blocker_removed_count = 1
        if fallback_candidates == 0:
            fallback_candidates = 1
            fallback_patched_count = 1

        if (
            streaming_enabled_count == streaming_candidates
            and blocker_removed_count == deliver_candidates
            and fallback_patched_count == fallback_candidates
        ):
            return PatchStatus.APPLIED
        elif streaming_enabled_count > 0 or blocker_removed_count > 0 or fallback_patched_count > 0:
            return PatchStatus.PARTIALLY_APPLIED
        else:
            return PatchStatus.NOT_APPLIED
    
    def apply(self) -> PatchResult:
        """Apply progressive updates patch"""
        
        files_modified = []
        files_failed = []
        
        # Step 1: Enable block streaming
        print("📝 Step 1: Enabling block streaming...")
        streaming_files = []
        for pattern in self.STREAMING_FILES:
            streaming_files.extend(self.find_files(pattern))
        
        for f in streaming_files:
            try:
                content = f.read_text(encoding='utf-8')
                
                # Replace disableBlockStreaming: true -> false
                new_content = re.sub(
                    r'disableBlockStreaming:\s*true',
                    'disableBlockStreaming: false',
                    content
                )
                
                if new_content != content:
                    self.backup_file(f)
                    f.write_text(new_content, encoding='utf-8')
                    files_modified.append(f)
                    print(f"  ✅ {f.name}: Enabled block streaming")
                else:
                    print(f"  ⏭️  {f.name}: Already enabled or not found")
                    
            except Exception as e:
                print(f"  ❌ {f.name}: {e}")
                files_failed.append(f)
        
        # Step 2: Fix deliver callback blocker
        print("\n📝 Step 2: Fixing deliver callback blocker...")
        deliver_files = []
        for pattern in self.DELIVER_FILES:
            deliver_files.extend(self.find_files(pattern))
        
        for f in deliver_files:
            try:
                content = f.read_text(encoding='utf-8')
                
                new_content = content

                # Common exact blocker in current bundles
                if 'if (info.kind !== "final") return;' in new_content:
                    new_content = new_content.replace(
                        'if (info.kind !== "final") return;',
                        'const isProgressUpdate = info.kind !== "final";\n\t\t\t\tif (isProgressUpdate && !payload?.text && !payload?.mediaUrl && !payload?.mediaUrls?.length) return;'
                    )

                # Regex fallback for variant formatting
                blocker_pattern = re.compile(
                    r'(deliver:\s*async\s*\([^)]+\)\s*=>\s*\{)\s*'
                    r'if\s*\(\s*info\.kind\s*!==\s*["\']final["\']\s*\)\s*return\s*;',
                    re.MULTILINE | re.DOTALL
                )
                if blocker_pattern.search(new_content):
                    replacement = r'''\1
\t\t\t\tconst isProgressUpdate = info.kind !== "final";
\t\t\t\tif (isProgressUpdate && !payload?.text && !payload?.mediaUrl && !payload?.mediaUrls?.length) return;'''
                    new_content = blocker_pattern.sub(replacement, new_content)

                if new_content == content:
                    print(f"  ⏭️  {f.name}: Blocker not found or already fixed")
                    continue
                
                if new_content != content:
                    self.backup_file(f)
                    f.write_text(new_content, encoding='utf-8')
                    files_modified.append(f)
                    print(f"  ✅ {f.name}: Fixed deliver blocker")
                else:
                    print(f"  ⚠️  {f.name}: Pattern matched but no changes")
                    
            except Exception as e:
                print(f"  ❌ {f.name}: {e}")
                files_failed.append(f)
        
        # Step 3: Add no-silent-drop fallback when final payload is missing
        print("\n📝 Step 3: Adding missing-final fallback...")
        fallback_files = []
        for pattern in self.FALLBACK_FILES:
            fallback_files.extend(self.find_files(pattern))

        old_fallback_block = '''if (!queuedFinal) {
\t\tif (shouldClearGroupHistory) params.groupHistories.set(params.groupHistoryKey, []);
\t\tlogVerbose("Skipping auto-reply: silent token or no text/media returned from resolver");
\t\treturn false;
\t}'''

        new_fallback_block = '''if (!queuedFinal) {
\t\tif (!didSendReply) {
\t\t\tawait deliverWebReply({
\t\t\t\treplyResult: {
\t\t\t\t\ttext: "Maaf, proses reply sempat kepotong. Coba kirim lagi ya."
\t\t\t\t},
\t\t\t\tmsg: params.msg,
\t\t\t\tmediaLocalRoots,
\t\t\t\tmaxMediaBytes: params.maxMediaBytes,
\t\t\t\ttextLimit,
\t\t\t\tchunkMode,
\t\t\t\treplyLogger: params.replyLogger,
\t\t\t\tconnectionId: params.connectionId,
\t\t\t\tskipLog: false,
\t\t\t\ttableMode
\t\t\t});
\t\t\tdidSendReply = true;
\t\t\twhatsappOutboundLog.warn("Auto-reply fallback sent after missing final payload");
\t\t}
\t\tif (shouldClearGroupHistory) params.groupHistories.set(params.groupHistoryKey, []);
\t\tlogVerbose("Skipping auto-reply: silent token or no text/media returned from resolver");
\t\treturn didSendReply;
\t}'''

        for f in fallback_files:
            try:
                content = f.read_text(encoding='utf-8')

                if 'Auto-reply fallback sent after missing final payload' in content:
                    print(f"  ⏭️  {f.name}: Fallback already patched")
                    continue

                if old_fallback_block not in content:
                    print(f"  ⏭️  {f.name}: Fallback block not found")
                    continue

                new_content = content.replace(old_fallback_block, new_fallback_block, 1)
                if new_content != content:
                    self.backup_file(f)
                    f.write_text(new_content, encoding='utf-8')
                    files_modified.append(f)
                    print(f"  ✅ {f.name}: Added missing-final fallback")
                else:
                    print(f"  ⚠️  {f.name}: Fallback replacement made no changes")

            except Exception as e:
                print(f"  ❌ {f.name}: {e}")
                files_failed.append(f)

        # Determine result
        if files_failed:
            status = PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED
            message = f"Applied to {len(files_modified)} files, failed on {len(files_failed)} files"
        elif files_modified:
            status = PatchStatus.APPLIED
            message = f"Successfully applied to {len(files_modified)} files"
        else:
            status = PatchStatus.APPLIED
            message = "All files already patched"
        
        return PatchResult(
            status=status,
            files_modified=files_modified,
            files_failed=files_failed,
            message=message
        )
    
    def rollback(self) -> PatchResult:
        """Rollback progressive patch (disable streaming)"""
        
        files_modified = []
        files_failed = []
        
        print("🔄 Rolling back progressive patch...")
        
        # Disable block streaming
        streaming_files = []
        for pattern in self.STREAMING_FILES:
            streaming_files.extend(self.find_files(pattern))
        
        for f in streaming_files:
            try:
                content = f.read_text(encoding='utf-8')
                
                # Replace disableBlockStreaming: false -> true
                new_content = re.sub(
                    r'disableBlockStreaming:\s*false',
                    'disableBlockStreaming: true',
                    content
                )
                
                if new_content != content:
                    self.backup_file(f)
                    f.write_text(new_content, encoding='utf-8')
                    files_modified.append(f)
                    print(f"  ✅ {f.name}: Disabled block streaming")
                    
            except Exception as e:
                print(f"  ❌ {f.name}: {e}")
                files_failed.append(f)
        
        # Note: We don't restore the blocker because that would break functionality
        # Instead, the blocker fix is kept but streaming is disabled
        
        if files_failed:
            status = PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED
        elif files_modified:
            status = PatchStatus.APPLIED
        else:
            status = PatchStatus.APPLIED
        
        return PatchResult(
            status=status,
            files_modified=files_modified,
            files_failed=files_failed,
            message=f"Rolled back (streaming disabled on {len(files_modified)} files)"
        )
