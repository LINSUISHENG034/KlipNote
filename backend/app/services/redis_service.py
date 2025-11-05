"""
Redis service for job status and result storage
Manages job status tracking and transcription result persistence
"""

import json
import redis
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from app.config import settings


class RedisService:
    """
    Redis service for managing transcription job status and results

    Stores data in Redis with the following key patterns:
    - job:{job_id}:status - Job status with progress tracking
    - job:{job_id}:result - Transcription result with segments
    """

    def __init__(self):
        """Initialize Redis client from settings"""
        # Extract host and port from CELERY_BROKER_URL
        # Format: redis://host:port/db
        broker_url = settings.CELERY_BROKER_URL

        # Parse Redis connection URL
        if broker_url.startswith("redis://"):
            parts = broker_url.replace("redis://", "").split("/")
            host_port = parts[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 6379
            db = int(parts[1]) if len(parts) > 1 else 0
        else:
            host = "localhost"
            port = 6379
            db = 0

        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True  # Automatically decode bytes to strings
        )

    def _get_utc_timestamp(self) -> str:
        """
        Generate ISO 8601 UTC timestamp

        Returns:
            ISO 8601 formatted UTC timestamp (e.g., "2025-11-05T10:30:00Z")
        """
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _validate_job_id(self, job_id: str) -> None:
        """
        Validate job_id is a valid UUID v4 to prevent injection attacks

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

    def set_status(
        self,
        job_id: str,
        status: str,
        progress: int,
        message: str,
        preserve_created_at: bool = True
    ) -> None:
        """
        Update job status in Redis

        Args:
            job_id: Unique job identifier (UUID v4)
            status: Job status ('pending', 'processing', 'completed', 'failed')
            progress: Progress percentage (0-100)
            message: Human-readable status message
            preserve_created_at: If True, preserve existing created_at timestamp

        Stores JSON with structure:
        {
            "status": "processing",
            "progress": 40,
            "message": "Transcribing audio...",
            "created_at": "2025-11-05T10:30:00Z",
            "updated_at": "2025-11-05T10:31:15Z"
        }
        """
        self._validate_job_id(job_id)
        key = f"job:{job_id}:status"

        # Get existing status to preserve created_at if requested
        created_at = self._get_utc_timestamp()
        if preserve_created_at:
            existing_status = self.get_status(job_id)
            if existing_status and "created_at" in existing_status:
                created_at = existing_status["created_at"]

        status_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "created_at": created_at,
            "updated_at": self._get_utc_timestamp()
        }

        self.client.set(key, json.dumps(status_data))

    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve job status from Redis

        Args:
            job_id: Unique job identifier

        Returns:
            Dictionary with status data, or None if not found
        """
        self._validate_job_id(job_id)
        key = f"job:{job_id}:status"
        data = self.client.get(key)

        if data is None:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def set_result(self, job_id: str, segments: List[Dict[str, Any]]) -> None:
        """
        Store transcription result in Redis

        Args:
            job_id: Unique job identifier
            segments: List of transcription segments with start, end, text

        Stores JSON with structure:
        {
            "segments": [
                {"start": 0.5, "end": 3.2, "text": "Hello, welcome..."},
                ...
            ]
        }
        """
        self._validate_job_id(job_id)
        key = f"job:{job_id}:result"
        result_data = {"segments": segments}
        self.client.set(key, json.dumps(result_data))

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve transcription result from Redis

        Args:
            job_id: Unique job identifier

        Returns:
            Dictionary with segments array, or None if not found
        """
        self._validate_job_id(job_id)
        key = f"job:{job_id}:result"
        data = self.client.get(key)

        if data is None:
            return None

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def delete_job_data(self, job_id: str) -> None:
        """
        Delete all job-related data from Redis (status and result)

        Args:
            job_id: Unique job identifier
        """
        self._validate_job_id(job_id)
        status_key = f"job:{job_id}:status"
        result_key = f"job:{job_id}:result"
        self.client.delete(status_key, result_key)

    def ping(self) -> bool:
        """
        Test Redis connection

        Returns:
            True if Redis is reachable, False otherwise
        """
        try:
            return self.client.ping()
        except redis.ConnectionError:
            return False
