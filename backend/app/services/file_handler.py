"""
File handling service for upload validation and storage
Handles format validation, duration checking, and file persistence
"""

import os
import uuid
import subprocess
import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import settings


class FileHandler:
    """Service class for file upload handling and validation"""

    # File extension to MIME type mapping
    EXTENSION_MIME_MAP = {
        ".mp3": "audio/mpeg",
        ".mp4": "video/mp4",
        ".wav": "audio/wav",
        ".m4a": "audio/x-m4a",
        ".wma": "audio/x-ms-wma",  # Windows Media Audio
    }

    @staticmethod
    def validate_format(file: UploadFile) -> None:
        """
        Validate uploaded file format against whitelist

        Checks both Content-Type header and file extension for maximum compatibility.
        This handles cases where clients (like Windows curl) send application/octet-stream.

        Args:
            file: FastAPI UploadFile object

        Raises:
            ValueError: If file format is not in whitelist
        """
        # First, try to validate by Content-Type header
        if file.content_type in settings.ALLOWED_FORMATS:
            return  # Valid format

        # If Content-Type is generic (application/octet-stream), check file extension
        if file.filename:
            file_ext = Path(file.filename).suffix.lower()
            if file_ext in FileHandler.EXTENSION_MIME_MAP:
                return  # Valid format based on extension

        # Neither Content-Type nor extension matched
        raise ValueError(
            f"Unsupported file format. Allowed: MP3, MP4, WAV, M4A, WMA. "
            f"Received Content-Type: {file.content_type}, "
            f"Filename: {file.filename or 'unknown'}"
        )

    @staticmethod
    def validate_duration(file_path: str) -> None:
        """
        Validate media duration using ffprobe

        Args:
            file_path: Path to the media file

        Raises:
            ValueError: If duration exceeds MAX_DURATION_HOURS
            RuntimeError: If ffprobe execution fails
        """
        try:
            # Run ffprobe to get duration in seconds
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path
                ],
                capture_output=True,
                text=True,
                check=True
            )

            duration_seconds = float(result.stdout.strip())
            max_duration_seconds = settings.MAX_DURATION_HOURS * 3600

            if duration_seconds > max_duration_seconds:
                hours = duration_seconds / 3600
                raise ValueError(
                    f"File duration exceeds {settings.MAX_DURATION_HOURS}-hour limit. "
                    f"File duration: {hours:.2f} hours"
                )

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to validate media duration: {e.stderr}")
        except ValueError as e:
            # Re-raise duration validation errors
            if "exceeds" in str(e):
                raise
            # Handle invalid ffprobe output
            raise RuntimeError(f"Invalid duration value from ffprobe: {e}")

    @staticmethod
    def generate_job_id() -> str:
        """
        Generate unique job ID using UUID v4

        Returns:
            UUID v4 string
        """
        return str(uuid.uuid4())

    @staticmethod
    def save_upload(job_id: str, file: UploadFile) -> str:
        """
        Save uploaded file to storage with job_id-based structure

        Args:
            job_id: Unique job identifier (UUID v4)
            file: FastAPI UploadFile object

        Returns:
            Absolute path to saved file

        Raises:
            IOError: If file save operation fails
        """
        # Extract file extension from filename, default to .mp3 if missing
        file_ext = Path(file.filename).suffix if (file.filename and Path(file.filename).suffix) else ".mp3"

        # Create job directory structure: /uploads/{job_id}/
        job_dir = Path(settings.UPLOAD_DIR) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save file as original.{ext}
        file_path = job_dir / f"original{file_ext}"

        try:
            # Use streaming to handle large files efficiently
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            return str(file_path.absolute())

        except Exception as e:
            raise IOError(f"Failed to save uploaded file: {e}")
