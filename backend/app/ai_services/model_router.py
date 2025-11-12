"""
Model routing logic for selecting the optimal transcription service.

Responsibilities:
1. Honor explicit user language hints.
2. Run Whisper-small language detection (30-second sample, 5-second timeout) when no hint is provided.
3. Persist structured selection metadata for observability.
4. Return the correct TranscriptionService implementation (BELLE-2 ↔ WhisperX) while
   gracefully falling back if a model fails to load.
"""

from __future__ import annotations

import logging
import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as DetectionTimeout
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import numpy as np
import torch
from pydantic import BaseModel, Field

from app.ai_services.base import TranscriptionService
from app.ai_services.belle2_service import Belle2Service
from app.ai_services.whisperx_service import WhisperXService
from app.ai_services.whisperx_shim import ensure_whisperx_available

ensure_whisperx_available()
from app.ai_services.whisperx.whisperx.audio import (
    SAMPLE_RATE,
    log_mel_spectrogram,
    pad_or_trim,
)
from app.config import settings

logger = logging.getLogger(__name__)

MANDARIN_CODES = {
    "zh",
    "zh-cn",
    "zh-hans",
    "zh-hant",
    "zh-tw",
    "zh-hk",
    "zh-sg",
    "cmn",
    "mandarin",
}
DEFAULT_ENGINE = "whisperx"


@dataclass
class DetectionResult:
    """Represents the outcome of a language detection attempt."""

    language: Optional[str]
    confidence: Optional[float]
    duration_ms: float
    status: str
    error: Optional[str] = None


class RouterConfig(BaseModel):
    """Configuration envelope for the model router."""

    enable_belle2: bool = Field(default=True)
    enable_sensevoice: bool = Field(default=False)
    default_engine: str = Field(default=DEFAULT_ENGINE)
    language_detection_model: str = Field(default="small")
    language_detection_duration: int = Field(default=30, ge=5, le=120)
    language_detection_timeout: float = Field(default=5.0, gt=0)
    detection_device: str = Field(default="cuda")
    detection_compute_type: str = Field(default="int8")
    log_selection_events: bool = Field(default=True)

    @classmethod
    def from_settings(cls) -> "RouterConfig":
        """Build config from runtime settings with sane fallbacks."""
        return cls(
            enable_belle2=getattr(settings, "ROUTER_ENABLE_BELLE2", True),
            enable_sensevoice=getattr(settings, "ROUTER_ENABLE_SENSEVOICE", False),
            default_engine=getattr(settings, "ROUTER_DEFAULT_ENGINE", DEFAULT_ENGINE),
            language_detection_model=getattr(
                settings, "ROUTER_LANGUAGE_DETECTION_MODEL", "small"
            ),
            language_detection_duration=getattr(
                settings, "ROUTER_LANGUAGE_DETECTION_DURATION", 30
            ),
            language_detection_timeout=getattr(
                settings, "ROUTER_LANGUAGE_DETECTION_TIMEOUT", 5.0
            ),
            detection_device=getattr(settings, "ROUTER_DETECTION_DEVICE", "cuda"),
            detection_compute_type=getattr(
                settings, "ROUTER_DETECTION_COMPUTE_TYPE", "int8"
            ),
            log_selection_events=getattr(
                settings, "ROUTER_LOG_SELECTION_EVENTS", True
            ),
        )


