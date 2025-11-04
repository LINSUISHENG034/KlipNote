"""
FastAPI application initialization
Main entry point for the web service
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

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


# Placeholder endpoints - will be implemented in subsequent stories
# Story 1.2: POST /api/upload - Upload audio file
# Story 1.4: GET /api/transcriptions/{task_id} - Get transcription status
# Story 1.4: GET /api/transcriptions/{task_id}/result - Get transcription result
