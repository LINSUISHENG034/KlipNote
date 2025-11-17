"""
Celery task for audio transcription using WhisperX and BELLE-2
Implements 5-stage progress tracking with multi-model support
"""

import os
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, TYPE_CHECKING
from celery import shared_task
from celery.exceptions import Retry
from app.services.redis_service import RedisService
from app.config import settings
from app.ai_services.enhancement.factory import create_pipeline

# Lazy imports to avoid loading PyTorch in web container
if TYPE_CHECKING:
    from app.ai_services.whisperx_service import WhisperXService
    from app.ai_services.belle2_service import Belle2Service
    from app.ai_services.base import TranscriptionService

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


def select_transcription_service(
    job_id: str,
    redis_service: RedisService,
    language: Optional[str] = None
) -> Tuple["TranscriptionService", str, Dict[str, Any]]:
    """
    Select appropriate transcription service based on language

    Args:
        job_id: Job identifier for logging
        redis_service: Redis service for status updates
        language: Language code ('zh' for Chinese, 'en' for English, None for auto-detect)

    Returns:
        Tuple of (transcription_service, model_name, selection_details)
    """
    # Lazy import to avoid loading PyTorch in web container
    from app.ai_services.belle2_service import Belle2Service
    from app.ai_services.whisperx_service import WhisperXService

    selection_details: Dict[str, Any] = {
        "detected_language": language or "auto",
        "user_language_hint": language,
        "selection_reason": None,
        "fallback_reason": None
    }

    # Try BELLE-2 for Chinese audio (explicit or auto-detected)
    if language == "zh" or language is None:
        try:
            logger.info(f"[Job {job_id}] Attempting to load BELLE-2 for Chinese audio")
            redis_service.set_status(
                job_id=job_id,
                status="processing",
                progress=20,
                message="Loading BELLE-2 model for Mandarin..."
            )

            service = Belle2Service()
            logger.info(f"[Job {job_id}] BELLE-2 loaded successfully")
            selection_details["selection_reason"] = (
                "language_hint_zh" if language == "zh" else "auto_detected_zh"
            )
            return service, "belle2", selection_details

        except Exception as e:
            # BELLE-2 load failed, fall back to WhisperX
            logger.warning(
                f"[Job {job_id}] BELLE-2 load failed: {e}. Falling back to WhisperX."
            )

            redis_service.set_status(
                job_id=job_id,
                status="processing",
                progress=20,
                message="BELLE-2 unavailable, using WhisperX fallback..."
            )

            selection_details["selection_reason"] = "belle2_load_failed"
            selection_details["fallback_reason"] = str(e)

    # Use WhisperX as default or fallback
    logger.info(f"[Job {job_id}] Using WhisperX service")
    redis_service.set_status(
        job_id=job_id,
        status="processing",
        progress=20,
        message="Loading AI model..."
    )

    service = WhisperXService()
    if not selection_details.get("selection_reason"):
        selection_details["selection_reason"] = (
            "language_not_chinese" if language and language != "zh" else "default_whisperx"
        )

    return service, "whisperx", selection_details


