"""Deduplicate WA outbound and buffer unmatched fence fragments."""

from __future__ import annotations

from ..core import Patch, PatchResult, PatchStatus

MARKER = "globalThis.__openclawWhatsAppDedupe"
INSERT_BEFORE = 'outboundLog.info(`Sending message -> ${redactedJid}${options.mediaUrl ? " (media)" : ""}`);\n'
PATCH_BLOCK = """\t\tif (typeof text === \"string\") {
\t\t\tif (/(^|\\n)Progress:\\s+/m.test(text) && /```/.test(text)) {
\t\t\t\ttext = text.trim().replace(/^```+\\n?/, \"\").replace(/\\n?```+$/, \"\").trim();
\t\t\t}
\t\t\tconst fenceStore = globalThis.__openclawFenceFragments ?? (globalThis.__openclawFenceFragments = new Map());
\t\t\tconst pending = fenceStore.get(redactedJid) || \"\";
\t\t\tconst merged = pending ? `${pending}\\n${text}` : text;
\t\t\tconst fenceCount = (merged.match(/```/g) || []).length;
\t\t\tif (fenceCount % 2 === 1) {
\t\t\t\tfenceStore.set(redactedJid, merged);
\t\t\t\tlogger.info({ jid: redactedJid }, \"buffer unmatched fenced fragment\");
\t\t\t\treturn {
\t\t\t\t\tmessageId: \"buffered-unmatched-fence\",
\t\t\t\t\ttoJid: jid
\t\t\t\t};
\t\t\t}
\t\t\tif (pending) {
\t\t\t\ttext = merged;
\t\t\t\tfenceStore.delete(redactedJid);
\t\t\t}
\t\t\tif (!options.mediaUrl) {
\t\t\t\tconst dedupeStore = globalThis.__openclawWhatsAppDedupe ?? (globalThis.__openclawWhatsAppDedupe = new Map());
\t\t\t\tconst dedupeKey = `${redactedJid}`;
\t\t\t\tconst dedupeText = text.trim();
\t\t\t\tconst now = Date.now();
\t\t\t\tconst prev = dedupeStore.get(dedupeKey);
\t\t\t\tif (dedupeText && prev && prev.text === dedupeText && now - prev.ts < 15000) {
\t\t\t\t\tlogger.info({ jid: redactedJid }, \"skip duplicate text message\");
\t\t\t\t\treturn {
\t\t\t\t\t\tmessageId: \"skipped-duplicate\",
\t\t\t\t\t\ttoJid: jid
\t\t\t\t\t};
\t\t\t\t}
\t\t\t\tdedupeStore.set(dedupeKey, { text: dedupeText, ts: now });
\t\t\t}
\t\t}
"""


class OutboundDedupePatch(Patch):
    name = "outbound_dedupe"
    description = "Deduplicate outbound messages"
    dependencies = []

    def _files(self):
        files = list(self.find_files("outbound-*.js"))
        sdk = self.dist_dir / "plugin-sdk"
        if sdk.is_dir():
            files += list(sdk.glob("outbound-*.js"))
        return sorted(set(files))

    def check(self) -> PatchStatus:
        files = self._files()
        if not files:
            return PatchStatus.NOT_APPLIED
        patched = 0
        candidates = 0
        for f in files:
            data = f.read_text(encoding="utf-8", errors="ignore")
            if INSERT_BEFORE not in data and MARKER not in data and "__openclawFenceFragments" not in data:
                continue
            candidates += 1
            if "__openclawFenceFragments" in data and MARKER in data:
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
                if "__openclawFenceFragments" in data and MARKER in data:
                    continue
                if INSERT_BEFORE not in data:
                    continue
                self.backup_file(f)
                patched = data.replace(INSERT_BEFORE, PATCH_BLOCK + INSERT_BEFORE, 1)
                f.write_text(patched, encoding="utf-8")
                files_modified.append(f)
            except Exception:
                files_failed.append(f)
        status = PatchStatus.APPLIED if not files_failed else (PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED)
        return PatchResult(status=status, files_modified=files_modified, files_failed=files_failed, message=f"patched={len(files_modified)} failed={len(files_failed)}")
