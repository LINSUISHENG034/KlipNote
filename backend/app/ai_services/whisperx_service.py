"""
WhisperX transcription service implementation
GPU-accelerated audio transcription using faster-whisper (bypassing whisperx)

NOTE: Originally used whisperx, but switched to faster-whisper directly due to
unsolvable dependency conflicts between whisperx's pyannote dependencies and torch.
faster-whisper provides the core Whisper transcription without pyannote coupling.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.ai_services.base import TranscriptionService
from app.ai_services.enhancement import VADManager
from app.ai_services.schema import BaseSegment, TranscriptionResult, build_transcription_result
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class WhisperXService(TranscriptionService):
    """
    Whisper-based transcription service using faster-whisper directly

    Originally used whisperx, but switched to faster-whisper to avoid pyannote.audio
    dependency conflicts. faster-whisper provides core Whisper functionality with
    GPU acceleration and efficient inference using CTranslate2.

    Caches the loaded model to avoid reloading on every transcription.
    """

    # Class-level model cache to avoid reloading
    _model_cache: Dict[str, Any] = {}

    def __init__(
        self,
        model_name: str = None,
        device: str = None,
        compute_type: str = None
    ):
        """
        Initialize Whisper service with faster-whisper

        Args:
            model_name: Whisper model (tiny, base, small, medium, large-v2, large-v3)
            device: 'cuda' for GPU or 'cpu'
            compute_type: 'float16' (GPU), 'int8' (GPU/CPU), 'float32' (CPU)
        """
        self.model_name = model_name or settings.WHISPER_MODEL
        self.device = device or settings.WHISPER_DEVICE
        self.compute_type = compute_type or settings.WHISPER_COMPUTE_TYPE

        # Check if model is cached
        cache_key = f"{self.model_name}_{self.device}_{self.compute_type}"
        if cache_key not in WhisperXService._model_cache:
            logger.info(f"Loading Whisper model: {self.model_name} on {self.device}")
            try:
                # Import faster-whisper directly (no whisperx/pyannote dependencies)
                from faster_whisper import WhisperModel

                # Load model
                self.model = WhisperModel(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type
                )
                # Cache the model
                WhisperXService._model_cache[cache_key] = self.model
                logger.info("Whisper model loaded and cached successfully")
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {e}")
                raise RuntimeError(
                    f"Failed to load Whisper model '{self.model_name}': {str(e)}"
                )
        else:
            logger.info(f"Using cached Whisper model: {self.model_name}")
            self.model = WhisperXService._model_cache[cache_key]

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,  # Auto-detect when None
        include_metadata: bool = False,
        **kwargs
    ) -> Union[List[BaseSegment], TranscriptionResult]:
        """
        Transcribe audio file using faster-whisper with automatic language detection

        Args:
            audio_path: Path to audio file
            language: Language code for transcription (ISO 639-1). If None (default),
                      Whisper automatically detects the source audio language.
                      Examples: 'en', 'zh', 'es', 'fr'
            include_metadata: Return the enhanced schema payload instead of simple segments.
            **kwargs: Additional Whisper parameters

        Returns:
            Either legacy `[{"start","end","text"}]` segments or a
            `TranscriptionResult` structure containing metadata.

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio file is invalid
            RuntimeError: If transcription fails
        """
        metadata_requested = include_metadata or settings.INCLUDE_ENHANCED_METADATA
        started_at = time.time()

        if not self.validate_audio_file(audio_path):
            raise FileNotFoundError(f"Audio file not found or invalid: {audio_path}")

        try:
            logger.info(f"Transcribing audio file: {audio_path}")

            # Transcribe with faster-whisper
            # Returns: (segments, info) where segments is an iterator
            # Apply Chinese-specific optimizations when language is Chinese or auto-detect
            segments_iter, info = self.model.transcribe(
                audio_path,
                language=language,
                
                # Beam search: smaller beam reduces hallucination tendency
                beam_size=3,  # Reduced from 5 to prevent over-generation
                
                # Anti-hallucination parameters (critical for quality)
                compression_ratio_threshold=2.4,  # Detect repetitive text (e.g., "我用了一尾" × 32)
                log_prob_threshold=-1.0,          # Filter low-confidence segments
                no_speech_threshold=0.6,          # Better silence detection
                vad_filter=False,                 # Unified VAD handles silence
                
                # Chinese optimization: guide to Simplified Mandarin
                initial_prompt="以下是普通话的句子。" if (language == "zh" or language is None) else None,
                # Fully deterministic: eliminates sampling randomness
                temperature=0.0,  # Changed from 0.2 for maximum stability
                # Critical for Chinese: prevents context pollution and error propagation
                condition_on_previous_text=False,
                
                # Segment-level timestamps (better for Chinese than word-level)
                word_timestamps=False
            )

            logger.info(f"Detected language: {info.language} with probability {info.language_probability:.2f}")

            # Enhanced logging to show auto-detection vs manual specification
            detected_lang = info.language
            lang_prob = info.language_probability
            detection_mode = "auto-detected" if language is None else "user-specified"
            logger.info(
                f"Audio language: {detected_lang.upper()} "
                f"(probability: {lang_prob:.2%}, "
                f"{detection_mode})"
            )

            # Log Chinese-specific optimizations when applied
            if detected_lang == "zh":
                logger.info(
                    "Chinese audio detected - optimizations active: "
                    "beam_size=3, "
                    "compression_ratio_threshold=2.4, "
                    "log_prob_threshold=-1.0, "
                    "no_speech_threshold=0.6, "
                    "temperature=0.0, "
                    "condition_on_previous_text=False, "
                    "VAD: min_silence=700ms/speech_pad=200ms, "
                    "post-processing: Traditional→Simplified conversion"
                )

            # Extract segments with timestamps
            segments: List[BaseSegment] = []
            for segment in segments_iter:
                # faster-whisper segments have: start, end, text, words (optional)
                text = segment.text.strip()

                # Convert Traditional Chinese to Simplified Chinese for zh language
                if detected_lang == "zh":
                    try:
                        import zhconv
                        # zh-cn = Simplified Chinese
                        text = zhconv.convert(text, 'zh-cn')
                    except ImportError:
                        logger.warning(
                            "zhconv library not installed - skipping Traditional→Simplified conversion. "
                            "Install with: uv pip install zhconv"
                        )
                    except Exception as e:
                        logger.warning(f"Chinese conversion failed: {e} - using original text")

                segments.append({
                    "start": float(segment.start),
                    "end": float(segment.end),
                    "text": text
                })

            logger.info(f"Transcription complete: {len(segments)} segments")

            vad_manager = VADManager()
            filtered_segments, vad_engine = vad_manager.process_segments(
                segments=segments,
                audio_path=audio_path,
            )

            if not metadata_requested:
                return filtered_segments

            enhancements = [f"vad:{vad_engine}"] if vad_engine else []
            return build_transcription_result(
                segments=filtered_segments,
                language=language or detected_lang,
                model_name="whisperx",
                processing_time=time.time() - started_at,
                duration=self._get_audio_duration(audio_path),
                vad_enabled=bool(vad_engine),
                alignment_model="whisperx",
                enhancements_applied=enhancements,
            )

        except FileNotFoundError as e:
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        except Exception as e:
            logger.error(f"Transcription failed: {e}", exc_info=True)
            # Translate technical errors to user-friendly messages
            error_msg = str(e).lower()

            if "cuda" in error_msg or "gpu" in error_msg:
                raise RuntimeError(
                    "GPU error during transcription. Please ensure GPU is available "
                    "and has sufficient memory."
                )
            elif "memory" in error_msg:
                raise RuntimeError(
                    "Out of memory during transcription. Try with a shorter audio file."
                )
            elif "format" in error_msg or "decode" in error_msg:
                raise ValueError(
                    "Audio file format is corrupted or unsupported."
                )
            else:
                raise RuntimeError(
                    f"Transcription failed: {str(e)}"
                )

    @staticmethod
    def _get_audio_duration(audio_path: str) -> Optional[float]:
        """Best-effort audio duration lookup."""
        try:
            import librosa

            return float(librosa.get_duration(path=audio_path))
        except Exception:
            return None

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        Returns:
            List of ISO 639-1 language codes supported by WhisperX
        """
        # WhisperX supports 99 languages - returning commonly used subset
        return [
            "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru",
            "zh", "ja", "ko", "ar", "hi", "tr", "vi", "th", "id",
            "uk", "sv", "fi", "no", "da", "cs", "sk", "el", "he"
        ]

    def validate_audio_file(self, audio_path: str) -> bool:
        """
        Validate audio file exists and has supported format

        Args:
            audio_path: Path to audio file

        Returns:
            True if valid, False otherwise
        """
        # Check file exists
        if not os.path.exists(audio_path):
            return False

        # Check file extension
        supported_formats = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".webm", ".aac", ".wma"}
        file_ext = Path(audio_path).suffix.lower()

        return file_ext in supported_formats
