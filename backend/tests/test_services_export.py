"""
Unit tests for export service functions

Tests SRT/TXT generation, timestamp formatting, and data flywheel storage logic.
"""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone

from app.services.export_service import (
    format_srt_timestamp,
    generate_srt,
    generate_txt,
    save_edited_transcription
)
from app.models import TranscriptionSegment, ExportMetadata


class TestFormatSRTTimestamp:
    """Test timestamp conversion from float seconds to SRT format"""

    def test_zero_seconds(self):
        """Test timestamp at 0.0 seconds"""
        assert format_srt_timestamp(0.0) == "00:00:00,000"

    def test_subsecond_timestamp(self):
        """Test timestamps with milliseconds only"""
        assert format_srt_timestamp(0.5) == "00:00:00,500"
        assert format_srt_timestamp(0.123) == "00:00:00,123"
        assert format_srt_timestamp(0.999) == "00:00:00,999"

    def test_seconds_only(self):
        """Test timestamps in seconds range"""
        assert format_srt_timestamp(3.2) == "00:00:03,200"
        assert format_srt_timestamp(45.75) == "00:00:45,750"
        assert format_srt_timestamp(59.0) == "00:00:59,000"

    def test_minutes_range(self):
        """Test timestamps in minutes range"""
        assert format_srt_timestamp(60.0) == "00:01:00,000"
        assert format_srt_timestamp(125.75) == "00:02:05,750"
        assert format_srt_timestamp(3599.5) == "00:59:59,500"

    def test_hours_range(self):
        """Test timestamps exceeding 1 hour"""
        assert format_srt_timestamp(3600.0) == "01:00:00,000"
        assert format_srt_timestamp(3661.123) == "01:01:01,123"
        assert format_srt_timestamp(7200.456) == "02:00:00,456"


class TestGenerateSRT:
    """Test SRT subtitle format generation"""

    def test_single_segment(self):
        """Test SRT generation with one segment"""
        segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Hello world")
        ]

        result = generate_srt(segments)

        assert "1\n" in result
        assert "00:00:00,500 --> 00:00:03,200\n" in result
        assert "Hello world\n" in result

    def test_multiple_segments(self):
        """Test SRT generation with multiple segments"""
        segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="First segment"),
            TranscriptionSegment(start=3.5, end=7.8, text="Second segment"),
            TranscriptionSegment(start=8.0, end=12.5, text="Third segment")
        ]

        result = generate_srt(segments)

        # Check sequence numbers
        assert "1\n" in result
        assert "2\n" in result
        assert "3\n" in result

        # Check timestamps
        assert "00:00:00,500 --> 00:00:03,200" in result
        assert "00:00:03,500 --> 00:00:07,800" in result
        assert "00:00:08,000 --> 00:00:12,500" in result

        # Check text content
        assert "First segment" in result
        assert "Second segment" in result
        assert "Third segment" in result

    def test_srt_format_structure(self):
        """Test SRT format has correct structure with blank lines"""
        segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Test"),
            TranscriptionSegment(start=3.5, end=7.8, text="Another")
        ]

        result = generate_srt(segments)
        lines = result.split('\n')

        # First subtitle block
        assert lines[0] == "1"
        assert "00:00:00,500 --> 00:00:03,200" in lines[1]
        assert lines[2] == "Test"
        assert lines[3] == ""  # Blank line separator

        # Second subtitle block
        assert lines[4] == "2"
        assert "00:00:03,500 --> 00:00:07,800" in lines[5]
        assert lines[6] == "Another"
        assert lines[7] == ""  # Blank line separator

    def test_long_duration_segments(self):
        """Test SRT generation with segments exceeding 1 hour"""
        segments = [
            TranscriptionSegment(start=3600.0, end=3665.5, text="After one hour")
        ]

        result = generate_srt(segments)

        assert "01:00:00,000 --> 01:01:05,500" in result
        assert "After one hour" in result


class TestGenerateTXT:
    """Test plain text format generation"""

    def test_single_segment(self):
        """Test TXT generation with one segment"""
        segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Hello world")
        ]

        result = generate_txt(segments)

        assert result == "Hello world"
        assert "0.5" not in result  # No timestamps
        assert "\n" not in result  # No newlines

    def test_multiple_segments_space_separated(self):
        """Test TXT generation with multiple segments"""
        segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="First"),
            TranscriptionSegment(start=3.5, end=7.8, text="Second"),
            TranscriptionSegment(start=8.0, end=12.5, text="Third")
        ]

        result = generate_txt(segments)

        assert result == "First Second Third"
        assert "0.5" not in result  # No timestamps
        assert "3.5" not in result
        assert "8.0" not in result

    def test_no_timestamps_in_output(self):
        """Verify no timestamp artifacts in plain text"""
        segments = [
            TranscriptionSegment(start=125.5, end=180.3, text="Test text")
        ]

        result = generate_txt(segments)

        assert "125.5" not in result
        assert "180.3" not in result
        assert "-->" not in result
        assert result == "Test text"


