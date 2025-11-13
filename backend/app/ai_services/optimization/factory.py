"""
Factory for creating timestamp optimizer instances.

This factory provides configuration-driven optimizer selection with automatic
fallback logic, enabling pluggable architecture without code changes.

Story 3.2a: Pluggable Optimizer Architecture Design
"""

import logging
from .base import TimestampOptimizer
from .whisperx_optimizer import WhisperXOptimizer
from .heuristic_optimizer import HeuristicOptimizer


logger = logging.getLogger(__name__)


class OptimizerFactory:
    """
    Factory for creating timestamp optimizer instances based on configuration.

    Supports three modes:
        - "whisperx": Try WhisperX, fallback to Heuristic if unavailable
        - "heuristic": Always use HeuristicOptimizer
        - "auto" (default): Prefer WhisperX, fallback to Heuristic

    Usage:
        # From configuration (default)
        optimizer = OptimizerFactory.create()

        # Explicit mode selection
        optimizer = OptimizerFactory.create(engine="whisperx")
        optimizer = OptimizerFactory.create(engine="heuristic")
        optimizer = OptimizerFactory.create(engine="auto")

    Configuration:
        Set OPTIMIZER_ENGINE environment variable:
            OPTIMIZER_ENGINE=auto    # Prefer WhisperX, fallback to Heuristic
            OPTIMIZER_ENGINE=whisperx  # Force WhisperX (with fallback)
            OPTIMIZER_ENGINE=heuristic  # Force Heuristic
    """

    @staticmethod
    def create(engine: str = None) -> TimestampOptimizer:
        """
        Create optimizer instance based on engine configuration.

        Args:
            engine: Optimizer engine to use. Valid values:
                    - "whisperx": Try WhisperX, fallback to Heuristic
                    - "heuristic": Always use HeuristicOptimizer
                    - "auto": Prefer WhisperX, fallback to Heuristic (default)
                    - None: Read from settings.OPTIMIZER_ENGINE

        Returns:
            TimestampOptimizer instance (WhisperXOptimizer or HeuristicOptimizer)

        Raises:
            ValueError: If engine is not one of: whisperx, heuristic, auto

        Examples:
            >>> optimizer = OptimizerFactory.create(engine="auto")
            >>> isinstance(optimizer, TimestampOptimizer)
            True

            >>> # WhisperX not available, auto-selects Heuristic
            >>> optimizer = OptimizerFactory.create(engine="auto")
            >>> isinstance(optimizer, HeuristicOptimizer)
            True
        """
        # Read from settings if engine not explicitly provided
        if engine is None:
            from app.config import settings
            engine = settings.OPTIMIZER_ENGINE

        # Mode: whisperx (try WhisperX, fallback to Heuristic)
        if engine == "whisperx":
            if WhisperXOptimizer.is_available():
                logger.info("Creating WhisperXOptimizer (engine=whisperx)")
                return WhisperXOptimizer()
            else:
                logger.warning(
                    "WhisperX dependencies unavailable (whisperx or pyannote.audio missing). "
                    "Falling back to HeuristicOptimizer."
                )
                return HeuristicOptimizer()

        # Mode: heuristic (always use Heuristic)
        elif engine == "heuristic":
            logger.info("Creating HeuristicOptimizer (engine=heuristic)")
            return HeuristicOptimizer()

        # Mode: auto (prefer WhisperX, fallback to Heuristic)
        elif engine == "auto":
            if WhisperXOptimizer.is_available():
                logger.info("Auto-selecting WhisperXOptimizer (WhisperX available)")
                return WhisperXOptimizer()
            else:
                logger.info(
                    "Auto-selecting HeuristicOptimizer (WhisperX unavailable). "
                    "Install whisperx and pyannote.audio for improved optimization."
                )
                return HeuristicOptimizer()

        # Invalid engine value
        else:
            raise ValueError(
                f"Unknown optimizer engine: '{engine}'. "
                f"Valid engines: 'whisperx', 'heuristic', 'auto'"
            )
