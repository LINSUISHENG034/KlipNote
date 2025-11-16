"""
Enhancement utilities for transcription services (VAD, refiners, etc.).

Story 4.2 introduces the unified Voice Activity Detection stack so backend
services can apply consistent silence filtering regardless of transcription
engine.
"""

from app.ai_services.enhancement.vad_manager import VADManager

__all__ = ["VADManager"]
