"""Allow media send paths from ~/.openclaw/media and ~/.openclaw/artifacts."""

from __future__ import annotations

import re

from ..core import Patch, PatchResult, PatchStatus


class MediaSendPathsPatch(Patch):
    name = "media_send_paths"
    description = "Allow send attachment paths from ~/.openclaw/media and ~/.openclaw/artifacts"
    dependencies = ["media_roots"]

    # Regex pattern to match both minified (isPathInside$1) and non-minified (isPathInside) code
    OLD_PATTERN = re.compile(
        r'const openClawTmpDir = path\.resolve\(resolvePreferredOpenClawTmpDir\(\)\);\s*'
        r'if \(!isPathInside(\$\d+)?\(openClawTmpDir, resolved\)\) return;',
        re.MULTILINE
    )
    
    NEW_BLOCK = """\tconst openClawTmpDir = path.resolve(resolvePreferredOpenClawTmpDir());
\tconst configStateDir = path.resolve(CONFIG_DIR);
\tconst mediaStateDir = path.join(configStateDir, \"media\");
\tconst artifactsStateDir = path.join(configStateDir, \"artifacts\");
\tconst allowedRoot = [openClawTmpDir, mediaStateDir, artifactsStateDir].find((root) => isPathInside$1(root, resolved));
\tif (!allowedRoot) return;
\tif (allowedRoot === openClawTmpDir) {
\t\tawait assertNoTmpAliasEscape({
\t\t\tfilePath: resolved,
\t\t\ttmpRoot: openClawTmpDir
\t\t});
\t}
\treturn resolved;"""

    def _files(self):
        files = list(self.find_files("skills-*.js"))
        files += list(self.find_files("auth-profiles-*.js"))
        sdk = self.dist_dir / "plugin-sdk"
        if sdk.is_dir():
            files += list(sdk.glob("skills-*.js"))
            files += list(sdk.glob("auth-profiles-*.js"))
        return sorted(set(files))

    def _is_patched(self, data: str) -> bool:
        """Check if file is already patched by looking for artifacts reference"""
        return "path.join(configStateDir, \"artifacts\")" in data

    def check(self) -> PatchStatus:
        files = self._files()
        if not files:
            return PatchStatus.NOT_APPLIED
        patched = 0
        unknown = 0
        targets = 0
        for f in files:
            data = f.read_text(encoding="utf-8", errors="ignore")
            if "async function resolveAllowedTmpMediaPath(params)" not in data:
                continue
            targets += 1
            if self._is_patched(data):
                patched += 1
            elif not self.OLD_PATTERN.search(data):
                unknown += 1
        if targets == 0:
            return PatchStatus.NOT_APPLIED
        if patched == targets and unknown == 0:
            return PatchStatus.APPLIED
        if patched > 0 or unknown > 0:
            return PatchStatus.PARTIALLY_APPLIED
        return PatchStatus.NOT_APPLIED

    def apply(self) -> PatchResult:
        files_modified = []
        files_failed = []
        for f in self._files():
            try:
                data = f.read_text(encoding="utf-8", errors="ignore")
                if "async function resolveAllowedTmpMediaPath(params)" not in data:
                    continue
                if self._is_patched(data):
                    continue
                
                match = self.OLD_PATTERN.search(data)
                if not match:
                    files_failed.append(f)
                    continue
                
                # Get the captured group (e.g., "$1" or None)
                suffix = match.group(1) or ""
                new_block = self.NEW_BLOCK.replace("isPathInside$1", f"isPathInside{suffix}")
                
                self.backup_file(f)
                new_data = data[:match.start()] + new_block + data[match.end():]
                f.write_text(new_data, encoding="utf-8")
                files_modified.append(f)
            except Exception:
                files_failed.append(f)
        status = PatchStatus.APPLIED if not files_failed else (PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED)
        return PatchResult(status=status, files_modified=files_modified, files_failed=files_failed, message=f"patched={len(files_modified)} failed={len(files_failed)}")
