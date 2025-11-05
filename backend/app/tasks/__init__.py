"""
Celery tasks module
Async task definitions for background processing
"""

from .transcription import transcribe_audio

# Story 1.3: transcribe_audio_task - WhisperX transcription task
