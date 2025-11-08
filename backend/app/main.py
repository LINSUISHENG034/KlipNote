"""
FastAPI application initialization
Main entry point for the web service
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pathlib import Path
import re
import logging
import os
from app.config import settings
from app.models import UploadResponse, StatusResponse, TranscriptionResult, ExportRequest
from app.services.file_handler import FileHandler
from app.services.redis_service import RedisService
from app.services import export_service
from app.tasks.transcription import transcribe_audio

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="KlipNote API",
    description="Audio transcription service with WhisperX",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "service": "KlipNote API",
        "status": "running",
        "version": "0.1.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "whisper_model": settings.WHISPER_MODEL,
        "whisper_device": settings.WHISPER_DEVICE
    }


@app.post("/upload", response_model=UploadResponse, status_code=200)
async def upload_file(file: UploadFile = File(...)):
    """
    Upload audio/video file for transcription

    Accepts multipart/form-data file uploads with the following validations:
    - **Format**: MP3, MP4, WAV, M4A only
    - **Duration**: Maximum 2 hours
    - **Size**: Maximum 2GB

    The file is saved to storage and a Celery task is queued for async transcription.
    Returns a unique job_id (UUID v4) for tracking the transcription task.

    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/upload" \\
         -F "file=@/path/to/audio.mp3"
    ```

    **Example Response:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    ```

    **Error Responses:**
    - **400**: Invalid format or duration exceeds 2 hours
    - **413**: File size exceeds 2GB limit
    - **500**: Storage or processing error
    """
    try:
        # Validate file format (MIME type)
        FileHandler.validate_format(file)

        # Generate unique job ID
        job_id = FileHandler.generate_job_id()

        # Save uploaded file to storage
        file_path = FileHandler.save_upload(job_id, file)

        # Validate media duration after file is saved
        FileHandler.validate_duration(file_path)

        # Initialize Redis service
        redis_service = RedisService()

        # Queue Celery task for transcription
        transcribe_audio.delay(job_id, file_path)

        # Initialize Redis status to "pending" (Stage 1 will update this)
        redis_service.set_status(
            job_id=job_id,
            status="pending",
            progress=10,
            message="Task queued...",
            preserve_created_at=False
        )

        return UploadResponse(job_id=job_id)

    except ValueError as e:
        # Format or duration validation errors
        raise HTTPException(status_code=400, detail=str(e))

    except IOError as e:
        # File storage errors
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")

    except RuntimeError as e:
        # FFprobe execution errors
        raise HTTPException(status_code=500, detail=f"Media validation error: {str(e)}")

    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


# Add middleware to handle file size limits
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    """Middleware to enforce maximum upload file size"""
    if request.method == "POST" and "/upload" in str(request.url):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > settings.MAX_FILE_SIZE:
            return HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {settings.MAX_FILE_SIZE / (1024**3):.1f}GB"
            )

    response = await call_next(request)
    return response


@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    """
    Retrieve current status and progress of transcription job

    Returns the current processing state, progress percentage, and descriptive message
    for the specified job. Useful for polling to determine when transcription is complete.

    **Progress Stages:**
    - **10%**: Task queued...
    - **20%**: Loading AI model...
    - **40%**: Transcribing audio... (longest stage)
    - **80%**: Aligning timestamps...
    - **100%**: Processing complete!

    **Response Fields:**
    - **status**: One of: pending, processing, completed, failed
    - **progress**: Integer percentage (0-100)
    - **message**: User-friendly stage description
    - **created_at**: ISO 8601 UTC timestamp when job was created
    - **updated_at**: ISO 8601 UTC timestamp of last status update

    **Example Request:**
    ```bash
    curl -X GET "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
    ```

    **Example Response:**
    ```json
    {
        "status": "processing",
        "progress": 40,
        "message": "Transcribing audio...",
        "created_at": "2025-11-05T10:30:00Z",
        "updated_at": "2025-11-05T10:31:15Z"
    }
    ```

    **Error Responses:**
    - **404**: Job ID not found (invalid or non-existent UUID)
    """
    redis_service = RedisService()

    try:
        status_data = redis_service.get_status(job_id)
    except ValueError as e:
        # Invalid UUID format
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    if status_data is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    return StatusResponse(**status_data)


@app.get("/result/{job_id}", response_model=TranscriptionResult)
async def get_result(job_id: str) -> TranscriptionResult:
    """
    Retrieve completed transcription result

    Returns the full transcription with word-level timestamps segmented into subtitle chunks.
    Only available after the job status is "completed". Use GET /status/{job_id} to check completion.

    **Response Fields:**
    - **segments**: Array of subtitle segments, each containing:
      - **start**: Start time in seconds (float)
      - **end**: End time in seconds (float)
      - **text**: Transcribed text for this segment

    **Example Request:**
    ```bash
    curl -X GET "http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000"
    ```

    **Example Response:**
    ```json
    {
        "segments": [
            {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
            {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
        ]
    }
    ```

    **Error Responses:**
    - **404**: Job not found, not yet complete, or transcription failed
      - Returns specific error message based on job state:
        - Job not found: Invalid or non-existent UUID
        - Not complete: Job is still pending or processing
        - Failed: Transcription error with details from status message
    """
    redis_service = RedisService()

    # Check status first to provide better error messages
    try:
        status_data = redis_service.get_status(job_id)
    except ValueError as e:
        # Invalid UUID format
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    if status_data is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    # Handle failed jobs
    if status_data.get("status") == "failed":
        raise HTTPException(
            status_code=404,
            detail=f"Transcription failed: {status_data.get('message', 'Unknown error')}"
        )

    # Handle incomplete jobs
    if status_data.get("status") != "completed":
        raise HTTPException(
            status_code=404,
            detail=f"Transcription not yet complete. Current status: {status_data.get('status')}"
        )

    # Retrieve result
    try:
        result_data = redis_service.get_result(job_id)
    except ValueError as e:
        # Invalid UUID format (shouldn't reach here, but defensive)
        raise HTTPException(
            status_code=404,
            detail="Job not found. Please check the job ID and try again."
        )

    if result_data is None:
        raise HTTPException(
            status_code=404,
            detail="Transcription result not found. Please try again later."
        )

    return TranscriptionResult(**result_data)


@app.get("/media/{job_id}")
async def serve_media(job_id: str):
    """
    Serve uploaded media file with HTTP Range support for seeking

    Returns the original uploaded audio/video file for playback in browser.
    Supports HTTP Range requests enabling smooth seeking in HTML5 media players.

    **Supported Formats:**
    - Audio: MP3, WAV, M4A, WMA
    - Video: MP4

    **Features:**
    - HTTP Range request support (206 Partial Content responses)
    - Accept-Ranges: bytes header for browser compatibility
    - Automatic Content-Type detection based on file extension

    **Example Request:**
    ```bash
    curl -X GET "http://localhost:8000/media/550e8400-e29b-41d4-a716-446655440000"
    ```

    **Example Response Headers:**
    ```
    HTTP/1.1 200 OK
    Content-Type: audio/mpeg
    Accept-Ranges: bytes
    Content-Length: 5242880
    ```

    **Range Request Example:**
    ```bash
    curl -X GET "http://localhost:8000/media/550e8400-e29b-41d4-a716-446655440000" \\
         -H "Range: bytes=0-1023"
    ```

    **Range Response:**
    ```
    HTTP/1.1 206 Partial Content
    Content-Type: audio/mpeg
    Content-Range: bytes 0-1023/5242880
    Content-Length: 1024
    ```

    **Error Responses:**
    - **400**: Invalid job ID format (must be UUID)
    - **404**: Job ID not found or media file missing
    """
    # Validate job_id format (UUID) to prevent path traversal attacks
    UUID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
    if not UUID_PATTERN.match(job_id):
        logger.warning(f"Invalid job_id format attempted: {job_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format. Must be a valid UUID."
        )

    # Locate job directory
    job_dir = Path(settings.UPLOAD_DIR) / job_id
    if not job_dir.exists():
        logger.warning(f"Job directory not found: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found"
        )

    # Find original.{ext} file
    media_files = list(job_dir.glob("original.*"))
    if not media_files:
        logger.warning(f"Media file not found for job: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Media file not found for job {job_id}"
        )

    # Warn if multiple original files exist (ambiguous scenario)
    if len(media_files) > 1:
        logger.warning(f"Multiple media files found for job {job_id}: {[f.name for f in media_files]}. Using first match: {media_files[0].name}")

    media_path = media_files[0]

    # Determine Content-Type from extension using FileHandler mapping
    ext = media_path.suffix.lower()
    content_type = FileHandler.EXTENSION_MIME_MAP.get(ext, "application/octet-stream")

    logger.info(f"Serving media file: {job_id}/{media_path.name} (type: {content_type})")

    # FileResponse automatically handles Range requests
    return FileResponse(
        path=str(media_path),
        media_type=content_type,
        filename=f"media{ext}"
    )


@app.post("/export/{job_id}")
async def export_transcription(job_id: str, request: ExportRequest):
    """
    Export edited transcription with data flywheel storage

    Accepts edited subtitle segments, generates SRT or TXT export file,
    and stores both original and edited versions for model improvement.

    **Supported Export Formats:**
    - **srt**: SubRip subtitle format with timestamps (HH:MM:SS,mmm)
    - **txt**: Plain text format (space-separated, no timestamps)

    **Data Flywheel:**
    Automatically captures human edits by comparing original vs edited transcriptions.
    Creates two files in /uploads/{job_id}/:
    - edited.json: Complete edited transcription with metadata
    - export_metadata.json: Export metadata (changes detected, timestamp, format)

    **Request Body:**
    ```json
    {
        "segments": [
            {"start": 0.5, "end": 3.2, "text": "Edited subtitle text"},
            {"start": 3.5, "end": 7.8, "text": "Another edited segment"}
        ],
        "format": "srt"
    }
    ```

    **Example Request:**
    ```bash
    curl -X POST "http://localhost:8000/export/550e8400-e29b-41d4-a716-446655440000" \\
         -H "Content-Type: application/json" \\
         -d '{"segments": [...], "format": "srt"}'
    ```

    **Response:**
    File download with appropriate Content-Type and Content-Disposition headers.
    Filename format: transcript-{job_id}.{ext}

    **Error Responses:**
    - **400**: Empty segments array or invalid request data
    - **404**: Job not found (no transcription.json exists)
    - **422**: Invalid format value (must be 'srt' or 'txt')
    """
    # Validate job_id format (UUID) to prevent path traversal
    UUID_PATTERN = re.compile(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', re.IGNORECASE)
    if not UUID_PATTERN.match(job_id):
        logger.warning(f"Invalid job_id format attempted in export: {job_id}")
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID format. Must be a valid UUID."
        )

    # Validate job exists by checking for transcription.json
    uploads_dir = Path(settings.UPLOAD_DIR) / job_id
    transcription_path = uploads_dir / "transcription.json"

    if not transcription_path.exists():
        logger.warning(f"Export attempted for non-existent job: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found. Please ensure transcription is complete."
        )

    logger.info(f"Export requested: job={job_id}, format={request.format}, segments={len(request.segments)}")

    # Generate export file based on format
    try:
        if request.format == 'srt':
            content = export_service.generate_srt(request.segments)
            media_type = "application/x-subrip"
            filename = f"transcript-{job_id}.srt"
        else:  # txt
            content = export_service.generate_txt(request.segments)
            media_type = "text/plain"
            filename = f"transcript-{job_id}.txt"

        # Data flywheel: store edited version and metadata
        metadata = export_service.save_edited_transcription(
            job_id=job_id,
            segments=request.segments,
            format_requested=request.format
        )

        logger.info(f"Data flywheel: Detected {metadata.changes_detected} edited segments for job {job_id}")
        logger.info(f"Export generated: {filename} ({len(content)} bytes)")

        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except FileNotFoundError as e:
        logger.error(f"Transcription file missing during export: {job_id}")
        raise HTTPException(
            status_code=404,
            detail=f"Original transcription not found for job {job_id}"
        )

    except Exception as e:
        logger.error(f"Export generation failed for job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Export generation failed: {str(e)}"
        )
