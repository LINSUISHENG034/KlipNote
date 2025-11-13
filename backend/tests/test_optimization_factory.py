"""
Unit tests for OptimizerFactory.

Tests factory pattern logic for all three modes (whisperx, heuristic, auto)
with mocked availability checks to verify selection and fallback behavior.

Story 3.2a: Pluggable Optimizer Architecture Design
"""

import pytest
from typing import List
from unittest.mock import patch
from app.ai_services.optimization import TimestampSegment
from app.ai_services.optimization.factory import OptimizerFactory
from app.ai_services.optimization.whisperx_optimizer import WhisperXOptimizer
from app.ai_services.optimization.heuristic_optimizer import HeuristicOptimizer


class TestOptimizerFactory:
    """Test suite for OptimizerFactory.create() method"""

    # ====================
    # Mode: whisperx
    # ====================

    def test_create_whisperx_available(self):
        """Test engine='whisperx' with WhisperX available returns WhisperXOptimizer"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
            optimizer = OptimizerFactory.create(engine="whisperx")
            assert isinstance(optimizer, WhisperXOptimizer)

    def test_create_whisperx_unavailable_fallback(self):
        """Test engine='whisperx' with WhisperX unavailable falls back to HeuristicOptimizer"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=False):
            optimizer = OptimizerFactory.create(engine="whisperx")
            assert isinstance(optimizer, HeuristicOptimizer)

    # ====================
    # Mode: heuristic
    # ====================

    def test_create_heuristic(self):
        """Test engine='heuristic' always returns HeuristicOptimizer"""
        optimizer = OptimizerFactory.create(engine="heuristic")
        assert isinstance(optimizer, HeuristicOptimizer)

    def test_create_heuristic_ignores_whisperx_availability(self):
        """Test engine='heuristic' returns HeuristicOptimizer even if WhisperX available"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
            optimizer = OptimizerFactory.create(engine="heuristic")
            assert isinstance(optimizer, HeuristicOptimizer)

    # ====================
    # Mode: auto
    # ====================

    def test_create_auto_whisperx_available(self):
        """Test engine='auto' with WhisperX available returns WhisperXOptimizer"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
            optimizer = OptimizerFactory.create(engine="auto")
            assert isinstance(optimizer, WhisperXOptimizer)

    def test_create_auto_whisperx_unavailable(self):
        """Test engine='auto' with WhisperX unavailable returns HeuristicOptimizer"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=False):
            optimizer = OptimizerFactory.create(engine="auto")
            assert isinstance(optimizer, HeuristicOptimizer)

    # ====================
    # Default (None) reads from settings
    # ====================

    def test_create_default_reads_from_settings(self):
        """Test engine=None reads OPTIMIZER_ENGINE from settings"""
        with patch('app.config.settings') as mock_settings:
            mock_settings.OPTIMIZER_ENGINE = "heuristic"
            optimizer = OptimizerFactory.create(engine=None)
            assert isinstance(optimizer, HeuristicOptimizer)

    def test_create_default_auto_whisperx_available(self):
        """Test engine=None with settings.OPTIMIZER_ENGINE='auto' and WhisperX available"""
        with patch('app.config.settings') as mock_settings:
            mock_settings.OPTIMIZER_ENGINE = "auto"
            with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
                optimizer = OptimizerFactory.create(engine=None)
                assert isinstance(optimizer, WhisperXOptimizer)

    def test_create_default_auto_whisperx_unavailable(self):
        """Test engine=None with settings.OPTIMIZER_ENGINE='auto' and WhisperX unavailable"""
        with patch('app.config.settings') as mock_settings:
            mock_settings.OPTIMIZER_ENGINE = "auto"
            with patch.object(WhisperXOptimizer, 'is_available', return_value=False):
                optimizer = OptimizerFactory.create(engine=None)
                assert isinstance(optimizer, HeuristicOptimizer)

    # ====================
    # Error handling
    # ====================

    def test_create_invalid_engine_raises_value_error(self):
        """Test invalid engine value raises ValueError"""
        with pytest.raises(ValueError, match="Unknown optimizer engine"):
            OptimizerFactory.create(engine="invalid")

    def test_create_invalid_engine_message_includes_valid_options(self):
        """Test ValueError message includes list of valid engines"""
        with pytest.raises(ValueError, match="whisperx.*heuristic.*auto"):
            OptimizerFactory.create(engine="nonexistent")

    # ====================
    # Logging behavior (optional - ensures logging calls made)
    # ====================

    def test_create_whisperx_logs_selection(self, caplog):
        """Test engine='whisperx' logs optimizer selection"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
            with caplog.at_level('INFO'):
                OptimizerFactory.create(engine="whisperx")
                assert "WhisperXOptimizer" in caplog.text

    def test_create_whisperx_logs_fallback_warning(self, caplog):
        """Test engine='whisperx' with unavailable WhisperX logs warning"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=False):
            with caplog.at_level('WARNING'):
                OptimizerFactory.create(engine="whisperx")
                assert "unavailable" in caplog.text.lower()
                assert "falling back" in caplog.text.lower()

    def test_create_heuristic_logs_selection(self, caplog):
        """Test engine='heuristic' logs optimizer selection"""
        with caplog.at_level('INFO'):
            OptimizerFactory.create(engine="heuristic")
            assert "HeuristicOptimizer" in caplog.text

    def test_create_auto_whisperx_available_logs_selection(self, caplog):
        """Test engine='auto' with WhisperX available logs selection"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
            with caplog.at_level('INFO'):
                OptimizerFactory.create(engine="auto")
                assert "Auto-selecting WhisperXOptimizer" in caplog.text

    def test_create_auto_whisperx_unavailable_logs_fallback(self, caplog):
        """Test engine='auto' with WhisperX unavailable logs fallback"""
        with patch.object(WhisperXOptimizer, 'is_available', return_value=False):
            with caplog.at_level('INFO'):
                OptimizerFactory.create(engine="auto")
                assert "Auto-selecting HeuristicOptimizer" in caplog.text


class TestWhisperXOptimizerAvailability:
    """Test WhisperXOptimizer.is_available() static method"""

    def test_is_available_stub_returns_false(self):
        """Story 3.2a stub always reports WhisperX unavailable"""
        assert WhisperXOptimizer.is_available() is False


class TestHeuristicOptimizerAvailability:
    """Test HeuristicOptimizer.is_available() static method"""

    def test_is_available_always_returns_true(self):
        """Test is_available() always returns True (no dependency conflicts)"""
        assert HeuristicOptimizer.is_available() is True


class TestHeuristicOptimizerBehavior:
    """Behavioral tests for HeuristicOptimizer stub implementation"""

    def test_optimize_returns_pass_through_segments(self):
        """Stub implementation should return the same segments with metrics"""
        segments: List[TimestampSegment] = [
            {"start": 0.0, "end": 1.0, "text": "你好", "confidence": 0.95},
            {"start": 1.0, "end": 2.0, "text": "世界"},
        ]
        optimizer = HeuristicOptimizer()
        result = optimizer.optimize(segments, audio_path="/tmp/audio.wav")

        assert result.optimizer_name == "heuristic"
        assert result.segments == segments
        assert result.metrics["segments_optimized"] == float(len(segments))
        assert result.metrics["latency_ms"] == 0.0

    def test_optimize_empty_segments_raises_value_error(self):
        """Empty payload should raise ValueError to surface caller issues"""
        optimizer = HeuristicOptimizer()
        with pytest.raises(ValueError, match="empty segment list"):
            optimizer.optimize([], audio_path="/tmp/audio.wav")
