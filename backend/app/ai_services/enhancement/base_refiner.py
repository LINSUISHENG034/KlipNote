"""Abstract contract for timestamp refinement components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, MutableMapping, Sequence

from app.ai_services.schema import EnhancedSegment


SegmentCollection = Sequence[MutableMapping[str, Any]]


class BaseRefiner(ABC):
    """Shared interface for refinement components (Story 4.3)."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {}

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if required dependencies are present."""

    @abstractmethod
    def refine(
        self,
        segments: SegmentCollection,
        audio_path: str,
        **kwargs: Any,
    ) -> List[EnhancedSegment]:
        """
        Refine incoming segments and return EnhancedSegment payloads.

        Implementations should avoid mutating the original input list to
        preserve upstream telemetry. Returned segments MUST satisfy the
        EnhancedSegment contract (char/word timing arrays populated when
        available).
        """

    def get_metrics(self) -> Dict[str, Any]:
        """Expose basic processing stats for telemetry/logging."""
        return dict(self._metrics)

    def _reset_metrics(self) -> None:
        """Helper for subclasses to reset metrics prior to processing."""
        self._metrics = {}
