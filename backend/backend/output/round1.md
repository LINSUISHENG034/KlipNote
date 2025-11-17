```bash
PS E:\Projects\KlipNote\backend> uv run python -m app.cli.validate_quality --model belle2 --pipeline "none" --corpus ../tests/fixtures/round1 --language zh
<frozen runpy>:128: RuntimeWarning: 'app.cli.validate_quality' found in sys.modules after import of package 'app.cli', but prior to execution of 'app.cli.validate_quality'; this may result in unpredictable behaviour
2025-11-19 02:25:22,773 - __main__ - INFO - Found 2 audio files to process
2025-11-19 02:25:22,773 - __main__ - INFO - Transcribing mandarin-test.mp3 with belle2...
2025-11-19 02:25:22,774 - app.ai_services.model_manager - INFO - ModelManager initialized (max 2 concurrent models)
2025-11-19 02:25:22,774 - app.ai_services.belle2_service - INFO - Belle2Service initialized (lazy loading): BELLE-2/Belle-whisper-large-v3-zh
2025-11-19 02:25:22,774 - app.ai_services.model_manager - INFO - Loading BELLE-2 model: BELLE-2/Belle-whisper-large-v3-zh on cuda
`torch_dtype` is deprecated! Use `dtype` instead!
2025-11-19 02:25:39,376 - app.ai_services.model_manager - INFO - BELLE-2 model loaded in 16.60s (VRAM: 2.88GB)
2025-11-19 02:25:39,376 - app.ai_services.belle2_service - INFO - Transcribing audio with BELLE-2: ..\tests\fixtures\round1\mandarin-test.mp3
2025-11-19 02:25:42,836 - app.ai_services.belle2_service - INFO - Processing 12 chunks of 30.0s each
The attention mask is not set and cannot be inferred from input because pad token is same as eos token. As a consequence, you may observe unexpected behavior. Please pass your input's `attention_mask` to obtain reliable results.
2025-11-19 02:27:39,175 - app.ai_services.belle2_service - INFO - BELLE-2 transcription complete: 12 segments
2025-11-19 02:27:39,175 - app.ai_services.belle2_service - INFO - Enhancements disabled (apply_enhancements=False, ENABLE_ENHANCEMENTS=True)
2025-11-19 02:27:39,177 - __main__ - INFO - Transcribing zh_short_audio.mp3 with belle2...
2025-11-19 02:27:39,177 - app.ai_services.belle2_service - INFO - Belle2Service initialized (lazy loading): BELLE-2/Belle-whisper-large-v3-zh
2025-11-19 02:27:39,178 - app.ai_services.model_manager - INFO - Using cached BELLE-2 model: BELLE-2/Belle-whisper-large-v3-zh
2025-11-19 02:27:39,178 - app.ai_services.belle2_service - INFO - Transcribing audio with BELLE-2: ..\tests\fixtures\round1\zh_short_audio.mp3
2025-11-19 02:27:39,247 - app.ai_services.belle2_service - INFO - Processing 2 chunks of 30.0s each
2025-11-19 02:27:48,162 - app.ai_services.belle2_service - INFO - BELLE-2 transcription complete: 2 segments
2025-11-19 02:27:48,162 - app.ai_services.belle2_service - INFO - Enhancements disabled (apply_enhancements=False, ENABLE_ENHANCEMENTS=True)
2025-11-19 02:27:48,162 - __main__ - INFO - Calculating quality metrics...
2025-11-19 02:27:48,163 - app.ai_services.quality.validator - INFO - Calculating quality metrics for belle2 with pipeline 'none' on 14 segments
2025-11-19 02:27:48,173 - app.ai_services.quality.validator - INFO - Segment stats: 14 segments, mean=26.78s, median=30.00s, P95=30.00s, compliance=7.1%
2025-11-19 02:27:48,174 - app.ai_services.quality.validator - INFO - Character stats: mean=165, median=187, P95=205, compliance=71.4%
2025-11-19 02:27:48,174 - app.ai_services.quality.validator - INFO - Character timing stats: 0/14 segments (0.0%) have char[] metadata
2025-11-19 02:27:48,174 - app.ai_services.quality.validator - INFO - Confidence stats: 0/14 segments (0.0%) have confidence scores, mean=N/A, low_confidence=0.0%
2025-11-19 02:27:48,175 - app.ai_services.quality.validator - INFO - Enhancement metrics: [], 0/14 segments modified (0.0%)
2025-11-19 02:27:48,175 - app.ai_services.quality.validator - INFO - Quality metrics calculated successfully: belle2
2025-11-19 02:27:48,176 - __main__ - INFO - Quality metrics saved to: backend\quality_metrics\belle2_none_20251118_182748.json

================================================================================
QUALITY VALIDATION REPORT: belle2 (none)
================================================================================
Model: belle2
Pipeline: none
Language: zh
Audio Duration: 375.0s

ACCURACY METRICS:
  CER: N/A (no reference transcripts)
  WER: N/A (no reference transcripts)

SEGMENT LENGTH STATISTICS:
  Total Segments: 14
  Mean Duration: 26.78s
  Median Duration: 30.00s
  P95 Duration: 30.00s
  Duration Compliance (1-7s): 7.1%
  Too Short (<1s): 0
  Too Long (>7s): 13

CHARACTER LENGTH STATISTICS:
  Mean Characters: 165
  Median Characters: 187
  P95 Characters: 205
  Character Compliance (≤200): 71.4%
  Over Limit (>200): 4

CHARACTER TIMING COVERAGE:
  Segments with char[]: 0/14 (0.0%)
  Total Characters: 2322
  Characters with Timing: 0

CONFIDENCE STATISTICS:
  Segments with Confidence: 0/14 (0.0%)
  Mean Confidence: N/A
  Low Confidence (<0.7): 0 (0.0%)

ENHANCEMENT METRICS:
  Applied: None
  Segments Modified: 0/14 (0.0%)

PROCESSING TIME:
  Transcription: 145.4s
  Enhancement: 0.0s
  Total: 145.4s
  Real-Time Factor: 0.39x
================================================================================
PS E:\Projects\KlipNote\backend> 
```