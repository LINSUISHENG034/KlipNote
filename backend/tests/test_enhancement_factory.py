"""Tests for EnhancementFactory.create_pipeline with configuration priority (AC-4.7-8)"""

import pytest
from app import config
from app.ai_services.enhancement.factory import create_pipeline
from app.ai_services.enhancement.vad_manager import VADManager
from app.ai_services.enhancement.timestamp_refiner import TimestampRefiner
from app.ai_services.enhancement.segment_splitter import SegmentSplitter


class TestConfigPriority:
    """Test configuration priority: API param > env vars > defaults (AC-4.7-8)"""

    def test_config_priority_api_overrides_env(self, monkeypatch):
        """Test API config takes precedence over environment variables"""
        # Set env vars (via settings) to non-default values
        monkeypatch.setattr(config.settings, "VAD_WEBRTC_AGGRESSIVENESS", 1)
        monkeypatch.setattr(config.settings, "REFINE_ENABLED", True)
        monkeypatch.setattr(config.settings, "REFINE_SEARCH_WINDOW_MS", 150)

        # API config with different values
        api_config = {
            "pipeline": "vad,refine",
            "vad": {"enabled": True, "aggressiveness": 3},
            "refine": {"enabled": True, "search_window_ms": 250}
        }

        pipeline = create_pipeline(config_dict=api_config)

        # Verify API value used (aggressiveness=3, not env's 1; window=250 not env's 150)
        components = pipeline.components
        assert len(components) >= 2

        # Find VAD component
        vad_component = next((c for c in components if isinstance(c, VADManager)), None)
        assert vad_component is not None
        # VAD aggressiveness should be 3 (from API), not 1 (from env)
        assert vad_component._engines["webrtc"].aggressiveness == 3

        # Find Refiner component
        refiner_component = next((c for c in components if isinstance(c, TimestampRefiner)), None)
        assert refiner_component is not None
        # Search window should be 250ms (from API), not 150ms (from env)
        assert refiner_component.search_window_ms == 250

    def test_config_priority_env_overrides_defaults(self, monkeypatch):
        """Test environment variables override default values"""
        # Configure settings to non-default values
        monkeypatch.setattr(config.settings, "VAD_WEBRTC_AGGRESSIVENESS", 1)
        monkeypatch.setattr(config.settings, "REFINE_SEARCH_WINDOW_MS", 150)
        monkeypatch.setattr(config.settings, "SPLIT_MAX_DURATION", 10.0)
        monkeypatch.setattr(config.settings, "SPLIT_MAX_CHARS", 250)

        pipeline = create_pipeline(config_dict=None)

        # Assuming settings have non-default values
        # This test verifies that env values are being used
        components = pipeline.components

        assert len(components) >= 3

        vad_component = next((c for c in components if isinstance(c, VADManager)), None)
        assert vad_component is not None
        assert vad_component._engines["webrtc"].aggressiveness == 1

        refiner_component = next((c for c in components if isinstance(c, TimestampRefiner)), None)
        assert refiner_component is not None
        assert refiner_component.search_window_ms == 150

        splitter_component = next((c for c in components if isinstance(c, SegmentSplitter)), None)
        assert splitter_component is not None
        assert splitter_component.max_duration == 10.0
        assert splitter_component.max_chars == 250

    def test_config_priority_defaults_used_when_no_env_or_api(self):
        """Test default values used when no config provided (AC-4.7-8)"""
        # No API config, ensure settings have sensible defaults
        pipeline = create_pipeline(config_dict=None)

        components = pipeline.components
        assert len(components) >= 3

        # Verify defaults are applied
        vad_component = next((c for c in components if isinstance(c, VADManager)), None)
        assert vad_component is not None

    def test_api_config_overrides_all_environment_vars(self, monkeypatch):
        """Test comprehensive API override of all components"""
        # Set all env vars
        monkeypatch.setattr(config.settings, "VAD_ENABLED", True)
        monkeypatch.setattr(config.settings, "VAD_WEBRTC_AGGRESSIVENESS", 2)
        monkeypatch.setattr(config.settings, "REFINE_ENABLED", True)
        monkeypatch.setattr(config.settings, "REFINE_SEARCH_WINDOW_MS", 150)
        monkeypatch.setattr(config.settings, "SPLIT_ENABLED", True)
        monkeypatch.setattr(config.settings, "SPLIT_MAX_DURATION", 10.0)
        monkeypatch.setattr(config.settings, "SPLIT_MAX_CHARS", 300)

        # API config with all different values
        api_config = {
            "pipeline": "vad,refine,split",
            "vad": {"enabled": True, "aggressiveness": 1},
            "refine": {"enabled": True, "search_window_ms": 300},
            "split": {"enabled": True, "max_duration": 8.0, "max_chars": 250}
        }

        pipeline = create_pipeline(config_dict=api_config)

        assert len(pipeline.components) == 3

        vad_component = next((c for c in pipeline.components if isinstance(c, VADManager)), None)
        assert vad_component._engines["webrtc"].aggressiveness == 1  # API value

        refiner_component = next((c for c in pipeline.components if isinstance(c, TimestampRefiner)), None)
        assert refiner_component.search_window_ms == 300  # API value

        splitter_component = next((c for c in pipeline.components if isinstance(c, SegmentSplitter)), None)
        assert splitter_component.max_duration == 8.0  # API value
        assert splitter_component.max_chars == 250  # API value

    def test_partial_api_config_merges_with_env_defaults(self, monkeypatch):
        """Test partial API config only overrides specified fields"""
        monkeypatch.setattr(config.settings, "VAD_WEBRTC_AGGRESSIVENESS", 2)
        monkeypatch.setattr(config.settings, "REFINE_SEARCH_WINDOW_MS", 150)
        monkeypatch.setattr(config.settings, "SPLIT_MAX_CHARS", 400)

        # Only override VAD in API config
        api_config = {
            "vad": {"enabled": True, "aggressiveness": 3}
        }

        pipeline = create_pipeline(config_dict=api_config)

        vad_component = next((c for c in pipeline.components if isinstance(c, VADManager)), None)
        assert vad_component._engines["webrtc"].aggressiveness == 3  # API value

        refiner_component = next((c for c in pipeline.components if isinstance(c, TimestampRefiner)), None)
        assert refiner_component.search_window_ms == 150  # Env value (since not in API)

        splitter_component = next((c for c in pipeline.components if isinstance(c, SegmentSplitter)), None)
        assert splitter_component.max_chars == 400  # Env value (since not in API)

    def test_disabled_component_in_api_config_skips_component(self, monkeypatch):
        """Test that disabled components are skipped in pipeline"""
        api_config = {
            "pipeline": "vad,refine,split",
            "vad": {"enabled": True, "aggressiveness": 3},
            "refine": {"enabled": False},  # Disabled
            "split": {"enabled": True, "max_duration": 5.0}
        }

        pipeline = create_pipeline(config_dict=api_config)

        components = pipeline.components
        assert len(components) == 2  # VAD and Split only

        # Refiner should be skipped
        refiner_component = next((c for c in components if isinstance(c, TimestampRefiner)), None)
        assert refiner_component is None

        # VAD and Splitter present
        vad_component = next((c for c in components if isinstance(c, VADManager)), None)
        assert vad_component is not None

        splitter_component = next((c for c in components if isinstance(c, SegmentSplitter)), None)
        assert splitter_component is not None
