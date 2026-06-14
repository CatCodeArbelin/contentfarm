"""Interfaces for optional video generation pipelines.

The video pipeline is intentionally not wired into the production workflow by
default. Production code can depend on :class:`VideoPipeline` and explicitly
inject a concrete implementation when video generation is enabled.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol, runtime_checkable

VideoPipelineStatus = Literal["unsupported"]


@dataclass(frozen=True, slots=True)
class VideoPipelineResult:
    """Result returned by a video pipeline step."""

    status: VideoPipelineStatus
    message: str
    artifacts: dict[str, Path] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class VideoPipeline(Protocol):
    """Protocol for optional text-to-video generation pipelines."""

    def text_to_tts_audio(self, text: str, *, voice: str | None = None) -> VideoPipelineResult:
        """Convert source text into a TTS audio artifact."""
        ...

    def audio_to_slides(self, audio_path: Path, *, script: str | None = None) -> VideoPipelineResult:
        """Create slide assets synchronized with an audio track."""
        ...

    def generate_subtitles(self, audio_path: Path, *, language: str | None = None) -> VideoPipelineResult:
        """Generate subtitle artifacts from an audio track."""
        ...

    def render_mp4(
        self,
        *,
        audio_path: Path,
        slides_path: Path,
        subtitles_path: Path | None = None,
    ) -> VideoPipelineResult:
        """Render a final MP4 from audio, slides, and optional subtitles."""
        ...


class UnsupportedVideoPipeline:
    """Stub implementation used when video generation is not configured."""

    _MESSAGE = "Video pipeline is not configured for this deployment."

    def text_to_tts_audio(self, text: str, *, voice: str | None = None) -> VideoPipelineResult:
        """Return an unsupported status instead of producing TTS audio."""
        return self._unsupported(step="text_to_tts_audio")

    def audio_to_slides(self, audio_path: Path, *, script: str | None = None) -> VideoPipelineResult:
        """Return an unsupported status instead of producing slides."""
        return self._unsupported(step="audio_to_slides")

    def generate_subtitles(self, audio_path: Path, *, language: str | None = None) -> VideoPipelineResult:
        """Return an unsupported status instead of producing subtitles."""
        return self._unsupported(step="generate_subtitles")

    def render_mp4(
        self,
        *,
        audio_path: Path,
        slides_path: Path,
        subtitles_path: Path | None = None,
    ) -> VideoPipelineResult:
        """Return an unsupported status instead of rendering an MP4."""
        return self._unsupported(step="render_mp4")

    def _unsupported(self, *, step: str) -> VideoPipelineResult:
        return VideoPipelineResult(
            status="unsupported",
            message=self._MESSAGE,
            metadata={"step": step},
        )
