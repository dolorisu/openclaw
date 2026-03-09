#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

TARGET = "const BARE_SESSION_RESET_PROMPT = "
NEW_PROMPT = (
    'const BARE_SESSION_RESET_PROMPT = "A new session was started via /new or /reset. '
    'Respond with one concise confirmation line only: \\"✅ New session started.\\" '
    'Do not greet, do not ask follow-up questions, and do not add extra guidance unless explicitly requested.";'
)


def discover_dist_dirs() -> list[Path]:
    out: set[Path] = set()
    home = Path.home()
    patterns = [
        home / ".local/share/mise/installs/node/*/lib/node_modules/openclaw/dist",
        home / ".nvm/versions/node/*/lib/node_modules/openclaw/dist",
        home / ".volta/tools/image/node/*/lib/node_modules/openclaw/dist",
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


def patch_file(path: Path) -> tuple[bool, str]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if NEW_PROMPT in text:
        return False, "already patched"
    idx = text.find(TARGET)
    if idx < 0:
        return False, "missing marker"
    end = text.find(";", idx)
    if end < 0:
        return False, "bad assignment"
    patched = text[:idx] + NEW_PROMPT + text[end + 1 :]
    path.write_text(patched, encoding="utf-8")
    return True, "patched"


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch reset cold-start prompt to concise confirmation")
    parser.add_argument("--status", action="store_true", help="Show patch status only")
    parser.add_argument("--dry-run", action="store_true", help="Show files that would be patched")
    args = parser.parse_args()

    patched = 0
    seen = 0
    candidates = 0
    for dist in discover_dist_dirs():
        files = list(dist.glob("*.js"))
        plugin_sdk = dist / "plugin-sdk"
        if plugin_sdk.is_dir():
            files += list(plugin_sdk.glob("*.js"))
        for f in files:
            seen += 1
            content = f.read_text(encoding="utf-8", errors="ignore")
            if TARGET not in content and NEW_PROMPT not in content:
                continue
            candidates += 1
            if args.status:
                status = "patched" if NEW_PROMPT in content else "unpatched"
                print(f"{status:9} {f}")
                continue
            if args.dry_run:
                if NEW_PROMPT not in content:
                    print(f"would_patch {f}")
                continue
            ok, note = patch_file(f)
            if ok:
                patched += 1
                print(f"patched {f}")
            else:
                print(f"skip {f} ({note})")

    if args.status:
        print(f"summary: files_seen={seen} candidates={candidates}")
    elif args.dry_run:
        print(f"summary: files_seen={seen} candidates={candidates}")
    else:
        print(f"summary: files_seen={seen} candidates={candidates} patched={patched}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
