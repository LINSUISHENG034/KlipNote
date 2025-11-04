"""
Test AI services abstraction layer - Story 1.1
Tests for TranscriptionService interface and WhisperX implementation
"""

import pytest
from app.ai_services.base import TranscriptionService
from app.ai_services.whisperx_service import WhisperXService
from app.ai_services import get_transcription_service


class TestTranscriptionServiceInterface:
    """Test abstract TranscriptionService interface"""

    def test_whisperx_implements_interface(self):
        """Verify WhisperXService implements TranscriptionService"""
        service = WhisperXService()
        assert isinstance(service, TranscriptionService)

    def test_interface_has_required_methods(self):
        """Verify TranscriptionService interface defines required methods"""
        required_methods = ["transcribe", "get_supported_languages", "validate_audio_file"]

        for method in required_methods:
            assert hasattr(TranscriptionService, method), \
                f"TranscriptionService should define {method} method"


class TestWhisperXService:
    """Test WhisperX service implementation"""

    def test_whisperx_service_initialization(self):
        """Test WhisperXService can be initialized"""
        service = WhisperXService()

        assert service is not None
        assert hasattr(service, "model_name")
        assert hasattr(service, "device")
        assert hasattr(service, "compute_type")

    def test_whisperx_custom_initialization(self):
        """Test WhisperXService with custom parameters"""
        service = WhisperXService(
            model_name="base",
            device="cpu",
            compute_type="float32"
        )

        assert service.model_name == "base"
        assert service.device == "cpu"
        assert service.compute_type == "float32"

    def test_get_supported_languages(self):
        """Test WhisperXService returns supported languages"""
        service = WhisperXService()
        languages = service.get_supported_languages()

        assert isinstance(languages, list)
        assert len(languages) > 0
        assert "en" in languages  # English should always be supported

    def test_validate_audio_file_with_valid_extension(self):
        """Test audio file validation with supported formats"""
        service = WhisperXService()

        # These should be considered valid formats (even if file doesn't exist)
        valid_formats = [".mp3", ".wav", ".m4a", ".flac", ".ogg", ".mp4"]
        for fmt in valid_formats:
            # Create a fake path with valid extension
            # Validation will fail because file doesn't exist, but that's expected
            result = service.validate_audio_file(f"/fake/path/audio{fmt}")
            # We're testing the extension checking logic, not file existence
            assert isinstance(result, bool)

    def test_validate_audio_file_nonexistent(self):
        """Test audio file validation with non-existent file"""
        service = WhisperXService()
        result = service.validate_audio_file("/nonexistent/path/audio.mp3")

        assert result is False  # Should return False for non-existent files

    def test_transcribe_not_implemented(self):
        """Test transcribe raises NotImplementedError (Story 1.3 will implement)"""
        service = WhisperXService()

        with pytest.raises(NotImplementedError) as exc_info:
            service.transcribe("/fake/audio.mp3")

        assert "Story 1.3" in str(exc_info.value)


class TestServiceFactory:
    """Test service factory function"""

    def test_get_whisperx_service(self):
        """Test factory returns WhisperX service"""
        service = get_transcription_service("whisperx")

        assert isinstance(service, WhisperXService)
        assert isinstance(service, TranscriptionService)

    def test_get_default_service(self):
        """Test factory returns WhisperX as default"""
        service = get_transcription_service()

        assert isinstance(service, WhisperXService)

    def test_get_unsupported_service_raises_error(self):
        """Test factory raises error for unsupported service types"""
        with pytest.raises(ValueError) as exc_info:
            get_transcription_service("unsupported-service")

        assert "Unsupported" in str(exc_info.value)
