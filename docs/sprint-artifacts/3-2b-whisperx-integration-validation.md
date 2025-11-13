# Story 3.2b: WhisperX Integration Validation Experiment

Status: ready-for-dev

## Story

As a developer,
I want to validate WhisperX wav2vec2 forced alignment integration feasibility,
So that we can make an informed Phase Gate decision on using mature solutions vs. self-developed optimizers.

## Acceptance Criteria

1. Isolated test environment (`.venv-test`) created with dependency resolution attempts
2. Dependency installation validated: `pyannote.audio==3.1.1` + `torch==2.0.1/2.1.0` + BELLE-2 compatibility
3. `app/ai_services/optimization/whisperx_optimizer.py` implements `TimestampOptimizer` interface
4. `WhisperXOptimizer.is_available()` returns True only if dependencies successfully installed
5. Performance benchmarking: 10 test files, optimization overhead <25% of transcription time
6. Quality A/B testing: CER/WER ≤ baseline, segment length improvement ≥10%
7. BELLE-2 compatibility validated: No regressions in transcription accuracy
8. **Phase Gate Decision Report** generated with GO/NO-GO recommendation
9. IF GO: Integrate WhisperXOptimizer into production pipeline
10. IF NO-GO: Document failure reasons, proceed with Story 3.3 (HeuristicOptimizer)

## Tasks / Subtasks

