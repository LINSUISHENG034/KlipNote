"""
Unit tests for QualityValidator class.

Tests CER/WER calculation, segment statistics, character timing validation,
confidence analysis, enhancement metrics, baseline comparison, and model comparison.
"""

import pytest

from app.ai_services.quality.models import (
    CharacterLengthStats,
    QualityMetrics,
    SegmentLengthStats,
    CharacterTimingStats,
    ConfidenceStats,
    EnhancementMetrics,
)
from app.ai_services.quality.validator import QualityValidator
from app.ai_services.schema import EnhancedSegment


@pytest.fixture
def validator():
    """Create QualityValidator instance for testing."""
    return QualityValidator()


@pytest.fixture
def sample_segments():
    """Create sample transcription segments for testing."""
    return [
        EnhancedSegment(
            start=0.0,
            end=3.5,
            text="This is the first segment.",
            confidence=0.95,
            chars=[
                {"char": "T", "start": 0.0, "end": 0.1},
                {"char": "h", "start": 0.1, "end": 0.2},
                # ... simplified for brevity
            ],
            words=[
                {"word": "This", "start": 0.0, "end": 0.5},
                {"word": "is", "start": 0.5, "end": 0.8},
            ],
            source_model="belle2",
            enhancements_applied=["VoiceActivityDetector", "TimestampRefiner"],
        ),
        EnhancedSegment(
            start=3.5,
            end=6.0,
            text="这是第二个片段，测试中文字符计数。",
            confidence=0.88,
            chars=[],
            words=[],
            source_model="belle2",
            enhancements_applied=["VoiceActivityDetector", "TimestampRefiner", "SegmentSplitter"],
        ),
        EnhancedSegment(
            start=6.0,
            end=8.5,
            text="Third segment for testing.",
            confidence=0.92,
            chars=[],
            words=[],
            source_model="belle2",
            enhancements_applied=[],
        ),
        EnhancedSegment(
            start=8.5,
            end=10.0,
            text="Short",
            confidence=0.65,  # Low confidence
            chars=[],
            words=[],
            source_model="belle2",
            enhancements_applied=[],
        ),
    ]


@pytest.fixture
def reference_segments():
    """Create reference segments for CER/WER testing."""
    return [
        EnhancedSegment(
            start=0.0,
            end=3.5,
            text="This is the first segment.",
            source_model="reference",
        ),
        EnhancedSegment(
            start=3.5,
            end=6.0,
            text="这是第二个片段，测试中文字符计数。",
            source_model="reference",
        ),
        EnhancedSegment(
            start=6.0,
            end=8.5,
            text="Third segment for testing.",
            source_model="reference",
        ),
        EnhancedSegment(
            start=8.5,
            end=10.0,
            text="Short",
            source_model="reference",
        ),
    ]


class TestCERCalculation:
    """Test Character Error Rate (CER) calculation."""

    def test_calculate_cer_perfect_match(self, validator, sample_segments, reference_segments):
        """Test CER calculation with perfect match (CER = 0.0)."""
        cer = validator.calculate_cer(sample_segments, reference_segments)
        assert cer is not None
        assert cer == 0.0, "Perfect match should have CER = 0.0"

    def test_calculate_cer_with_errors(self, validator):
        """Test CER calculation with character errors."""
        hypothesis = [EnhancedSegment(start=0.0, end=1.0, text="hello world")]
        reference = [EnhancedSegment(start=0.0, end=1.0, text="hello warld")]  # 1 char error

        cer = validator.calculate_cer(hypothesis, reference)
        assert cer is not None
        assert 0.0 < cer <= 1.0, "CER should be between 0 and 1"
        # Expected CER ≈ 1/11 ≈ 0.091
        assert 0.08 < cer < 0.1, f"Expected CER ≈ 0.091, got {cer}"

    def test_calculate_cer_empty_hypothesis(self, validator, reference_segments):
        """Test CER with empty hypothesis."""
        hypothesis = [EnhancedSegment(start=0.0, end=1.0, text="")]
        cer = validator.calculate_cer(hypothesis, reference_segments)
        # jiwer might return None or 1.0 for empty hypothesis
        assert cer is None or cer == 1.0

    def test_calculate_cer_empty_reference(self, validator, sample_segments):
        """Test CER with empty reference."""
        reference = [EnhancedSegment(start=0.0, end=1.0, text="")]
        cer = validator.calculate_cer(sample_segments, reference)
        assert cer is None  # Cannot calculate without reference


