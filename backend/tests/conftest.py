"""
Pytest configuration and shared fixtures for backend tests
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, MagicMock
from typing import Generator, Dict, Any, List


@pytest.fixture
def test_client() -> Generator[TestClient, None, None]:
    """
    Provide FastAPI TestClient for endpoint testing

    Usage:
        def test_endpoint(test_client):
            response = test_client.get("/")
            assert response.status_code == 200
    """
    from app.main import app
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_whisperx() -> Mock:
    """
    Mock WhisperX service to avoid GPU dependency in tests

    Returns:
        Mock WhisperX service with transcribe() method

    Usage:
        def test_transcription(mock_whisperx):
            result = mock_whisperx.transcribe("audio.mp3")
            assert len(result) > 0
    """
    mock_service = MagicMock()

    # Mock transcribe method to return sample transcription
    def mock_transcribe(audio_path: str, language: str = "en", **kwargs) -> List[Dict[str, Any]]:
        return [
            {"start": 0.0, "end": 2.5, "text": "Hello, this is a test."},
            {"start": 2.5, "end": 5.0, "text": "Transcription is working."}
        ]

    mock_service.transcribe.side_effect = mock_transcribe
    mock_service.get_supported_languages.return_value = [
        "en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru"
    ]
    mock_service.validate_audio_file.return_value = True

    return mock_service


@pytest.fixture
def sample_audio_segments() -> List[Dict[str, Any]]:
    """
    Provide sample transcription segments for testing

    Returns:
        List of transcription segments with start, end, text fields
    """
    return [
        {"start": 0.0, "end": 2.5, "text": "Hello, this is a test."},
        {"start": 2.5, "end": 5.0, "text": "Transcription is working."},
        {"start": 5.0, "end": 8.0, "text": "This is the third segment."}
    ]


@pytest.fixture
def mock_celery_task() -> Mock:
    """
    Mock Celery task for testing async operations without Redis

    Returns:
        Mock Celery task with apply_async and delay methods
    """
    mock_task = MagicMock()

    # Mock task result
    mock_result = MagicMock()
    mock_result.id = "test-task-id-12345"
    mock_result.state = "PENDING"
    mock_result.ready.return_value = False

    mock_task.apply_async.return_value = mock_result
    mock_task.delay.return_value = mock_result

    return mock_task


@pytest.fixture
def temp_upload_dir(tmp_path):
    """
    Provide temporary directory for file upload testing

    Args:
        tmp_path: pytest built-in fixture for temporary directory

    Returns:
        Path to temporary upload directory
    """
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture(scope="session")
def docker_compose_available() -> bool:
    """
    Check if Docker Compose is available for integration tests

    Returns:
        True if docker-compose is available, False otherwise
    """
    import subprocess
    try:
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
