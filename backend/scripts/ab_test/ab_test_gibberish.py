#!/usr/bin/env python3
"""
Story 3.2c A/B Test: Gibberish/Repetition Detection

Detects repetitive "gibberish loops" and other transcription quality issues
that were problematic before Story 3.1 BELLE-2 integration.

Usage:
    python backend/scripts/ab_test_gibberish.py --test-dir tests/fixtures --model belle2 --output belle2_gibberish.json
    python backend/scripts/ab_test_gibberish.py --test-dir tests/fixtures --model whisperx --output whisperx_gibberish.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import time
import re
from collections import Counter

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import transcription functions
from ab_test_accuracy import transcribe_belle2, transcribe_whisperx


def detect_repetitive_phrases(text: str, min_phrase_length: int = 3) -> Dict[str, Any]:
    """
    Detect repetitive phrases in transcription text

    Args:
        text: Transcription text to analyze
        min_phrase_length: Minimum phrase length to consider (in words)

    Returns:
        Dict with repetition statistics
    """
    # Tokenize into words (simple whitespace split)
    words = text.split()

    if len(words) < min_phrase_length:
        return {
            "has_repetition": False,
            "repetition_score": 0,
            "repeated_phrases": []
        }

    # Find repeated n-grams
    repeated_phrases = {}

    for n in range(min_phrase_length, min(10, len(words) // 2)):  # Check up to 10-word phrases
        ngrams = [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]
        ngram_counts = Counter(ngrams)

        # Find phrases that repeat 2+ times
        for phrase, count in ngram_counts.items():
            if count >= 2:
                repeated_phrases[phrase] = count

    # Calculate repetition score (% of text that is repetitive)
    total_repetitive_chars = sum(len(phrase) * (count - 1) for phrase, count in repeated_phrases.items())
    repetition_score = (total_repetitive_chars / len(text)) * 100 if text else 0

    # Sort by frequency and phrase length
    top_repetitions = sorted(
        repeated_phrases.items(),
        key=lambda x: (x[1], len(x[0])),
        reverse=True
    )[:10]  # Top 10 most repeated phrases

    return {
        "has_repetition": len(repeated_phrases) > 0,
        "repetition_score": repetition_score,
        "repeated_phrases": [{"phrase": phrase, "count": count} for phrase, count in top_repetitions],
        "unique_repeated_phrases": len(repeated_phrases)
    }


def detect_gibberish_patterns(text: str) -> Dict[str, Any]:
    """
    Detect gibberish patterns in transcription

    Returns:
        Dict with gibberish indicators
    """
    # Pattern 1: Excessive repeated characters (e.g., "啊啊啊啊啊")
    repeated_char_pattern = re.findall(r'(.)\1{4,}', text)  # Same char 5+ times
    excessive_char_repetition = len(repeated_char_pattern)

    # Pattern 2: Very long "words" (likely gibberish)
    words = text.split()
    very_long_words = [w for w in words if len(w) > 20]  # Words with 20+ characters

    # Pattern 3: Excessive punctuation repetition
    punct_repetition = re.findall(r'([。，、！？])\1{2,}', text)

    # Pattern 4: Nonsense character sequences (for Chinese, check for invalid patterns)
    # This is a simplified check - real gibberish detection would be more sophisticated

    # Calculate gibberish score
    gibberish_indicators = (
        excessive_char_repetition +
        len(very_long_words) +
        len(punct_repetition)
    )

    gibberish_score = min(100, gibberish_indicators * 10)  # Scale to 0-100

    return {
        "has_gibberish": gibberish_indicators > 0,
        "gibberish_score": gibberish_score,
        "excessive_char_repetition_count": excessive_char_repetition,
        "very_long_words_count": len(very_long_words),
        "very_long_words": very_long_words[:5],  # Top 5 examples
        "punctuation_repetition_count": len(punct_repetition)
    }


def analyze_transcription_quality(segments: List[Dict]) -> Dict[str, Any]:
    """
    Comprehensive quality analysis for gibberish/repetition

    Args:
        segments: Transcription segments

    Returns:
        Dict with quality metrics
    """
    if not segments:
        return {
            "full_text_analysis": {},
            "segment_level_issues": {},
            "overall_quality_score": 100
        }

    # Combine all segment text
    full_text = " ".join(seg["text"] for seg in segments)

    # Analyze full text
    repetition_analysis = detect_repetitive_phrases(full_text)
    gibberish_analysis = detect_gibberish_patterns(full_text)

    # Analyze segment-level issues
    empty_segments = sum(1 for seg in segments if not seg["text"].strip())
    very_short_text = sum(1 for seg in segments if len(seg["text"]) < 3)  # < 3 chars

    # Check for segments that are exact duplicates
    segment_texts = [seg["text"] for seg in segments]
    duplicate_segments = len(segment_texts) - len(set(segment_texts))

    segment_level_issues = {
        "empty_segments": empty_segments,
        "very_short_text_segments": very_short_text,
        "duplicate_segments": duplicate_segments,
        "empty_pct": (empty_segments / len(segments)) * 100 if segments else 0
    }

    # Calculate overall quality score (100 = perfect, 0 = severe issues)
    quality_penalties = 0
    quality_penalties += min(50, repetition_analysis["repetition_score"])  # Max 50 penalty
    quality_penalties += min(30, gibberish_analysis["gibberish_score"] * 0.3)  # Max 30 penalty
    quality_penalties += min(20, segment_level_issues["empty_pct"])  # Max 20 penalty

    overall_quality_score = max(0, 100 - quality_penalties)

    return {
        "full_text_analysis": {
            "repetition": repetition_analysis,
            "gibberish": gibberish_analysis
        },
        "segment_level_issues": segment_level_issues,
        "overall_quality_score": overall_quality_score,
        "has_major_issues": overall_quality_score < 70
    }


def run_gibberish_test(
    test_dir: str,
    model: str,
    output: str,
    limit: int = None
) -> Dict[str, Any]:
    """
    Run gibberish/repetition detection test

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

    audio_files = [f for f in audio_files if "corrupted" not in f.name]
    audio_files = sorted(audio_files)

    if limit:
        audio_files = audio_files[:limit]

    print(f"\n{'='*60}")
    print(f"A/B Test: Gibberish/Repetition Detection")
    print(f"Model: {model.upper()}")
    print(f"Test files: {len(audio_files)}")
    print(f"{'='*60}\n")

    # Select transcription function
    transcribe_func = transcribe_belle2 if model == "belle2" else transcribe_whisperx

    # Run tests
    results = []
    total_quality_score = 0
    files_with_issues = 0

    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")

        # Transcribe
        result = transcribe_func(str(audio_file), language="zh")

        if not result["success"]:
            print(f"  ✗ Error: {result['error']}")
            results.append({
                "file": audio_file.name,
                "transcription": result,
                "quality_analysis": None
            })
            continue

        # Analyze quality
        quality_analysis = analyze_transcription_quality(result["segments"])

        total_quality_score += quality_analysis["overall_quality_score"]
        if quality_analysis["has_major_issues"]:
            files_with_issues += 1

        print(f"  ✓ Transcribed: {result['segment_count']} segments")
        print(f"  📊 Quality score: {quality_analysis['overall_quality_score']:.1f}/100")

        rep_score = quality_analysis["full_text_analysis"]["repetition"]["repetition_score"]
        gib_score = quality_analysis["full_text_analysis"]["gibberish"]["gibberish_score"]

        print(f"  🔁 Repetition score: {rep_score:.1f}%")
        print(f"  🗑️  Gibberish score: {gib_score:.1f}/100")

        if quality_analysis["has_major_issues"]:
            print(f"  ⚠️  Major quality issues detected!")

        # Show top repetitions if any
        top_reps = quality_analysis["full_text_analysis"]["repetition"]["repeated_phrases"]
        if top_reps:
            print(f"  🔁 Top repetition: \"{top_reps[0]['phrase']}\" (x{top_reps[0]['count']})")

        results.append({
            "file": audio_file.name,
            "transcription": {
                "segment_count": result["segment_count"],
                "transcription_time_s": result["transcription_time_s"]
            },
            "quality_analysis": quality_analysis
        })

    # Calculate aggregate metrics
    avg_quality_score = total_quality_score / len(audio_files) if audio_files else 0

    report = {
        "model": model,
        "test_dir": str(test_path),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_files_count": len(audio_files),
        "summary": {
            "avg_quality_score": avg_quality_score,
            "files_with_major_issues": files_with_issues,
            "files_with_major_issues_pct": (files_with_issues / len(audio_files)) * 100 if audio_files else 0,
            "threshold_quality_score": 70.0,
            "meets_threshold": avg_quality_score >= 70.0
        },
        "results": results
    }

    # Save results
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Gibberish/Repetition Test Complete")
    print(f"Model: {model.upper()}")
    print(f"Files tested: {len(audio_files)}")
    print(f"Average quality score: {avg_quality_score:.1f}/100")
    print(f"Files with major issues: {files_with_issues} ({files_with_issues / len(audio_files) * 100:.1f}%)")
    print(f"Quality threshold (70): {'✓ PASS' if report['summary']['meets_threshold'] else '✗ FAIL'}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="A/B Test: Gibberish/repetition detection for BELLE-2 vs WhisperX"
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

    run_gibberish_test(
        test_dir=args.test_dir,
        model=args.model,
        output=args.output,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
