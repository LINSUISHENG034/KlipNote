"""
Pydantic models for request/response validation
Will be populated in subsequent stories
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
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


class ExportRequest(BaseModel):
    """Request body for POST /export/{job_id} endpoint"""
    segments: List[TranscriptionSegment] = Field(
        ...,
        description="Edited subtitle array to export",
        min_length=1
    )
    format: Literal['srt', 'txt'] = Field(
        ...,
        description="Export format choice: 'srt' (SubRip subtitle) or 'txt' (plain text)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "segments": [
                        {"start": 0.5, "end": 3.2, "text": "Edited subtitle text"},
                        {"start": 3.5, "end": 7.8, "text": "Another edited segment"}
                    ],
                    "format": "srt"
                }
            ]
        }
    }


class ExportMetadata(BaseModel):
    """Metadata stored with edited transcription for data flywheel"""
    job_id: str = Field(
        ...,
        description="Unique job identifier"
    )
    original_segment_count: int = Field(
        ...,
        description="Number of segments in original transcription",
        ge=0
    )
    edited_segment_count: int = Field(
        ...,
        description="Number of segments in edited version",
        ge=0
    )
    export_timestamp: str = Field(
        ...,
        description="ISO 8601 UTC timestamp when export was generated"
    )
    format_requested: str = Field(
        ...,
        description="Export format requested: 'srt' or 'txt'"
    )
    changes_detected: int = Field(
        ...,
        description="Number of segments with text differences from original",
        ge=0
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "550e8400-e29b-41d4-a716-446655440000",
                    "original_segment_count": 45,
                    "edited_segment_count": 45,
                    "export_timestamp": "2025-11-07T14:30:00Z",
                    "format_requested": "srt",
                    "changes_detected": 7
                }
            ]
        }
    }
