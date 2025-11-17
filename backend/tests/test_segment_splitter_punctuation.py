from __future__ import annotations

from typing import List, Tuple

from app.ai_services.enhancement.segment_splitter import SegmentSplitter
from app.ai_services.schema import CharTiming, EnhancedSegment, WordTiming


def _build_segment(text: str, start: float = 0.0, end: float = 10.0) -> EnhancedSegment:
    duration = (end - start) / max(len(text), 1)
    chars: List[CharTiming] = []
    cursor = start
    for ch in text:
        chars.append({"char": ch, "start": cursor, "end": cursor + duration})
        cursor += duration
    return {
        "start": start,
        "end": end,
        "text": text,
        "chars": chars,
        "words": [],
        "enhancements_applied": [],
    }

def _build_segment_with_words(
    text: str,
    *,
    start: float = 0.0,
    end: float = 12.0,
) -> EnhancedSegment:
    words = []
    cursor = start
    increment = (end - start) / max(len(text.split()), 1)
    for word in text.split():
        words.append({"word": word, "start": cursor, "end": cursor + increment})
        cursor += increment
    chars, _ = _chars_with_duration(text, start, (end - start) / max(len(text), 1))
    return {
        "start": start,
        "end": end,
        "text": text,
        "chars": chars,
        "words": words,
        "enhancements_applied": [],
    }

def _chars_with_duration(
    text: str,
    start: float,
    step: float,
) -> Tuple[List[CharTiming], float]:
    cursor = start
    chars: List[CharTiming] = []
    for ch in text:
        chars.append({"char": ch, "start": cursor, "end": cursor + step})
        cursor += step
    return chars, cursor


def test_split_long_segment_at_punctuation() -> None:
    segment = _build_segment("你好，我很好。你呢？", start=0.0, end=10.0)
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)

    result = splitter.split([segment])

    assert len(result) >= 2
    assert result[0]["text"].endswith("。") or result[0]["text"].endswith("，")
    assert splitter.get_metrics()["split_operations"] >= 1


def test_no_split_when_duration_within_limits() -> None:
    segment = _build_segment("你好", start=0.0, end=5.0)
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)

    result = splitter.split([segment])

    assert len(result) == 1
    assert result[0]["text"] == "你好"
    assert "segment_split" in result[0]["enhancements_applied"]


def test_char_timings_preserved_after_split() -> None:
    text = "你好世界。欢迎你"
    chars, total = _chars_with_duration(text, 0.0, 0.5)
    segment: EnhancedSegment = {
        "start": 0.0,
        "end": total,
        "text": text,
        "chars": chars,
        "words": [],
        "enhancements_applied": [],
    }

    splitter = SegmentSplitter(max_duration=5.0, max_chars=5)
    result = splitter.split([segment])

    assert len(result) >= 2
    first, second = result[0], result[-1]
    assert len("".join(ch["char"] for ch in first["chars"])) == len(first["text"])
    assert first["start"] == first["chars"][0]["start"]
    assert first["end"] == first["chars"][-1]["end"]
    assert second["end"] == segment["end"]


def test_word_timings_used_when_chars_missing() -> None:
    text = "hello world。how are you？"
    segment = _build_segment_with_words(text, start=0.0, end=15.0)
    segment["chars"] = []  # simulate missing char timings

    splitter = SegmentSplitter(max_duration=4.0, max_chars=200)
    result = splitter.split([segment])

    assert len(result) >= 2
    assert result[0]["start"] == result[0]["words"][0]["start"]
    assert result[-1]["end"] == result[-1]["words"][-1]["end"]


def test_pause_fallback_splits_when_no_punctuation() -> None:
    text = "helloworld"  # no punctuation
    segment = _build_segment(text, start=0.0, end=10.0)
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)

    result = splitter.split([segment], pause_boundaries=[5.0])

    assert len(result) == 2
    assert "segment_split" in result[0]["enhancements_applied"]
