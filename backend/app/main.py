"""
FastAPI application initialization
Main entry point for the web service
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.models import UploadResponse
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


# Placeholder endpoints - will be implemented in subsequent stories
# Story 1.2: POST /api/upload - Upload audio file
# Story 1.4: GET /api/transcriptions/{task_id} - Get transcription status
# Story 1.4: GET /api/transcriptions/{task_id}/result - Get transcription result
