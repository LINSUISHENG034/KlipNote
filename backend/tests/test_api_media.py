"""
Tests for GET /media/{job_id} endpoint
Tests media file serving with HTTP Range request support
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient


class TestServeMediaSuccess:
    """Test successful media file serving"""

    def test_serve_media_mp4(self, test_client, temp_upload_dir, monkeypatch):
        """Test GET /media/{job_id} returns MP4 video file"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup: Create mock job directory with MP4 file
        job_id = "550e8400-e29b-41d4-a716-446655440001"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        media_file = job_dir / "original.mp4"
        media_file.write_bytes(b"fake video data")

        # Execute
        response = test_client.get(f"/media/{job_id}")

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "video/mp4"
        assert "accept-ranges" in response.headers
        assert response.headers["accept-ranges"] == "bytes"
        assert response.content == b"fake video data"

    def test_serve_media_mp3(self, test_client, temp_upload_dir, monkeypatch):
        """Test GET /media/{job_id} returns MP3 audio file"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup
        job_id = "550e8400-e29b-41d4-a716-446655440002"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        media_file = job_dir / "original.mp3"
        media_file.write_bytes(b"fake audio data")

        # Execute
        response = test_client.get(f"/media/{job_id}")

        # Assert
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.headers["accept-ranges"] == "bytes"
        assert response.content == b"fake audio data"


class TestServeMediaNotFound:
    """Test 404 error handling for missing jobs/files"""

    def test_serve_media_job_not_found(self, test_client, temp_upload_dir, monkeypatch):
        """Test GET /media/{job_id} returns 404 for non-existent job"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Execute: Request media for non-existent job (valid UUID format)
        response = test_client.get("/media/550e8400-ffff-ffff-ffff-446655440099")

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        assert "job" in response.json()["detail"].lower()

    def test_serve_media_file_missing(self, test_client, temp_upload_dir, monkeypatch):
        """Test GET /media/{job_id} returns 404 when media file missing"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup: Create job directory but no original.* file
        job_id = "550e8400-e29b-41d4-a716-446655440003"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        # Create other files but not original.*
        (job_dir / "transcription.json").write_text('{"segments": []}')

        # Execute
        response = test_client.get(f"/media/{job_id}")

        # Assert
        assert response.status_code == 404
        assert "media file not found" in response.json()["detail"].lower()


class TestInvalidJobIdFormat:
    """Test 400 error for invalid job_id format (UUID validation)"""

    def test_serve_media_invalid_uuid_format(self, test_client, temp_upload_dir, monkeypatch):
        """Test GET /media/{job_id} returns 400 for invalid UUID format"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Execute: Invalid UUID formats
        invalid_uuids = [
            "not-a-uuid",
            "test-job-123",
            "12345",
            "550e8400-e29b-41d4-a716",  # Incomplete UUID
            "GGGGGGGG-e29b-41d4-a716-446655440000",  # Invalid hex characters
        ]

        for invalid_id in invalid_uuids:
            response = test_client.get(f"/media/{invalid_id}")
            assert response.status_code == 400, f"Expected 400 for job_id: {invalid_id}"
            assert "invalid" in response.json()["detail"].lower()
            assert "uuid" in response.json()["detail"].lower()

    def test_serve_media_path_traversal_blocked(self, test_client, temp_upload_dir, monkeypatch):
        """Test path traversal attempts are blocked (FastAPI handles at routing layer)"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Path traversal attempts - FastAPI routing blocks these before they reach our endpoint
        # They return 404 because FastAPI doesn't match the route
        path_traversal_attempts = [
            "../../../etc/passwd",
            "../../config",
        ]

        for invalid_id in path_traversal_attempts:
            response = test_client.get(f"/media/{invalid_id}")
            # FastAPI returns 404 for paths it doesn't match, which is fine
            # Our UUID validation provides an additional layer of security
            assert response.status_code in [400, 404], f"Expected 400 or 404 for: {invalid_id}"


class TestRangeRequestSupport:
    """Test HTTP Range request support for media seeking"""

    def test_serve_media_range_request_first_bytes(self, test_client, temp_upload_dir, monkeypatch):
        """Test HTTP Range request returns 206 Partial Content for first 100 bytes"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup: Create 1000-byte media file
        job_id = "550e8400-e29b-41d4-a716-446655440010"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        media_file = job_dir / "original.mp3"
        test_data = b"0123456789" * 100  # 1000 bytes
        media_file.write_bytes(test_data)

        # Execute: Request first 100 bytes (Range: bytes=0-99)
        response = test_client.get(
            f"/media/{job_id}",
            headers={"Range": "bytes=0-99"}
        )

        # Assert
        assert response.status_code == 206  # Partial Content
        assert "content-range" in response.headers
        assert response.headers["content-range"] == "bytes 0-99/1000"
        assert len(response.content) == 100
        assert response.content == test_data[:100]

    def test_serve_media_range_request_middle_bytes(self, test_client, temp_upload_dir, monkeypatch):
        """Test HTTP Range request for middle of file"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup
        job_id = "550e8400-e29b-41d4-a716-446655440011"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        media_file = job_dir / "original.mp3"
        test_data = b"ABCDEFGHIJ" * 100  # 1000 bytes
        media_file.write_bytes(test_data)

        # Execute: Request bytes 500-599 (middle of file)
        response = test_client.get(
            f"/media/{job_id}",
            headers={"Range": "bytes=500-599"}
        )

        # Assert
        assert response.status_code == 206
        assert response.headers["content-range"] == "bytes 500-599/1000"
        assert len(response.content) == 100
        assert response.content == test_data[500:600]

    def test_serve_media_range_request_end_bytes(self, test_client, temp_upload_dir, monkeypatch):
        """Test HTTP Range request for end of file (open-ended range)"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup
        job_id = "550e8400-e29b-41d4-a716-446655440012"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        media_file = job_dir / "original.wav"
        test_data = b"X" * 1000
        media_file.write_bytes(test_data)

        # Execute: Request from byte 900 to end (Range: bytes=900-)
        response = test_client.get(
            f"/media/{job_id}",
            headers={"Range": "bytes=900-"}
        )

        # Assert
        assert response.status_code == 206
        assert "900-999/1000" in response.headers["content-range"]
        assert len(response.content) == 100
        assert response.content == test_data[900:]


