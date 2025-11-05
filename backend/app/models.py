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


# Placeholder models for future stories
# Story 1.4: TranscriptionStatus, TranscriptionResult models
