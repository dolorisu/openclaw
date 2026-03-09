"""Guard WA progressive updates from sending dangling tails."""

from __future__ import annotations

from ..core import Patch, PatchResult, PatchStatus

HELPER_MARKER = "const TRAILING_SENTENCE_BOUNDARY_RE = /(?:\\n{2,}|[.!?](?:[\"')\\]]+)?\\s+)/g;"
TAIL_MARKER = "let pendingProgressTail = \"\";"
PREVIEW_MARKER = "function shouldSendProgressPreviewText(text) {"
NORMALIZED_SNIPPET = """\t\t\t\tconst normalizedPayload = isProgressUpdate ? {
\t\t\t\t\t...payload,
\t\t\t\t\ttext: sanitizeProgressUpdateText(normalizeProgressTextForWhatsApp(payload.text))
\t\t\t\t} : payload;
\t\t\t\tawait deliverWebReply({"""
NORMALIZED_PATCHED = """\t\t\t\tif (isProgressUpdate && !shouldSendProgressPreviewText(payload.text) && !payload.mediaUrl && !payload.mediaUrls?.length) return;
\t\t\t\tconst normalizedPayload = isProgressUpdate ? {
\t\t\t\t\t...payload,
\t\t\t\t\ttext: sanitizeProgressUpdateText(normalizeProgressTextForWhatsApp(payload.text))
\t\t\t\t} : payload;
\t\t\t\tif (isProgressUpdate && typeof normalizedPayload.text === \"string\") {
\t\t\t\t\tconst mergedText = joinProgressFragments(pendingProgressTail, normalizedPayload.text);
\t\t\t\t\tconst split = splitTrailingProgressFragment(mergedText);
\t\t\t\t\tpendingProgressTail = split.tail;
\t\t\t\t\tnormalizedPayload.text = split.head;
\t\t\t\t\tif (!normalizedPayload.text.trim() && !normalizedPayload.mediaUrl && !normalizedPayload.mediaUrls?.length) return;
\t\t\t\t} else if (!isProgressUpdate && typeof normalizedPayload.text === \"string\" && pendingProgressTail) {
\t\t\t\t\tnormalizedPayload.text = joinProgressFragments(pendingProgressTail, normalizedPayload.text);
\t\t\t\t\tpendingProgressTail = \"\";
\t\t\t\t}
\t\t\t\tawait deliverWebReply({"""
NO_FINAL_SNIPPET = """\t\tlogVerbose(\"Auto-reply updates delivered without final payload\");
\t}"""
NO_FINAL_PATCHED = """\t\tlogVerbose(\"Auto-reply updates delivered without final payload\");
\t\tif (pendingProgressTail.trim()) {
\t\t\tawait deliverWebReply({
\t\t\t\treplyResult: {
\t\t\t\t\ttext: pendingProgressTail
\t\t\t\t},
\t\t\t\tmsg: params.msg,
\t\t\t\tmediaLocalRoots,
\t\t\t\tmaxMediaBytes: params.maxMediaBytes,
\t\t\t\ttextLimit,
\t\t\t\tchunkMode,
\t\t\t\treplyLogger: params.replyLogger,
\t\t\t\tconnectionId: params.connectionId,
\t\t\t\tskipLog: false,
\t\t\t\ttableMode
\t\t\t});
\t\t\tdidSendReply = true;
\t\t\tparams.rememberSentText(pendingProgressTail, {
\t\t\t\tcombinedBody,
\t\t\t\tcombinedBodySessionKey: params.route.sessionKey,
\t\t\t\tlogVerboseMessage: true
\t\t\t});
\t\t\tpendingProgressTail = \"\";
\t\t}
\t}"""
HELPER_BLOCK = """const TRAILING_SENTENCE_BOUNDARY_RE = /(?:\\n{2,}|[.!?](?:[\"')\\]]+)?\\s+)/g;
function joinProgressFragments(prefix, suffix) {
\tif (!prefix) return suffix;
\tif (!suffix) return prefix;
\tconst needsSpace = !/[\\s([{"'`-]$/.test(prefix) && !/^[\\s,.;:!?)}\\]\"'`-]/.test(suffix);
\treturn needsSpace ? `${prefix} ${suffix}` : `${prefix}${suffix}`;
}
function splitTrailingProgressFragment(text) {
\tif (!text) return { head: \"\", tail: \"\" };
\tconst normalized = text.replace(/\\r\\n?/g, \"\\n\");
\tif (/```|~~~/.test(normalized)) return { head: normalized, tail: \"\" };
\tconst trimmed = normalized.trimEnd();
\tif (trimmed.length < 80) return { head: normalized, tail: \"\" };
\tlet cut = -1;
\tfor (const match of normalized.matchAll(TRAILING_SENTENCE_BOUNDARY_RE)) cut = (match.index ?? 0) + match[0].length;
\tif (cut <= 0 || cut >= normalized.length) return { head: normalized, tail: \"\" };
\tconst head = normalized.slice(0, cut).trimEnd();
\tconst tail = normalized.slice(cut).trimStart();
\tif (!tail || tail.length > 220 || /\\n{2,}/.test(tail) || /[.!?](?:[\"')\\]]+)?$/.test(tail.trimEnd())) return { head: normalized, tail: \"\" };
\treturn { head, tail };
}
function shouldSendProgressPreviewText(text) {
\tif (typeof text !== \"string\") return true;
\tconst normalized = text.replace(/\\r\\n?/g, \"\\n\").trim();
\tif (!normalized) return false;
\tif (/```|~~~/.test(normalized)) return false;
\tif (/^Progress:\\s+/m.test(normalized) && !/^Command:\\s+/m.test(normalized) && normalized.length < 220) return false;
\tif (normalized.length >= 260) return true;
\tif (/\\n{2,}/.test(normalized)) return true;
\tif (/^[\\s>*-]*\\d+[.)]\\s+/m.test(normalized) || /^[\\s>*-]*[-*+]\\s+/m.test(normalized)) return true;
\treturn false;
}
"""


