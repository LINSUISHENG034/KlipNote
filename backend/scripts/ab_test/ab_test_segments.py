#!/usr/bin/env python3
"""
Story 3.2c A/B Test: Segment Length Compliance

Compares segment length statistics and compliance with subtitle standards
(1-7 seconds, <200 characters) between BELLE-2 and WhisperX models.

Usage:
    python backend/scripts/ab_test_segments.py --test-dir tests/fixtures --model belle2 --output belle2_segments.json
    python backend/scripts/ab_test_segments.py --test-dir tests/fixtures --model whisperx --output whisperx_segments.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import transcription functions from ab_test_accuracy
from ab_test_accuracy import transcribe_belle2, transcribe_whisperx


def calculate_segment_stats(segments: List[Dict]) -> Dict[str, Any]:
    """
    Calculate comprehensive segment length statistics

    Args:
        segments: List of transcription segments

    Returns:
        Dict with duration and character count statistics
    """
    if not segments:
        return {
            "count": 0,
            "duration": {},
            "char_count": {},
            "compliance": {}
        }

    import numpy as np

    # Extract metrics
    durations = [seg["end"] - seg["start"] for seg in segments]
    char_counts = [len(seg["text"]) for seg in segments]

    # Duration statistics
    duration_stats = {
        "mean_s": float(np.mean(durations)),
        "median_s": float(np.median(durations)),
        "min_s": float(np.min(durations)),
        "max_s": float(np.max(durations)),
        "std_s": float(np.std(durations)),
        "p25_s": float(np.percentile(durations, 25)),
        "p75_s": float(np.percentile(durations, 75)),
        "p95_s": float(np.percentile(durations, 95))
    }

    # Character count statistics
    char_stats = {
        "mean": float(np.mean(char_counts)),
        "median": float(np.median(char_counts)),
        "min": int(np.min(char_counts)),
        "max": int(np.max(char_counts)),
        "std": float(np.std(char_counts)),
        "p95": float(np.percentile(char_counts, 95))
    }

    # Compliance with subtitle standards
    meets_duration = sum(1 for d in durations if 1.0 <= d <= 7.0)
    meets_char_limit = sum(1 for c in char_counts if c < 200)
    meets_both = sum(
        1 for seg in segments
        if 1.0 <= (seg["end"] - seg["start"]) <= 7.0 and len(seg["text"]) < 200
    )

    # Segments that are too long or too short
    too_short = sum(1 for d in durations if d < 1.0)
    too_long = sum(1 for d in durations if d > 7.0)
    too_many_chars = sum(1 for c in char_counts if c >= 200)

    compliance_stats = {
        "meets_1_7_seconds": meets_duration,
        "meets_1_7_seconds_pct": (meets_duration / len(segments)) * 100,
        "meets_under_200_chars": meets_char_limit,
        "meets_under_200_chars_pct": (meets_char_limit / len(segments)) * 100,
        "meets_both_constraints": meets_both,
        "meets_both_constraints_pct": (meets_both / len(segments)) * 100,
        "too_short_under_1s": too_short,
        "too_short_under_1s_pct": (too_short / len(segments)) * 100,
        "too_long_over_7s": too_long,
        "too_long_over_7s_pct": (too_long / len(segments)) * 100,
        "too_many_chars_over_200": too_many_chars,
        "too_many_chars_over_200_pct": (too_many_chars / len(segments)) * 100
    }

    return {
        "count": len(segments),
        "duration": duration_stats,
        "char_count": char_stats,
        "compliance": compliance_stats
    }


def analyze_segment_quality(segments: List[Dict]) -> Dict[str, Any]:
    """
    Analyze segment quality characteristics

    Returns:
        Dict with quality indicators
    """
    if not segments:
        return {}

    # Check for empty segments
    empty_segments = sum(1 for seg in segments if not seg["text"].strip())

    # Check for very long continuous speech (no natural breaks)
    long_segments = [seg for seg in segments if (seg["end"] - seg["start"]) > 15.0]

    # Check for extremely short segments (fragmentation)
    very_short = sum(1 for seg in segments if (seg["end"] - seg["start"]) < 0.5)

    return {
        "empty_segments": empty_segments,
        "very_long_segments_over_15s": len(long_segments),
        "very_short_segments_under_0.5s": very_short,
        "fragmentation_score": (very_short / len(segments)) * 100 if segments else 0
    }


def run_segment_test(
    test_dir: str,
    model: str,
    output: str,
    limit: int = None
) -> Dict[str, Any]:
    """
    Run segment length compliance test for specified model

    Args:
        test_dir: Directory containing test audio files
        model: "belle2" or "whisperx"
        output: Output JSON file path
        limit: Maximum number of files to test

    Returns:
        Test results dict
    """
    test_path = Path(test_dir)

    # Discover audio files
    audio_files = []
    for ext in ["*.mp3", "*.wav", "*.m4a", "*.flac"]:
        audio_files.extend(test_path.glob(ext))

    # Filter out corrupted test files
    audio_files = [f for f in audio_files if "corrupted" not in f.name]
    audio_files = sorted(audio_files)

    if limit:
        audio_files = audio_files[:limit]

    print(f"\n{'='*60}")
    print(f"A/B Test: Segment Length Compliance")
    print(f"Model: {model.upper()}")
    print(f"Test files: {len(audio_files)}")
    print(f"{'='*60}\n")

    # Select transcription function
    transcribe_func = transcribe_belle2 if model == "belle2" else transcribe_whisperx

    # Run tests
    results = []
    total_compliance_both = 0
    total_segments = 0

    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")

        # Transcribe
        result = transcribe_func(str(audio_file), language="zh")

        if not result["success"]:
            print(f"  ✗ Error: {result['error']}")
            results.append({
                "file": audio_file.name,
                "transcription": result,
                "segment_stats": None,
                "quality_analysis": None
            })
            continue

        # Calculate segment statistics
        segment_stats = calculate_segment_stats(result["segments"])
        quality_analysis = analyze_segment_quality(result["segments"])

        total_compliance_both += segment_stats["compliance"]["meets_both_constraints"]
        total_segments += segment_stats["count"]

        print(f"  ✓ Segments: {segment_stats['count']}")
        print(f"  📊 Mean duration: {segment_stats['duration']['mean_s']:.2f}s")
        print(f"  📊 Median duration: {segment_stats['duration']['median_s']:.2f}s")
        print(f"  ✅ Compliance (1-7s): {segment_stats['compliance']['meets_1_7_seconds_pct']:.1f}%")
        print(f"  ✅ Compliance (<200 chars): {segment_stats['compliance']['meets_under_200_chars_pct']:.1f}%")
        print(f"  ✅ Compliance (both): {segment_stats['compliance']['meets_both_constraints_pct']:.1f}%")

        if quality_analysis["very_long_segments_over_15s"] > 0:
            print(f"  ⚠ Very long segments (>15s): {quality_analysis['very_long_segments_over_15s']}")

        results.append({
            "file": audio_file.name,
            "transcription": {
                "segment_count": result["segment_count"],
                "transcription_time_s": result["transcription_time_s"]
            },
            "segment_stats": segment_stats,
            "quality_analysis": quality_analysis
        })

    # Calculate aggregate metrics
    avg_compliance_pct = (total_compliance_both / total_segments * 100) if total_segments > 0 else 0

    # Aggregate statistics across all files
    all_segment_stats = [r["segment_stats"] for r in results if r["segment_stats"]]

    if all_segment_stats:
        aggregate_stats = {
            "total_segments": total_segments,
            "avg_compliance_both_pct": avg_compliance_pct,
            "avg_mean_duration_s": sum(s["duration"]["mean_s"] for s in all_segment_stats) / len(all_segment_stats),
            "avg_median_duration_s": sum(s["duration"]["median_s"] for s in all_segment_stats) / len(all_segment_stats),
            "threshold_95_pct": 95.0,
            "meets_threshold": avg_compliance_pct >= 95.0
        }
    else:
        aggregate_stats = {
            "total_segments": 0,
            "avg_compliance_both_pct": 0,
            "meets_threshold": False
        }

    report = {
        "model": model,
        "test_dir": str(test_path),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_files_count": len(audio_files),
        "summary": aggregate_stats,
        "results": results
    }

    # Save results
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Segment Compliance Test Complete")
    print(f"Model: {model.upper()}")
    print(f"Files tested: {len(audio_files)}")
    print(f"Total segments: {total_segments}")
    print(f"Average compliance (both constraints): {avg_compliance_pct:.1f}%")
    print(f"Threshold (95%): {'✓ PASS' if aggregate_stats['meets_threshold'] else '✗ FAIL'}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="A/B Test: Segment length compliance for BELLE-2 vs WhisperX"
    )
    parser.add_argument(
        "--test-dir",
        default="tests/fixtures",
        help="Directory containing test audio files"
    )
    parser.add_argument(
        "--model",
        required=True,
        choices=["belle2", "whisperx"],
        help="Model to test: belle2 or whisperx"
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to test"
    )

    args = parser.parse_args()

    run_segment_test(
        test_dir=args.test_dir,
        model=args.model,
        output=args.output,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
