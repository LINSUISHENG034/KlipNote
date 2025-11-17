"""
Quality validator for multi-model transcription evaluation.

Implements CER/WER calculation, segment statistics, character timing validation,
confidence analysis, enhancement effectiveness metrics, and baseline/model comparisons.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Optional

import jiwer
import numpy as np

from app.ai_services.quality.models import (
    BaselineComparison,
    CharacterLengthStats,
    CharacterTimingStats,
    ConfidenceStats,
    EnhancementMetrics,
    ModelComparisonReport,
    QualityMetrics,
    SegmentLengthStats,
)
from app.ai_services.schema import EnhancedSegment

logger = logging.getLogger(__name__)


class QualityValidator:
    """
    Comprehensive quality validation framework for transcription evaluation.

    Calculates accuracy metrics (CER/WER), segment statistics, character timing
    quality, confidence scores, enhancement effectiveness, and provides baseline
    and model comparison capabilities.
    """

    # Quality thresholds for regression detection
    CER_WER_REGRESSION_THRESHOLD = 0.15  # 15% increase triggers regression alert
    COMPLIANCE_REGRESSION_THRESHOLD = 0.10  # 10% decrease triggers alert
    LOW_CONFIDENCE_THRESHOLD = 0.7  # Confidence scores below this are flagged

    def __init__(self):
        """Initialize the quality validator."""
        self.logger = logging.getLogger(__name__)

    def calculate_cer(
        self,
        hypothesis_segments: List[EnhancedSegment],
        reference_segments: List[EnhancedSegment],
    ) -> Optional[float]:
        """
        Calculate Character Error Rate (CER) using jiwer library.

        Args:
            hypothesis_segments: Transcription segments to evaluate
            reference_segments: Ground truth reference segments

        Returns:
            CER as float between 0.0 and 1.0, or None if calculation fails
        """
        try:
            # Extract text from segments
            hypothesis_text = " ".join(seg["text"] for seg in hypothesis_segments)
            reference_text = " ".join(seg["text"] for seg in reference_segments)

            if not reference_text or not hypothesis_text:
                self.logger.warning("Empty hypothesis or reference text, cannot calculate CER")
                return None

            # Calculate CER using jiwer
            cer = jiwer.cer(reference_text, hypothesis_text)
            self.logger.info(f"CER calculated: {cer:.4f}")
            return float(cer)

        except Exception as e:
            self.logger.error(f"Failed to calculate CER: {e}", exc_info=True)
            return None

    def calculate_wer(
        self,
        hypothesis_segments: List[EnhancedSegment],
        reference_segments: List[EnhancedSegment],
    ) -> Optional[float]:
        """
        Calculate Word Error Rate (WER) using jiwer library.

        Args:
            hypothesis_segments: Transcription segments to evaluate
            reference_segments: Ground truth reference segments

        Returns:
            WER as float between 0.0 and 1.0, or None if calculation fails
        """
        try:
            # Extract text from segments
            hypothesis_text = " ".join(seg["text"] for seg in hypothesis_segments)
            reference_text = " ".join(seg["text"] for seg in reference_segments)

            if not reference_text or not hypothesis_text:
                self.logger.warning("Empty hypothesis or reference text, cannot calculate WER")
                return None

            # Calculate WER using jiwer
            wer = jiwer.wer(reference_text, hypothesis_text)
            self.logger.info(f"WER calculated: {wer:.4f}")
            return float(wer)

        except Exception as e:
            self.logger.error(f"Failed to calculate WER: {e}", exc_info=True)
            return None

    def calculate_segment_stats(
        self, segments: List[EnhancedSegment]
    ) -> SegmentLengthStats:
        """
        Calculate segment length statistics and compliance metrics.

        Args:
            segments: List of transcription segments

        Returns:
            SegmentLengthStats with duration distribution and compliance
        """
        durations = [seg["end"] - seg["start"] for seg in segments]

        if not durations:
            return SegmentLengthStats(
                segment_count=0,
                mean_duration=0.0,
                median_duration=0.0,
                p95_duration=0.0,
                duration_compliance_pct=100.0,
                too_short_count=0,
                too_long_count=0,
            )

        # Calculate statistics
        mean_duration = float(np.mean(durations))
        median_duration = float(np.median(durations))
        p95_duration = float(np.percentile(durations, 95))

        # Compliance: segments in 1-7s range
        compliant_count = sum(1 <= d <= 7 for d in durations)
        too_short_count = sum(d < 1 for d in durations)
        too_long_count = sum(d > 7 for d in durations)
        compliance_pct = (compliant_count / len(durations)) * 100

        self.logger.info(
            f"Segment stats: {len(segments)} segments, "
            f"mean={mean_duration:.2f}s, median={median_duration:.2f}s, "
            f"P95={p95_duration:.2f}s, compliance={compliance_pct:.1f}%"
        )

        return SegmentLengthStats(
            segment_count=len(segments),
            mean_duration=mean_duration,
            median_duration=median_duration,
            p95_duration=p95_duration,
            duration_compliance_pct=compliance_pct,
            too_short_count=too_short_count,
            too_long_count=too_long_count,
        )

    def calculate_char_stats(
        self, segments: List[EnhancedSegment]
    ) -> CharacterLengthStats:
        """
        Calculate character length statistics for subtitle compliance.

        Args:
            segments: List of transcription segments

        Returns:
            CharacterLengthStats with character count distribution
        """
        char_counts = [len(seg["text"]) for seg in segments]

        if not char_counts:
            return CharacterLengthStats(
                mean_chars=0,
                median_chars=0,
                p95_chars=0,
                char_compliance_pct=100.0,
                over_limit_count=0,
            )

        # Calculate statistics
        mean_chars = int(np.mean(char_counts))
        median_chars = int(np.median(char_counts))
        p95_chars = int(np.percentile(char_counts, 95))

        # Compliance: segments ≤200 characters
        compliant_count = sum(c <= 200 for c in char_counts)
        over_limit_count = sum(c > 200 for c in char_counts)
        compliance_pct = (compliant_count / len(char_counts)) * 100

        self.logger.info(
            f"Character stats: mean={mean_chars}, median={median_chars}, "
            f"P95={p95_chars}, compliance={compliance_pct:.1f}%"
        )

        return CharacterLengthStats(
            mean_chars=mean_chars,
            median_chars=median_chars,
            p95_chars=p95_chars,
            char_compliance_pct=compliance_pct,
            over_limit_count=over_limit_count,
        )

    def calculate_char_timing_stats(
        self, segments: List[EnhancedSegment]
    ) -> CharacterTimingStats:
        """
        Calculate character-level timing coverage and quality metrics.

        Args:
            segments: List of transcription segments

        Returns:
            CharacterTimingStats with character timing coverage analysis
        """
        segments_with_chars = sum(
            1 for seg in segments if "chars" in seg and seg["chars"]
        )
        total_chars = sum(len(seg["text"]) for seg in segments)
        chars_with_timing = sum(
            len(seg.get("chars", [])) for seg in segments if "chars" in seg
        )

        coverage_pct = (
            (segments_with_chars / len(segments)) * 100 if segments else 0.0
        )

        mean_chars_per_segment = None
        if segments_with_chars > 0:
            chars_in_segments_with_timing = [
                len(seg.get("chars", []))
                for seg in segments
                if "chars" in seg and seg["chars"]
            ]
            if chars_in_segments_with_timing:
                mean_chars_per_segment = float(np.mean(chars_in_segments_with_timing))

        self.logger.info(
            f"Character timing stats: {segments_with_chars}/{len(segments)} segments "
            f"({coverage_pct:.1f}%) have char[] metadata"
        )

        return CharacterTimingStats(
            segments_with_chars=segments_with_chars,
            char_coverage_pct=coverage_pct,
            total_chars=total_chars,
            chars_with_timing=chars_with_timing,
            mean_chars_per_segment=mean_chars_per_segment,
        )

    def calculate_confidence_stats(
        self, segments: List[EnhancedSegment]
    ) -> ConfidenceStats:
        """
        Calculate confidence score distribution and quality indicators.

        Args:
            segments: List of transcription segments

        Returns:
            ConfidenceStats with confidence score analysis
        """
        segments_with_confidence = [
            seg for seg in segments if seg.get("confidence") is not None
        ]
        confidence_scores = [seg["confidence"] for seg in segments_with_confidence]

        coverage_pct = (
            (len(segments_with_confidence) / len(segments)) * 100 if segments else 0.0
        )

        mean_confidence = None
        median_confidence = None
        if confidence_scores:
            mean_confidence = float(np.mean(confidence_scores))
            median_confidence = float(np.median(confidence_scores))

        low_confidence_count = sum(
            1 for score in confidence_scores if score < self.LOW_CONFIDENCE_THRESHOLD
        )
        low_confidence_pct = (
            (low_confidence_count / len(confidence_scores)) * 100
            if confidence_scores
            else 0.0
        )

        mean_conf_str = f"{mean_confidence:.3f}" if mean_confidence is not None else "N/A"
        self.logger.info(
            f"Confidence stats: {len(segments_with_confidence)}/{len(segments)} segments "
            f"({coverage_pct:.1f}%) have confidence scores, "
            f"mean={mean_conf_str}, "
            f"low_confidence={low_confidence_pct:.1f}%"
        )

        return ConfidenceStats(
            segments_with_confidence=len(segments_with_confidence),
            confidence_coverage_pct=coverage_pct,
            mean_confidence=mean_confidence,
            median_confidence=median_confidence,
            low_confidence_count=low_confidence_count,
            low_confidence_pct=low_confidence_pct,
        )

    def calculate_enhancement_metrics(
        self, segments: List[EnhancedSegment]
    ) -> EnhancementMetrics:
        """
        Calculate enhancement pipeline effectiveness and impact metrics.

        Args:
            segments: List of transcription segments

        Returns:
            EnhancementMetrics with pipeline impact analysis
        """
        # Collect unique enhancement names
        all_enhancements = set()
        segments_modified = 0

        for seg in segments:
            enhancements = seg.get("enhancements_applied", [])
            if enhancements:
                all_enhancements.update(enhancements)
                segments_modified += 1

        modification_rate_pct = (
            (segments_modified / len(segments)) * 100 if segments else 0.0
        )

        # Try to extract specific enhancement metrics
        vad_removed_count = None
        split_increase_count = None
        refine_boundary_shifts = None

        # These would need to be tracked during enhancement pipeline execution
        # For now, we detect presence of enhancements from metadata
        if "VoiceActivityDetector" in all_enhancements:
            # VAD removal count would need to be tracked in pipeline metrics
            vad_removed_count = 0  # Placeholder

        if "SegmentSplitter" in all_enhancements:
            # Split increase would need to be tracked in pipeline metrics
            split_increase_count = 0  # Placeholder

        if "TimestampRefiner" in all_enhancements:
            # Boundary shifts would need to be tracked in pipeline metrics
            refine_boundary_shifts = 0  # Placeholder

        self.logger.info(
            f"Enhancement metrics: {list(all_enhancements)}, "
            f"{segments_modified}/{len(segments)} segments modified "
            f"({modification_rate_pct:.1f}%)"
        )

        return EnhancementMetrics(
            enhancements_applied=list(all_enhancements),
            segments_modified_count=segments_modified,
            modification_rate_pct=modification_rate_pct,
            vad_removed_count=vad_removed_count,
            split_increase_count=split_increase_count,
            refine_boundary_shifts=refine_boundary_shifts,
        )

    def calculate_quality_metrics(
        self,
        segments: List[EnhancedSegment],
        model_name: str,
        pipeline_config: str,
        reference_segments: Optional[List[EnhancedSegment]] = None,
        transcription_time: float = 0.0,
        enhancement_time: float = 0.0,
        language: Optional[str] = None,
        audio_duration: Optional[float] = None,
    ) -> QualityMetrics:
        """
        Calculate comprehensive quality metrics for a transcription.

        Args:
            segments: Transcription segments to evaluate
            model_name: Name of transcription model (e.g., 'belle2', 'whisperx')
            pipeline_config: Enhancement pipeline configuration string
            reference_segments: Optional ground truth segments for CER/WER
            transcription_time: Transcription processing time in seconds
            enhancement_time: Enhancement processing time in seconds
            language: Detected or specified language
            audio_duration: Audio file duration in seconds

        Returns:
            QualityMetrics with comprehensive evaluation results
        """
        self.logger.info(
            f"Calculating quality metrics for {model_name} "
            f"with pipeline '{pipeline_config}' on {len(segments)} segments"
        )

        # Calculate accuracy metrics if reference available
        cer = None
        wer = None
        if reference_segments:
            cer = self.calculate_cer(segments, reference_segments)
            wer = self.calculate_wer(segments, reference_segments)

        # Calculate all statistics
        segment_stats = self.calculate_segment_stats(segments)
        char_stats = self.calculate_char_stats(segments)
        char_timing_stats = self.calculate_char_timing_stats(segments)
        confidence_stats = self.calculate_confidence_stats(segments)
        enhancement_metrics = self.calculate_enhancement_metrics(segments)

        # Generate timestamp
        timestamp = datetime.utcnow().isoformat() + "Z"

        metrics = QualityMetrics(
            model_name=model_name,
            pipeline_config=pipeline_config,
            cer=cer,
            wer=wer,
            segment_stats=segment_stats,
            char_stats=char_stats,
            char_timing_stats=char_timing_stats,
            confidence_stats=confidence_stats,
            enhancement_metrics=enhancement_metrics,
            transcription_time=transcription_time,
            enhancement_time=enhancement_time,
            total_time=transcription_time + enhancement_time,
            language=language,
            audio_duration=audio_duration,
            timestamp=timestamp,
        )

        self.logger.info(f"Quality metrics calculated successfully: {metrics.model_name}")
        return metrics

    def compare_with_baseline(
        self, current_metrics: QualityMetrics, baseline_metrics: QualityMetrics
    ) -> BaselineComparison:
        """
        Compare current metrics against baseline reference.

        Args:
            current_metrics: Current quality metrics
            baseline_metrics: Baseline reference metrics

        Returns:
            BaselineComparison with delta analysis and regression detection
        """
        self.logger.info(
            f"Comparing current metrics against baseline "
            f"(current: {current_metrics.model_name}, baseline: {baseline_metrics.model_name})"
        )

        # Calculate CER deltas
        cer_delta = None
        cer_delta_pct = None
        if current_metrics.cer is not None and baseline_metrics.cer is not None:
            cer_delta = current_metrics.cer - baseline_metrics.cer
            cer_delta_pct = (
                (cer_delta / baseline_metrics.cer) * 100 if baseline_metrics.cer > 0 else 0.0
            )

        # Calculate WER deltas
        wer_delta = None
        wer_delta_pct = None
        if current_metrics.wer is not None and baseline_metrics.wer is not None:
            wer_delta = current_metrics.wer - baseline_metrics.wer
            wer_delta_pct = (
                (wer_delta / baseline_metrics.wer) * 100 if baseline_metrics.wer > 0 else 0.0
            )

        # Calculate compliance deltas
        duration_compliance_delta = (
            current_metrics.segment_stats.duration_compliance_pct
            - baseline_metrics.segment_stats.duration_compliance_pct
        )
        char_compliance_delta = (
            current_metrics.char_stats.char_compliance_pct
            - baseline_metrics.char_stats.char_compliance_pct
        )

        # Detect regressions
        regression_detected = False
        regression_details = []

        if cer_delta_pct and cer_delta_pct > (self.CER_WER_REGRESSION_THRESHOLD * 100):
            regression_detected = True
            regression_details.append(
                f"CER increased by {cer_delta_pct:.1f}% (threshold: {self.CER_WER_REGRESSION_THRESHOLD * 100}%)"
            )

        if wer_delta_pct and wer_delta_pct > (self.CER_WER_REGRESSION_THRESHOLD * 100):
            regression_detected = True
            regression_details.append(
                f"WER increased by {wer_delta_pct:.1f}% (threshold: {self.CER_WER_REGRESSION_THRESHOLD * 100}%)"
            )

        if duration_compliance_delta < -(self.COMPLIANCE_REGRESSION_THRESHOLD * 100):
            regression_detected = True
            regression_details.append(
                f"Duration compliance dropped by {abs(duration_compliance_delta):.1f}% "
                f"(threshold: {self.COMPLIANCE_REGRESSION_THRESHOLD * 100}%)"
            )

        if char_compliance_delta < -(self.COMPLIANCE_REGRESSION_THRESHOLD * 100):
            regression_detected = True
            regression_details.append(
                f"Character compliance dropped by {abs(char_compliance_delta):.1f}% "
                f"(threshold: {self.COMPLIANCE_REGRESSION_THRESHOLD * 100}%)"
            )

        regression_summary = (
            "; ".join(regression_details) if regression_detected else None
        )

        if regression_detected:
            self.logger.warning(f"Quality regression detected: {regression_summary}")
        else:
            self.logger.info("No quality regression detected")

        return BaselineComparison(
            current_cer=current_metrics.cer,
            baseline_cer=baseline_metrics.cer,
            cer_delta=cer_delta,
            cer_delta_pct=cer_delta_pct,
            current_wer=current_metrics.wer,
            baseline_wer=baseline_metrics.wer,
            wer_delta=wer_delta,
            wer_delta_pct=wer_delta_pct,
            current_duration_compliance=current_metrics.segment_stats.duration_compliance_pct,
            baseline_duration_compliance=baseline_metrics.segment_stats.duration_compliance_pct,
            duration_compliance_delta=duration_compliance_delta,
            current_char_compliance=current_metrics.char_stats.char_compliance_pct,
            baseline_char_compliance=baseline_metrics.char_stats.char_compliance_pct,
            char_compliance_delta=char_compliance_delta,
            regression_detected=regression_detected,
            regression_details=regression_summary,
        )

    def compare_models(
        self,
        model_a_metrics: QualityMetrics,
        model_b_metrics: QualityMetrics,
    ) -> ModelComparisonReport:
        """
        Generate side-by-side comparison report for two models.

        Args:
            model_a_metrics: Quality metrics for model A
            model_b_metrics: Quality metrics for model B

        Returns:
            ModelComparisonReport with comparative analysis and recommendation
        """
        self.logger.info(
            f"Comparing models: {model_a_metrics.model_name} vs {model_b_metrics.model_name}"
        )

        # Compare CER
        cer_comparison = None
        if (
            model_a_metrics.cer is not None
            and model_b_metrics.cer is not None
        ):
            if model_a_metrics.cer < model_b_metrics.cer:
                cer_comparison = "model_a"
            elif model_b_metrics.cer < model_a_metrics.cer:
                cer_comparison = "model_b"
            else:
                cer_comparison = "tie"

        # Compare WER
        wer_comparison = None
        if (
            model_a_metrics.wer is not None
            and model_b_metrics.wer is not None
        ):
            if model_a_metrics.wer < model_b_metrics.wer:
                wer_comparison = "model_a"
            elif model_b_metrics.wer < model_a_metrics.wer:
                wer_comparison = "model_b"
            else:
                wer_comparison = "tie"

        # Compare duration compliance
        if (
            model_a_metrics.segment_stats.duration_compliance_pct
            > model_b_metrics.segment_stats.duration_compliance_pct
        ):
            duration_comparison = "model_a"
        elif (
            model_b_metrics.segment_stats.duration_compliance_pct
            > model_a_metrics.segment_stats.duration_compliance_pct
        ):
            duration_comparison = "model_b"
        else:
            duration_comparison = "tie"

        # Compare character compliance
        if (
            model_a_metrics.char_stats.char_compliance_pct
            > model_b_metrics.char_stats.char_compliance_pct
        ):
            char_comparison = "model_a"
        elif (
            model_b_metrics.char_stats.char_compliance_pct
            > model_a_metrics.char_stats.char_compliance_pct
        ):
            char_comparison = "model_b"
        else:
            char_comparison = "tie"

        # Compare confidence scores
        confidence_comparison = None
        if (
            model_a_metrics.confidence_stats.mean_confidence is not None
            and model_b_metrics.confidence_stats.mean_confidence is not None
        ):
            if (
                model_a_metrics.confidence_stats.mean_confidence
                > model_b_metrics.confidence_stats.mean_confidence
            ):
                confidence_comparison = "model_a"
            elif (
                model_b_metrics.confidence_stats.mean_confidence
                > model_a_metrics.confidence_stats.mean_confidence
            ):
                confidence_comparison = "model_b"
            else:
                confidence_comparison = "tie"

        # Generate recommendation
        model_a_wins = sum(
            [
                cer_comparison == "model_a" if cer_comparison else False,
                wer_comparison == "model_a" if wer_comparison else False,
                duration_comparison == "model_a",
                char_comparison == "model_a",
                confidence_comparison == "model_a" if confidence_comparison else False,
            ]
        )

        model_b_wins = sum(
            [
                cer_comparison == "model_b" if cer_comparison else False,
                wer_comparison == "model_b" if wer_comparison else False,
                duration_comparison == "model_b",
                char_comparison == "model_b",
                confidence_comparison == "model_b" if confidence_comparison else False,
            ]
        )

        if model_a_wins > model_b_wins:
            recommended_model = "model_a"
            rationale = (
                f"{model_a_metrics.model_name} wins on {model_a_wins} of 5 metrics "
                f"(CER, WER, duration compliance, char compliance, confidence)"
            )
        elif model_b_wins > model_a_wins:
            recommended_model = "model_b"
            rationale = (
                f"{model_b_metrics.model_name} wins on {model_b_wins} of 5 metrics "
                f"(CER, WER, duration compliance, char compliance, confidence)"
            )
        else:
            recommended_model = "depends_on_use_case"
            rationale = (
                f"Models tied on {model_a_wins} metrics each. "
                "Recommendation depends on specific use case priorities."
            )

        self.logger.info(f"Model comparison complete: {recommended_model} - {rationale}")

        return ModelComparisonReport(
            model_a_name=model_a_metrics.model_name,
            model_b_name=model_b_metrics.model_name,
            pipeline_config=model_a_metrics.pipeline_config,
            model_a_metrics=model_a_metrics,
            model_b_metrics=model_b_metrics,
            cer_comparison=cer_comparison,
            wer_comparison=wer_comparison,
            duration_compliance_comparison=duration_comparison,
            char_compliance_comparison=char_comparison,
            confidence_comparison=confidence_comparison,
            recommended_model=recommended_model,
            recommendation_rationale=rationale,
        )


__all__ = ["QualityValidator"]