class TailGuardPatch(Patch):
    name = "tail_guard"
    description = "Prevent splitting short progress fragments"
    dependencies = []

    def _files(self):
        return sorted(self.find_files("channel-web-*.js"))

    def check(self) -> PatchStatus:
        files = self._files()
        if not files:
            return PatchStatus.APPLIED
        patched = 0
        candidates = 0
        for f in files:
            data = f.read_text(encoding="utf-8", errors="ignore")
            if (
                HELPER_MARKER in data
                or TAIL_MARKER in data
                or PREVIEW_MARKER in data
                or NORMALIZED_SNIPPET in data
                or NORMALIZED_PATCHED in data
                or NO_FINAL_SNIPPET in data
                or NO_FINAL_PATCHED in data
            ):
                candidates += 1
                if HELPER_MARKER in data and TAIL_MARKER in data and PREVIEW_MARKER in data:
                    patched += 1
        if candidates == 0:
            return PatchStatus.APPLIED
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
                patched = data
                if HELPER_MARKER not in patched:
                    anchor = "async function deliverWebReply(params) {"
                    i = patched.find(anchor)
                    if i < 0:
                        continue
                    patched = patched[:i] + HELPER_BLOCK + patched[i:]
                if TAIL_MARKER not in patched:
                    marker = "\tlet didSendReply = false;"
                    if marker not in patched:
                        continue
                    patched = patched.replace(marker, marker + "\n\t" + TAIL_MARKER, 1)
                if NORMALIZED_PATCHED not in patched:
                    if NORMALIZED_SNIPPET not in patched:
                        continue
                    patched = patched.replace(NORMALIZED_SNIPPET, NORMALIZED_PATCHED, 1)
                if NO_FINAL_PATCHED not in patched:
                    if NO_FINAL_SNIPPET not in patched:
                        continue
                    patched = patched.replace(NO_FINAL_SNIPPET, NO_FINAL_PATCHED, 1)
                if patched != data:
                    self.backup_file(f)
                    f.write_text(patched, encoding="utf-8")
                    files_modified.append(f)
            except Exception:
                files_failed.append(f)
        status = PatchStatus.APPLIED if not files_failed else (PatchStatus.PARTIALLY_APPLIED if files_modified else PatchStatus.FAILED)
        return PatchResult(status=status, files_modified=files_modified, files_failed=files_failed, message=f"patched={len(files_modified)} failed={len(files_failed)}")
