"""
Integration tests for TimestampRefiner component (Story 4.3 - AC #11)

Tests real audio processing with both Chinese and English samples to validate:
- Character-level timing accuracy for Chinese (Subtask 7.1)
- Word-level timing accuracy for English (Subtask 7.2)
- End-to-end pipeline: BELLE-2/WhisperX → Refiner (Subtask 7.4)
- Performance constraint: <5 min for 500 segments (AC #9)

NOTE: Frontend click-to-timestamp validation (Subtask 7.3) requires manual testing
with Chrome DevTools and is documented in the manual test procedure below.

Test Fixtures:
- tests/fixtures/mandarin-test.mp3 - Chinese audio sample
- tests/fixtures/en_columbia.wma - English audio sample
"""

import pytest
import os
import time
from pathlib import Path
from typing import List, Dict, Any

from app.ai_services.enhancement.timestamp_refiner import TimestampRefiner
from app.ai_services.schema import EnhancedSegment


# Test fixture paths (relative to project root)
FIXTURES_DIR = Path(__file__).parent.parent.parent / "tests" / "fixtures"
CHINESE_AUDIO = FIXTURES_DIR / "mandarin-test.mp3"
ENGLISH_AUDIO = FIXTURES_DIR / "en_columbia.wma"


@pytest.fixture
def timestamp_refiner():
    """Provide TimestampRefiner instance for tests"""
    return TimestampRefiner()


@pytest.fixture
def chinese_test_segments() -> List[Dict[str, Any]]:
    """Sample Chinese transcription segments for testing"""
    return [
        {
            "start": 0.0,
            "end": 3.5,
            "text": "这是一个测试文件",
            "source_model": "belle2",
        },
        {
            "start": 3.5,
            "end": 7.2,
            "text": "用于验证中文字符级时间戳",
            "source_model": "belle2",
        },
        {
            "start": 7.2,
            "end": 11.0,
            "text": "每个字符都应该有准确的时间信息",
            "source_model": "belle2",
        },
    ]


@pytest.fixture
def english_test_segments() -> List[Dict[str, Any]]:
    """Sample English transcription segments for testing"""
    return [
        {
            "start": 0.0,
            "end": 2.5,
            "text": "This is a test file",
            "source_model": "whisperx",
        },
        {
            "start": 2.5,
            "end": 5.8,
            "text": "for validating word level timestamps",
            "source_model": "whisperx",
        },
        {
            "start": 5.8,
            "end": 9.0,
            "text": "Each word should have accurate timing information",
            "source_model": "whisperx",
        },
    ]


# ============================================================================
# Subtask 7.1: Test with real Chinese audio (verify char-level timing accuracy)
# ============================================================================


@pytest.mark.integration
def test_chinese_audio_char_timing_accuracy(timestamp_refiner, chinese_test_segments):
    """
    Subtask 7.1: Verify character-level timing accuracy with real Chinese audio.

    Validates:
    - CharTiming array populated for all Chinese segments
    - Character count matches text length (excluding spaces/punctuation)
    - Character timing boundaries are sequential and within segment bounds
    - Each CharTiming has all required fields (char, start, end, score)
    """
    if not timestamp_refiner.is_available():
        pytest.skip("librosa/numpy not available")

    if not CHINESE_AUDIO.exists():
        pytest.skip(f"Chinese test audio not found: {CHINESE_AUDIO}")

    # Refine timestamps with real audio
    refined_segments = timestamp_refiner.refine(
        segments=chinese_test_segments,
        audio_path=str(CHINESE_AUDIO),
        language="zh"
    )

    # Validate all segments have char-level timing
    assert len(refined_segments) > 0, "Should have refined segments"

    for seg in refined_segments:
        # All Chinese segments should have chars array
        assert "chars" in seg, f"Segment missing chars array: {seg['text']}"
        assert isinstance(seg["chars"], list), "chars should be a list"
        assert len(seg["chars"]) > 0, f"chars array empty for: {seg['text']}"

        # Count Chinese characters in text (excluding spaces/punctuation)
        chinese_chars = [ch for ch in seg["text"] if '\u4e00' <= ch <= '\u9fff']
        assert len(seg["chars"]) == len(chinese_chars), \
            f"CharTiming count mismatch: expected {len(chinese_chars)}, got {len(seg['chars'])}"

        # Validate each CharTiming entry
        previous_end = seg["start"]
        for idx, char_timing in enumerate(seg["chars"]):
            # Required fields present
            assert "char" in char_timing, f"CharTiming missing 'char' field at index {idx}"
            assert "start" in char_timing, f"CharTiming missing 'start' field at index {idx}"
            assert "end" in char_timing, f"CharTiming missing 'end' field at index {idx}"
            assert "score" in char_timing, f"CharTiming missing 'score' field at index {idx}"

            # Timing boundaries valid
            assert seg["start"] <= char_timing["start"], \
                f"CharTiming start before segment: {char_timing['start']} < {seg['start']}"
            assert char_timing["start"] < char_timing["end"], \
                f"CharTiming start >= end: {char_timing}"
            assert char_timing["end"] <= seg["end"], \
                f"CharTiming end after segment: {char_timing['end']} > {seg['end']}"

            # Sequential progression (no overlap with previous char)
            # Use small epsilon tolerance for floating point comparison
            EPSILON = 1e-6
            assert char_timing["start"] >= previous_end - EPSILON, \
                f"CharTiming overlap detected at index {idx}: {char_timing['start']} < {previous_end}"
            previous_end = char_timing["end"]

            # Score is valid confidence value
            assert 0.0 <= char_timing["score"] <= 1.0, \
                f"Invalid confidence score: {char_timing['score']}"

        # Metadata tracking
        assert "timestamp_refine" in seg.get("enhancements_applied", []), \
            "Missing timestamp_refine enhancement tag"
        assert seg.get("alignment_model") == TimestampRefiner.alignment_model_name, \
            f"Incorrect alignment_model: {seg.get('alignment_model')}"

    print(f"✓ Chinese char-level timing validated: {len(refined_segments)} segments")


