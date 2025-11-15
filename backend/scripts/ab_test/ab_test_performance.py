#!/usr/bin/env python3
"""
Story 3.2c A/B Test: Performance Benchmarking

Measures GPU processing time, RTF (Real-Time Factor), and throughput
for BELLE-2 vs WhisperX transcription models.

RTF = processing_time / audio_duration
  - RTF < 1.0 means faster than real-time
  - RTF = 1.0 means real-time processing
  - RTF > 1.0 means slower than real-time

Usage:
    python backend/scripts/ab_test_performance.py --test-dir tests/fixtures --model belle2 --output belle2_performance.json
    python backend/scripts/ab_test_performance.py --test-dir tests/fixtures --model whisperx --output whisperx_performance.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import transcription functions
from ab_test_accuracy import transcribe_belle2, transcribe_whisperx


def get_audio_duration(audio_path: str) -> float:
    """
    Get audio duration in seconds

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds
    """
    try:
        import librosa
        # Load audio to get duration (faster than full load)
        duration = librosa.get_duration(path=audio_path)
        return duration
    except ImportError:
        print("WARNING: librosa not installed. Using whisperx for duration.")
        try:
            import whisperx
            audio = whisperx.load_audio(audio_path)
            # WhisperX loads at 16kHz
            duration = len(audio) / 16000.0
            return duration
        except:
            return 0.0


def calculate_rtf(processing_time_s: float, audio_duration_s: float) -> float:
    """
    Calculate Real-Time Factor

    RTF = processing_time / audio_duration
    """
    if audio_duration_s == 0:
        return 0.0
    return processing_time_s / audio_duration_s


def get_gpu_info() -> Dict[str, Any]:
    """
    Get GPU information

    Returns:
        Dict with GPU details
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return {
                "available": False,
                "device_name": None,
                "device_count": 0
            }

        return {
            "available": True,
            "device_name": torch.cuda.get_device_name(0),
            "device_count": torch.cuda.device_count(),
            "cuda_version": torch.version.cuda,
            "pytorch_version": torch.__version__
        }
    except ImportError:
        return {"available": False}


