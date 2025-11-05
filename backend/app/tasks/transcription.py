"""
Celery task for audio transcription using WhisperX
Implements 5-stage progress tracking and result storage
"""

import os
import json
import logging
import uuid
from typing import Dict, Any
from celery import shared_task
from celery.exceptions import Retry
from app.ai_services.whisperx_service import WhisperXService
from app.services.redis_service import RedisService
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)


def validate_job_id(job_id: str) -> None:
    """
    Validate job_id is a valid UUID v4 to prevent path traversal attacks

    Args:
        job_id: Job identifier to validate

    Raises:
        ValueError: If job_id is not a valid UUID v4
    """
    try:
        uuid_obj = uuid.UUID(job_id, version=4)
        if str(uuid_obj) != job_id:
            raise ValueError("job_id format mismatch")
    except (ValueError, AttributeError) as e:
        raise ValueError(f"Invalid job_id: must be UUID v4 format, got {job_id}") from e


@shared_task(
    bind=True,
    name="app.tasks.transcription.transcribe_audio",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True
)
def transcribe_audio(self, job_id: str, file_path: str) -> Dict[str, Any]:
    """
    Transcribe audio file using WhisperX with 5-stage progress tracking

    Stages:
    1. (10%) Task queued...
    2. (20%) Loading AI model...
    3. (40%) Transcribing audio...
    4. (80%) Aligning timestamps...
    5. (100%) Processing complete!

    Args:
        self: Celery task instance (from bind=True)
        job_id: Unique job identifier (UUID v4)
        file_path: Path to audio file to transcribe

    Returns:
        Dictionary with transcription result:
        {
            "segments": [
                {"start": 0.5, "end": 3.2, "text": "Hello..."},
                ...
            ]
        }

    Raises:
        Retry: On transient failures (Redis connection, GPU memory)
        RuntimeError: On permanent failures (corrupted file, GPU error)
    """
    redis_service = RedisService()

    # Validate job_id is UUID v4 to prevent path traversal attacks
    validate_job_id(job_id)

    try:
        # ======================================================================
        # STAGE 1: Task queued (10%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 1: Task queued")
        redis_service.set_status(
            job_id=job_id,
            status="pending",
            progress=10,
            message="Task queued...",
            preserve_created_at=False  # Set initial created_at
        )

        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # ======================================================================
        # STAGE 2: Loading AI model (20%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 2: Loading AI model")
        redis_service.set_status(
            job_id=job_id,
            status="processing",
            progress=20,
            message="Loading AI model..."
        )

        # Initialize WhisperX service (model is cached after first load)
        whisperx_service = WhisperXService()

        # ======================================================================
        # STAGE 3: Transcribing audio (40%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 3: Transcribing audio")
        redis_service.set_status(
            job_id=job_id,
            status="processing",
            progress=40,
            message="Transcribing audio..."
        )

        # Call WhisperX transcription
        segments = whisperx_service.transcribe(
            audio_path=file_path,
            language="en"  # TODO: Auto-detect language in future story
        )

        # ======================================================================
        # STAGE 4: Aligning timestamps (80%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 4: Aligning timestamps (already done in WhisperX)")
        redis_service.set_status(
            job_id=job_id,
            status="processing",
            progress=80,
            message="Aligning timestamps..."
        )

        # Note: Alignment is already done in WhisperXService.transcribe()
        # This stage is kept for UI progress consistency

        # ======================================================================
        # STAGE 5: Saving results (100%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 5: Saving results")

        # Save result to Redis
        redis_service.set_result(job_id=job_id, segments=segments)

        # Save result to disk: /uploads/{job_id}/transcription.json
        job_dir = os.path.join(settings.UPLOAD_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        transcription_file = os.path.join(job_dir, "transcription.json")
        result_data = {"segments": segments}

        with open(transcription_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        # Verify file was written successfully
        if not os.path.exists(transcription_file) or os.path.getsize(transcription_file) == 0:
            raise IOError("Failed to write transcription file")

        logger.info(f"[Job {job_id}] Transcription saved to {transcription_file}")

        # Update status to completed
        redis_service.set_status(
            job_id=job_id,
            status="completed",
            progress=100,
            message="Processing complete!"
        )

        logger.info(f"[Job {job_id}] Transcription task completed successfully")
        return result_data

    except FileNotFoundError as e:
        # File not found - permanent failure
        error_msg = f"Audio file not found: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}")

        redis_service.set_status(
            job_id=job_id,
            status="failed",
            progress=0,
            message="File not found. Please re-upload the file."
        )
        raise RuntimeError(error_msg)

    except ValueError as e:
        # Invalid file format - permanent failure
        error_msg = f"Invalid audio file: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}")

        redis_service.set_status(
            job_id=job_id,
            status="failed",
            progress=0,
            message="Audio file is corrupted or in an unsupported format."
        )
        raise RuntimeError(error_msg)

    except ConnectionError as e:
        # Redis connection error - transient, retry
        error_msg = f"Redis connection error: {str(e)}"
        logger.warning(f"[Job {job_id}] {error_msg} - Retrying...")

        # Don't update status (Redis might be down)
        # Task will auto-retry due to autoretry_for
        raise Retry(exc=e, countdown=5)

    except Exception as e:
        # Unexpected error - log and mark as failed
        error_msg = f"Transcription failed: {str(e)}"
        logger.error(f"[Job {job_id}] {error_msg}", exc_info=True)

        # Try to update status to failed
        try:
            # Determine user-friendly error message
            user_message = "Transcription failed due to an unexpected error."

            if "cuda" in str(e).lower() or "gpu" in str(e).lower():
                user_message = "GPU error. Please ensure GPU is available and has sufficient memory."
            elif "memory" in str(e).lower():
                user_message = "Out of memory. Try with a shorter audio file."

            redis_service.set_status(
                job_id=job_id,
                status="failed",
                progress=0,
                message=user_message
            )
        except Exception as status_error:
            logger.error(f"[Job {job_id}] Failed to update error status: {status_error}")

        raise RuntimeError(error_msg)