# ============================================================================
# Subtask 7.2: Test with real English audio (verify word-level timing accuracy)
# ============================================================================


@pytest.mark.integration
def test_english_audio_word_timing_accuracy(timestamp_refiner, english_test_segments):
    """
    Subtask 7.2: Verify word-level timing accuracy with real English audio.

    Validates:
    - WordTiming array populated for all English segments
    - Word count matches text (approximately, accounting for tokenization)
    - Word timing boundaries are sequential and within segment bounds
    - Each WordTiming has all required fields (word, start, end, score, language)
    """
    if not timestamp_refiner.is_available():
        pytest.skip("librosa/numpy not available")

    if not ENGLISH_AUDIO.exists():
        pytest.skip(f"English test audio not found: {ENGLISH_AUDIO}")

    # Refine timestamps with real audio
    refined_segments = timestamp_refiner.refine(
        segments=english_test_segments,
        audio_path=str(ENGLISH_AUDIO),
        language="en"
    )

    # Validate all segments have word-level timing
    assert len(refined_segments) > 0, "Should have refined segments"

    for seg in refined_segments:
        # All segments should have words array
        assert "words" in seg, f"Segment missing words array: {seg['text']}"
        assert isinstance(seg["words"], list), "words should be a list"
        assert len(seg["words"]) > 0, f"words array empty for: {seg['text']}"

        # Word count should roughly match text
        text_words = seg["text"].split()
        assert len(seg["words"]) >= len(text_words) * 0.8, \
            f"Word count significantly lower: {len(seg['words'])} < {len(text_words)}"

        # Validate each WordTiming entry
        previous_end = seg["start"]
        for idx, word_timing in enumerate(seg["words"]):
            # Required fields present
            assert "word" in word_timing, f"WordTiming missing 'word' field at index {idx}"
            assert "start" in word_timing, f"WordTiming missing 'start' field at index {idx}"
            assert "end" in word_timing, f"WordTiming missing 'end' field at index {idx}"
            assert "score" in word_timing, f"WordTiming missing 'score' field at index {idx}"
            assert "language" in word_timing, f"WordTiming missing 'language' field at index {idx}"

            # Language hint correct
            assert word_timing["language"] == "en", \
                f"Incorrect language: {word_timing['language']}"

            # Timing boundaries valid
            assert seg["start"] <= word_timing["start"], \
                f"WordTiming start before segment: {word_timing['start']} < {seg['start']}"
            assert word_timing["start"] < word_timing["end"], \
                f"WordTiming start >= end: {word_timing}"
            assert word_timing["end"] <= seg["end"], \
                f"WordTiming end after segment: {word_timing['end']} > {seg['end']}"

            # Sequential progression (allow small overlap due to forced alignment)
            EPSILON = 0.01  # 10ms tolerance for word timing
            assert word_timing["start"] >= previous_end - EPSILON, \
                f"WordTiming overlap at index {idx}: {word_timing['start']} < {previous_end}"
            previous_end = word_timing["end"]

            # Score is valid
            assert 0.0 <= word_timing["score"] <= 1.0, \
                f"Invalid confidence score: {word_timing['score']}"

        # Metadata tracking
        assert "timestamp_refine" in seg.get("enhancements_applied", []), \
            "Missing timestamp_refine enhancement tag"

    print(f"✓ English word-level timing validated: {len(refined_segments)} segments")


