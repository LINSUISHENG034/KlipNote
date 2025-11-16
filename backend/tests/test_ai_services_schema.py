from app.ai_services.schema import (
    BaseSegment,
    EnhancedSegment,
    TimestampSegment,
    TranscriptionResult,
    build_transcription_result,
)


def test_timestamp_segment_alias():
    """Alias exists for backward compatibility (AC #2)."""
    assert TimestampSegment is EnhancedSegment


def test_build_transcription_result_round_trip():
    segments: List[BaseSegment] = [
        {"start": 0.0, "end": 1.0, "text": "hello"},
        {"start": 1.0, "end": 2.0, "text": "world", "confidence": 0.9, "avg_logprob": -0.1},
    ]

    result: TranscriptionResult = build_transcription_result(
        segments=segments,
        language="en",
        model_name="whisperx",
        processing_time=0.123,
        duration=2.0,
        vad_enabled=True,
        alignment_model="whisperx",
        enhancements_applied=["vad:silero"],
    )

    assert "segments" in result
    assert len(result["segments"]) == 2
    assert result["segments"][0]["text"] == "hello"
    assert result["segments"][1]["confidence"] == 0.9
    assert result["metadata"]["language"] == "en"
    assert result["metadata"]["model_name"] == "whisperx"
    assert result["metadata"]["vad_enabled"] is True
    assert "vad:silero" in result["stats"]["enhancements_applied"]
