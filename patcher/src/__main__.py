"""
Entry point for running openclaw_patcher as a module

Usage:
    python -m openclaw_patcher status
    python -m openclaw_patcher apply --all
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
