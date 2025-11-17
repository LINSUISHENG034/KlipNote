"""
Abstract base class for transcription services
Defines interface for WhisperX and future AI service implementations
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from app.ai_services.schema import BaseSegment, TranscriptionResult


class TranscriptionService(ABC):
    """
    Abstract base class for audio transcription services

    This interface allows for multiple transcription service implementations:
    - WhisperXService (GPU-accelerated, current implementation)
    - Future: DeepgramService, FasterWhisperService, etc.
    """

    @abstractmethod
    def transcribe(
        self,
        audio_path: str,
        language: str = "en",
        include_metadata: bool = False,
        apply_enhancements: bool = True,
        **kwargs
    ) -> Union[List[BaseSegment], TranscriptionResult]:
        """
        Transcribe audio file to text with timestamps.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            include_metadata: When True, return a TranscriptionResult payload with
                metadata + enhanced segments; otherwise return the legacy list of
                BaseSegment dictionaries for backward compatibility.
            apply_enhancements: When False, skip downstream enhancement components
                and return raw transcription segments (pipeline will handle them).
            **kwargs: Additional service-specific parameters

        Returns:
            Either a simple `List[BaseSegment]` or a structured
            `TranscriptionResult` depending on `include_metadata`.

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio file is invalid or unsupported format
            RuntimeError: If transcription fails
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """
        Get list of supported language codes

        Returns:
            List of ISO 639-1 language codes
        """
        pass

    @abstractmethod
    def validate_audio_file(self, audio_path: str) -> bool:
        """
        Validate audio file format and accessibility

        Args:
            audio_path: Path to audio file

        Returns:
            True if file is valid, False otherwise
        """
        pass
