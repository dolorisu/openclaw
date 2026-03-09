"""
Multi-Bubble Patch

Splits responses with double newlines (\\n\\n) into separate message bubbles.

What this patch does:
- Finds text with \\n\\n separators
- Splits into multiple bubbles
- Sends each bubble as separate message
- Works for both WhatsApp and Telegram

Without this patch:
- Long responses come as one big wall of text
- Hard to read, poor UX

With this patch:
- Natural conversation flow
- Each paragraph is separate bubble
- Much better readability
"""

from __future__ import annotations

import re
from pathlib import Path

from ..core import Patch, PatchStatus, PatchResult


class MultiBubblePatch(Patch):
    name = "multibubble"
    description = "Split messages on \\n\\n into separate bubbles"
    dependencies = []
    
    # File patterns to patch
    DELIVER_FILES = ["deliver-*.js"]
    WEB_FILES = ["channel-web-*.js", "web-*.js"]
    TELEGRAM_FILES = ["pi-embedded-*.js"]
    
    # Marker to detect if already patched
    SPLIT_MARKER = 'text.replace(/\\r\\n?/g, "\\n").split(/\\n\\s*\\n+/)'
    
    def check(self) -> PatchStatus:
        """Check if multibubble patch is applied"""
        
        all_files = []
        for pattern in self.DELIVER_FILES + self.WEB_FILES + self.TELEGRAM_FILES:
            all_files.extend(self.find_files(pattern))
        
        if not all_files:
            return PatchStatus.NOT_APPLIED
        
        patched_count = 0
        for f in all_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            if self.SPLIT_MARKER in content:
                patched_count += 1
        
        if patched_count == len(all_files):
            return PatchStatus.APPLIED
        elif patched_count > 0:
            return PatchStatus.PARTIALLY_APPLIED
        else:
            return PatchStatus.NOT_APPLIED
    
    def apply(self) -> PatchResult:
        """Apply multibubble patch"""
        
        files_modified = []
        files_failed = []
        
        # Patch deliver-*.js files
        print("📝 Patching deliver-*.js files...")
        for f in self.find_files("deliver-*.js"):
            if self._patch_deliver_file(f):
                files_modified.append(f)
            else:
                files_failed.append(f)
        
        # Patch web-*.js files  
        print("📝 Patching web/channel-web files...")
        for pattern in self.WEB_FILES:
            for f in self.find_files(pattern):
                if self._patch_web_file(f):
                    files_modified.append(f)
                else:
                    files_failed.append(f)
        
        # Patch Telegram files
        print("📝 Patching Telegram files...")
        for f in self.find_files("pi-embedded-*.js"):
            if self._patch_telegram_file(f):
                files_modified.append(f)
            else:
                files_failed.append(f)
        
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
    
    def _patch_deliver_file(self, file_path: Path) -> bool:
        """Patch deliver-*.js file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if already patched
            if self.SPLIT_MARKER in content:
                print(f"  ⏭️  {file_path.name}: Already patched")
                return True
            
            # Find the sendTextChunks function
            pattern = re.compile(
                r'([ \t]*)const sendTextChunks = async \(text, overrides\) => \{\n\1[ \t]*throwIfAborted\(abortSignal\);\n',
                re.MULTILINE
            )
            
            match = pattern.search(content)
            if not match:
                print(f"  ❌ {file_path.name}: Pattern not found")
                return False
            
            indent = match.group(1)
            
            # Build the split block
            split_block = (
                f'{indent}\t// Multi-bubble: split on \\n\\n\n'
                f'{indent}\tif (typeof text === "string" && text.includes("\\n\\n") && !text.includes("```")) {{\n'
                f'{indent}\t\tconst bubbles = text.replace(/\\r\\n?/g, "\\n").split(/\\n\\s*\\n+/).map((s) => s.trim()).filter(Boolean);\n'
                f'{indent}\t\tfor (const bubble of bubbles) {{\n'
                f'{indent}\t\t\tthrowIfAborted(abortSignal);\n'
                f'{indent}\t\t\tresults.push(await handler.sendText(bubble, overrides));\n'
                f'{indent}\t\t}}\n'
                f'{indent}\t\treturn;\n'
                f'{indent}\t}}\n'
            )
            
            # Insert after the throwIfAborted line
            insert_at = match.end()
            new_content = content[:insert_at] + split_block + content[insert_at:]
            
            self.backup_file(file_path)
            file_path.write_text(new_content, encoding='utf-8')
            print(f"  ✅ {file_path.name}: Patched")
            return True
            
        except Exception as e:
            print(f"  ❌ {file_path.name}: {e}")
            return False
    
    def _patch_web_file(self, file_path: Path) -> bool:
        """Patch web-*.js / channel-web-*.js file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if already patched
            if 'paragraphParts = rawText.includes("```")' in content:
                print(f"  ⏭️  {file_path.name}: Already patched")
                return True
            
            # Find and replace paragraph splitting logic
            old_pattern = r'const paragraphParts = rawText\.split\(/\\n\\n\+/\)\.map\(\(part\) => part\.trim\(\)\)\.filter\(Boolean\);'
            
            new_logic = (
                'const keepAtomicProgress = /^\\s*Progress:\\s+/m.test(rawText) && /^\\s*Path:\\s+/m.test(rawText);\n'
                '\t\tconst paragraphParts = rawText.includes("```") || keepAtomicProgress ? [rawText] : '
                'rawText.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean);'
            )
            
            if re.search(old_pattern, content):
                new_content = re.sub(old_pattern, new_logic, content)
                
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                print(f"  ✅ {file_path.name}: Patched")
                return True
            else:
                print(f"  ⚠️  {file_path.name}: Pattern not found (might be already patched)")
                return True  # Consider success if pattern not found (might be newer version)
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: {e}")
            return False
    
    def _patch_telegram_file(self, file_path: Path) -> bool:
        """Patch Telegram pi-embedded-*.js file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if already patched
            if '__openclawNoSplit' in content:
                print(f"  ⏭️  {file_path.name}: Already patched")
                return True
            
            # Find sendTelegramText function
            marker = 'const splitSource = fallbackText.replace(/\\r\\n?/g, "\\n");'
            
            if marker not in content:
                print(f"  ⚠️  {file_path.name}: Marker not found")
                return False
            
            # Build split block
            split_block = """\tconst splitSource = fallbackText.replace(/\\r\\n?/g, "\\n");
