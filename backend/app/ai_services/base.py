"""
Abstract base class for transcription services
Defines interface for WhisperX and future AI service implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


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
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Transcribe audio file to text with timestamps

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es', 'fr')
            **kwargs: Additional service-specific parameters

        Returns:
            List of segment dictionaries with structure:
            [
                {
                    "start": float,  # Start time in seconds
                    "end": float,    # End time in seconds
                    "text": str      # Transcribed text
                },
                ...
            ]

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
