# Enhancement Pipeline Guide

Story 4.5 introduces the Enhancement Pipeline to orchestrate optional processing
components after base transcription. This document explains how to configure the
pipeline, the available component presets, and how to diagnose issues.

## Overview

The Enhancement Pipeline composes the following modules in configurable order:

1. **Voice Activity Detection (VAD)** – removes silence-only segments.
2. **Timestamp Refiner** – populates char/word timing arrays and adjusts
   boundaries.
3. **Segment Splitter** – enforces subtitle-friendly durations and lengths.

Each component implements telemetry hooks so Celery tasks log per-component
metrics and capture them in transcription metadata.

## Configuration

Settings live in `app.config.Settings` and can be controlled via `.env`:

| Variable | Description | Example |
| --- | --- | --- |
| `ENABLE_ENHANCEMENTS` | Global kill switch. When `false`, the pipeline is skipped and legacy service-level behavior runs. | `ENABLE_ENHANCEMENTS=true` |
| `ENHANCEMENT_PIPELINE` | Comma-separated component names in execution order. Supported values: `vad`, `refine`, `split`. Use `none` or an empty string to disable all components. | `ENHANCEMENT_PIPELINE=vad,refine,split` |

**Examples**

```
# Disable enhancements entirely (raw model segments)
ENABLE_ENHANCEMENTS=false

# Run only VAD (silence removal)
ENABLE_ENHANCEMENTS=true
ENHANCEMENT_PIPELINE=vad

# Timestamp refinement without splitting
ENHANCEMENT_PIPELINE=vad,refine

# No enhancements but keep telemetry scaffolding
ENHANCEMENT_PIPELINE=none
```

### Runtime Behavior

- Celery transcription tasks instantiate the pipeline via
  `create_pipeline()` and execute it immediately after the transcription
  service returns raw segments.
- Components can be reordered or removed without redeploying code.
- Per-component metrics (duration, counts, engine info) are recorded in the job
  result at `stats.enhancement_pipeline` for observability.

## Common Recipes

| Recipe | `ENHANCEMENT_PIPELINE` | Use Case |
| --- | --- | --- |
| **Full Quality** | `vad,refine,split` | Production workloads that need the best readability and timing fidelity. |
| **Low Latency Preview** | `vad` | Quick pre-checks where only silence trimming matters. |
| **Timestamp-Only** | `vad,refine` | Editors that want refined timestamps but control splitting manually. |
| **Raw Output** | `none` (or `ENABLE_ENHANCEMENTS=false`) | Diagnostics, debugging regressions, or benchmarking raw model behavior. |

## Troubleshooting

1. **Pipeline skipped unexpectedly**  
   - Verify `ENABLE_ENHANCEMENTS` is `true`.  
   - Confirm `ENHANCEMENT_PIPELINE` is not empty/`none`.  
   - Check Celery logs for "Enhancement pipeline skipped" messages.

2. **Component failure**  
   - Pipeline logs include `"error"` entries per component.  
   - Failures do **not** stop the pipeline; the system falls back to the
     previous segment list.  
   - Inspect `stats.enhancement_pipeline.component_metrics` to identify the
     failing module and exception message.

3. **Performance exceeds target**  
   - Compare `total_pipeline_time_ms` to transcription time to ensure the
     ≤25% overhead goal (NFR-E4-002).  
   - Disable heavy components (e.g., `split`) or run targeted profiling.

4. **Need reproducible presets**  
   - Encode presets in `.env` or deployment secrets.  
   - Always document the active recipe in release notes or job logs so QA can
     replay the same configuration.

## Updating the Pipeline

1. Modify `.env` or deployment secrets with the new component string.
2. Redeploy Celery workers so the new configuration is picked up.
3. Monitor logs for the new `"pipeline_config"` value to ensure changes
   propagated.
4. Review integration tests in `backend/tests/test_enhancement_pipeline.py`
   before shipping significant behavior updates.

---

For deeper architectural background see:
- `docs/architecture.md` (§Enhancement Component Architecture)
- `docs/sprint-artifacts/tech-spec-epic-4.md`
- Story file `docs/sprint-artifacts/4-5-enhancement-pipeline-composition.md`
