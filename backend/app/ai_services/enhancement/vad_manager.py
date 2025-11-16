"""Unified VAD manager for BELLE-2 + WhisperX pipelines."""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from app.ai_services.enhancement.vad_engines import BaseVAD, SileroVAD, WebRTCVAD
from app.ai_services.schema import BaseSegment
from app.config import settings

logger = logging.getLogger(__name__)


class VADManager:
    """Coordinate multiple VAD engines with auto-selection + fallback."""

    def __init__(
        self,
        *,
        engine: Optional[str] = None,
        min_silence_duration: Optional[float] = None,
        silero_threshold: Optional[float] = None,
        silero_min_silence_ms: Optional[int] = None,
        webrtc_aggressiveness: Optional[int] = None,
        webrtc_min_speech_ms: Optional[int] = None,
        webrtc_max_silence_ms: Optional[int] = None,
    ) -> None:
        self.engine_preference = (engine or settings.VAD_ENGINE).lower()
        self.min_silence_duration = min_silence_duration or settings.VAD_MIN_SILENCE_DURATION
        self._engines = {
            "silero": SileroVAD(
                threshold=silero_threshold or settings.VAD_SILERO_THRESHOLD,
                min_silence_ms=silero_min_silence_ms or settings.VAD_SILERO_MIN_SILENCE_MS,
            ),
            "webrtc": WebRTCVAD(
                aggressiveness=webrtc_aggressiveness or settings.VAD_WEBRTC_AGGRESSIVENESS,
                min_speech_ms=webrtc_min_speech_ms or settings.VAD_WEBRTC_MIN_SPEECH_MS,
                max_silence_ms=webrtc_max_silence_ms or settings.VAD_WEBRTC_MAX_SILENCE_MS,
            ),
        }

    def process_segments(
        self,
        segments: List[BaseSegment],
        audio_path: str,
    ) -> Tuple[List[BaseSegment], Optional[str]]:
        """
        Filter segments using the best-available VAD engine.

        Returns:
            (filtered_segments, engine_name_used)
        """
        engine = self._select_engine()
        if not engine:
            logger.debug("No VAD engine available; returning original segments")
            return segments, None

        speech_segments = engine.detect_speech(audio_path)
        if not speech_segments:
            logger.info("VAD (%s) returned no speech spans; keeping original segments", engine.name)
            return segments, None

        filtered = engine.filter_segments(
            segments,
            speech_segments,
            min_silence_duration=self.min_silence_duration,
        )
        return filtered, engine.name

    def _select_engine(self) -> Optional[BaseVAD]:
        ordered = self._engine_order()
        for name in ordered:
            engine = self._engines.get(name)
            if engine and engine.is_available():
                return engine
        return None

    def _engine_order(self) -> List[str]:
        if self.engine_preference == "silero":
            return ["silero", "webrtc"]
        if self.engine_preference == "webrtc":
            return ["webrtc"]
        # auto -> prefer Silero
        return ["silero", "webrtc"]
