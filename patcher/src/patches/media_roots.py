"""Allow media roots to include ~/.openclaw/artifacts."""

from __future__ import annotations

from pathlib import Path

from ..core import Patch, PatchResult, PatchStatus


OLD_BLOCK = """\treturn [
\t\toptions.preferredTmpDir ?? resolveCachedPreferredTmpDir(),
\t\tpath.join(resolvedStateDir, \"media\"),
\t\tpath.join(resolvedStateDir, \"agents\"),
\t\tpath.join(resolvedStateDir, \"workspace\"),
\t\tpath.join(resolvedStateDir, \"sandboxes\")
\t];"""

NEW_BLOCK = """\treturn [
\t\toptions.preferredTmpDir ?? resolveCachedPreferredTmpDir(),
\t\tpath.join(resolvedStateDir, \"media\"),
\t\tpath.join(resolvedStateDir, \"agents\"),
\t\tpath.join(resolvedStateDir, \"workspace\"),
\t\tpath.join(resolvedStateDir, \"sandboxes\"),
\t\tpath.join(resolvedStateDir, \"artifacts\")
\t];"""


class MediaRootsPatch(Patch):
    name = "media_roots"
    description = "Allow media local roots from ~/.openclaw/artifacts"
    dependencies = []

    def _files(self) -> list[Path]:
        files = set(self.find_files("fetch-*.js"))
        files |= set(self.find_files("auth-profiles-*.js"))
        sdk = self.dist_dir / "plugin-sdk"
        if sdk.is_dir():
            files |= set(sdk.glob("fetch-*.js"))
            files |= set(sdk.glob("auth-profiles-*.js"))
        return sorted(files)

    def check(self) -> PatchStatus:
        files = self._files()
        if not files:
            return PatchStatus.NOT_APPLIED
        patched = 0
        unknown = 0
        targets = 0
        for f in files:
            data = f.read_text(encoding="utf-8", errors="ignore")
            if "function buildMediaLocalRoots(stateDir, options = {})" not in data:
                continue
            targets += 1
            if NEW_BLOCK in data:
                patched += 1
            elif OLD_BLOCK not in data:
                unknown += 1
        if targets == 0:
            return PatchStatus.NOT_APPLIED
        target = targets
        if patched == target and unknown == 0:
            return PatchStatus.APPLIED
        if patched > 0 or unknown > 0:
            return PatchStatus.PARTIALLY_APPLIED
        return PatchStatus.NOT_APPLIED

    def apply(self) -> PatchResult:
        files_modified = []
        files_failed = []
        files = self._files()
        for f in files:
            try:
                data = f.read_text(encoding="utf-8", errors="ignore")
                if "function buildMediaLocalRoots(stateDir, options = {})" not in data:
                    continue
                if NEW_BLOCK in data:
                    continue
                if OLD_BLOCK not in data:
                    files_failed.append(f)
                    continue
                self.backup_file(f)
                f.write_text(data.replace(OLD_BLOCK, NEW_BLOCK, 1), encoding="utf-8")
                files_modified.append(f)
            except Exception:
                files_failed.append(f)
        status = PatchStatus.APPLIED if not files_failed else (PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED)
        return PatchResult(status=status, files_modified=files_modified, files_failed=files_failed, message=f"patched={len(files_modified)} failed={len(files_failed)}")
