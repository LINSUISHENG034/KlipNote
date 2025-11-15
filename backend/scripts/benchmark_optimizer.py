#!/usr/bin/env python3
"""
Performance benchmarking script for WhisperX optimizer validation.

Story 3.2b: WhisperX Integration Validation
Task 4: Create performance benchmarking script (AC: #5)

Success Criteria:
- Measure BELLE-2 transcription time
- Measure WhisperX optimization time
- Calculate overhead percentage: (optimization_time / transcription_time) * 100
- Validate overhead <25% threshold
- Test with minimum 10 diverse audio files (5-60 minutes, various speakers)
- Generate JSON report with detailed timing statistics

Usage:
    cd backend
    python scripts/benchmark_optimizer.py [--test-dir <path>] [--output <path>]

Example:
    python scripts/benchmark_optimizer.py
    python scripts/benchmark_optimizer.py --test-dir ../tests/fixtures
    python scripts/benchmark_optimizer.py --output benchmark_results.json
"""

import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.optimization.whisperx_optimizer import WhisperXOptimizer


def get_audio_files(test_dir: Path) -> List[Path]:
    """
    Discover audio files in test directory.

    Args:
        test_dir: Directory containing test audio files

    Returns:
        List of audio file paths sorted by size (smallest to largest)
    """
    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.mp4', '.webm', '.aac', '.wma'}
    audio_files = []

    for ext in audio_extensions:
        audio_files.extend(test_dir.glob(f"*{ext}"))

    # Sort by file size (smallest first for faster initial testing)
    audio_files.sort(key=lambda p: p.stat().st_size)

    return audio_files


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def benchmark_single_file(
    audio_path: Path,
    transcription_service: Belle2Service,
    optimizer: WhisperXOptimizer,
    file_index: int,
    total_files: int
) -> Dict[str, Any]:
    """
    Benchmark a single audio file.

    Args:
        audio_path: Path to audio file
        transcription_service: BELLE-2 service instance
        optimizer: WhisperX optimizer instance
        file_index: Current file index (1-based)
        total_files: Total number of files

    Returns:
        Dictionary with benchmark results
    """
    file_size = audio_path.stat().st_size

    print(f"\n[{file_index}/{total_files}] Processing: {audio_path.name}")
    print(f"  Size: {format_file_size(file_size)}")

    # Phase 1: BELLE-2 Transcription
    print("  Phase 1: BELLE-2 transcription...")
    transcribe_start = time.time()
    segments = transcription_service.transcribe(str(audio_path), language="zh")
    transcription_time = time.time() - transcribe_start
    print(f"    ✓ Completed in {transcription_time:.2f}s ({len(segments)} segments)")

    # Phase 2: WhisperX Optimization
    print("  Phase 2: WhisperX optimization...")
    optimize_start = time.time()
    optimization_result = optimizer.optimize(segments, str(audio_path), language="zh")
    optimization_time = time.time() - optimize_start
    print(f"    ✓ Completed in {optimization_time:.2f}s")

    # Calculate metrics
    total_time = transcription_time + optimization_time
    overhead_pct = (optimization_time / transcription_time) * 100 if transcription_time > 0 else 0

    # Determine if this file meets threshold
    meets_threshold = overhead_pct < 25.0
    status = "✓ PASS" if meets_threshold else "✗ FAIL"

    print(f"  Results:")
    print(f"    Transcription: {transcription_time:.2f}s")
    print(f"    Optimization:  {optimization_time:.2f}s")
    print(f"    Total:         {total_time:.2f}s")
    print(f"    Overhead:      {overhead_pct:.2f}% {status}")

    return {
        "file": audio_path.name,
        "file_path": str(audio_path.absolute()),
        "file_size_bytes": file_size,
        "file_size_human": format_file_size(file_size),
        "transcription_time_s": round(transcription_time, 2),
        "optimization_time_s": round(optimization_time, 2),
        "total_time_s": round(total_time, 2),
        "overhead_pct": round(overhead_pct, 2),
        "meets_threshold": meets_threshold,
        "segments_before": len(segments),
        "segments_after": optimization_result.metrics["segments_optimized"],
        "word_count": optimization_result.metrics.get("word_count", 0),
        "optimizer": optimization_result.optimizer_name,
        "optimizer_metrics": optimization_result.metrics
    }


