"""Patch modules for OpenClaw"""

from .multibubble import MultiBubblePatch
from .progressive import ProgressivePatch
from .tail_guard import TailGuardPatch
from .outbound_dedupe import OutboundDedupePatch
from .reset_prompt import ResetPromptPatch
from .media_roots import MediaRootsPatch
from .media_send_paths import MediaSendPathsPatch
from .code_formatter import CodeFormatterPatch

ALL_PATCHES = [
    MultiBubblePatch,
    ProgressivePatch,
    TailGuardPatch,
    OutboundDedupePatch,
    ResetPromptPatch,
    MediaRootsPatch,
    MediaSendPathsPatch,
    CodeFormatterPatch,
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
    "CodeFormatterPatch",
]
