"""
Tests for RedisService
Tests status and result storage/retrieval with fakeredis
"""

import pytest
import json
import time
import uuid
from datetime import datetime
from app.services.redis_service import RedisService
import fakeredis


@pytest.fixture
def redis_service(monkeypatch):
    """Fixture providing RedisService with fakeredis backend"""
    # Patch Redis client to use fakeredis
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr("app.services.redis_service.redis.Redis", lambda **kwargs: fake_redis)

    service = RedisService()
    return service


def test_set_and_get_status(redis_service):
    """Test setting and retrieving job status"""
    job_id = str(uuid.uuid4())

    # Set initial status
    redis_service.set_status(
        job_id=job_id,
        status="pending",
        progress=10,
        message="Task queued...",
        preserve_created_at=False
    )

    # Retrieve status
    status = redis_service.get_status(job_id)

    assert status is not None
    assert status["status"] == "pending"
    assert status["progress"] == 10
    assert status["message"] == "Task queued..."
    assert "created_at" in status
    assert "updated_at" in status

    # Verify timestamps are in ISO 8601 UTC format
    assert status["created_at"].endswith("Z")
    assert status["updated_at"].endswith("Z")


def test_set_status_preserves_created_at(redis_service):
    """Test that updating status preserves original created_at timestamp"""
    job_id = str(uuid.uuid4())

    # Set initial status
    redis_service.set_status(
        job_id=job_id,
        status="pending",
        progress=10,
        message="Task queued...",
        preserve_created_at=False
    )

    initial_status = redis_service.get_status(job_id)
    initial_created_at = initial_status["created_at"]

    # Delay to ensure timestamp changes (timestamps are at second precision)
    time.sleep(1.1)

    # Update status (preserve_created_at=True by default)
    redis_service.set_status(
        job_id=job_id,
        status="processing",
        progress=40,
        message="Transcribing audio...",
        preserve_created_at=True
    )

    updated_status = redis_service.get_status(job_id)

    # created_at should be preserved, updated_at should change
    assert updated_status["created_at"] == initial_created_at
    assert updated_status["updated_at"] != initial_status["updated_at"]
    assert updated_status["status"] == "processing"
    assert updated_status["progress"] == 40


def test_get_status_nonexistent_job(redis_service):
    """Test retrieving status for non-existent job returns None"""
    status = redis_service.get_status(str(uuid.uuid4()))
    assert status is None


def test_set_and_get_result(redis_service):
    """Test setting and retrieving transcription result"""
    job_id = str(uuid.uuid4())

    segments = [
        {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
        {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
    ]

    # Set result
    redis_service.set_result(job_id=job_id, segments=segments)

    # Retrieve result
    result = redis_service.get_result(job_id)

    assert result is not None
    assert "segments" in result
    assert len(result["segments"]) == 2
    assert result["segments"][0]["start"] == 0.5
    assert result["segments"][0]["end"] == 3.2
    assert result["segments"][0]["text"] == "Hello, welcome to the meeting."
    assert result["segments"][1]["start"] == 3.5
    assert result["segments"][1]["end"] == 7.8


def test_get_result_nonexistent_job(redis_service):
    """Test retrieving result for non-existent job returns None"""
    result = redis_service.get_result(str(uuid.uuid4()))
    assert result is None


def test_delete_job_data(redis_service):
    """Test deleting all job-related data"""
    job_id = str(uuid.uuid4())

    # Create status and result
    redis_service.set_status(
        job_id=job_id,
        status="completed",
        progress=100,
        message="Done",
        preserve_created_at=False
    )
    redis_service.set_result(
        job_id=job_id,
        segments=[{"start": 0.0, "end": 1.0, "text": "Test"}]
    )

    # Verify data exists
    assert redis_service.get_status(job_id) is not None
    assert redis_service.get_result(job_id) is not None

    # Delete job data
    redis_service.delete_job_data(job_id)

    # Verify data is deleted
    assert redis_service.get_status(job_id) is None
    assert redis_service.get_result(job_id) is None


def test_ping(redis_service):
    """Test Redis connection ping"""
    assert redis_service.ping() is True


def test_timestamp_format(redis_service):
    """Test that timestamps are properly formatted in ISO 8601 UTC"""
    job_id = str(uuid.uuid4())

    redis_service.set_status(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Test",
        preserve_created_at=False
    )

    status = redis_service.get_status(job_id)

    # Verify ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
    created_at = status["created_at"]
    updated_at = status["updated_at"]

    # Should be parseable as datetime
    datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ")
    datetime.strptime(updated_at, "%Y-%m-%dT%H:%M:%SZ")

    # Should end with Z (UTC indicator)
    assert created_at.endswith("Z")
    assert updated_at.endswith("Z")


def test_redis_key_patterns(redis_service, monkeypatch):
    """Test that Redis keys follow correct patterns"""
    job_id = str(uuid.uuid4())

    # Get the underlying fake Redis client
    fake_redis = fakeredis.FakeRedis(decode_responses=True)
    monkeypatch.setattr(redis_service, "client", fake_redis)

    # Set status and result
    redis_service.set_status(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Test",
        preserve_created_at=False
    )
    redis_service.set_result(
        job_id=job_id,
        segments=[{"start": 0.0, "end": 1.0, "text": "Test"}]
    )

    # Verify keys exist with correct patterns
    status_key = f"job:{job_id}:status"
    result_key = f"job:{job_id}:result"

    assert fake_redis.exists(status_key)
    assert fake_redis.exists(result_key)

    # Verify stored data is valid JSON
    status_json = fake_redis.get(status_key)
    result_json = fake_redis.get(result_key)

    assert json.loads(status_json)  # Should not raise
    assert json.loads(result_json)  # Should not raise