class TestWERCalculation:
    """Test Word Error Rate (WER) calculation."""

    def test_calculate_wer_perfect_match(self, validator, sample_segments, reference_segments):
        """Test WER calculation with perfect match (WER = 0.0)."""
        wer = validator.calculate_wer(sample_segments, reference_segments)
        assert wer is not None
        assert wer == 0.0, "Perfect match should have WER = 0.0"

    def test_calculate_wer_with_errors(self, validator):
        """Test WER calculation with word errors."""
        hypothesis = [
            EnhancedSegment(start=0.0, end=1.0, text="the quick brown fox")
        ]
        reference = [
            EnhancedSegment(start=0.0, end=1.0, text="the quick brown dog")
        ]  # 1 word error

        wer = validator.calculate_wer(hypothesis, reference)
        assert wer is not None
        assert 0.0 < wer <= 1.0
        # Expected WER = 1/4 = 0.25
        assert 0.24 < wer < 0.26, f"Expected WER ≈ 0.25, got {wer}"

    def test_calculate_wer_empty_hypothesis(self, validator, reference_segments):
        """Test WER with empty hypothesis."""
        hypothesis = [EnhancedSegment(start=0.0, end=1.0, text="")]
        wer = validator.calculate_wer(hypothesis, reference_segments)
        assert wer is None or wer == 1.0

    def test_calculate_wer_chinese_text(self, validator):
        """Test WER calculation with Chinese text (character-based word segmentation)."""
        hypothesis = [EnhancedSegment(start=0.0, end=1.0, text="你好世界")]
        reference = [EnhancedSegment(start=0.0, end=1.0, text="你好世界")]

        wer = validator.calculate_wer(hypothesis, reference)
        assert wer is not None
        # jiwer treats Chinese as single "words" without spaces
        # Perfect match should give WER = 0.0
        assert wer == 0.0


class TestSegmentStatistics:
    """Test segment length statistics calculation."""

    def test_calculate_segment_stats(self, validator, sample_segments):
        """Test segment statistics calculation."""
        stats = validator.calculate_segment_stats(sample_segments)

        assert stats.segment_count == 4
        assert stats.mean_duration > 0
        assert stats.median_duration > 0
        assert stats.p95_duration > 0
        assert 0 <= stats.duration_compliance_pct <= 100

        # Check specific durations
        # Segment 1: 3.5s, Segment 2: 2.5s, Segment 3: 2.5s, Segment 4: 1.5s
        # All are within 1-7s range, so compliance should be 100%
        assert stats.duration_compliance_pct == 100.0
        assert stats.too_short_count == 0
        assert stats.too_long_count == 0

    def test_calculate_segment_stats_with_violations(self, validator):
        """Test segment statistics with duration violations."""
        segments = [
            EnhancedSegment(start=0.0, end=0.5, text="Too short"),  # <1s
            EnhancedSegment(start=0.5, end=8.0, text="Too long" * 100),  # >7s
            EnhancedSegment(start=8.0, end=11.0, text="Compliant"),  # 3s, OK
        ]

        stats = validator.calculate_segment_stats(segments)

        assert stats.segment_count == 3
        assert stats.too_short_count == 1
        assert stats.too_long_count == 1
        # Only 1/3 segments compliant
        assert 30 < stats.duration_compliance_pct < 40

    def test_calculate_segment_stats_empty(self, validator):
        """Test segment statistics with empty segments list."""
        stats = validator.calculate_segment_stats([])

        assert stats.segment_count == 0
        assert stats.mean_duration == 0.0
        assert stats.duration_compliance_pct == 100.0  # No violations if no segments


class TestCharacterStatistics:
    """Test character length statistics calculation."""

    def test_calculate_char_stats(self, validator, sample_segments):
        """Test character statistics calculation."""
        stats = validator.calculate_char_stats(sample_segments)

        assert stats.mean_chars > 0
        assert stats.median_chars > 0
        assert stats.p95_chars > 0
        assert 0 <= stats.char_compliance_pct <= 100

        # All sample segments have <200 chars
        assert stats.char_compliance_pct == 100.0
        assert stats.over_limit_count == 0

    def test_calculate_char_stats_with_violations(self, validator):
        """Test character statistics with over-limit segments."""
        segments = [
            EnhancedSegment(start=0.0, end=1.0, text="Short"),  # 5 chars
            EnhancedSegment(start=1.0, end=2.0, text="A" * 250),  # >200 chars
            EnhancedSegment(start=2.0, end=3.0, text="B" * 150),  # OK
        ]

        stats = validator.calculate_char_stats(segments)

        assert stats.over_limit_count == 1
        # 2/3 segments compliant
        assert 65 < stats.char_compliance_pct < 70

    def test_calculate_char_stats_chinese(self, validator):
        """Test character statistics with Chinese text."""
        segments = [
            EnhancedSegment(start=0.0, end=1.0, text="你好世界这是测试"),  # 8 Chinese chars
            EnhancedSegment(start=1.0, end=2.0, text="Hello world"),  # 11 Latin chars
        ]

        stats = validator.calculate_char_stats(segments)

        # Mean should be around (8 + 11) / 2 = 9.5
        assert 9 <= stats.mean_chars <= 10
        assert stats.char_compliance_pct == 100.0  # All under 200


