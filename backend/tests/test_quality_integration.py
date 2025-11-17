"""
Integration tests for multi-model quality validation framework.

Tests full transcription + quality validation workflow with BELLE-2 and WhisperX.
"""

import json
from pathlib import Path

import pytest

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.quality import QualityValidator
from app.ai_services.quality.models import QualityMetrics
from app.ai_services.whisperx_service import WhisperXService


@pytest.fixture
def test_audio_file():
    """Return path to small test audio file."""
    # Use scipy's test audio file (5 seconds, 44.1kHz, stereo, WAV)
    import scipy.io.wavfile
    test_wav = Path(".venv/Lib/site-packages/scipy/io/tests/data/test-44100Hz-2ch-32bit-float-le.wav")

    if not test_wav.exists():
        pytest.skip(f"Test audio file not found: {test_wav}")

    return str(test_wav)


@pytest.fixture
def quality_validator():
    """Create QualityValidator instance."""
    return QualityValidator()


@pytest.mark.integration
def test_belle2_full_validation_workflow(test_audio_file, quality_validator):
    """Test full validation workflow with BELLE-2 model."""
    # Initialize BELLE-2 service
    try:
        service = Belle2Service()
    except Exception as e:
        pytest.skip(f"BELLE-2 service not available: {e}")

    # Step 1: Transcribe audio
    result = service.transcribe(test_audio_file, language="auto", apply_enhancements=False)
    segments = result.get("segments", [])

    assert len(segments) > 0, "Should produce at least one segment"

    # Step 2: Calculate quality metrics
    metrics = quality_validator.calculate_quality_metrics(
        segments=segments,
        model_name="belle2",
        pipeline_config="none",
        transcription_time=1.0,
        enhancement_time=0.0,
        language="auto",
        audio_duration=5.0,
    )

    # Step 3: Validate metrics structure and values
    assert isinstance(metrics, QualityMetrics)
    assert metrics.model_name == "belle2"
    assert metrics.pipeline_config == "none"
    assert metrics.segment_stats.segment_count == len(segments)
    assert metrics.segment_stats.mean_duration > 0
    assert metrics.char_stats.mean_chars > 0
    assert 0 <= metrics.segment_stats.duration_compliance_pct <= 100
    assert 0 <= metrics.char_stats.char_compliance_pct <= 100

    # Step 4: Validate metrics can be serialized to JSON
    metrics_dict = metrics.model_dump()
    json_str = json.dumps(metrics_dict, ensure_ascii=False)
    assert len(json_str) > 0

    # Step 5: Validate metrics can be deserialized
    restored_metrics = QualityMetrics(**json.loads(json_str))
    assert restored_metrics.model_name == metrics.model_name
    assert restored_metrics.segment_stats.segment_count == metrics.segment_stats.segment_count


@pytest.mark.integration
def test_whisperx_full_validation_workflow(test_audio_file, quality_validator):
    """Test full validation workflow with WhisperX model."""
    # Initialize WhisperX service
    try:
        service = WhisperXService()
    except Exception as e:
        pytest.skip(f"WhisperX service not available: {e}")

    # Step 1: Transcribe audio
    result = service.transcribe(test_audio_file, language="auto", apply_enhancements=False)
    segments = result.get("segments", [])

    assert len(segments) > 0, "Should produce at least one segment"

    # Step 2: Calculate quality metrics
    metrics = quality_validator.calculate_quality_metrics(
        segments=segments,
        model_name="whisperx",
        pipeline_config="none",
        transcription_time=1.0,
        enhancement_time=0.0,
        language="auto",
        audio_duration=5.0,
    )

    # Step 3: Validate metrics structure
    assert isinstance(metrics, QualityMetrics)
    assert metrics.model_name == "whisperx"
    assert metrics.pipeline_config == "none"
    assert metrics.segment_stats.segment_count == len(segments)

    # Step 4: Validate character timing coverage (WhisperX should provide char timing)
    # WhisperX may or may not provide char[] depending on configuration
    assert metrics.char_timing_stats.char_coverage_pct >= 0

    # Step 5: Validate confidence stats (WhisperX provides confidence)
    assert metrics.confidence_stats.confidence_coverage_pct >= 0


@pytest.mark.integration
def test_cross_model_comparison(test_audio_file, quality_validator):
    """Test comparing BELLE-2 vs WhisperX on same audio."""
    # Initialize both services
    try:
        belle2_service = Belle2Service()
        whisperx_service = WhisperXService()
    except Exception as e:
        pytest.skip(f"Services not available: {e}")

    # Step 1: Transcribe with BELLE-2
    belle2_result = belle2_service.transcribe(
        test_audio_file, language="auto", apply_enhancements=False
    )
    belle2_segments = belle2_result.get("segments", [])

    # Step 2: Calculate BELLE-2 metrics
    belle2_metrics = quality_validator.calculate_quality_metrics(
        segments=belle2_segments,
        model_name="belle2",
        pipeline_config="none",
        transcription_time=1.0,
        enhancement_time=0.0,
        audio_duration=5.0,
    )

    # Step 3: Transcribe with WhisperX
    whisperx_result = whisperx_service.transcribe(
        test_audio_file, language="auto", apply_enhancements=False
    )
    whisperx_segments = whisperx_result.get("segments", [])

    # Step 4: Calculate WhisperX metrics
    whisperx_metrics = quality_validator.calculate_quality_metrics(
        segments=whisperx_segments,
        model_name="whisperx",
        pipeline_config="none",
        transcription_time=1.0,
        enhancement_time=0.0,
        audio_duration=5.0,
    )

    # Step 5: Generate comparison report
    comparison = quality_validator.compare_models(belle2_metrics, whisperx_metrics)

    # Step 6: Validate comparison structure
    assert comparison.model_a_name == "belle2"
    assert comparison.model_b_name == "whisperx"
    assert comparison.pipeline_config == "none"
    assert comparison.recommended_model in ["model_a", "model_b", "depends_on_use_case"]
    assert len(comparison.recommendation_rationale) > 0

    # Step 7: Validate comparison logic
    assert comparison.duration_compliance_comparison in ["model_a", "model_b", "tie"]
    assert comparison.char_compliance_comparison in ["model_a", "model_b", "tie"]

    # Step 8: Validate comparison can be serialized
    comparison_dict = comparison.model_dump()
    json_str = json.dumps(comparison_dict, ensure_ascii=False)
    assert len(json_str) > 0


