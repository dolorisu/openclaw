"""
Patch modules for OpenClaw

Each module defines a Patch subclass that implements:
- check(): Verify if patch is applied
- apply(): Apply the patch
- rollback(): Revert the patch (optional)
"""

from .multibubble import MultiBubblePatch
from .progressive import ProgressivePatch
from .tail_guard import TailGuardPatch
from .outbound_dedupe import OutboundDedupePatch
from .reset_prompt import ResetPromptPatch
from .media_roots import MediaRootsPatch
from .media_send_paths import MediaSendPathsPatch

# All available patches
ALL_PATCHES = [
    MultiBubblePatch,
    ProgressivePatch,
    TailGuardPatch,
    OutboundDedupePatch,
    ResetPromptPatch,
    MediaRootsPatch,
    MediaSendPathsPatch,
]

__all__ = [
    "ALL_PATCHES",
    "MultiBubblePatch",
    "ProgressivePatch",
    "TailGuardPatch",
    "OutboundDedupePatch",
    "ResetPromptPatch",
    "MediaRootsPatch",
    "MediaSendPathsPatch",
]
