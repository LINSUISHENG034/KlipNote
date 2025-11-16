"""Tests for WebRTC VAD segment filtering and merging enhancements."""

import pytest
from unittest.mock import MagicMock, patch

from app.ai_services.enhancement.vad_engines.webrtc_vad import WebRTCVAD


class TestWebRTCVADFiltering:
    """Test WebRTC VAD short segment filtering."""

    def test_filters_short_segments(self):
        """Test that segments shorter than min_speech_ms are filtered out."""
        vad = WebRTCVAD(min_speech_ms=300)

        # Mock raw segments with some short ones
        raw_segments = [
            (0.0, 0.1),   # 100ms - should be filtered
            (1.0, 1.5),   # 500ms - should be kept
            (2.0, 2.15),  # 150ms - should be filtered
            (3.0, 3.8),   # 800ms - should be kept
        ]

        filtered = vad._filter_short_segments(raw_segments)

        assert len(filtered) == 2
        assert (1.0, 1.5) in filtered
        assert (3.0, 3.8) in filtered
        assert (0.0, 0.1) not in filtered
        assert (2.0, 2.15) not in filtered

    def test_keeps_segments_at_threshold(self):
        """Test that segments exactly at min_speech_ms are kept."""
        vad = WebRTCVAD(min_speech_ms=300)

        raw_segments = [
            (0.0, 0.3),   # Exactly 300ms - should be kept
            (1.0, 1.29),  # 290ms - should be filtered
            (2.0, 2.31),  # 310ms - should be kept
        ]

        filtered = vad._filter_short_segments(raw_segments)

        assert len(filtered) == 2
        assert (0.0, 0.3) in filtered
        assert (2.0, 2.31) in filtered

    def test_empty_segments_list(self):
        """Test handling of empty segment list."""
        vad = WebRTCVAD(min_speech_ms=300)
        filtered = vad._filter_short_segments([])
        assert filtered == []

    def test_all_segments_filtered(self):
        """Test when all segments are too short."""
        vad = WebRTCVAD(min_speech_ms=500)

        raw_segments = [
            (0.0, 0.1),   # 100ms
            (1.0, 1.2),   # 200ms
            (2.0, 2.3),   # 300ms
        ]

        filtered = vad._filter_short_segments(raw_segments)
        assert len(filtered) == 0


class TestWebRTCVADMerging:
    """Test WebRTC VAD segment merging."""

    def test_merges_close_segments(self):
        """Test that segments separated by <max_silence_ms are merged."""
        vad = WebRTCVAD(max_silence_ms=500)

        segments = [
            (0.0, 1.0),
            (1.3, 2.0),   # 300ms gap - should merge with previous
            (2.8, 3.5),   # 800ms gap - should NOT merge
            (3.9, 4.5),   # 400ms gap - should merge with previous
        ]

        merged = vad._merge_close_segments(segments)

        assert len(merged) == 2
        assert merged[0] == (0.0, 2.0)   # First two merged
        assert merged[1] == (2.8, 4.5)   # Last two merged

    def test_merge_at_threshold(self):
        """Test merging behavior at exact threshold."""
        vad = WebRTCVAD(max_silence_ms=500)

        segments = [
            (0.0, 1.0),
            (1.5, 2.0),   # Exactly 500ms gap - should merge
            (2.501, 3.0), # >500ms gap - should NOT merge
        ]

        merged = vad._merge_close_segments(segments)

        assert len(merged) == 2
        assert merged[0] == (0.0, 2.0)
        assert merged[1] == (2.501, 3.0)

    def test_no_merging_needed(self):
        """Test when no segments need merging."""
        vad = WebRTCVAD(max_silence_ms=500)

        segments = [
            (0.0, 1.0),
            (2.0, 3.0),   # 1000ms gap
            (5.0, 6.0),   # 2000ms gap
        ]

        merged = vad._merge_close_segments(segments)

        assert len(merged) == 3
        assert merged == segments

    def test_merge_multiple_consecutive(self):
        """Test merging multiple consecutive segments."""
        vad = WebRTCVAD(max_silence_ms=500)

        segments = [
            (0.0, 1.0),
            (1.2, 2.0),   # 200ms gap
            (2.3, 3.0),   # 300ms gap
            (3.4, 4.0),   # 400ms gap
        ]

        merged = vad._merge_close_segments(segments)

        assert len(merged) == 1
        assert merged[0] == (0.0, 4.0)

    def test_empty_segments_list(self):
        """Test handling of empty segment list."""
        vad = WebRTCVAD(max_silence_ms=500)
        merged = vad._merge_close_segments([])
        assert merged == []

    def test_single_segment(self):
        """Test handling of single segment."""
        vad = WebRTCVAD(max_silence_ms=500)
        segments = [(0.0, 1.0)]
        merged = vad._merge_close_segments(segments)
        assert merged == segments