def calculate_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate summary statistics from benchmark results.

    Args:
        results: List of per-file benchmark results

    Returns:
        Dictionary with summary statistics
    """
    if not results:
        return {
            "error": "No files processed successfully",
            "pass": False
        }

    overhead_values = [r["overhead_pct"] for r in results]
    transcription_times = [r["transcription_time_s"] for r in results]
    optimization_times = [r["optimization_time_s"] for r in results]

    avg_overhead = sum(overhead_values) / len(overhead_values)
    max_overhead = max(overhead_values)
    min_overhead = min(overhead_values)

    files_passing = sum(1 for r in results if r["meets_threshold"])
    pass_rate = (files_passing / len(results)) * 100

    return {
        "total_files": len(results),
        "files_passing_threshold": files_passing,
        "files_failing_threshold": len(results) - files_passing,
        "pass_rate_pct": round(pass_rate, 2),
        "avg_overhead_pct": round(avg_overhead, 2),
        "max_overhead_pct": round(max_overhead, 2),
        "min_overhead_pct": round(min_overhead, 2),
        "median_overhead_pct": round(sorted(overhead_values)[len(overhead_values)//2], 2),
        "avg_transcription_time_s": round(sum(transcription_times) / len(transcription_times), 2),
        "avg_optimization_time_s": round(sum(optimization_times) / len(optimization_times), 2),
        "total_transcription_time_s": round(sum(transcription_times), 2),
        "total_optimization_time_s": round(sum(optimization_times), 2),
        "threshold_pct": 25.0,
        "meets_avg_threshold": avg_overhead < 25.0,
        "pass": avg_overhead < 25.0 and pass_rate >= 80.0  # 80% of files must pass
    }


def print_summary_table(summary: Dict[str, Any]) -> None:
    """Print formatted summary table"""
    print(f"\n{'='*70}")
    print(f"{'BENCHMARK SUMMARY':^70}")
    print(f"{'='*70}")
    print(f"Files Tested:          {summary.get('total_files', 0)}")
    print(f"Files Passing:         {summary.get('files_passing_threshold', 0)}")
    print(f"Files Failing:         {summary.get('files_failing_threshold', 0)}")
    print(f"Pass Rate:             {summary.get('pass_rate_pct', 0):.2f}%")
    print(f"{'-'*70}")
    print(f"Avg Overhead:          {summary.get('avg_overhead_pct', 0):.2f}%")
    print(f"Min Overhead:          {summary.get('min_overhead_pct', 0):.2f}%")
    print(f"Max Overhead:          {summary.get('max_overhead_pct', 0):.2f}%")
    print(f"Median Overhead:       {summary.get('median_overhead_pct', 0):.2f}%")
    print(f"{'-'*70}")
    print(f"Threshold:             {summary.get('threshold_pct', 25.0)}%")
    print(f"Meets Threshold:       {'✓ YES' if summary.get('meets_avg_threshold') else '✗ NO'}")
    print(f"{'-'*70}")
    print(f"Total Transcription:   {summary.get('total_transcription_time_s', 0):.2f}s")
    print(f"Total Optimization:    {summary.get('total_optimization_time_s', 0):.2f}s")
    print(f"{'='*70}")

    if summary.get('pass'):
        print(f"{'✓ OVERALL RESULT: PASS':^70}")
    else:
        print(f"{'✗ OVERALL RESULT: FAIL':^70}")
    print(f"{'='*70}")


def main():
    """Main benchmarking workflow"""
    parser = argparse.ArgumentParser(
        description="Benchmark WhisperX optimizer performance vs BELLE-2 transcription"
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
        default=Path(__file__).parent.parent / "benchmark_report.json",
        help="Output JSON report path (default: ../benchmark_report.json)"
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

    # Check minimum requirement
    if len(audio_files) < 10:
        print(f"⚠ Warning: Story 3.2b requires minimum 10 diverse test files")
        print(f"  Current: {len(audio_files)} files")
        print(f"  Recommendation: Add more diverse audio files to {args.test_dir}")

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
        print(f"  Hint: Ensure dependencies installed: uv pip install whisperx pyannote.audio==3.1.1")
        sys.exit(1)

    # Run benchmarks
    print(f"\n{'='*70}")
    print("Running benchmarks...")
    print(f"{'='*70}")

    results = []
    errors = []

    for i, audio_path in enumerate(audio_files, start=1):
        try:
            result = benchmark_single_file(
                audio_path,
                transcription_service,
                optimizer,
                file_index=i,
                total_files=len(audio_files)
            )
            results.append(result)
        except Exception as e:
            error_msg = f"Error processing {audio_path.name}: {e}"
            print(f"  ✗ {error_msg}")
            errors.append({
                "file": audio_path.name,
                "error": str(e)
            })

    # Calculate summary
    summary = calculate_summary(results)

    # Generate report
    report = {
        "benchmark_date": datetime.now().isoformat(),
        "benchmark_version": "1.0.0",
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
    print(f"\nSaving benchmark report...")
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
