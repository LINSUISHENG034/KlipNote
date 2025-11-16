"""WebRTC-based VAD fallback engine."""

from __future__ import annotations

import logging
from typing import List, Tuple

from app.ai_services.enhancement.vad_engines.base_vad import BaseVAD, SpeechSpans

logger = logging.getLogger(__name__)


class WebRTCVAD(BaseVAD):
    """Signal-processing VAD via the `webrtcvad` reference implementation."""

    name = "webrtc"

    def __init__(
        self,
        *,
        aggressiveness: int = 2,
        frame_duration_ms: int = 30,
        sample_rate: int = 16000,
        min_speech_ms: int = 300,
        max_silence_ms: int = 500,
    ) -> None:
        super().__init__()
        self.aggressiveness = aggressiveness
        self.frame_duration_ms = frame_duration_ms
        self.sample_rate = sample_rate
        self.min_speech_ms = min_speech_ms
        self.max_silence_ms = max_silence_ms
        self._vad = None

    def is_available(self) -> bool:
        try:
            import webrtcvad  # noqa: F401
            import pydub  # noqa: F401
        except ImportError:
            return False
        return True

    def detect_speech(self, audio_path: str) -> SpeechSpans:
        if not self.is_available():
            logger.debug("WebRTC VAD unavailable (dependency not installed)")
            return []

        try:
            from pydub import AudioSegment
            import webrtcvad
        except ImportError:  # pragma: no cover - guarded by is_available
            return []

        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_frame_rate(self.sample_rate).set_channels(1).set_sample_width(2)
        raw = audio.raw_data
        frame_size = int(self.sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        vad = self._vad or webrtcvad.Vad(self.aggressiveness)
        self._vad = vad

        speech_segments: List[Tuple[float, float]] = []
        start = None
        timestamp = 0.0

        for idx in range(0, len(raw), frame_size):
            frame = raw[idx: idx + frame_size]
            if len(frame) < frame_size:
                break

            is_speech = vad.is_speech(frame, self.sample_rate)
            if is_speech and start is None:
                start = timestamp
            elif not is_speech and start is not None:
                speech_segments.append((start, timestamp))
                start = None

            timestamp += self.frame_duration_ms / 1000.0

        if start is not None:
            speech_segments.append((start, timestamp))

        # Post-process: filter short segments and merge close ones
        filtered = self._filter_short_segments(speech_segments)
        merged = self._merge_close_segments(filtered)

        return merged

    def _filter_short_segments(
        self,
        segments: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        Filter out speech segments shorter than min_speech_ms.

        Args:
            segments: Raw speech segments

        Returns:
            Filtered segments (>= min_speech_ms duration)
        """
        min_duration_s = self.min_speech_ms / 1000.0
        filtered = [
            (start, end) for start, end in segments
            if (end - start) >= min_duration_s
        ]

        if len(filtered) < len(segments):
            logger.debug(
                f"WebRTC VAD filtered {len(segments) - len(filtered)} short segments "
                f"(<{self.min_speech_ms}ms)"
            )

        return filtered

    def _merge_close_segments(
        self,
        segments: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """
        Merge speech segments separated by silence shorter than max_silence_ms.

        Args:
            segments: Filtered speech segments

        Returns:
            Merged segments
        """
        if not segments:
            return []

        max_gap_s = self.max_silence_ms / 1000.0
        merged = [segments[0]]

        for start, end in segments[1:]:
            prev_start, prev_end = merged[-1]
            gap = start - prev_end

            # Merge if gap is small enough
            if gap <= max_gap_s:
                merged[-1] = (prev_start, end)
                logger.debug(
                    f"WebRTC VAD merged segments at gap={gap*1000:.0f}ms "
                    f"(threshold={self.max_silence_ms}ms)"
                )
            else:
                merged.append((start, end))

        if len(merged) < len(segments):
            logger.debug(
                f"WebRTC VAD merged {len(segments) - len(merged)} close segments"
            )

        return merged
