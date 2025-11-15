# Epic Technical Specification: Chinese Transcription Quality Optimization

Date: 2025-11-13 (Updated)
Author: Link, PM (John)
Epic ID: 3
Status: In Progress - Architectural Adjustment Approved

---

## Overview

Epic 3 selects the optimal Chinese transcription model through empirical A/B testing, then implements appropriate timestamp optimization to meet subtitle quality standards. Story 3.1 successfully integrated BELLE-2 to eliminate repetitive "gibberish loops," and Story 3.2b's phase gate validation revealed that WhisperX cannot coexist with BELLE-2 due to PyTorch security requirements (CVE-2025-32434). Rather than assume BELLE-2 superiority, Epic 3 now conducts comprehensive model comparison to make evidence-based architectural decision.

### Architectural Approach

Following user requirements for **evidence-based decisions over assumptions**, Epic 3 adopts a three-phase validation and implementation strategy:

1. **Phase 1 (Stories 3.2a-3.2b): Pluggable Architecture + Dependency Validation** ✅ COMPLETE
   - ✅ Implemented `TimestampOptimizer` abstract interface enabling multiple optimizer implementations
   - ✅ Validated WhisperX dependency constraints - discovered PyTorch conflict (CVE-2025-32434)
   - ✅ Phase Gate decision: NO-GO for WhisperX optimizer integration with BELLE-2
   - **Key finding:** BELLE-2 and WhisperX mutually exclusive due to PyTorch version requirements

2. **Phase 2 (Story 3.2c): BELLE-2 vs WhisperX Model Comparison** ⏳ NEW - IN PROGRESS
   - Comprehensive A/B testing across all quality dimensions
   - Isolated environment (`.venv-whisperx` with PyTorch 2.6+/CUDA 12.x) for WhisperX evaluation
   - Comparison metrics: CER/WER accuracy, segment length compliance, gibberish elimination, speed, GPU memory
   - Phase Gate decision: Select winner for production deployment

3. **Phase 3 (Stories 3.3-3.5): Optimization Implementation** *(Conditional on Phase 2 winner)*
   - **If BELLE-2 wins:** Self-developed HeuristicOptimizer (VAD, refinement, splitting)
   - **If WhisperX wins:** Leverage WhisperX built-in optimization pipeline
   - Ensures optimal quality regardless of model selection

4. **Phase 4 (Story 3.6): Quality Validation Framework** *(Required)*
   - Automated CER/WER calculation and segment length statistics
   - Works with winning model and its optimization approach

### Key Architectural Decisions

**ADR-001: Pluggable TimestampOptimizer Interface**
- **Decision:** Abstract interface with multiple implementations (WhisperX, Heuristic)
- **Rationale:** Prevents technology lock-in, enables future optimizer upgrades, provides fallback strategy
- **Trade-offs:** +3-5 days implementation time vs. long-term architectural flexibility
- **Status:** ✅ Implemented in Story 3.2a

**ADR-002: Three-Phase Implementation with Phase Gates**
- **Decision:** Validate WhisperX dependencies (3.2b) → A/B test models (3.2c) → Implement winner's optimization
- **Rationale:** Story 3.2b revealed PyTorch conflict making BELLE-2+WhisperX coexistence impossible. Rather than assume BELLE-2 superiority, conduct empirical comparison to select best model for production.
- **Trade-offs:** +3-5 days for A/B testing vs. evidence-based architectural decision
- **Status:** Phase 1 ✅ Complete (3.2a-3.2b), Phase 2 ⏳ In Progress (3.2c)

**ADR-003: Evidence-Based Model Selection Over Assumptions**
- **Decision:** Comprehensive A/B comparison (BELLE-2 vs WhisperX) across all quality dimensions
- **Rationale:** User requirement for "哪个组件效果更好就使用哪个组件" - select objectively superior model rather than defaulting to BELLE-2. WhisperX offers "更加齐全的配套功能" that may eliminate need for Stories 3.3-3.5.
- **Comparison Metrics:** CER/WER accuracy, segment length (1-7s/≤200 chars), gibberish elimination, processing speed, GPU memory efficiency
- **Trade-offs:** Additional validation effort vs. confidence in long-term architecture
- **Status:** ⏳ Story 3.2c in progress
- **Date:** 2025-11-14

## Objectives and Scope

**In Scope:**

