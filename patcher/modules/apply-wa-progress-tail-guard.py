#!/usr/bin/env python3
"""
Patch OpenClaw WhatsApp web delivery to avoid dangling sentence tails
during progress streaming updates.

What it changes:
- Keeps multi-bubble behavior (

 split) untouched.
- Buffers short trailing sentence fragments in progress updates and merges
  them into the next update/final message.

Target bundles:
- dist/channel-web-*.js

Discovery order:
1) npm root -g
2) resolve from openclaw binary path
3) common manager paths (nvm/mise/volta/asdf/homebrew)
4) optional --scan-root recursive search
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

HELPER_MARKER = "const TRAILING_SENTENCE_BOUNDARY_RE = /(?:\\n{2,}|[.!?](?:[\"')\\]]+)?\\s+)/g;"
TAIL_MARKER = "let pendingProgressTail = \"\";"
PROGRESS_PREVIEW_MARKER = "function shouldSendProgressPreviewText(text) {"
OLD_SPLIT_CORE = """\tconst normalized = text.replace(/\\r\\n?/g, \"\\n\");
\tif (normalized.length < 80) return {
\t\thead: normalized,
\t\ttail: \"\"
\t};
\tlet cut = -1;
\tfor (const match of normalized.matchAll(TRAILING_SENTENCE_BOUNDARY_RE)) cut = (match.index ?? 0) + match[0].length;
\tif (cut <= 0 || cut >= normalized.length) return {
\t\thead: normalized,
\t\ttail: \"\"
\t};
\tconst head = normalized.slice(0, cut).trimEnd();
\tconst tail = normalized.slice(cut).trimStart();
\tif (!tail || tail.length > 180 || /\\n{2,}/.test(tail) || /[.!?](?:[\"')\\]]+)?$/.test(tail.trimEnd())) return {
\t\thead: normalized,
\t\ttail: \"\"
\t};"""
NEW_SPLIT_CORE = """\tconst normalized = text.replace(/\\r\\n?/g, \"\\n\");
\tconst trimmed = normalized.trimEnd();
\tconst endsLikeSentence = /[.!?](?:[\"')\\]]+)?$/.test(trimmed);
\tif (normalized.length < 80) return {
\t\thead: normalized,
\t\ttail: \"\"
\t};
\tlet cut = -1;
\tfor (const match of normalized.matchAll(TRAILING_SENTENCE_BOUNDARY_RE)) cut = (match.index ?? 0) + match[0].length;
\tif (cut <= 0 || cut >= normalized.length) return {
\t\thead: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? \"\" : normalized,
\t\ttail: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? normalized : \"\"
\t};
\tconst head = normalized.slice(0, cut).trimEnd();
\tconst tail = normalized.slice(cut).trimStart();
\tif (!tail || tail.length > 220 || /\\n{2,}/.test(tail) || /[.!?](?:[\"')\\]]+)?$/.test(tail.trimEnd())) return {
\t\thead: normalized,
\t\ttail: \"\"
\t};"""
OLD_NEWEST_SPLIT_CORE = """\tconst normalized = text.replace(/\\r\\n?/g, "\\n");
\tconst trimmed = normalized.trimEnd();
\tconst endsLikeSentence = /[.!?](?:[\"')\\]]+)?$/.test(trimmed);
\tif (normalized.length < 80) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tlet cut = -1;
\tfor (const match of normalized.matchAll(TRAILING_SENTENCE_BOUNDARY_RE)) cut = (match.index ?? 0) + match[0].length;
\tif (cut <= 0 || cut >= normalized.length) return {
\t\thead: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? "" : normalized,
\t\ttail: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? normalized : ""
\t};
\tlet head = normalized.slice(0, cut).trimEnd();
\tlet tail = normalized.slice(cut).trimStart();
\tif (!tail || tail.length > 220 || /\\n{2,}/.test(tail) || /[.!?](?:[\"')\\]]+)?$/.test(tail.trimEnd())) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tconst headLastLine = head.split("\\n").pop()?.trim() ?? "";
\tif (/^\\d+\\.$/.test(headLastLine)) {
\t\thead = head.slice(0, head.length - headLastLine.length).trimEnd();
\t\ttail = joinProgressFragments(headLastLine, tail);
\t};"""
NEWEST_SPLIT_CORE = """\tconst normalized = text.replace(/\\r\\n?/g, "\\n");
\tconst trimmed = normalized.trimEnd();
\tconst endsLikeSentence = /[.!?](?:[\"')\\]]+)?$/.test(trimmed);
\tconst fenceCount = (normalized.match(/```/g) || []).length;
\tif (fenceCount % 2 === 1) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (fenceCount > 0) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tif (/^Tree\\b[^\\n]*:?$/.test(trimmed)) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (/^Command:\\s+/m.test(normalized) && !/^Evidence:\\s*/m.test(normalized)) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (/^Command:\\s+/m.test(normalized) || /^Evidence:\\s*/m.test(normalized) || /^Check\\s+/m.test(normalized)) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tif (normalized.length < 80) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tlet cut = -1;
\tfor (const match of normalized.matchAll(TRAILING_SENTENCE_BOUNDARY_RE)) cut = (match.index ?? 0) + match[0].length;
\tif (cut <= 0 || cut >= normalized.length) return {
\t\thead: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? "" : normalized,
\t\ttail: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? normalized : ""
\t};
\tlet head = normalized.slice(0, cut).trimEnd();
\tlet tail = normalized.slice(cut).trimStart();
\tif (!tail || tail.length > 220 || /\\n{2,}/.test(tail) || /[.!?](?:[\"')\\]]+)?$/.test(tail.trimEnd())) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tconst headLastLine = head.split("\\n").pop()?.trim() ?? "";
\tif (/^\\d+\\.$/.test(headLastLine)) {
\t\thead = head.slice(0, head.length - headLastLine.length).trimEnd();
\t\ttail = joinProgressFragments(headLastLine, tail);
\t};"""
OLD_ATOMIC_GUARD = """\tif (/```/.test(normalized) || /^Command:\\s+/m.test(normalized) || /^Evidence:\\s*/m.test(normalized) || /^Check\\s+/m.test(normalized)) return {
\t\thead: normalized,
\t\ttail: ""
\t};"""
NEW_ATOMIC_GUARD = """\tconst fenceCount = (normalized.match(/```/g) || []).length;
\tif (fenceCount % 2 === 1) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (fenceCount > 0) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tif (/^Tree\\b[^\\n]*:?$/.test(trimmed)) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (/^Command:\\s+/m.test(normalized) && !/^Evidence:\\s*/m.test(normalized)) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (/^Command:\\s+/m.test(normalized) || /^Evidence:\\s*/m.test(normalized) || /^Check\\s+/m.test(normalized)) return {
\t\thead: normalized,
\t\ttail: ""
\t};"""
NORMALIZED_SNIPPET = """\t\t\t\tconst normalizedPayload = isProgressUpdate ? {
\t\t\t\t\t...payload,
\t\t\t\t\ttext: sanitizeProgressUpdateText(normalizeProgressTextForWhatsApp(payload.text))
\t\t\t\t} : payload;
\t\t\t\tawait deliverWebReply({"""
NORMALIZED_PATCHED = """\t\t\t\tconst normalizedPayload = isProgressUpdate ? {
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
NORMALIZED_PATCHED_WITH_PREVIEW_GUARD = """\t\t\t\tif (isProgressUpdate && !shouldSendProgressPreviewText(payload.text) && !payload.mediaUrl && !payload.mediaUrls?.length) return;
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
function sanitizeProgressUpdateText(text) {
\tif (typeof text !== "string") return text;
\treturn text
\t\t.replace(/```+/g, "")
\t\t.replace(/^---+\\s*$/gm, "")
\t\t.replace(/\\n{3,}/g, "\\n\\n")
\t\t.trim();
}
function splitTrailingProgressFragment(text) {
\tif (!text) return {
\t\thead: "",
\t\ttail: ""
\t};
\tconst normalized = text.replace(/\\r\\n?/g, "\\n");
\tconst trimmed = normalized.trimEnd();
\tconst endsLikeSentence = /[.!?](?:[\"')\\]]+)?$/.test(trimmed);
\tconst fenceCount = (normalized.match(/```/g) || []).length;
\tif (fenceCount % 2 === 1) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (fenceCount > 0) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tif (/^Tree\\b[^\\n]*:?$/.test(trimmed)) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (/^Command:\\s+/m.test(normalized) && !/^Evidence:\\s*/m.test(normalized)) return {
\t\thead: "",
\t\ttail: normalized
\t};
\tif (/^Command:\\s+/m.test(normalized) || /^Evidence:\\s*/m.test(normalized) || /^Check\\s+/m.test(normalized)) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tif (normalized.length < 80) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tlet cut = -1;
\tfor (const match of normalized.matchAll(TRAILING_SENTENCE_BOUNDARY_RE)) cut = (match.index ?? 0) + match[0].length;
\tif (cut <= 0 || cut >= normalized.length) return {
\t\thead: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? "" : normalized,
\t\ttail: !endsLikeSentence && !/\\n{2,}/.test(normalized) ? normalized : ""
\t};
\tlet head = normalized.slice(0, cut).trimEnd();
\tlet tail = normalized.slice(cut).trimStart();
\tif (!tail || tail.length > 220 || /\\n{2,}/.test(tail) || /[.!?](?:[\"')\\]]+)?$/.test(tail.trimEnd())) return {
\t\thead: normalized,
\t\ttail: ""
\t};
\tconst headLastLine = head.split("\\n").pop()?.trim() ?? "";
\tif (/^\\d+\\.$/.test(headLastLine)) {
\t\thead = head.slice(0, head.length - headLastLine.length).trimEnd();
\t\ttail = joinProgressFragments(headLastLine, tail);
\t}
\treturn {
\t\thead,
\t\ttail
\t};
}
function shouldSendProgressPreviewText(text) {
\tif (typeof text !== "string") return true;
\tconst normalized = text.replace(/\\r\\n?/g, "\\n").trim();
\tif (!normalized) return false;
\tif (/```|~~~/.test(normalized)) return false;
	if (/^Progress:\\s+/m.test(normalized) && !/^Command:\\s+/m.test(normalized) && normalized.length < 220) return false;
\tif (normalized.length >= 260) return true;
\tif (/\\n{2,}/.test(normalized)) return true;
\tif (/^[\\s>*-]*\\d+[.)]\\s+/m.test(normalized) || /^[\\s>*-]*[-*+]\\s+/m.test(normalized)) return true;
\treturn false;
}
"""


def patch_normalized_payload_block_fallback(text: str) -> tuple[str | None, str]:
    start_token = 'const isProgressUpdate = info.kind !== "final";'
    reply_token = "replyResult: normalizedPayload,"
    msg_token = "msg: params.msg,"

    start = text.find(start_token)
    if start < 0:
        return None, "isProgressUpdate marker missing"
    reply_idx = text.find(reply_token, start)
    if reply_idx < 0:
        return None, "replyResult marker missing"
    msg_idx = text.find(msg_token, reply_idx)
    if msg_idx < 0:
        return None, "msg marker missing"

    new_block = """const isProgressUpdate = info.kind !== \"final\";
\t\t\t\tif (isProgressUpdate && !shouldSendProgressPreviewText(payload.text) && !payload.mediaUrl && !payload.mediaUrls?.length) return;
\t\t\t\tconst normalizedPayload = isProgressUpdate ? {
\t\t\t\t\t...payload,
\t\t\t\t\ttext: normalizeProgressTextForWhatsApp(payload.text)
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
\t\t\t\tawait deliverWebReply({
\t\t\t\t\treplyResult: normalizedPayload,
\t\t\t\t\t"""

    patched = text[:start] + new_block + text[msg_idx:]
    return patched, "patched via fallback"


def patch_no_final_fallback(text: str) -> tuple[str | None, str]:
    pattern = r'\t\tlogVerbose\("Auto-reply updates delivered without final payload"\);\s*\t\}'
    patched, count = re.subn(pattern, NO_FINAL_PATCHED, text, count=1)
    if count:
        return patched, "patched no-final via regex"
    return None, "queuedFinal tail snippet missing"


def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return ""


def find_node_binary() -> str | None:
    for candidate in (
        shutil.which("node"),
        str(Path.home() / ".local/share/mise/installs/node/24.14.0/bin/node"),
        str(Path.home() / ".nvm/current/bin/node"),
        "/usr/bin/node",
        "/usr/local/bin/node",
    ):
        if candidate and Path(candidate).exists():
            return candidate
    return None


def node_syntax_check(path: Path, node_bin: str | None) -> tuple[bool, str]:
    if not node_bin:
        return False, "node binary not found"
    proc = subprocess.run([node_bin, "--check", str(path)], capture_output=True, text=True)
    if proc.returncode == 0:
        return True, "ok"
    err = (proc.stderr or proc.stdout or "syntax check failed").strip().splitlines()
    msg = err[-1] if err else "syntax check failed"
    return False, msg


def dist_from_exec(exec_name: str) -> set[Path]:
    found: set[Path] = set()
    exe = shutil.which(exec_name)
    if not exe:
        return found
    p = Path(exe).resolve()
    for parent in p.parents:
        if parent.name == "openclaw" and parent.parent.name == "node_modules":
            dist = parent / "dist"
            if dist.is_dir():
                found.add(dist)
    return found


def glob_paths(pattern: Path) -> Iterable[Path]:
    text = str(pattern)
    if "*" in text:
        return Path("/").glob(text.lstrip("/"))
    p = Path(text)
    return [p] if p.exists() else []


def discover_dist_dirs(extra_roots: list[Path]) -> list[Path]:
    candidates: set[Path] = set()

    npm = shutil.which("npm")
    if npm:
        npm_root = run([npm, "root", "-g"])
        if npm_root:
            dist = Path(npm_root) / "openclaw" / "dist"
            if dist.is_dir():
                candidates.add(dist)

    for cmd in ("openclaw", "openclaw-gateway"):
        candidates |= dist_from_exec(cmd)

    home = Path.home()
    patterns = [
        home / ".local/share/mise/installs/node/*/lib/node_modules/openclaw/dist",
        home / ".nvm/versions/node/*/lib/node_modules/openclaw/dist",
        home / ".volta/tools/image/node/*/lib/node_modules/openclaw/dist",
        home / ".asdf/installs/nodejs/*/.npm/lib/node_modules/openclaw/dist",
        Path("/opt/homebrew/lib/node_modules/openclaw/dist"),
        Path("/usr/local/lib/node_modules/openclaw/dist"),
        home / ".npm-global/lib/node_modules/openclaw/dist",
    ]

    for pattern in patterns:
        for match in map(Path, glob_paths(pattern)):
            if match.is_dir():
                candidates.add(match)

    for root in extra_roots:
        if root.is_dir():
            for dist in root.rglob("node_modules/openclaw/dist"):
                if dist.is_dir():
                    candidates.add(dist)

    return sorted(candidates)


def backup_path(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_suffix(path.suffix + f".bak.{ts}")


def patch_content(text: str) -> tuple[str | None, str]:
    if "async function deliverWebReply(" not in text:
        return None, "deliverWebReply not found"

    patched = text

    if HELPER_MARKER not in patched:
        anchor = "async function deliverWebReply(params) {"
        idx = patched.find(anchor)
        if idx < 0:
            return None, "deliverWebReply anchor missing"
        patched = patched[:idx] + HELPER_BLOCK + patched[idx:]

    if OLD_SPLIT_CORE in patched:
        patched = patched.replace(OLD_SPLIT_CORE, NEW_SPLIT_CORE, 1)
    if NEW_SPLIT_CORE in patched:
        patched = patched.replace(NEW_SPLIT_CORE, NEWEST_SPLIT_CORE, 1)
    if OLD_NEWEST_SPLIT_CORE in patched:
        patched = patched.replace(OLD_NEWEST_SPLIT_CORE, NEWEST_SPLIT_CORE, 1)
    if TAIL_MARKER not in patched:
        marker = "\tlet didSendReply = false;"
        if marker not in patched:
            return None, "didSendReply marker missing"
        patched = patched.replace(marker, marker + "\n\t" + TAIL_MARKER, 1)

    if PROGRESS_PREVIEW_MARKER not in patched:
        anchor = "async function deliverWebReply(params) {"
        idx = patched.find(anchor)
        if idx < 0:
            return None, "deliverWebReply anchor missing for preview helper"
        helper_fn = """function shouldSendProgressPreviewText(text) {
\tif (typeof text !== \"string\") return true;
\tconst normalized = text.replace(/\\r\\n?/g, \"\\n\").trim();
\tif (!normalized) return false;
\tif (/```|~~~/.test(normalized)) return false;
	if (/^Progress:\\s+/m.test(normalized) && !/^Command:\\s+/m.test(normalized) && normalized.length < 220) return false;
\tif (normalized.length >= 260) return true;
\tif (/\\n{2,}/.test(normalized)) return true;
\tif (/^[\\s>*-]*\\d+[.)]\\s+/m.test(normalized) || /^[\\s>*-]*[-*+]\\s+/m.test(normalized)) return true;
\treturn false;
}
"""
        patched = patched[:idx] + helper_fn + patched[idx:]

    old_preview_fn = r"""function shouldSendProgressPreviewText(text) {
	if (typeof text !== "string") return true;
	const normalized = text.replace(/\r\n?/g, "\n").trim();
	if (!normalized) return false;
	if (normalized.length >= 260) return true;
	if (/\n{2,}/.test(normalized)) return true;
	if (/^[\s>*-]*\d+[.)]\s+/m.test(normalized) || /^[\s>*-]*[-*+]\s+/m.test(normalized)) return true;
	return false;
}
"""
    new_preview_fn = r"""function shouldSendProgressPreviewText(text) {
	if (typeof text !== "string") return true;
	const normalized = text.replace(/\r\n?/g, "\n").trim();
	if (!normalized) return false;
	if (/```|~~~/.test(normalized)) return false;
	if (/^Progress:\s+/m.test(normalized) && !/^Command:\s+/m.test(normalized) && normalized.length < 220) return false;
	if (normalized.length >= 260) return true;
	if (/\n{2,}/.test(normalized)) return true;
	if (/^[\s>*-]*\d+[.)]\s+/m.test(normalized) || /^[\s>*-]*[-*+]\s+/m.test(normalized)) return true;
	return false;
}
"""
    if old_preview_fn in patched and new_preview_fn not in patched:
        patched = patched.replace(old_preview_fn, new_preview_fn, 1)

    if NORMALIZED_PATCHED_WITH_PREVIEW_GUARD not in patched:
        if NORMALIZED_PATCHED in patched:
            patched = patched.replace(NORMALIZED_PATCHED, NORMALIZED_PATCHED_WITH_PREVIEW_GUARD, 1)
        elif NORMALIZED_SNIPPET in patched:
            patched = patched.replace(NORMALIZED_SNIPPET, NORMALIZED_PATCHED_WITH_PREVIEW_GUARD, 1)
        else:
            fallback, _ = patch_normalized_payload_block_fallback(patched)
            if fallback is None:
                return None, "normalized payload snippet missing"
            patched = fallback

    if NO_FINAL_PATCHED not in patched:
        if NO_FINAL_SNIPPET not in patched:
            fallback, _ = patch_no_final_fallback(patched)
            if fallback is None:
                return None, "queuedFinal tail snippet missing"
            patched = fallback
        else:
            patched = patched.replace(NO_FINAL_SNIPPET, NO_FINAL_PATCHED, 1)

    if patched == text:
        return None, "already patched"
    return patched, "patched"


def patch_one(path: Path, dry_run: bool, strict: bool, node_bin: str | None) -> tuple[str, str, tuple[Path, Path] | None]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    patched_data, note = patch_content(data)
    if patched_data is None:
        if note == "already patched":
            return "skipped", note, None
        if note in {
            "normalized payload snippet missing",
            "queuedFinal tail snippet missing",
            "didSendReply marker missing",
            "deliverWebReply anchor missing",
            "deliverWebReply anchor missing for preview helper",
        }:
            return "skipped", f"incompatible bundle ({note})", None
        return "failed", note, None

    if dry_run:
        return "would_patch", "dry run", None

    bak = backup_path(path)
    shutil.copy2(path, bak)
    path.write_text(patched_data, encoding="utf-8")

    if strict:
        ok, syntax_note = node_syntax_check(path, node_bin)
        if not ok:
            shutil.copy2(bak, path)
            return "failed", f"syntax check failed: {syntax_note}", None

    return "patched", f"backup: {bak.name}", (path, bak)


def status_for(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if "async function deliverWebReply(" not in data:
        return "skip", "no deliverWebReply"
    has_helper = HELPER_MARKER in data
    has_tail = TAIL_MARKER in data
    has_preview = PROGRESS_PREVIEW_MARKER in data
    if has_helper and has_tail and has_preview:
        return "patched", "markers present"
    return "unpatched", f"helper={has_helper}, tail={has_tail}, preview={has_preview}"


def restore_backups(backups: list[tuple[Path, Path]]) -> None:
    for target, bak in reversed(backups):
        if bak.exists():
            shutil.copy2(bak, target)


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch WhatsApp progress streaming to avoid sentence tail split")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be patched")
    parser.add_argument("--status", action="store_true", help="Show patch status only")
    parser.add_argument("--strict", action="store_true", help="Run node --check and rollback on failure")
    parser.add_argument(
        "--scan-root",
        action="append",
        default=[],
        help="Extra root to recursively scan for node_modules/openclaw/dist",
    )
    args = parser.parse_args()

    if args.status and args.dry_run:
        print("Use either --status or --dry-run, not both.")
        return 2

    dist_dirs = discover_dist_dirs([Path(p).expanduser() for p in args.scan_root])
    if not dist_dirs:
        print("No OpenClaw dist directories found.")
        print("Tip: pass --scan-root /path/to/search")
        return 1

    print("Discovered dist directories:")
    for d in dist_dirs:
        print(f"- {d}")

    if args.status:
        total = patched = unpatched = unknown = 0
        for dist in dist_dirs:
            files = sorted(dist.glob("channel-web-*.js"))
            if not files:
                continue
            print(f"\nStatus in: {dist}")
            for f in files:
                st, note = status_for(f)
                if st == "skip":
                    continue
                total += 1
                if st == "patched":
                    patched += 1
                elif st == "unpatched":
                    unpatched += 1
                else:
                    unknown += 1
                print(f"  {st:9} {f.name} ({note})")
        print("\nSummary:")
        print(f"- files seen: {total}")
        print(f"- patched: {patched}")
        print(f"- unpatched: {unpatched}")
        print(f"- unknown: {unknown}")
        return 0

    total = patched_count = skipped = failed = would = 0
    backups: list[tuple[Path, Path]] = []
    node_bin = find_node_binary() if args.strict and not args.dry_run else None

    for dist in dist_dirs:
        files = sorted(dist.glob("channel-web-*.js"))
        if not files:
            continue
        print(f"\nPatching in: {dist}")
        for f in files:
            total += 1
            st, note, backup = patch_one(f, args.dry_run, args.strict, node_bin)
            if st == "patched":
                patched_count += 1
                if backup:
                    backups.append(backup)
            elif st == "skipped":
                skipped += 1
            elif st == "failed":
                failed += 1
            elif st == "would_patch":
                would += 1
            print(f"  {st:11} {f.name} ({note})")
            if st == "failed" and args.strict and not args.dry_run:
                print("\nStrict mode failure; restoring backups...")
                restore_backups(backups)
                print("Rollback complete.")
                return 2

    print("\nSummary:")
    print(f"- files seen: {total}")
    if args.dry_run:
        print(f"- would patch: {would}")
    else:
        print(f"- patched: {patched_count}")
    print(f"- skipped: {skipped}")
    print(f"- failed: {failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
