#!/usr/bin/env python3
"""Compatibility wrapper.

Canonical location:
  ~/.openclaw/patcher/apply-multibubble-patch.py
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    target = Path(__file__).resolve().parent.parent / "patcher" / "apply-multibubble-patch.py"
    if not target.exists():
        print(f"Missing canonical script: {target}", file=sys.stderr)
        return 1
    print(f"[compat] forwarding to {target}", file=sys.stderr)
    return subprocess.call([sys.executable, str(target), *sys.argv[1:]], env=os.environ.copy())


if __name__ == "__main__":
    raise SystemExit(main())