class TestContentTypeMapping:
    """Test correct Content-Type headers for different file formats"""

    def test_content_type_mp3(self, test_client, temp_upload_dir, monkeypatch):
        """Test Content-Type header for MP3 files"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        job_id = "550e8400-e29b-41d4-a716-446655440020"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.mp3").write_bytes(b"data")

        response = test_client.get(f"/media/{job_id}")
        assert response.headers["content-type"] == "audio/mpeg"

    def test_content_type_mp4(self, test_client, temp_upload_dir, monkeypatch):
        """Test Content-Type header for MP4 files"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        job_id = "550e8400-e29b-41d4-a716-446655440021"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.mp4").write_bytes(b"data")

        response = test_client.get(f"/media/{job_id}")
        assert response.headers["content-type"] == "video/mp4"

    def test_content_type_wav(self, test_client, temp_upload_dir, monkeypatch):
        """Test Content-Type header for WAV files"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        job_id = "550e8400-e29b-41d4-a716-446655440022"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.wav").write_bytes(b"data")

        response = test_client.get(f"/media/{job_id}")
        assert response.headers["content-type"] == "audio/wav"

    def test_content_type_m4a(self, test_client, temp_upload_dir, monkeypatch):
        """Test Content-Type header for M4A files"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        job_id = "550e8400-e29b-41d4-a716-446655440023"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.m4a").write_bytes(b"data")

        response = test_client.get(f"/media/{job_id}")
        assert response.headers["content-type"] == "audio/x-m4a"

    def test_content_type_wma(self, test_client, temp_upload_dir, monkeypatch):
        """Test Content-Type header for WMA files"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        job_id = "550e8400-e29b-41d4-a716-446655440024"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.wma").write_bytes(b"data")

        response = test_client.get(f"/media/{job_id}")
        assert response.headers["content-type"] == "audio/x-ms-wma"

    def test_content_type_unknown_extension(self, test_client, temp_upload_dir, monkeypatch):
        """Test fallback Content-Type for unknown extensions"""
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        job_id = "550e8400-e29b-41d4-a716-446655440025"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.xyz").write_bytes(b"data")

        response = test_client.get(f"/media/{job_id}")
        assert response.headers["content-type"] == "application/octet-stream"


class TestAcceptRangesHeader:
    """Test Accept-Ranges header is present for browser compatibility"""

    def test_accept_ranges_header_present(self, test_client, temp_upload_dir, monkeypatch):
        """Test response includes Accept-Ranges: bytes header"""
        # Patch UPLOAD_DIR to use temp directory
        from app import config
        monkeypatch.setattr(config.settings, "UPLOAD_DIR", str(temp_upload_dir))

        # Setup
        job_id = "550e8400-e29b-41d4-a716-446655440030"  # Valid UUID
        job_dir = temp_upload_dir / job_id
        job_dir.mkdir()
        (job_dir / "original.mp3").write_bytes(b"test data")

        # Execute
        response = test_client.get(f"/media/{job_id}")

        # Assert
        assert response.status_code == 200
        assert "accept-ranges" in response.headers
        assert response.headers["accept-ranges"] == "bytes"
