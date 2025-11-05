"""
FastAPI application initialization
Main entry point for the web service
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import UploadResponse, StatusResponse, TranscriptionResult
from app.services.file_handler import FileHandler
from app.services.redis_service import RedisService
from app.tasks.transcription import transcribe_audio

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
    allow_origins=settings.cors_origins_list,
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

