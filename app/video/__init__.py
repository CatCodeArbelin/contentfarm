"""Optional video generation interfaces."""

from app.video.interface import UnsupportedVideoPipeline, VideoPipeline, VideoPipelineResult

__all__ = ["UnsupportedVideoPipeline", "VideoPipeline", "VideoPipelineResult"]