class TestWebRTCVADIntegration:
    """Test full WebRTC VAD pipeline with filtering and merging."""

    @patch('pydub.AudioSegment')
    @patch('webrtcvad.Vad')
    def test_full_pipeline_filters_and_merges(self, mock_vad_class, mock_audio_segment_class):
        """Test that detect_speech applies both filtering and merging."""
        # Setup mocks
        mock_audio = MagicMock()
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.set_sample_width.return_value = mock_audio
        # 1.68 seconds of audio (56 frames * 30ms) to match speech pattern
        mock_audio.raw_data = b'\x00' * (16000 * 2 * 2)  # 2 seconds (enough for 56 frames + buffer)

        mock_audio_segment_class.from_file.return_value = mock_audio

        mock_vad = MagicMock()
        # Simulate speech detection pattern:
        # Frames 0-10: speech (330ms)
        # Frames 11-15: silence (150ms)
        # Frames 16-25: speech (330ms)
        # Frames 26-50: silence (750ms)
        # Frames 51-55: speech (165ms - short)
        # Frames 56+: silence (padding to cover all frames)
        speech_pattern = (
            [True] * 11 +     # 0-10: speech
            [False] * 5 +     # 11-15: silence
            [True] * 10 +     # 16-25: speech
            [False] * 25 +    # 26-50: long silence
            [True] * 5 +      # 51-55: short speech
            [False] * 100     # 56+: padding for remaining frames
        )
        mock_vad.is_speech.side_effect = speech_pattern
        mock_vad_class.return_value = mock_vad

        vad = WebRTCVAD(
            min_speech_ms=200,   # Filter segments <200ms
            max_silence_ms=200,  # Merge if gap <200ms
        )

        result = vad.detect_speech("test.wav")

        # Expected:
        # 1. Raw: (0.0-0.33), (0.48-0.78), (1.53-1.68)
        # 2. After filtering (>200ms): (0.0-0.33), (0.48-0.78) - last one filtered
        # 3. After merging (<200ms gap): (0.0-0.78) - first two merged
        assert len(result) == 1
        # Check approximate values (allow small floating point differences)
        assert abs(result[0][0] - 0.0) < 0.05
        assert abs(result[0][1] - 0.78) < 0.05

    def test_configurable_parameters(self):
        """Test that min_speech_ms and max_silence_ms are configurable."""
        vad1 = WebRTCVAD(min_speech_ms=200, max_silence_ms=300)
        assert vad1.min_speech_ms == 200
        assert vad1.max_silence_ms == 300

        vad2 = WebRTCVAD(min_speech_ms=500, max_silence_ms=1000)
        assert vad2.min_speech_ms == 500
        assert vad2.max_silence_ms == 1000

    def test_default_parameters(self):
        """Test default parameter values."""
        vad = WebRTCVAD()
        assert vad.min_speech_ms == 300   # Default
        assert vad.max_silence_ms == 500  # Default