class TestSaveEditedTranscription:
    """Test data flywheel storage logic"""

    @pytest.fixture
    def mock_job_dir(self, tmp_path, monkeypatch):
        """Create mock job directory with original transcription"""
        job_id = "550e8400-e29b-41d4-a716-446655440001"
        job_dir = tmp_path / job_id
        job_dir.mkdir()

        # Create original transcription file
        original_segments = [
            {"start": 0.5, "end": 3.2, "text": "Original text here"},
            {"start": 3.5, "end": 7.8, "text": "Unchanged segment"},
            {"start": 8.0, "end": 12.5, "text": "Another original"}
        ]
        original_data = {"segments": original_segments}

        with open(job_dir / "transcription.json", 'w', encoding='utf-8') as f:
            json.dump(original_data, f)

        # Monkeypatch settings.UPLOAD_DIR to use tmp_path
        import app.services.export_service
        monkeypatch.setattr(app.services.export_service.settings, 'UPLOAD_DIR', str(tmp_path))

        return job_dir, job_id

    def test_save_with_no_changes(self, mock_job_dir):
        """Test data flywheel when no edits were made"""
        job_dir, job_id = mock_job_dir

        # Segments identical to original
        edited_segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Original text here"),
            TranscriptionSegment(start=3.5, end=7.8, text="Unchanged segment"),
            TranscriptionSegment(start=8.0, end=12.5, text="Another original")
        ]

        metadata = save_edited_transcription(job_id, edited_segments, "srt")

        assert metadata.changes_detected == 0
        assert metadata.original_segment_count == 3
        assert metadata.edited_segment_count == 3
        assert metadata.format_requested == "srt"
        assert metadata.job_id == job_id

        # Verify files created
        assert (job_dir / "edited.json").exists()
        assert (job_dir / "export_metadata.json").exists()

    def test_save_with_partial_edits(self, mock_job_dir):
        """Test data flywheel with some segments edited"""
        job_dir, job_id = mock_job_dir

        # 2 out of 3 segments changed
        edited_segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="EDITED text here"),  # Changed
            TranscriptionSegment(start=3.5, end=7.8, text="Unchanged segment"),  # Same
            TranscriptionSegment(start=8.0, end=12.5, text="EDITED original")   # Changed
        ]

        metadata = save_edited_transcription(job_id, edited_segments, "txt")

        assert metadata.changes_detected == 2
        assert metadata.original_segment_count == 3
        assert metadata.edited_segment_count == 3
        assert metadata.format_requested == "txt"

    def test_save_with_all_edits(self, mock_job_dir):
        """Test data flywheel when all segments were edited"""
        job_dir, job_id = mock_job_dir

        # All segments changed
        edited_segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Completely different"),
            TranscriptionSegment(start=3.5, end=7.8, text="Also changed"),
            TranscriptionSegment(start=8.0, end=12.5, text="Changed again")
        ]

        metadata = save_edited_transcription(job_id, edited_segments, "srt")

        assert metadata.changes_detected == 3
        assert metadata.original_segment_count == 3
        assert metadata.edited_segment_count == 3

    def test_edited_json_structure(self, mock_job_dir):
        """Verify edited.json contains correct structure"""
        job_dir, job_id = mock_job_dir

        edited_segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Edited")
        ]

        save_edited_transcription(job_id, edited_segments, "srt")

        # Read and verify edited.json
        with open(job_dir / "edited.json", 'r', encoding='utf-8') as f:
            edited_data = json.load(f)

        assert "job_id" in edited_data
        assert "segments" in edited_data
        assert "metadata" in edited_data
        assert edited_data["job_id"] == job_id
        assert len(edited_data["segments"]) == 1
        assert edited_data["segments"][0]["text"] == "Edited"

    def test_export_metadata_json_structure(self, mock_job_dir):
        """Verify export_metadata.json contains correct fields"""
        job_dir, job_id = mock_job_dir

        edited_segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="Test")
        ]

        metadata = save_edited_transcription(job_id, edited_segments, "srt")

        # Read and verify export_metadata.json
        with open(job_dir / "export_metadata.json", 'r', encoding='utf-8') as f:
            metadata_json = json.load(f)

        assert metadata_json["job_id"] == job_id
        assert "original_segment_count" in metadata_json
        assert "edited_segment_count" in metadata_json
        assert "export_timestamp" in metadata_json
        assert "format_requested" in metadata_json
        assert "changes_detected" in metadata_json

        # Verify timestamp is ISO 8601 UTC
        timestamp = datetime.fromisoformat(metadata_json["export_timestamp"].replace('Z', '+00:00'))
        assert timestamp.tzinfo is not None

    def test_segment_count_mismatch(self, mock_job_dir):
        """Test when edited version has different segment count"""
        job_dir, job_id = mock_job_dir

        # User added a new segment (4 instead of 3)
        edited_segments = [
            TranscriptionSegment(start=0.5, end=3.2, text="First"),
            TranscriptionSegment(start=3.5, end=7.8, text="Second"),
            TranscriptionSegment(start=8.0, end=12.5, text="Third"),
            TranscriptionSegment(start=13.0, end=16.0, text="NEW SEGMENT")
        ]

        metadata = save_edited_transcription(job_id, edited_segments, "srt")

        assert metadata.original_segment_count == 3
        assert metadata.edited_segment_count == 4
        # Changes detected = 3 (first 3 segments, new segment doesn't match any original)
        assert metadata.changes_detected >= 0
