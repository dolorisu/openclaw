from __future__ import annotations
import re
from ..core import Patch, PatchStatus, PatchResult

class CodeFormatterPatch(Patch):
    name = "code_formatter"
    description = "Auto-format JSON with 2-space indentation"
    dependencies = []
    PATCH_MARKER = "CODE-FORMATTER-PATCH"
    TARGET_FILES = ["outbound-*.js"]
    
    def check(self):
        for pattern in self.TARGET_FILES:
            for f in self.find_files(pattern):
                try:
                    if self.PATCH_MARKER in f.read_text(encoding='utf-8'):
                        return PatchStatus.APPLIED
                except:
                    continue
        return PatchStatus.NOT_APPLIED
    
    def apply(self):
        files_modified = []
        formatter = '\n\t// CODE-FORMATTER-PATCH\n\tif (text && typeof text === "string") {\n\t\tif ((text.startsWith("[") && text.endsWith("]")) ||\n\t\t    (text.startsWith("{") && text.endsWith("}"))) {\n\t\t\ttry {\n\t\t\t\tconst parsed = JSON.parse(text);\n\t\t\t\ttext = JSON.stringify(parsed, null, 2);\n\t\t\t\tconsole.log("[CODE-FORMATTER] JSON formatted");\n\t\t\t} catch (e) {}\n\t\t}\n\t}\n'
        for pattern in self.TARGET_FILES:
            for f in self.find_files(pattern):
                try:
                    content = f.read_text(encoding='utf-8')
                    if self.PATCH_MARKER in content:
                        continue
                    if 'let text = body;' in content:
                        content = content.replace('let text = body;', 'let text = body;' + formatter)
                        self.backup_file(f)
                        f.write_text(content, encoding='utf-8')
                        files_modified.append(f)
                except:
                    continue
        return PatchResult(
            status=PatchStatus.APPLIED if files_modified else PatchStatus.NOT_APPLIED,
            files_modified=files_modified
        )
