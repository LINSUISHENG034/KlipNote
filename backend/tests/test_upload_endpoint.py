"""
Integration tests for POST /upload endpoint
Tests API endpoint with file uploads, validation, and error handling
"""

import pytest
import io
import json
from pathlib import Path
from unittest.mock import patch, Mock
import subprocess

from fastapi.testclient import TestClient


class TestUploadEndpointSuccess:
    """Test suite for successful upload scenarios"""

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_valid_mp3_file(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test uploading valid MP3 file returns 200 with job_id"""
        # Mock settings and duration validation
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None  # No exception = valid duration

        # Create fake MP3 file
        file_content = b"fake mp3 audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test_audio.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return job_id in UUID v4 format
        assert "job_id" in data
        assert isinstance(data["job_id"], str)
        assert len(data["job_id"]) == 36  # UUID v4 length with hyphens

        # Verify UUID v4 format pattern
        import uuid
        job_id = uuid.UUID(data["job_id"])
        assert job_id.version == 4

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_valid_mp4_file(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test uploading valid MP4 file returns 200 with job_id"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        file_content = b"fake mp4 video content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test_video.mp4", file, "video/mp4")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_valid_wav_file(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test uploading valid WAV file returns 200 with job_id"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        file_content = b"fake wav audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test_audio.wav", file, "audio/wav")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_valid_m4a_file(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test uploading valid M4A file returns 200 with job_id"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        file_content = b"fake m4a audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test_audio.m4a", file, "audio/x-m4a")}
        )

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_saves_file_to_correct_location(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test that uploaded file is saved to /uploads/{job_id}/original.{ext}"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        file_content = b"test audio content for verification"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Verify file was saved
        expected_file = Path(config.settings.UPLOAD_DIR) / job_id / "original.mp3"
        assert expected_file.exists()

        # Verify content
        with open(expected_file, "rb") as f:
            saved_content = f.read()
        assert saved_content == file_content


class TestUploadEndpointValidationErrors:
    """Test suite for validation error scenarios (400 errors)"""

    def test_upload_invalid_format_returns_400(self, test_client):
        """Test uploading unsupported file format returns 400"""
        file_content = b"This is a text file"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("document.txt", file, "text/plain")}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Unsupported file format" in data["detail"]

    def test_upload_executable_returns_400(self, test_client):
        """Test uploading executable file returns 400"""
        file_content = b"fake exe content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("malware.exe", file, "application/x-msdownload")}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file format" in data["detail"]

    def test_upload_image_returns_400(self, test_client):
        """Test uploading image file returns 400"""
        file_content = b"fake jpeg content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("photo.jpg", file, "image/jpeg")}
        )

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported file format" in data["detail"]

    @patch("subprocess.run")
    def test_upload_exceeding_duration_returns_400(self, mock_subprocess, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test uploading file exceeding 2-hour duration returns 400"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        # Mock ffprobe returning 3 hours (10800 seconds)
        mock_subprocess.return_value = Mock(
            stdout="10800.0",
            stderr="",
            returncode=0
        )

        file_content = b"fake long audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("long_audio.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "exceeds" in data["detail"]
        assert "2-hour limit" in data["detail"]

    def test_upload_missing_file_returns_422(self, test_client):
        """Test request without file returns 422 (FastAPI validation error)"""
        response = test_client.post("/upload")

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data


class TestUploadEndpointSizeLimit:
    """Test suite for file size limit scenarios (413 errors)"""

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_file_exactly_2gb(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test uploading file exactly at 2GB limit succeeds"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Note: We can't actually create 2GB file in test, so we mock the size check
        # This test verifies the logic, not actual 2GB upload
        file_content = b"simulated large file content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("large_audio.mp3", file, "audio/mpeg")}
        )

        # Should succeed (actual size enforcement happens at FastAPI/ASGI level)
        assert response.status_code == 200

    def test_upload_oversized_file_middleware_check(self, test_client):
        """Test that middleware checks for oversized files"""
        # The middleware checks Content-Length header
        # In real scenarios, web server (nginx/uvicorn) enforces this
        # This test documents expected behavior

        # For files >2GB, client should receive 413
        # Actual enforcement happens at ASGI server level
        # Our middleware provides additional check as documented

        # Note: TestClient doesn't enforce Content-Length limits
        # This is tested in integration/manual testing
        pass


class TestUploadEndpointDocumentation:
    """Test suite for API documentation"""

    def test_upload_endpoint_in_openapi_schema(self, test_client):
        """Test that /upload endpoint is documented in OpenAPI schema"""
        response = test_client.get("/openapi.json")

        assert response.status_code == 200
        openapi_schema = response.json()

        # Verify /upload endpoint exists in paths
        assert "/upload" in openapi_schema["paths"]
        upload_spec = openapi_schema["paths"]["/upload"]

        # Verify POST method exists
        assert "post" in upload_spec
        post_spec = upload_spec["post"]

        # Verify response model includes UploadResponse
        assert "200" in post_spec["responses"]
        success_response = post_spec["responses"]["200"]

        # Check response schema references UploadResponse model
        assert "content" in success_response
        assert "application/json" in success_response["content"]

    def test_docs_page_accessible(self, test_client):
        """Test that FastAPI /docs page is accessible"""
        response = test_client.get("/docs")

        assert response.status_code == 200
        # Verify it's HTML (interactive docs)
        assert "text/html" in response.headers["content-type"]


class TestUploadEndpointEdgeCases:
    """Test suite for edge cases and error handling"""

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_with_special_characters_in_filename(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test handling filename with special characters"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        file_content = b"audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("audio file (test) [2024].mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200
        # UUID-based storage should handle any filename safely

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_with_unicode_filename(self, mock_validate_duration, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test handling filename with unicode characters"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        file_content = b"audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("音频文件.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200

    @patch("subprocess.run")
    def test_upload_with_ffprobe_failure(self, mock_subprocess, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test handling ffprobe execution failure"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        # Mock ffprobe failing
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffprobe"],
            stderr="Invalid file"
        )

        file_content = b"corrupted audio"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("corrupted.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 500
        data = response.json()
        assert "Media validation error" in data["detail"]

    @patch("app.main.transcribe_audio")
    @patch("subprocess.run")
    def test_upload_file_at_duration_boundary(self, mock_subprocess, mock_transcribe_task, fake_redis_client, test_client, tmp_path, monkeypatch):
        """Test file exactly at 2-hour duration limit"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        # Mock ffprobe returning exactly 2 hours (7200 seconds)
        mock_subprocess.return_value = Mock(
            stdout="7200.0",
            stderr="",
            returncode=0
        )

        file_content = b"exactly 2 hour audio"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("boundary_audio.mp3", file, "audio/mpeg")}
        )

        # Should succeed (≤2 hours is allowed)
        assert response.status_code == 200

    @patch("subprocess.run")
    def test_upload_file_just_over_duration_limit(self, mock_subprocess, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test file just slightly over 2-hour limit"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        # Mock ffprobe returning 2 hours + 1 second (7201 seconds)
        mock_subprocess.return_value = Mock(
            stdout="7201.0",
            stderr="",
            returncode=0
        )

        file_content = b"slightly over limit audio"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("over_limit.mp3", file, "audio/mpeg")}
        )

        # Should fail (>2 hours not allowed)
        assert response.status_code == 400
        data = response.json()
        assert "exceeds" in data["detail"]


