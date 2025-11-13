"""
Optimization module for timestamp optimization strategies.

This module provides a pluggable architecture for timestamp optimization,
supporting multiple implementations (WhisperX, Heuristic) selectable via configuration.

Story 3.2a: Pluggable Optimizer Architecture Design
"""

from .base import (
    OptimizationResult,
    TimestampOptimizer,
    TimestampSegment,
    WordTiming,
)
from .factory import OptimizerFactory
from .heuristic_optimizer import HeuristicOptimizer
from .whisperx_optimizer import WhisperXOptimizer

__all__ = [
    'TimestampOptimizer',
    'TimestampSegment',
    'WordTiming',
    'OptimizationResult',
    'HeuristicOptimizer',
    'WhisperXOptimizer',
    'OptimizerFactory',
]