- **Pluggable Optimizer Architecture (Story 3.2a):** ✅ COMPLETE - `TimestampOptimizer` abstract interface, `OptimizerFactory` with auto-selection logic, `OPTIMIZER_ENGINE` configuration setting
- **WhisperX Integration Validation (Story 3.2b):** ✅ COMPLETE - Isolated dependency testing, WhisperXOptimizer implementation, Phase Gate decision report (NO-GO: PyTorch conflict)
- **BELLE-2 vs WhisperX Model Comparison (Story 3.2c - NEW):** ⏳ IN PROGRESS - Comprehensive A/B testing across CER/WER accuracy, segment length compliance, gibberish elimination, processing speed, GPU memory efficiency. Isolated `.venv-whisperx` environment with PyTorch 2.6+/CUDA 12.x for WhisperX evaluation. Phase Gate decision: Select winner for production.
- **Heuristic Optimizer - VAD Preprocessing (Story 3.3 - CONDITIONAL):** Voice Activity Detection filtering, silence removal, parameter optimization. *Activates only if BELLE-2 wins Story 3.2c comparison.*
- **Heuristic Optimizer - Timestamp Refinement (Story 3.4 - CONDITIONAL):** Token-level timestamp extraction, energy-based boundary refinement. *Activates only if BELLE-2 wins Story 3.2c comparison.*
- **Heuristic Optimizer - Segment Splitting (Story 3.5 - CONDITIONAL):** Intelligent splitting to meet 1-7 second conventions, Chinese text length estimation. *Activates only if BELLE-2 wins Story 3.2c comparison.*
- **Quality Validation Framework (Story 3.6 - REQUIRED):** Automated CER/WER calculation, segment length statistics, regression testing. Works with winning model from Story 3.2c.

**Out of Scope:**

- **Model routing logic:** Deferred to Epic 4 (BELLE-2 remains default for Chinese)
- **SenseVoice integration:** Deferred to Epic 4 (optimization precedes model sophistication)
- **Performance monitoring dashboard:** Deferred to Epic 4
- **Real-time streaming optimization:** Focus on batch/offline processing
- **Speaker diarization integration:** Future epic consideration
- **Advanced punctuation models:** Use BELLE-2 built-in punctuation

**Success Criteria:**

- **95% of output segments meet length constraints:** 1-7 seconds duration AND <200 characters
- **Segment length reduction ≥20% vs. baseline:** Mean segment duration improves from 8-12s to 5-7s
- **Optimization pipeline overhead <25% of transcription time:** Optimization adds <15 minutes to 1-hour transcription
- **Zero regression in transcription accuracy:** CER/WER maintains or improves vs. Story 3.1 baseline
- **Click-to-timestamp alignment maintains <200ms accuracy:** Timestamp optimization preserves existing functionality
- **Architectural flexibility:** Configuration-driven optimizer selection without code changes

## System Architecture Alignment

### Pluggable Optimizer Architecture (Story 3.2a)

**Component Structure:**

```
app/ai_services/optimization/
├── base.py                 # TimestampOptimizer abstract interface + OptimizationResult
├── factory.py              # OptimizerFactory with auto-selection logic
├── whisperx_optimizer.py   # WhisperX wav2vec2 forced alignment (Story 3.2b)
├── heuristic_optimizer.py  # Self-developed VAD+refinement+splitting (Stories 3.3-3.5)
└── quality_validator.py    # CER/WER calculation, metrics (Story 3.6)
```

**Core Interfaces:**

```python
# app/ai_services/optimization/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class OptimizationResult:
    """Standardized optimizer output"""
    segments: List[Dict[str, Any]]  # Optimized segments with start, end, text, words
    metrics: Dict[str, float]        # Performance metrics (processing_time_ms, segments_optimized)
    optimizer_name: str              # "whisperx" | "heuristic"

class TimestampOptimizer(ABC):
    """Abstract interface for timestamp optimization strategies"""

    @abstractmethod
    def optimize(
        self,
        segments: List[Dict[str, Any]],
        audio_path: str,
        language: str = "zh"
    ) -> OptimizationResult:
        """
        Optimize transcription segments' timestamps and splitting

        Args:
            segments: Raw transcription segments from BELLE-2/faster-whisper
            audio_path: Path to original audio file
            language: Language code (default: "zh" for Chinese)

        Returns:
            OptimizationResult with optimized segments and performance metrics
        """
        pass

    @staticmethod
    @abstractmethod
    def is_available() -> bool:
        """Check if optimizer dependencies are installed and functional"""
        pass
```

**Factory Pattern (Story 3.2a):**

