"""
Tests for Celery transcription task
Tests 5-stage progress tracking, result storage, and error handling
"""

import pytest
import os
import json
import uuid
from unittest.mock import Mock, MagicMock, patch
from app.tasks.transcription import transcribe_audio
import fakeredis


@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary audio file for testing"""
    audio_file = tmp_path / "test_job_id" / "original.mp3"
    audio_file.parent.mkdir(parents=True, exist_ok=True)
    audio_file.write_text("fake audio data")
    return str(audio_file)


@pytest.fixture
def mock_redis_service():
    """Mock RedisService for testing"""
    with patch("app.tasks.transcription.RedisService") as MockRedisService:
        mock_service = MagicMock()
        MockRedisService.return_value = mock_service

        # Track status updates
        mock_service.status_updates = []

        def track_status(job_id, status, progress, message, preserve_created_at=True):
            mock_service.status_updates.append({
                "job_id": job_id,
                "status": status,
                "progress": progress,
                "message": message
            })

        mock_service.set_status.side_effect = track_status

        yield mock_service


@pytest.fixture
def mock_whisperx_service():
    """Mock WhisperXService for testing"""
    with patch("app.tasks.transcription._load_whisperx_service") as MockLoader:
        mock_service = MagicMock()
        MockLoader.return_value = mock_service

        # Mock transcribe to return test segments
        mock_service.transcribe.return_value = [
            {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
            {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
        ]

        yield mock_service


@pytest.fixture(autouse=True)
def mock_pipeline_factory():
    """Stub enhancement pipeline factory to avoid heavy dependencies."""
    with patch("app.tasks.transcription.create_pipeline") as mock_factory:
        pipeline = MagicMock()
        pipeline.is_empty.return_value = True
        mock_factory.return_value = pipeline
        yield mock_factory


def test_transcribe_audio_task_accepts_parameters(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task accepts job_id and file_path parameters"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    # Patch settings.UPLOAD_DIR to use tmp_path
    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        result = transcribe_audio(job_id, file_path)

    assert result is not None
    assert "segments" in result


def test_transcribe_audio_5_stage_progress(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task updates status through all 5 stages with correct progress values"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        transcribe_audio(job_id, file_path)

    # Verify all 5 stages were called
    status_updates = mock_redis_service.status_updates
    assert len(status_updates) >= 5

    # Stage 1: Task queued (10%)
    assert status_updates[0]["status"] == "pending"
    assert status_updates[0]["progress"] == 10
    assert "queued" in status_updates[0]["message"].lower()

    # Stage 2: Loading AI model (20%)
    assert status_updates[1]["status"] == "processing"
    assert status_updates[1]["progress"] == 20
    assert "loading" in status_updates[1]["message"].lower()

    # Stage 3: Transcribing audio (40%)
    assert status_updates[2]["status"] == "processing"
    assert status_updates[2]["progress"] == 40
    assert "transcribing" in status_updates[2]["message"].lower()

    # Stage 4: Aligning timestamps (80%)
    assert status_updates[3]["status"] == "processing"
    assert status_updates[3]["progress"] == 80
    assert "aligning" in status_updates[3]["message"].lower()

    # Stage 5: Processing complete (100%)
    assert status_updates[4]["status"] == "completed"
    assert status_updates[4]["progress"] == 100
    assert "complete" in status_updates[4]["message"].lower()


def test_transcribe_audio_stores_result_in_redis(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task stores result in Redis with correct format"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        transcribe_audio(job_id, file_path)

    # Verify set_result was called
    mock_redis_service.set_result.assert_called_once()

    # Verify result format
    call_args = mock_redis_service.set_result.call_args
    assert call_args[1]["job_id"] == job_id

    segments = call_args[1]["segments"]
    assert isinstance(segments, list)
    assert len(segments) == 2
    assert segments[0]["start"] == 0.5
    assert segments[0]["end"] == 3.2


def test_transcribe_audio_saves_result_to_disk(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task saves result to disk at /uploads/{job_id}/transcription.json"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        transcribe_audio(job_id, file_path)

    # Verify transcription.json was created
    transcription_file = tmp_path / job_id / "transcription.json"
    assert transcription_file.exists()

    # Verify file content
    with open(transcription_file, "r") as f:
        result = json.load(f)

    assert "segments" in result
    assert len(result["segments"]) == 2
    assert result["segments"][0]["start"] == 0.5


def test_transcribe_audio_handles_file_not_found(mock_redis_service, mock_whisperx_service):
    """Test that task handles missing file and sets failed status"""
    job_id = str(uuid.uuid4())
    file_path = "/nonexistent/file.mp3"

    with pytest.raises(RuntimeError, match="Audio file not found"):
        transcribe_audio(job_id, file_path)

    # Verify failed status was set
    assert any(
        update["status"] == "failed"
        for update in mock_redis_service.status_updates
    )


def test_transcribe_audio_handles_corrupted_file(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task handles corrupted file and sets failed status with error message"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    # Mock transcribe to raise ValueError (corrupted file)
    mock_whisperx_service.transcribe.side_effect = ValueError("Audio file is corrupted")

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        with pytest.raises(RuntimeError):
            transcribe_audio(job_id, file_path)

    # Verify failed status was set
    assert any(
        update["status"] == "failed" and "corrupted" in update["message"].lower()
        for update in mock_redis_service.status_updates
    )


def test_transcribe_audio_handles_gpu_errors(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task handles GPU errors with user-friendly message"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    # Mock transcribe to raise GPU error
    mock_whisperx_service.transcribe.side_effect = RuntimeError("CUDA out of memory")

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        with pytest.raises(RuntimeError):
            transcribe_audio(job_id, file_path)

    # Verify failed status with GPU error message
    assert any(
        update["status"] == "failed" and "gpu" in update["message"].lower()
        for update in mock_redis_service.status_updates
    )


def test_transcribe_audio_calls_whisperx_service(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that task calls WhisperXService.transcribe() with correct file_path"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        transcribe_audio(job_id, file_path)

    # Verify WhisperXService.transcribe was called
    mock_whisperx_service.transcribe.assert_called_once_with(
        audio_path=file_path,
        language=None,
        include_metadata=True,
        apply_enhancements=False,
    )


def test_transcribe_audio_result_format_matches_model(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path):
    """Test that result format matches TranscriptionResult model spec"""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        result = transcribe_audio(job_id, file_path)

    # Verify result structure
    assert "segments" in result
    assert isinstance(result["segments"], list)

    # Verify each segment has required fields
    for segment in result["segments"]:
        assert "start" in segment
        assert "end" in segment
        assert "text" in segment
        assert isinstance(segment["start"], float)
        assert isinstance(segment["end"], float)
        assert isinstance(segment["text"], str)


def test_transcribe_audio_logs_job_id(mock_redis_service, mock_whisperx_service, temp_audio_file, tmp_path, caplog):
    """Test that task logs include job_id for debugging"""
    import logging
    caplog.set_level(logging.INFO)

    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        transcribe_audio(job_id, file_path)

    # Verify job_id appears in logs
    assert job_id in caplog.text


def test_transcribe_audio_runs_enhancement_pipeline(mock_redis_service, mock_whisperx_service, mock_pipeline_factory, temp_audio_file, tmp_path):
    """Ensure enhancement pipeline executes when components are configured."""
    job_id = str(uuid.uuid4())
    file_path = temp_audio_file

    pipeline = MagicMock()
    pipeline.is_empty.return_value = False
    enhanced_segment = {"start": 0.0, "end": 1.0, "text": "enhanced"}
    pipeline.process.return_value = ([enhanced_segment], {"component_metrics": []})
    mock_pipeline_factory.return_value = pipeline

    with patch("app.tasks.transcription.settings.UPLOAD_DIR", str(tmp_path)):
        result = transcribe_audio(job_id, file_path)

    pipeline.process.assert_called_once()
    assert result["segments"] == [enhanced_segment]