class TestCharacterTimingStats:
    """Test character-level timing coverage."""

    def test_calculate_char_timing_stats(self, validator, sample_segments):
        """Test character timing statistics."""
        stats = validator.calculate_char_timing_stats(sample_segments)

        assert stats.total_chars > 0
        # Only first segment has chars[] metadata
        assert stats.segments_with_chars == 1
        assert 0 < stats.char_coverage_pct < 100
        assert stats.chars_with_timing >= 0

    def test_calculate_char_timing_stats_no_timing(self, validator):
        """Test character timing stats with no timing metadata."""
        segments = [
            EnhancedSegment(start=0.0, end=1.0, text="No timing"),
            EnhancedSegment(start=1.0, end=2.0, text="Also no timing"),
        ]

        stats = validator.calculate_char_timing_stats(segments)

        assert stats.segments_with_chars == 0
        assert stats.char_coverage_pct == 0.0
        assert stats.chars_with_timing == 0
        assert stats.mean_chars_per_segment is None

    def test_calculate_char_timing_stats_full_coverage(self, validator):
        """Test character timing stats with 100% coverage."""
        segments = [
            EnhancedSegment(
                start=0.0,
                end=1.0,
                text="ABC",
                chars=[
                    {"char": "A", "start": 0.0, "end": 0.3},
                    {"char": "B", "start": 0.3, "end": 0.6},
                    {"char": "C", "start": 0.6, "end": 1.0},
                ],
            ),
            EnhancedSegment(
                start=1.0,
                end=2.0,
                text="DE",
                chars=[
                    {"char": "D", "start": 1.0, "end": 1.5},
                    {"char": "E", "start": 1.5, "end": 2.0},
                ],
            ),
        ]

        stats = validator.calculate_char_timing_stats(segments)

        assert stats.segments_with_chars == 2
        assert stats.char_coverage_pct == 100.0
        assert stats.chars_with_timing == 5
        assert stats.mean_chars_per_segment == 2.5  # (3 + 2) / 2


class TestConfidenceStats:
    """Test confidence score analysis."""

    def test_calculate_confidence_stats(self, validator, sample_segments):
        """Test confidence statistics calculation."""
        stats = validator.calculate_confidence_stats(sample_segments)

        # All 4 sample segments have confidence scores
        assert stats.segments_with_confidence == 4
        assert stats.confidence_coverage_pct == 100.0
        assert stats.mean_confidence is not None
        assert 0.0 <= stats.mean_confidence <= 1.0
        assert stats.median_confidence is not None

        # One segment has confidence 0.65 (< 0.7)
        assert stats.low_confidence_count == 1
        assert 20 < stats.low_confidence_pct < 30  # 1/4 = 25%

    def test_calculate_confidence_stats_no_confidence(self, validator):
        """Test confidence stats with no confidence metadata."""
        segments = [
            EnhancedSegment(start=0.0, end=1.0, text="No confidence"),
            EnhancedSegment(start=1.0, end=2.0, text="Also no confidence"),
        ]

        stats = validator.calculate_confidence_stats(segments)

        assert stats.segments_with_confidence == 0
        assert stats.confidence_coverage_pct == 0.0
        assert stats.mean_confidence is None
        assert stats.median_confidence is None
        assert stats.low_confidence_count == 0

    def test_calculate_confidence_stats_all_high(self, validator):
        """Test confidence stats with all high-confidence segments."""
        segments = [
            EnhancedSegment(start=0.0, end=1.0, text="High", confidence=0.95),
            EnhancedSegment(start=1.0, end=2.0, text="Also high", confidence=0.92),
        ]

        stats = validator.calculate_confidence_stats(segments)

        assert stats.segments_with_confidence == 2
        assert stats.low_confidence_count == 0
        assert stats.low_confidence_pct == 0.0
        assert stats.mean_confidence > 0.9