```python
# app/ai_services/optimization/factory.py
from app.config import settings
from .base import TimestampOptimizer
from .whisperx_optimizer import WhisperXOptimizer
from .heuristic_optimizer import HeuristicOptimizer
import logging

logger = logging.getLogger(__name__)

class OptimizerFactory:
    """Factory for creating timestamp optimizer instances"""

    @staticmethod
    def create(engine: str = None) -> TimestampOptimizer:
        """
        Create optimizer instance based on engine configuration

        Args:
            engine: "whisperx" | "heuristic" | "auto" (default from settings)

        Returns:
            TimestampOptimizer instance

        Raises:
            ValueError: If engine is unknown
        """
        engine = engine or settings.OPTIMIZER_ENGINE

        if engine == "whisperx":
            if WhisperXOptimizer.is_available():
                logger.info("Creating WhisperXOptimizer")
                return WhisperXOptimizer()
            else:
                logger.warning("WhisperX unavailable, falling back to HeuristicOptimizer")
                return HeuristicOptimizer()

        elif engine == "heuristic":
            logger.info("Creating HeuristicOptimizer")
            return HeuristicOptimizer()

        elif engine == "auto":
            # Auto-select: Prefer WhisperX, fallback to Heuristic
            if WhisperXOptimizer.is_available():
                logger.info("Auto-selecting WhisperXOptimizer")
                return WhisperXOptimizer()
            else:
                logger.info("Auto-selecting HeuristicOptimizer (WhisperX unavailable)")
                return HeuristicOptimizer()

        else:
            raise ValueError(f"Unknown optimizer engine: {engine}. Valid: whisperx, heuristic, auto")
```

**Configuration (Story 3.2a):**

```python
# app/config.py
class Settings(BaseSettings):
    # Existing settings...

    # Epic 3 Optimization Settings
    OPTIMIZER_ENGINE: str = "auto"  # "whisperx" | "heuristic" | "auto"
    ENABLE_OPTIMIZATION: bool = True  # Feature flag for Epic 3 pipeline

    class Config:
        env_file = ".env"
```

```bash
# .env
OPTIMIZER_ENGINE=auto  # Prefer WhisperX, fallback to Heuristic
ENABLE_OPTIMIZATION=true
```

### WhisperXOptimizer Implementation (Story 3.2b)

**Module:** `app/ai_services/optimization/whisperx_optimizer.py`

**Dependencies:**
```python
# Conditional dependencies - install only if Phase Gate = GO
# See requirements.txt conditional section
whisperx>=3.1.1  # CONDITIONAL: Only if Story 3.2b succeeds
pyannote.audio==3.1.1  # CONDITIONAL: Dependency conflict risk
torch==2.0.1+cu118 OR torch==2.1.0+cu118  # CONDITIONAL: Validated versions
torchaudio==2.0.2 OR torchaudio==2.1.0  # CONDITIONAL: Match torch version
```

**Implementation:**

```python
class WhisperXOptimizer(TimestampOptimizer):
    """WhisperX wav2vec2 forced alignment optimizer"""

    def __init__(self):
        if not self.is_available():
            raise OptimizerUnavailableError(
                "WhisperX dependencies not installed. "
                "Install with: pip install whisperx pyannote.audio"
            )
        import whisperx
        self.whisperx = whisperx
        self.align_model = None  # Lazy-loaded on first optimize() call
        self.align_metadata = None

    @staticmethod
    def is_available() -> bool:
        """Check if WhisperX and pyannote.audio are installed"""
        try:
            import whisperx
            import pyannote.audio
            return True
        except ImportError:
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
            audio_path: Path to audio file for alignment
            language: Language code (default: "zh")

        Returns:
            OptimizationResult with word-aligned segments
        """
        import time
        start_time = time.time()

        # Lazy-load alignment model on first call
        if self.align_model is None:
            self.align_model, self.align_metadata = self.whisperx.load_align_model(
                language_code=language,
                device="cuda"
            )

        # Load audio
        audio = self.whisperx.load_audio(audio_path)

        # Apply forced alignment
        aligned_result = self.whisperx.align(
            segments,
            self.align_model,
            self.align_metadata,
            audio,
            device="cuda",
            return_char_alignments=False
        )

        processing_time_ms = (time.time() - start_time) * 1000

        return OptimizationResult(
            segments=aligned_result["segments"],
            metrics={
                "processing_time_ms": processing_time_ms,
                "segments_optimized": len(aligned_result["segments"]),
                "word_count": sum(len(seg.get("words", [])) for seg in aligned_result["segments"])
            },
            optimizer_name="whisperx"
        )
```