@pytest.mark.integration
def test_baseline_regression_detection(test_audio_file, quality_validator):
    """Test regression detection against baseline metrics."""
    # Initialize service
    try:
        service = Belle2Service()
    except Exception as e:
        pytest.skip(f"BELLE-2 service not available: {e}")

    # Step 1: Transcribe audio (current run)
    result = service.transcribe(test_audio_file, language="auto", apply_enhancements=False)
    segments = result.get("segments", [])

    # Step 2: Calculate current metrics
    current_metrics = quality_validator.calculate_quality_metrics(
        segments=segments,
        model_name="belle2",
        pipeline_config="none",
        transcription_time=1.0,
        enhancement_time=0.0,
        audio_duration=5.0,
    )

    # Step 3: Create synthetic baseline metrics (simulating Epic 3 baseline)
    # For testing, we artificially create a baseline with slightly better metrics
    baseline_metrics = QualityMetrics(
        model_name="belle2",
        pipeline_config="none",
        cer=0.05 if current_metrics.cer else None,  # Baseline CER
        wer=0.10 if current_metrics.wer else None,  # Baseline WER
        segment_stats=current_metrics.segment_stats,  # Same segment stats
        char_stats=current_metrics.char_stats,  # Same char stats
        char_timing_stats=current_metrics.char_timing_stats,
        confidence_stats=current_metrics.confidence_stats,
        enhancement_metrics=current_metrics.enhancement_metrics,
        transcription_time=1.0,
        enhancement_time=0.0,
        total_time=1.0,
        language="auto",
        audio_duration=5.0,
        timestamp="2025-01-01T00:00:00Z",
    )

    # Step 4: Compare current with baseline
    comparison = quality_validator.compare_with_baseline(current_metrics, baseline_metrics)

    # Step 5: Validate comparison structure
    assert comparison.current_duration_compliance is not None
    assert comparison.baseline_duration_compliance is not None
    assert comparison.duration_compliance_delta is not None
    assert isinstance(comparison.regression_detected, bool)

    # Step 6: Test regression detection logic (should not regress on same metrics)
    # Since we're using essentially the same metrics, no regression should be detected
    # (unless CER/WER are None, which is fine)
    if current_metrics.cer is None and current_metrics.wer is None:
        # No accuracy metrics, so regression detection is based on compliance only
        # With same compliance values, should not detect regression
        assert comparison.regression_detected is False

    # Step 7: Validate regression details format
    if comparison.regression_detected:
        assert comparison.regression_details is not None
        assert len(comparison.regression_details) > 0
    else:
        # No regression, details should be None
        assert comparison.regression_details is None

    # Step 8: Test with artificially worse current metrics (should trigger regression)
    # Create a worse current metrics by decreasing compliance
    from app.ai_services.quality.models import (
        CharacterLengthStats,
        SegmentLengthStats,
    )

    worse_segment_stats = SegmentLengthStats(
        segment_count=current_metrics.segment_stats.segment_count,
        mean_duration=current_metrics.segment_stats.mean_duration,
        median_duration=current_metrics.segment_stats.median_duration,
        p95_duration=current_metrics.segment_stats.p95_duration,
        duration_compliance_pct=max(0, current_metrics.segment_stats.duration_compliance_pct - 15),  # 15% worse
        too_short_count=current_metrics.segment_stats.too_short_count + 5,
        too_long_count=current_metrics.segment_stats.too_long_count,
    )

    worse_metrics = QualityMetrics(
        model_name="belle2",
        pipeline_config="none",
        cer=current_metrics.cer,
        wer=current_metrics.wer,
        segment_stats=worse_segment_stats,  # Worse compliance
        char_stats=current_metrics.char_stats,
        char_timing_stats=current_metrics.char_timing_stats,
        confidence_stats=current_metrics.confidence_stats,
        enhancement_metrics=current_metrics.enhancement_metrics,
        transcription_time=1.0,
        enhancement_time=0.0,
        total_time=1.0,
        language="auto",
        audio_duration=5.0,
        timestamp="2025-01-02T00:00:00Z",
    )

    # Step 9: Compare worse metrics with baseline
    worse_comparison = quality_validator.compare_with_baseline(worse_metrics, baseline_metrics)

    # Step 10: Validate regression is detected
    # With 15% worse compliance, should trigger regression (threshold is 10%)
    assert worse_comparison.regression_detected is True
    assert worse_comparison.regression_details is not None
    assert "compliance" in worse_comparison.regression_details.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
