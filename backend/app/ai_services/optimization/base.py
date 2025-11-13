"""
Base interfaces and data models for timestamp optimization.

This module defines the abstract TimestampOptimizer interface and
OptimizationResult dataclass used by all optimizer implementations.

Story 3.2a: Pluggable Optimizer Architecture Design
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Sequence, TypedDict


class WordTiming(TypedDict, total=False):
    """
    Structure describing start/end offsets for a single word.

    Optional fields like `score` allow optimizers to surface confidence data
    without forcing every implementation to provide it.
    """

    start: float
    end: float
    text: str
    score: float


class _RequiredTimestampSegment(TypedDict):
    start: float
    end: float
    text: str


class TimestampSegment(_RequiredTimestampSegment, total=False):
    """
    Canonical transcription segment used across optimizers.

    Optional fields capture richer metadata when available (e.g., WhisperX word
    timings) but remain backwards-compatible with raw BELLE-2 output.
    """

    words: List[WordTiming]
    confidence: float
    speaker: str


@dataclass
class OptimizationResult:
    """
    Standardized result from timestamp optimization.

    This dataclass provides a consistent output format across all optimizer
    implementations (WhisperX, Heuristic, future optimizers).

    Attributes:
        segments: List of optimized transcription segments in TimestampSegment format
                  (required: start/end/text, optional: words, confidence, speaker)
        metrics: Performance metrics from the optimization process. Common keys:
                 - processing_time_ms: Time taken for optimization
                 - segments_optimized: Number of segments processed
                 - optimizer-specific metrics (e.g., word_count for WhisperX)
        optimizer_name: Name of the optimizer that produced this result.
                        Valid values: "whisperx", "heuristic"
    """
    segments: List[TimestampSegment]
    metrics: Dict[str, float]
    optimizer_name: str


class TimestampOptimizer(ABC):
    """
    Abstract interface for timestamp optimization strategies.

    This interface enables pluggable optimizer implementations that can be
    selected via configuration without code changes. All optimizer implementations
    must inherit from this class and implement its abstract methods.

    Example implementations:
        - WhisperXOptimizer: Uses wav2vec2 forced alignment (Story 3.2b)
        - HeuristicOptimizer: Uses VAD + energy refinement + splitting (Stories 3.3-3.5)

    Usage:
        optimizer = OptimizerFactory.create(engine="auto")
        result = optimizer.optimize(segments, audio_path, language="zh")
    """

    @abstractmethod
    def optimize(
        self,
        segments: Sequence[TimestampSegment],
        audio_path: str,
        language: str = "zh"
    ) -> OptimizationResult:
        """
        Optimize transcription segments' timestamps and splitting.

        This method takes raw transcription segments and applies optimizer-specific
        processing to improve timestamp accuracy and segment boundaries.

        Args:
            segments: Iterable of raw transcription segments in TimestampSegment format.
                      Required keys: start (float), end (float), text (str)
                      Optional keys: words (list[WordTiming]), confidence (float), speaker (str)
            audio_path: Absolute path to the original audio file. Required for
                        audio analysis (waveform energy, VAD, forced alignment)
            language: Language code for the audio. Default "zh" for Chinese.
                      Used for language-specific processing (e.g., text length estimation)

        Returns:
            OptimizationResult containing:
                - Optimized segments with improved timestamps and boundaries
                - Performance metrics (processing time, segments processed, etc.)
                - Optimizer name for tracing

        Raises:
            NotImplementedError: If optimizer implementation not yet complete
            FileNotFoundError: If audio_path does not exist
            ValueError: If segments list is empty or malformed
        """
        pass

    @staticmethod
    @abstractmethod
    def is_available() -> bool:
        """
        Check if optimizer dependencies are installed and functional.

        This static method allows checking optimizer availability without
        instantiation. Used by OptimizerFactory for auto-selection and fallback logic.

        Returns:
            True if optimizer can be instantiated and used.
            False if required dependencies are missing or incompatible.

        Example:
            if WhisperXOptimizer.is_available():
                optimizer = WhisperXOptimizer()
            else:
                optimizer = HeuristicOptimizer()  # Fallback
        """
        pass
