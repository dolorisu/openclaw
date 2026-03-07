#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


MARKER = "globalThis.__openclawWhatsAppDedupe"

INSERT_BEFORE = 'outboundLog.info(`Sending message -> ${redactedJid}${options.mediaUrl ? " (media)" : ""}`);\n'

OLD_PATCH_BLOCK = """\t\tif (typeof text === "string") {
\t\t\tconst fenceCount = (text.match(/```/g) || []).length;
\t\t\tif (fenceCount % 2 === 1) {
\t\t\t\tlogger.info({ jid: redactedJid }, "skip unmatched fenced message");
\t\t\t\treturn {
\t\t\t\t\tmessageId: "skipped-unmatched-fence",
\t\t\t\t\ttoJid: jid
\t\t\t\t};
\t\t\t}
\t\t\tif (!options.mediaUrl) {
\t\t\t\tconst dedupeStore = globalThis.__openclawWhatsAppDedupe ?? (globalThis.__openclawWhatsAppDedupe = new Map());
\t\t\t\tconst dedupeKey = `${redactedJid}`;
\t\t\t\tconst dedupeText = text.trim();
\t\t\t\tconst now = Date.now();
\t\t\t\tconst prev = dedupeStore.get(dedupeKey);
\t\t\t\tif (dedupeText && prev && prev.text === dedupeText && now - prev.ts < 15000) {
\t\t\t\t\tlogger.info({ jid: redactedJid }, "skip duplicate text message");
\t\t\t\t\treturn {
\t\t\t\t\t\tmessageId: "skipped-duplicate",
\t\t\t\t\t\ttoJid: jid
\t\t\t\t\t};
\t\t\t\t}
\t\t\t\tdedupeStore.set(dedupeKey, { text: dedupeText, ts: now });
\t\t\t}
\t\t}
"""

PATCH_BLOCK = """\t\tif (typeof text === "string") {
\t\t\tconst fenceStore = globalThis.__openclawFenceFragments ?? (globalThis.__openclawFenceFragments = new Map());
\t\t\tconst pending = fenceStore.get(redactedJid) || "";
\t\t\tconst merged = pending ? `${pending}\n${text}` : text;
\t\t\tconst fenceCount = (merged.match(/```/g) || []).length;
\t\t\tif (fenceCount % 2 === 1) {
\t\t\t\tfenceStore.set(redactedJid, merged);
\t\t\t\tlogger.info({ jid: redactedJid }, "buffer unmatched fenced fragment");
\t\t\t\treturn {
\t\t\t\t\tmessageId: "buffered-unmatched-fence",
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
\t\t\t\t\tlogger.info({ jid: redactedJid }, "skip duplicate text message");
\t\t\t\t\treturn {
\t\t\t\t\t\tmessageId: "skipped-duplicate",
\t\t\t\t\t\ttoJid: jid
\t\t\t\t\t};
\t\t\t\t}
\t\t\t\tdedupeStore.set(dedupeKey, { text: dedupeText, ts: now });
\t\t\t}
\t\t}
"""

BROKEN_PATCH_BLOCK_V2 = """\t\tif (typeof text === "string") {
\t\t\tif ((/^|\\n)Progress:\\s+/m.test(text) && /```/.test(text)) {
\t\t\t\ttext = text.trim().replace(/^```+\\n?/, "").replace(/\\n?```+$/, "").trim();
\t\t\t}
\t\t\tconst fenceStore = globalThis.__openclawFenceFragments ?? (globalThis.__openclawFenceFragments = new Map());
\t\t\tconst pending = fenceStore.get(redactedJid) || "";
\t\t\tconst merged = pending ? `${pending}\\n${text}` : text;
\t\t\tconst fenceCount = (merged.match(/```/g) || []).length;
\t\t\tif (fenceCount % 2 === 1) {
\t\t\t\tfenceStore.set(redactedJid, merged);
\t\t\t\tlogger.info({ jid: redactedJid }, "buffer unmatched fenced fragment");
\t\t\t\treturn {
\t\t\t\t\tmessageId: "buffered-unmatched-fence",
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
\t\t\t\t\tlogger.info({ jid: redactedJid }, "skip duplicate text message");
\t\t\t\t\treturn {
\t\t\t\t\t\tmessageId: "skipped-duplicate",
\t\t\t\t\t\ttoJid: jid
\t\t\t\t\t};
\t\t\t\t}
\t\t\t\tdedupeStore.set(dedupeKey, { text: dedupeText, ts: now });
\t\t\t}
\t\t}
"""

