"""
Export service for generating SRT and TXT files from transcription segments.

Provides functions to convert transcription segments into downloadable export formats
and implement the data flywheel for capturing human edits.
"""
from typing import List
from datetime import datetime, timezone
import json
import os

from app.models import TranscriptionSegment, ExportMetadata
from app.config import settings


def format_srt_timestamp(seconds: float) -> str:
    """
    Convert float seconds to SRT timestamp format HH:MM:SS,mmm

    Args:
        seconds: Time in seconds (can be float with milliseconds)

    Returns:
        Formatted timestamp string (e.g., "00:00:03,500")

    Examples:
        >>> format_srt_timestamp(0.5)
        '00:00:00,500'
        >>> format_srt_timestamp(125.75)
        '00:02:05,750'
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = round((seconds % 1) * 1000)  # Use round() instead of int() for precision

    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"


def generate_srt(segments: List[TranscriptionSegment]) -> str:
    """
    Generate SRT subtitle format from segments.

    SRT Format:
    1
    00:00:00,500 --> 00:00:03,200
    Subtitle text here

    2
    00:00:03,500 --> 00:00:07,800
    Another subtitle

    Args:
        segments: List of transcription segments with start, end, text

    Returns:
        Complete SRT file content as string
    """
    srt_lines = []

    for index, segment in enumerate(segments, start=1):
        # Convert float seconds to SRT timestamp: HH:MM:SS,mmm
        start_time = format_srt_timestamp(segment.start)
        end_time = format_srt_timestamp(segment.end)

        # SRT format: sequence number, timestamps, text, blank line
        srt_lines.append(f"{index}")
        srt_lines.append(f"{start_time} --> {end_time}")
        srt_lines.append(segment.text)
        srt_lines.append("")  # Blank line separator

    return "\n".join(srt_lines)


def generate_txt(segments: List[TranscriptionSegment]) -> str:
    """
    Generate plain text format from segments (no timestamps).

    Output: Space-separated text only
    Example: "Hello world Another segment Final text"

    Args:
        segments: List of transcription segments

    Returns:
        Space-separated plain text with no timestamps or formatting
    """
    texts = [segment.text for segment in segments]
    return " ".join(texts)


def save_edited_transcription(
    job_id: str,
    segments: List[TranscriptionSegment],
    format_requested: str
) -> ExportMetadata:
    """
    Save edited transcription and metadata for data flywheel.

    Process:
    1. Load original transcription from {UPLOAD_DIR}/{job_id}/transcription.json
    2. Compare original vs edited segments
    3. Count text changes
    4. Save edited.json and export_metadata.json

    Args:
        job_id: Unique job identifier
        segments: Edited transcription segments
        format_requested: Export format ('srt' or 'txt')

    Returns:
        ExportMetadata object with comparison statistics

    Raises:
        FileNotFoundError: If original transcription.json doesn't exist
        json.JSONDecodeError: If transcription.json is corrupted
    """
    uploads_dir = os.path.join(settings.UPLOAD_DIR, job_id)

    # Load original transcription
    original_path = os.path.join(uploads_dir, "transcription.json")
    with open(original_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
        original_segments = original_data.get("segments", [])

    # Compare and count changes
    changes_detected = 0
    for i, edited_seg in enumerate(segments):
        if i < len(original_segments):
            original_text = original_segments[i].get("text", "")
            if edited_seg.text != original_text:
                changes_detected += 1

    # Prepare metadata
    metadata = ExportMetadata(
        job_id=job_id,
        original_segment_count=len(original_segments),
        edited_segment_count=len(segments),
        export_timestamp=datetime.now(timezone.utc).isoformat(),
        format_requested=format_requested,
        changes_detected=changes_detected
    )

    # Save edited transcription with embedded metadata
    edited_data = {
        "job_id": job_id,
        "segments": [seg.model_dump() for seg in segments],
        "metadata": metadata.model_dump()
    }

    edited_path = os.path.join(uploads_dir, "edited.json")
    with open(edited_path, 'w', encoding='utf-8') as f:
        json.dump(edited_data, f, indent=2)

    # Save metadata separately for easy querying
    metadata_path = os.path.join(uploads_dir, "export_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata.model_dump(), f, indent=2)

    return metadata
