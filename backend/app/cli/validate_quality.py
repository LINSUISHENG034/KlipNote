"""
CLI tool for quality validation of transcription models.

Usage:
    python -m app.cli.validate_quality --model belle2 --pipeline "vad,refine,split" --corpus test_audio/
    python -m app.cli.validate_quality --model whisperx --pipeline "none" --corpus test_audio/ --reference reference_transcripts/
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
from app.config import settings

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_reference_transcripts(reference_path: Path) -> Optional[List[EnhancedSegment]]:
    """
    Load reference transcripts from JSON file.

    Args:
        reference_path: Path to reference transcripts JSON file

    Returns:
        List of EnhancedSegment dictionaries, or None if file doesn't exist
    """
    if not reference_path.exists():
        logger.warning(f"Reference file not found: {reference_path}")
        return None

    try:
        with open(reference_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Handle both {"segments": [...]} and [...] formats
            if isinstance(data, dict) and "segments" in data:
                return data["segments"]
            return data
    except Exception as e:
        logger.error(f"Failed to load reference transcripts: {e}")
        return None


def transcribe_file(
    audio_path: Path, model_name: str, language: str = "auto", pipeline: str = "vad,refine,split"
) -> tuple[List[EnhancedSegment], float, float]:
    """
    Transcribe audio file with specified model.

    Args:
        audio_path: Path to audio file
        model_name: Model name ('belle2' or 'whisperx')
        language: Language code or 'auto'
        pipeline: Enhancement pipeline config ("none" to disable, otherwise enables enhancements)

    Returns:
        Tuple of (segments, transcription_time, enhancement_time)
    """
    logger.info(f"Transcribing {audio_path.name} with {model_name}...")

    # Select service based on model name
    if model_name.lower() == "belle2":
        service = Belle2Service()
    elif model_name.lower() == "whisperx":
        service = WhisperXService()
    else:
        raise ValueError(f"Unknown model: {model_name}. Supported: belle2, whisperx")

    # Determine whether to apply enhancements based on pipeline parameter
    apply_enhancements = (pipeline.strip().lower() != "none")

    # Transcribe with enhancements
    result = service.transcribe(str(audio_path), language=language, apply_enhancements=apply_enhancements)

    # Extract segments and timing info from result
    segments = result.get("segments", [])
    metadata = result.get("metadata", {})
    transcription_time = metadata.get("processing_time", 0.0)

    # Enhancement time would be tracked separately in production
    # For now, estimate from pipeline metrics if available
    enhancement_time = 0.0
    if "stats" in result and "pipeline_metrics" in result["stats"]:
        pipeline_metrics = result["stats"]["pipeline_metrics"]
        enhancement_time = pipeline_metrics.get("total_pipeline_time_ms", 0.0) / 1000.0

    return segments, transcription_time, enhancement_time


def main():
    """Main CLI entry point for quality validation."""
    parser = argparse.ArgumentParser(
        description="Validate transcription quality for a model and pipeline configuration"
    )
    parser.add_argument(
        "--model",
        required=True,
        choices=["belle2", "whisperx"],
        help="Transcription model to evaluate",
    )
    parser.add_argument(
        "--pipeline",
        default="vad,refine,split",
        help="Enhancement pipeline configuration (e.g., 'vad,refine,split', 'vad', 'none')",
    )
    parser.add_argument(
        "--corpus",
        required=True,
        type=Path,
        help="Path to audio corpus directory or single audio file",
    )
    parser.add_argument(
        "--reference",
        type=Path,
        help="Path to reference transcripts directory (optional, for CER/WER calculation)",
    )
    parser.add_argument(
        "--language",
        default="auto",
        help="Language code for transcription (default: auto)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output path for metrics JSON file (default: quality_metrics/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

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
        # Find common audio extensions
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

    # Process each audio file
    all_segments = []
    all_references = []
    total_transcription_time = 0.0
    total_enhancement_time = 0.0
    total_audio_duration = 0.0

    for audio_file in audio_files:
        try:
            # Transcribe
            segments, trans_time, enh_time = transcribe_file(
                audio_file, args.model, args.language, args.pipeline
            )
            all_segments.extend(segments)
            total_transcription_time += trans_time
            total_enhancement_time += enh_time

            # Load reference if available
            if args.reference:
                ref_path = args.reference / f"{audio_file.stem}.json"
                ref_segments = load_reference_transcripts(ref_path)
                if ref_segments:
                    all_references.extend(ref_segments)

            # Estimate audio duration from segments
            if segments:
                audio_duration = segments[-1]["end"]
                total_audio_duration += audio_duration

        except Exception as e:
            logger.error(f"Failed to process {audio_file.name}: {e}", exc_info=True)
            continue

    if not all_segments:
        logger.error("No segments transcribed. Exiting.")
        sys.exit(1)

    # Calculate quality metrics
    logger.info("Calculating quality metrics...")
    reference_segments = all_references if all_references else None

    metrics = validator.calculate_quality_metrics(
        segments=all_segments,
        model_name=args.model,
        pipeline_config=args.pipeline,
        reference_segments=reference_segments,
        transcription_time=total_transcription_time,
        enhancement_time=total_enhancement_time,
        language=args.language,
        audio_duration=total_audio_duration,
    )

    # Generate output filename
    from datetime import datetime

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{args.model}_{args.pipeline.replace(',', '-')}_{timestamp}.json"
    output_path = output_dir / output_filename

    # Save metrics to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics.model_dump(), f, indent=2, ensure_ascii=False)

    logger.info(f"Quality metrics saved to: {output_path}")

    # Print summary
    print("\n" + "=" * 80)
    print(f"QUALITY VALIDATION REPORT: {args.model} ({args.pipeline})")
    print("=" * 80)
    print(f"Model: {metrics.model_name}")
    print(f"Pipeline: {metrics.pipeline_config}")
    print(f"Language: {metrics.language or 'auto'}")
    print(f"Audio Duration: {metrics.audio_duration:.1f}s" if metrics.audio_duration else "N/A")
    print()
    print("ACCURACY METRICS:")
    if metrics.cer is not None:
        print(f"  CER (Character Error Rate): {metrics.cer:.4f} ({metrics.cer * 100:.2f}%)")
    else:
        print("  CER: N/A (no reference transcripts)")
    if metrics.wer is not None:
        print(f"  WER (Word Error Rate): {metrics.wer:.4f} ({metrics.wer * 100:.2f}%)")
    else:
        print("  WER: N/A (no reference transcripts)")
    print()
    print("SEGMENT LENGTH STATISTICS:")
    print(f"  Total Segments: {metrics.segment_stats.segment_count}")
    print(f"  Mean Duration: {metrics.segment_stats.mean_duration:.2f}s")
    print(f"  Median Duration: {metrics.segment_stats.median_duration:.2f}s")
    print(f"  P95 Duration: {metrics.segment_stats.p95_duration:.2f}s")
    print(f"  Duration Compliance (1-7s): {metrics.segment_stats.duration_compliance_pct:.1f}%")
    print(f"  Too Short (<1s): {metrics.segment_stats.too_short_count}")
    print(f"  Too Long (>7s): {metrics.segment_stats.too_long_count}")
    print()
    print("CHARACTER LENGTH STATISTICS:")
    print(f"  Mean Characters: {metrics.char_stats.mean_chars}")
    print(f"  Median Characters: {metrics.char_stats.median_chars}")
    print(f"  P95 Characters: {metrics.char_stats.p95_chars}")
    print(f"  Character Compliance (≤200): {metrics.char_stats.char_compliance_pct:.1f}%")
    print(f"  Over Limit (>200): {metrics.char_stats.over_limit_count}")
    print()
    print("CHARACTER TIMING COVERAGE:")
    print(
        f"  Segments with char[]: {metrics.char_timing_stats.segments_with_chars}/{metrics.segment_stats.segment_count} ({metrics.char_timing_stats.char_coverage_pct:.1f}%)"
    )
    print(f"  Total Characters: {metrics.char_timing_stats.total_chars}")
    print(f"  Characters with Timing: {metrics.char_timing_stats.chars_with_timing}")
    print()
    print("CONFIDENCE STATISTICS:")
    print(
        f"  Segments with Confidence: {metrics.confidence_stats.segments_with_confidence}/{metrics.segment_stats.segment_count} ({metrics.confidence_stats.confidence_coverage_pct:.1f}%)"
    )
    if metrics.confidence_stats.mean_confidence is not None:
        print(
            f"  Mean Confidence: {metrics.confidence_stats.mean_confidence:.3f} ({metrics.confidence_stats.mean_confidence * 100:.1f}%)"
        )
        print(
            f"  Median Confidence: {metrics.confidence_stats.median_confidence:.3f}" if metrics.confidence_stats.median_confidence else "  Median Confidence: N/A"
        )
    else:
        print("  Mean Confidence: N/A")
    print(
        f"  Low Confidence (<0.7): {metrics.confidence_stats.low_confidence_count} ({metrics.confidence_stats.low_confidence_pct:.1f}%)"
    )
    print()
    print("ENHANCEMENT METRICS:")
    print(f"  Applied: {', '.join(metrics.enhancement_metrics.enhancements_applied) if metrics.enhancement_metrics.enhancements_applied else 'None'}")
    print(
        f"  Segments Modified: {metrics.enhancement_metrics.segments_modified_count}/{metrics.segment_stats.segment_count} ({metrics.enhancement_metrics.modification_rate_pct:.1f}%)"
    )
    print()
    print("PROCESSING TIME:")
    print(f"  Transcription: {metrics.transcription_time:.1f}s")
    print(f"  Enhancement: {metrics.enhancement_time:.1f}s")
    print(f"  Total: {metrics.total_time:.1f}s")
    if metrics.audio_duration:
        rtf = metrics.total_time / metrics.audio_duration
        print(f"  Real-Time Factor: {rtf:.2f}x")
    print("=" * 80)


if __name__ == "__main__":
    main()
