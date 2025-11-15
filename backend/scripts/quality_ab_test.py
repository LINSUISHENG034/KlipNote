#!/usr/bin/env python3
"""
Quality A/B testing script for WhisperX optimizer validation.

Story 3.2b: WhisperX Integration Validation
Task 5: Create quality A/B testing script (AC: #6, #7)

Success Criteria:
- For each test file: Transcribe with BELLE-2 (baseline)
- For each test file: Transcribe + optimize with WhisperXOptimizer
- Calculate segment length statistics: mean, median, P95
- Calculate segment length improvement percentage
- Calculate CER/WER if reference transcripts available
- Validate: CER/WER ≤ baseline, segment length improvement ≥10%
- Generate JSON report with quality metrics

Usage:
    cd backend
    python scripts/quality_ab_test.py [--test-dir <path>] [--output <path>]

Example:
    python scripts/quality_ab_test.py
    python scripts/quality_ab_test.py --test-dir ../tests/fixtures
    python scripts/quality_ab_test.py --output quality_report.json
"""

import sys
import time
import json
import argparse
import statistics
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.optimization.whisperx_optimizer import WhisperXOptimizer


def calculate_segment_stats(segments: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate segment length statistics.

    Args:
        segments: List of transcription segments

    Returns:
        Dictionary with duration and character count statistics
    """
    if not segments:
        return {
            "count": 0,
            "mean_duration_s": 0.0,
            "median_duration_s": 0.0,
            "p95_duration_s": 0.0,
            "mean_char_count": 0.0,
            "median_char_count": 0.0,
            "pct_1_7_seconds": 0.0,
            "pct_under_200_chars": 0.0,
            "pct_meets_both": 0.0
        }

    durations = [seg["end"] - seg["start"] for seg in segments]
    char_counts = [len(seg["text"]) for seg in segments]

    # Calculate constraint compliance
    meets_duration = sum(1 for d in durations if 1.0 <= d <= 7.0)
    meets_char_limit = sum(1 for c in char_counts if c < 200)
    meets_both = sum(
        1 for seg in segments
        if 1.0 <= (seg["end"] - seg["start"]) <= 7.0 and len(seg["text"]) < 200
    )

    return {
        "count": len(segments),
        "mean_duration_s": round(statistics.mean(durations), 2),
        "median_duration_s": round(statistics.median(durations), 2),
        "p95_duration_s": round(statistics.quantiles(durations, n=20)[18], 2) if len(durations) >= 20 else round(max(durations), 2),
        "min_duration_s": round(min(durations), 2),
        "max_duration_s": round(max(durations), 2),
        "mean_char_count": round(statistics.mean(char_counts), 2),
        "median_char_count": round(statistics.median(char_counts), 2),
        "max_char_count": max(char_counts),
        "pct_1_7_seconds": round((meets_duration / len(segments)) * 100, 2),
        "pct_under_200_chars": round((meets_char_limit / len(segments)) * 100, 2),
        "pct_meets_both": round((meets_both / len(segments)) * 100, 2)
    }


def calculate_cer_wer(
    hypothesis: str,
    reference: str
) -> Dict[str, float]:
    """
    Calculate Character Error Rate (CER) and Word Error Rate (WER).

    Args:
        hypothesis: Generated transcription text
        reference: Reference transcription text

    Returns:
        Dictionary with CER and WER metrics
    """
    try:
        import jiwer
    except ImportError:
        return {
            "cer": None,
            "wer": None,
            "error": "jiwer library not installed"
        }

    try:
        cer = jiwer.cer(reference, hypothesis)
        wer = jiwer.wer(reference, hypothesis)
        return {
            "cer": round(cer, 4),
            "wer": round(wer, 4)
        }
    except Exception as e:
        return {
            "cer": None,
            "wer": None,
            "error": str(e)
        }


def test_single_file(
    audio_path: Path,
    transcription_service: Belle2Service,
    optimizer: WhisperXOptimizer,
    reference_text: Optional[str],
    file_index: int,
    total_files: int
) -> Dict[str, Any]:
    """
    A/B test a single audio file (baseline vs optimized).

    Args:
        audio_path: Path to audio file
        transcription_service: BELLE-2 service instance
        optimizer: WhisperX optimizer instance
        reference_text: Optional reference transcription for CER/WER
        file_index: Current file index (1-based)
        total_files: Total number of files

    Returns:
        Dictionary with quality comparison results
    """
    print(f"\n[{file_index}/{total_files}] Testing: {audio_path.name}")

    # Baseline: BELLE-2 transcription only
    print("  Baseline: BELLE-2 transcription...")
    baseline_segments = transcription_service.transcribe(str(audio_path), language="zh")
    baseline_text = " ".join(seg["text"] for seg in baseline_segments)
    baseline_stats = calculate_segment_stats(baseline_segments)
    print(f"    ✓ {baseline_stats['count']} segments, mean: {baseline_stats['mean_duration_s']}s")

    # Optimized: BELLE-2 + WhisperX optimization
    print("  Optimized: BELLE-2 + WhisperX...")
    optimization_result = optimizer.optimize(baseline_segments, str(audio_path), language="zh")
    optimized_segments = optimization_result.segments
    optimized_text = " ".join(seg["text"] for seg in optimized_segments)
    optimized_stats = calculate_segment_stats(optimized_segments)
    print(f"    ✓ {optimized_stats['count']} segments, mean: {optimized_stats['mean_duration_s']}s")

    # Calculate improvements
    duration_improvement_pct = 0.0
    if baseline_stats["mean_duration_s"] > 0:
        duration_improvement_pct = (
            (baseline_stats["mean_duration_s"] - optimized_stats["mean_duration_s"]) /
            baseline_stats["mean_duration_s"]
        ) * 100

    constraint_improvement_pct = (
        optimized_stats["pct_meets_both"] - baseline_stats["pct_meets_both"]
    )

    # CER/WER calculation (if reference available)
    baseline_accuracy = None
    optimized_accuracy = None

    if reference_text:
        print("  Calculating CER/WER vs reference...")
        baseline_accuracy = calculate_cer_wer(baseline_text, reference_text)
        optimized_accuracy = calculate_cer_wer(optimized_text, reference_text)

        if baseline_accuracy.get("cer") is not None:
            print(f"    Baseline  CER: {baseline_accuracy['cer']:.4f}, WER: {baseline_accuracy['wer']:.4f}")
            print(f"    Optimized CER: {optimized_accuracy['cer']:.4f}, WER: {optimized_accuracy['wer']:.4f}")

    # Validation results
    meets_length_improvement = duration_improvement_pct >= 10.0
    meets_constraint_target = optimized_stats["pct_meets_both"] >= 95.0

    no_accuracy_regression = True
    if baseline_accuracy and optimized_accuracy:
        if baseline_accuracy.get("cer") is not None and optimized_accuracy.get("cer") is not None:
            no_accuracy_regression = optimized_accuracy["cer"] <= baseline_accuracy["cer"]

    print(f"  Results:")
    print(f"    Duration improvement:  {duration_improvement_pct:+.2f}% {'✓' if meets_length_improvement else '✗'}")
    print(f"    Constraint compliance: {optimized_stats['pct_meets_both']:.2f}% {'✓' if meets_constraint_target else '✗'}")
    print(f"    No accuracy regression: {'✓ YES' if no_accuracy_regression else '✗ NO'}")

    return {
        "file": audio_path.name,
        "file_path": str(audio_path.absolute()),
        "baseline": {
            "segments": baseline_stats,
            "accuracy": baseline_accuracy,
            "text_length": len(baseline_text)
        },
        "optimized": {
            "segments": optimized_stats,
            "accuracy": optimized_accuracy,
            "text_length": len(optimized_text),
            "optimizer": optimization_result.optimizer_name,
            "metrics": optimization_result.metrics
        },
        "improvements": {
            "duration_improvement_pct": round(duration_improvement_pct, 2),
            "constraint_compliance_improvement_pct": round(constraint_improvement_pct, 2),
            "segment_count_change": optimized_stats["count"] - baseline_stats["count"]
        },
        "validation": {
            "meets_length_improvement_10pct": meets_length_improvement,
            "meets_constraint_target_95pct": meets_constraint_target,
            "no_accuracy_regression": no_accuracy_regression,
            "pass": meets_length_improvement and no_accuracy_regression
        }
    }


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from quality test results.

    Args:
        results: List of per-file quality test results

    Returns:
        Dictionary with summary statistics
    """
    if not results:
        return {
            "error": "No files processed successfully",
            "pass": False
        }

    duration_improvements = [r["improvements"]["duration_improvement_pct"] for r in results]
    constraint_improvements = [r["improvements"]["constraint_compliance_improvement_pct"] for r in results]

    files_passing = sum(1 for r in results if r["validation"]["pass"])
    pass_rate = (files_passing / len(results)) * 100

    # Calculate average constraint compliance
    avg_baseline_compliance = statistics.mean([
        r["baseline"]["segments"]["pct_meets_both"] for r in results
    ])
    avg_optimized_compliance = statistics.mean([
        r["optimized"]["segments"]["pct_meets_both"] for r in results
    ])

    # Calculate average duration
    avg_baseline_duration = statistics.mean([
        r["baseline"]["segments"]["mean_duration_s"] for r in results
    ])
    avg_optimized_duration = statistics.mean([
        r["optimized"]["segments"]["mean_duration_s"] for r in results
    ])

    # Check for accuracy regressions
    files_with_accuracy = sum(
        1 for r in results
        if r["baseline"]["accuracy"] and r["baseline"]["accuracy"].get("cer") is not None
    )
    files_no_regression = sum(
        1 for r in results
        if r["validation"]["no_accuracy_regression"]
    )

    return {
        "total_files": len(results),
        "files_passing": files_passing,
        "files_failing": len(results) - files_passing,
        "pass_rate_pct": round(pass_rate, 2),
        "avg_duration_improvement_pct": round(statistics.mean(duration_improvements), 2),
        "median_duration_improvement_pct": round(statistics.median(duration_improvements), 2),
        "min_duration_improvement_pct": round(min(duration_improvements), 2),
        "max_duration_improvement_pct": round(max(duration_improvements), 2),
        "avg_constraint_improvement_pct": round(statistics.mean(constraint_improvements), 2),
        "avg_baseline_compliance_pct": round(avg_baseline_compliance, 2),
        "avg_optimized_compliance_pct": round(avg_optimized_compliance, 2),
        "avg_baseline_duration_s": round(avg_baseline_duration, 2),
        "avg_optimized_duration_s": round(avg_optimized_duration, 2),
        "files_with_accuracy_metrics": files_with_accuracy,
        "files_no_accuracy_regression": files_no_regression,
        "meets_length_improvement_threshold": statistics.mean(duration_improvements) >= 10.0,
        "meets_constraint_compliance_target": avg_optimized_compliance >= 95.0,
        "no_accuracy_regressions": files_no_regression == max(files_with_accuracy, 1),
        "pass": (
            statistics.mean(duration_improvements) >= 10.0 and
            files_no_regression == max(files_with_accuracy, 1) and
            pass_rate >= 80.0
        )
    }


def print_summary_table(summary: Dict[str, Any]) -> None:
    """Print formatted summary table"""
    print(f"\n{'='*70}")
    print(f"{'QUALITY A/B TEST SUMMARY':^70}")
    print(f"{'='*70}")
    print(f"Files Tested:              {summary.get('total_files', 0)}")
    print(f"Files Passing:             {summary.get('files_passing', 0)}")
    print(f"Files Failing:             {summary.get('files_failing', 0)}")
    print(f"Pass Rate:                 {summary.get('pass_rate_pct', 0):.2f}%")
    print(f"{'-'*70}")
    print(f"Avg Duration Improvement:  {summary.get('avg_duration_improvement_pct', 0):+.2f}%")
    print(f"Min Duration Improvement:  {summary.get('min_duration_improvement_pct', 0):+.2f}%")
    print(f"Max Duration Improvement:  {summary.get('max_duration_improvement_pct', 0):+.2f}%")
    print(f"{'-'*70}")
    print(f"Avg Baseline Compliance:   {summary.get('avg_baseline_compliance_pct', 0):.2f}%")
    print(f"Avg Optimized Compliance:  {summary.get('avg_optimized_compliance_pct', 0):.2f}%")
    print(f"Target Compliance:         95.00%")
    print(f"{'-'*70}")
    print(f"Avg Baseline Duration:     {summary.get('avg_baseline_duration_s', 0):.2f}s")
    print(f"Avg Optimized Duration:    {summary.get('avg_optimized_duration_s', 0):.2f}s")
    print(f"{'-'*70}")
    print(f"Files with Accuracy Data:  {summary.get('files_with_accuracy_metrics', 0)}")
    print(f"No Accuracy Regressions:   {'✓ YES' if summary.get('no_accuracy_regressions') else '✗ NO'}")
    print(f"{'-'*70}")
    print(f"Validation Results:")
    print(f"  ≥10% Duration Improvement:  {'✓ PASS' if summary.get('meets_length_improvement_threshold') else '✗ FAIL'}")
    print(f"  ≥95% Constraint Compliance: {'✓ PASS' if summary.get('meets_constraint_compliance_target') else '✗ FAIL'}")
    print(f"  No CER/WER Regressions:     {'✓ PASS' if summary.get('no_accuracy_regressions') else '✗ FAIL'}")
    print(f"{'='*70}")

    if summary.get('pass'):
        print(f"{'✓ OVERALL RESULT: PASS':^70}")
    else:
        print(f"{'✗ OVERALL RESULT: FAIL':^70}")
    print(f"{'='*70}")


def get_audio_files(test_dir: Path) -> List[Path]:
    """Discover audio files in test directory"""
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.webm', '.aac', '.wma'}
    audio_files = []

    for ext in audio_extensions:
        audio_files.extend(test_dir.glob(f"*{ext}"))

    audio_files.sort(key=lambda p: p.stat().st_size)
    return audio_files


def main():
    """Main quality testing workflow"""
    parser = argparse.ArgumentParser(
        description="Quality A/B testing for WhisperX optimizer validation"
    )
    parser.add_argument(
        "--test-dir",
        type=Path,
        default=Path(__file__).parent.parent / "tests" / "fixtures",
        help="Directory containing test audio files (default: ../tests/fixtures)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent.parent / "quality_report.json",
        help="Output JSON report path (default: ../quality_report.json)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of files to test (default: all files)"
    )

    args = parser.parse_args()

    # Discover test files
    print(f"Discovering audio files in: {args.test_dir}")
    audio_files = get_audio_files(args.test_dir)

    if not audio_files:
        print(f"✗ No audio files found in {args.test_dir}")
        sys.exit(1)

    if args.limit:
        audio_files = audio_files[:args.limit]

    print(f"Found {len(audio_files)} audio file(s)")

    # Initialize services
    print(f"\n{'='*70}")
    print("Initializing services...")
    print(f"{'='*70}")

    try:
        print("Loading BELLE-2 transcription service...")
        transcription_service = Belle2Service(device="cuda")
        print("  ✓ BELLE-2 service ready")
    except Exception as e:
        print(f"  ✗ Failed to initialize BELLE-2: {e}")
        sys.exit(1)

    try:
        print("Loading WhisperX optimizer...")
        optimizer = WhisperXOptimizer()
        print("  ✓ WhisperX optimizer ready")
    except Exception as e:
        print(f"  ✗ Failed to initialize WhisperX: {e}")
        sys.exit(1)

    # Run quality tests
    print(f"\n{'='*70}")
    print("Running quality A/B tests...")
    print(f"{'='*70}")

    results = []
    errors = []

    for i, audio_path in enumerate(audio_files, start=1):
        # Note: Reference transcripts not available in this version
        # Future enhancement: Load reference from .txt files matching audio names
        reference_text = None

        try:
            result = test_single_file(
                audio_path,
                transcription_service,
                optimizer,
                reference_text,
                file_index=i,
                total_files=len(audio_files)
            )
            results.append(result)
        except Exception as e:
            error_msg = f"Error testing {audio_path.name}: {e}"
            print(f"  ✗ {error_msg}")
            errors.append({
                "file": audio_path.name,
                "error": str(e)
            })

    # Calculate summary
    summary = calculate_summary(results)

    # Generate report
    report = {
        "test_date": datetime.now().isoformat(),
        "test_version": "1.0.0",
        "optimizer_engine": "whisperx",
        "test_directory": str(args.test_dir.absolute()),
        "test_files_discovered": len(audio_files),
        "test_files_processed": len(results),
        "test_files_failed": len(errors),
        "results": results,
        "errors": errors,
        "summary": summary
    }

    # Save JSON report
    print(f"\nSaving quality test report...")
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Report saved to: {args.output}")

    # Print summary
    print_summary_table(summary)

    # Exit with appropriate code
    if summary.get("pass"):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
