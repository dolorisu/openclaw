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
    
    def check(self) -> PatchStatus:
        """Check if progressive patch is applied"""
        
        # Check 1: Block streaming enabled?
        streaming_files = []
        for pattern in self.STREAMING_FILES:
            streaming_files.extend(self.find_files(pattern))
        
        if not streaming_files:
            return PatchStatus.NOT_APPLIED
        
        streaming_enabled_count = 0
        for f in streaming_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            # Check if disableBlockStreaming is set to false
            if re.search(r'disableBlockStreaming:\s*false', content):
                streaming_enabled_count += 1
        
        # Check 2: Deliver blocker removed?
        deliver_files = []
        for pattern in self.DELIVER_FILES:
            deliver_files.extend(self.find_files(pattern))
        
        blocker_removed_count = 0
        for f in deliver_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
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
        
        # Determine status
        if streaming_enabled_count == len(streaming_files) and blocker_removed_count == len(deliver_files):
            return PatchStatus.APPLIED
        elif streaming_enabled_count > 0 or blocker_removed_count > 0:
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
                
                # Find the deliver callback with the blocker
                # Pattern: deliver: async (payload, info) => { if (info.kind !== "final") return;
                
                blocker_pattern = re.compile(
                    r'(deliver:\s*async\s*\([^)]+\)\s*=>\s*\{)\s*'
                    r'if\s*\(\s*info\.kind\s*!==\s*["\']final["\']\s*\)\s*return\s*;',
                    re.MULTILINE | re.DOTALL
                )
                
                if not blocker_pattern.search(content):
                    print(f"  ⏭️  {f.name}: Blocker not found or already fixed")
                    continue
                
                # Replacement: Remove blocker, add progress handling
                replacement = r'''\1
\t\t// Progressive updates: allow non-final messages through
\t\tconst isProgressUpdate = info.kind !== "final";
\t\t
\t\t// Skip empty or tiny progress updates to avoid spam
\t\tif (isProgressUpdate) {
\t\t\tconst text = payload?.text || "";
\t\t\tconst normalized = text.replace(/\\r\\n?/g, "\\n").trim();
\t\t\t
\t\t\t// Skip if empty
\t\t\tif (!normalized) return;
\t\t\t
\t\t\t// Skip if too short (< 20 chars, likely just typing indicator)
\t\t\tif (normalized.length < 20) return;
\t\t\t
\t\t\t// Skip if no meaningful content (just "Progress:" without details)
\t\t\tif (/^Progress:\\s*$/.test(normalized)) return;
\t\t}'''
                
                new_content = blocker_pattern.sub(replacement, content)
                
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
