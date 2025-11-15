#!/usr/bin/env python3
"""
Story 3.2c: Consolidate A/B Test Results

Consolidates results from all 5 A/B tests and generates comprehensive
comparison report between BELLE-2 and WhisperX models.

Usage:
    # After running all 5 tests for both models, consolidate:
    python backend/scripts/consolidate_ab_results.py \
        --belle2-accuracy backend/ab_test_results/belle2_accuracy.json \
        --belle2-segments backend/ab_test_results/belle2_segments.json \
        --belle2-gibberish backend/ab_test_results/belle2_gibberish.json \
        --belle2-performance backend/ab_test_results/belle2_performance.json \
        --belle2-memory backend/ab_test_results/belle2_memory.json \
        --whisperx-accuracy backend/ab_test_results/whisperx_accuracy.json \
        --whisperx-segments backend/ab_test_results/whisperx_segments.json \
        --whisperx-gibberish backend/ab_test_results/whisperx_gibberish.json \
        --whisperx-performance backend/ab_test_results/whisperx_performance.json \
        --whisperx-memory backend/ab_test_results/whisperx_memory.json \
        --output backend/ab_test_results/consolidated_comparison.json
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

def load_json_result(file_path: Optional[str]) -> Optional[Dict]:
    """Load JSON result file"""
    if not file_path:
        return None

    path = Path(file_path)
    if not path.exists():
        print(f"WARNING: File not found: {file_path}")
        return None

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def compare_accuracy(belle2_data: Dict, whisperx_data: Dict) -> Dict[str, Any]:
    """Compare accuracy metrics (CER/WER)"""
    belle2_summary = belle2_data.get("summary", {}) if belle2_data else {}
    whisperx_summary = whisperx_data.get("summary", {}) if whisperx_data else {}

    belle2_cer = belle2_summary.get("avg_cer_percent")
    belle2_wer = belle2_summary.get("avg_wer_percent")
    whisperx_cer = whisperx_summary.get("avg_cer_percent")
    whisperx_wer = whisperx_summary.get("avg_wer_percent")

    comparison = {
        "belle2": {
            "cer_percent": belle2_cer,
            "wer_percent": belle2_wer
        },
        "whisperx": {
            "cer_percent": whisperx_cer,
            "wer_percent": whisperx_wer
        }
    }

    # Determine winner (lower is better for error rates)
    if belle2_cer is not None and whisperx_cer is not None:
        cer_winner = "belle2" if belle2_cer < whisperx_cer else "whisperx"
        cer_improvement = abs(belle2_cer - whisperx_cer)
        comparison["cer_winner"] = cer_winner
        comparison["cer_improvement_pct"] = cer_improvement
    else:
        comparison["cer_winner"] = "unknown"

    if belle2_wer is not None and whisperx_wer is not None:
        wer_winner = "belle2" if belle2_wer < whisperx_wer else "whisperx"
        wer_improvement = abs(belle2_wer - whisperx_wer)
        comparison["wer_winner"] = wer_winner
        comparison["wer_improvement_pct"] = wer_improvement
    else:
        comparison["wer_winner"] = "unknown"

    return comparison


def compare_segments(belle2_data: Dict, whisperx_data: Dict) -> Dict[str, Any]:
    """Compare segment length compliance"""
    belle2_summary = belle2_data.get("summary", {}) if belle2_data else {}
    whisperx_summary = whisperx_data.get("summary", {}) if whisperx_data else {}

    belle2_compliance = belle2_summary.get("avg_compliance_both_pct")
    whisperx_compliance = whisperx_summary.get("avg_compliance_both_pct")
    belle2_mean_duration = belle2_summary.get("avg_mean_duration_s")
    whisperx_mean_duration = whisperx_summary.get("avg_mean_duration_s")

    comparison = {
        "belle2": {
            "compliance_both_pct": belle2_compliance,
            "mean_duration_s": belle2_mean_duration
        },
        "whisperx": {
            "compliance_both_pct": whisperx_compliance,
            "mean_duration_s": whisperx_mean_duration
        }
    }

    # Determine winner (higher compliance is better)
    if belle2_compliance is not None and whisperx_compliance is not None:
        winner = "belle2" if belle2_compliance > whisperx_compliance else "whisperx"
        improvement = abs(belle2_compliance - whisperx_compliance)
        comparison["compliance_winner"] = winner
        comparison["compliance_improvement_pct"] = improvement
        comparison["meets_95pct_threshold"] = {
            "belle2": belle2_compliance >= 95.0,
            "whisperx": whisperx_compliance >= 95.0
        }
    else:
        comparison["compliance_winner"] = "unknown"

    return comparison


def compare_gibberish(belle2_data: Dict, whisperx_data: Dict) -> Dict[str, Any]:
    """Compare gibberish/repetition detection results"""
    belle2_summary = belle2_data.get("summary", {}) if belle2_data else {}
    whisperx_summary = whisperx_data.get("summary", {}) if whisperx_data else {}

    belle2_quality = belle2_summary.get("avg_quality_score")
    whisperx_quality = whisperx_summary.get("avg_quality_score")
    belle2_issues = belle2_summary.get("files_with_major_issues_pct")
    whisperx_issues = whisperx_summary.get("files_with_major_issues_pct")

    comparison = {
        "belle2": {
            "quality_score": belle2_quality,
            "files_with_issues_pct": belle2_issues
        },
        "whisperx": {
            "quality_score": whisperx_quality,
            "files_with_issues_pct": whisperx_issues
        }
    }

    # Determine winner (higher quality score is better)
    if belle2_quality is not None and whisperx_quality is not None:
        winner = "belle2" if belle2_quality > whisperx_quality else "whisperx"
        improvement = abs(belle2_quality - whisperx_quality)
        comparison["quality_winner"] = winner
        comparison["quality_improvement"] = improvement
    else:
        comparison["quality_winner"] = "unknown"

    return comparison


def compare_performance(belle2_data: Dict, whisperx_data: Dict) -> Dict[str, Any]:
    """Compare performance metrics (RTF, throughput)"""
    belle2_summary = belle2_data.get("summary", {}) if belle2_data else {}
    whisperx_summary = whisperx_data.get("summary", {}) if whisperx_data else {}

    belle2_rtf = belle2_summary.get("avg_rtf")
    whisperx_rtf = whisperx_summary.get("avg_rtf")
    belle2_throughput = belle2_summary.get("avg_throughput_x_realtime")
    whisperx_throughput = whisperx_summary.get("avg_throughput_x_realtime")

    comparison = {
        "belle2": {
            "rtf": belle2_rtf,
            "throughput_x_realtime": belle2_throughput,
            "faster_than_realtime": belle2_rtf < 1.0 if belle2_rtf else None
        },
        "whisperx": {
            "rtf": whisperx_rtf,
            "throughput_x_realtime": whisperx_throughput,
            "faster_than_realtime": whisperx_rtf < 1.0 if whisperx_rtf else None
        }
    }

    # Determine winner (lower RTF is better, higher throughput is better)
    if belle2_rtf is not None and whisperx_rtf is not None:
        winner = "belle2" if belle2_rtf < whisperx_rtf else "whisperx"
        speedup = max(belle2_rtf, whisperx_rtf) / min(belle2_rtf, whisperx_rtf)
        comparison["performance_winner"] = winner
        comparison["speedup_factor"] = speedup
    else:
        comparison["performance_winner"] = "unknown"

    return comparison


def compare_memory(belle2_data: Dict, whisperx_data: Dict) -> Dict[str, Any]:
    """Compare VRAM usage"""
    belle2_summary = belle2_data.get("summary", {}) if belle2_data else {}
    whisperx_summary = whisperx_data.get("summary", {}) if whisperx_data else {}

    belle2_peak = belle2_summary.get("max_allocated_gb")
    whisperx_peak = whisperx_summary.get("max_allocated_gb")
    belle2_avg_peak = belle2_summary.get("avg_peak_allocated_gb")
    whisperx_avg_peak = whisperx_summary.get("avg_peak_allocated_gb")

    comparison = {
        "belle2": {
            "peak_allocated_gb": belle2_peak,
            "avg_peak_allocated_gb": belle2_avg_peak
        },
        "whisperx": {
            "peak_allocated_gb": whisperx_peak,
            "avg_peak_allocated_gb": whisperx_avg_peak
        }
    }

    # Determine winner (lower memory usage is better)
    if belle2_peak is not None and whisperx_peak is not None:
        winner = "belle2" if belle2_peak < whisperx_peak else "whisperx"
        memory_diff = abs(belle2_peak - whisperx_peak)
        comparison["memory_winner"] = winner
        comparison["memory_diff_gb"] = memory_diff
    else:
        comparison["memory_winner"] = "unknown"

    return comparison


def calculate_weighted_score(comparisons: Dict) -> Dict[str, Any]:
    """
    Calculate weighted score based on Epic 3 priorities

    Weights (from tech spec):
    - Accuracy (CER/WER): 30%
    - Segment compliance: 25%
    - Gibberish elimination: 20%
    - Performance: 15%
    - Memory efficiency: 10%
    """
    weights = {
        "accuracy": 0.30,
        "segments": 0.25,
        "gibberish": 0.20,
        "performance": 0.15,
        "memory": 0.10
    }

    scores = {"belle2": 0, "whisperx": 0}

    # Accuracy (lower CER/WER is better, normalize to 0-100 scale)
    acc_comp = comparisons.get("accuracy", {})
    if acc_comp.get("cer_winner"):
        winner = acc_comp["cer_winner"]
        scores[winner] += weights["accuracy"] * 50  # 50% of accuracy weight for CER
        scores["belle2" if winner == "whisperx" else "whisperx"] += 0

    if acc_comp.get("wer_winner"):
        winner = acc_comp["wer_winner"]
        scores[winner] += weights["accuracy"] * 50  # 50% of accuracy weight for WER

    # Segment compliance (higher is better)
    seg_comp = comparisons.get("segments", {})
    if seg_comp.get("compliance_winner"):
        winner = seg_comp["compliance_winner"]
        scores[winner] += weights["segments"] * 100

    # Gibberish elimination (higher quality is better)
    gib_comp = comparisons.get("gibberish", {})
    if gib_comp.get("quality_winner"):
        winner = gib_comp["quality_winner"]
        scores[winner] += weights["gibberish"] * 100

    # Performance (lower RTF is better)
    perf_comp = comparisons.get("performance", {})
    if perf_comp.get("performance_winner"):
        winner = perf_comp["performance_winner"]
        scores[winner] += weights["performance"] * 100

    # Memory (lower usage is better)
    mem_comp = comparisons.get("memory", {})
    if mem_comp.get("memory_winner"):
        winner = mem_comp["memory_winner"]
        scores[winner] += weights["memory"] * 100

    # Determine overall winner
    overall_winner = "belle2" if scores["belle2"] > scores["whisperx"] else "whisperx"

    return {
        "weights": weights,
        "scores": scores,
        "overall_winner": overall_winner,
        "score_difference": abs(scores["belle2"] - scores["whisperx"])
    }


def generate_recommendation(comparisons: Dict, weighted_score: Dict) -> Dict[str, str]:
    """Generate final recommendation"""
    winner = weighted_score["overall_winner"]
    score_diff = weighted_score["score_difference"]

    # Determine confidence level
    if score_diff > 20:
        confidence = "high"
        confidence_description = "Clear winner across multiple dimensions"
    elif score_diff > 10:
        confidence = "medium"
        confidence_description = "Winner with moderate advantage"
    else:
        confidence = "low"
        confidence_description = "Very close competition, consider other factors"

    # Generate recommendation text
    recommendation = f"Recommended model: {winner.upper()}"

    # Add reasoning
    reasons = []

    acc_comp = comparisons.get("accuracy", {})
    if acc_comp.get("cer_winner") == winner:
        reasons.append(f"Superior accuracy (lower CER/WER)")

    seg_comp = comparisons.get("segments", {})
    if seg_comp.get("compliance_winner") == winner:
        reasons.append(f"Better segment length compliance")

    gib_comp = comparisons.get("gibberish", {})
    if gib_comp.get("quality_winner") == winner:
        reasons.append(f"Higher transcription quality (less gibberish)")

    perf_comp = comparisons.get("performance", {})
    if perf_comp.get("performance_winner") == winner:
        reasons.append(f"Faster processing (lower RTF)")

    mem_comp = comparisons.get("memory", {})
    if mem_comp.get("memory_winner") == winner:
        reasons.append(f"Lower memory footprint")

    return {
        "recommended_model": winner,
        "confidence": confidence,
        "confidence_description": confidence_description,
        "recommendation": recommendation,
        "reasons": reasons,
        "epic_3_path": f"Proceed with {winner.upper()} as primary transcription model"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Consolidate A/B test results for BELLE-2 vs WhisperX comparison"
    )

    # BELLE-2 results
    parser.add_argument("--belle2-accuracy", help="BELLE-2 accuracy test results JSON")
    parser.add_argument("--belle2-segments", help="BELLE-2 segments test results JSON")
    parser.add_argument("--belle2-gibberish", help="BELLE-2 gibberish test results JSON")
    parser.add_argument("--belle2-performance", help="BELLE-2 performance test results JSON")
    parser.add_argument("--belle2-memory", help="BELLE-2 memory test results JSON")

    # WhisperX results
    parser.add_argument("--whisperx-accuracy", help="WhisperX accuracy test results JSON")
    parser.add_argument("--whisperx-segments", help="WhisperX segments test results JSON")
    parser.add_argument("--whisperx-gibberish", help="WhisperX gibberish test results JSON")
    parser.add_argument("--whisperx-performance", help="WhisperX performance test results JSON")
    parser.add_argument("--whisperx-memory", help="WhisperX memory test results JSON")

    # Output
    parser.add_argument("--output", required=True, help="Output consolidated results JSON")

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("Consolidating A/B Test Results: BELLE-2 vs WhisperX")
    print(f"{'='*60}\n")

    # Load all result files
    belle2_results = {
        "accuracy": load_json_result(args.belle2_accuracy),
        "segments": load_json_result(args.belle2_segments),
        "gibberish": load_json_result(args.belle2_gibberish),
        "performance": load_json_result(args.belle2_performance),
        "memory": load_json_result(args.belle2_memory)
    }

    whisperx_results = {
        "accuracy": load_json_result(args.whisperx_accuracy),
        "segments": load_json_result(args.whisperx_segments),
        "gibberish": load_json_result(args.whisperx_gibberish),
        "performance": load_json_result(args.whisperx_performance),
        "memory": load_json_result(args.whisperx_memory)
    }

    # Perform comparisons
    comparisons = {
        "accuracy": compare_accuracy(belle2_results["accuracy"], whisperx_results["accuracy"]),
        "segments": compare_segments(belle2_results["segments"], whisperx_results["segments"]),
        "gibberish": compare_gibberish(belle2_results["gibberish"], whisperx_results["gibberish"]),
        "performance": compare_performance(belle2_results["performance"], whisperx_results["performance"]),
        "memory": compare_memory(belle2_results["memory"], whisperx_results["memory"])
    }

    # Calculate weighted score
    weighted_score = calculate_weighted_score(comparisons)

    # Generate recommendation
    recommendation = generate_recommendation(comparisons, weighted_score)

    # Build consolidated report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "story": "3.2c - BELLE-2 vs WhisperX Model Comparison",
        "comparisons": comparisons,
        "weighted_score": weighted_score,
        "recommendation": recommendation
    }

    # Save consolidated report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print("CONSOLIDATED COMPARISON SUMMARY")
    print("="*60)
    print(f"\n🏆 Overall Winner: {weighted_score['overall_winner'].upper()}")
    print(f"   BELLE-2 Score: {weighted_score['scores']['belle2']:.1f}")
    print(f"   WhisperX Score: {weighted_score['scores']['whisperx']:.1f}")
    print(f"\n📊 Dimension Winners:")
    print(f"   Accuracy (CER/WER): {comparisons['accuracy'].get('cer_winner', 'unknown').upper()}")
    print(f"   Segment Compliance: {comparisons['segments'].get('compliance_winner', 'unknown').upper()}")
    print(f"   Gibberish Quality: {comparisons['gibberish'].get('quality_winner', 'unknown').upper()}")
    print(f"   Performance (RTF): {comparisons['performance'].get('performance_winner', 'unknown').upper()}")
    print(f"   Memory Efficiency: {comparisons['memory'].get('memory_winner', 'unknown').upper()}")
    print(f"\n💡 Recommendation: {recommendation['recommendation']}")
    print(f"   Confidence: {recommendation['confidence'].upper()} - {recommendation['confidence_description']}")
    print(f"\n   Reasons:")
    for reason in recommendation['reasons']:
        print(f"   • {reason}")
    print(f"\n📁 Report saved to: {output_path}")
    print("="*60 + "\n")

    return report


if __name__ == "__main__":
    main()
