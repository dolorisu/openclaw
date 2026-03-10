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
                '\t\tconst paragraphParts = rawText.includes("```") || keepAtomicProgress ? [rawText] : splitWhatsAppParagraphParts(rawText);'
            )

            new_content = content
            if re.search(old_pattern, new_content):
                new_content = re.sub(old_pattern, new_logic, new_content)
                changed = True

            # Handle newer runtime variants where paragraphParts has extra filtering
            paragraph_variant_pattern = r'const paragraphParts = rawText\.includes\("```"\)\s*\|\|\s*keepAtomicProgress \? \[rawText\] : [^;]+;'
            paragraph_variant_replacement = 'const paragraphParts = rawText.includes("```") || keepAtomicProgress ? [rawText] : splitWhatsAppParagraphParts(rawText);'
            if re.search(paragraph_variant_pattern, new_content) and 'splitWhatsAppParagraphParts(rawText)' not in new_content:
                new_content = re.sub(paragraph_variant_pattern, paragraph_variant_replacement, new_content)
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
                'function normalizeWhatsAppText(text) {\n'
                '\tif (typeof text !== "string") return String(text ?? "");\n'
                '\tlet out = text.replace(/\\r\\n?/g, "\\n");\n'
                '\tout = out.replace(/[\\u200B-\\u200D\\uFEFF]/g, "");\n'
                '\tout = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);\n'
                '\tout = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");\n'
                '\tout = out.replace(/^([^\\n]{8,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");\n'
                '\tout = out.replace(/^([ \\t]*[-*+•]\\s+[^\\n]{1,40})\\n(?=[a-z(])/gim, "$1 ");\n'
                '\tout = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");\n'
                '\tout = out.replace(/\\n{3,}/g, "\\n\\n");\n'
                '\treturn out.trim();\n'
                '}\n'
                'function splitWhatsAppParagraphParts(text) {\n'
                '\tconst splitConversationalParagraph = (part) => {\n'
                '\t\tconst p = String(part || "").trim();\n'
                '\t\tif (!p) return [];\n'
                '\t\tconst dashSplit = p.match(/^(.{8,80}?—)\\s*(.{12,})$/);\n'
                '\t\tif (dashSplit) return [dashSplit[1], dashSplit[2]];\n'
                '\t\tif (p.length < 70) return [p];\n'
                '\t\tif (p.includes("```") || p.includes("`") || /https?:\\/\\//i.test(p)) return [p];\n'
                '\t\tif (/^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n'
                '\t\tif (/\\n/.test(p) && /^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n'
                '\t\tconst flat = p.replace(/\\n+/g, " ").replace(/\\s{2,}/g, " ").trim();\n'
                '\t\tconst clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);\n'
                '\t\tif (clause) return [clause[1], clause[2]];\n'
                '\t\tconst sentence = flat.match(/^(.{18,120}?[.!?~])\\s+(.{20,})$/);\n'
                '\t\tif (sentence) return [sentence[1], sentence[2]];\n'
                '\t\treturn [p];\n'
                '\t};\n'
                '\tconst base = String(text || "").split(/\\n\\s*\\n+/).map((part) => part.trim()).filter(Boolean).flatMap(splitConversationalParagraph);\n'
                '\tif (base.length <= 1) return base;\n'
                '\tconst merged = [];\n'
                '\tfor (const part of base) {\n'
                '\t\tif (!merged.length) { merged.push(part); continue; }\n'
                '\t\tconst prev = merged[merged.length - 1];\n'
                '\t\tconst startsListLike = /^(?:[-*+•]|\\d+[.)])\\s+/.test(part);\n'
                '\t\tconst prevEndsColon = /[:：]$/.test(prev);\n'
                '\t\tconst prevEndsSoftClause = /[,—-]$/.test(prev);\n'
                '\t\tconst startsContinuation = /^[a-z(]/.test(part);\n'
                '\t\tif (startsListLike && prevEndsColon) {\n'
                '\t\t\tmerged[merged.length - 1] = `${prev}\\n\\n${part}`;\n'
                '\t\t\tcontinue;\n'
                '\t\t}\n'
                '\t\tif (startsContinuation && !prevEndsSoftClause) {\n'
                '\t\t\tmerged[merged.length - 1] = `${prev} ${part}`;\n'
                '\t\t\tcontinue;\n'
                '\t\t}\n'
                '\t\tmerged.push(part);\n'
                '\t}\n'
                '\treturn merged;\n'
                '}\n'
                'function chunkWhatsAppPart(part, textLimit, chunkMode, tableMode) {\n'
                '\tconst rendered = markdownToWhatsApp(convertMarkdownTables(part, tableMode));\n'
                '\tconst numericLimit = typeof textLimit === "number" && Number.isFinite(textLimit) ? textLimit : 0;\n'
                '\tconst safeLimit = Math.max(numericLimit, 3200);\n'
                '\tif (rendered.length <= safeLimit) return [rendered];\n'
                '\treturn chunkMarkdownTextWithMode(rendered, textLimit, chunkMode);\n'
                '}\n'
            )

            text_shape_helpers = (
                'function normalizeWhatsAppText(text) {\n'
                '\tif (typeof text !== "string") return String(text ?? "");\n'
                '\tlet out = text.replace(/\\r\\n?/g, "\\n");\n'
                '\tout = out.replace(/[\\u200B-\\u200D\\uFEFF]/g, "");\n'
                '\tout = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);\n'
                '\tout = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");\n'
                '\tout = out.replace(/^([^\\n]{8,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");\n'
                '\tout = out.replace(/^([ \\t]*[-*+•]\\s+[^\\n]{1,40})\\n(?=[a-z(])/gim, "$1 ");\n'
                '\tout = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");\n'
                '\tout = out.replace(/\\n{3,}/g, "\\n\\n");\n'
                '\treturn out.trim();\n'
                '}\n'
                'function splitWhatsAppParagraphParts(text) {\n'
                '\tconst splitConversationalParagraph = (part) => {\n'
                '\t\tconst p = String(part || "").trim();\n'
                '\t\tif (!p) return [];\n'
                '\t\tconst dashSplit = p.match(/^(.{8,80}?—)\\s*(.{12,})$/);\n'
                '\t\tif (dashSplit) return [dashSplit[1], dashSplit[2]];\n'
                '\t\tif (p.length < 70) return [p];\n'
                '\t\tif (p.includes("```") || p.includes("`") || /https?:\\/\\//i.test(p)) return [p];\n'
                '\t\tif (/^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n'
                '\t\tif (/\\n/.test(p) && /^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n'
                '\t\tconst flat = p.replace(/\\n+/g, " ").replace(/\\s{2,}/g, " ").trim();\n'
                '\t\tconst clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);\n'
                '\t\tif (clause) return [clause[1], clause[2]];\n'
                '\t\tconst sentence = flat.match(/^(.{18,120}?[.!?~])\\s+(.{20,})$/);\n'
                '\t\tif (sentence) return [sentence[1], sentence[2]];\n'
                '\t\treturn [p];\n'
                '\t};\n'
                '\tconst base = String(text || "").split(/\\n\\s*\\n+/).map((part) => part.trim()).filter(Boolean).flatMap(splitConversationalParagraph);\n'
                '\tif (base.length <= 1) return base;\n'
                '\tconst merged = [];\n'
                '\tfor (const part of base) {\n'
                '\t\tif (!merged.length) { merged.push(part); continue; }\n'
                '\t\tconst prev = merged[merged.length - 1];\n'
                '\t\tconst startsListLike = /^(?:[-*+•]|\\d+[.)])\\s+/.test(part);\n'
                '\t\tconst prevEndsColon = /[:：]$/.test(prev);\n'
                '\t\tconst prevEndsSoftClause = /[,—-]$/.test(prev);\n'
                '\t\tconst startsContinuation = /^[a-z(]/.test(part);\n'
                '\t\tif (startsListLike && prevEndsColon) {\n'
                '\t\t\tmerged[merged.length - 1] = `${prev}\\n\\n${part}`;\n'
                '\t\t\tcontinue;\n'
                '\t\t}\n'
                '\t\tif (startsContinuation && !prevEndsSoftClause) {\n'
                '\t\t\tmerged[merged.length - 1] = `${prev} ${part}`;\n'
                '\t\t\tcontinue;\n'
                '\t\t}\n'
                '\t\tmerged.push(part);\n'
                '\t}\n'
                '\treturn merged;\n'
                '}\n'
                'function chunkWhatsAppPart(part, textLimit, chunkMode, tableMode) {\n'
                '\tconst rendered = markdownToWhatsApp(convertMarkdownTables(part, tableMode));\n'
                '\tconst numericLimit = typeof textLimit === "number" && Number.isFinite(textLimit) ? textLimit : 0;\n'
                '\tconst safeLimit = Math.max(numericLimit, 3200);\n'
                '\tif (rendered.length <= safeLimit) return [rendered];\n'
                '\treturn chunkMarkdownTextWithMode(rendered, textLimit, chunkMode);\n'
                '}\n'
            )

            text_chunks_pattern = r'const textChunks = rawText\.includes\("```"\)\s*\|\|\s*keepAtomicProgress \? \[markdownToWhatsApp\(convertMarkdownTables\(rawText, tableMode\)\)\] : [^;]+;'
            text_chunks_replacement = 'const textChunks = rawText.includes("```") || keepAtomicProgress ? [markdownToWhatsApp(convertMarkdownTables(rawText, tableMode))] : paragraphParts.flatMap((part) => chunkWhatsAppPart(part, textLimit, chunkMode, tableMode));'
            if re.search(text_chunks_pattern, new_content):
                updated_content = re.sub(text_chunks_pattern, text_chunks_replacement, new_content)
                if updated_content != new_content:
                    new_content = updated_content
                    changed = True

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

            old_normalize_helper = (
                'function normalizeWhatsAppText(text) {\n'
                '\tif (typeof text !== "string") return String(text ?? "");\n'
                '\tlet out = text.replace(/\\r\\n?/g, "\\n");\n'
                '\tout = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);\n'
                '\tout = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");\n'
                '\tout = out.replace(/\\n{3,}/g, "\\n\\n");\n'
                '\treturn out.trim();\n'
                '}\n'
            )

            new_normalize_helper = (
                'function normalizeWhatsAppText(text) {\n'
                '\tif (typeof text !== "string") return String(text ?? "");\n'
                '\tlet out = text.replace(/\\r\\n?/g, "\\n");\n'
                '\tout = out.replace(/[\\u200B-\\u200D\\uFEFF]/g, "");\n'
                '\tout = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);\n'
                '\tout = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");\n'
                '\tout = out.replace(/^([^\\n]{40,120},)\\s+(?=[^\\n]{24,})/m, "$1\\n\\n");\n'
                '\tout = out.replace(/^([^\\n]{24,120}[—-])\\s+(?=[^\\n]{20,})/m, "$1\\n\\n");\n'
                '\tout = out.replace(/,\\n(?=\\s*[a-z(])/g, ", ");\n'
                '\tout = out.replace(/^([ \\t]*[-*+•]\\s+[^\\n]{1,40})\\n(?=[a-z(])/gim, "$1 ");\n'
                '\tout = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");\n'
                '\tout = out.replace(/\\n{3,}/g, "\\n\\n");\n'
                '\treturn out.trim();\n'
                '}\n'
            )

            chunk_helper_block = (
                'function chunkWhatsAppPart(part, textLimit, chunkMode, tableMode) {\n'
                '\tconst rendered = markdownToWhatsApp(convertMarkdownTables(part, tableMode));\n'
                '\tconst numericLimit = typeof textLimit === "number" && Number.isFinite(textLimit) ? textLimit : 0;\n'
                '\tconst safeLimit = Math.max(numericLimit, 3200);\n'
                '\tif (rendered.length <= safeLimit) return [rendered];\n'
                '\treturn chunkMarkdownTextWithMode(rendered, textLimit, chunkMode);\n'
                '}\n'
            )

            if old_helper in new_content and generic_helper not in new_content:
                new_content = new_content.replace(old_helper, generic_helper, 1)
                changed = True

            # Upgrade existing normalize helper in-place (for already-patched bundles)
            if 'function normalizeWhatsAppText(text) {' in new_content:
                if 'out = out.replace(/[\\u200B-\\u200D\\uFEFF]/g, "");' not in new_content and 'let out = text.replace(/\\r\\n?/g, "\\n");' in new_content:
                    new_content = new_content.replace(
                        'let out = text.replace(/\\r\\n?/g, "\\n");',
                        'let out = text.replace(/\\r\\n?/g, "\\n");\n\tout = out.replace(/[\\u200B-\\u200D\\uFEFF]/g, "");',
                        1
                    )
                    changed = True

                if 'out = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");' not in new_content and 'out = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);' in new_content:
                    new_content = new_content.replace(
                        'out = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);',
                        'out = out.replace(/^\\s*#{2,6}\\s+(.+)$/gm, (_, title) => `**${String(title || "").trim()}**`);\n\tout = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");',
                        1
                    )
                    changed = True

                if 'out = out.replace(/^([^\\n]{8,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");' not in new_content and 'out = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");' in new_content:
                    new_content = new_content.replace(
                        'out = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");',
                        'out = out.replace(/^([^\\n]{6,120}[.!?~])\\s+(?=\\S)/m, "$1\\n\\n");\n\tout = out.replace(/^([^\\n]{8,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");',
                        1
                    )
                    changed = True

                if 'out = out.replace(/^([^\\n]{12,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");' in new_content:
                    new_content = new_content.replace('out = out.replace(/^([^\\n]{12,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");', 'out = out.replace(/^([^\\n]{8,90}?—)\\s*(?=\\S.{16,})/m, "$1\\n\\n");')
                    changed = True

                # Remove old phrase/topic-specific hacks (keep generic rules only)
                for legacy_line in [
                    'out = out.replace(/^(\\s*(?:oke|siap|baik|wkwk|hmm|yosh|nah|btw)\\b[^\\n]{0,110}?[~!?])\\s+(?=\\S)/im, "$1\\n\\n");',
                    'out = out.replace(/^(Oke,\\s*ini\\s*ringkasnya\\s*ya~)\\s+/im, "$1\\n\\n");',
                    'out = out.replace(/^(Sarapan\\s*dulu\\s*yaa~)\\s+/im, "$1\\n\\n");',
                    'out = out.replace(/^(Wkwk[^\\n]{0,80}?~)\\s+(?=[^A-Za-z0-9\\s])/im, "$1\\n\\n");',
                    'out = out.replace(/(Ringkasan konsep utama)\\s+([1-9]\\)\\s+)/gi, "$1\\n$2");',
                    'out = out.replace(/([^.?!:;\\n])\\n(?=\\s*(?:Inti artikel itu:|Ringkasan konsep utama\\b|Ini penting\\b|Bedanya vs SIWE\\b|Security angle\\b|Kombinasi paling kuat:|Hasilnya:|Status saat ini\\b|Jadi cocok untuk\\b|Kalau mau, next aku bisa))/g, "$1\\n\\n");',
                    'out = out.replace(/^([^\\n]{40,120},)\\s+(?=[^\\n]{24,})/m, "$1\\n\\n");',
                    'out = out.replace(/^([^\\n]{24,120}[—-])\\s+(?=[^\\n]{20,})/m, "$1\\n\\n");',
                    'out = out.replace(/,\\n(?=\\s*[a-z(])/g, ", ");'
                ]:
                    if legacy_line in new_content:
                        new_content = new_content.replace(legacy_line + '\n', '')
                        new_content = new_content.replace(legacy_line, '')
                        changed = True

                if 'out = out.replace(/^([ \\t]*[-*+•]\\s+[^\\n]{1,40})\\n(?=[a-z(])/gim, "$1 ");' not in new_content and 'out = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");' in new_content:
                    new_content = new_content.replace(
                        'out = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");',
                        'out = out.replace(/^([ \\t]*[-*+•]\\s+[^\\n]{1,40})\\n(?=[a-z(])/gim, "$1 ");\n\tout = out.replace(/([^.?!:;\\n])\\n(?!\\s*(?:[-*+•]\\s|\\d+[.)]\\s|#{1,6}\\s|>))(?!\\s*$)/g, "$1 ");',
                        1
                    )
                    changed = True

                # Upgrade split helper from topic-specific to universal
                if 'const startsBenefit = /^(?:✅\\s*)?Benefit:/i.test(part);' in new_content:
                    new_content = new_content.replace(
                        'const startsBenefit = /^(?:✅\\s*)?Benefit:/i.test(part);\n\t\tconst startsFlow = /^Flow:/i.test(part);\n\t\tconst startsLowerCont = /^(?:dan|atau|serta|asal)\\b/i.test(part);\n\t\tif (startsBenefit || startsFlow) {',
                        'const startsListLike = /^(?:[-*+•]|\\d+[.)])\\s+/.test(part);\n\t\tconst prevEndsColon = /[:：]$/.test(prev);\n\t\tconst startsContinuation = /^[a-z(]/.test(part);\n\t\tif (startsListLike && prevEndsColon) {'
                    )
                    new_content = new_content.replace('if (startsLowerCont) {', 'if (startsContinuation) {')
                    changed = True

                if 'const prevEndsSoftClause = /[,—-]$/.test(prev);' not in new_content and 'const prevEndsColon = /[:：]$/.test(prev);' in new_content:
                    new_content = new_content.replace(
                        'const prevEndsColon = /[:：]$/.test(prev);',
                        'const prevEndsColon = /[:：]$/.test(prev);\n\t\tconst prevEndsSoftClause = /[,—-]$/.test(prev);',
                        1
                    )
                    changed = True

                if 'if (startsContinuation && !prevEndsSoftClause) {' not in new_content and 'if (startsContinuation) {' in new_content:
                    new_content = new_content.replace('if (startsContinuation) {', 'if (startsContinuation && !prevEndsSoftClause) {', 1)
                    changed = True

                # Upgrade split helper to conversational clause splitter
                old_split_base = 'const base = String(text || "").split(/\\n\\s*\\n+/).map((part) => part.trim()).filter(Boolean);'
                if old_split_base in new_content and 'splitConversationalParagraph = (part) =>' not in new_content:
                    new_split_block = (
                        'const splitConversationalParagraph = (part) => {\n\t\tconst p = String(part || "").trim();\n\t\tif (!p) return [];\n\t\tif (p.length < 70) return [p];\n\t\tif (p.includes("```") || p.includes("`") || /https?:\\/\\//i.test(p)) return [p];\n\t\tif (/^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n\t\tif (/\\n/.test(p) && /^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n\t\tconst flat = p.replace(/\\n+/g, " ").replace(/\\s{2,}/g, " ").trim();\n\t\tconst clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);\n\t\tif (clause) return [clause[1], clause[2]];\n\t\tconst sentence = flat.match(/^(.{18,120}?[.!?~])\\s+(.{20,})$/);\n\t\tif (sentence) return [sentence[1], sentence[2]];\n\t\treturn [p];\n\t};\n\tconst base = String(text || "").split(/\\n\\s*\\n+/).map((part) => part.trim()).filter(Boolean).flatMap(splitConversationalParagraph);'
                    )
                    new_content = new_content.replace(old_split_base, new_split_block, 1)
                    changed = True

                # Upgrade existing conversational splitter variant
                old_guard = 'if (p.includes("```") || p.includes("`") || /https?:\\/\\//i.test(p) || /\\n/.test(p)) return [p];'
                if old_guard in new_content:
                    new_content = new_content.replace(old_guard, 'if (p.includes("```") || p.includes("`") || /https?:\\/\\//i.test(p)) return [p];')
                    changed = True

                old_list_guard = 'if (/^(?:[-*+•]|\\d+[.)])\\s+/.test(p)) return [p];'
                if old_list_guard in new_content:
                    new_content = new_content.replace(old_list_guard, 'if (/^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n\t\tif (/\\n/.test(p) && /^(?:[-*+•]|\\d+[.)])\\s+/m.test(p)) return [p];\n\t\tconst flat = p.replace(/\\n+/g, " ").replace(/\\s{2,}/g, " ").trim();')
                    changed = True

                if 'const dashSplit = p.match(/^(.{8,80}?—)\\s*(.{12,})$/);' not in new_content and 'const p = String(part || "").trim();' in new_content:
                    new_content = new_content.replace(
                        'const p = String(part || "").trim();',
                        'const p = String(part || "").trim();\n\t\tconst dashSplit = p.match(/^(.{8,80}?—)\\s*(.{12,})$/);\n\t\tif (dashSplit) return [dashSplit[1], dashSplit[2]];',
                        1
                    )
                    changed = True

                if 'const clause = p.match(/^(.{18,96}?(?:,|—|-|:))\\s+(.{20,})$/);' in new_content:
                    new_content = new_content.replace('const clause = p.match(/^(.{18,96}?(?:,|—|-|:))\\s+(.{20,})$/);', 'const clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);')
                    changed = True

                if 'const clause = flat.match(/^(.{18,96}?(?:,|—|-|:))\\s+(.{20,})$/);' in new_content:
                    new_content = new_content.replace('const clause = flat.match(/^(.{18,96}?(?:,|—|-|:))\\s+(.{20,})$/);', 'const clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);')
                    changed = True

                if 'const clause = flat.match(/^(.{18,96}?(?:,|—|-|:))\\s+(.{20,})$/);' in new_content:
                    new_content = new_content.replace('const clause = flat.match(/^(.{18,96}?(?:,|—|-|:))\\s+(.{20,})$/);', 'const clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);')
                    changed = True

                if 'const clause = flat.match(/^(.{18,110}?(?:—|:))\\s+(.{20,})$/);' in new_content:
                    new_content = new_content.replace('const clause = flat.match(/^(.{18,110}?(?:—|:))\\s+(.{20,})$/);', 'const clause = flat.match(/^(.{18,110}?(?:—|:))\\s*(.{20,})$/);')
                    changed = True

                if 'const sentence = p.match(/^(.{18,120}?[.!?~])\\s+(.{20,})$/);' in new_content:
                    new_content = new_content.replace('const sentence = p.match(/^(.{18,120}?[.!?~])\\s+(.{20,})$/);', 'const sentence = flat.match(/^(.{18,120}?[.!?~])\\s+(.{20,})$/);')
                    changed = True

            if old_normalize_helper in new_content and new_normalize_helper not in new_content:
                new_content = new_content.replace(old_normalize_helper, new_normalize_helper, 1)
                changed = True

            buggy_quote_check = 'if (ch === """ || ch === "\'" || ch === "`") { quote = ch; continue; }'
            fixed_quote_check = 'if (ch === "\\\"" || ch.charCodeAt(0) === 39 || ch === "`") { quote = ch; continue; }'
            if buggy_quote_check in new_content:
                new_content = new_content.replace(buggy_quote_check, fixed_quote_check)
                changed = True

            if self.JSON_CODEBLOCK_MARKER not in new_content and 'async function deliverWebReply(params) {' in new_content:
                new_content = new_content.replace('async function deliverWebReply(params) {', generic_helper + 'async function deliverWebReply(params) {', 1)
                changed = True

            if 'function normalizeWhatsAppText(text) {' not in new_content and self.JSON_CODEBLOCK_MARKER in new_content:
                new_content = new_content.replace('async function deliverWebReply(params) {', text_shape_helpers + 'async function deliverWebReply(params) {', 1)
                changed = True

            if 'function chunkWhatsAppPart(part, textLimit, chunkMode, tableMode) {' not in new_content and 'async function deliverWebReply(params) {' in new_content:
                new_content = new_content.replace('async function deliverWebReply(params) {', chunk_helper_block + 'async function deliverWebReply(params) {', 1)
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
                'const rawText = normalizeWhatsAppText(formatJsonCodeFences((replyResult.text || "").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*$/gm, "$1:").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*/gm, "$1: ").replace(/^\\s*[-*_]{3,}\\s*$/gm, "").replace(/```[a-zA-Z0-9_-]+\\n/g, "```\\n").replace(/\\n{3,}/g, "\\n\\n").trim()));'
            )
            if old_raw_line in new_content and 'normalizeWhatsAppText(formatJsonCodeFences((replyResult.text || "")' not in new_content:
                new_content = new_content.replace(old_raw_line, new_raw_block, 1)
                changed = True

            legacy_raw_block = 'const rawText = formatJsonCodeFences((replyResult.text || "").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*$/gm, "$1:").replace(/^\\s*\\*\\*([^*\\n]{1,64}):\\*\\*\\s*/gm, "$1: ").replace(/^\\s*[-*_]{3,}\\s*$/gm, "").replace(/```[a-zA-Z0-9_-]+\\n/g, "```\\n").replace(/\\n{3,}/g, "\\n\\n").trim());'
            if legacy_raw_block in new_content and 'normalizeWhatsAppText(formatJsonCodeFences((replyResult.text || "")' not in new_content:
                new_content = new_content.replace(legacy_raw_block, new_raw_block, 1)
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