**Phase Gate Decision Criteria (Story 3.2b):**

| Criterion | Threshold | Measurement Method |
|-----------|-----------|-------------------|
| **Dependency Installation** | SUCCESS | pyannote.audio + torch + BELLE-2 install without conflicts |
| **GPU Acceleration** | torch.cuda.is_available() == True | GPU compatibility validated |
| **Quality Metrics** | CER/WER ≤ baseline, segment length improvement ≥10% | A/B testing with 10+ test files |
| **Performance** | Optimization overhead <25% of transcription time | Benchmarking with 10 test files |
| **Reliability** | 100% success rate | 10 test runs without exceptions |

**Phase Gate Decision: GO** → Integrate WhisperXOptimizer, defer Stories 3.3-3.5
**Phase Gate Decision: NO-GO** → Proceed with Stories 3.3-3.5 (HeuristicOptimizer)

### HeuristicOptimizer Implementation (Stories 3.3-3.5)

**Module:** `app/ai_services/optimization/heuristic_optimizer.py`

**Dependencies:**
```python
# Always-available dependencies (no conflicts)
webrtcvad==2.0.10
librosa==0.10.1
scipy==1.11.4
numpy>=1.24.0
```

**Implementation:**

```python
class HeuristicOptimizer(TimestampOptimizer):
    """Self-developed heuristic optimizer: VAD + Energy Refinement + Intelligent Splitting"""

    def __init__(self):
        import webrtcvad
        import librosa
        self.vad = webrtcvad.Vad(aggressiveness=2)  # 0-3, default 2
        self.librosa = librosa

    @staticmethod
    def is_available() -> bool:
        """HeuristicOptimizer always available (no dependency conflicts)"""
        return True

    def optimize(
        self,
        segments: List[Dict[str, Any]],
        audio_path: str,
        language: str = "zh"
    ) -> OptimizationResult:
        """
        Apply heuristic optimization pipeline:
        1. VAD Preprocessing (Story 3.3)
        2. Token-level timestamp extraction (Story 3.4)
        3. Energy-based boundary refinement (Story 3.4)
        4. Intelligent segment splitting (Story 3.5)

        Args:
            segments: Raw transcription segments from BELLE-2
            audio_path: Path to audio file for analysis
            language: Language code (default: "zh")

        Returns:
            OptimizationResult with optimized segments
        """
        import time
        start_time = time.time()

        # Step 1: VAD Preprocessing (Story 3.3)
        vad_stats = self._apply_vad_preprocessing(audio_path, segments)

        # Step 2: Token-level timestamps (Story 3.4)
        # Note: BELLE-2 provides word-level timestamps in segment["words"]
        segments_with_tokens = self._extract_token_timestamps(segments)

        # Step 3: Energy-based refinement (Story 3.4)
        refined_segments = self._refine_boundaries_by_energy(segments_with_tokens, audio_path)

        # Step 4: Intelligent splitting (Story 3.5)
        split_segments = self._split_long_segments(refined_segments, language=language)

        processing_time_ms = (time.time() - start_time) * 1000

        return OptimizationResult(
            segments=split_segments,
            metrics={
                "processing_time_ms": processing_time_ms,
                "segments_optimized": len(split_segments),
                "vad_silence_removed_pct": vad_stats["silence_percentage"],
                "segments_split": len(split_segments) - len(segments)
            },
            optimizer_name="heuristic"
        )

    def _apply_vad_preprocessing(self, audio_path: str, segments: List[Dict]) -> Dict:
        """Story 3.3: VAD filtering to remove silence segments"""
        # Implementation details in Story 3.3 technical specification
        pass

    def _extract_token_timestamps(self, segments: List[Dict]) -> List[Dict]:
        """Story 3.4: Extract word-level timestamps from BELLE-2 outputs"""
        # BELLE-2 provides word timestamps in segment["words"]
        pass

    def _refine_boundaries_by_energy(self, segments: List[Dict], audio_path: str) -> List[Dict]:
        """Story 3.4: Refine segment boundaries using audio energy analysis"""
        # Load audio waveform with librosa
        # Analyze energy at segment boundaries
        # Search ±200ms for minimum energy point
        pass

    def _split_long_segments(self, segments: List[Dict], language: str = "zh") -> List[Dict]:
        """Story 3.5: Split segments >7s to meet subtitle conventions"""
        # Chinese text length estimation: char_count * 0.4s
        # Split at natural boundaries (punctuation, pauses)
        # Merge segments <1s when safe
        pass
```