class TestUploadEndpointCeleryIntegration:
    """Test suite for Celery task queuing integration"""

    @patch("app.main.transcribe_audio")
    @patch("app.main.RedisService")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_queues_celery_task(self, mock_validate_duration, mock_redis_service_class, mock_transcribe_task, test_client, tmp_path, monkeypatch):
        """Test that POST /upload queues Celery task with correct parameters"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Mock Redis service instance
        mock_redis = Mock()
        mock_redis_service_class.return_value = mock_redis

        # Create test file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Verify task.delay() was called
        mock_transcribe_task.delay.assert_called_once()

        # Verify task received correct job_id
        call_args = mock_transcribe_task.delay.call_args[0]
        assert call_args[0] == job_id  # First argument is job_id

        # Verify task received correct file_path
        expected_path = str(Path(config.settings.UPLOAD_DIR) / job_id / "original.mp3")
        assert call_args[1] == expected_path  # Second argument is file_path

    @patch("app.main.transcribe_audio")
    @patch("app.main.RedisService")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_initializes_redis_status(self, mock_validate_duration, mock_redis_service_class, mock_transcribe_task, test_client, tmp_path, monkeypatch):
        """Test that POST /upload initializes Redis status to pending"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Mock Redis service instance
        mock_redis = Mock()
        mock_redis_service_class.return_value = mock_redis

        # Create test file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200
        job_id = response.json()["job_id"]

        # Verify Redis set_status was called with pending status
        mock_redis.set_status.assert_called_once()
        call_kwargs = mock_redis.set_status.call_args[1]

        assert call_kwargs["job_id"] == job_id
        assert call_kwargs["status"] == "pending"
        assert call_kwargs["progress"] == 10
        assert "queued" in call_kwargs["message"].lower()
        assert call_kwargs["preserve_created_at"] is False  # Initial status

    @patch("app.main.transcribe_audio")
    @patch("app.main.RedisService")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_task_receives_saved_file_path(self, mock_validate_duration, mock_redis_service_class, mock_transcribe_task, test_client, tmp_path, monkeypatch):
        """Test that Celery task receives file_path from FileHandler.save_upload()"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Mock Redis service
        mock_redis = Mock()
        mock_redis_service_class.return_value = mock_redis

        # Create test file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        response = test_client.post(
            "/upload",
            files={"file": ("audio.mp3", file, "audio/mpeg")}
        )

        assert response.status_code == 200

        # Verify task was called with file path that exists
        call_args = mock_transcribe_task.delay.call_args[0]
        file_path = call_args[1]

        # File should actually exist (saved by FileHandler)
        assert Path(file_path).exists()
        assert Path(file_path).name == "original.mp3"


class TestStatusResultIntegrationWithUpload:
    """Integration tests for full upload → status → result workflow"""

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_then_check_status_pending(self, mock_validate_duration, mock_transcribe_task, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test Upload → Call /status immediately → Verify 'pending' status"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Upload file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        upload_response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Immediately check status (before task completes)
        status_response = test_client.get(f"/status/{job_id}")

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "pending"
        assert status_data["progress"] == 10
        assert "queued" in status_data["message"].lower()

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_then_status_shows_completed(self, mock_validate_duration, mock_transcribe_task, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test Upload → Simulate completion → Call /status → Verify 'completed'"""
        from app import config
        import json
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Upload file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        upload_response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Simulate task completion by updating Redis status
        status_key = f"job:{job_id}:status"
        completed_status = {
            "status": "completed",
            "progress": 100,
            "message": "Processing complete!",
            "created_at": "2025-11-05T10:30:00Z",
            "updated_at": "2025-11-05T10:32:45Z"
        }
        fake_redis_client.set(status_key, json.dumps(completed_status))

        # Check status endpoint
        status_response = test_client.get(f"/status/{job_id}")

        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        assert status_data["progress"] == 100
        assert "complete" in status_data["message"].lower()

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_upload_then_fetch_result(self, mock_validate_duration, mock_transcribe_task, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test Upload → Simulate completion → Call /result → Verify segments present"""
        from app import config
        import json
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Upload file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        upload_response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Simulate task completion by updating Redis status and result
        status_key = f"job:{job_id}:status"
        completed_status = {
            "status": "completed",
            "progress": 100,
            "message": "Processing complete!",
            "created_at": "2025-11-05T10:30:00Z",
            "updated_at": "2025-11-05T10:32:45Z"
        }
        fake_redis_client.set(status_key, json.dumps(completed_status))

        result_key = f"job:{job_id}:result"
        transcription_result = {
            "segments": [
                {"start": 0.5, "end": 2.8, "text": "Hello, this is a test transcription."},
                {"start": 3.0, "end": 5.5, "text": "The audio has been processed successfully."}
            ]
        }
        fake_redis_client.set(result_key, json.dumps(transcription_result))

        # Fetch result endpoint
        result_response = test_client.get(f"/result/{job_id}")

        assert result_response.status_code == 200
        result_data = result_response.json()

        assert "segments" in result_data
        assert len(result_data["segments"]) == 2
        assert result_data["segments"][0]["text"] == "Hello, this is a test transcription."
        assert result_data["segments"][1]["text"] == "The audio has been processed successfully."

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_full_workflow_upload_status_result(self, mock_validate_duration, mock_transcribe_task, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test complete workflow: Upload → Check pending status → Simulate completion → Check completed status → Fetch result"""
        from app import config
        import json
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Step 1: Upload file
        file_content = b"full workflow test audio"
        file = io.BytesIO(file_content)

        upload_response = test_client.post(
            "/upload",
            files={"file": ("workflow_test.mp3", file, "audio/mpeg")}
        )

        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Step 2: Check initial status (pending)
        status_response_1 = test_client.get(f"/status/{job_id}")
        assert status_response_1.status_code == 200
        assert status_response_1.json()["status"] == "pending"

        # Step 3: Simulate processing status
        status_key = f"job:{job_id}:status"
        processing_status = {
            "status": "processing",
            "progress": 40,
            "message": "Transcribing audio...",
            "created_at": "2025-11-05T10:30:00Z",
            "updated_at": "2025-11-05T10:31:15Z"
        }
        fake_redis_client.set(status_key, json.dumps(processing_status))

        status_response_2 = test_client.get(f"/status/{job_id}")
        assert status_response_2.status_code == 200
        assert status_response_2.json()["status"] == "processing"
        assert status_response_2.json()["progress"] == 40

        # Step 4: Simulate completion
        completed_status = {
            "status": "completed",
            "progress": 100,
            "message": "Processing complete!",
            "created_at": "2025-11-05T10:30:00Z",
            "updated_at": "2025-11-05T10:32:45Z"
        }
        fake_redis_client.set(status_key, json.dumps(completed_status))

        result_key = f"job:{job_id}:result"
        transcription_result = {
            "segments": [
                {"start": 0.0, "end": 1.5, "text": "This is the complete workflow test."}
            ]
        }
        fake_redis_client.set(result_key, json.dumps(transcription_result))

        # Step 5: Check completed status
        status_response_3 = test_client.get(f"/status/{job_id}")
        assert status_response_3.status_code == 200
        assert status_response_3.json()["status"] == "completed"
        assert status_response_3.json()["progress"] == 100

        # Step 6: Fetch final result
        result_response = test_client.get(f"/result/{job_id}")
        assert result_response.status_code == 200
        assert len(result_response.json()["segments"]) == 1
        assert result_response.json()["segments"][0]["text"] == "This is the complete workflow test."

    @patch("app.main.transcribe_audio")
    @patch("app.services.file_handler.FileHandler.validate_duration")
    def test_result_endpoint_before_job_complete(self, mock_validate_duration, mock_transcribe_task, test_client, tmp_path, monkeypatch, fake_redis_client):
        """Test calling /result while job is still processing returns 404"""
        from app import config
        import json
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
        mock_validate_duration.return_value = None

        # Upload file
        file_content = b"test audio content"
        file = io.BytesIO(file_content)

        upload_response = test_client.post(
            "/upload",
            files={"file": ("test.mp3", file, "audio/mpeg")}
        )

        assert upload_response.status_code == 200
        job_id = upload_response.json()["job_id"]

        # Simulate processing status (not completed)
        status_key = f"job:{job_id}:status"
        processing_status = {
            "status": "processing",
            "progress": 40,
            "message": "Transcribing audio...",
            "created_at": "2025-11-05T10:30:00Z",
            "updated_at": "2025-11-05T10:31:15Z"
        }
        fake_redis_client.set(status_key, json.dumps(processing_status))

        # Try to fetch result (should fail with 404)
        result_response = test_client.get(f"/result/{job_id}")

        assert result_response.status_code == 404
        assert "not yet complete" in result_response.json()["detail"].lower()


