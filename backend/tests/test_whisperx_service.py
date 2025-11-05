"""
Tests for WhisperXService
Tests transcription with mocked WhisperX to avoid GPU dependency
"""

import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from app.ai_services.whisperx_service import WhisperXService


@pytest.fixture
def temp_audio_file(tmp_path):
    """Create a temporary audio file for testing"""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_text("fake audio data")
    return str(audio_file)


@pytest.fixture
def mock_whisperx():
    """Mock whisperx module to avoid GPU dependency"""
    with patch("app.ai_services.whisperx_service.whisperx") as mock_wx:
        # Mock model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "segments": [
                {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
                {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
            ]
        }

        # Mock load_model
        mock_wx.load_model.return_value = mock_model

        # Mock load_audio
        mock_wx.load_audio.return_value = "fake_audio_array"

        # Mock alignment model
        mock_align_model = MagicMock()
        mock_metadata = {"language": "en"}
        mock_wx.load_align_model.return_value = (mock_align_model, mock_metadata)

        # Mock align function - returns aligned segments
        mock_wx.align.return_value = {
            "segments": [
                {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
                {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
            ]
        }

        yield mock_wx


def test_whisperx_service_initialization(mock_whisperx):
    """Test WhisperXService initializes correctly with model caching"""
    # Clear model cache
    WhisperXService._model_cache.clear()

    service = WhisperXService(
        model_name="base",
        device="cpu",
        compute_type="float32"
    )

    assert service.model_name == "base"
    assert service.device == "cpu"
    assert service.compute_type == "float32"
    assert service.model is not None

    # Verify model was loaded
    mock_whisperx.load_model.assert_called_once_with(
        "base",
        "cpu",
        compute_type="float32"
    )


def test_whisperx_service_model_caching(mock_whisperx):
    """Test that model is cached and not reloaded on second initialization"""
    # Clear model cache
    WhisperXService._model_cache.clear()

    # First initialization
    service1 = WhisperXService(
        model_name="base",
        device="cpu",
        compute_type="float32"
    )

    # Second initialization with same parameters
    service2 = WhisperXService(
        model_name="base",
        device="cpu",
        compute_type="float32"
    )

    # Model should only be loaded once (cached)
    assert mock_whisperx.load_model.call_count == 1
    assert service1.model is service2.model  # Same cached instance


def test_transcribe_returns_segments_with_timestamps(mock_whisperx, temp_audio_file):
    """Test that transcribe() returns properly formatted segments"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    segments = service.transcribe(temp_audio_file, language="en")

    assert isinstance(segments, list)
    assert len(segments) == 2

    # Verify first segment
    assert segments[0]["start"] == 0.5
    assert segments[0]["end"] == 3.2
    assert segments[0]["text"] == "Hello, welcome to the meeting."

    # Verify second segment
    assert segments[1]["start"] == 3.5
    assert segments[1]["end"] == 7.8
    assert segments[1]["text"] == "Let's begin with today's agenda."


def test_transcribe_with_word_level_timestamps(mock_whisperx, temp_audio_file):
    """Test that transcribe() produces segments with float timestamps (word-level precision)"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    segments = service.transcribe(temp_audio_file)

    # All timestamps should be floats
    for segment in segments:
        assert isinstance(segment["start"], float)
        assert isinstance(segment["end"], float)
        assert segment["end"] > segment["start"]  # End > Start


def test_transcribe_file_not_found():
    """Test transcribe() raises FileNotFoundError for non-existent file"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    with pytest.raises(FileNotFoundError, match="Audio file not found or invalid"):
        service.transcribe("/nonexistent/audio.mp3")


def test_transcribe_handles_whisperx_errors(mock_whisperx, temp_audio_file):
    """Test transcribe() translates WhisperX errors to user-friendly messages"""
    WhisperXService._model_cache.clear()

    # Mock transcribe to raise an error
    mock_model = mock_whisperx.load_model.return_value
    mock_model.transcribe.side_effect = RuntimeError("CUDA out of memory")

    service = WhisperXService()

    with pytest.raises(RuntimeError, match="GPU error during transcription"):
        service.transcribe(temp_audio_file)


def test_transcribe_handles_format_errors(mock_whisperx, temp_audio_file):
    """Test transcribe() handles corrupted file format errors"""
    WhisperXService._model_cache.clear()

    # Mock load_audio to raise format error
    mock_whisperx.load_audio.side_effect = ValueError("Failed to decode audio")

    service = WhisperXService()

    with pytest.raises(ValueError, match="Audio file format is corrupted"):
        service.transcribe(temp_audio_file)


def test_get_supported_languages():
    """Test get_supported_languages() returns language list"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    languages = service.get_supported_languages()

    assert isinstance(languages, list)
    assert len(languages) > 0
    assert "en" in languages  # English should be supported
    assert "es" in languages  # Spanish should be supported
    assert "fr" in languages  # French should be supported


def test_validate_audio_file_valid_formats(tmp_path):
    """Test validate_audio_file() accepts valid formats"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    valid_formats = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4", ".webm", ".aac"]

    for ext in valid_formats:
        audio_file = tmp_path / f"test_audio{ext}"
        audio_file.write_text("fake audio")

        assert service.validate_audio_file(str(audio_file)) is True


def test_validate_audio_file_invalid_format(tmp_path):
    """Test validate_audio_file() rejects invalid formats"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    invalid_file = tmp_path / "test_audio.txt"
    invalid_file.write_text("not an audio file")

    assert service.validate_audio_file(str(invalid_file)) is False


def test_validate_audio_file_nonexistent():
    """Test validate_audio_file() rejects non-existent files"""
    WhisperXService._model_cache.clear()
    service = WhisperXService()

    assert service.validate_audio_file("/nonexistent/file.mp3") is False


def test_alignment_model_caching(mock_whisperx, temp_audio_file):
    """Test that alignment model is cached per language"""
    WhisperXService._model_cache.clear()
    WhisperXService._align_model_cache.clear()

    service = WhisperXService()

    # First transcription in English
    service.transcribe(temp_audio_file, language="en")

    # Second transcription in English (should use cached alignment model)
    service.transcribe(temp_audio_file, language="en")

    # Alignment model should only be loaded once for English
    mock_whisperx.load_align_model.assert_called_once_with(
        language_code="en",
        device="cuda"  # Default device from settings
    )