- [ ] Task 1: Create isolated test environment (AC: #1, #2)
  - [ ] Create `.venv-test` virtual environment separate from main `.venv`
  - [ ] Install torch with CUDA support using NJU mirror for faster downloads: `uv pip install torch==2.1.0+cu118 torchaudio==2.1.0 --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu118/`
  - [ ] Attempt WhisperX installation: `uv pip install whisperx>=3.1.1`
  - [ ] Attempt pyannote.audio installation: `uv pip install pyannote.audio==3.1.1`
  - [ ] Validate torch CUDA compatibility: Test torch==2.0.1+cu118 and torch==2.1.0+cu118
  - [ ] Check for dependency conflicts with existing BELLE-2 setup
  - [ ] Document successful installation command sequence OR document failure reasons
  - [ ] Test GPU availability: `torch.cuda.is_available()` returns True

- [ ] Task 2: Implement WhisperXOptimizer with full functionality (AC: #3, #4)
  - [ ] Update `backend/app/ai_services/optimization/whisperx_optimizer.py`
  - [ ] Implement `is_available()` to check for `whisperx` and `pyannote.audio` imports
  - [ ] Implement `__init__()` with lazy model loading pattern
  - [ ] Implement `optimize()` method using `whisperx.load_align_model()` and `whisperx.align()`
  - [ ] Add proper error handling for missing dependencies with helpful messages
  - [ ] Return `OptimizationResult` with aligned segments, metrics, optimizer_name="whisperx"
  - [ ] Add docstrings explaining WhisperX forced alignment approach

- [ ] Task 3: Create test suite for WhisperXOptimizer (AC: #4)
  - [ ] Create `backend/tests/test_whisperx_optimizer.py`
  - [ ] Test `is_available()` returns True when dependencies installed
  - [ ] Test `is_available()` returns False when dependencies missing (mock import failure)
  - [ ] Test `optimize()` with mocked whisperx.align() for unit testing
  - [ ] Test error handling when dependencies unavailable
  - [ ] Achieve 70%+ coverage for whisperx_optimizer.py

- [ ] Task 4: Create performance benchmarking script (AC: #5)
  - [ ] Create `backend/scripts/benchmark_optimizer.py` CLI tool
  - [ ] Load 10 diverse test audio files (5-60 minutes, various speakers)
  - [ ] For each file: Transcribe with BELLE-2, measure transcription time
  - [ ] For each file: Apply WhisperXOptimizer, measure optimization time
  - [ ] Calculate overhead percentage: (optimization_time / transcription_time) * 100
  - [ ] Validate overhead <25% threshold met
  - [ ] Generate JSON report with timing statistics

- [ ] Task 5: Create quality A/B testing script (AC: #6, #7)
  - [ ] Create `backend/scripts/quality_ab_test.py` CLI tool
  - [ ] For each test file: Transcribe with BELLE-2 (baseline)
  - [ ] For each test file: Transcribe + optimize with WhisperXOptimizer
  - [ ] Calculate segment length statistics: mean, median, P95
  - [ ] Calculate segment length improvement percentage
  - [ ] Calculate CER/WER if reference transcripts available
  - [ ] Validate: CER/WER ≤ baseline, segment length improvement ≥10%
  - [ ] Generate JSON report with quality metrics

- [ ] Task 6: Generate Phase Gate Decision Report (AC: #8, #9, #10)
  - [ ] Create `docs/phase-gate-story-3-2b.md` report
  - [ ] Document dependency installation results (success/failure, conflicts)
  - [ ] Include performance benchmarking results (overhead %, meets threshold?)
  - [ ] Include quality A/B testing results (CER/WER delta, length improvement %)
  - [ ] Include BELLE-2 compatibility validation (any regressions?)
  - [ ] Provide GO/NO-GO recommendation with rationale
  - [ ] If GO: List integration steps for production pipeline
  - [ ] If NO-GO: List failure reasons, recommend Story 3.3 activation

- [ ] Task 7: Integration into production pipeline (AC: #9 - CONDITIONAL ON GO)
  - [ ] Update `backend/requirements.txt` with WhisperX dependencies
  - [ ] Update `backend/app/tasks/transcription.py` to call OptimizerFactory
  - [ ] Add optimization step after BELLE-2 transcription
  - [ ] Update Redis progress messages: "Applying timestamp optimization..."
  - [ ] Store baseline segments for A/B comparison
  - [ ] Save optimization metadata to job folder
  - [ ] Verify OPTIMIZER_ENGINE=auto selects WhisperX successfully
  - [ ] Run integration test: Full transcription workflow with optimization

## Dev Notes

### Story Context and Purpose

**Story 3.2b Position in Epic 3:**

Story 3.2b is the **validation experiment** that determines Epic 3's implementation path. After Story 3.2a established the pluggable optimizer architecture, this story validates whether WhisperX wav2vec2 forced alignment is the right mature solution for timestamp optimization.

- **Story 3.2a** ← Previous: Pluggable Optimizer Architecture (foundation completed, status: review)
- **Story 3.2b** ← **This story**: WhisperX Integration Validation (Phase Gate experiment)
- **Story 3.3-3.5** → Conditional: Heuristic Optimizer (activates ONLY if Phase Gate = NO-GO)
- **Story 3.6** → Required: Quality Validation Framework (works with both optimizer types)

**Critical Phase Gate Decision:**

This story's outcome determines whether:
- **GO:** WhisperX integration succeeds → Skip Stories 3.3-3.5, proceed to Story 3.6
- **NO-GO:** WhisperX has dependency conflicts or quality issues → Implement Stories 3.3-3.5 (HeuristicOptimizer fallback)

The Phase Gate decision is collaborative (Dev, SM, PM) based on objective criteria, not automated.

**Experiment Methodology:**

Unlike typical stories, this is a **validation experiment** with conditional outcomes:
1. **Dependency Validation Phase:** Can WhisperX + pyannote.audio install alongside BELLE-2/torch?
2. **Performance Validation Phase:** Does optimization overhead meet <25% threshold?
3. **Quality Validation Phase:** Does optimization improve segment length ≥10% without accuracy loss?
4. **Decision Phase:** GO/NO-GO based on objective success criteria

[Source: docs/tech-spec-epic-3.md#Overview, lines 16-26; docs/tech-spec-epic-3.md#Phase-Gate-Decision-Criteria, lines 304-316]

### Problem Being Solved

**Current State (Post-Story 3.2a):**

Story 3.2a successfully delivered:
- ✅ `TimestampOptimizer` abstract interface
- ✅ `OptimizerFactory` with auto/fallback logic
- ✅ `WhisperXOptimizer` stub (is_available() returns False, optimize() raises NotImplementedError)
- ✅ `HeuristicOptimizer` stub (is_available() returns True, optimize() pass-through)
- ✅ Configuration settings: OPTIMIZER_ENGINE, ENABLE_OPTIMIZATION
- ✅ Factory pattern unit tests

**NEW CHALLENGE to Validate:**

Story 3.2b must answer critical questions:
1. **Dependency Compatibility:** Can `pyannote.audio==3.1.1` coexist with BELLE-2's torch setup?
2. **Performance:** Does WhisperX alignment overhead stay <25% of transcription time?
3. **Quality:** Does forced alignment improve segment length without breaking accuracy?
4. **Reliability:** Does WhisperX work consistently across diverse audio files?

**Why Validation Experiment Approach?**

Per tech-spec-epic-3.md §33-42 (ADR-002: Two-Phase Implementation with Phase Gate):
- **Risk Mitigation:** WhisperX may conflict with BELLE-2/torch dependencies
- **Cost Optimization:** If WhisperX works, avoid 10-15 days developing HeuristicOptimizer
- **Early Risk Discovery:** Validate mature solution feasibility BEFORE committing to self-development

**Phase Gate Success Criteria (from tech-spec-epic-3.md §304-316):**

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Dependency Installation | SUCCESS | pyannote.audio + torch + BELLE-2 no conflicts |
| GPU Acceleration | torch.cuda.is_available() == True | GPU compatibility validated |
| Quality Metrics | CER/WER ≤ baseline, length ≥10% improvement | A/B test 10+ files |
| Performance | Overhead <25% of transcription time | Benchmark 10 files |
| Reliability | 100% success rate | 10 test runs without exceptions |

[Source: docs/tech-spec-epic-3.md#Phase-Gate-Decision-Criteria, lines 304-316]

### Technical Implementation Approach

**Three-Phase Validation Approach:**

#### Phase 1: Isolated Environment & Dependency Validation

**Create Separate Test Environment:**

Why separate `.venv-test` instead of using existing `.venv`?
- **Risk Isolation:** Avoid breaking existing BELLE-2 setup during experiments
- **Clean Testing:** Validate dependency resolution from scratch
- **Easy Rollback:** Delete `.venv-test` if conflicts found, no impact on main environment

```bash
# Create isolated test environment (Windows Git Bash)
cd E:/Projects/KlipNote/backend
python -m venv .venv-test
source .venv-test/Scripts/activate

# Verify isolation
which python  # Must show: .venv-test/Scripts/python
python --version  # Must show: 3.12.x

# Install core dependencies first (BELLE-2 + torch)
# IMPORTANT: Use NJU mirror for faster torch+CUDA downloads in China
# NJU mirror: https://mirrors.nju.edu.cn/pytorch/whl/cu118/
uv pip install transformers==4.35.2
uv pip install torch==2.1.0+cu118 torchaudio==2.1.0 --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu118/
uv pip install faster-whisper==1.0.3

# Validate BELLE-2 still works
python -c "from transformers import AutoModelForSpeechSeq2Seq; print('BELLE-2 import OK')"

# Attempt WhisperX installation
uv pip install whisperx>=3.1.1

# Attempt pyannote.audio installation
uv pip install pyannote.audio==3.1.1

# Check for conflicts
uv pip check  # Reports any dependency conflicts

# Test GPU availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Performance Note - Mirror Sources:**

For developers in China, use Nanjing University (NJU) mirror to significantly speed up torch+CUDA wheel downloads:
- **NJU Mirror**: `https://mirrors.nju.edu.cn/pytorch/whl/cu118/`
- **Official PyTorch**: `https://download.pytorch.org/whl/cu118` (slower from China)

The mirror provides the same official PyTorch wheels with much faster download speeds. Use `--index-url` instead of `--extra-index-url` to prioritize the mirror.

**Expected Outcomes:**

**Scenario A (Success):**
- All dependencies install without conflicts
- `torch.cuda.is_available()` returns True
- BELLE-2 import test succeeds
- WhisperX import test succeeds
- → Proceed to Phase 2 (Implementation)

**Scenario B (Dependency Conflicts):**
- `pip check` reports version conflicts (e.g., torch 2.0.1 vs 2.1.0)
- Installation fails with incompatibility errors
- → Document failure reasons in Phase Gate report
- → Recommendation: NO-GO, proceed with Story 3.3 (HeuristicOptimizer)

[Source: docs/tech-spec-epic-3.md#WhisperXOptimizer-Implementation, lines 210-302]

#### Phase 2: WhisperXOptimizer Implementation

**Update Stub Implementation:**

Story 3.2a created stub with `raise NotImplementedError`. Replace with full implementation:

```python
# backend/app/ai_services/optimization/whisperx_optimizer.py
from .base import TimestampOptimizer, OptimizationResult
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class WhisperXOptimizer(TimestampOptimizer):
    """
    WhisperX wav2vec2 forced alignment optimizer

    Uses WhisperX's wav2vec2-based alignment model to refine word-level timestamps
    and improve segment boundaries for better subtitle quality.

    Dependencies:
        - whisperx>=3.1.1
        - pyannote.audio==3.1.1
        - torch (CUDA-enabled)

    Performance: ~10-15% overhead vs BELLE-2 transcription time
    Quality: 10-30% segment length improvement, no accuracy loss
    """

    def __init__(self):
        """Initialize WhisperXOptimizer with lazy model loading"""
        if not self.is_available():
            raise RuntimeError(
                "WhisperX dependencies not installed. "
                "Install with: uv pip install whisperx pyannote.audio==3.1.1"
            )

        # Lazy-loaded on first optimize() call
        self.align_model = None
        self.align_metadata = None
        self._whisperx = None

    @staticmethod
    def is_available() -> bool:
        """
        Check if WhisperX and pyannote.audio are installed

        Returns:
            True if dependencies available, False otherwise
        """
        try:
            import whisperx
            import pyannote.audio
            import torch

            # Also verify CUDA is available (WhisperX requires GPU)
            if not torch.cuda.is_available():
                logger.warning(
                    "WhisperX dependencies found but CUDA unavailable. "
                    "WhisperX requires GPU acceleration."
                )
                return False

            return True
        except ImportError as e:
            logger.debug(f"WhisperX unavailable: {e}")
            return False

    def optimize(
        self,
        segments: List[Dict[str, Any]],
        audio_path: str,
        language: str = "zh"
    ) -> OptimizationResult:
        """
        Apply WhisperX wav2vec2 forced alignment for word-level timestamps

        Args:
            segments: Raw transcription segments from BELLE-2
                Format: [{"start": 0.5, "end": 3.2, "text": "..."}]
            audio_path: Path to audio file for alignment
            language: Language code (default: "zh" for Chinese)

        Returns:
            OptimizationResult with:
                - segments: Word-aligned segments with refined timestamps
                - metrics: processing_time_ms, segments_optimized, word_count
                - optimizer_name: "whisperx"

        Raises:
            RuntimeError: If dependencies unavailable or alignment fails
        """
        import time
        start_time = time.time()

        # Lazy-load WhisperX on first call
        if self._whisperx is None:
            import whisperx
            self._whisperx = whisperx

        # Lazy-load alignment model on first call
        if self.align_model is None:
            logger.info(f"Loading WhisperX alignment model for language: {language}")
            self.align_model, self.align_metadata = self._whisperx.load_align_model(
                language_code=language,
                device="cuda"
            )
            logger.info("WhisperX alignment model loaded successfully")

        # Load audio
        audio = self._whisperx.load_audio(audio_path)

        # Apply forced alignment
        logger.info(f"Applying WhisperX forced alignment to {len(segments)} segments")
        aligned_result = self._whisperx.align(
            segments,
            self.align_model,
            self.align_metadata,
            audio,
            device="cuda",
            return_char_alignments=False
        )

        processing_time_ms = (time.time() - start_time) * 1000

        # Count words in aligned segments
        word_count = sum(
            len(seg.get("words", []))
            for seg in aligned_result["segments"]
        )

        logger.info(
            f"WhisperX alignment complete: {len(aligned_result['segments'])} segments, "
            f"{word_count} words, {processing_time_ms:.0f}ms"
        )

        return OptimizationResult(
            segments=aligned_result["segments"],
            metrics={
                "processing_time_ms": processing_time_ms,
                "segments_optimized": len(aligned_result["segments"]),
                "word_count": word_count
            },
            optimizer_name="whisperx"
        )
```

**Key Implementation Details:**

1. **Lazy Model Loading:** Alignment model loaded on first `optimize()` call, not `__init__`
   - Rationale: Avoid GPU memory allocation until actually needed
   - Pattern: Same as BELLE-2 model manager lazy loading from Story 3.1

2. **GPU Requirement:** `is_available()` checks `torch.cuda.is_available()`
   - WhisperX wav2vec2 alignment requires GPU (no CPU fallback)
   - Clear warning logged if dependencies present but CUDA unavailable

3. **Error Handling:** Helpful error messages guide user to installation commands
   - `RuntimeError` with installation instructions if dependencies missing
   - Logs alignment progress for debugging

4. **Performance Tracking:** `processing_time_ms` metric enables benchmarking
   - Used in Task 4 to calculate overhead percentage
   - Validates <25% threshold requirement

[Source: docs/tech-spec-epic-3.md#WhisperXOptimizer-Implementation, lines 226-302]

#### Phase 3: Performance & Quality Validation

**Benchmarking Script (Task 4):**

```python
# backend/scripts/benchmark_optimizer.py
import sys
import time
import json
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.optimization.factory import OptimizerFactory

def benchmark_optimizer(audio_files: list[str], optimizer_engine: str = "whisperx"):
    """
    Benchmark optimizer performance on test audio files

    Args:
        audio_files: List of audio file paths
        optimizer_engine: "whisperx" or "heuristic"

    Returns:
        Dict with benchmarking results
    """
    transcription_service = Belle2Service()
    optimizer = OptimizerFactory.create(engine=optimizer_engine)

    results = []

    for audio_path in audio_files:
        print(f"\nProcessing: {audio_path}")

        # Transcription phase
        transcribe_start = time.time()
        segments = transcription_service.transcribe(audio_path, language="zh")
        transcription_time = time.time() - transcribe_start

        # Optimization phase
        optimize_start = time.time()
        optimization_result = optimizer.optimize(segments, audio_path, language="zh")
        optimization_time = time.time() - optimize_start

        # Calculate overhead percentage
        overhead_pct = (optimization_time / transcription_time) * 100

        file_result = {
            "file": audio_path,
            "transcription_time_s": transcription_time,
            "optimization_time_s": optimization_time,
            "overhead_pct": overhead_pct,
            "segments_before": len(segments),
            "segments_after": len(optimization_result.segments),
            "optimizer": optimization_result.optimizer_name
        }

        results.append(file_result)
        print(f"  Transcription: {transcription_time:.1f}s")
        print(f"  Optimization: {optimization_time:.1f}s")
        print(f"  Overhead: {overhead_pct:.1f}%")

    # Calculate aggregate statistics
    avg_overhead = sum(r["overhead_pct"] for r in results) / len(results)
    max_overhead = max(r["overhead_pct"] for r in results)

    report = {
        "optimizer_engine": optimizer_engine,
        "test_files_count": len(results),
        "results": results,
        "summary": {
            "avg_overhead_pct": avg_overhead,
            "max_overhead_pct": max_overhead,
            "threshold_pct": 25.0,
            "meets_threshold": avg_overhead < 25.0
        }
    }

    return report

if __name__ == "__main__":
    # Test audio files (5-60 minutes, diverse speakers)
    test_files = [
        "test_audio/short_5min.mp3",
        "test_audio/medium_15min.mp3",
        "test_audio/long_60min.mp3",
        # ... add 7 more files
    ]

    report = benchmark_optimizer(test_files, optimizer_engine="whisperx")

    # Save report
    with open("benchmark_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Benchmark Complete")
    print(f"Average Overhead: {report['summary']['avg_overhead_pct']:.1f}%")
    print(f"Threshold: {report['summary']['threshold_pct']}%")
    print(f"Result: {'✓ PASS' if report['summary']['meets_threshold'] else '✗ FAIL'}")
```

**Quality A/B Testing Script (Task 5):**

```python
# backend/scripts/quality_ab_test.py
import sys
import json
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai_services.belle2_service import Belle2Service
from app.ai_services.optimization.factory import OptimizerFactory

def calculate_segment_stats(segments):
    """Calculate segment length statistics"""
    durations = [seg["end"] - seg["start"] for seg in segments]
    char_counts = [len(seg["text"]) for seg in segments]

    return {
        "count": len(segments),
        "mean_duration_s": np.mean(durations),
        "median_duration_s": np.median(durations),
        "p95_duration_s": np.percentile(durations, 95),
        "mean_char_count": np.mean(char_counts),
        "pct_1_7_seconds": (sum(1 for d in durations if 1.0 <= d <= 7.0) / len(durations)) * 100
    }

def quality_ab_test(audio_files: list[str], reference_transcripts: dict = None):
    """
    A/B test quality: baseline vs optimized segments

    Args:
        audio_files: List of audio file paths
        reference_transcripts: Optional dict of {file: reference_text} for CER/WER

    Returns:
        Dict with quality comparison results
    """
    transcription_service = Belle2Service()
    optimizer = OptimizerFactory.create(engine="whisperx")

    results = []

    for audio_path in audio_files:
        print(f"\nProcessing: {audio_path}")

        # Baseline (BELLE-2 only)
        baseline_segments = transcription_service.transcribe(audio_path, language="zh")
        baseline_stats = calculate_segment_stats(baseline_segments)

        # Optimized (BELLE-2 + WhisperX)
        optimized_result = optimizer.optimize(baseline_segments, audio_path, language="zh")
        optimized_stats = calculate_segment_stats(optimized_result.segments)

        # Calculate improvement
        length_improvement_pct = (
            (baseline_stats["mean_duration_s"] - optimized_stats["mean_duration_s"])
            / baseline_stats["mean_duration_s"]
        ) * 100

        file_result = {
            "file": audio_path,
            "baseline": baseline_stats,
            "optimized": optimized_stats,
            "improvement": {
                "mean_duration_reduction_pct": length_improvement_pct,
                "pct_1_7_seconds_delta": optimized_stats["pct_1_7_seconds"] - baseline_stats["pct_1_7_seconds"]
            }
        }

        results.append(file_result)
        print(f"  Baseline mean: {baseline_stats['mean_duration_s']:.2f}s")
        print(f"  Optimized mean: {optimized_stats['mean_duration_s']:.2f}s")
        print(f"  Improvement: {length_improvement_pct:.1f}%")

    # Aggregate statistics
    avg_improvement = np.mean([r["improvement"]["mean_duration_reduction_pct"] for r in results])

    report = {
        "test_files_count": len(results),
        "results": results,
        "summary": {
            "avg_length_improvement_pct": avg_improvement,
            "threshold_pct": 10.0,
            "meets_threshold": avg_improvement >= 10.0
        }
    }

    return report

if __name__ == "__main__":
    test_files = [
        "test_audio/short_5min.mp3",
        "test_audio/medium_15min.mp3",
        "test_audio/long_60min.mp3",
        # ... add 7 more files
    ]

    report = quality_ab_test(test_files)

    with open("quality_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n{'='*50}")
    print(f"Quality A/B Test Complete")
    print(f"Average Improvement: {report['summary']['avg_length_improvement_pct']:.1f}%")
    print(f"Threshold: {report['summary']['threshold_pct']}%")
    print(f"Result: {'✓ PASS' if report['summary']['meets_threshold'] else '✗ FAIL'}")
```

[Source: docs/tech-spec-epic-3.md#Phase-Gate-Decision-Criteria, lines 304-316]

### Learnings from Previous Story

**From Story 3-2a-pluggable-optimizer-architecture (Status: review)**

**Architectural Foundation Established:**

Story 3.2a delivered the complete pluggable optimizer architecture that Story 3.2b builds upon:

1. **TimestampOptimizer Interface Pattern:**
   - Abstract interface with `optimize()` and `is_available()` methods
   - `OptimizationResult` dataclass standardizes output
   - Story 3.2b implements real WhisperX logic, replacing stub's `NotImplementedError`

2. **OptimizerFactory Pattern:**
   - Supports "whisperx", "heuristic", "auto" modes
   - Auto mode: Prefers WhisperX, falls back to Heuristic
   - Story 3.2b makes `WhisperXOptimizer.is_available()` return True (if deps installed)

3. **Configuration Settings:**
   - `OPTIMIZER_ENGINE = "auto"` (default)
   - `ENABLE_OPTIMIZATION = True` (feature flag)
   - Story 3.2b uses these settings in integration testing (Task 7)

**Testing Pattern from Story 3.2a:**

Story 3.2a established testing approach that Story 3.2b extends:
- ✅ Unit tests: Mock external dependencies (no GPU required)
- ✅ pytest framework with fixtures and mocking
- ✅ Coverage target: 70%+ for new modules
- ✅ Test organization: One test file per module

**Story 3.2b Testing Approach:**

- **Unit Tests:** Mock `whisperx.align()` for no-GPU testing (same pattern as Story 3.2a factory tests)
- **Integration Tests:** Use real GPU for benchmarking/quality validation (Tasks 4-5)
- **Conditional Tests:** Mark GPU tests with `@pytest.mark.gpu`, skip if CUDA unavailable

**Key Files Created in Story 3.2a (DO NOT MODIFY):**

```
backend/app/ai_services/optimization/
├── __init__.py                # NO CHANGE: Exports already include WhisperXOptimizer
├── base.py                    # NO CHANGE: Interface unchanged
├── factory.py                 # NO CHANGE: Factory logic unchanged
└── heuristic_optimizer.py     # NO CHANGE: Pass-through stub (Stories 3.3-3.5 activate if NO-GO)
```

**File to UPDATE in Story 3.2b:**

```
backend/app/ai_services/optimization/
└── whisperx_optimizer.py      # MODIFY: Replace stub with full implementation
```

**New Files Created in Story 3.2b:**

```
backend/scripts/
├── benchmark_optimizer.py     # NEW: Performance benchmarking CLI
└── quality_ab_test.py         # NEW: Quality A/B testing CLI

backend/tests/
└── test_whisperx_optimizer.py # NEW: Unit tests for WhisperXOptimizer

docs/
└── phase-gate-story-3-2b.md   # NEW: Phase Gate decision report
```

**Environment Setup from Story 3.2a:**

Story 3.2a uses main `.venv` with uv workflow:
```bash
cd backend
source .venv/Scripts/activate  # CRITICAL: Activate before commands
which python  # Verify: Must show .venv/Scripts/python
```

**Story 3.2b Isolated Environment:**

Create separate `.venv-test` to avoid breaking main environment during experiments:
```bash
cd backend
python -m venv .venv-test  # Separate environment
source .venv-test/Scripts/activate
which python  # Verify: Must show .venv-test/Scripts/python
```

**Why Separate Environment?**
- **Risk Isolation:** Main `.venv` has working BELLE-2 setup (Story 3.1)
- **Clean Testing:** Validate WhisperX dependency resolution from scratch
- **Easy Rollback:** Delete `.venv-test` if conflicts found, no impact on main environment
- **Phase Gate Decision:** If NO-GO, main environment unaffected

[Source: docs/stories/3-2a-pluggable-optimizer-architecture.md#Learnings-from-Previous-Story, lines 330-400]

### Project Structure Notes

**Files to CREATE:**

```
backend/.venv-test/                          # NEW: Isolated test environment (git-ignored)
backend/scripts/benchmark_optimizer.py       # NEW: Performance benchmarking CLI
backend/scripts/quality_ab_test.py           # NEW: Quality A/B testing CLI
backend/tests/test_whisperx_optimizer.py     # NEW: Unit tests for WhisperXOptimizer
docs/phase-gate-story-3-2b.md                # NEW: Phase Gate decision report
```

**Files to MODIFY:**

```
backend/app/ai_services/optimization/whisperx_optimizer.py  # UPDATE: Replace stub with full implementation
backend/requirements.txt                                     # CONDITIONAL: Add WhisperX deps IF GO
backend/app/tasks/transcription.py                           # CONDITIONAL: Integrate optimizer IF GO
```

**Files NOT to Touch:**

```
backend/app/ai_services/optimization/base.py           # NO CHANGE: Interface stable
backend/app/ai_services/optimization/factory.py        # NO CHANGE: Factory logic complete
backend/app/ai_services/optimization/heuristic_optimizer.py  # NO CHANGE: Stories 3.3-3.5 activate if NO-GO
backend/app/ai_services/belle2_service.py              # NO CHANGE: Transcription unchanged
backend/app/config.py                                   # NO CHANGE: Settings already added in 3.2a
backend/.env.example                                    # NO CHANGE: Config examples complete
docs/architecture.md                                    # NO CHANGE: Updated in 3.2a
```

**Conditional Integration (Task 7 - ONLY IF GO):**

If Phase Gate decision is GO, integrate WhisperX into production pipeline:

```python
# backend/app/tasks/transcription.py (MODIFY IF GO)
from app.ai_services.optimization.factory import OptimizerFactory
from app.config import settings

@shared_task
def transcribe_audio(job_id: str, file_path: str):
    # Existing BELLE-2 transcription
    service = Belle2Service()
    segments = service.transcribe(file_path, language="zh")

    # NEW: Optimization step (if enabled)
    if settings.ENABLE_OPTIMIZATION:
        # Save baseline for A/B comparison
        save_baseline_segments(job_id, segments)

        # Update progress
        update_redis_status(job_id, "processing", 60, "Applying timestamp optimization...")

        # Apply optimization
        optimizer = OptimizerFactory.create()  # Uses OPTIMIZER_ENGINE setting
        optimization_result = optimizer.optimize(segments, file_path, language="zh")

        # Save optimization metadata
        save_optimization_metadata(job_id, optimization_result.metrics)

        # Use optimized segments
        segments = optimization_result.segments

    # Save final result
    save_transcription_result(job_id, segments)
    update_redis_status(job_id, "completed", 100, "Processing complete!")
```

**Conditional Dependencies (IF GO):**

```
# backend/requirements.txt (ADD IF GO)
whisperx>=3.1.1
pyannote.audio==3.1.1
torch==2.1.0+cu118
torchaudio==2.1.0
lightning==2.3.0
```

[Source: docs/tech-spec-epic-3.md#Transcription-Pipeline-Integration, lines 494-539]

### Testing Standards Summary

**Unit Tests (Task 3):**

**Test File:** `backend/tests/test_whisperx_optimizer.py`

**Test Cases:**

1. **Test `is_available()` returns True when dependencies installed:**
   - Mock successful `import whisperx` and `import pyannote.audio`
   - Mock `torch.cuda.is_available()` to return True
   - Assert `WhisperXOptimizer.is_available()` returns True

2. **Test `is_available()` returns False when whisperx missing:**
   - Mock `import whisperx` to raise ImportError
   - Assert `WhisperXOptimizer.is_available()` returns False

3. **Test `is_available()` returns False when CUDA unavailable:**
   - Mock successful imports but `torch.cuda.is_available()` returns False
   - Assert `WhisperXOptimizer.is_available()` returns False

4. **Test `optimize()` with mocked whisperx:**
   - Mock `whisperx.load_align_model()` to return mock model
   - Mock `whisperx.align()` to return synthetic aligned segments
   - Call `optimize()` with test segments
   - Assert returns `OptimizationResult` with correct structure
   - Assert `optimizer_name == "whisperx"`

5. **Test error handling when dependencies unavailable:**
   - Mock `is_available()` to return False
   - Assert `__init__()` raises RuntimeError with installation message

**Test Pattern Example:**

```python
# backend/tests/test_whisperx_optimizer.py
import pytest
from unittest.mock import patch, MagicMock
from app.ai_services.optimization.whisperx_optimizer import WhisperXOptimizer

def test_is_available_success():
    """Test is_available() returns True when dependencies installed"""
    with patch('whisperx.__version__', '3.1.1'), \
         patch('pyannote.audio.__version__', '3.1.1'), \
         patch('torch.cuda.is_available', return_value=True):

        assert WhisperXOptimizer.is_available() is True

def test_is_available_no_whisperx():
    """Test is_available() returns False when whisperx missing"""
    with patch('builtins.__import__', side_effect=ImportError("No module named 'whisperx'")):
        assert WhisperXOptimizer.is_available() is False

def test_optimize_with_mock(mocker):
    """Test optimize() with mocked whisperx.align()"""
    # Mock whisperx module
    mock_whisperx = mocker.MagicMock()
    mock_whisperx.load_align_model.return_value = (MagicMock(), MagicMock())
    mock_whisperx.load_audio.return_value = "audio_data"
    mock_whisperx.align.return_value = {
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Test", "words": [{"word": "Test", "start": 0.0, "end": 2.5}]}
        ]
    }

    with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
        optimizer = WhisperXOptimizer()
        optimizer._whisperx = mock_whisperx

        test_segments = [{"start": 0.0, "end": 3.0, "text": "Test"}]
        result = optimizer.optimize(test_segments, "test.mp3", language="zh")

        assert result.optimizer_name == "whisperx"
        assert len(result.segments) == 1
        assert result.metrics["segments_optimized"] == 1
```

**Integration Tests (Tasks 4-5):**

**Performance Benchmarking (Task 4):**
- NOT unit tests - requires real GPU and audio files
- Run as CLI script: `python scripts/benchmark_optimizer.py`
- Mark with `@pytest.mark.gpu` if wrapped in pytest
- Skip if `torch.cuda.is_available()` is False

**Quality A/B Testing (Task 5):**
- NOT unit tests - requires real transcription and optimization
- Run as CLI script: `python scripts/quality_ab_test.py`
- Mark with `@pytest.mark.gpu` if wrapped in pytest
- Uses real BELLE-2 + WhisperX for objective quality comparison

**Coverage Target:**
- `whisperx_optimizer.py`: 70%+ (unit tests cover main logic paths)
- `benchmark_optimizer.py`: No coverage requirement (CLI tool)
- `quality_ab_test.py`: No coverage requirement (CLI tool)

[Source: docs/tech-spec-epic-3.md#Unit-Testing, lines 772-777; docs/architecture.md#Testing-Strategy, lines 980-1244]

### References

- [Source: docs/tech-spec-epic-3.md#Story-3.2b] - Acceptance criteria (lines 669-680)
- [Source: docs/tech-spec-epic-3.md#WhisperXOptimizer-Implementation] - Implementation details (lines 210-302)
- [Source: docs/tech-spec-epic-3.md#Phase-Gate-Decision-Criteria] - Success criteria table (lines 304-316)
- [Source: docs/tech-spec-epic-3.md#ADR-002] - Two-phase implementation rationale (lines 39-42)
- [Source: docs/epics.md#Story-3.2b] - User story and prerequisites (lines 407-428)
- [Source: docs/PRD.md#NFR-005] - Transcription quality requirements (line 79)
- [Source: docs/architecture.md#AI-Service-Abstraction-Strategy] - Interface pattern (lines 650-798)
- [Source: docs/stories/3-2a-pluggable-optimizer-architecture.md#Learnings-from-Previous-Story] - Previous story patterns (lines 330-400)

## Dev Agent Record

### Context Reference

- `.bmad-ephemeral/stories/3-2b-whisperx-integration-validation.context.xml` (Generated: 2025-11-13)

### Agent Model Used

<!-- To be filled by Dev agent -->

### Debug Log References

### Completion Notes List

### File List

## Change Log

**2025-11-13** - Story drafted by SM agent (create-story workflow)
- Created story file for 3-2b-whisperx-integration-validation
- Extracted requirements from tech-spec-epic-3.md (AC lines 669-680, architecture lines 210-316)
- Applied learnings from Story 3.2a (factory pattern, testing approach, environment isolation)
- Defined 7 tasks with detailed phase gate validation approach
- Analyzed previous story (3-2a-pluggable-optimizer-architecture) for continuity
- Emphasized validation experiment methodology and conditional outcomes
- Status: drafted (ready for story-context workflow or direct implementation)
