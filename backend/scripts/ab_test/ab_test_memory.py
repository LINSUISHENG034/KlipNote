#!/usr/bin/env python3
"""
Story 3.2c A/B Test: VRAM Usage Monitoring

Monitors GPU memory usage during transcription to understand resource
requirements and compare BELLE-2 vs WhisperX memory footprints.

Usage:
    python backend/scripts/ab_test_memory.py --test-dir tests/fixtures --model belle2 --output belle2_memory.json
    python backend/scripts/ab_test_memory.py --test-dir tests/fixtures --model whisperx --output whisperx_memory.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import time
import threading

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import transcription functions
from ab_test_accuracy import transcribe_belle2, transcribe_whisperx


class GPUMemoryMonitor:
    """Monitor GPU memory usage during transcription"""

    def __init__(self, sample_interval_ms: int = 100):
        """
        Args:
            sample_interval_ms: Sampling interval in milliseconds
        """
        self.sample_interval = sample_interval_ms / 1000.0  # Convert to seconds
        self.samples = []
        self.monitoring = False
        self.monitor_thread = None

        try:
            import torch
            self.torch = torch
            self.gpu_available = torch.cuda.is_available()
        except ImportError:
            self.torch = None
            self.gpu_available = False

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            if self.gpu_available:
                allocated = self.torch.cuda.memory_allocated() / (1024 ** 3)  # GB
                reserved = self.torch.cuda.memory_reserved() / (1024 ** 3)  # GB
                self.samples.append({
                    "timestamp": time.time(),
                    "allocated_gb": allocated,
                    "reserved_gb": reserved
                })
            time.sleep(self.sample_interval)

    def start(self):
        """Start monitoring"""
        if not self.gpu_available:
            return

        self.samples = []
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self) -> Dict[str, Any]:
        """
        Stop monitoring and return statistics

        Returns:
            Dict with memory usage statistics
        """
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)

        if not self.samples:
            return {
                "gpu_available": self.gpu_available,
                "samples_count": 0,
                "allocated": {},
                "reserved": {}
            }

        allocated_values = [s["allocated_gb"] for s in self.samples]
        reserved_values = [s["reserved_gb"] for s in self.samples]

        return {
            "gpu_available": self.gpu_available,
            "samples_count": len(self.samples),
            "allocated": {
                "min_gb": min(allocated_values),
                "max_gb": max(allocated_values),
                "mean_gb": sum(allocated_values) / len(allocated_values),
                "final_gb": allocated_values[-1]
            },
            "reserved": {
                "min_gb": min(reserved_values),
                "max_gb": max(reserved_values),
                "mean_gb": sum(reserved_values) / len(reserved_values),
                "final_gb": reserved_values[-1]
            }
        }


def get_initial_gpu_memory() -> Dict[str, float]:
    """Get GPU memory before transcription"""
    try:
        import torch
        if torch.cuda.is_available():
            return {
                "allocated_gb": torch.cuda.memory_allocated() / (1024 ** 3),
                "reserved_gb": torch.cuda.memory_reserved() / (1024 ** 3)
            }
    except ImportError:
        pass
    return {"allocated_gb": 0.0, "reserved_gb": 0.0}


def run_memory_test(
    test_dir: str,
    model: str,
    output: str,
    limit: int = None,
    sample_interval_ms: int = 100
) -> Dict[str, Any]:
    """
    Run VRAM usage monitoring test

    Args:
        test_dir: Directory containing test audio files
        model: "belle2" or "whisperx"
        output: Output JSON file path
        limit: Maximum number of files to test
        sample_interval_ms: Memory sampling interval in milliseconds

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
    print(f"A/B Test: VRAM Usage Monitoring")
    print(f"Model: {model.upper()}")
    print(f"Test files: {len(audio_files)}")
    print(f"Sampling interval: {sample_interval_ms}ms")
    print(f"{'='*60}\n")

    # Select transcription function
    transcribe_func = transcribe_belle2 if model == "belle2" else transcribe_whisperx

    # Get baseline memory
    baseline_memory = get_initial_gpu_memory()
    print(f"Baseline GPU memory: {baseline_memory['allocated_gb']:.2f} GB allocated, "
          f"{baseline_memory['reserved_gb']:.2f} GB reserved\n")

    # Run tests
    results = []
    max_allocated = 0
    max_reserved = 0

    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")

        # Create memory monitor
        monitor = GPUMemoryMonitor(sample_interval_ms=sample_interval_ms)

        # Start monitoring
        monitor.start()

        # Transcribe
        result = transcribe_func(str(audio_file), language="zh")

        # Stop monitoring and get stats
        memory_stats = monitor.stop()

        if not result["success"]:
            print(f"  ✗ Error: {result['error']}")
            results.append({
                "file": audio_file.name,
                "transcription": result,
                "memory": memory_stats
            })
            continue

        # Track peak memory
        if memory_stats.get("allocated", {}).get("max_gb", 0) > max_allocated:
            max_allocated = memory_stats["allocated"]["max_gb"]
        if memory_stats.get("reserved", {}).get("max_gb", 0) > max_reserved:
            max_reserved = memory_stats["reserved"]["max_gb"]

        print(f"  ✓ Transcribed: {result['segment_count']} segments")

        if memory_stats["gpu_available"]:
            alloc = memory_stats["allocated"]
            print(f"  📊 Memory allocated: {alloc['max_gb']:.2f} GB (peak), {alloc['mean_gb']:.2f} GB (avg)")
            print(f"  📊 Memory reserved: {memory_stats['reserved']['max_gb']:.2f} GB (peak)")
            print(f"  📊 Samples collected: {memory_stats['samples_count']}")
        else:
            print(f"  ⚠️  GPU monitoring not available")

        results.append({
            "file": audio_file.name,
            "transcription": {
                "segment_count": result["segment_count"],
                "transcription_time_s": result["transcription_time_s"]
            },
            "memory": memory_stats
        })

    # Calculate aggregate metrics
    files_with_gpu = [r for r in results if r["memory"]["gpu_available"]]

    if files_with_gpu:
        avg_peak_allocated = sum(r["memory"]["allocated"]["max_gb"] for r in files_with_gpu) / len(files_with_gpu)
        avg_peak_reserved = sum(r["memory"]["reserved"]["max_gb"] for r in files_with_gpu) / len(files_with_gpu)
    else:
        avg_peak_allocated = 0
        avg_peak_reserved = 0

    report = {
        "model": model,
        "test_dir": str(test_path),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "baseline_memory": baseline_memory,
        "test_files_count": len(audio_files),
        "summary": {
            "max_allocated_gb": max_allocated,
            "max_reserved_gb": max_reserved,
            "avg_peak_allocated_gb": avg_peak_allocated,
            "avg_peak_reserved_gb": avg_peak_reserved,
            "files_with_gpu_monitoring": len(files_with_gpu)
        },
        "results": results
    }

    # Save results
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"VRAM Usage Monitoring Complete")
    print(f"Model: {model.upper()}")
    print(f"Files tested: {len(audio_files)}")
    print(f"Files with GPU monitoring: {len(files_with_gpu)}")
    if files_with_gpu:
        print(f"Peak allocated memory: {max_allocated:.2f} GB")
        print(f"Peak reserved memory: {max_reserved:.2f} GB")
        print(f"Average peak allocated: {avg_peak_allocated:.2f} GB")
        print(f"Average peak reserved: {avg_peak_reserved:.2f} GB")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="A/B Test: VRAM usage monitoring for BELLE-2 vs WhisperX"
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
        "--sample-interval",
        type=int,
        default=100,
        help="Memory sampling interval in milliseconds (default: 100ms)"
    )

    args = parser.parse_args()

    run_memory_test(
        test_dir=args.test_dir,
        model=args.model,
        output=args.output,
        limit=args.limit,
        sample_interval_ms=args.sample_interval
    )


if __name__ == "__main__":
    main()
