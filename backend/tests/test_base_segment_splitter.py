from __future__ import annotations

from typing import Any, List

import pytest

from app.ai_services.enhancement.base_segment_splitter import (
    BaseSegmentSplitter,
    SegmentList,
)
from app.ai_services.schema import EnhancedSegment


class _DummySplitter(BaseSegmentSplitter):
    """Concrete splitter used for exercising the base contract."""

    @classmethod
    def is_available(cls) -> bool:
        return True

    def split(self, segments: SegmentList, **kwargs: Any) -> SegmentList:
        self._reset_metrics()
        self._metrics["segments_in"] = len(segments)
        return list(segments)


@pytest.fixture()
def sample_segments() -> List[EnhancedSegment]:
    return [
        {
            "start": 0.0,
            "end": 1.0,
            "text": "你好",
            "words": [],
            "chars": [],
            "enhancements_applied": [],
        }
    ]


def test_get_metrics_returns_copy(sample_segments: SegmentList) -> None:
    splitter = _DummySplitter()
    splitter.split(sample_segments)

    metrics = splitter.get_metrics()
    metrics["segments_in"] = 999

    assert splitter.get_metrics()["segments_in"] == 1


def test_reset_metrics_clears_previous_values(sample_segments: SegmentList) -> None:
    splitter = _DummySplitter()
    splitter.split(sample_segments)
    assert splitter.get_metrics() == {"segments_in": 1}

    splitter._reset_metrics()
    assert splitter.get_metrics() == {}
