"""
Unit tests for FileHandler service
Tests file validation, duration checking, and storage methods
"""

import pytest
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from fastapi import UploadFile
from io import BytesIO
import subprocess

from app.services.file_handler import FileHandler
from app.config import settings


class TestValidateFormat:
    """Test suite for FileHandler.validate_format()"""

    def test_validate_format_with_valid_mp3(self):
        """Test validation accepts valid MP3 file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/mpeg"
        mock_file.filename = "test.mp3"

        # Should not raise exception
        FileHandler.validate_format(mock_file)

    def test_validate_format_with_valid_mp4(self):
        """Test validation accepts valid MP4 file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "video/mp4"
        mock_file.filename = "test.mp4"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_valid_wav(self):
        """Test validation accepts valid WAV file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/wav"
        mock_file.filename = "test.wav"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_valid_m4a(self):
        """Test validation accepts valid M4A file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/x-m4a"
        mock_file.filename = "test.m4a"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_alternative_m4a_mime(self):
        """Test validation accepts alternative M4A MIME type"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "audio/mp4"
        mock_file.filename = "test.m4a"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_invalid_text_file(self):
        """Test validation rejects text file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "text/plain"
        mock_file.filename = "document.txt"

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_format(mock_file)

        assert "Unsupported file format" in str(exc_info.value)
        assert "text/plain" in str(exc_info.value)

    def test_validate_format_with_invalid_executable(self):
        """Test validation rejects executable file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/x-msdownload"
        mock_file.filename = "malware.exe"

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_format(mock_file)

        assert "Unsupported file format" in str(exc_info.value)

    def test_validate_format_with_invalid_image(self):
        """Test validation rejects image file"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "image/jpeg"
        mock_file.filename = "photo.jpg"

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_format(mock_file)

        assert "Unsupported file format" in str(exc_info.value)

    def test_validate_format_with_octet_stream_and_valid_extension(self):
        """Test validation accepts application/octet-stream with valid MP3 extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "audio.mp3"

        # Should not raise exception (validates by extension)
        FileHandler.validate_format(mock_file)

    def test_validate_format_with_octet_stream_and_mp4_extension(self):
        """Test validation accepts application/octet-stream with valid MP4 extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "video.mp4"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_octet_stream_and_wav_extension(self):
        """Test validation accepts application/octet-stream with valid WAV extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "audio.wav"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_octet_stream_and_m4a_extension(self):
        """Test validation accepts application/octet-stream with valid M4A extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "audio.m4a"

        FileHandler.validate_format(mock_file)

    def test_validate_format_with_octet_stream_and_invalid_extension(self):
        """Test validation rejects application/octet-stream with invalid extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "document.txt"

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_format(mock_file)

        assert "Unsupported file format" in str(exc_info.value)
        assert "application/octet-stream" in str(exc_info.value)

    def test_validate_format_with_octet_stream_and_no_extension(self):
        """Test validation rejects application/octet-stream with no file extension"""
        mock_file = Mock(spec=UploadFile)
        mock_file.content_type = "application/octet-stream"
        mock_file.filename = "audiofile"

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_format(mock_file)

        assert "Unsupported file format" in str(exc_info.value)

    def test_validate_format_case_insensitive_extension(self):
        """Test that file extension validation is case-insensitive"""
        test_cases = [
            "audio.MP3",
            "audio.Mp3",
            "video.MP4",
            "sound.WAV",
            "music.M4A",
        ]

        for filename in test_cases:
            mock_file = Mock(spec=UploadFile)
            mock_file.content_type = "application/octet-stream"
            mock_file.filename = filename

            # Should not raise exception
            FileHandler.validate_format(mock_file)


class TestValidateDuration:
    """Test suite for FileHandler.validate_duration()"""

    @patch("subprocess.run")
    def test_validate_duration_with_short_file(self, mock_subprocess):
        """Test validation accepts file under 2 hours"""
        # Mock ffprobe returning 30 minutes (1800 seconds)
        mock_subprocess.return_value = Mock(
            stdout="1800.0",
            stderr="",
            returncode=0
        )

        # Should not raise exception
        FileHandler.validate_duration("/test/path/audio.mp3")

        # Verify ffprobe was called correctly
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        assert "ffprobe" in call_args
        assert "-show_entries" in call_args
        assert "format=duration" in call_args

    @patch("subprocess.run")
    def test_validate_duration_with_exactly_2_hours(self, mock_subprocess):
        """Test validation accepts file exactly at 2-hour limit"""
        # Mock ffprobe returning exactly 2 hours (7200 seconds)
        mock_subprocess.return_value = Mock(
            stdout="7200.0",
            stderr="",
            returncode=0
        )

        FileHandler.validate_duration("/test/path/audio.mp3")

    @patch("subprocess.run")
    def test_validate_duration_with_long_file(self, mock_subprocess):
        """Test validation rejects file exceeding 2 hours"""
        # Mock ffprobe returning 3 hours (10800 seconds)
        mock_subprocess.return_value = Mock(
            stdout="10800.0",
            stderr="",
            returncode=0
        )

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_duration("/test/path/audio.mp3")

        assert "exceeds" in str(exc_info.value)
        assert "2-hour limit" in str(exc_info.value)
        assert "3.00 hours" in str(exc_info.value)

    @patch("subprocess.run")
    def test_validate_duration_with_very_long_file(self, mock_subprocess):
        """Test validation rejects file far exceeding limit"""
        # Mock ffprobe returning 10 hours (36000 seconds)
        mock_subprocess.return_value = Mock(
            stdout="36000.0",
            stderr="",
            returncode=0
        )

        with pytest.raises(ValueError) as exc_info:
            FileHandler.validate_duration("/test/path/audio.mp3")

        assert "10.00 hours" in str(exc_info.value)

    @patch("subprocess.run")
    def test_validate_duration_with_ffprobe_error(self, mock_subprocess):
        """Test handling of ffprobe execution failure"""
        # Mock ffprobe failing with error
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["ffprobe"],
            stderr="Invalid file format"
        )

        with pytest.raises(RuntimeError) as exc_info:
            FileHandler.validate_duration("/test/path/invalid.mp3")

        assert "Failed to validate media duration" in str(exc_info.value)

    @patch("subprocess.run")
    def test_validate_duration_with_invalid_ffprobe_output(self, mock_subprocess):
        """Test handling of invalid ffprobe output"""
        # Mock ffprobe returning invalid output
        mock_subprocess.return_value = Mock(
            stdout="invalid_number",
            stderr="",
            returncode=0
        )

        with pytest.raises(RuntimeError) as exc_info:
            FileHandler.validate_duration("/test/path/audio.mp3")

        assert "Invalid duration value" in str(exc_info.value)


class TestGenerateJobId:
    """Test suite for FileHandler.generate_job_id()"""

    def test_generate_job_id_returns_string(self):
        """Test that job_id is returned as string"""
        job_id = FileHandler.generate_job_id()
        assert isinstance(job_id, str)

    def test_generate_job_id_is_valid_uuid(self):
        """Test that job_id is valid UUID v4 format"""
        job_id = FileHandler.generate_job_id()

        # Should be parseable as UUID
        parsed_uuid = uuid.UUID(job_id)
        assert str(parsed_uuid) == job_id

        # Should be version 4
        assert parsed_uuid.version == 4

    def test_generate_job_id_is_unique(self):
        """Test that multiple calls generate unique IDs"""
        job_ids = set()
        for _ in range(100):
            job_id = FileHandler.generate_job_id()
            job_ids.add(job_id)

        # All 100 IDs should be unique
        assert len(job_ids) == 100

    def test_generate_job_id_format(self):
        """Test that job_id matches UUID v4 format pattern"""
        job_id = FileHandler.generate_job_id()

        # UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
        # where y is 8, 9, a, or b
        parts = job_id.split("-")
        assert len(parts) == 5
        assert len(parts[0]) == 8
        assert len(parts[1]) == 4
        assert len(parts[2]) == 4
        assert len(parts[3]) == 4
        assert len(parts[4]) == 12

        # Version field should start with 4
        assert parts[2][0] == "4"


class TestSaveUpload:
    """Test suite for FileHandler.save_upload()"""

    def test_save_upload_creates_directory_structure(self, tmp_path, monkeypatch):
        """Test that save_upload creates correct directory structure"""
        # Mock settings.UPLOAD_DIR to use tmp_path
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        # Create mock UploadFile
        file_content = b"fake audio content"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(file_content)
        mock_file.filename = "test_audio.mp3"

        job_id = "test-job-id-12345"

        # Save upload
        file_path = FileHandler.save_upload(job_id, mock_file)

        # Verify directory structure
        expected_dir = Path(settings.UPLOAD_DIR) / job_id
        assert expected_dir.exists()
        assert expected_dir.is_dir()

        # Verify file was created
        expected_file = expected_dir / "original.mp3"
        assert expected_file.exists()
        assert str(expected_file.absolute()) == file_path

    def test_save_upload_preserves_file_extension(self, tmp_path, monkeypatch):
        """Test that file extension is preserved from original filename"""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        test_cases = [
            ("audio.mp3", ".mp3"),
            ("video.mp4", ".mp4"),
            ("sound.wav", ".wav"),
            ("music.m4a", ".m4a"),
        ]

        for filename, expected_ext in test_cases:
            mock_file = Mock(spec=UploadFile)
            mock_file.file = BytesIO(b"content")
            mock_file.filename = filename

            job_id = FileHandler.generate_job_id()
            file_path = FileHandler.save_upload(job_id, mock_file)

            assert file_path.endswith(f"original{expected_ext}")

    def test_save_upload_writes_file_content(self, tmp_path, monkeypatch):
        """Test that file content is correctly written"""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        file_content = b"This is test audio file content"
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(file_content)
        mock_file.filename = "test.mp3"

        job_id = FileHandler.generate_job_id()
        file_path = FileHandler.save_upload(job_id, mock_file)

        # Read file and verify content
        with open(file_path, "rb") as f:
            saved_content = f.read()

        assert saved_content == file_content

    def test_save_upload_handles_large_files(self, tmp_path, monkeypatch):
        """Test streaming works for large files"""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        # Create 10MB fake content
        large_content = b"X" * (10 * 1024 * 1024)
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(large_content)
        mock_file.filename = "large_audio.mp3"

        job_id = FileHandler.generate_job_id()
        file_path = FileHandler.save_upload(job_id, mock_file)

        # Verify file size
        saved_file = Path(file_path)
        assert saved_file.stat().st_size == len(large_content)

    def test_save_upload_handles_no_extension(self, tmp_path, monkeypatch):
        """Test handling of filename without extension"""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(b"content")
        mock_file.filename = "audiofile"

        job_id = FileHandler.generate_job_id()
        file_path = FileHandler.save_upload(job_id, mock_file)

        # Should default to .mp3
        assert file_path.endswith("original.mp3")

    def test_save_upload_returns_absolute_path(self, tmp_path, monkeypatch):
        """Test that returned path is absolute"""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(b"content")
        mock_file.filename = "test.mp3"

        job_id = FileHandler.generate_job_id()
        file_path = FileHandler.save_upload(job_id, mock_file)

        # Path should be absolute
        assert Path(file_path).is_absolute()

    def test_save_upload_handles_existing_directory(self, tmp_path, monkeypatch):
        """Test that existing directory doesn't cause error"""
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))

        job_id = "existing-job-id"

        # Create directory first
        job_dir = Path(settings.UPLOAD_DIR) / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Now try to save upload
        mock_file = Mock(spec=UploadFile)
        mock_file.file = BytesIO(b"content")
        mock_file.filename = "test.mp3"

        file_path = FileHandler.save_upload(job_id, mock_file)

        # Should succeed and return path
        assert Path(file_path).exists()
