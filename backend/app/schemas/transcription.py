from pydantic import BaseModel, Field, root_validator
from typing import Optional, Dict, Any, List, Literal
from uuid import UUID
from datetime import datetime

from app.core.enums import BaseJobStatus
from app.core.config import settings

# --- Schemas for Configuration ---

class TranscriptionConfig(BaseModel):
    """
    Defines and validates the user-configurable parameters for a transcription job.
    This schema restores the detailed VAD parameters from the original implementation.
    """
    # Core parameters
    model_name: Literal["tiny", "base", "small", "medium", "large-v2", "large-v3"] = Field(
        default="medium", description="The Whisper model to use."
    )
    language: str = Field(
        default=settings.WHISPERX_LANGUAGE, 
        description="Target language for transcription, e.g., 'en', 'zh', 'auto'."
    )
    batch_size: int = Field(
        default=settings.BATCH_SIZE, gt=0, description="Batch size for ASR inference."
    )
    
    # Alignment parameters
    enable_alignment: bool = Field(
        default=False, description="Enable word-level alignment."
    )

    # Diarization parameters
    enable_diarization: bool = Field(
        default=False, description="Enable speaker diarization."
    )
    min_speakers: Optional[int] = Field(
        default=None, gt=0, description="Minimum number of speakers for diarization."
    )
    max_speakers: Optional[int] = Field(
        default=None, gt=0, description="Maximum number of speakers for diarization."
    )

    # VAD (Voice Activity Detection) parameters for chunking
    vad_method: Literal["silero", "pyannote"] = Field(
        default=settings.WHISPERX_VAD_METHOD, description="The VAD model to use."
    )
    vad_use_onnx: bool = Field(
        default=False, description="Use ONNX for VAD inference."
    )
    vad_threshold: float = Field(
        default=settings.WHISPERX_VAD_ONSET, ge=0.0, le=1.0, 
        description="Voice activity detection probability threshold."
    )
    min_silence_duration_ms: int = Field(
        default=700, ge=100, description="Minimum silence duration in ms for splitting."
    )
    max_chunk_duration_s: int = Field(
        default=30, description="Maximum duration of a chunk in seconds before forcing a split."
    )
    vad_speech_pad_ms: int = Field(
        default=100, description="Padding in ms to add to the start/end of a speech segment."
    )
    vad_window_size_ms: int = Field(
        default=30, description="Window size in ms for VAD processing."
    )

    @root_validator(pre=True)
    def validate_diarization_and_speakers(cls, values):
        """
        Validates that speaker counts are logical and forces alignment if
        diarization is enabled.
        """
        diarization = values.get('enable_diarization')
        align = values.get('enable_alignment')
        min_speakers = values.get('min_speakers')
        max_speakers = values.get('max_speakers')

        if diarization and not align:
            # If user enables diarization, we silently enable alignment as it's a prerequisite.
            values['enable_alignment'] = True

        if min_speakers and max_speakers and min_speakers > max_speakers:
            raise ValueError("min_speakers cannot be greater than max_speakers")

        return values

# --- Schemas for API Payloads ---

class TranscriptionCreate(BaseModel):
    """
    The schema for the 'config' part of the job creation request.
    """
    config: TranscriptionConfig = Field(default_factory=TranscriptionConfig)


# --- Schemas for API Responses ---

class TranscriptionJobRead(BaseModel):
    """
    Schema for data returned to the client when reading a transcription job.
    This is the primary response model for API endpoints.
    """
    id: UUID
    user_id: UUID
    status: BaseJobStatus
    detail_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    language: Optional[str] = None
    config: TranscriptionConfig # Return the validated config

    class Config:
        from_attributes = True # Formerly orm_mode
