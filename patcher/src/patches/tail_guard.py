"""
Tail Guard Patch

Prevents splitting short progress fragments into separate bubbles.

Dependencies: progressive (requires block streaming enabled)
"""

from ..core import Patch, PatchStatus, PatchResult


class TailGuardPatch(Patch):
    name = "tail_guard"
    description = "Prevent splitting short progress fragments"
    dependencies = ["progressive"]
    
    def check(self) -> PatchStatus:
        # TODO: Implement check logic
        return PatchStatus.NOT_APPLIED
    
    def apply(self) -> PatchResult:
        # TODO: Port from apply-wa-progress-tail-guard.py
        return PatchResult(
            status=PatchStatus.FAILED,
            message="Not yet implemented - use legacy patcher"
        )