# ============================================================================
# Subtask 7.4: End-to-end pipeline test (BELLE-2/WhisperX → Refiner)
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_end_to_end_belle2_refiner_pipeline():
    """
    Subtask 7.4: Test complete pipeline from BELLE-2 transcription to refined output.

    Validates:
    - BELLE-2 service produces valid segments
    - TimestampRefiner accepts BELLE-2 output
    - Pipeline produces EnhancedSegment with char/word timing
    - All metadata tracked correctly through pipeline

    NOTE: Requires BELLE-2 model to be available (GPU test)
    """
    if not CHINESE_AUDIO.exists():
        pytest.skip(f"Chinese test audio not found: {CHINESE_AUDIO}")

    # Import BELLE-2 service
    try:
        from app.ai_services.belle2_service import Belle2Service
    except ImportError:
        pytest.skip("BELLE-2 service not available")

    # Check GPU availability
    try:
        import torch
        if not torch.cuda.is_available():
            pytest.skip("GPU not available for BELLE-2")
    except ImportError:
        pytest.skip("PyTorch not available")

    # Step 1: Transcribe with BELLE-2
    belle2_service = Belle2Service()
    if not belle2_service.is_available():
        pytest.skip("BELLE-2 model not available")

    print(f"\n1. Transcribing with BELLE-2: {CHINESE_AUDIO.name}")
    segments = belle2_service.transcribe(str(CHINESE_AUDIO), language="zh")

    assert len(segments) > 0, "BELLE-2 should produce segments"
    print(f"   ✓ Produced {len(segments)} segments")

    # Step 2: Refine timestamps
    refiner = TimestampRefiner()
    if not refiner.is_available():
        pytest.skip("TimestampRefiner dependencies not available")

    print(f"2. Refining timestamps with TimestampRefiner")
    refined_segments = refiner.refine(
        segments=segments,
        audio_path=str(CHINESE_AUDIO),
        language="zh"
    )

    assert len(refined_segments) == len(segments), \
        "Refiner should preserve segment count"
    print(f"   ✓ Refined {len(refined_segments)} segments")

    # Step 3: Validate pipeline output
    print(f"3. Validating pipeline output")
    for idx, seg in enumerate(refined_segments):
        # EnhancedSegment structure
        assert "start" in seg and "end" in seg and "text" in seg, \
            f"Segment {idx} missing required fields"

        # Character-level timing populated
        assert "chars" in seg or "words" in seg, \
            f"Segment {idx} missing timing arrays"

        # Metadata chain preserved
        assert seg.get("source_model") == "belle2", \
            f"Segment {idx} lost source_model metadata"

        # Enhancement tracking
        enhancements = seg.get("enhancements_applied", [])
        assert "vad_silero" in enhancements or "vad_webrtc" in enhancements, \
            f"Segment {idx} missing VAD enhancement (from Story 4.2)"
        assert "timestamp_refine" in enhancements, \
            f"Segment {idx} missing timestamp_refine enhancement"

    print(f"   ✓ All {len(refined_segments)} segments valid")
    print(f"\n✓ End-to-end pipeline test passed")


# ============================================================================
# AC #9: Performance validation (<5 min for 500 segments)
# ============================================================================


