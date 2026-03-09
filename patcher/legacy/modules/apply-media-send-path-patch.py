#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path


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


def discover_files(dist: Path) -> list[Path]:
    files = set(dist.glob("skills-*.js"))
    sdk = dist / "plugin-sdk"
    if sdk.is_dir():
        files |= set(sdk.glob("skills-*.js"))
    return sorted(files)


def status_one(path: Path) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if "async function resolveAllowedTmpMediaPath(params)" not in data:
        return "skip", "no media send path target"
    if "path.join(configStateDir, \"artifacts\")" in data:
        return "patched", "marker present"
    if OLD_BLOCK in data:
        return "unpatched", "legacy tmp-only allowlist"
    return "unknown", "signature mismatch"


def patch_one(path: Path, dry_run: bool) -> tuple[str, str]:
    data = path.read_text(encoding="utf-8", errors="ignore")
    if "path.join(configStateDir, \"artifacts\")" in data:
        return "patched", "marker present"
    if OLD_BLOCK not in data:
        if "async function resolveAllowedTmpMediaPath(params)" in data:
            return "unknown", "signature mismatch"
        return "skip", "no media send path target"
    patched = data.replace(OLD_BLOCK, NEW_BLOCK, 1)
    if not dry_run:
        path.write_text(patched, encoding="utf-8")
    return "patched", "applied"


def main() -> int:
    parser = argparse.ArgumentParser(description="Patch media send allowlist to include ~/.openclaw/media and ~/.openclaw/artifacts")
    parser.add_argument("--status", action="store_true", help="show status only")
    parser.add_argument("--dry-run", action="store_true", help="compute without writing")
    args = parser.parse_args()

    dist = Path.home() / ".npm-global" / "lib" / "node_modules" / "openclaw" / "dist"
    if not dist.is_dir():
        print(f"dist not found: {dist}")
        return 1

    files = discover_files(dist)
    if not files:
        print("No skills bundles found")
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
        else:
            unknown += 1
        print(f"media-send  {st:9} {path.name} ({note})")

    print(f"summary: patched={patched} unpatched={unpatched} unknown={unknown}")
    if args.status:
        return 1 if unpatched or unknown else 0
    return 1 if unknown else 0


if __name__ == "__main__":
    raise SystemExit(main())