\tif (!opts?.__openclawNoSplit && /\\n\\s*\\n+/.test(splitSource) && !splitSource.includes("```")) {
\t\tconst parts = splitSource.split(/\\n\\s*\\n+/).map((part) => part.trim()).filter(Boolean);
\t\tif (parts.length > 1) {
\t\t\tlet firstMessageId;
\t\t\tfor (let i = 0; i < parts.length; i += 1) {
\t\t\t\tconst part = parts[i];
\t\t\t\tconst messageId = await sendTelegramText(bot, chatId, part, runtime, {
\t\t\t\t\t...opts,
\t\t\t\t\tplainText: part,
\t\t\t\t\t__openclawNoSplit: true,
\t\t\t\t\treplyToMessageId: i === 0 ? opts?.replyToMessageId : void 0,
\t\t\t\t\treplyMarkup: i === 0 ? opts?.replyMarkup : void 0
\t\t\t\t});
\t\t\t\tif (firstMessageId === void 0) firstMessageId = messageId;
\t\t\t}
\t\t\tif (firstMessageId !== void 0) return firstMessageId;
\t\t}
\t}
"""
            
            new_content = content.replace(marker, split_block)
            
            if new_content != content:
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                print(f"  ✅ {file_path.name}: Patched")
                return True
            else:
                print(f"  ⚠️  {file_path.name}: No changes")
                return False
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: {e}")
            return False
