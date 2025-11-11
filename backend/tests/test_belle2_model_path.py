"""
Tests for BELLE-2 model path configuration
"""

import pytest
import os
from unittest.mock import patch

@pytest.mark.usefixtures("clearenv")
class TestBelle2ModelPath:
    """Tests for BELLE-2 model path configuration"""

    def test_belle2_service_with_local_model_path(self, tmp_path):
        """
        Test that Belle2Service can be initialized with a local model path
        """
        import importlib
        from app.config import settings
        from app.ai_services.belle2_service import Belle2Service
        
        # Create a dummy model directory
        model_path = tmp_path / "dummy_model"
        model_path.mkdir()
        (model_path / "config.json").touch()
        (model_path / "model.safetensors").touch()
        
        # Set the BELLE2_MODEL_PATH environment variable
        with patch.dict(os.environ, {"BELLE2_MODEL_PATH": str(model_path)}):
            # Reload the settings module to pick up the new environment variable
            importlib.reload(settings)
            
            # Instantiate the Belle2Service
            service = Belle2Service()
        
            # Assert that the model_name is set to the local model path
            assert service.model_name == str(model_path)
    def test_belle2_service_without_local_model_path(self):
        """
        Test that Belle2Service falls back to the default model name
        """
        from app.ai_services.belle2_service import Belle2Service
        from app.config import Settings

        # Instantiate the Settings class
        settings = Settings()

        # Instantiate the Belle2Service
        service = Belle2Service()

        # Assert that the model_name is set to the default model name
        assert service.model_name == "BELLE-2/Belle-whisper-large-v3-zh"

    def test_belle2_service_with_model_name_override(self):
        """
        Test that the model_name argument overrides the environment variable
        """
        from app.ai_services.belle2_service import Belle2Service
        from app.config import Settings

        # Set the BELLE2_MODEL_PATH environment variable
        with patch.dict(os.environ, {"BELLE2_MODEL_PATH": "dummy_path"}):
            # Instantiate the Settings class to reload the environment variables
            settings = Settings()

            # Instantiate the Belle2Service with a model_name argument
            service = Belle2Service(model_name="override_model_name")

            # Assert that the model_name is set to the override model name
            assert service.model_name == "override_model_name"

@pytest.fixture
def clearenv():
    """
    Fixture to clear the BELLE2_MODEL_PATH environment variable
    """
    if "BELLE2_MODEL_PATH" in os.environ:
        del os.environ["BELLE2_MODEL_PATH"]
    yield
    if "BELLE2_MODEL_PATH" in os.environ:
        del os.environ["BELLE2_MODEL_PATH"]
