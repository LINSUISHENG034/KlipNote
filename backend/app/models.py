"""
Pydantic models for request/response validation
Will be populated in subsequent stories
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import re


class UploadResponse(BaseModel):
    """Response model for POST /upload endpoint"""
    job_id: str = Field(
        ...,
        description="Unique job identifier in UUID v4 format",
        pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    }


class StatusResponse(BaseModel):
    """Response model for job status tracking"""
    status: str = Field(
        ...,
        description="Current job status",
        pattern="^(pending|processing|completed|failed)$"
    )
    progress: int = Field(
        ...,
        description="Progress percentage (0-100)",
        ge=0,
        le=100
    )
    message: str = Field(
        ...,
        description="Human-readable status message"
    )
    created_at: str = Field(
        ...,
        description="ISO 8601 UTC timestamp when job was created"
    )
    updated_at: str = Field(
        ...,
        description="ISO 8601 UTC timestamp of last update"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "processing",
                    "progress": 40,
                    "message": "Transcribing audio...",
                    "created_at": "2025-11-05T10:30:00Z",
                    "updated_at": "2025-11-05T10:31:15Z"
                }
            ]
        }
    }


class TranscriptionSegment(BaseModel):
    """Individual subtitle segment with word-level timestamps"""
    start: float = Field(
        ...,
        description="Start time in seconds",
        ge=0.0
    )
    end: float = Field(
        ...,
        description="End time in seconds",
        gt=0.0
    )
    text: str = Field(
        ...,
        description="Transcribed text for this segment",
        min_length=1
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "start": 0.5,
                    "end": 3.2,
                    "text": "Hello, welcome to the meeting."
                }
            ]
        }
    }


class TranscriptionResult(BaseModel):
    """Complete transcription result with all segments"""
    segments: List[TranscriptionSegment] = Field(
        ...,
        description="List of transcription segments with timestamps"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "segments": [
                        {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
                        {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
                    ]
                }
            ]
        }
    }
