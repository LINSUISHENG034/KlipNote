"""
AI Services module
Service factory for transcription service implementations
"""

from app.ai_services.base import TranscriptionService
from app.ai_services.whisperx_service import WhisperXService
from typing import Literal


def get_transcription_service(
    service_type: Literal["whisperx"] = "whisperx"
) -> TranscriptionService:
    """
    Factory function to get transcription service instance

    Args:
        service_type: Type of service ('whisperx', future: 'deepgram', 'faster-whisper')

    Returns:
        TranscriptionService instance

    Raises:
        ValueError: If service_type is not supported
    """
    if service_type == "whisperx":
        return WhisperXService()
    else:
        raise ValueError(f"Unsupported transcription service: {service_type}")


__all__ = [
    "TranscriptionService",
    "WhisperXService",
    "get_transcription_service"
]