def save_model_metadata(
    job_id: str,
    model_name: str,
    service: "TranscriptionService",
    selection_details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Save model metadata to job directory

    Args:
        job_id: Job identifier
        model_name: Model name ('belle2' or 'whisperx')
        service: Transcription service instance
    """
    try:
        job_dir = os.path.join(settings.UPLOAD_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        metadata_file = os.path.join(job_dir, "model_metadata.json")

        # Get model info if service supports it
        model_info = {}
        if hasattr(service, 'get_model_info'):
            model_info = service.get_model_info()
        else:
            model_info = {
                "engine": model_name,
                "model_version": "unknown"
            }

        enriched_metadata = {
            "job_id": job_id,
            "selected_engine": model_info.get("engine", model_name),
            "model_version": model_info.get("model_version", "unknown"),
            "device": model_info.get("device"),
            "vram_usage_gb": model_info.get("vram_usage_gb"),
            "model_load_time_ms": round(
                float(model_info.get("load_time_seconds") or 0.0) * 1000, 3
            ),
            "detected_language": (selection_details or {}).get("detected_language"),
            "user_language_hint": (selection_details or {}).get("user_language_hint"),
            "selection_reason": (selection_details or {}).get("selection_reason"),
            "fallback_reason": (selection_details or {}).get("fallback_reason"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(enriched_metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"[Job {job_id}] Model metadata saved: {model_name}")

    except Exception as e:
        logger.warning(f"[Job {job_id}] Failed to save model metadata: {e}")


@shared_task(
    bind=True,
    name="app.tasks.transcription.transcribe_audio",
    max_retries=3,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600,  # Max 10 minutes
    retry_jitter=True
)
def transcribe_audio(self, job_id: str, file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribe audio file using BELLE-2 (Chinese) or WhisperX with fallback

    Stages:
    1. (10%) Task queued...
    2. (20%) Loading AI model... (BELLE-2 for Chinese, WhisperX fallback)
    3. (40%) Transcribing audio...
    4. (80%) Aligning timestamps...
    5. (100%) Processing complete!

    Args:
        self: Celery task instance (from bind=True)
        job_id: Unique job identifier (UUID v4)
        file_path: Path to audio file to transcribe
        language: Language code ('zh', 'en', etc.) or None for auto-detect

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

        # In multi-worker architecture, use MODEL environment variable to determine service
        # Each worker container has MODEL set to "belle2" or "whisperx"
        worker_model = os.getenv("MODEL", "whisperx").lower()

        selection_details = {
            "detected_language": language or "auto",
            "user_language_hint": language,
            "selection_reason": f"worker_queue_{worker_model}",
            "fallback_reason": None
        }

        if worker_model == "belle2":
            try:
                logger.info(f"[Job {job_id}] Loading BELLE-2 (worker queue: belle2)")
                redis_service.set_status(
                    job_id=job_id,
                    status="processing",
                    progress=20,
                    message="Loading BELLE-2 model for Mandarin..."
                )
                transcription_service = _load_belle2_service()
                model_name = "belle2"
                logger.info(f"[Job {job_id}] BELLE-2 loaded successfully")
            except Exception as e:
                # BELLE-2 load failed, fall back to WhisperX
                logger.warning(f"[Job {job_id}] BELLE-2 load failed: {e}. Falling back to WhisperX.")
                redis_service.set_status(
                    job_id=job_id,
                    status="processing",
                    progress=20,
                    message="BELLE-2 unavailable, using WhisperX fallback..."
                )
                selection_details["selection_reason"] = "belle2_load_failed"
                selection_details["fallback_reason"] = str(e)
                transcription_service = _load_whisperx_service()
                model_name = "whisperx"
        else:
            logger.info(f"[Job {job_id}] Loading WhisperX (worker queue: whisperx)")
            redis_service.set_status(
                job_id=job_id,
                status="processing",
                progress=20,
                message="Loading AI model..."
            )
            transcription_service = _load_whisperx_service()
            model_name = "whisperx"
            logger.info(f"[Job {job_id}] WhisperX loaded successfully")

        # ======================================================================
        # STAGE 3: Transcribing audio (40%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 3: Transcribing audio with {model_name}")
        redis_service.set_status(
            job_id=job_id,
            status="processing",
            progress=40,
            message="Transcribing audio..."
        )

        # Call transcription with automatic language detection if not specified
        pipeline_enabled = bool(settings.ENABLE_ENHANCEMENTS)
        segments_or_result = transcription_service.transcribe(
            audio_path=file_path,
            language=language,  # None = auto-detect, 'zh' = Chinese, 'en' = English
            include_metadata=True,
            apply_enhancements=not pipeline_enabled,
        )

        if isinstance(segments_or_result, dict):
            result_data = dict(segments_or_result)
        else:
            result_data = {"segments": list(segments_or_result)}

        pipeline_metrics = None
        if pipeline_enabled:
            try:
                pipeline = create_pipeline()
            except ValueError as config_error:
                logger.error(
                    "[Job %s] Invalid enhancement pipeline config: %s",
                    job_id,
                    config_error,
                )
                pipeline = None

            if pipeline and not pipeline.is_empty():
                enhanced_segments, pipeline_metrics = pipeline.process(
                    segments=result_data.get("segments", []),
                    audio_path=file_path,
                    language=language,
                )
                result_data["segments"] = enhanced_segments
                stats = result_data.setdefault("stats", {})
                stats["enhancement_pipeline"] = pipeline_metrics
                metadata = result_data.setdefault("metadata", {})
                metadata["enhancement_pipeline"] = pipeline_metrics.get("pipeline_config")
                metadata["enhancements_applied"] = pipeline_metrics.get(
                    "applied_enhancements"
                )
                logger.info(
                    "[Job %s] Enhancement pipeline metrics: %s",
                    job_id,
                    pipeline_metrics,
                )
            else:
                logger.info(
                    "[Job %s] Enhancement pipeline skipped (no components configured)",
                    job_id,
                )
        else:
            logger.info(
                "[Job %s] Enhancements disabled via ENABLE_ENHANCEMENTS=false",
                job_id,
            )

        # ======================================================================
        # STAGE 4: Aligning timestamps (80%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 4: Aligning timestamps (already done in service)")
        redis_service.set_status(
            job_id=job_id,
            status="processing",
            progress=80,
            message="Aligning timestamps..."
        )

        # Note: Alignment is already done in transcription services
        # This stage is kept for UI progress consistency

        # ======================================================================
        # STAGE 5: Saving results (100%)
        # ======================================================================
        logger.info(f"[Job {job_id}] Stage 5: Saving results")

        # Save result to Redis
        redis_service.set_result(job_id=job_id, segments=result_data.get("segments", []))

        # Save result to disk: /uploads/{job_id}/transcription.json
        job_dir = os.path.join(settings.UPLOAD_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        transcription_file = os.path.join(job_dir, "transcription.json")
        with open(transcription_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)

        # Verify file was written successfully
        if not os.path.exists(transcription_file) or os.path.getsize(transcription_file) == 0:
            raise IOError("Failed to write transcription file")

        logger.info(f"[Job {job_id}] Transcription saved to {transcription_file}")

        # Save model metadata
        save_model_metadata(job_id, model_name, transcription_service, selection_details)

        # Update status to completed
        redis_service.set_status(
            job_id=job_id,
            status="completed",
            progress=100,
            message="Processing complete!"
        )

        logger.info(f"[Job {job_id}] Transcription task completed successfully using {model_name}")
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
# Helper factories so tests can patch without importing heavy dependencies.
def _load_belle2_service() -> "TranscriptionService":
    from app.ai_services.belle2_service import Belle2Service

    return Belle2Service()


def _load_whisperx_service() -> "TranscriptionService":
    from app.ai_services.whisperx_service import WhisperXService

    return WhisperXService()
