"""
OpenClaw Patcher - Unified patch management system

A modular patch management system for OpenClaw that handles:
- Multi-bubble message splitting
- Progressive/streaming updates
- Channel-specific improvements (WhatsApp, Telegram)
"""

__version__ = "2.0.0"

from .core import PatchEngine, Patch, PatchStatus

__all__ = ["PatchEngine", "Patch", "PatchStatus"]
