#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


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


def discover_files(dist: Path) -> list[Path]:
    files = set(dist.glob("fetch-*.js"))
    sdk = dist / "plugin-sdk"
    if sdk.is_dir():
        files |= set(sdk.glob("fetch-*.js"))
    return sorted(files)


def patch_one(path: Path, dry_run: bool) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if NEW_BLOCK in data:
        return "patched", "marker present"
    if OLD_BLOCK not in data:
        if "function buildMediaLocalRoots(stateDir, options = {})" in data:
            return "unpatched", "unexpected roots block"
        return "skip", "no media roots target"

    patched = data.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if not dry_run:
        path.write_text(patched, encoding="utf-8")
    return "patched", "applied"


def status_one(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if "function buildMediaLocalRoots(stateDir, options = {})" not in data:
        return "skip", "no media roots target"
    if NEW_BLOCK in data:
        return "patched", "marker present"
    if OLD_BLOCK in data:
        return "unpatched", "legacy roots block"
    return "unknown", "signature mismatch"


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch media local roots to allow ~/.openclaw/artifacts")
    parser.add_argument("--status", action="store_true", help="show patch status only")
    parser.add_argument("--dry-run", action="store_true", help="compute without writing")
    args = parser.parse_args()

    dist = Path.home() / ".npm-global" / "lib" / "node_modules" / "openclaw" / "dist"
    if not dist.is_dir():
        print(f"dist not found: {dist}")
        return 1

    files = discover_files(dist)
    if not files:
        print("No fetch bundles found")
        return 0

    patched = unpatched = unknown = 0
    for path in files:
        if args.status:
            st, note = status_one(path)
        else:
            st, note = patch_one(path, dry_run=args.dry_run)
        if st == "skip":
            continue
        if st == "patched":
            patched += 1
        elif st == "unpatched":
            unpatched += 1
        elif st == "unknown":
            unknown += 1
        print(f"media-roots {st:9} {path.name} ({note})")

    print(f"summary: patched={patched} unpatched={unpatched} unknown={unknown}")
    if args.status:
        return 1 if unpatched or unknown else 0
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
