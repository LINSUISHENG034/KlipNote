"""
BELLE-2 transcription service implementation
Chinese-optimized Whisper large-v3 model from HuggingFace

BELLE-2/Belle-whisper-large-v3-zh is a full fine-tune of OpenAI Whisper large-v3
specifically optimized for Mandarin Chinese, achieving 24-65% CER improvement
over baseline Whisper models.
"""

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch
from app.ai_services.base import TranscriptionService
from app.ai_services.enhancement import VADManager
from app.ai_services.schema import BaseSegment, TranscriptionResult, build_transcription_result
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class Belle2Service(TranscriptionService):
    """
    BELLE-2 transcription service for Mandarin Chinese audio

    Uses HuggingFace Transformers to load BELLE-2/Belle-whisper-large-v3-zh,
    a Chinese-optimized fine-tune of Whisper large-v3. Implements the same
    TranscriptionService interface as WhisperXService for drop-in compatibility.

    Lazy-loads the model on first transcription to avoid startup delays.
    Uses ModelManager for LRU caching with max 2 concurrent models.
    """

    def __init__(
        self,
        model_name: str = None,
        device: str = None
    ):
        """
        Initialize BELLE-2 service

        Args:
            model_name: HuggingFace model ID (default: BELLE-2/Belle-whisper-large-v3-zh)
            device: 'cuda' for GPU or 'cpu'
        """
        # Get model name with proper fallback chain
        # Check explicit parameter first, then env vars, then default
        self.model_name = (
            model_name or
            getattr(settings, 'BELLE2_MODEL_PATH', None) or
            getattr(settings, 'BELLE2_MODEL_NAME', None) or
            'BELLE-2/Belle-whisper-large-v3-zh'
        )
        self.device = device or settings.WHISPER_DEVICE

        # Import ModelManager
        from app.ai_services.model_manager import ModelManager
        self.model_manager = ModelManager()

        # Model and processor will be loaded lazily on first transcription
        self.model = None
        self.processor = None
        self._load_time = None

        logger.info(f"Belle2Service initialized (lazy loading): {self.model_name}")

    def _load_model(self) -> None:
        """
        Lazy-load BELLE-2 model via ModelManager

        First call: Downloads model (~3.1GB, 5-10 minutes)
        Subsequent calls: Loads from cache (<5 seconds)
        """
        if self.model is not None:
            # Already loaded in this instance
            return

        try:
            start_time = time.time()
            self.model, self.processor = self.model_manager.load_belle2(
                self.model_name,
                self.device
            )
            self._load_time = time.time() - start_time

        except Exception as e:
            logger.error(f"Failed to load BELLE-2 model via ModelManager: {e}")
            raise RuntimeError(
                f"Failed to load BELLE-2 model '{self.model_name}': {str(e)}"
            )

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = "zh",
        include_metadata: bool = False,
        **kwargs
    ) -> Union[List[BaseSegment], TranscriptionResult]:
        """
        Transcribe audio file using BELLE-2 with Chinese optimizations

        Args:
            audio_path: Path to audio file
            language: Language code (defaults to 'zh' for Chinese)
            **kwargs: Additional parameters

        Returns:
            List of transcription segments with timestamps:
            [
                {"start": 0.5, "end": 3.2, "text": "你好，欢迎..."},
                ...
            ]

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio file is invalid
            RuntimeError: If transcription fails
        """
        metadata_requested = include_metadata or settings.INCLUDE_ENHANCED_METADATA
        started_at = time.time()

        if not self.validate_audio_file(audio_path):
            raise FileNotFoundError(f"Audio file not found or invalid: {audio_path}")

        # Lazy-load model if not already loaded
        if self.model is None:
            self._load_model()

        try:
            logger.info(f"Transcribing audio with BELLE-2: {audio_path}")

            # Load audio with librosa (BELLE-2 expects 16kHz audio)
            import librosa

            audio, sr = librosa.load(audio_path, sr=16000, mono=True)

            # Whisper models can only process ~30 seconds at a time
            # Split audio into 30-second chunks with no overlap
            chunk_length = 30.0  # seconds
            chunk_samples = int(chunk_length * 16000)

            all_segments = []
            num_chunks = int(np.ceil(len(audio) / chunk_samples))

            logger.info(f"Processing {num_chunks} chunks of {chunk_length}s each")

            for i in range(num_chunks):
                start_sample = i * chunk_samples
                end_sample = min((i + 1) * chunk_samples, len(audio))
                audio_chunk = audio[start_sample:end_sample]
                chunk_start_time = i * chunk_length

                # Prepare inputs for this chunk
                inputs = self.processor(
                    audio_chunk,
                    sampling_rate=16000,
                    return_tensors="pt"
                ).to(self.device)

                # Convert input features to match model dtype (float16)
                if hasattr(self.model, 'dtype'):
                    inputs.input_features = inputs.input_features.to(dtype=self.model.dtype)
                else:
                    inputs.input_features = inputs.input_features.to(dtype=torch.float16)

                # Configure Chinese-specific generation settings (forced language + temperature fallback)
                generation_config = {
                    "language": "zh",  # Force Chinese language ID
                    "task": "transcribe",
                    "temperature": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],  # Temperature fallback to curb repetitions
                    "num_beams": 5,  # Beam search for better quality
                    "max_length": 448,  # Standard Whisper chunk length
                    "compression_ratio_threshold": 2.4,
                    "logprob_threshold": -1.0,
                    "no_speech_threshold": 0.6,
                }

                # Generate transcription for this chunk
                with torch.no_grad():
                    generated_ids = self.model.generate(
                        inputs.input_features,
                        **generation_config
                    )

                # Decode twice: once with timestamps for parsing, once clean for fallback text
                transcription_with_timestamps = self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=False
                )
                transcription_clean = self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=True
                )

            # Parse into WhisperX-compatible segments
            chunk_duration = len(audio_chunk) / 16000
            chunk_segments = self._parse_segments(
                transcription_with_timestamps,
                chunk_duration
            )

            # Fallback: if timestamp parsing failed, use the clean text as a single span
            if not chunk_segments:
                fallback_text = transcription_clean[0] if transcription_clean else ""
                if fallback_text:
                    chunk_segments = [{
                        "start": 0.0,
                        "end": chunk_duration,
                        "text": fallback_text.strip()
                    }]

            # Offset chunk-relative timestamps to absolute timeline
            for segment in chunk_segments:
                all_segments.append({
                    "start": segment["start"] + chunk_start_time,
                    "end": segment["end"] + chunk_start_time,
                    "text": segment["text"]
                })

            logger.info(f"BELLE-2 transcription complete: {len(all_segments)} segments")
            vad_manager = VADManager()
            filtered_segments, vad_engine = vad_manager.process_segments(
                segments=all_segments,
                audio_path=audio_path,
            )

            if not metadata_requested:
                return filtered_segments

            enhancements = [f"vad:{vad_engine}"] if vad_engine else []
            return build_transcription_result(
                segments=filtered_segments,
                language="zh",
                model_name="belle2",
                processing_time=time.time() - started_at,
                duration=len(audio) / 16000 if "audio" in locals() else None,
                vad_enabled=bool(vad_engine),
                alignment_model="belle2",
                enhancements_applied=enhancements,
            )

        except FileNotFoundError:
            logger.error(f"Audio file not found: {audio_path}")
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        except Exception as e:
            logger.error(f"BELLE-2 transcription failed: {e}", exc_info=True)
            error_msg = str(e).lower()

            if "cuda" in error_msg or "gpu" in error_msg:
                raise RuntimeError(
                    "GPU error during BELLE-2 transcription. Please ensure GPU is available "
                    "and has sufficient memory (~6GB VRAM required)."
                )
            elif "memory" in error_msg or "out of memory" in error_msg:
                raise RuntimeError(
                    "Out of memory during BELLE-2 transcription. Model requires ~6GB VRAM."
                )
            elif "format" in error_msg or "decode" in error_msg:
                raise ValueError(
                    "Audio file format is corrupted or unsupported."
                )
            else:
                raise RuntimeError(
                    f"BELLE-2 transcription failed: {str(e)}"
                )

    def _parse_segments(
        self,
        transcription: List,
        audio_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Parse HuggingFace transcription output into WhisperX-compatible segments

        Args:
            transcription: Output from processor.batch_decode with timestamps
            audio_duration: Total audio duration in seconds

        Returns:
            List of segments with start, end, text
        """
        segments = []

        # HuggingFace Whisper returns transcription with timestamp tokens
        # Format: "<|startoftranscript|><|zh|><|transcribe|><|0.00|>text<|2.50|>text<|endoftext|>"
        for item in transcription:
            if isinstance(item, dict) and "text" in item:
                text = item["text"]
            else:
                text = str(item)

            # Parse timestamp tokens (format: <|0.00|>, <|2.50|>, etc.)
            import re
            timestamp_pattern = r'<\|(\d+\.\d+)\|>'
            timestamps = [float(ts) for ts in re.findall(timestamp_pattern, text)]

            # Remove special tokens from text
            clean_text = re.sub(r'<\|.*?\|>', '', text).strip()

            # Split by timestamps if multiple segments
            if len(timestamps) >= 2:
                # Create segments between consecutive timestamps
                text_parts = re.split(timestamp_pattern, text)
                text_parts = [p.strip() for p in text_parts if p.strip() and not re.match(r'^\d+\.\d+$', p)]

                for i in range(len(timestamps) - 1):
                    if i < len(text_parts):
                        segments.append({
                            "start": timestamps[i],
                            "end": timestamps[i + 1],
                            "text": text_parts[i]
                        })
            elif len(timestamps) == 1:
                # Single timestamp, use as start with audio duration as end
                segments.append({
                    "start": timestamps[0],
                    "end": audio_duration,
                    "text": clean_text
                })
            else:
                # No timestamps found, return full text as single segment
                if clean_text:
                    segments.append({
                        "start": 0.0,
                        "end": audio_duration,
                        "text": clean_text
                    })

        return segments

    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported languages

        BELLE-2 is specifically optimized for Chinese, but technically supports
        other languages due to Whisper base architecture.

        Returns:
            List of ISO 639-1 language codes
        """
        return ["zh", "zh-CN", "zh-TW", "zh-HK"]

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

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata for logging and debugging

        Returns:
            Dictionary with model information:
            {
                "engine": "belle2",
                "model_version": str,
                "device": str,
                "vram_usage_gb": float,
                "load_time_seconds": float
            }
        """
        return {
            "engine": "belle2",
            "model_version": self.model_name,
            "device": self.device,
            "vram_usage_gb": self.get_vram_usage(),
            "load_time_seconds": self._load_time if self._load_time else 0.0
        }

    def get_vram_usage(self) -> float:
        """
        Get current VRAM usage in GB

        Returns:
            VRAM usage in gigabytes (0.0 if CPU or CUDA unavailable)
        """
        if self.device == "cuda" and torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 3)
        return 0.0
