"""Silero (torch.hub) VAD implementation."""

from __future__ import annotations

import logging
from typing import List, Tuple

from app.ai_services.enhancement.vad_engines.base_vad import BaseVAD, SpeechSpans

logger = logging.getLogger(__name__)


class SileroVAD(BaseVAD):
    """Wrap the Silero VAD torch.hub reference implementation."""

    name = "silero"

    def __init__(
        self,
        *,
        threshold: float = 0.5,
        min_silence_ms: int = 700,
    ) -> None:
        super().__init__(min_silence_ms / 1000.0)
        self.threshold = threshold
        self.min_silence_ms = min_silence_ms
        self._model = None
        self._get_speech_timestamps = None
        self._read_audio = None

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
        except ImportError:
            return False
        return True

    def detect_speech(self, audio_path: str) -> SpeechSpans:
        if not self.is_available():
            logger.debug("Silero VAD unavailable (torch not installed)")
            return []

        try:
            model, get_speech_timestamps, read_audio = self._load_model()
            # read_audio resamples to 16000 Hz
            wav = read_audio(audio_path, sampling_rate=16000)
            speech_segments = get_speech_timestamps(
                wav,
                model,
                sampling_rate=16000,
                threshold=self.threshold,
                min_silence_duration_ms=self.min_silence_ms,
            )
            return [
                (segment["start"] / 16000.0, segment["end"] / 16000.0)
                for segment in speech_segments
            ]
        except Exception as exc:  # pragma: no cover - defensive guard
            logger.warning("Silero VAD failed, falling back to raw segments: %s", exc)
            return []

    def _load_model(self) -> Tuple[object, object, object]:
        if self._model is not None:
            return self._model, self._get_speech_timestamps, self._read_audio

        import torch

        logger.info("Loading Silero VAD model via torch.hub")
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )
        (get_speech_timestamps, _, read_audio, _, _) = utils

        self._model = model
        self._get_speech_timestamps = get_speech_timestamps
        self._read_audio = read_audio
        return model, get_speech_timestamps, read_audio