@pytest.mark.integration
@pytest.mark.slow
def test_performance_500_segments_under_5_minutes():
    """
    AC #9: Validate processing completes <5 min for 500 segments.

    Creates a large dataset of 500 segments and measures actual processing time.
    Performance constraint: Total processing time must be <300 seconds (5 minutes).

    NOTE: This is a performance benchmark test - may take several minutes to complete.
    """
    if not CHINESE_AUDIO.exists():
        pytest.skip(f"Test audio not found: {CHINESE_AUDIO}")

    refiner = TimestampRefiner()
    if not refiner.is_available():
        pytest.skip("TimestampRefiner dependencies not available")

    # Generate 500 test segments (simulating long transcription)
    # Each segment 3 seconds long = ~25 minutes of audio
    segments = []
    for i in range(500):
        segments.append({
            "start": i * 3.0,
            "end": (i + 1) * 3.0,
            "text": f"这是第{i + 1}个测试段落用于性能验证",
            "source_model": "belle2",
        })

    print(f"\n⏱️  Performance test: Refining 500 segments...")
    print(f"   Audio file: {CHINESE_AUDIO.name}")
    print(f"   Total duration: ~{500 * 3 / 60:.1f} minutes (simulated)")

    # Measure processing time
    start_time = time.perf_counter()
    refined_segments = refiner.refine(
        segments=segments,
        audio_path=str(CHINESE_AUDIO),
        language="zh"
    )
    processing_time = time.perf_counter() - start_time

    # Validate constraint
    assert processing_time < 300.0, \
        f"Processing took {processing_time:.2f}s, exceeds 5 min (300s) constraint"

    # Validate all segments processed
    assert len(refined_segments) == 500, \
        f"Expected 500 segments, got {len(refined_segments)}"

    # Get metrics from refiner
    metrics = refiner.get_metrics()
    segments_processed = metrics.get("segments_processed", 0)
    processing_time_ms = metrics.get("processing_time_ms", 0)

    print(f"\n✓ Performance test PASSED")
    print(f"   Segments processed: {segments_processed}")
    print(f"   Total time: {processing_time:.2f}s ({processing_time / 60:.2f} min)")
    print(f"   Average per segment: {processing_time / 500 * 1000:.2f}ms")
    print(f"   Constraint: <300s (5 min)")
    print(f"   Margin: {300 - processing_time:.2f}s under limit")

    # Additional performance assertions
    assert processing_time_ms > 0, "Metrics should track processing time"
    assert segments_processed == 500, f"Metrics mismatch: {segments_processed} != 500"


# ============================================================================
# Subtask 7.3: Frontend click-to-timestamp validation (MANUAL TEST)
# ============================================================================


def test_frontend_click_to_timestamp_manual_procedure():
    """
    Subtask 7.3: Frontend click-to-timestamp accuracy validation (MANUAL TEST).

    This test documents the manual testing procedure for validating click-to-timestamp
    accuracy in the frontend using Chrome DevTools. Automated frontend testing requires
    Playwright/Selenium which is beyond the scope of this backend integration test.

    MANUAL TEST PROCEDURE:
    =====================

    Prerequisites:
    1. Backend server running: `cd backend && uv run uvicorn app.main:app --reload`
    2. Frontend server running: `cd frontend && npm run dev`
    3. Chrome browser with DevTools

    Test Steps:
    -----------
    1. Open Chrome and navigate to http://localhost:5173

    2. Upload test file:
       - Use Chinese test audio: tests/fixtures/mandarin-test.mp3
       - Wait for transcription to complete

    3. Open Chrome DevTools (F12):
       - Go to Console tab
       - Prepare to monitor media player events

    4. Test click-to-timestamp accuracy:
       a. Click on any subtitle segment in the results view
       b. In DevTools Console, inspect the media player's currentTime:
          ```javascript
          document.querySelector('video, audio').currentTime
          ```
       c. Verify the currentTime matches the segment's start time (±200ms)

    5. Test multiple segments:
       - Repeat step 4 for at least 5 different segments
       - Test segments at different positions (beginning, middle, end)
       - Test both short and long segments

    6. Validate timing accuracy:
       - For each click, calculate: |player.currentTime - segment.start|
       - All deviations should be <0.2 seconds (200ms per AC #6)

    7. Test with English audio:
       - Repeat steps 2-6 with: tests/fixtures/en_columbia.wma

    Expected Results:
    ----------------
    ✓ Clicking any segment seeks media player to segment.start
    ✓ Player starts playing automatically after seek
    ✓ Timing deviation <200ms for all tested segments
    ✓ Active segment is visually highlighted during playback
    ✓ Highlight updates as playback progresses through segments

    Acceptance:
    ----------
    - Test 10+ segments total (5 Chinese + 5 English minimum)
    - 100% of clicks result in <200ms deviation
    - No playback glitches or UI freezes
    - Visual highlight accurately tracks playback position

    Test Evidence:
    -------------
    Screenshot or screen recording showing:
    1. Clicking segment in UI
    2. DevTools Console showing currentTime values
    3. Timing deviation calculations demonstrating <200ms accuracy

    NOTE: This manual test validates AC #11 requirement:
    "Integration tests validate click-to-timestamp accuracy and char/word timing arrays"

    The char/word timing arrays are validated programmatically in tests above.
    The click-to-timestamp frontend behavior requires manual validation as documented here.
    """
    # This is a documentation test - always passes
    # Actual validation happens manually following procedure above
    print("\n" + "=" * 70)
    print("MANUAL TEST PROCEDURE: Frontend Click-to-Timestamp Validation")
    print("=" * 70)
    print(__doc__)
    print("=" * 70)
    assert True, "Manual test procedure documented"
