"""
Enhanced transcription schema definitions for Epic 4 metadata work.

TypedDict structures capture the layered metadata model so that services can
optionally emit richer payloads without breaking simple `[{"start","end","text"}]`
segment consumers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

try:
    from typing import NotRequired  # Python 3.11+
except ImportError:
    from typing_extensions import NotRequired  # Python 3.10 compatibility


class CharTiming(TypedDict, total=False):
    """Character-level timestamp container."""

    char: str
    start: float
    end: float
    score: NotRequired[float]


class WordTiming(TypedDict, total=False):
    """Word-level timestamp container with optional language metadata."""

    word: str
    start: float
    end: float
    score: NotRequired[float]
    language: NotRequired[str]


class BaseSegment(TypedDict):
    """Minimal backward-compatible transcription segment."""

    start: float
    end: float
    text: str


class EnhancedSegment(BaseSegment, total=False):
    """Extended segment metadata used by downstream enhancement components."""

    words: List[WordTiming]
    chars: List[CharTiming]
    confidence: Optional[float]
    no_speech_prob: Optional[float]
    avg_logprob: Optional[float]
    source_model: Optional[str]
    enhancements_applied: List[str]
    speaker: Optional[str]


class TranscriptionMetadata(TypedDict, total=False):
    """Global metadata for a transcription run."""

    language: Optional[str]
    duration: Optional[float]
    model_name: Optional[str]
    processing_time: Optional[float]
    vad_enabled: bool
    alignment_model: Optional[str]


class TranscriptionResult(TypedDict, total=False):
    """Top-level payload bundling segments, metadata, and computed stats."""

    segments: List[EnhancedSegment]
    metadata: TranscriptionMetadata
    stats: Dict[str, Any]


# Backward-compatibility alias requested in AC #2
TimestampSegment = EnhancedSegment


def build_transcription_result(
    *,
    segments: List[BaseSegment],
    language: Optional[str],
    model_name: str,
    processing_time: float,
    duration: Optional[float],
    vad_enabled: bool,
    alignment_model: Optional[str],
    enhancements_applied: Optional[List[str]] = None,
) -> TranscriptionResult:
    """
    Convert simple segments collection into a TranscriptionResult.

    Args:
        segments: Raw BaseSegment entries gathered from transcription.
        language: Detected or requested language code.
        model_name: Engine name (e.g., 'belle2', 'whisperx').
        processing_time: Seconds spent performing transcription.
        duration: Total audio duration, if known.
        vad_enabled: Whether unified VAD post-processing ran.
        alignment_model: Which aligner (if any) produced timestamps.
        enhancements_applied: Additional enhancement labels to tag segments.
    """
    applied = enhancements_applied or []

    enriched_segments: List[EnhancedSegment] = []
    for segment in segments:
        enriched_segments.append(
            EnhancedSegment(
                start=float(segment.get("start", 0.0)),
                end=float(segment.get("end", 0.0)),
                text=str(segment.get("text", "")),
                words=list(segment.get("words", [])),
                chars=list(segment.get("chars", [])),
                confidence=segment.get("confidence"),
                no_speech_prob=segment.get("no_speech_prob"),
                avg_logprob=segment.get("avg_logprob"),
                source_model=segment.get("source_model", model_name),
                enhancements_applied=list(segment.get("enhancements_applied", applied)),
                speaker=segment.get("speaker"),
            )
        )

    metadata: TranscriptionMetadata = {
        "language": language,
        "duration": duration,
        "model_name": model_name,
        "processing_time": processing_time,
        "vad_enabled": vad_enabled,
        "alignment_model": alignment_model,
    }

    stats: Dict[str, Any] = {
        "segment_count": len(enriched_segments),
        "enhancements_applied": applied,
    }

    return TranscriptionResult(
        segments=enriched_segments,
        metadata=metadata,
        stats=stats,
    )


__all__ = [
    "BaseSegment",
    "CharTiming",
    "EnhancedSegment",
    "TimestampSegment",
    "TranscriptionMetadata",
    "TranscriptionResult",
    "WordTiming",
    "build_transcription_result",
]