### Quality Validation Framework (Story 3.6)

**Module:** `app/ai_services/optimization/quality_validator.py`

**Shared by BOTH WhisperXOptimizer and HeuristicOptimizer**

```python
class QualityValidator:
    """Quality metrics calculation and regression testing"""

    def __init__(self):
        import jiwer
        self.jiwer = jiwer

    def calculate_metrics(
        self,
        segments: List[Dict[str, Any]],
        reference_text: str = None
    ) -> Dict[str, Any]:
        """
        Calculate quality metrics for optimized segments

        Args:
            segments: Optimized transcription segments
            reference_text: Optional reference transcript for CER/WER calculation

        Returns:
            Dict with CER, WER, segment length statistics, constraint compliance
        """
        metrics = {
            "segment_count": len(segments),
            "segment_length_stats": self._calculate_length_stats(segments),
            "constraint_compliance": self._check_constraints(segments)
        }

        if reference_text:
            hypothesis_text = " ".join(seg["text"] for seg in segments)
            metrics["cer"] = self.jiwer.cer(reference_text, hypothesis_text)
            metrics["wer"] = self.jiwer.wer(reference_text, hypothesis_text)

        return metrics

    def _calculate_length_stats(self, segments: List[Dict]) -> Dict[str, float]:
        """Calculate mean, median, P95 segment lengths"""
        durations = [seg["end"] - seg["start"] for seg in segments]
        char_counts = [len(seg["text"]) for seg in segments]

        return {
            "mean_duration_s": np.mean(durations),
            "median_duration_s": np.median(durations),
            "p95_duration_s": np.percentile(durations, 95),
            "mean_char_count": np.mean(char_counts),
            "median_char_count": np.median(char_counts)
        }

    def _check_constraints(self, segments: List[Dict]) -> Dict[str, float]:
        """Check % of segments meeting 1-7s, <200 char constraints"""
        meets_duration = sum(1 for seg in segments if 1.0 <= (seg["end"] - seg["start"]) <= 7.0)
        meets_char_limit = sum(1 for seg in segments if len(seg["text"]) < 200)
        meets_both = sum(
            1 for seg in segments
            if 1.0 <= (seg["end"] - seg["start"]) <= 7.0 and len(seg["text"]) < 200
        )

        return {
            "pct_1_7_seconds": (meets_duration / len(segments)) * 100,
            "pct_under_200_chars": (meets_char_limit / len(segments)) * 100,
            "pct_meets_both_constraints": (meets_both / len(segments)) * 100
        }
```

### Transcription Pipeline Integration

**Updated Pipeline Flow:**

```
Audio Input → BELLE-2/faster-whisper Transcription →
┌─────────────────────────────────────────────────────┐
│ Optimization Layer (if ENABLE_OPTIMIZATION=true)   │
├─────────────────────────────────────────────────────┤
│ OptimizerFactory.create(engine="auto")             │
│                                                      │
│ IF WhisperXOptimizer.is_available():                │
│   └→ WhisperX wav2vec2 forced alignment            │
│ ELSE:                                                │
│   └→ HeuristicOptimizer:                            │
│      1. VAD Preprocessing                            │
│      2. Token Timestamp Extraction                   │
│      3. Energy-Based Refinement                      │
│      4. Intelligent Segment Splitting                │
└─────────────────────────────────────────────────────┘
→ QualityValidator.calculate_metrics() →
→ Save to /uploads/{job_id}/ → Return to Frontend
```

**File Storage (`/uploads/{job_id}/`):**

```
/uploads/{job_id}/
├── audio.mp3 (original)
├── transcription.json (BELLE-2 raw output)
├── optimized_transcription.json (optimizer output)
├── optimization_metadata.json (optimizer name, metrics, processing time)
├── quality_metrics.json (CER, WER, length stats, constraint compliance)
└── segments_baseline.json (pre-optimization for A/B comparison)
```

**Redis Progress Tracking Updates:**

```python
# Progress messages during optimization
"Applying timestamp optimization..."  # Before OptimizerFactory.create()
"Using WhisperX forced alignment..."  # If WhisperXOptimizer
"Using heuristic optimization..."     # If HeuristicOptimizer
"Validating output quality..."        # QualityValidator
"Optimization complete"               # After pipeline
```

## Non-Functional Requirements

**NFR-001: Performance**
- **Requirement:** Optimization pipeline overhead <25% of transcription time
- **Measurement:** 1-hour audio: 30-60 min transcription + max 15 min optimization
- **Validation:** Benchmarking in Story 3.2b (WhisperX) and Story 3.5 (Heuristic)

