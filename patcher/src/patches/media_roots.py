"""
Media Roots Patch

Allows local media files from ~/.openclaw/artifacts directory.
"""

from ..core import Patch, PatchStatus, PatchResult


class MediaRootsPatch(Patch):
    name = "media_roots"
    description = "Allow media from ~/.openclaw/artifacts"
    dependencies = []
    
    def check(self) -> PatchStatus:
        # TODO: Implement check logic
        return PatchStatus.NOT_APPLIED
    
    def apply(self) -> PatchResult:
        # TODO: Port from apply-media-local-roots.py
        return PatchResult(
            status=PatchStatus.FAILED,
            message="Not yet implemented - use legacy patcher"
        )
