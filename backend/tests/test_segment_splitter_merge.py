from __future__ import annotations

from typing import List

import pytest

from app.ai_services.enhancement.segment_splitter import SegmentSplitter
from app.ai_services.schema import CharTiming, EnhancedSegment


def _build_short_segment(text: str, start: float, duration: float) -> EnhancedSegment:
    chars: List[CharTiming] = []
    cursor = start
    step = duration / max(len(text), 1)
    for ch in text:
        chars.append({"char": ch, "start": cursor, "end": cursor + step})
        cursor += step
    return {
        "start": start,
        "end": start + duration,
        "text": text,
        "chars": chars,
        "words": [],
        "enhancements_applied": [],
    }


def test_merge_short_segments_when_safe() -> None:
    seg1 = _build_short_segment("短", start=0.0, duration=0.8)
    seg2 = _build_short_segment("句", start=0.8, duration=0.9)
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)

    result = splitter.split([seg1, seg2])

    assert len(result) == 1
    merged = result[0]
    assert merged["text"].replace(" ", "") == "短句"
    assert merged["start"] == pytest.approx(seg1["start"])
    assert merged["end"] - merged["start"] == pytest.approx(
        (seg1["end"] - seg1["start"]) + (seg2["end"] - seg2["start"])
    )
    assert "segment_split" in merged["enhancements_applied"]


def test_no_merge_when_exceeds_duration() -> None:
    seg1 = _build_short_segment("短", start=0.0, duration=0.8)
    seg2 = _build_short_segment("长" * 250, start=0.8, duration=6.5)
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)

    result = splitter.split([seg1, seg2])

    # Combined chars exceed max_chars, so no merge
    assert len(result) == 2
    assert all("segment_split" in seg["enhancements_applied"] for seg in result)