class TestEnhancementMetrics:
    """Test enhancement pipeline effectiveness metrics."""

    def test_calculate_enhancement_metrics(self, validator, sample_segments):
        """Test enhancement metrics calculation."""
        metrics = validator.calculate_enhancement_metrics(sample_segments)

        # Sample segments have various enhancements applied
        assert len(metrics.enhancements_applied) > 0
        assert "VoiceActivityDetector" in metrics.enhancements_applied
        assert "TimestampRefiner" in metrics.enhancements_applied

        # 2 out of 4 segments have enhancements
        assert metrics.segments_modified_count == 2
        assert 45 < metrics.modification_rate_pct < 55  # 2/4 = 50%

    def test_calculate_enhancement_metrics_no_enhancements(self, validator):
        """Test enhancement metrics with no enhancements applied."""
        segments = [
            EnhancedSegment(start=0.0, end=1.0, text="No enhancements"),
            EnhancedSegment(start=1.0, end=2.0, text="Also no enhancements"),
        ]

        metrics = validator.calculate_enhancement_metrics(segments)

        assert len(metrics.enhancements_applied) == 0
        assert metrics.segments_modified_count == 0
        assert metrics.modification_rate_pct == 0.0


class TestQualityMetricsCalculation:
    """Test comprehensive quality metrics calculation."""

    def test_calculate_quality_metrics_with_reference(
        self, validator, sample_segments, reference_segments
    ):
        """Test full quality metrics calculation with reference."""
        metrics = validator.calculate_quality_metrics(
            segments=sample_segments,
            model_name="belle2",
            pipeline_config="vad,refine,split",
            reference_segments=reference_segments,
            transcription_time=10.5,
            enhancement_time=2.3,
            language="zh",
            audio_duration=15.0,
        )

        assert isinstance(metrics, QualityMetrics)
        assert metrics.model_name == "belle2"
        assert metrics.pipeline_config == "vad,refine,split"
        assert metrics.cer is not None
        assert metrics.wer is not None
        assert metrics.segment_stats.segment_count == 4
        assert metrics.char_stats.mean_chars > 0
        assert metrics.char_timing_stats.char_coverage_pct > 0
        assert metrics.confidence_stats.confidence_coverage_pct > 0
        assert metrics.enhancement_metrics.enhancements_applied
        assert metrics.transcription_time == 10.5
        assert metrics.enhancement_time == 2.3
        assert metrics.total_time == 12.8
        assert metrics.language == "zh"
        assert metrics.audio_duration == 15.0
        assert metrics.timestamp  # ISO 8601 timestamp

    def test_calculate_quality_metrics_without_reference(
        self, validator, sample_segments
    ):
        """Test quality metrics calculation without reference (no CER/WER)."""
        metrics = validator.calculate_quality_metrics(
            segments=sample_segments,
            model_name="whisperx",
            pipeline_config="none",
            transcription_time=8.0,
            enhancement_time=0.0,
        )

        assert metrics.model_name == "whisperx"
        assert metrics.cer is None  # No reference provided
        assert metrics.wer is None
        assert metrics.segment_stats.segment_count == 4
        assert metrics.total_time == 8.0


