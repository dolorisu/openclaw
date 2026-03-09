"""Harden /reset cold-start prompt."""

from __future__ import annotations

from ..core import Patch, PatchResult, PatchStatus

TARGET = "const BARE_SESSION_RESET_PROMPT = "
NEW_PROMPT = (
    'const BARE_SESSION_RESET_PROMPT = "A new session was started via /new or /reset. '
    'Respond with one concise confirmation line only: \\\"✅ New session started.\\\" '
    'Do not greet, do not ask follow-up questions, and do not add extra guidance unless explicitly requested.";'
)


class ResetPromptPatch(Patch):
    name = "reset_prompt"
    description = "Harden /reset command handling"
    dependencies = []

    def _files(self):
        files = list(self.find_files("*.js"))
        sdk = self.dist_dir / "plugin-sdk"
        if sdk.is_dir():
            files += list(sdk.glob("*.js"))
        return sorted(set(files))

    def check(self) -> PatchStatus:
        files = self._files()
        candidates = 0
        patched = 0
        for f in files:
            data = f.read_text(encoding="utf-8", errors="ignore")
            if TARGET not in data and NEW_PROMPT not in data:
                continue
            candidates += 1
            if NEW_PROMPT in data:
                patched += 1
        if candidates == 0:
            return PatchStatus.NOT_APPLIED
        if patched == candidates:
            return PatchStatus.APPLIED
        if patched > 0:
            return PatchStatus.PARTIALLY_APPLIED
        return PatchStatus.NOT_APPLIED

    def apply(self) -> PatchResult:
        files_modified = []
        files_failed = []
        for f in self._files():
            try:
                data = f.read_text(encoding="utf-8", errors="ignore")
                if NEW_PROMPT in data or TARGET not in data:
                    continue
                idx = data.find(TARGET)
                end = data.find(";", idx)
                if idx < 0 or end < 0:
                    files_failed.append(f)
                    continue
                self.backup_file(f)
                patched = data[:idx] + NEW_PROMPT + data[end + 1 :]
                f.write_text(patched, encoding="utf-8")
                files_modified.append(f)
            except Exception:
                files_failed.append(f)
        status = PatchStatus.APPLIED if not files_failed else (PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED)
        return PatchResult(status=status, files_modified=files_modified, files_failed=files_failed, message=f"patched={len(files_modified)} failed={len(files_failed)}")
