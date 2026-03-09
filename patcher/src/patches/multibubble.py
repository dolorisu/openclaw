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
    JSON_CODEBLOCK_MARKER = 'function formatJsonCodeFences(text) {'
    
    def check(self) -> PatchStatus:
        """Check if multibubble patch is applied"""
        
        all_files = []
        for pattern in self.DELIVER_FILES + self.WEB_FILES + self.TELEGRAM_FILES:
            all_files.extend(self.find_files(pattern))

        if not all_files:
            return PatchStatus.NOT_APPLIED

        patched_count = 0
        candidate_count = 0
        for f in all_files:
            content = f.read_text(encoding='utf-8', errors='ignore')
            is_deliver_candidate = 'const sendTextChunks = async (text, overrides) => {' in content or self.SPLIT_MARKER in content
            is_web_candidate = (
                'const paragraphParts = rawText.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean);' in content
                or 'paragraphParts = rawText.includes("```")' in content
                or self.JSON_CODEBLOCK_MARKER in content
            )
            is_tg_candidate = 'const splitSource = fallbackText.replace(/\\r\\n?/g, "\\n");' in content or '__openclawNoSplit' in content

            file_candidate = is_deliver_candidate or is_web_candidate or is_tg_candidate
            file_patched = (
                (is_deliver_candidate and self.SPLIT_MARKER in content)
                or (is_web_candidate and 'paragraphParts = rawText.includes("```")' in content and self.JSON_CODEBLOCK_MARKER in content)
                or (is_tg_candidate and '__openclawNoSplit' in content)
            )

            if file_candidate:
                candidate_count += 1
                if file_patched:
                    patched_count += 1

        if candidate_count == 0:
            return PatchStatus.NOT_APPLIED
        if patched_count == candidate_count:
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
            result = self._patch_deliver_file(f)
            if result == "patched":
                files_modified.append(f)
            elif result == "failed":
                files_failed.append(f)
        
        # Patch web-*.js files  
        print("📝 Patching web/channel-web files...")
        for pattern in self.WEB_FILES:
            for f in self.find_files(pattern):
                result = self._patch_web_file(f)
                if result == "patched":
                    files_modified.append(f)
                elif result == "failed":
                    files_failed.append(f)
        
        # Patch Telegram files
        print("📝 Patching Telegram files...")
        for f in self.find_files("pi-embedded-*.js"):
            result = self._patch_telegram_file(f)
            if result == "patched":
                files_modified.append(f)
            elif result == "failed":
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
    
    def _patch_deliver_file(self, file_path: Path) -> str:
        """Patch deliver-*.js file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if already patched
            if self.SPLIT_MARKER in content:
                print(f"  ⏭️  {file_path.name}: Already patched")
                return "skip"
            
            # Find the sendTextChunks function
            pattern = re.compile(
                r'([ \t]*)const sendTextChunks = async \(text, overrides\) => \{\n\1[ \t]*throwIfAborted\(abortSignal\);\n',
                re.MULTILINE
            )
            
            match = pattern.search(content)
            if not match:
                print(f"  ❌ {file_path.name}: Pattern not found")
                return "skip"
            
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
            return "patched"
            
        except Exception as e:
            print(f"  ❌ {file_path.name}: {e}")
            return "failed"
    
    def _patch_web_file(self, file_path: Path) -> str:
        """Patch web-*.js / channel-web-*.js file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            changed = False

            # Find and replace paragraph splitting logic
            old_pattern = r'const paragraphParts = rawText\.split\(/\\n\\n\+/\)\.map\(\(part\) => part\.trim\(\)\)\.filter\(Boolean\);'
            
            new_logic = (
                'const keepAtomicProgress = /^\\s*Progress:\\s+/m.test(rawText) && /^\\s*Path:\\s+/m.test(rawText);\n'
                '\t\tconst paragraphParts = rawText.includes("```") || keepAtomicProgress ? [rawText] : '
                'rawText.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean);'
            )

            new_content = content
            if re.search(old_pattern, new_content):
                new_content = re.sub(old_pattern, new_logic, new_content)
                changed = True

            generic_helper = (
                'function formatJsonCodeFences(text) {\n'
                '\tif (typeof text !== "string" || !text.includes("```")) return text;\n'
                '\tconst braceLang = new Set(["js", "javascript", "ts", "typescript", "tsx", "jsx", "rs", "rust", "java", "c", "cpp"]);\n'
                '\tconst countBraces = (line) => {\n'
                '\t\tlet opens = 0;\n'
                '\t\tlet closes = 0;\n'
                '\t\tlet quote = null;\n'
                '\t\tlet escaped = false;\n'
                '\t\tfor (const ch of line) {\n'
                '\t\t\tif (escaped) { escaped = false; continue; }\n'
                '\t\t\tif (ch === "\\\\") { escaped = true; continue; }\n'
                '\t\t\tif (quote) { if (ch === quote) quote = null; continue; }\n'
                '\t\t\tif (ch === "\\\"" || ch.charCodeAt(0) === 39 || ch === "`") { quote = ch; continue; }\n'
                '\t\t\tif (ch === "{" || ch === "[" || ch === "(") opens += 1;\n'
                '\t\t\tif (ch === "}" || ch === "]" || ch === ")") closes += 1;\n'
                '\t\t}\n'
                '\t\treturn { opens, closes };\n'
                '\t};\n'
                '\tconst leadingClosers = (line) => {\n'
                '\t\tconst m = line.match(/^[\\}\\]\\)]+/);\n'
                '\t\treturn m ? m[0].length : 0;\n'
                '\t};\n'
                '\tconst formatBrace = (code, unit = "  ") => {\n'
                '\t\tconst lines = String(code || "").replace(/\\r\\n?/g, "\\n").split("\\n");\n'
                '\t\tlet depth = 0;\n'
                '\t\tconst out = [];\n'
                '\t\tfor (const raw of lines) {\n'
                '\t\t\tconst t = raw.trim();\n'
                '\t\t\tif (!t) { out.push(""); continue; }\n'
                '\t\t\tconst level = Math.max(depth - leadingClosers(t), 0);\n'
                '\t\t\tout.push(unit.repeat(level) + t);\n'
                '\t\t\tconst c = countBraces(t);\n'
                '\t\t\tdepth = Math.max(depth + c.opens - c.closes, 0);\n'
                '\t\t}\n'
                '\t\treturn out.join("\\n");\n'
                '\t};\n'
                '\tconst formatPy = (code) => /[\\{\\[]/.test(code) ? formatBrace(code, "    ") : code;\n'
                '\tconst formatFence = (lang, body) => {\n'
                '\t\tconst l = String(lang || "").toLowerCase();\n'
                '\t\tconst code = String(body || "").trim();\n'
                '\t\tif (!code) return body;\n'
                '\t\tif (l === "json" || l === "jsonc") {\n'
                '\t\t\ttry { return JSON.stringify(JSON.parse(code), null, 2); } catch { return body; }\n'
                '\t\t}\n'
                '\t\tif (braceLang.has(l)) return formatBrace(code, "  ");\n'
                '\t\tif (l === "py" || l === "python") return formatPy(code);\n'
                '\t\treturn body;\n'
                '\t};\n'
                '\treturn text.replace(/```([a-zA-Z0-9_-]*)\\n([\\s\\S]*?)\\n```/g, (full, lang, body) => "```" + lang + "\\n" + formatFence(lang, body) + "\\n```");\n'
                '}\n'
            )

            old_helper = (
                'function formatJsonCodeFences(text) {\n'
                '\tif (typeof text !== "string" || !text.includes("```")) return text;\n'
                '\treturn text.replace(/```(?:json)?\\n([\\s\\S]*?)```/g, (full, body) => {\n'
                '\t\tconst candidate = String(body || "").trim();\n'
                '\t\tif (!candidate) return full;\n'
                '\t\ttry {\n'
                '\t\t\tconst parsed = JSON.parse(candidate);\n'
                '\t\t\treturn "```\\n" + JSON.stringify(parsed, null, 2) + "\\n```";\n'
                '\t\t} catch {\n'
                '\t\t\treturn full;\n'
                '\t\t}\n'
                '\t});\n'
                '}\n'
            )

            if old_helper in new_content and generic_helper not in new_content:
                new_content = new_content.replace(old_helper, generic_helper, 1)
                changed = True

            buggy_quote_check = 'if (ch === """ || ch === "\'" || ch === "`") { quote = ch; continue; }'
            fixed_quote_check = 'if (ch === "\\\"" || ch.charCodeAt(0) === 39 || ch === "`") { quote = ch; continue; }'
            if buggy_quote_check in new_content:
                new_content = new_content.replace(buggy_quote_check, fixed_quote_check)
                changed = True

            if self.JSON_CODEBLOCK_MARKER not in new_content and 'async function deliverWebReply(params) {' in new_content:
                new_content = new_content.replace('async function deliverWebReply(params) {', generic_helper + 'async function deliverWebReply(params) {', 1)
                changed = True

            if 'function formatCodeBlocks(text) {' not in new_content and self.JSON_CODEBLOCK_MARKER in new_content:
                alias_block = (
                    'function formatCodeBlocks(text) {\n'
                    '\treturn formatJsonCodeFences(typeof text === "string" ? text : String(text ?? ""));\n'
                    '}\n'
                )
                new_content = new_content.replace('async function deliverWebReply(params) {', alias_block + 'async function deliverWebReply(params) {', 1)
                changed = True

            old_raw_line = 'const rawText = (replyResult.text || "").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*$/gm, "$1:").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*/gm, "$1: ").replace(/^\\s*[-*_]{3,}\\s*$/gm, "").replace(/```[a-zA-Z0-9_-]+\\n/g, "```\\n").replace(/\\n{3,}/g, "\\n\\n").trim();'
            new_raw_block = (
                'const rawText = formatJsonCodeFences((replyResult.text || "").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*$/gm, "$1:").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*/gm, "$1: ").replace(/^\\s*[-*_]{3,}\\s*$/gm, "").replace(/```[a-zA-Z0-9_-]+\\n/g, "```\\n").replace(/\\n{3,}/g, "\\n\\n").trim());'
            )
            if old_raw_line in new_content and 'formatJsonCodeFences((replyResult.text || "")' not in new_content:
                new_content = new_content.replace(old_raw_line, new_raw_block, 1)
                changed = True

            if changed:
                self.backup_file(file_path)
                file_path.write_text(new_content, encoding='utf-8')
                print(f"  ✅ {file_path.name}: Patched")
                return "patched"

            print(f"  ⏭️  {file_path.name}: Already patched")
            return "skip"
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: {e}")
            return "failed"
    
    def _patch_telegram_file(self, file_path: Path) -> str:
        """Patch Telegram pi-embedded-*.js file"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Check if already patched
            if '__openclawNoSplit' in content:
                print(f"  ⏭️  {file_path.name}: Already patched")
                return "skip"
            
            # Find sendTelegramText function
            marker = 'const splitSource = fallbackText.replace(/\\r\\n?/g, "\\n");'
            
            if marker not in content:
                print(f"  ⚠️  {file_path.name}: Marker not found")
                return "skip"
            
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
                return "patched"
            else:
                print(f"  ⚠️  {file_path.name}: No changes")
                return "skip"
                
        except Exception as e:
            print(f"  ❌ {file_path.name}: {e}")
            return "failed"