def run_performance_test(
    test_dir: str,
    model: str,
    output: str,
    limit: int = None,
    warmup: bool = True
) -> Dict[str, Any]:
    """
    Run performance benchmarking test

    Args:
        test_dir: Directory containing test audio files
        model: "belle2" or "whisperx"
        output: Output JSON file path
        limit: Maximum number of files to test
        warmup: Perform warmup run to load models into GPU

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
    print(f"A/B Test: Performance Benchmarking")
    print(f"Model: {model.upper()}")
    print(f"Test files: {len(audio_files)}")
    print(f"{'='*60}\n")

    # Get GPU info
    gpu_info = get_gpu_info()
    print(f"GPU: {gpu_info.get('device_name', 'N/A')}")
    print(f"CUDA: {gpu_info.get('cuda_version', 'N/A')}")
    print()

    # Select transcription function
    transcribe_func = transcribe_belle2 if model == "belle2" else transcribe_whisperx

    # Warmup run (if enabled)
    if warmup and audio_files:
        print("Performing warmup run to load models into GPU...")
        warmup_file = audio_files[0]
        transcribe_func(str(warmup_file), language="zh")
        print("Warmup complete.\n")

    # Run tests
    results = []
    total_processing_time = 0
    total_audio_duration = 0
    total_segments = 0

    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")

        # Get audio duration
        audio_duration = get_audio_duration(str(audio_file))
        print(f"  ⏱️  Audio duration: {audio_duration:.2f}s")

        # Transcribe with timing
        start_time = time.time()
        result = transcribe_func(str(audio_file), language="zh")
        processing_time = time.time() - start_time

        if not result["success"]:
            print(f"  ✗ Error: {result['error']}")
            results.append({
                "file": audio_file.name,
                "audio_duration_s": audio_duration,
                "transcription": result,
                "performance": None
            })
            continue

        # Calculate performance metrics
        rtf = calculate_rtf(processing_time, audio_duration)
        throughput = audio_duration / processing_time if processing_time > 0 else 0  # x real-time

        total_processing_time += processing_time
        total_audio_duration += audio_duration
        total_segments += result["segment_count"]

        performance_metrics = {
            "processing_time_s": processing_time,
            "rtf": rtf,
            "throughput_x_realtime": throughput,
            "segments_per_second": result["segment_count"] / processing_time if processing_time > 0 else 0,
            "faster_than_realtime": rtf < 1.0
        }

        print(f"  ✓ Processing time: {processing_time:.2f}s")
        print(f"  📊 RTF: {rtf:.3f}x")
        print(f"  📊 Throughput: {throughput:.2f}x real-time")
        print(f"  📊 Segments: {result['segment_count']} ({performance_metrics['segments_per_second']:.2f}/s)")

        if rtf > 1.0:
            print(f"  ⚠️  Slower than real-time!")

        results.append({
            "file": audio_file.name,
            "audio_duration_s": audio_duration,
            "transcription": {
                "segment_count": result["segment_count"],
                "model": result["model"]
            },
            "performance": performance_metrics
        })

    # Calculate aggregate metrics
    avg_rtf = calculate_rtf(total_processing_time, total_audio_duration)
    avg_throughput = total_audio_duration / total_processing_time if total_processing_time > 0 else 0

    # Performance by file size category
    small_files = [r for r in results if r["audio_duration_s"] < 60]  # < 1 min
    medium_files = [r for r in results if 60 <= r["audio_duration_s"] < 600]  # 1-10 min
    large_files = [r for r in results if r["audio_duration_s"] >= 600]  # >= 10 min

    def calc_avg_rtf(file_list):
        if not file_list or not any(r["performance"] for r in file_list):
            return None
        valid = [r for r in file_list if r["performance"]]
        total_proc = sum(r["performance"]["processing_time_s"] for r in valid)
        total_dur = sum(r["audio_duration_s"] for r in valid)
        return calculate_rtf(total_proc, total_dur)

    report = {
        "model": model,
        "test_dir": str(test_path),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "gpu_info": gpu_info,
        "test_files_count": len(audio_files),
        "summary": {
            "total_audio_duration_s": total_audio_duration,
            "total_processing_time_s": total_processing_time,
            "total_segments": total_segments,
            "avg_rtf": avg_rtf,
            "avg_throughput_x_realtime": avg_throughput,
            "faster_than_realtime": avg_rtf < 1.0,
            "rtf_by_file_size": {
                "small_files_under_1min": calc_avg_rtf(small_files),
                "medium_files_1_10min": calc_avg_rtf(medium_files),
                "large_files_over_10min": calc_avg_rtf(large_files)
            }
        },
        "results": results
    }

    # Save results
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Performance Benchmarking Complete")
    print(f"Model: {model.upper()}")
    print(f"Files tested: {len(audio_files)}")
    print(f"Total audio duration: {total_audio_duration / 60:.1f} minutes")
    print(f"Total processing time: {total_processing_time / 60:.1f} minutes")
    print(f"Average RTF: {avg_rtf:.3f}x")
    print(f"Average throughput: {avg_throughput:.2f}x real-time")
    print(f"Faster than real-time: {'✓ YES' if avg_rtf < 1.0 else '✗ NO'}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="A/B Test: Performance benchmarking for BELLE-2 vs WhisperX"
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
    parser.add_argument(
        "--no-warmup",
        action="store_true",
        help="Skip warmup run"
    )

    args = parser.parse_args()

    run_performance_test(
        test_dir=args.test_dir,
        model=args.model,
        output=args.output,
        limit=args.limit,
        warmup=not args.no_warmup
    )


if __name__ == "__main__":
    main()
