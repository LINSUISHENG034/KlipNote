"""
Quality metrics data models for multi-model transcription validation.

Pydantic models capture accuracy metrics (CER/WER), segment statistics,
character timing quality, confidence scores, and enhancement effectiveness.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SegmentLengthStats(BaseModel):
    """Segment length distribution and compliance statistics."""

    segment_count: int = Field(..., description="Total number of segments")
    mean_duration: float = Field(..., description="Mean segment duration in seconds")
    median_duration: float = Field(..., description="Median segment duration in seconds")
    p95_duration: float = Field(..., description="95th percentile duration in seconds")
    duration_compliance_pct: float = Field(
        ...,
        description="Percentage of segments meeting 1-7s constraint",
        ge=0.0,
        le=100.0,
    )
    too_short_count: int = Field(
        ..., description="Number of segments <1s (too short)"
    )
    too_long_count: int = Field(..., description="Number of segments >7s (too long)")


class CharacterLengthStats(BaseModel):
    """Character length distribution statistics for subtitle compliance."""

    mean_chars: int = Field(..., description="Mean character count per segment")
    median_chars: int = Field(..., description="Median character count per segment")
    p95_chars: int = Field(..., description="95th percentile character count")
    char_compliance_pct: float = Field(
        ...,
        description="Percentage of segments ≤200 chars",
        ge=0.0,
        le=100.0,
    )
    over_limit_count: int = Field(
        ..., description="Number of segments exceeding 200 char limit"
    )


class CharacterTimingStats(BaseModel):
    """Character-level timing coverage and quality metrics."""

    segments_with_chars: int = Field(
        ..., description="Number of segments with char[] metadata"
    )
    char_coverage_pct: float = Field(
        ...,
        description="Percentage of segments with character timing",
        ge=0.0,
        le=100.0,
    )
    total_chars: int = Field(..., description="Total character count across all segments")
    chars_with_timing: int = Field(
        ..., description="Number of characters with timing metadata"
    )
    mean_chars_per_segment: Optional[float] = Field(
        None, description="Average chars per segment (for segments with timing)"
    )


class ConfidenceStats(BaseModel):
    """Confidence score distribution and quality indicators."""

    segments_with_confidence: int = Field(
        ..., description="Number of segments with confidence scores"
    )
    confidence_coverage_pct: float = Field(
        ...,
        description="Percentage of segments with confidence metadata",
        ge=0.0,
        le=100.0,
    )
    mean_confidence: Optional[float] = Field(
        None, description="Mean confidence score (if available)", ge=0.0, le=1.0
    )
    median_confidence: Optional[float] = Field(
        None, description="Median confidence score", ge=0.0, le=1.0
    )
    low_confidence_count: int = Field(
        ..., description="Number of segments with confidence <0.7"
    )
    low_confidence_pct: float = Field(
        ...,
        description="Percentage of low confidence segments",
        ge=0.0,
        le=100.0,
    )


class EnhancementMetrics(BaseModel):
    """Enhancement pipeline effectiveness and impact metrics."""

    enhancements_applied: List[str] = Field(
        ..., description="List of enhancement components applied"
    )
    segments_modified_count: int = Field(
        ..., description="Number of segments modified by enhancements"
    )
    modification_rate_pct: float = Field(
        ...,
        description="Percentage of segments modified",
        ge=0.0,
        le=100.0,
    )
    vad_removed_count: Optional[int] = Field(
        None, description="Segments removed by VAD (if VAD applied)"
    )
    split_increase_count: Optional[int] = Field(
        None, description="Net segment increase from splitting (if splitter applied)"
    )
    refine_boundary_shifts: Optional[int] = Field(
        None,
        description="Number of boundaries refined (if timestamp refiner applied)",
    )


class QualityMetrics(BaseModel):
    """
    Comprehensive quality metrics for transcription validation.

    Combines accuracy metrics (CER/WER), segment statistics, character timing,
    confidence analysis, and enhancement effectiveness for multi-model comparison.
    """

    # Model and configuration context
    model_name: str = Field(..., description="Transcription model name (belle2/whisperx)")
    pipeline_config: str = Field(
        ..., description="Enhancement pipeline configuration (e.g., 'vad,refine,split')"
    )

    # Accuracy metrics (requires reference transcripts)
    cer: Optional[float] = Field(
        None, description="Character Error Rate (0.0-1.0, lower is better)", ge=0.0
    )
    wer: Optional[float] = Field(
        None, description="Word Error Rate (0.0-1.0, lower is better)", ge=0.0
    )

    # Segment length statistics
    segment_stats: SegmentLengthStats = Field(
        ..., description="Segment duration distribution and compliance"
    )

    # Character length statistics
    char_stats: CharacterLengthStats = Field(
        ..., description="Character count distribution for subtitle compliance"
    )

    # Character timing quality
    char_timing_stats: CharacterTimingStats = Field(
        ..., description="Character-level timing coverage and quality"
    )

    # Confidence score analysis
    confidence_stats: ConfidenceStats = Field(
        ..., description="Confidence score distribution and quality indicators"
    )

    # Enhancement effectiveness
    enhancement_metrics: EnhancementMetrics = Field(
        ..., description="Enhancement pipeline impact and effectiveness"
    )

    # Processing time metrics
    transcription_time: float = Field(..., description="Transcription time in seconds")
    enhancement_time: float = Field(..., description="Enhancement time in seconds")
    total_time: float = Field(..., description="Total processing time in seconds")

    # Additional metadata
    language: Optional[str] = Field(None, description="Detected or specified language")
    audio_duration: Optional[float] = Field(
        None, description="Audio file duration in seconds"
    )
    timestamp: str = Field(..., description="ISO 8601 timestamp of validation run")


class BaselineComparison(BaseModel):
    """Comparison between current metrics and baseline reference."""

    current_cer: Optional[float] = Field(None, description="Current CER")
    baseline_cer: Optional[float] = Field(None, description="Baseline CER")
    cer_delta: Optional[float] = Field(
        None, description="Change in CER (negative = improvement)"
    )
    cer_delta_pct: Optional[float] = Field(
        None, description="Percentage change in CER"
    )

    current_wer: Optional[float] = Field(None, description="Current WER")
    baseline_wer: Optional[float] = Field(None, description="Baseline WER")
    wer_delta: Optional[float] = Field(
        None, description="Change in WER (negative = improvement)"
    )
    wer_delta_pct: Optional[float] = Field(
        None, description="Percentage change in WER"
    )

    current_duration_compliance: float = Field(
        ..., description="Current segment duration compliance %"
    )
    baseline_duration_compliance: float = Field(
        ..., description="Baseline segment duration compliance %"
    )
    duration_compliance_delta: float = Field(
        ..., description="Change in duration compliance (positive = improvement)"
    )

    current_char_compliance: float = Field(
        ..., description="Current character count compliance %"
    )
    baseline_char_compliance: float = Field(
        ..., description="Baseline character count compliance %"
    )
    char_compliance_delta: float = Field(
        ..., description="Change in char compliance (positive = improvement)"
    )

    regression_detected: bool = Field(
        ...,
        description="True if quality regression detected (>15% CER/WER increase or >10% compliance drop)",
    )
    regression_details: Optional[str] = Field(
        None, description="Human-readable description of regression if detected"
    )


class ModelComparisonReport(BaseModel):
    """Side-by-side comparison of two models on the same corpus."""

    model_a_name: str = Field(..., description="First model name")
    model_b_name: str = Field(..., description="Second model name")
    pipeline_config: str = Field(..., description="Enhancement pipeline configuration")

    model_a_metrics: QualityMetrics = Field(..., description="Model A quality metrics")
    model_b_metrics: QualityMetrics = Field(..., description="Model B quality metrics")

    # Comparative analysis
    cer_comparison: Optional[str] = Field(
        None,
        description="Which model has better CER (if available)",
        examples=["model_a", "model_b", "tie"],
    )
    wer_comparison: Optional[str] = Field(
        None, description="Which model has better WER (if available)"
    )
    duration_compliance_comparison: str = Field(
        ..., description="Which model has better duration compliance"
    )
    char_compliance_comparison: str = Field(
        ..., description="Which model has better character compliance"
    )
    confidence_comparison: Optional[str] = Field(
        None, description="Which model has better confidence scores"
    )

    recommended_model: str = Field(
        ...,
        description="Recommended model based on overall metrics",
        examples=["model_a", "model_b", "depends_on_use_case"],
    )
    recommendation_rationale: str = Field(
        ..., description="Explanation of recommendation"
    )


__all__ = [
    "BaselineComparison",
    "CharacterLengthStats",
    "CharacterTimingStats",
    "ConfidenceStats",
    "EnhancementMetrics",
    "ModelComparisonReport",
    "QualityMetrics",
    "SegmentLengthStats",
]