PATCH_BLOCK_V2 = """\t\tif (typeof text === "string") {
\t\t\tif (/(^|\\n)Progress:\\s+/m.test(text) && /```/.test(text)) {
\t\t\t\ttext = text.trim().replace(/^```+\\n?/, "").replace(/\\n?```+$/, "").trim();
\t\t\t}
\t\t\tconst fenceStore = globalThis.__openclawFenceFragments ?? (globalThis.__openclawFenceFragments = new Map());
\t\t\tconst pending = fenceStore.get(redactedJid) || "";
\t\t\tconst merged = pending ? `${pending}\\n${text}` : text;
\t\t\tconst fenceCount = (merged.match(/```/g) || []).length;
\t\t\tif (fenceCount % 2 === 1) {
\t\t\t\tfenceStore.set(redactedJid, merged);
\t\t\t\tlogger.info({ jid: redactedJid }, "buffer unmatched fenced fragment");
\t\t\t\treturn {
\t\t\t\t\tmessageId: "buffered-unmatched-fence",
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
\t\t\t\t\tlogger.info({ jid: redactedJid }, "skip duplicate text message");
\t\t\t\t\treturn {
\t\t\t\t\t\tmessageId: "skipped-duplicate",
\t\t\t\t\t\ttoJid: jid
\t\t\t\t\t};
\t\t\t\t}
\t\t\t\tdedupeStore.set(dedupeKey, { text: dedupeText, ts: now });
\t\t\t}
\t\t}
"""


def discover_dist_dirs() -> list[Path]:
    out: set[Path] = set()

    home = Path.home()
    patterns = [
        home / ".local/share/mise/installs/node/*/lib/node_modules/openclaw/dist",
        home / ".nvm/versions/node/*/lib/node_modules/openclaw/dist",
        home / ".volta/tools/image/node/*/lib/node_modules/openclaw/dist",
        home / ".asdf/installs/nodejs/*/.npm/lib/node_modules/openclaw/dist",
        Path("/opt/homebrew/lib/node_modules/openclaw/dist"),
        Path("/usr/local/lib/node_modules/openclaw/dist"),
    ]
    for pattern in patterns:
        if "*" in str(pattern):
            for dist in Path("/").glob(str(pattern).lstrip("/")):
                if dist.is_dir():
                    out.add(dist)
        elif pattern.is_dir():
            out.add(pattern)

    npm = shutil.which("npm")
    if npm:
        try:
            npm_root = subprocess.check_output([npm, "root", "-g"], text=True, stderr=subprocess.DEVNULL).strip()
        except Exception:
            npm_root = ""
        if npm_root:
            dist = Path(npm_root) / "openclaw" / "dist"
            if dist.is_dir():
                out.add(dist)

    return sorted(out)


def patch_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if BROKEN_PATCH_BLOCK_V2 in text and PATCH_BLOCK_V2 not in text:
        path.write_text(text.replace(BROKEN_PATCH_BLOCK_V2, PATCH_BLOCK_V2, 1), encoding="utf-8")
        return True
    if PATCH_BLOCK in text and PATCH_BLOCK_V2 not in text:
        path.write_text(text.replace(PATCH_BLOCK, PATCH_BLOCK_V2, 1), encoding="utf-8")
        return True
    if OLD_PATCH_BLOCK in text and PATCH_BLOCK not in text:
        path.write_text(text.replace(OLD_PATCH_BLOCK, PATCH_BLOCK, 1), encoding="utf-8")
        return True
    if MARKER in text:
        return False
    if INSERT_BEFORE not in text:
        return False
    patched = text.replace(INSERT_BEFORE, PATCH_BLOCK + INSERT_BEFORE, 1)
    path.write_text(patched, encoding="utf-8")
    return True


def status_file(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "__openclawFenceFragments" in text and MARKER in text:
        return "patched"
    if MARKER in text or "skip unmatched fenced message" in text:
        return "legacy"
    if INSERT_BEFORE in text:
        return "unpatched"
    return "skip"


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch WA outbound dedupe and fence fragment buffering")
    parser.add_argument("--status", action="store_true", help="Show patch status only")
    parser.add_argument("--dry-run", action="store_true", help="Show files that would be patched")
    args = parser.parse_args()

    if args.status and args.dry_run:
        print("Use either --status or --dry-run, not both.")
        return 2

    patched = 0
    would_patch = 0
    seen = 0
    status_totals = {"patched": 0, "legacy": 0, "unpatched": 0, "skip": 0}
    for dist in discover_dist_dirs():
        files = list(dist.glob("outbound-*.js"))
        plugin_sdk = dist / "plugin-sdk"
        if plugin_sdk.is_dir():
            files += list(plugin_sdk.glob("outbound-*.js"))
        for path in files:
            seen += 1
            if args.status:
                st = status_file(path)
                status_totals[st] += 1
                if st != "skip":
                    print(f"{st:9} {path}")
                continue
            if args.dry_run:
                st = status_file(path)
                if st in {"unpatched", "legacy"}:
                    would_patch += 1
                    print(f"would_patch {path}")
                continue
            if patch_file(path):
                patched += 1
                print(f"patched {path}")

    if args.status:
        print(
            "summary: "
            f"seen={seen} patched={status_totals['patched']} legacy={status_totals['legacy']} "
            f"unpatched={status_totals['unpatched']} skip={status_totals['skip']}"
        )
        return 0

    if args.dry_run:
        print(f"summary: seen={seen} would_patch={would_patch}")
        return 0

    print(f"summary: seen={seen} patched={patched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
