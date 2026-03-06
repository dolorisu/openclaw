#!/usr/bin/env python3
"""
Portable OpenClaw multi-bubble patcher for WhatsApp and Telegram.

Patches compiled dist files so messages with double newlines (\n\n)
are sent as multiple bubbles in both delivery paths:
- deliver-*.js (tool/message path)
- channel-web-*.js + web-*.js (auto-reply group/direct path)

Supports: --channels whatsapp,telegram (default: both)

Designed to survive different OpenClaw install layouts.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Iterable

# Will be dynamically built based on --channels arg
DELIVER_MARKER_TEMPLATE = '({channel_checks}) && typeof text === "string" && text.includes("\\n\\n")'
WEB_PATCH_MARKER_A = 'const rawText = replyResult.text || "";'
WEB_PATCH_MARKER_B = 'const paragraphParts = rawText.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean);'
TELEGRAM_PATCH_MARKER = 'const markdownChunks = markdown.includes("\\n\\n") ? markdown.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean) : params.chunkMode === "newline" ? chunkMarkdownTextWithMode(markdown, params.textLimit, params.chunkMode) : [markdown];'


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

    home = Path.home()
    patterns = [
        home / ".local/share/mise/installs/node/*/lib/node_modules/openclaw/dist",
        home / ".nvm/versions/node/*/lib/node_modules/openclaw/dist",
        home / ".volta/tools/image/node/*/lib/node_modules/openclaw/dist",
        home / ".asdf/installs/nodejs/*/.npm/lib/node_modules/openclaw/dist",
        Path("/usr/local/lib/node_modules/openclaw/dist"),
        Path("/opt/homebrew/lib/node_modules/openclaw/dist"),
    ]

    for pattern in patterns:
        for match in map(Path, glob_paths(pattern)):
            if match.is_dir():
                candidates.add(match)

    for cmd in ("openclaw", "openclaw-gateway"):
        candidates |= dist_from_exec(cmd)

    npm = shutil.which("npm")
    if npm:
        npm_root = run([npm, "root", "-g"])
        if npm_root:
            dist = Path(npm_root) / "openclaw" / "dist"
            if dist.is_dir():
                candidates.add(dist)

    for root in extra_roots:
        if root.is_dir():
            for dist in root.rglob("node_modules/openclaw/dist"):
                if dist.is_dir():
                    candidates.add(dist)

    return sorted(candidates)


def backup_path(path: Path) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return path.with_suffix(path.suffix + f".bak.{ts}")


def build_deliver_patched(data: str, channels: list[str], force: bool = False) -> tuple[str | None, str]:
    # Build channel check: channel === "whatsapp" || channel === "telegram"
    channel_checks = " || ".join(f'channel === "{ch}"' for ch in channels)
    marker = f'({channel_checks}) && typeof text === "string" && text.includes("\\n\\n")'
    sendpayload_guard = (
        f'if (handler.sendPayload && effectivePayload.channelData && !(({channel_checks}) && '
        'payloadSummary.mediaUrls.length === 0 && typeof payloadSummary.text === "string" && '
        'payloadSummary.text.includes("\\n\\n"))) {'
    )
    
    # Check if exact patch already exists (split + sendPayload guard)
    if marker in data and sendpayload_guard in data:
        return None, "already patched (exact match)"

    # If split marker exists but sendPayload guard missing, upgrade in place
    if marker in data and sendpayload_guard not in data:
        upgraded = data.replace(
            'if (handler.sendPayload && effectivePayload.channelData) {',
            sendpayload_guard
        )
        if upgraded != data:
            return upgraded, "upgraded with sendPayload split guard"
    
    # Check if old patch exists (can upgrade with --force)
    old_patch_exists = 'channel === "whatsapp" && typeof text === "string" && text.includes("\\n\\n")' in data
    if old_patch_exists and not force:
        return None, "already patched (use --force to upgrade channels)"
    
    # If force mode and old patch exists, upgrade it
    if old_patch_exists and force:
        # Simple string replacement to upgrade channel check
        for ch in ["whatsapp", "telegram", "discord"]:  # common channels
            old = f'channel === "{ch}"'
            if old in data and old not in channel_checks:
                continue  # skip if not in new patch
            # Replace standalone channel check with multi-channel check
        upgraded = re.sub(
            r'channel === "(whatsapp)"( && typeof text)',
            f'({channel_checks})\\2',
            data
        )
        if upgraded != data:
            return upgraded, "upgraded from old patch"

    pattern = re.compile(
        r'(?P<i>^[ \t]*)const sendTextChunks = async \(text, overrides\) => \{\n(?P=i)[ \t]*throwIfAborted\(abortSignal\);\n',
        re.MULTILINE,
    )
    m = pattern.search(data)
    if not m:
        return None, "needle not found"

    indent = m.group("i")
    block = (
        f'{indent}\tif ({channel_checks} && typeof text === "string" && text.includes("\\n\\n")) {{\n'
        f'{indent}\t\tconst bubbles = text.split(/\\n\\n+/).map((s) => s.trim()).filter(Boolean);\n'
        f'{indent}\t\tfor (const bubble of bubbles) {{\n'
        f'{indent}\t\t\tthrowIfAborted(abortSignal);\n'
        f'{indent}\t\t\tresults.push(await handler.sendText(bubble, overrides));\n'
        f'{indent}\t\t}}\n'
        f'{indent}\t\treturn;\n'
        f'{indent}\t}}\n'
    )

    insert_at = m.end()
    patched = data[:insert_at] + block + data[insert_at:]
    upgraded = patched.replace(
        'if (handler.sendPayload && effectivePayload.channelData) {',
        sendpayload_guard
    )
    return upgraded, "patched"


def build_web_patched(text: str) -> tuple[str | None, str]:
    if "async function deliverWebReply(" not in text:
        return None, "no deliverWebReply"
    if WEB_PATCH_MARKER_A in text and WEB_PATCH_MARKER_B in text:
        return None, "already patched"

    lines = text.splitlines(keepends=True)

    start = None
    for i, line in enumerate(lines):
        if "async function deliverWebReply(" in line:
            start = i
            break
    if start is None:
        return None, "deliverWebReply not found"

    target = None
    for i in range(start, min(start + 260, len(lines))):
        if "const textChunks = chunkMarkdownTextWithMode(" in lines[i] and "replyResult.text" in lines[i]:
            target = i
            break
    if target is None:
        return None, "textChunks line not found"

    indent = lines[target][: len(lines[target]) - len(lines[target].lstrip())]
    replacement = [
        indent + 'const rawText = replyResult.text || "";\n',
        indent + 'const paragraphParts = rawText.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean);\n',
        indent
        + 'const textChunks = paragraphParts.flatMap((part) => chunkMarkdownTextWithMode(markdownToWhatsApp(convertMarkdownTables(part, tableMode)), textLimit, chunkMode));\n',
    ]

    patched_lines = lines[:target] + replacement + lines[target + 1 :]
    return "".join(patched_lines), "patched"


def build_telegram_bot_patched(text: str) -> tuple[str | None, str]:
    if "function buildChunkTextResolver(params)" not in text:
        return None, "no telegram chunk resolver"
    if TELEGRAM_PATCH_MARKER in text:
        return None, "already patched"

    old_line = 'const markdownChunks = params.chunkMode === "newline" ? chunkMarkdownTextWithMode(markdown, params.textLimit, params.chunkMode) : [markdown];'
    new_line = 'const markdownChunks = markdown.includes("\\n\\n") ? markdown.split(/\\n\\n+/).map((part) => part.trim()).filter(Boolean) : params.chunkMode === "newline" ? chunkMarkdownTextWithMode(markdown, params.textLimit, params.chunkMode) : [markdown];'
    if old_line not in text:
        return None, "telegram chunk line not found"
    return text.replace(old_line, new_line, 1), "patched"


def status_deliver(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    # Check if any variant of multi-bubble patch exists
    if ('channel === "whatsapp"' in data or 'channel === "telegram"' in data) and 'text.includes("\\n\\n")' in data:
        return "patched", "marker present"
    if "const sendTextChunks = async (text, overrides) => {" in data:
        return "unpatched", "sendTextChunks found"
    return "unknown", "signature not found"


def status_web(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if "async function deliverWebReply(" not in data:
        return "skip", "no deliverWebReply"
    if WEB_PATCH_MARKER_A in data and WEB_PATCH_MARKER_B in data:
        return "patched", "markers present"
    if "const textChunks = chunkMarkdownTextWithMode(" in data:
        return "unpatched", "legacy textChunks path"
    return "unknown", "signature not found"


def status_telegram_bot(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if "function buildChunkTextResolver(params)" not in data:
        return "skip", "no telegram chunk resolver"
    if TELEGRAM_PATCH_MARKER in data:
        return "patched", "marker present"
    if 'const markdownChunks = params.chunkMode === "newline" ? chunkMarkdownTextWithMode(markdown, params.textLimit, params.chunkMode) : [markdown];' in data:
        return "unpatched", "legacy chunk resolver"
    return "unknown", "signature not found"


def discover_telegram_chunk_files(dist: Path) -> list[Path]:
    files: set[Path] = set()
    files |= set(dist.glob("pi-embedded-*.js"))
    files |= set(dist.glob("reply-*.js"))
    files |= set(dist.glob("subagent-registry-*.js"))
    plugin_sdk = dist / "plugin-sdk"
    if plugin_sdk.is_dir():
        files |= set(plugin_sdk.glob("reply-*.js"))
    return sorted(files)


def restore_backups(backups: list[tuple[Path, Path]]) -> None:
    for target, bak in reversed(backups):
        if bak.exists():
            shutil.copy2(bak, target)


def patch_one(path: Path, kind: str, dry_run: bool, strict: bool, node_bin: str | None, channels: list[str], force: bool = False) -> tuple[str, str, tuple[Path, Path] | None]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if kind == "deliver":
        patched_data, note = build_deliver_patched(data, channels, force)
    elif kind == "web":
        patched_data, note = build_web_patched(data)
    else:
        patched_data, note = build_telegram_bot_patched(data)

    if patched_data is None:
        if note.startswith("already patched") or note == "no deliverWebReply" or note == "no telegram chunk resolver":
            return "skipped", note, None
        return "failed", note, None

    if dry_run:
        return "would_patch", "dry run", None

    bak = backup_path(path)
    shutil.copy2(path, bak)
    path.write_text(patched_data, encoding="utf-8")

    if strict:
        ok, note = node_syntax_check(path, node_bin)
        if not ok:
            shutil.copy2(bak, path)
            return "failed", f"syntax check failed: {note}", None

    return "patched", f"backup: {bak.name}", (path, bak)


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch OpenClaw dist bundles for multi-bubble split on WhatsApp/Telegram")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be patched")
    parser.add_argument("--status", action="store_true", help="Show patch status only")
    parser.add_argument("--strict", action="store_true", help="Run node syntax checks; rollback all changes on failure")
    parser.add_argument("--force", action="store_true", help="Force re-patch or upgrade existing patch to new channels")
    parser.add_argument(
        "--channels",
        default="whatsapp,telegram",
        help="Comma-separated list of channels to enable multi-bubble (default: whatsapp,telegram). Example: --channels whatsapp,telegram",
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        default=[],
        help="Extra root to recursively scan for node_modules/openclaw/dist",
    )
    args = parser.parse_args()
    
    # Parse channels
    channels = [ch.strip() for ch in args.channels.split(",") if ch.strip()]
    if not channels:
        print("Error: --channels cannot be empty")
        return 1

    if args.status and args.dry_run:
        print("Use either --status or --dry-run, not both.")
        return 2

    dist_dirs = discover_dist_dirs([Path(p).expanduser() for p in args.scan_root])
    if not dist_dirs:
        print("No OpenClaw dist directories found.")
        print("Tip: pass --scan-root /path/to/search")
        return 1

    print(f"Multi-bubble patch for channels: {', '.join(channels)}")
    print("\nDiscovered dist directories:")
    for d in dist_dirs:
        print(f"- {d}")

    if args.status:
        deliver_total = deliver_patched = deliver_unpatched = deliver_unknown = 0
        web_total = web_patched = web_unpatched = web_unknown = 0
        telegram_total = telegram_patched = telegram_unpatched = telegram_unknown = 0

        for dist in dist_dirs:
            deliver_files = sorted(dist.glob("deliver-*.js"))
            web_files = sorted(list(dist.glob("channel-web-*.js")) + list(dist.glob("web-*.js")))
            telegram_files = discover_telegram_chunk_files(dist)
            if deliver_files or web_files or telegram_files:
                print(f"\nStatus in: {dist}")

            for f in deliver_files:
                deliver_total += 1
                st, note = status_deliver(f)
                if st == "patched":
                    deliver_patched += 1
                elif st == "unpatched":
                    deliver_unpatched += 1
                else:
                    deliver_unknown += 1
                print(f"  deliver {st:9} {f.name} ({note})")

            for f in web_files:
                st, note = status_web(f)
                if st == "skip":
                    continue
                web_total += 1
                if st == "patched":
                    web_patched += 1
                elif st == "unpatched":
                    web_unpatched += 1
                else:
                    web_unknown += 1
                print(f"  web     {st:9} {f.name} ({note})")

            for f in telegram_files:
                st, note = status_telegram_bot(f)
                if st == "skip":
                    continue
                telegram_total += 1
                if st == "patched":
                    telegram_patched += 1
                elif st == "unpatched":
                    telegram_unpatched += 1
                else:
                    telegram_unknown += 1
                print(f"  tg-bot  {st:9} {f.name} ({note})")

        print("\nSummary:")
        print(f"- deliver files: {deliver_total} (patched: {deliver_patched}, unpatched: {deliver_unpatched}, unknown: {deliver_unknown})")
        print(f"- web files: {web_total} (patched: {web_patched}, unpatched: {web_unpatched}, unknown: {web_unknown})")
        print(f"- telegram bot files: {telegram_total} (patched: {telegram_patched}, unpatched: {telegram_unpatched}, unknown: {telegram_unknown})")
        return 0

    total = patched = skipped = failed = would = 0
    backups: list[tuple[Path, Path]] = []
    node_bin = find_node_binary() if args.strict and not args.dry_run else None

    for dist in dist_dirs:
        deliver_files = sorted(dist.glob("deliver-*.js"))
        web_files = sorted(list(dist.glob("channel-web-*.js")) + list(dist.glob("web-*.js")))
        telegram_files = discover_telegram_chunk_files(dist)
        files = [("deliver", f) for f in deliver_files] + [("web", f) for f in web_files] + [("telegram", f) for f in telegram_files]
        if not files:
            continue

        print(f"\nPatching in: {dist}")
        for kind, f in files:
            total += 1
            status, note, backup_info = patch_one(f, kind, args.dry_run, args.strict, node_bin, channels, args.force)
            if status == "patched":
                patched += 1
                if backup_info:
                    backups.append(backup_info)
            elif status == "skipped":
                skipped += 1
            elif status == "failed":
                failed += 1
            elif status == "would_patch":
                would += 1
            print(f"  {kind:7} {status:11} {f.name} ({note})")

            if status == "failed" and args.strict and not args.dry_run:
                print("\nStrict mode: failure detected, restoring patched files from backups...")
                restore_backups(backups)
                print("Rollback complete.")
                print("\nSummary:")
                print(f"- files seen: {total}")
                print(f"- patched: 0 (rolled back)")
                print(f"- skipped: {skipped}")
                print(f"- failed: {failed}")
                return 2

    print("\nSummary:")
    print(f"- files seen: {total}")
    if args.dry_run:
        print(f"- would patch: {would}")
    else:
        print(f"- patched: {patched}")
    print(f"- skipped: {skipped}")
    print(f"- failed: {failed}")

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
