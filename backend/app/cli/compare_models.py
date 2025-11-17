"""
CLI tool for comparing transcription models side-by-side.

Usage:
    python -m app.cli.compare_models --model1 belle2 --model2 whisperx --corpus test_audio/
    python -m app.cli.compare_models --model1 belle2 --model2 whisperx --corpus test_audio/ --reference reference_transcripts/ --pipeline "vad,refine,split"
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.quality import QualityValidator
from app.ai_services.schema import EnhancedSegment
from app.ai_services.whisperx_service import WhisperXService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_reference_transcripts(reference_path: Path) -> Optional[List[EnhancedSegment]]:
    """Load reference transcripts from JSON file."""
    if not reference_path.exists():
        return None

    try:
        with open(reference_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict) and "segments" in data:
                return data["segments"]
            return data
    except Exception as e:
        logger.error(f"Failed to load reference transcripts: {e}")
        return None


def transcribe_corpus_with_model(
    audio_files: List[Path],
    model_name: str,
    pipeline: str,
    language: str,
    reference_dir: Optional[Path],
) -> tuple[List[EnhancedSegment], Optional[List[EnhancedSegment]], float, float, float]:
    """
    Transcribe all audio files with specified model.

    Returns:
        Tuple of (segments, references, trans_time, enh_time, audio_duration)
    """
    logger.info(f"Transcribing {len(audio_files)} files with {model_name}...")

    # Select service
    if model_name.lower() == "belle2":
        service = Belle2Service()
    elif model_name.lower() == "whisperx":
        service = WhisperXService()
    else:
        raise ValueError(f"Unknown model: {model_name}")

    all_segments = []
    all_references = []
    total_trans_time = 0.0
    total_enh_time = 0.0
    total_duration = 0.0

    for audio_file in audio_files:
        try:
            # Transcribe
            result = service.transcribe(
                str(audio_file), language=language, apply_enhancements=True
            )
            segments = result.get("segments", [])
            metadata = result.get("metadata", {})

            all_segments.extend(segments)
            total_trans_time += metadata.get("processing_time", 0.0)

            # Estimate enhancement time
            if "stats" in result and "pipeline_metrics" in result["stats"]:
                pipeline_metrics = result["stats"]["pipeline_metrics"]
                total_enh_time += (
                    pipeline_metrics.get("total_pipeline_time_ms", 0.0) / 1000.0
                )

            # Estimate audio duration
            if segments:
                total_duration += segments[-1]["end"]

            # Load reference if available
            if reference_dir:
                ref_path = reference_dir / f"{audio_file.stem}.json"
                ref_segments = load_reference_transcripts(ref_path)
                if ref_segments:
                    all_references.extend(ref_segments)

        except Exception as e:
            logger.error(f"Failed to process {audio_file.name}: {e}", exc_info=True)
            continue

    references = all_references if all_references else None
    return all_segments, references, total_trans_time, total_enh_time, total_duration


def main():
    """Main CLI entry point for model comparison."""
    parser = argparse.ArgumentParser(
        description="Compare two transcription models side-by-side"
    )
    parser.add_argument(
        "--model1",
        required=True,
        choices=["belle2", "whisperx"],
        help="First model to compare",
    )
    parser.add_argument(
        "--model2",
        required=True,
        choices=["belle2", "whisperx"],
        help="Second model to compare",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Path to audio corpus directory or single audio file",
    )
    parser.add_argument(
        "--pipeline",
        default="vad,refine,split",
        help="Enhancement pipeline configuration to use for both models",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        help="Path to reference transcripts directory (optional, for CER/WER)",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Language code for transcription (default: auto)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for comparison report JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.model1 == args.model2:
        logger.error("Model1 and Model2 must be different")
        sys.exit(1)

    # Determine output directory
    if args.output:
        output_dir = args.output.parent if args.output.is_file() else args.output
    else:
        output_dir = Path("backend/quality_metrics")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect audio files
    if args.corpus.is_file():
        audio_files = [args.corpus]
    elif args.corpus.is_dir():
        audio_files = []
        for ext in ["*.mp3", "*.wav", "*.m4a", "*.ogg", "*.flac"]:
            audio_files.extend(args.corpus.glob(ext))
    else:
        logger.error(f"Corpus path not found: {args.corpus}")
        sys.exit(1)

    if not audio_files:
        logger.error(f"No audio files found in {args.corpus}")
        sys.exit(1)

    logger.info(f"Found {len(audio_files)} audio files to process")

    # Initialize validator
    validator = QualityValidator()

    # Transcribe with Model 1
    logger.info(f"\n{'='*80}")
    logger.info(f"TRANSCRIBING WITH {args.model1.upper()}")
    logger.info(f"{'='*80}")
    (
        model1_segments,
        references,
        model1_trans_time,
        model1_enh_time,
        model1_duration,
    ) = transcribe_corpus_with_model(
        audio_files, args.model1, args.pipeline, args.language, args.reference
    )

    if not model1_segments:
        logger.error(f"No segments from {args.model1}. Exiting.")
        sys.exit(1)

    # Calculate Model 1 metrics
    model1_metrics = validator.calculate_quality_metrics(
        segments=model1_segments,
        model_name=args.model1,
        pipeline_config=args.pipeline,
        reference_segments=references,
        transcription_time=model1_trans_time,
        enhancement_time=model1_enh_time,
        language=args.language,
        audio_duration=model1_duration,
    )

    # Transcribe with Model 2
    logger.info(f"\n{'='*80}")
    logger.info(f"TRANSCRIBING WITH {args.model2.upper()}")
    logger.info(f"{'='*80}")
    (
        model2_segments,
        _,  # references already loaded from model1
        model2_trans_time,
        model2_enh_time,
        model2_duration,
    ) = transcribe_corpus_with_model(
        audio_files, args.model2, args.pipeline, args.language, args.reference
    )

    if not model2_segments:
        logger.error(f"No segments from {args.model2}. Exiting.")
        sys.exit(1)

    # Calculate Model 2 metrics
    model2_metrics = validator.calculate_quality_metrics(
        segments=model2_segments,
        model_name=args.model2,
        pipeline_config=args.pipeline,
        reference_segments=references,
        transcription_time=model2_trans_time,
        enhancement_time=model2_enh_time,
        language=args.language,
        audio_duration=model2_duration,
    )

    # Generate comparison report
    logger.info("\nGenerating comparison report...")
    comparison = validator.compare_models(model1_metrics, model2_metrics)

    # Generate output filename
    from datetime import datetime

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_filename = (
        f"comparison_{args.model1}-vs-{args.model2}_{args.pipeline.replace(',', '-')}_{timestamp}.json"
    )
    output_path = output_dir / output_filename

    # Save comparison to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison.model_dump(), f, indent=2, ensure_ascii=False)

    logger.info(f"Comparison report saved to: {output_path}")

    # Print comparison report
    print("\n" + "=" * 80)
    print(f"MODEL COMPARISON REPORT: {args.model1.upper()} vs {args.model2.upper()}")
    print("=" * 80)
    print(f"Pipeline: {args.pipeline}")
    print(f"Corpus: {len(audio_files)} audio files")
    print(f"Language: {args.language}")
    print()

    # Accuracy comparison
    print("ACCURACY METRICS:")
    print(f"  {'Metric':<25} {args.model1.upper():<20} {args.model2.upper():<20} {'Winner':<10}")
    print(f"  {'-'*25} {'-'*20} {'-'*20} {'-'*10}")

    if model1_metrics.cer is not None and model2_metrics.cer is not None:
        cer1_str = f"{model1_metrics.cer:.4f} ({model1_metrics.cer * 100:.2f}%)"
        cer2_str = f"{model2_metrics.cer:.4f} ({model2_metrics.cer * 100:.2f}%)"
        winner = (
            comparison.cer_comparison.replace("model_a", args.model1)
            .replace("model_b", args.model2)
            .upper()
        )
        print(f"  {'CER (lower=better)':<25} {cer1_str:<20} {cer2_str:<20} {winner:<10}")
    else:
        print(f"  {'CER':<25} {'N/A':<20} {'N/A':<20} {'N/A':<10}")

    if model1_metrics.wer is not None and model2_metrics.wer is not None:
        wer1_str = f"{model1_metrics.wer:.4f} ({model1_metrics.wer * 100:.2f}%)"
        wer2_str = f"{model2_metrics.wer:.4f} ({model2_metrics.wer * 100:.2f}%)"
        winner = (
            comparison.wer_comparison.replace("model_a", args.model1)
            .replace("model_b", args.model2)
            .upper()
        )
        print(f"  {'WER (lower=better)':<25} {wer1_str:<20} {wer2_str:<20} {winner:<10}")
    else:
        print(f"  {'WER':<25} {'N/A':<20} {'N/A':<20} {'N/A':<10}")

    print()

    # Segment quality comparison
    print("SEGMENT QUALITY:")
    print(f"  {'Metric':<30} {args.model1.upper():<20} {args.model2.upper():<20} {'Winner':<10}")
    print(f"  {'-'*30} {'-'*20} {'-'*20} {'-'*10}")

    dur_comp1 = model1_metrics.segment_stats.duration_compliance_pct
    dur_comp2 = model2_metrics.segment_stats.duration_compliance_pct
    dur_winner = (
        comparison.duration_compliance_comparison.replace("model_a", args.model1)
        .replace("model_b", args.model2)
        .upper()
    )
    print(
        f"  {'Duration Compliance (1-7s)':<30} {f'{dur_comp1:.1f}%':<20} {f'{dur_comp2:.1f}%':<20} {dur_winner:<10}"
    )

    char_comp1 = model1_metrics.char_stats.char_compliance_pct
    char_comp2 = model2_metrics.char_stats.char_compliance_pct
    char_winner = (
        comparison.char_compliance_comparison.replace("model_a", args.model1)
        .replace("model_b", args.model2)
        .upper()
    )
    print(
        f"  {'Char Compliance (≤200)':<30} {f'{char_comp1:.1f}%':<20} {f'{char_comp2:.1f}%':<20} {char_winner:<10}"
    )

    print(
        f"  {'Mean Segment Duration':<30} {f'{model1_metrics.segment_stats.mean_duration:.2f}s':<20} {f'{model2_metrics.segment_stats.mean_duration:.2f}s':<20} {'-':<10}"
    )
    print(
        f"  {'Mean Characters':<30} {model1_metrics.char_stats.mean_chars:<20} {model2_metrics.char_stats.mean_chars:<20} {'-':<10}"
    )

    print()

    # Confidence comparison
    print("CONFIDENCE SCORES:")
    print(f"  {'Metric':<30} {args.model1.upper():<20} {args.model2.upper():<20} {'Winner':<10}")
    print(f"  {'-'*30} {'-'*20} {'-'*20} {'-'*10}")

    if (
        model1_metrics.confidence_stats.mean_confidence is not None
        and model2_metrics.confidence_stats.mean_confidence is not None
    ):
        conf1 = model1_metrics.confidence_stats.mean_confidence
        conf2 = model2_metrics.confidence_stats.mean_confidence
        conf_winner = (
            comparison.confidence_comparison.replace("model_a", args.model1)
            .replace("model_b", args.model2)
            .upper()
            if comparison.confidence_comparison
            else "N/A"
        )
        print(
            f"  {'Mean Confidence':<30} {f'{conf1:.3f} ({conf1*100:.1f}%)':<20} {f'{conf2:.3f} ({conf2*100:.1f}%)':<20} {conf_winner:<10}"
        )
    else:
        print(f"  {'Mean Confidence':<30} {'N/A':<20} {'N/A':<20} {'N/A':<10}")

    low_conf1_pct = model1_metrics.confidence_stats.low_confidence_pct
    low_conf2_pct = model2_metrics.confidence_stats.low_confidence_pct
    print(
        f"  {'Low Confidence (<0.7)':<30} {f'{low_conf1_pct:.1f}%':<20} {f'{low_conf2_pct:.1f}%':<20} {'-':<10}"
    )

    print()

    # Processing time comparison
    print("PROCESSING TIME:")
    print(f"  {'Metric':<30} {args.model1.upper():<20} {args.model2.upper():<20}")
    print(f"  {'-'*30} {'-'*20} {'-'*20}")
    print(
        f"  {'Total Time':<30} {f'{model1_metrics.total_time:.1f}s':<20} {f'{model2_metrics.total_time:.1f}s':<20}"
    )
    if model1_metrics.audio_duration and model2_metrics.audio_duration:
        rtf1 = model1_metrics.total_time / model1_metrics.audio_duration
        rtf2 = model2_metrics.total_time / model2_metrics.audio_duration
        print(f"  {'Real-Time Factor':<30} {f'{rtf1:.2f}x':<20} {f'{rtf2:.2f}x':<20}")

    print()

    # Recommendation
    print("=" * 80)
    print("RECOMMENDATION:")
    print(f"  {comparison.recommended_model.replace('model_a', args.model1.upper()).replace('model_b', args.model2.upper())}")
    print(f"  Rationale: {comparison.recommendation_rationale}")
    print("=" * 80)


if __name__ == "__main__":
    main()
