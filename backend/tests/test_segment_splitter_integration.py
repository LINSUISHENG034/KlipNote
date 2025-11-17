from __future__ import annotations

import pytest
from pathlib import Path
from typing import List

from app.ai_services.enhancement.segment_splitter import SegmentSplitter
from app.ai_services.enhancement.timestamp_refiner import TimestampRefiner
from app.ai_services.schema import EnhancedSegment


def _make_segment(text: str, start: float, end: float) -> EnhancedSegment:
    return {
        "start": start,
        "end": end,
        "text": text,
        "chars": [],
        "words": [],
        "enhancements_applied": [],
    }


def test_integration_mixed_segments_compliance() -> None:
    # Mix of long, short, and compliant segments with punctuation.
    segments: List[EnhancedSegment] = [
        _make_segment("你好，我很好。你呢？", 0.0, 12.0),  # will split
        _make_segment("短", 12.0, 12.8),  # short, will merge
        _make_segment("句", 12.8, 13.6),  # short, will merge
        _make_segment("正常长度句子", 13.6, 18.0),  # already compliant
    ]

    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)
    result = splitter.split(segments)

    assert len(result) >= 3
    assert splitter.get_metrics()["compliance_ratio"] >= 0.95
    for seg in result:
        assert len((seg.get("text") or "")) <= splitter.max_chars
        duration = float(seg["end"]) - float(seg["start"])
        assert 0.5 <= duration <= splitter.max_duration


# ============================================================================
# Subtask 9.3: End-to-end pipeline test (Refiner → Splitter)
# ============================================================================

# Test fixture paths (relative to project root)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"
CHINESE_AUDIO = FIXTURES_DIR / "mandarin-test.mp3"
ENGLISH_AUDIO = FIXTURES_DIR / "en_columbia.wma"


@pytest.mark.integration
@pytest.mark.slow
def test_end_to_end_refiner_splitter_pipeline():
    """
    Subtask 9.3: Test complete pipeline from TimestampRefiner to SegmentSplitter.

    Validates:
    - TimestampRefiner produces EnhancedSegment with char/word timing arrays
    - SegmentSplitter accepts refined segments with timing metadata
    - Pipeline preserves and correctly distributes char/word timing arrays
    - All metadata (enhancements_applied) tracked correctly through pipeline
    - Constraint compliance maintained after splitting

    This ensures the SegmentSplitter component integrates correctly with
    upstream enhancement components (Story 4.3 TimestampRefiner).
    """
    if not CHINESE_AUDIO.exists():
        pytest.skip(f"Chinese test audio not found: {CHINESE_AUDIO}")

    # Step 1: Create test segments (simulating BELLE-2 output)
    print("\n1. Creating test segments (simulating BELLE-2 output)")
    initial_segments: List[EnhancedSegment] = [
        {
            "start": 0.0,
            "end": 10.0,  # Long segment, will be split
            "text": "这是一个很长的测试文件。用于验证中文字符级时间戳的准确性。我们需要确保分割后仍然保持时间信息。",
            "source_model": "belle2",
            "enhancements_applied": [],
        },
        {
            "start": 10.0,
            "end": 10.8,  # Short segment (will merge with next)
            "text": "短",
            "source_model": "belle2",
            "enhancements_applied": [],
        },
        {
            "start": 10.8,
            "end": 11.6,  # Short segment (will merge with previous)
            "text": "句",
            "source_model": "belle2",
            "enhancements_applied": [],
        },
        {
            "start": 11.6,
            "end": 15.0,  # Normal compliant segment
            "text": "这是一个正常长度的句子",
            "source_model": "belle2",
            "enhancements_applied": [],
        },
    ]
    print(f"   ✓ Created {len(initial_segments)} test segments")

    # Step 2: Refine timestamps with TimestampRefiner
    refiner = TimestampRefiner()
    if not refiner.is_available():
        pytest.skip("TimestampRefiner dependencies not available")

    print("2. Refining timestamps with TimestampRefiner")
    refined_segments = refiner.refine(
        segments=initial_segments,
        audio_path=str(CHINESE_AUDIO),
        language="zh"
    )

    assert len(refined_segments) == len(initial_segments), \
        "Refiner should preserve segment count"
    print(f"   ✓ Refined {len(refined_segments)} segments with char/word timing")

    # Validate refiner output has timing arrays
    for seg in refined_segments:
        assert "timestamp_refine" in seg.get("enhancements_applied", []), \
            "Refiner should add timestamp_refine tag"
        assert "chars" in seg or "words" in seg, \
            "Refiner should populate char or word timing arrays"

    # Step 3: Split segments with SegmentSplitter
    print("3. Splitting segments with SegmentSplitter")
    splitter = SegmentSplitter(max_duration=7.0, max_chars=200)
    split_segments = splitter.split(refined_segments)

    print(f"   ✓ Split into {len(split_segments)} segments")
    print(f"   ✓ Compliance ratio: {splitter.get_metrics()['compliance_ratio']:.2%}")

    # Step 4: Validate pipeline output
    print("4. Validating pipeline output")

    # All segments should meet constraints
    assert splitter.get_metrics()["compliance_ratio"] >= 0.95, \
        "95% of segments should meet constraints after splitting"

    for idx, seg in enumerate(split_segments):
        # EnhancedSegment structure preserved
        assert "start" in seg and "end" in seg and "text" in seg, \
            f"Segment {idx} missing required fields"

        # Constraint compliance
        duration = float(seg["end"]) - float(seg["start"])
        assert 1.0 <= duration <= 7.0, \
            f"Segment {idx} duration {duration:.2f}s outside 1-7s constraint"
        assert len(seg.get("text", "")) <= 200, \
            f"Segment {idx} text length {len(seg['text'])} exceeds 200 char limit"

        # Timing arrays preserved (at least one should exist)
        assert "chars" in seg or "words" in seg, \
            f"Segment {idx} lost timing arrays during split"

        # If chars exist, validate integrity
        if "chars" in seg and len(seg["chars"]) > 0:
            chars = seg["chars"]
            # Character timing should be within segment bounds
            assert chars[0]["start"] >= seg["start"] - 0.01, \
                f"Segment {idx} char timing starts before segment"
            assert chars[-1]["end"] <= seg["end"] + 0.01, \
                f"Segment {idx} char timing ends after segment"

            # Sequential progression
            for i in range(len(chars) - 1):
                assert chars[i]["end"] <= chars[i + 1]["start"] + 0.01, \
                    f"Segment {idx} char timing overlap at index {i}"

        # If words exist, validate integrity
        if "words" in seg and len(seg["words"]) > 0:
            words = seg["words"]
            # Word timing should be within segment bounds
            assert words[0]["start"] >= seg["start"] - 0.01, \
                f"Segment {idx} word timing starts before segment"
            assert words[-1]["end"] <= seg["end"] + 0.01, \
                f"Segment {idx} word timing ends after segment"

        # Metadata chain preserved
        assert seg.get("source_model") == "belle2", \
            f"Segment {idx} lost source_model metadata"

        # Enhancement tracking through pipeline
        enhancements = seg.get("enhancements_applied", [])
        assert "timestamp_refine" in enhancements, \
            f"Segment {idx} missing timestamp_refine enhancement from Refiner"
        assert "segment_split" in enhancements, \
            f"Segment {idx} missing segment_split enhancement from Splitter"

    print(f"   ✓ All {len(split_segments)} segments validated")
    print(f"   ✓ Timing array integrity preserved through pipeline")
    print(f"   ✓ Metadata chain complete: BELLE-2 → Refiner → Splitter")
    print("\n✓ End-to-end pipeline test passed (Subtask 9.3)")