**NFR-002: Transcription Quality**
- **Requirement:** 95% of output segments meet 1-7 second, <200 character constraints
- **Measurement:** QualityValidator constraint compliance metrics
- **Validation:** Story 3.6 automated quality metrics

**NFR-003: Accuracy Preservation**
- **Requirement:** Zero regression in transcription accuracy (CER/WER ≤ baseline)
- **Measurement:** QualityValidator CER/WER calculation vs. Story 3.1 baseline
- **Validation:** Story 3.6 regression testing framework

**NFR-004: Architectural Flexibility**
- **Requirement:** Configuration-driven optimizer selection without code changes
- **Measurement:** OPTIMIZER_ENGINE setting changes optimizer at runtime
- **Validation:** Story 3.2a factory pattern unit tests

**NFR-005: Compatibility**
- **Requirement:** Optimization transparent to frontend; existing API contracts unchanged
- **Measurement:** Frontend continues using GET /result/{job_id} without modifications
- **Validation:** Story 3.6 integration tests with existing frontend

**NFR-006: Reliability**
- **Requirement:** OptimizerFactory gracefully falls back if preferred optimizer unavailable
- **Measurement:** "auto" mode falls back to HeuristicOptimizer if WhisperX unavailable
- **Validation:** Story 3.2a factory pattern tests, Story 3.2b dependency validation

## Dependencies and Integrations

### Internal Dependencies

| Component | Dependency | Reason |
|-----------|-----------|--------|
| **OptimizerFactory** | app.config.Settings | Read OPTIMIZER_ENGINE configuration |
| **WhisperXOptimizer** | BELLE-2 transcription segments | Input for forced alignment |
| **HeuristicOptimizer** | BELLE-2 transcription segments | Input for optimization pipeline |
| **QualityValidator** | Optimized segments | Calculate metrics on optimizer output |
| **Transcription Pipeline** | OptimizerFactory | Create optimizer instance |

### External Dependencies

**Always Required:**
```
# Epic 3 core dependencies (no conflicts)
webrtcvad==2.0.10          # VAD for HeuristicOptimizer
librosa==0.10.1            # Audio analysis for HeuristicOptimizer
scipy==1.11.4              # Signal processing
jiwer==3.0.3               # CER/WER calculation
numpy>=1.24.0              # Numerical operations
```

**Conditional (IF Story 3.2b Phase Gate = GO):**
```
# ONLY install if WhisperX integration succeeds
whisperx>=3.1.1
pyannote.audio==3.1.1
torch==2.0.1+cu118 OR torch==2.1.0+cu118
torchaudio==2.0.2 OR torchaudio==2.1.0
lightning==2.3.0
```

**Installation Strategy:**

```bash
# Phase 1: Core dependencies (always install)
pip install webrtcvad==2.0.10 librosa==0.10.1 scipy==1.11.4 jiwer==3.0.3

# Phase 2: WhisperX validation (isolated environment)
# Story 3.2b creates .venv-test for dependency testing

# Phase 3: Production deployment (conditional)
# IF Phase Gate = GO:
pip install whisperx pyannote.audio==3.1.1 torch==2.1.0+cu118 torchaudio==2.1.0 \
  --extra-index-url https://download.pytorch.org/whl/cu118

# IF Phase Gate = NO-GO:
# Continue with core dependencies only (HeuristicOptimizer)
```

### API Contract Extensions

**Existing API (unchanged):**
```
GET /result/{job_id}
Response: {
  "status": "completed",
  "transcription": [...segments...],
  "created_at": "2025-11-13T10:30:00Z"
}
```

**New Metadata (optional in response):**
```
GET /result/{job_id}?include_metadata=true
Response: {
  "status": "completed",
  "transcription": [...optimized segments...],
  "created_at": "2025-11-13T10:30:00Z",
  "optimization_metadata": {
    "optimizer_used": "whisperx",
    "processing_time_ms": 45000,
    "segments_optimized": 120
  },
  "quality_metrics": {
    "segment_count": 120,
    "mean_duration_s": 5.2,
    "pct_meets_both_constraints": 96.7
  }
}
```

## Acceptance Criteria (Authoritative)

### Story 3.2a: Pluggable Optimizer Architecture