class TestBaselineComparison:
    """Test baseline comparison functionality."""

    def test_compare_with_baseline_no_regression(self, validator):
        """Test baseline comparison with no regression detected."""
        baseline = QualityMetrics(
            model_name="belle2",
            pipeline_config="vad,refine,split",
            cer=0.05,
            wer=0.10,
            segment_stats=SegmentLengthStats(
                segment_count=100,
                mean_duration=3.5,
                median_duration=3.2,
                p95_duration=5.8,
                duration_compliance_pct=95.0,
                too_short_count=2,
                too_long_count=3,
            ),
            char_stats=CharacterLengthStats(
                mean_chars=85,
                median_chars=80,
                p95_chars=150,
                char_compliance_pct=98.0,
                over_limit_count=2,
            ),
            char_timing_stats=CharacterTimingStats(
                segments_with_chars=80,
                char_coverage_pct=80.0,
                total_chars=8500,
                chars_with_timing=6800,
                mean_chars_per_segment=85.0,
            ),
            confidence_stats=ConfidenceStats(
                segments_with_confidence=100,
                confidence_coverage_pct=100.0,
                mean_confidence=0.90,
                median_confidence=0.91,
                low_confidence_count=5,
                low_confidence_pct=5.0,
            ),
            enhancement_metrics=EnhancementMetrics(
                enhancements_applied=["VoiceActivityDetector"],
                segments_modified_count=50,
                modification_rate_pct=50.0,
            ),
            transcription_time=10.0,
            enhancement_time=2.0,
            total_time=12.0,
            timestamp="2025-01-01T00:00:00Z",
        )

        current = QualityMetrics(
            model_name="belle2",
            pipeline_config="vad,refine,split",
            cer=0.048,  # Slight improvement
            wer=0.098,  # Slight improvement
            segment_stats=SegmentLengthStats(
                segment_count=100,
                mean_duration=3.4,
                median_duration=3.1,
                p95_duration=5.7,
                duration_compliance_pct=96.0,
                too_short_count=1,
                too_long_count=3,
            ),
            char_stats=CharacterLengthStats(
                mean_chars=83,
                median_chars=78,
                p95_chars=148,
                char_compliance_pct=98.5,
                over_limit_count=1,
            ),
            char_timing_stats=CharacterTimingStats(
                segments_with_chars=82,
                char_coverage_pct=82.0,
                total_chars=8300,
                chars_with_timing=6800,
                mean_chars_per_segment=82.9,
            ),
            confidence_stats=ConfidenceStats(
                segments_with_confidence=100,
                confidence_coverage_pct=100.0,
                mean_confidence=0.91,
                median_confidence=0.92,
                low_confidence_count=4,
                low_confidence_pct=4.0,
            ),
            enhancement_metrics=EnhancementMetrics(
                enhancements_applied=["VoiceActivityDetector"],
                segments_modified_count=52,
                modification_rate_pct=52.0,
            ),
            transcription_time=9.5,
            enhancement_time=1.8,
            total_time=11.3,
            timestamp="2025-01-02T00:00:00Z",
        )

        comparison = validator.compare_with_baseline(current, baseline)

        assert comparison.regression_detected is False
        assert comparison.cer_delta < 0  # Improvement (negative delta)
        assert comparison.wer_delta < 0
        assert comparison.duration_compliance_delta > 0  # Improvement
        assert comparison.char_compliance_delta > 0

    def test_compare_with_baseline_cer_regression(self, validator):
        """Test baseline comparison with CER regression."""
        baseline = QualityMetrics(
            model_name="belle2",
            pipeline_config="vad,refine,split",
            cer=0.05,
            wer=0.10,
            segment_stats=SegmentLengthStats(
                segment_count=100,
                mean_duration=3.5,
                median_duration=3.2,
                p95_duration=5.8,
                duration_compliance_pct=95.0,
                too_short_count=2,
                too_long_count=3,
            ),
            char_stats=CharacterLengthStats(
                mean_chars=85,
                median_chars=80,
                p95_chars=150,
                char_compliance_pct=98.0,
                over_limit_count=2,
            ),
            char_timing_stats=CharacterTimingStats(
                segments_with_chars=80,
                char_coverage_pct=80.0,
                total_chars=8500,
                chars_with_timing=6800,
                mean_chars_per_segment=85.0,
            ),
            confidence_stats=ConfidenceStats(
                segments_with_confidence=100,
                confidence_coverage_pct=100.0,
                mean_confidence=0.90,
                median_confidence=0.91,
                low_confidence_count=5,
                low_confidence_pct=5.0,
            ),
            enhancement_metrics=EnhancementMetrics(
                enhancements_applied=[],
                segments_modified_count=0,
                modification_rate_pct=0.0,
            ),
            transcription_time=10.0,
            enhancement_time=0.0,
            total_time=10.0,
            timestamp="2025-01-01T00:00:00Z",
        )

        current = QualityMetrics(
            model_name="belle2",
            pipeline_config="vad,refine,split",
            cer=0.06,  # >15% increase: (0.06-0.05)/0.05 = 20%
            wer=0.10,
            segment_stats=SegmentLengthStats(
                segment_count=100,
                mean_duration=3.5,
                median_duration=3.2,
                p95_duration=5.8,
                duration_compliance_pct=95.0,
                too_short_count=2,
                too_long_count=3,
            ),
            char_stats=CharacterLengthStats(
                mean_chars=85,
                median_chars=80,
                p95_chars=150,
                char_compliance_pct=98.0,
                over_limit_count=2,
            ),
            char_timing_stats=CharacterTimingStats(
                segments_with_chars=80,
                char_coverage_pct=80.0,
                total_chars=8500,
                chars_with_timing=6800,
                mean_chars_per_segment=85.0,
            ),
            confidence_stats=ConfidenceStats(
                segments_with_confidence=100,
                confidence_coverage_pct=100.0,
                mean_confidence=0.90,
                median_confidence=0.91,
                low_confidence_count=5,
                low_confidence_pct=5.0,
            ),
            enhancement_metrics=EnhancementMetrics(
                enhancements_applied=[],
                segments_modified_count=0,
                modification_rate_pct=0.0,
            ),
            transcription_time=10.0,
            enhancement_time=0.0,
            total_time=10.0,
            timestamp="2025-01-02T00:00:00Z",
        )

        comparison = validator.compare_with_baseline(current, baseline)

        assert comparison.regression_detected is True
        assert "CER" in comparison.regression_details
        assert comparison.cer_delta_pct > 15.0  # >15% threshold


