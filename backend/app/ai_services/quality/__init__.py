"""
Quality validation framework for multi-model transcription evaluation.

This module provides comprehensive quality metrics, baseline comparisons,
and model performance analysis for KlipNote's multi-model transcription system.
"""

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
from app.ai_services.quality.validator import QualityValidator

__all__ = [
    "BaselineComparison",
    "CharacterLengthStats",
    "CharacterTimingStats",
    "ConfidenceStats",
    "EnhancementMetrics",
    "ModelComparisonReport",
    "QualityMetrics",
    "QualityValidator",
    "SegmentLengthStats",
]
