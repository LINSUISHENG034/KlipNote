#!/usr/bin/env python3
"""
Story 3.2c A/B Test: Accuracy Comparison (CER/WER)

Compares transcription accuracy between BELLE-2 and WhisperX models
using Character Error Rate (CER) and Word Error Rate (WER) metrics.

Usage:
    # From project root with main .venv for BELLE-2
    python backend/scripts/ab_test_accuracy.py --test-dir tests/fixtures --model belle2 --output belle2_accuracy.json

    # Switch to .venv-whisperx for WhisperX
    .venv-whisperx/Scripts/activate
    python backend/scripts/ab_test_accuracy.py --test-dir tests/fixtures --model whisperx --output whisperx_accuracy.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
import time

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def calculate_cer_wer(hypothesis: str, reference: str) -> Dict[str, float]:
    """
    Calculate CER and WER between hypothesis and reference texts

    Args:
        hypothesis: Transcribed text from model
        reference: Ground truth text

    Returns:
        Dict with cer and wer scores
    """
    try:
        import jiwer
    except ImportError:
        print("ERROR: jiwer not installed. Install with: pip install jiwer")
        sys.exit(1)

    # Calculate WER (Word Error Rate)
    wer = jiwer.wer(reference, hypothesis)

    # Calculate CER (Character Error Rate)
    cer = jiwer.cer(reference, hypothesis)

    return {
        "cer": cer,
        "wer": wer,
        "cer_percent": cer * 100,
        "wer_percent": wer * 100
    }


def transcribe_belle2(audio_path: str, language: str = "zh") -> Dict[str, Any]:
    """Transcribe audio using BELLE-2 model"""
    from app.ai_services.belle2_service import Belle2Service

    service = Belle2Service()
    start_time = time.time()

    try:
        segments = service.transcribe(audio_path, language=language)
        transcription_time = time.time() - start_time

        # Combine segment texts
        full_text = " ".join(seg["text"] for seg in segments)

        return {
            "model": "belle2",
            "text": full_text,
            "segments": segments,
            "transcription_time_s": transcription_time,
            "segment_count": len(segments),
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "model": "belle2",
            "text": "",
            "segments": [],
            "transcription_time_s": time.time() - start_time,
            "segment_count": 0,
            "success": False,
            "error": str(e)
        }


def transcribe_whisperx(audio_path: str, language: str = "zh") -> Dict[str, Any]:
    """Transcribe audio using WhisperX model"""
    try:
        import whisperx
        import torch
    except ImportError:
        return {
            "model": "whisperx",
            "text": "",
            "segments": [],
            "transcription_time_s": 0,
            "segment_count": 0,
            "success": False,
            "error": "WhisperX not installed. Run in .venv-whisperx environment."
        }

    start_time = time.time()

    try:
        # Load audio
        audio = whisperx.load_audio(audio_path)

        # Load WhisperX model (large-v3 for Chinese)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        compute_type = "float16" if device == "cuda" else "int8"

        model = whisperx.load_model(
            "large-v3",
            device=device,
            compute_type=compute_type,
            language=language
        )

        # Transcribe
        result = model.transcribe(audio, language=language)
        transcription_time = time.time() - start_time

        # Extract text and segments
        segments = result.get("segments", [])
        full_text = " ".join(seg["text"] for seg in segments)

        return {
            "model": "whisperx",
            "text": full_text,
            "segments": segments,
            "transcription_time_s": transcription_time,
            "segment_count": len(segments),
            "device": device,
            "compute_type": compute_type,
            "success": True,
            "error": None
        }
    except Exception as e:
        return {
            "model": "whisperx",
            "text": "",
            "segments": [],
            "transcription_time_s": time.time() - start_time,
            "segment_count": 0,
            "success": False,
            "error": str(e)
        }


def load_ground_truth(test_dir: Path) -> Dict[str, str]:
    """
    Load ground truth transcripts from JSON file

    Expected format:
    {
        "audio_file.mp3": "reference transcript text",
        ...
    }
    """
    ground_truth_file = test_dir / "ground_truth.json"

    if not ground_truth_file.exists():
        # Try alternative format (mandarin-test-reference.txt)
        ref_file = test_dir / "mandarin-test-reference.txt"
        if ref_file.exists():
            with open(ref_file, "r", encoding="utf-8") as f:
                ref_text = f.read().strip()
            return {"mandarin-test.mp3": ref_text}

        print(f"WARNING: No ground truth file found at {ground_truth_file}")
        return {}

    with open(ground_truth_file, "r", encoding="utf-8") as f:
        return json.load(f)


def run_accuracy_test(
    test_dir: str,
    model: str,
    output: str,
    limit: int = None
) -> Dict[str, Any]:
    """
    Run accuracy test for specified model

    Args:
        test_dir: Directory containing test audio files
        model: "belle2" or "whisperx"
        output: Output JSON file path
        limit: Maximum number of files to test (None = all)

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

    # Sort by name for consistency
    audio_files = sorted(audio_files)

    if limit:
        audio_files = audio_files[:limit]

    print(f"\n{'='*60}")
    print(f"A/B Test: Accuracy (CER/WER)")
    print(f"Model: {model.upper()}")
    print(f"Test files: {len(audio_files)}")
    print(f"{'='*60}\n")

    # Load ground truth
    ground_truth = load_ground_truth(test_path)

    # Select transcription function
    transcribe_func = transcribe_belle2 if model == "belle2" else transcribe_whisperx

    # Run tests
    results = []
    total_cer = 0
    total_wer = 0
    valid_comparisons = 0

    for audio_file in audio_files:
        print(f"Processing: {audio_file.name}")

        # Transcribe
        result = transcribe_func(str(audio_file), language="zh")

        if not result["success"]:
            print(f"  ✗ Error: {result['error']}")
            results.append({
                "file": audio_file.name,
                "transcription": result,
                "accuracy": None,
                "has_ground_truth": False
            })
            continue

        print(f"  ✓ Transcribed: {result['segment_count']} segments in {result['transcription_time_s']:.1f}s")

        # Calculate accuracy if ground truth available
        accuracy_metrics = None
        if audio_file.name in ground_truth:
            reference = ground_truth[audio_file.name]
            hypothesis = result["text"]

            accuracy_metrics = calculate_cer_wer(hypothesis, reference)
            total_cer += accuracy_metrics["cer"]
            total_wer += accuracy_metrics["wer"]
            valid_comparisons += 1

            print(f"  📊 CER: {accuracy_metrics['cer_percent']:.2f}% | WER: {accuracy_metrics['wer_percent']:.2f}%")
        else:
            print(f"  ⚠ No ground truth available for {audio_file.name}")

        results.append({
            "file": audio_file.name,
            "transcription": result,
            "accuracy": accuracy_metrics,
            "has_ground_truth": audio_file.name in ground_truth
        })

    # Calculate aggregate metrics
    avg_cer = (total_cer / valid_comparisons * 100) if valid_comparisons > 0 else None
    avg_wer = (total_wer / valid_comparisons * 100) if valid_comparisons > 0 else None

    report = {
        "model": model,
        "test_dir": str(test_path),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "test_files_count": len(audio_files),
        "files_with_ground_truth": valid_comparisons,
        "summary": {
            "avg_cer_percent": avg_cer,
            "avg_wer_percent": avg_wer,
            "valid_comparisons": valid_comparisons
        },
        "results": results
    }

    # Save results
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Accuracy Test Complete")
    print(f"Model: {model.upper()}")
    print(f"Files tested: {len(audio_files)}")
    print(f"Files with ground truth: {valid_comparisons}")
    if avg_cer is not None:
        print(f"Average CER: {avg_cer:.2f}%")
        print(f"Average WER: {avg_wer:.2f}%")
    print(f"Results saved to: {output_path}")
    print(f"{'='*60}\n")

    return report


def main():
    parser = argparse.ArgumentParser(
        description="A/B Test: Accuracy comparison (CER/WER) for BELLE-2 vs WhisperX"
    )
    parser.add_argument(
        "--test-dir",
        default="tests/fixtures",
        help="Directory containing test audio files (default: tests/fixtures)"
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
        help="Output JSON file path (e.g., belle2_accuracy.json)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to test (default: all)"
    )

    args = parser.parse_args()

    run_accuracy_test(
        test_dir=args.test_dir,
        model=args.model,
        output=args.output,
        limit=args.limit
    )


if __name__ == "__main__":
    main()