class TestModelComparison:
    """Test model comparison functionality."""

    def test_compare_models(self, validator):
        """Test side-by-side model comparison."""
        belle2_metrics = QualityMetrics(
            model_name="belle2",
            pipeline_config="vad,refine,split",
            cer=0.045,
            wer=0.09,
            segment_stats=SegmentLengthStats(
                segment_count=100,
                mean_duration=3.5,
                median_duration=3.2,
                p95_duration=5.8,
                duration_compliance_pct=96.0,
                too_short_count=1,
                too_long_count=3,
            ),
            char_stats=CharacterLengthStats(
                mean_chars=85,
                median_chars=80,
                p95_chars=150,
                char_compliance_pct=97.0,
                over_limit_count=3,
            ),
            char_timing_stats=CharacterTimingStats(
                segments_with_chars=85,
                char_coverage_pct=85.0,
                total_chars=8500,
                chars_with_timing=7225,
                mean_chars_per_segment=100.0,
            ),
            confidence_stats=ConfidenceStats(
                segments_with_confidence=100,
                confidence_coverage_pct=100.0,
                mean_confidence=0.92,
                median_confidence=0.93,
                low_confidence_count=3,
                low_confidence_pct=3.0,
            ),
            enhancement_metrics=EnhancementMetrics(
                enhancements_applied=["VoiceActivityDetector"],
                segments_modified_count=50,
                modification_rate_pct=50.0,
            ),
            transcription_time=12.0,
            enhancement_time=2.5,
            total_time=14.5,
            timestamp="2025-01-01T00:00:00Z",
        )

        whisperx_metrics = QualityMetrics(
            model_name="whisperx",
            pipeline_config="vad,refine,split",
            cer=0.05,
            wer=0.08,  # Better WER
            segment_stats=SegmentLengthStats(
                segment_count=100,
                mean_duration=3.4,
                median_duration=3.1,
                p95_duration=5.7,
                duration_compliance_pct=94.0,  # Slightly worse
                too_short_count=2,
                too_long_count=4,
            ),
            char_stats=CharacterLengthStats(
                mean_chars=82,
                median_chars=78,
                p95_chars=148,
                char_compliance_pct=98.0,  # Better
                over_limit_count=2,
            ),
            char_timing_stats=CharacterTimingStats(
                segments_with_chars=90,
                char_coverage_pct=90.0,
                total_chars=8200,
                chars_with_timing=7380,
                mean_chars_per_segment=91.1,
            ),
            confidence_stats=ConfidenceStats(
                segments_with_confidence=100,
                confidence_coverage_pct=100.0,
                mean_confidence=0.89,
                median_confidence=0.90,
                low_confidence_count=5,
                low_confidence_pct=5.0,
            ),
            enhancement_metrics=EnhancementMetrics(
                enhancements_applied=["VoiceActivityDetector"],
                segments_modified_count=48,
                modification_rate_pct=48.0,
            ),
            transcription_time=10.0,
            enhancement_time=2.0,
            total_time=12.0,
            timestamp="2025-01-01T00:00:00Z",
        )

        comparison = validator.compare_models(belle2_metrics, whisperx_metrics)

        assert comparison.model_a_name == "belle2"
        assert comparison.model_b_name == "whisperx"
        assert comparison.cer_comparison == "model_a"  # belle2 has better CER
        assert comparison.wer_comparison == "model_b"  # whisperx has better WER
        assert comparison.recommended_model in ["model_a", "model_b", "depends_on_use_case"]
        assert comparison.recommendation_rationale


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
