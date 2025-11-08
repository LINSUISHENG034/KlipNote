"""
Integration tests for POST /export/{job_id} endpoint

Tests export API with various formats, error handling, and data flywheel storage.
"""
import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.models import TranscriptionSegment


client = TestClient(app)


@pytest.fixture
def mock_job_with_transcription(tmp_path, monkeypatch):
    """
    Create mock job directory with original transcription.json
    """
    # Mock job ID
    job_id = "550e8400-e29b-41d4-a716-446655440001"

    # Create job directory
    job_dir = tmp_path / job_id
    job_dir.mkdir()

    # Create original transcription
    original_segments = [
        {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
        {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."},
        {"start": 8.0, "end": 12.5, "text": "First topic is the quarterly results."}
    ]
    original_data = {"segments": original_segments}

    with open(job_dir / "transcription.json", 'w', encoding='utf-8') as f:
        json.dump(original_data, f)

    # Monkeypatch settings.UPLOAD_DIR to use tmp_path
    import app.main
    monkeypatch.setattr(app.main.settings, 'UPLOAD_DIR', str(tmp_path))

    return job_dir, job_id


class TestExportSuccess:
    """Test successful export operations"""

    def test_export_srt_format(self, mock_job_with_transcription):
        """Test SRT export generation"""
        job_dir, job_id = mock_job_with_transcription

        # Request body with edited segments
        segments = [
            {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
            {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."}
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200
        assert 'application/x-subrip' in response.headers['Content-Type']
        assert f'filename=transcript-{job_id}.srt' in response.headers['Content-Disposition']

        # Verify SRT content structure
        content = response.text
        assert '1\n' in content
        assert '00:00:00,500 --> 00:00:03,200' in content
        assert 'Hello, welcome to the meeting.' in content
        assert '2\n' in content
        assert '00:00:03,500 --> 00:00:07,800' in content

    def test_export_txt_format(self, mock_job_with_transcription):
        """Test TXT export generation"""
        job_dir, job_id = mock_job_with_transcription

        segments = [
            {"start": 0.5, "end": 3.2, "text": "First segment"},
            {"start": 3.5, "end": 7.8, "text": "Second segment"}
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'txt'}
        )

        assert response.status_code == 200
        assert 'text/plain' in response.headers['Content-Type']
        assert f'filename=transcript-{job_id}.txt' in response.headers['Content-Disposition']

        # Verify TXT content (space-separated, no timestamps)
        content = response.text
        assert content == "First segment Second segment"
        assert '0.5' not in content  # No timestamps

    def test_data_flywheel_files_created(self, mock_job_with_transcription):
        """Verify data flywheel creates edited.json and export_metadata.json"""
        job_dir, job_id = mock_job_with_transcription

        segments = [
            {"start": 0.5, "end": 3.2, "text": "Edited text"},
            {"start": 3.5, "end": 7.8, "text": "Another edit"}
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200

        # Verify data flywheel files exist
        assert (job_dir / "edited.json").exists()
        assert (job_dir / "export_metadata.json").exists()

        # Verify metadata content
        with open(job_dir / "export_metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        assert metadata["job_id"] == job_id
        assert metadata["format_requested"] == "srt"
        assert metadata["edited_segment_count"] == 2
        assert "export_timestamp" in metadata
        assert "changes_detected" in metadata

    def test_export_with_no_edits(self, mock_job_with_transcription):
        """Test export when segments are identical to original (changes_detected = 0)"""
        job_dir, job_id = mock_job_with_transcription

        # Use exact original segments (no edits)
        segments = [
            {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
            {"start": 3.5, "end": 7.8, "text": "Let's begin with today's agenda."},
            {"start": 8.0, "end": 12.5, "text": "First topic is the quarterly results."}
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'txt'}
        )

        assert response.status_code == 200

        # Verify metadata shows 0 changes
        with open(job_dir / "export_metadata.json", 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        assert metadata["changes_detected"] == 0

    def test_export_filename_format(self, mock_job_with_transcription):
        """Verify filename follows transcript-{job_id}.{ext} format"""
        job_dir, job_id = mock_job_with_transcription

        segments = [{"start": 0.5, "end": 3.2, "text": "Test"}]

        # Test SRT filename
        response_srt = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )
        assert f'transcript-{job_id}.srt' in response_srt.headers['Content-Disposition']

        # Test TXT filename
        response_txt = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'txt'}
        )
        assert f'transcript-{job_id}.txt' in response_txt.headers['Content-Disposition']


class TestExportErrors:
    """Test export error handling"""

    def test_export_job_not_found(self, tmp_path, monkeypatch):
        """Test 404 error for non-existent job"""
        # Monkeypatch settings to use empty tmp_path
        import app.main
        monkeypatch.setattr(app.main.settings, 'UPLOAD_DIR', str(tmp_path))

        non_existent_job = "550e8400-e29b-41d4-a716-446655440099"

        segments = [{"start": 0.5, "end": 3.2, "text": "Test"}]

        response = client.post(
            f'/export/{non_existent_job}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 404
        assert 'not found' in response.json()['detail'].lower()

    def test_export_invalid_job_id_format(self):
        """Test 400 error for invalid job_id format (not UUID)"""
        invalid_job_id = "not-a-valid-uuid"

        segments = [{"start": 0.5, "end": 3.2, "text": "Test"}]

        response = client.post(
            f'/export/{invalid_job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 400
        assert 'invalid' in response.json()['detail'].lower()

    def test_export_empty_segments(self, mock_job_with_transcription):
        """Test 422 error for empty segments array (Pydantic validation)"""
        job_dir, job_id = mock_job_with_transcription

        response = client.post(
            f'/export/{job_id}',
            json={'segments': [], 'format': 'srt'}
        )

        # Pydantic min_length=1 validation returns 422, not 400
        assert response.status_code == 422

    def test_export_invalid_format(self, mock_job_with_transcription):
        """Test 422 error for invalid format value (Pydantic validation)"""
        job_dir, job_id = mock_job_with_transcription

        segments = [{"start": 0.5, "end": 3.2, "text": "Test"}]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'invalid'}
        )

        # Pydantic validation error returns 422
        assert response.status_code == 422

    def test_export_missing_format_field(self, mock_job_with_transcription):
        """Test 422 error when format field is missing"""
        job_dir, job_id = mock_job_with_transcription

        segments = [{"start": 0.5, "end": 3.2, "text": "Test"}]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments}  # Missing 'format' field
        )

        assert response.status_code == 422

    def test_export_missing_segments_field(self, mock_job_with_transcription):
        """Test 422 error when segments field is missing"""
        job_dir, job_id = mock_job_with_transcription

        response = client.post(
            f'/export/{job_id}',
            json={'format': 'srt'}  # Missing 'segments' field
        )

        assert response.status_code == 422

    def test_export_invalid_segment_structure(self, mock_job_with_transcription):
        """Test 422 error for invalid segment data structure"""
        job_dir, job_id = mock_job_with_transcription

        # Segments missing required fields
        invalid_segments = [
            {"start": 0.5, "text": "Missing end field"}  # Missing 'end'
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': invalid_segments, 'format': 'srt'}
        )

        assert response.status_code == 422


class TestExportEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_export_single_segment(self, mock_job_with_transcription):
        """Test export with only one segment"""
        job_dir, job_id = mock_job_with_transcription

        segments = [{"start": 0.5, "end": 3.2, "text": "Only segment"}]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200
        assert 'Only segment' in response.text

    def test_export_many_segments(self, mock_job_with_transcription):
        """Test export with 100+ segments (performance check)"""
        job_dir, job_id = mock_job_with_transcription

        # Generate 100 segments
        segments = [
            {"start": i * 5.0, "end": i * 5.0 + 4.0, "text": f"Segment {i}"}
            for i in range(100)
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200

        # Verify SRT has 100 sequence numbers
        content = response.text
        assert '100\n' in content  # Last sequence number
        assert 'Segment 99' in content  # Last segment text

    def test_export_long_text_segments(self, mock_job_with_transcription):
        """Test export with very long text in segments"""
        job_dir, job_id = mock_job_with_transcription

        long_text = "This is a very long segment text. " * 50  # ~1750 chars

        segments = [{"start": 0.5, "end": 10.0, "text": long_text}]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200
        assert long_text in response.text

    def test_export_special_characters_in_text(self, mock_job_with_transcription):
        """Test export with special characters and unicode"""
        job_dir, job_id = mock_job_with_transcription

        segments = [
            {"start": 0.5, "end": 3.2, "text": "Special chars: @#$%^&*()"},
            {"start": 3.5, "end": 7.8, "text": "Unicode: ñ é ü 中文 日本語"},
            {"start": 8.0, "end": 12.5, "text": "Quotes: \"Hello\" and 'world'"}
        ]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200
        content = response.text

        # Verify special characters preserved
        assert "@#$%^&*()" in content
        assert "ñ é ü" in content
        assert "中文 日本語" in content
        assert '"Hello"' in content

    def test_export_zero_start_time(self, mock_job_with_transcription):
        """Test export with segment starting at 0.0 seconds"""
        job_dir, job_id = mock_job_with_transcription

        segments = [{"start": 0.0, "end": 2.5, "text": "Starting at zero"}]

        response = client.post(
            f'/export/{job_id}',
            json={'segments': segments, 'format': 'srt'}
        )

        assert response.status_code == 200
        assert '00:00:00,000' in response.text
