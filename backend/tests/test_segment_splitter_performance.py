from __future__ import annotations

import time

from app.ai_services.enhancement.segment_splitter import SegmentSplitter
from app.ai_services.schema import EnhancedSegment


def test_performance_500_segments_under_target() -> None:
    segments = [
        {
            "start": float(i),
            "end": float(i) + 2.0,
            "text": "你好世界" * 5,
            "chars": [],
            "words": [],
            "enhancements_applied": [],
        }
        for i in range(500)
    ]
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)

    start = time.perf_counter()
    result = splitter.split(segments)
    elapsed = time.perf_counter() - start

    assert len(result) == 500
    assert elapsed < 2.0  # well under 3 minute requirement
    assert splitter.get_metrics()["compliance_ratio"] >= 0.95
