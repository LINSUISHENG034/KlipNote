"""
WhisperX wav2vec2 forced alignment optimizer.

This optimizer uses WhisperX's wav2vec2 model for word-level timestamp
forced alignment to improve transcription quality.

Story 3.2a: Stub implementation (architecture foundation)
Story 3.2b: Full implementation with dependency validation and alignment logic
"""

import time
import logging
from typing import List, Any, Dict, Optional
from .base import OptimizationResult, TimestampOptimizer, TimestampSegment


logger = logging.getLogger(__name__)


class WhisperXOptimizer(TimestampOptimizer):
    """
    WhisperX wav2vec2 forced alignment optimizer.

    Uses WhisperX's wav2vec2-based alignment model to refine word-level timestamps
    and improve segment boundaries for better subtitle quality.

    Dependencies:
        - whisperx>=3.1.1
        - pyannote.audio==3.1.1
        - torch (CUDA-enabled)

    Performance: ~10-15% overhead vs BELLE-2 transcription time
    Quality: 10-30% segment length improvement, no accuracy loss
    """

    def __init__(self):
        """
        Initialize WhisperXOptimizer with lazy model loading.

        Raises:
            RuntimeError: If WhisperX dependencies are not installed.
        """
        if not self.is_available():
            raise RuntimeError(
                "WhisperX dependencies not installed. "
                "Install with: uv pip install whisperx pyannote.audio==3.1.1"
            )

        # Lazy-loaded on first optimize() call
        self.align_model = None
        self.align_metadata = None
        self._whisperx = None

    @staticmethod
    def is_available() -> bool:
        """
        Check if WhisperX and pyannote.audio are installed.

        Returns:
            True if dependencies available, False otherwise.
        """
        try:
            import whisperx
            import pyannote.audio
            import torch

            # Also verify CUDA is available (WhisperX requires GPU)
            if not torch.cuda.is_available():
                logger.warning(
                    "WhisperX dependencies found but CUDA unavailable. "
                    "WhisperX requires GPU acceleration."
                )
                return False

            return True
        except ImportError as e:
            logger.debug(f"WhisperX unavailable: {e}")
            return False

    def optimize(
        self,
        segments: List[TimestampSegment],
        audio_path: str,
        language: str = "zh"
    ) -> OptimizationResult:
        """
        Apply WhisperX wav2vec2 forced alignment for word-level timestamps.

        Args:
            segments: Raw transcription segments from BELLE-2
                Format: [{"start": 0.5, "end": 3.2, "text": "..."}]
            audio_path: Path to audio file for alignment
            language: Language code (default: "zh" for Chinese)

        Returns:
            OptimizationResult with:
                - segments: Word-aligned segments with refined timestamps
                - metrics: processing_time_ms, segments_optimized, word_count
                - optimizer_name: "whisperx"

        Raises:
            RuntimeError: If dependencies unavailable or alignment fails
        """
        start_time = time.time()

        # Lazy-load WhisperX on first call
        if self._whisperx is None:
            import whisperx
            self._whisperx = whisperx

        # Lazy-load alignment model on first call
        if self.align_model is None:
            logger.info(f"Loading WhisperX alignment model for language: {language}")
            self.align_model, self.align_metadata = self._whisperx.load_align_model(
                language_code=language,
                device="cuda"
            )
            logger.info("WhisperX alignment model loaded successfully")

        # Load audio
        audio = self._whisperx.load_audio(audio_path)

        # Convert TimestampSegment to dict format for WhisperX
        segments_dict = [
            {
                "start": float(seg["start"]),
                "end": float(seg["end"]),
                "text": seg["text"]
            }
            for seg in segments
        ]

        # Apply forced alignment
        logger.info(f"Applying WhisperX forced alignment to {len(segments_dict)} segments")
        aligned_result = self._whisperx.align(
            segments_dict,
            self.align_model,
            self.align_metadata,
            audio,
            device="cuda",
            return_char_alignments=False
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Count words in aligned segments
        word_count = sum(
            len(seg.get("words", []))
            for seg in aligned_result["segments"]
        )

        logger.info(
            f"WhisperX alignment complete: {len(aligned_result['segments'])} segments, "
            f"{word_count} words, {processing_time_ms:.0f}ms"
        )

        return OptimizationResult(
            segments=aligned_result["segments"],
            metrics={
                "processing_time_ms": processing_time_ms,
                "segments_optimized": len(aligned_result["segments"]),
                "word_count": word_count
            },
            optimizer_name="whisperx"
        )
