"""Base class for VAD engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Sequence, Tuple

from app.ai_services.schema import BaseSegment


SpeechSpans = Sequence[Tuple[float, float]]


class BaseVAD(ABC):
    """Common helpers for VAD implementations."""

    name: str = "base"

    def __init__(self, min_silence_duration: float = 1.0) -> None:
        self.min_silence_duration = min_silence_duration

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the engine dependencies are available."""

    @abstractmethod
    def detect_speech(self, audio_path: str) -> SpeechSpans:
        """Return speech spans as (start, end) tuples in seconds."""

    def filter_segments(
        self,
        segments: List[BaseSegment],
        speech_segments: SpeechSpans,
        min_silence_duration: float | None = None,
    ) -> List[BaseSegment]:
        """
        Remove silence-only segments when no speech overlap is detected.

        Args:
            segments: Original transcription segments.
            speech_segments: Detected speech spans.
            min_silence_duration: Optional override for silence pruning threshold.
        """
        silence_threshold = min_silence_duration or self.min_silence_duration
        if not speech_segments:
            return segments

        filtered: List[BaseSegment] = []
        for segment in segments:
            start = float(segment.get("start", 0.0))
            end = float(segment.get("end", 0.0))
            duration = max(0.0, end - start)

            # Always keep very short segments to avoid over-pruning
            if duration < silence_threshold:
                filtered.append(segment)
                continue

            if self._has_overlap(start, end, speech_segments):
                filtered.append(segment)

        return filtered

    @staticmethod
    def _has_overlap(
        start: float,
        end: float,
        speech_segments: SpeechSpans,
    ) -> bool:
        """Check if the [start, end] range overlaps any speech span."""
        for speech_start, speech_end in speech_segments:
            overlap_start = max(start, speech_start)
            overlap_end = min(end, speech_end)
            if overlap_end - overlap_start > 0:
                return True
        return False