class LanguageDetector:
    """Thin wrapper around Whisper-small language detection with timeout safety."""

    _model_cache: Dict[str, Any] = {}
    _model_lock = threading.Lock()

    def __init__(self, config: RouterConfig):
        self.config = config
        self.device = self._resolve_device(config.detection_device)
        self.compute_type = config.detection_compute_type

    def detect(self, audio_path: str) -> DetectionResult:
        """Detect the dominant language by sampling the first N seconds of audio."""
        start = time.perf_counter()
        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._detect_sync, audio_path)
                language, confidence = future.result(
                    timeout=self.config.language_detection_timeout
                )

            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            return DetectionResult(
                language=language,
                confidence=confidence,
                duration_ms=duration_ms,
                status="completed",
            )

        except DetectionTimeout:
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            logger.warning(
                "Language detection timed out after %.2fs for %s",
                self.config.language_detection_timeout,
                audio_path,
            )
            return DetectionResult(
                language=None,
                confidence=None,
                duration_ms=duration_ms,
                status="timeout",
                error="detection_timeout",
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            duration_ms = round((time.perf_counter() - start) * 1000, 3)
            logger.warning(
                "Language detection failed for %s: %s", audio_path, exc, exc_info=True
            )
            return DetectionResult(
                language=None,
                confidence=None,
                duration_ms=duration_ms,
                status="error",
                error=str(exc),
            )

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _detect_sync(self, audio_path: str) -> Tuple[str, float]:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found for detection: {audio_path}")

        model = self._load_model()
        duration = max(5, min(self.config.language_detection_duration, 60))
        sample = _load_audio_snippet(audio_path, duration_seconds=duration)

        if sample.size == 0:
            raise RuntimeError("Audio snippet for detection is empty")

        target_samples = int(duration * SAMPLE_RATE)
        trimmed = pad_or_trim(sample, length=target_samples)
        segment = log_mel_spectrogram(
            trimmed,
            n_mels=self._infer_mel_count(model),
            device=self.device,
        )
        encoder_output = model.encode(segment)
        results = model.model.detect_language(encoder_output)

        language_token, probability = results[0][0]
        language_code = language_token[2:-2].lower()
        return language_code, float(probability)

    def _load_model(self):
        cache_key = (
            self.config.language_detection_model,
            self.device,
            self.compute_type,
        )
        if cache_key in self._model_cache:
            return self._model_cache[cache_key]

        with self._model_lock:
            if cache_key in self._model_cache:
                return self._model_cache[cache_key]

            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:  # pragma: no cover - dependency guard
                raise RuntimeError(
                    "faster-whisper is required for language detection"
                ) from exc

            model = WhisperModel(
                self.config.language_detection_model,
                device=self.device,
                compute_type=self.compute_type,
            )
            self._model_cache[cache_key] = model
            return model

    @staticmethod
    def _resolve_device(preferred: str) -> str:
        if preferred == "cuda" and not torch.cuda.is_available():
            return "cpu"
        return preferred

    @staticmethod
    def _infer_mel_count(model: Any) -> int:
        dims = getattr(model, "dims", None)
        if hasattr(model, "model") and hasattr(model.model, "dims"):
            dims = model.model.dims
        return int(getattr(dims, "n_mels", 80))


def select_engine(
    job_id: str,
    audio_path: str,
    language_hint: Optional[str] = None,
    config: Optional[RouterConfig] = None,
    detector: Optional[LanguageDetector] = None,
) -> Tuple[TranscriptionService, str, Dict[str, Any]]:
    """
    Select the correct transcription engine for a job.

    Returns:
        (service_instance, engine_name, selection_details)
    """
    router_config = config or RouterConfig.from_settings()
    language_hint_normalized = _normalize_language_code(language_hint)
    selection_details: Dict[str, Any] = {
        "job_id": job_id,
        "user_language_hint": language_hint_normalized,
        "detected_language": None,
        "detection_confidence": None,
        "detection_duration_ms": 0.0,
        "detection_status": "skipped" if language_hint_normalized else "pending",
        "selection_reason": None,
        "fallback_reason": None,
        "selection_timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if language_hint_normalized:
        selection_details["detected_language"] = language_hint_normalized
        service, engine_name = _select_from_hint(selection_details, router_config)
        selection_details["selected_engine"] = engine_name
        _emit_selection_log(selection_details, router_config)
        return service, engine_name, selection_details

    detection_client = detector or LanguageDetector(router_config)
    detection_result = detection_client.detect(audio_path)
    selection_details["detected_language"] = detection_result.language
    selection_details["detection_confidence"] = detection_result.confidence
    selection_details["detection_duration_ms"] = detection_result.duration_ms
    selection_details["detection_status"] = detection_result.status
    if detection_result.error:
        selection_details["fallback_reason"] = detection_result.error

    target_engine = router_config.default_engine or DEFAULT_ENGINE
    if (
        detection_result.status == "completed"
        and detection_result.language
        and _is_mandarin(detection_result.language)
        and router_config.enable_belle2
    ):
        selection_details["selection_reason"] = (
            f"detected_{detection_result.language}"
        )
        service, engine_name = _instantiate_service("belle2", selection_details)
    else:
        selection_details["selection_reason"] = _determine_detection_reason(
            detection_result
        )
        service, engine_name = _instantiate_service(target_engine, selection_details)

    selection_details["selected_engine"] = engine_name
    _emit_selection_log(selection_details, router_config)
    return service, engine_name, selection_details


# ------------------------------------------------------------------------- #
# Routing helpers
# ------------------------------------------------------------------------- #
def _select_from_hint(
    selection_details: Dict[str, Any],
    config: RouterConfig,
) -> Tuple[TranscriptionService, str]:
    hint = selection_details["user_language_hint"]
    if hint and _is_mandarin(hint) and config.enable_belle2:
        selection_details["selection_reason"] = f"user_hint_{hint}"
        service, engine_name = _instantiate_service("belle2", selection_details)
    else:
        reason = f"user_hint_{hint or 'unknown'}"
        selection_details["selection_reason"] = reason
        service, engine_name = _instantiate_service(
            config.default_engine or DEFAULT_ENGINE, selection_details
        )
    return service, engine_name


def _instantiate_service(
    requested_engine: str,
    selection_details: Dict[str, Any],
) -> Tuple[TranscriptionService, str]:
    engine = (requested_engine or DEFAULT_ENGINE).lower()

    if engine == "belle2":
        try:
            service = Belle2Service()
            return service, "belle2"
        except Exception as exc:  # pragma: no cover - fallback path
            logger.warning("BELLE-2 unavailable, falling back to WhisperX: %s", exc)
            selection_details["selection_reason"] = "belle2_load_failed"
            selection_details["fallback_reason"] = str(exc)
            fallback = WhisperXService()
            return fallback, "whisperx"

    if engine != "whisperx":
        logger.warning(
            "Unsupported engine '%s', falling back to WhisperX", requested_engine
        )
        selection_details["fallback_reason"] = f"unsupported_engine:{requested_engine}"

    service = WhisperXService()
    return service, "whisperx"


def _determine_detection_reason(result: DetectionResult) -> str:
    if result.status == "completed" and result.language:
        return f"detected_{result.language}"
    if result.status == "timeout":
        return "detection_timeout"
    if result.status == "error":
        return "detection_error"
    return "default_whisperx"


def _emit_selection_log(selection_details: Dict[str, Any], config: RouterConfig) -> None:
    if not config.log_selection_events:
        return

    payload = {
        "job_id": selection_details.get("job_id"),
        "selected_engine": selection_details.get("selected_engine"),
        "user_language_hint": selection_details.get("user_language_hint"),
        "detected_language": selection_details.get("detected_language"),
        "detection_confidence": selection_details.get("detection_confidence"),
        "detection_duration_ms": selection_details.get("detection_duration_ms"),
        "detection_status": selection_details.get("detection_status"),
        "selection_reason": selection_details.get("selection_reason"),
        "fallback_reason": selection_details.get("fallback_reason"),
        "selection_timestamp": selection_details.get("selection_timestamp"),
    }
    logger.info("model_selection", extra={"event": "model_selection", **payload})


# ------------------------------------------------------------------------- #
# Utility helpers
# ------------------------------------------------------------------------- #
def _normalize_language_code(language: Optional[str]) -> Optional[str]:
    if not language:
        return None
    return language.strip().lower().replace("_", "-")


def _is_mandarin(language: Optional[str]) -> bool:
    if not language:
        return False
    normalized = _normalize_language_code(language)
    return normalized in MANDARIN_CODES if normalized else False


def _load_audio_snippet(audio_path: str, duration_seconds: int) -> np.ndarray:
    """
    Efficiently decode only the first N seconds of audio using ffmpeg.
    """
    cmd = [
        "ffmpeg",
        "-nostdin",
        "-threads",
        "0",
        "-i",
        audio_path,
        "-t",
        str(duration_seconds),
        "-f",
        "s16le",
        "-ac",
        "1",
        "-acodec",
        "pcm_s16le",
        "-ar",
        str(SAMPLE_RATE),
        "-",
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            timeout=duration_seconds + 2,
        )
    except subprocess.CalledProcessError as exc:  # pragma: no cover - ffmpeg errors
        raise RuntimeError(f"ffmpeg failed to load audio: {exc.stderr}") from exc

    return (
        np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    )
