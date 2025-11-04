"""
Test configuration management - Story 1.1
Tests for Pydantic Settings and environment configuration
"""

import pytest
from app.config import Settings, settings
import os


class TestSettingsConfiguration:
    """Test Pydantic Settings configuration"""

    def test_settings_instance_exists(self):
        """Test global settings instance is available"""
        assert settings is not None
        assert isinstance(settings, Settings)

    def test_settings_has_required_fields(self):
        """Test Settings class has all required configuration fields"""
        required_fields = [
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "WHISPER_MODEL",
            "WHISPER_DEVICE",
            "WHISPER_COMPUTE_TYPE",
            "UPLOAD_DIR",
            "MAX_FILE_SIZE",
            "MAX_DURATION_HOURS",
            "CORS_ORIGINS"
        ]

        for field in required_fields:
            assert hasattr(settings, field), f"Settings should have {field} field"

    def test_default_values(self):
        """Test Settings has sensible default values"""
        test_settings = Settings()

        assert "redis" in test_settings.CELERY_BROKER_URL.lower()
        assert test_settings.WHISPER_MODEL in ["large-v2", "large-v3", "base", "small", "medium"]
        assert test_settings.WHISPER_DEVICE in ["cuda", "cpu"]
        assert test_settings.MAX_FILE_SIZE > 0
        assert test_settings.MAX_DURATION_HOURS > 0

    def test_cors_origins_list_property(self):
        """Test CORS origins JSON parsing"""
        test_settings = Settings()
        origins = test_settings.cors_origins_list

        assert isinstance(origins, list)
        assert len(origins) > 0

    def test_cors_origins_list_fallback(self):
        """Test CORS origins parsing fallback for invalid JSON"""
        test_settings = Settings(CORS_ORIGINS="invalid-json")
        origins = test_settings.cors_origins_list

        # Should fallback to default
        assert isinstance(origins, list)
        assert "http://localhost:5173" in origins


class TestEnvFileConfiguration:
    """Test .env.example template file"""

    def test_env_example_exists(self):
        """Test .env.example template exists"""
        from pathlib import Path
        env_example = Path(".env.example")
        assert env_example.exists(), ".env.example should exist"

    def test_env_example_has_required_variables(self):
        """Test .env.example includes all required variables"""
        from pathlib import Path

        env_example = Path(".env.example")
        content = env_example.read_text()

        required_vars = [
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "WHISPER_MODEL",
            "WHISPER_DEVICE",
            "WHISPER_COMPUTE_TYPE",
            "UPLOAD_DIR",
            "MAX_FILE_SIZE",
            "CORS_ORIGINS"
        ]

        for var in required_vars:
            assert var in content, f"{var} should be in .env.example"
