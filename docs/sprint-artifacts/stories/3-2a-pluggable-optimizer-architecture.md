# Story 3.2a: Pluggable Optimizer Architecture

Status: done

## Story

As a system architect,
I want a pluggable timestamp optimization interface,
So that multiple optimizer implementations can coexist and be selected via configuration without code changes.

## Acceptance Criteria

1. `app/ai_services/optimization/base.py` defines `TimestampOptimizer` abstract interface with `optimize()` and `is_available()` methods
2. `OptimizationResult` dataclass standardizes optimizer output (segments, metrics, optimizer_name)
3. `app/ai_services/optimization/factory.py` implements `OptimizerFactory.create(engine)` with three modes: "whisperx", "heuristic", "auto"
4. `OPTIMIZER_ENGINE` configuration added to `app/config.py` with default "auto"
5. "auto" mode: Prefers WhisperXOptimizer if available, falls back to HeuristicOptimizer with logging
6. Factory pattern unit tests verify mode selection and fallback logic
7. Documentation updated: architecture.md §704-708 reflects pluggable design
8. Zero disruption to Story 3.1 BELLE-2 integration (optimization layer is post-transcription)

## Tasks / Subtasks

- [x] Task 1: Create optimization package structure (AC: #1, #2)
  - [x] Create `backend/app/ai_services/optimization/__init__.py`
  - [x] Create `backend/app/ai_services/optimization/base.py`
  - [x] Define `TimestampOptimizer` abstract class with `optimize()` and `is_available()` methods
  - [x] Define `OptimizationResult` dataclass with fields: segments (List[Dict]), metrics (Dict[str, float]), optimizer_name (str)
  - [x] Add docstrings explaining interface contract and return formats
  - [x] Export base classes in `__init__.py`

- [x] Task 2: Implement OptimizerFactory with mode selection (AC: #3, #5)
  - [x] Create `backend/app/ai_services/optimization/factory.py`
  - [x] Implement `OptimizerFactory.create(engine: str = None)` static method
  - [x] Support three modes: "whisperx", "heuristic", "auto"
  - [x] "auto" mode logic: Check `WhisperXOptimizer.is_available()`, prefer WhisperX, fallback to Heuristic with logging
  - [x] Raise `ValueError` for unknown engine strings
  - [x] Add comprehensive docstrings with usage examples

- [x] Task 3: Add configuration settings (AC: #4)
  - [x] Add `OPTIMIZER_ENGINE: str = "auto"` to `backend/app/config.py` Settings class
  - [x] Add `ENABLE_OPTIMIZATION: bool = True` feature flag to `backend/app/config.py`
  - [x] Add example values to `backend/.env.example`: `OPTIMIZER_ENGINE=auto`, `ENABLE_OPTIMIZATION=true`
  - [x] Add config docstrings explaining valid values and behavior

- [x] Task 4: Create stub optimizer implementations (AC: #8)
  - [x] Create `backend/app/ai_services/optimization/whisperx_optimizer.py` with stub class
  - [x] WhisperXOptimizer: Implement `is_available()` returning False (dependencies not installed yet)
  - [x] WhisperXOptimizer: Implement `optimize()` with `raise NotImplementedError("Story 3.2b")`
  - [x] Create `backend/app/ai_services/optimization/heuristic_optimizer.py` with stub class
  - [x] HeuristicOptimizer: Implement `is_available()` returning True (no dependencies)
  - [x] HeuristicOptimizer: Implement `optimize()` returning pass-through segments (no optimization yet)
  - [x] Export optimizers in `optimization/__init__.py`

- [x] Task 5: Write unit tests for factory pattern (AC: #6)
  - [x] Create `backend/tests/test_optimization_factory.py`
  - [x] Test `create(engine="whisperx")` returns WhisperXOptimizer when available
  - [x] Test `create(engine="heuristic")` returns HeuristicOptimizer
  - [x] Test `create(engine="auto")` prefers WhisperX, falls back to Heuristic
  - [x] Test `create(engine="invalid")` raises ValueError with clear message
  - [x] Mock `WhisperXOptimizer.is_available()` for predictable test behavior
  - [x] Verify logging messages for fallback scenarios
  - [x] Achieve 90%+ coverage for factory.py

- [x] Task 6: Update architecture documentation (AC: #7)
  - [x] Read `docs/architecture.md` lines 704-708 (AI Service Abstraction Strategy section)
  - [x] Add new subsection: "Timestamp Optimization Architecture"
  - [x] Document `TimestampOptimizer` interface pattern
  - [x] Document `OptimizerFactory` mode selection logic
  - [x] Explain pluggable design benefits (future-proof, configuration-driven)
  - [x] Add code examples showing optimizer selection flow

## Dev Notes

### Story Context and Purpose

**Story 3.2a Position in Epic 3:**

Story 3.2a is the **architectural foundation** for Epic 3's two-phase optimization strategy. After Story 3.1 (BELLE-2) successfully eliminated repetitive "gibberish loops" in Mandarin transcription, production testing revealed a new quality issue: segments are too long for practical subtitle editing workflows (8-12s average vs. 1-7s industry standard). Epic 3 pivots to address this segmentation quality problem through a pluggable optimization architecture.

- **Story 3.1** ← Previous: BELLE-2 Integration (improved transcription accuracy, revealed segmentation issue)
- **Story 3.2a** ← **This story**: Pluggable Optimizer Architecture (establishes abstraction layer)
- **Story 3.2b** → Next: WhisperX Integration Validation (mature solution validation)
- **Story 3.3-3.5** → Conditional: Heuristic Optimizer (self-developed fallback if WhisperX fails)
- **Story 3.6** → Required: Quality Validation Framework (metrics and regression testing)

**Critical Dependencies:**
- **Prerequisite**: Story 3.1 (BELLE-2 provides transcription segments needing optimization)
- **Enables**: Story 3.2b (WhisperX implementation) AND Stories 3.3-3.5 (Heuristic implementation)
- **Design Principle**: Architecture-first approach prevents technology lock-in

### Problem Being Solved

**Current State (Post-Story 3.1):**

Story 3.1 BELLE-2 integration achieved:
- ✅ Eliminated repetitive "gibberish loops" in Chinese transcription
- ✅ 24-65% CER improvement over WhisperX baseline
- ✅ Stable timestamp alignment (<200ms drift)

**NEW ISSUE Discovered in Production Testing:**
- ❌ Segments too long: 8-12s average, many 10-30+ seconds
- ❌ Industry standard: 1-7s per segment, <200 characters
- ❌ User workflow impact: Difficult to edit, review, and navigate long segments
- ❌ No optimization pipeline exists for timestamp refinement or segment splitting

**Why Pluggable Architecture?**

Per tech-spec-epic-3.md §15-42 (Sprint Change Proposal 2025-11-13), user requirements prioritize **architectural flexibility over technology lock-in**:

1. **Risk Mitigation**: WhisperX may have dependency conflicts with existing BELLE-2/torch setup
2. **Fallback Strategy**: Self-developed HeuristicOptimizer ensures Epic 3 objectives achieved regardless
3. **Future-Proofing**: New optimization techniques can be added without refactoring
4. **Configuration-Driven**: Production can switch optimizers via environment variable, no code deployment

**Solution: Two-Phase Implementation Strategy**

Story 3.2a establishes the foundation that enables:
- **Phase 1 (Stories 3.2a-3.2b)**: Pluggable architecture + WhisperX validation
- **Phase 2 (Stories 3.3-3.5)**: Heuristic optimizer (activates only if Phase 1 fails)
- **Phase 3 (Story 3.6)**: Quality validation (works with both optimizer types)

[Source: docs/tech-spec-epic-3.md#Overview, lines 10-42; docs/tech-spec-epic-3.md#Architectural-Approach, lines 16-26]

### Technical Implementation Approach

**Architecture Pattern: Strategy Pattern with Factory**

Story 3.2a follows the same **AI Service Abstraction Strategy** proven in Story 3.1 (BELLE-2 TranscriptionService), adapted for timestamp optimization:

```python
# NEW: backend/app/ai_services/optimization/base.py
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

[Source: docs/tech-spec-epic-3.md#Core-Interfaces, lines 90-131]

**Factory Pattern for Mode Selection:**

```python
# NEW: backend/app/ai_services/optimization/factory.py
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

[Source: docs/tech-spec-epic-3.md#Factory-Pattern, lines 134-186]

**Configuration Settings:**

```python
# backend/app/config.py (MODIFY)
class Settings(BaseSettings):
    # Existing settings...

    # Epic 3 Optimization Settings
    OPTIMIZER_ENGINE: str = "auto"  # "whisperx" | "heuristic" | "auto"
    ENABLE_OPTIMIZATION: bool = True  # Feature flag for Epic 3 pipeline

    class Config:
        env_file = ".env"
```

```bash
# .env.example (MODIFY)
OPTIMIZER_ENGINE=auto  # Prefer WhisperX, fallback to Heuristic
ENABLE_OPTIMIZATION=true
```

[Source: docs/tech-spec-epic-3.md#Configuration, lines 189-209]

**Stub Optimizer Implementations:**

Story 3.2a creates **stub implementations** to enable factory testing. Actual optimization logic implemented in subsequent stories:

```python
# NEW: backend/app/ai_services/optimization/whisperx_optimizer.py
from .base import TimestampOptimizer, OptimizationResult
from typing import List, Dict, Any

class WhisperXOptimizer(TimestampOptimizer):
    """WhisperX wav2vec2 forced alignment optimizer (Story 3.2b)"""

    @staticmethod
    def is_available() -> bool:
        """Check if WhisperX dependencies installed"""
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
        """Placeholder: Implementation in Story 3.2b"""
        raise NotImplementedError(
            "WhisperXOptimizer implementation pending Story 3.2b. "
            "Use OPTIMIZER_ENGINE=heuristic for now."
        )
```

```python
# NEW: backend/app/ai_services/optimization/heuristic_optimizer.py
from .base import TimestampOptimizer, OptimizationResult
from typing import List, Dict, Any

class HeuristicOptimizer(TimestampOptimizer):
    """Self-developed heuristic optimizer (Stories 3.3-3.5)"""

    @staticmethod
    def is_available() -> bool:
        """HeuristicOptimizer always available (no external dependencies)"""
        return True

    def optimize(
        self,
        segments: List[Dict[str, Any]],
        audio_path: str,
        language: str = "zh"
    ) -> OptimizationResult:
        """Placeholder: Pass-through segments until Stories 3.3-3.5"""
        import time
        start_time = time.time()

        # No optimization yet - return segments unchanged
        processing_time_ms = (time.time() - start_time) * 1000

        return OptimizationResult(
            segments=segments,  # Pass-through
            metrics={
                "processing_time_ms": processing_time_ms,
                "segments_optimized": len(segments)
            },
            optimizer_name="heuristic"
        )
```

[Source: docs/tech-spec-epic-3.md#WhisperXOptimizer-Implementation, lines 210-302; docs/tech-spec-epic-3.md#HeuristicOptimizer-Implementation, lines 317-420]

### Learnings from Previous Story

**From Story 3-1-belle2-integration (Status: review)**

**Architectural Patterns to Reuse:**

1. **Abstract Interface Pattern** (`TranscriptionService` in Story 3.1)
   - Proven successful for BELLE-2 integration
   - Enables drop-in compatibility for multiple implementations
   - **Story 3.2a Application**: `TimestampOptimizer` follows same pattern

2. **Factory Pattern with Fallback** (`select_transcription_service()` in Story 3.1)
   - Try/catch with graceful degradation
   - Logging at warning level for fallbacks
   - Redis status updates for user transparency
   - **Story 3.2a Application**: `OptimizerFactory.create()` uses identical strategy

3. **Configuration-Driven Selection** (`.env` → `config.py` → service init)
   - Environment variables for deployment flexibility
   - Pydantic Settings for type safety
   - **Story 3.2a Application**: `OPTIMIZER_ENGINE` setting mirrors `BELLE2_MODEL_NAME`

**Testing Strategy from Story 3.1:**

- ✅ Unit tests: Mock external dependencies (no GPU/network required)
- ✅ Integration tests: Mark with `@pytest.mark.gpu`, skip if unavailable
- ✅ Coverage target: 70%+ for new modules, 90%+ for critical paths
- ✅ Test organization: One test file per module

**Story 3.2a Testing Approach:**

Story 3.2a is **architecture-only** (no GPU dependencies), so all tests are unit tests:
- Mock `WhisperXOptimizer.is_available()` for predictable factory behavior
- Test all three factory modes: "whisperx", "heuristic", "auto"
- Test fallback logic when WhisperX unavailable
- Test error handling for invalid engine strings
- Verify logging messages at correct levels

**Key Files Created in Story 3.1 (DO NOT MODIFY):**

```
backend/app/ai_services/
├── belle2_service.py          # NO CHANGE: Transcription service unchanged
├── model_manager.py           # NO CHANGE: Optimization doesn't load models
└── base.py                    # NO CHANGE: TranscriptionService interface unchanged
```

**New Packages Created in Story 3.2a:**

```
backend/app/ai_services/optimization/
├── __init__.py                # NEW: Package initialization
├── base.py                    # NEW: TimestampOptimizer interface + OptimizationResult
├── factory.py                 # NEW: OptimizerFactory
├── whisperx_optimizer.py      # NEW: Stub implementation (Story 3.2b completes)
└── heuristic_optimizer.py     # NEW: Pass-through stub (Stories 3.3-3.5 complete)
```

**Environment Setup (from Story 3.1):**

Story 3.1 established uv virtual environment workflow:
```bash
cd backend
source .venv/Scripts/activate  # CRITICAL: Activate before Python commands
which python  # Verify: Must show .venv/Scripts/python
```

**Story 3.2a has NO new dependencies** (pure Python architecture), so no `uv pip install` needed.

[Source: docs/stories/3-1-belle2-integration.md#Learnings-from-Previous-Story, lines 258-294; docs/stories/3-1-belle2-integration.md#File-List, lines 614-630]

### Project Structure Notes

**Files to CREATE:**

```
backend/app/ai_services/optimization/
├── __init__.py                    # NEW: Package initialization, export base classes
├── base.py                        # NEW: TimestampOptimizer interface + OptimizationResult
├── factory.py                     # NEW: OptimizerFactory with mode selection
├── whisperx_optimizer.py          # NEW: Stub (is_available() + NotImplementedError)
└── heuristic_optimizer.py         # NEW: Stub (is_available() + pass-through optimize())

backend/tests/
└── test_optimization_factory.py   # NEW: Unit tests for factory pattern
```

**Files to MODIFY:**

```
backend/app/config.py              # ADD: OPTIMIZER_ENGINE, ENABLE_OPTIMIZATION settings
backend/.env.example               # ADD: OPTIMIZER_ENGINE=auto, ENABLE_OPTIMIZATION=true
docs/architecture.md               # UPDATE: Add "Timestamp Optimization Architecture" section
```

**Files NOT to Touch:**

```
backend/app/ai_services/belle2_service.py       # NO CHANGE: Transcription unchanged
backend/app/ai_services/whisperx_service.py     # NO CHANGE: Existing service
backend/app/ai_services/model_manager.py        # NO CHANGE: No new models
backend/app/ai_services/base.py                 # NO CHANGE: TranscriptionService interface
backend/app/tasks/transcription.py              # NO CHANGE: Integration in Story 3.6
backend/requirements.txt                        # NO CHANGE: No new dependencies
frontend/                                        # NO CHANGE: Backend-only story
```

**Why Story 3.2a Has No Pipeline Integration:**

Story 3.2a establishes **architecture only** (interfaces, factory, stubs). Actual integration into transcription pipeline happens in **Story 3.6** after optimizer implementations are complete and validated:

- **Story 3.2b**: WhisperXOptimizer implementation (or Phase Gate decision NO-GO)
- **Stories 3.3-3.5**: HeuristicOptimizer implementation (if 3.2b fails)
- **Story 3.6**: Integrate OptimizerFactory into `transcription.py`, add QualityValidator

This **architecture-first approach** prevents refactoring if Phase Gate decision changes optimizer strategy.

[Source: docs/tech-spec-epic-3.md#Component-Structure, lines 75-86; docs/architecture.md#Development-Environment-Requirements, lines 115-228]

### Testing Standards Summary

**Unit Tests (Task 5):**

**Test File:** `backend/tests/test_optimization_factory.py`

**Test Cases:**

1. **Test "whisperx" mode with WhisperX available**
   - Mock `WhisperXOptimizer.is_available()` to return True
   - Call `OptimizerFactory.create(engine="whisperx")`
   - Assert returns instance of WhisperXOptimizer
   - Verify info log: "Creating WhisperXOptimizer"

2. **Test "whisperx" mode with WhisperX unavailable (fallback)**
   - Mock `WhisperXOptimizer.is_available()` to return False
   - Call `OptimizerFactory.create(engine="whisperx")`
   - Assert returns instance of HeuristicOptimizer
   - Verify warning log: "WhisperX unavailable, falling back to HeuristicOptimizer"

3. **Test "heuristic" mode**
   - Call `OptimizerFactory.create(engine="heuristic")`
   - Assert returns instance of HeuristicOptimizer
   - Verify info log: "Creating HeuristicOptimizer"

4. **Test "auto" mode with WhisperX available**
   - Mock `WhisperXOptimizer.is_available()` to return True
   - Call `OptimizerFactory.create(engine="auto")`
   - Assert returns instance of WhisperXOptimizer
   - Verify info log: "Auto-selecting WhisperXOptimizer"

5. **Test "auto" mode with WhisperX unavailable**
   - Mock `WhisperXOptimizer.is_available()` to return False
   - Call `OptimizerFactory.create(engine="auto")`
   - Assert returns instance of HeuristicOptimizer
   - Verify info log: "Auto-selecting HeuristicOptimizer (WhisperX unavailable)"

6. **Test invalid engine string**
   - Call `OptimizerFactory.create(engine="invalid")`
   - Assert raises ValueError with message: "Unknown optimizer engine: invalid. Valid: whisperx, heuristic, auto"

7. **Test default engine from settings**
   - Mock `settings.OPTIMIZER_ENGINE = "auto"`
   - Call `OptimizerFactory.create()` (no engine parameter)
   - Assert uses settings value (auto mode behavior)

**Test Pattern Example:**

```python
# backend/tests/test_optimization_factory.py
import pytest
from unittest.mock import patch, MagicMock
from app.ai_services.optimization.factory import OptimizerFactory
from app.ai_services.optimization.whisperx_optimizer import WhisperXOptimizer
from app.ai_services.optimization.heuristic_optimizer import HeuristicOptimizer

def test_create_whisperx_mode_available(caplog):
    """Test whisperx mode returns WhisperXOptimizer when available"""
    with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
        optimizer = OptimizerFactory.create(engine="whisperx")

        assert isinstance(optimizer, WhisperXOptimizer)
        assert "Creating WhisperXOptimizer" in caplog.text

def test_create_whisperx_mode_unavailable_fallback(caplog):
    """Test whisperx mode falls back to Heuristic when unavailable"""
    with patch.object(WhisperXOptimizer, 'is_available', return_value=False):
        optimizer = OptimizerFactory.create(engine="whisperx")

        assert isinstance(optimizer, HeuristicOptimizer)
        assert "WhisperX unavailable, falling back to HeuristicOptimizer" in caplog.text

def test_create_auto_mode_prefers_whisperx(caplog):
    """Test auto mode prefers WhisperX when available"""
    with patch.object(WhisperXOptimizer, 'is_available', return_value=True):
        optimizer = OptimizerFactory.create(engine="auto")

        assert isinstance(optimizer, WhisperXOptimizer)
        assert "Auto-selecting WhisperXOptimizer" in caplog.text

def test_create_invalid_engine_raises_error():
    """Test invalid engine string raises ValueError"""
    with pytest.raises(ValueError) as excinfo:
        OptimizerFactory.create(engine="invalid")

    assert "Unknown optimizer engine: invalid" in str(excinfo.value)
    assert "Valid: whisperx, heuristic, auto" in str(excinfo.value)
```

**Coverage Target:**
- factory.py: 90%+ (all branches tested)
- base.py: 100% (simple dataclass + interface)
- Stub optimizers: 100% (minimal code)

**No Integration Tests:**

Story 3.2a is architecture-only with no GPU/external dependencies. All tests are unit tests. Integration testing happens in:
- **Story 3.2b**: WhisperX implementation integration tests
- **Stories 3.3-3.5**: Heuristic optimizer integration tests
- **Story 3.6**: End-to-end pipeline integration tests

[Source: docs/tech-spec-epic-3.md#Unit-Testing, lines 772-777; docs/architecture.md#Testing-Strategy, lines 806-1071]

### References

- [Source: docs/tech-spec-epic-3.md#Story-3.2a] - Acceptance criteria (lines 658-667)
- [Source: docs/tech-spec-epic-3.md#Pluggable-Optimizer-Architecture] - Architecture design (lines 75-209)
- [Source: docs/tech-spec-epic-3.md#Core-Interfaces] - Interface specifications (lines 90-131)
- [Source: docs/tech-spec-epic-3.md#Architectural-Decisions] - ADR-001 Pluggable Interface rationale (lines 33-42)
- [Source: docs/epics.md#Story-3.2a] - User story and prerequisites (lines 387-402)
- [Source: docs/prd.md#NFR-005] - Transcription quality requirements (line 79)
- [Source: docs/architecture.md#AI-Service-Abstraction-Strategy] - Interface pattern (lines 650-706)
- [Source: docs/architecture.md#Development-Environment-Requirements] - uv virtual environment (lines 115-228)
- [Source: docs/stories/3-1-belle2-integration.md#Learnings-from-Previous-Story] - Previous story patterns (lines 258-294)

## Dev Agent Record

### Context Reference

- `.bmad-ephemeral/stories/3-2a-pluggable-optimizer-architecture.context.xml`

### Agent Model Used

<!-- To be filled by Dev agent -->

### Debug Log References

- 2025-11-13 08:10 — Task 1 plan:
  - Scaffold `backend/app/ai_services/optimization/` with `__init__.py` plus `base.py` to hold shared contracts.
  - Implement `TimestampOptimizer` ABC with `optimize()`/`is_available()` signatures and docstrings that define expectations for inputs and outputs.
  - Add `OptimizationResult` dataclass (segments, metrics, optimizer_name) so all optimizers share one response payload.
  - Re-export the interface + dataclass from `optimization/__init__.py` for easier downstream imports.
- 2025-11-13 09:05 — Implemented Tasks 1-4:
  - Added typed `TimestampSegment`/`WordTiming` structures plus richer docstrings in `optimization/base.py`.
  - Updated `optimization/__init__.py` to re-export interfaces + concrete optimizers for downstream modules.
  - Wrote fallback pipeline in `heuristic_optimizer.py` (pass-through w/ metrics + empty payload validation) and ensured `whisperx_optimizer.py` advertises availability False until Story 3.2b.
  - Implemented `OptimizerFactory` auto/fallback logic and typed config values (`OPTIMIZER_ENGINE`, `ENABLE_OPTIMIZATION`) with docs + `.env.example` defaults.
- 2025-11-13 09:20 — Testing + docs:
  - Added comprehensive factory + heuristic tests covering selection, logging, availability, and error paths (`backend/tests/test_optimization_factory.py`).
  - Updated `docs/architecture.md` with “Timestamp Optimization Architecture” subsection describing the pluggable design and usage example.
  - Ran `uv run --project backend pytest backend/tests/test_optimization_factory.py` (20 passed, coverage report captured).

### Completion Notes List

- 2025-11-13 — Delivered pluggable optimization scaffold:
  - Added typed optimizer contracts (`TimestampSegment`, `OptimizationResult`, `TimestampOptimizer`) and re-exports for downstream imports.
  - Implemented `OptimizerFactory` with `"whisperx"`, `"heuristic"`, `"auto"` modes plus config wiring (`OPTIMIZER_ENGINE`, `ENABLE_OPTIMIZATION` + `.env.example` docs).
  - Stubbed `WhisperXOptimizer` availability detection and pass-through `HeuristicOptimizer` fallback (guards empty payloads, emits metrics).
  - Authored comprehensive factory/unit tests and documented the architecture in `docs/architecture.md`.
  - Tests: `uv run --project backend pytest backend/tests/test_optimization_factory.py` (20 passed, coverage report emitted; broader suite still contains unrelated known failures).

### File List

- `backend/app/ai_services/optimization/base.py`
- `backend/app/ai_services/optimization/__init__.py`
- `backend/app/ai_services/optimization/factory.py`
- `backend/app/ai_services/optimization/heuristic_optimizer.py`
- `backend/app/ai_services/optimization/whisperx_optimizer.py`
- `backend/app/config.py`
- `backend/.env.example`
- `backend/tests/test_optimization_factory.py`
- `docs/architecture.md`
- `docs/sprint-status.yaml`
- `.bmad-ephemeral/stories/3-2a-pluggable-optimizer-architecture.md`

## Change Log

**2025-11-13** - Story drafted by SM agent (create-story workflow)
- Created story file for 3-2a-pluggable-optimizer-architecture
- Extracted requirements from tech-spec-epic-3.md (AC lines 658-667, architecture lines 75-209)
- Applied learnings from Story 3.1 (interface pattern, factory pattern, testing strategy)
- Defined 6 tasks with detailed acceptance criteria mapping
- Analyzed previous story (3-1-belle2-integration) for continuity and patterns to reuse
- Status: drafted (ready for story-context workflow or direct implementation)

**2025-11-13** - Dev implementation session (agent Link)
- Implemented optimizer contracts, factory, config wiring, and stub optimizers with pass-through behavior + availability detection.
- Added full factory/heuristic unit-test suite and documented the timestamp optimization architecture in `docs/architecture.md`.
- Story status moved to `in-progress`; sprint-status updated accordingly.

**2025-11-13** - Ready for review
- Verified all tasks/subtasks, recorded test results, and updated File List & Dev Agent Record.
- Ran `uv run --project backend pytest backend/tests/test_optimization_factory.py` (pass) and attempted full suite (`uv run --project backend pytest`)—fails remain in legacy WhisperX/BELLE-2 tests unrelated to this story (missing `whisperx` attr patch, stale fixtures).
- Story + sprint status moved to `review`.
