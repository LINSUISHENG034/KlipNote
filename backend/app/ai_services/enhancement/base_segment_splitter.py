from __future__ import annotations

"""
Base interface for model-agnostic segment splitting components (Story 4.4).

Segment splitters take EnhancedSegment payloads emitted by upstream enhancement
components (TimestampRefiner, VAD, etc.) and return a new list of segments that
preserve timing + metadata guarantees. Concrete implementations provide the
actual splitting/merging strategy while this base enforces telemetry and
availability hooks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.ai_services.schema import EnhancedSegment

SegmentList = List[EnhancedSegment]


class BaseSegmentSplitter(ABC):
    """Shared interface for all SegmentSplitter implementations."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {}

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True if optional dependencies (if any) exist in runtime."""

    @abstractmethod
    def split(self, segments: SegmentList, **kwargs: Any) -> SegmentList:
        """
        Split or merge incoming segments.

        Implementations should avoid mutating ``segments`` in-place. Instead,
        return a brand new list that satisfies the EnhancedSegment contract
        including timing metadata.
        """

    def get_metrics(self) -> Dict[str, Any]:
        """Expose telemetry for logging and downstream validation."""
        return dict(self._metrics)

    def _reset_metrics(self) -> None:
        """Convenience helper for subclasses prior to processing."""
        self._metrics = {}