1. `app/ai_services/optimization/base.py` defines `TimestampOptimizer` abstract interface with `optimize()` and `is_available()` methods
2. `OptimizationResult` dataclass standardizes optimizer output (segments, metrics, optimizer_name)
3. `app/ai_services/optimization/factory.py` implements `OptimizerFactory.create(engine)` with three modes: "whisperx", "heuristic", "auto"
4. `OPTIMIZER_ENGINE` configuration added to `app/config.py` with default "auto"
5. "auto" mode: Prefers WhisperXOptimizer if available, falls back to HeuristicOptimizer with logging
6. Factory pattern unit tests verify mode selection and fallback logic
7. Documentation updated: architecture.md §704-708 reflects pluggable design
8. Zero disruption to Story 3.1 BELLE-2 integration (optimization layer is post-transcription)

### Story 3.2b: WhisperX Integration Validation Experiment

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

### Story 3.3: Heuristic Optimizer - VAD Preprocessing *(CONDITIONAL)*

1. `app/ai_services/optimization/heuristic_optimizer.py` implements `TimestampOptimizer` interface with VAD preprocessing
2. WebRTC VAD integrated with configurable aggressiveness (0-3)
3. VAD filtering removes silence segments >1s duration, generates statistics (original/filtered duration, silence %)
4. BELLE-2 decoder parameters configurable via environment variables (beam size, temperature)
5. A/B testing framework saves pre-optimization baseline (`segments_baseline.json`) for comparison
6. VAD processing completes in <5 minutes for 1-hour audio
7. Unit tests mock audio files, verify VAD filtering logic
8. Integration test on noisy audio validates silence removal effectiveness

### Story 3.4: Heuristic Optimizer - Timestamp Refinement *(CONDITIONAL)*

1. HeuristicOptimizer extends with timestamp refinement capability
2. Token-level timestamps extracted from BELLE-2 decoder outputs
3. Energy-based refinement analyzes audio waveform using librosa, identifies low-energy boundaries
4. Boundary refinement searches ±200ms for optimal split point (minimum energy)
5. Timestamp alignment maintains <200ms accuracy vs. original BELLE-2 outputs
6. Processing completes in <5 minutes for 500 segments
7. Unit tests mock decoder outputs and waveforms
8. Integration test validates click-to-timestamp functionality after refinement

### Story 3.5: Heuristic Optimizer - Segment Splitting *(CONDITIONAL)*

1. HeuristicOptimizer extends with segment splitting capability
2. Segments >7 seconds split at natural boundaries (punctuation, pauses)
3. Chinese text length estimation implemented (character count × 0.4s)
4. Splitting respects word/sentence boundaries from token timestamps
5. Short segments <1s merged when safe (no interruption of natural flow)
6. 95% of output segments meet 1-7s, <200 char constraints
7. Processing completes in <3 minutes for 500 segments
8. Unit tests cover splitting/merging logic with synthetic segments
9. Integration test on real Chinese audio validates constraint compliance

### Story 3.6: Quality Validation Framework *(REQUIRED)*

1. `quality_validator.py` calculates CER/WER using jiwer library
2. Segment length statistics calculated (mean, median, P95, % meeting constraints)
3. Baseline comparison implemented (CER delta, length improvement %)
4. Regression testing framework compares against stored baseline transcripts
5. Quality metrics stored in `quality_metrics.json`
6. CLI tool provided for manual validation and baseline generation
7. Unit tests verify metric calculations with known inputs
8. Integration test validates Story 3.1 baseline vs. optimized outputs show ≥20% length improvement

## Traceability Mapping

| Story ID | PRD Requirement | Architecture Component | Success Metric |
|----------|----------------|------------------------|----------------|
| **3.2a** | REQ-015 (Optimization Pipeline) | TimestampOptimizer interface, OptimizerFactory | Factory pattern unit tests pass |
| **3.2b** | REQ-015 (Optimization Pipeline) | WhisperXOptimizer | Phase Gate decision report |
| **3.3** | REQ-015 (Optimization Pipeline) | HeuristicOptimizer (VAD) | VAD processing <5 min for 1-hour audio |
| **3.4** | REQ-015 (Optimization Pipeline) | HeuristicOptimizer (Refinement) | Timestamp alignment <200ms accuracy |
| **3.5** | REQ-016 (Subtitle Standards) | HeuristicOptimizer (Splitting) | 95% segments meet 1-7s constraints |
| **3.6** | REQ-017 (Quality Validation) | QualityValidator | CER/WER calculation, length stats |

## Risks, Assumptions, Open Questions

### High-Priority Risks

