"""Allow media send paths from ~/.openclaw/media and ~/.openclaw/artifacts."""

from __future__ import annotations

from ..core import Patch, PatchResult, PatchStatus

OLD_BLOCK = """\tconst openClawTmpDir = path.resolve(resolvePreferredOpenClawTmpDir());
\tif (!isPathInside(openClawTmpDir, resolved)) return;
\tawait assertNoTmpAliasEscape({
\t\tfilePath: resolved,
\t\ttmpRoot: openClawTmpDir
\t});
\treturn resolved;"""

NEW_BLOCK = """\tconst openClawTmpDir = path.resolve(resolvePreferredOpenClawTmpDir());
\tconst configStateDir = path.resolve(CONFIG_DIR);
\tconst mediaStateDir = path.join(configStateDir, \"media\");
\tconst artifactsStateDir = path.join(configStateDir, \"artifacts\");
\tconst allowedRoot = [openClawTmpDir, mediaStateDir, artifactsStateDir].find((root) => isPathInside(root, resolved));
\tif (!allowedRoot) return;
\tif (allowedRoot === openClawTmpDir) {
\t\tawait assertNoTmpAliasEscape({
\t\t\tfilePath: resolved,
\t\t\ttmpRoot: openClawTmpDir
\t\t});
\t}
\treturn resolved;"""


class MediaSendPathsPatch(Patch):
    name = "media_send_paths"
    description = "Allow send attachment paths from ~/.openclaw/media and ~/.openclaw/artifacts"
    dependencies = ["media_roots"]

    def _files(self):
        files = list(self.find_files("skills-*.js"))
        sdk = self.dist_dir / "plugin-sdk"
        if sdk.is_dir():
            files += list(sdk.glob("skills-*.js"))
        return sorted(set(files))

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
            if "path.join(configStateDir, \"artifacts\")" in data:
                patched += 1
            elif OLD_BLOCK not in data:
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
                if "path.join(configStateDir, \"artifacts\")" in data:
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