| Risk | Likelihood | Impact | Mitigation | Owner |
|------|-----------|--------|------------|-------|
| **pyannote.audio dependency conflicts (Story 3.2b)** | 🟡 Medium | 🟡 Medium | Isolated test environment + HeuristicOptimizer fallback | Dev |
| **CUDA version incompatibility (Story 3.2b)** | 🟡 Medium | 🟡 Medium | Test CUDA 11.8 and 12.1 configurations | Dev |
| **Timeline overrun (Phase 1→Phase 2)** | 🟡 Medium | 🟢 Low | Phase Gate at Day 5-8 for early decision | SM/PM |
| **Quality below baseline (either optimizer)** | 🟢 Low | 🔴 High | Mandatory quality validation (Story 3.6) with regression testing | QA |
| **BELLE-2 compatibility breaks (Story 3.2b)** | 🟢 Low | 🔴 High | Validate BELLE-2 + WhisperX in Phase 1 experiment | Dev |
| **Performance overhead >25% (either optimizer)** | 🟢 Low | 🟡 Medium | Benchmarking in Stories 3.2b/3.5, fallback if exceeded | Dev |

### Assumptions

1. **BELLE-2 provides word-level timestamps:** Assumed BELLE-2 decoder outputs include token timestamps for Story 3.4
2. **GPU available for WhisperX:** Assumed CUDA-enabled GPU accessible for wav2vec2 alignment
3. **Chinese text length estimation accuracy:** Assumed 0.4s per character heuristic is sufficient (validated in Story 3.5)
4. **Reference transcripts available for CER/WER:** Optional but preferred for Story 3.6 validation

### Open Questions

1. **Q:** Should Phase Gate decision require user approval or be automated based on objective criteria?
   - **A (from Sprint Change Proposal):** Phase Gate decision meeting with Dev, SM, PM (user) - collaborative decision with user final say

2. **Q:** If WhisperX succeeds, should HeuristicOptimizer still be implemented for A/B comparison?
   - **A (from Sprint Change Proposal):** Deferred to future epic; Stories 3.3-3.5 remain in backlog for potential future implementation

3. **Q:** Should optimization be applied to non-Chinese languages (English, etc.)?
   - **A:** Deferred to Epic 4; Epic 3 focuses on Chinese optimization only

## Test Strategy Summary

### Unit Testing

**Story 3.2a: Factory Pattern**
- Test OptimizerFactory.create() with all three modes ("whisperx", "heuristic", "auto")
- Test fallback logic when WhisperXOptimizer.is_available() returns False
- Mock WhisperXOptimizer and HeuristicOptimizer for factory tests

**Story 3.2b: WhisperXOptimizer**
- Test WhisperXOptimizer.is_available() with/without dependencies installed
- Mock whisperx.align() for unit testing optimizer logic
- Test exception handling when dependencies unavailable

**Stories 3.3-3.5: HeuristicOptimizer**
- Test each pipeline stage independently (VAD, refinement, splitting)
- Mock audio files, transcription segments, decoder outputs
- Test constraint compliance (1-7s, <200 chars)

**Story 3.6: QualityValidator**
- Test CER/WER calculation with known reference/hypothesis pairs
- Test segment length statistics with synthetic segments
- Test constraint compliance metrics

### Integration Testing

**Story 3.2b: WhisperX E2E**
- Transcribe 10 diverse audio files (5-60 minutes, various speakers)
- Apply WhisperX optimization
- Validate CER/WER, segment length improvement, processing time
- Compare with Story 3.1 baseline

**Stories 3.3-3.5: Heuristic E2E**
- Transcribe same 10 audio files
- Apply HeuristicOptimizer pipeline
- Validate CER/WER, segment length improvement, processing time
- Compare with Story 3.1 baseline

**Story 3.6: Quality Validation E2E**
- Run QualityValidator on both WhisperX and Heuristic outputs
- Generate quality metrics reports
- Validate Epic 3 success criteria achievement (95% constraint compliance, ≥20% length improvement)

### Performance Testing

**Benchmarking (Stories 3.2b, 3.5):**
- 10 test files ranging 5-60 minutes duration
- Measure transcription time, optimization time, total time
- Validate optimization overhead <25% of transcription time
- Measure GPU VRAM usage for WhisperX

**Regression Testing (Story 3.6):**
- Baseline comparison framework
- CER/WER delta vs. Story 3.1
- Segment length improvement percentage
- Automated alerts if metrics degrade

---

**Document Status:** ✅ Updated for Sprint Change Proposal 2025-11-13
**Next Review:** After Story 3.2b Phase Gate Decision
