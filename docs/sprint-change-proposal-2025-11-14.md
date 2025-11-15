# Sprint Change Proposal: BELLE-2 vs WhisperX Model Selection

**Date:** 2025-11-14
**Epic:** Epic 3 - Chinese Transcription Quality Optimization
**Trigger Story:** 3.2b - WhisperX Integration Validation
**Proposal Status:** PENDING APPROVAL
**Scope Classification:** Moderate - Requires backlog reorganization and Epic 3 redefinition

---

## Section 1: Issue Summary

### Problem Statement

Story 3.2b's phase gate validation revealed that WhisperX cannot coexist with BELLE-2 due to irreconcilable PyTorch dependency conflicts:

- **Security Requirement:** CVE-2025-32434 requires PyTorch ≥2.6
- **WhisperX Dependency:** Enforces PyTorch ≥2.6 (via transformers library)
- **BELLE-2 Dependency:** Validated with CUDA 11.8 / PyTorch <2.6 in Story 3.1
- **Irreconcilable Conflict:** Cannot satisfy both security and BELLE-2 compatibility in single environment

The original Epic 3 plan assumed BELLE-2 as the base transcription model requiring timestamp optimization (via WhisperX optimizer or HeuristicOptimizer fallback). However, user analysis suggests conducting comprehensive A/B comparison between BELLE-2 and WhisperX as **primary transcription models** to make evidence-based architectural decision rather than assuming BELLE-2 superiority.

### Context and Discovery

**When/How Discovered:**
- Story 3.2b Phase Gate validation (2025-11-14)
- Quick test execution revealed PyTorch version conflict
- User request: "我想对BELLE-2和WhisperX进行充分的对比，哪个组件效果更好就使用哪个组件"

**Supporting Evidence:**

**Technical Constraint:**
```
ValueError: Due to a serious vulnerability issue in `torch.load`, even with
`weights_only=True`, we now require users to upgrade torch to at least v2.6
in order to use the function.

See vulnerability report: https://nvd.nist.gov/vuln/detail/CVE-2025-32434
```

**User Rationale:**
- WhisperX has "更加齐全的配套功能" (more complete supporting features)
- Evidence-based decision preferred over assumption
- Comprehensive comparison across all quality dimensions requested

**Impact:**
- Story 3.2b achieved its validation purpose: discovered blocker early before production integration
- Protected main `.venv` environment from breaking changes
- Revealed strategic opportunity to validate model selection empirically

---

## Section 2: Impact Analysis

### Epic Impact

**Epic 3: Chinese Transcription Quality Optimization**

**Original Scope:** Optimize BELLE-2 timestamps using WhisperX optimizer or HeuristicOptimizer fallback

**New Scope:** Select optimal Chinese transcription model through A/B testing, then implement appropriate optimization

**Epic Structure Changes:**

```
BEFORE:
Epic 3: Chinese Transcription Quality Optimization
├── Story 3.1: BELLE-2 Integration ✅
├── Story 3.2a: Pluggable Optimizer Architecture ✅
├── Story 3.2b: WhisperX Integration Validation 🔄
├── Story 3.3: Heuristic VAD Preprocessing (CONDITIONAL)
├── Story 3.4: Heuristic Timestamp Refinement (CONDITIONAL)
├── Story 3.5: Heuristic Segment Splitting (CONDITIONAL)
└── Story 3.6: Quality Validation Framework

AFTER:
Epic 3: Chinese Transcription Model Selection & Quality Optimization
├── Phase 1: Architecture + Validation ✅ COMPLETE
│   ├── Story 3.1: BELLE-2 Integration ✅
│   ├── Story 3.2a: Pluggable Optimizer Architecture ✅
│   └── Story 3.2b: WhisperX Dependency Validation ✅ (NO-GO)
│
├── Phase 2: Model Comparison ⏳ NEW
│   └── Story 3.2c: BELLE-2 vs WhisperX A/B Testing ⏳
│
├── Phase 3: Winner Optimization (CONDITIONAL)
│   ├── IF BELLE-2 WINS:
│   │   ├── Story 3.3: Heuristic VAD Preprocessing
│   │   ├── Story 3.4: Heuristic Timestamp Refinement
│   │   └── Story 3.5: Heuristic Segment Splitting
│   │
│   └── IF WHISPERX WINS:
│       ├── Story 3.3-alt: WhisperX Production Integration
│       ├── Story 3.4-alt: WhisperX Optimizer Integration
│       └── Story 3.5-alt: Remove BELLE-2 Dependencies
│
└── Phase 4: Quality Validation (REQUIRED)
    └── Story 3.6: Quality Validation Framework
```

**Key Changes:**
- ✅ Stories 3.1, 3.2a, 3.2b preserved (no rollback)
- ➕ New Story 3.2c added (comprehensive A/B testing)
- 🔄 Stories 3.3-3.5 remain conditional, now explicitly tied to BELLE-2 winning
- 📋 Epic title updated to reflect model selection scope

### Story Impact

**Current and Future Stories Requiring Changes:**

| Story | Status | Change Required |
|-------|--------|-----------------|
| 3.1 | ✅ Done | None - BELLE-2 integration preserved |
| 3.2a | ✅ Done | None - pluggable architecture enables model swap |
| 3.2b | 🔄 In Progress → Done | Mark complete with NO-GO decision |
| 3.2c | ➕ NEW | Create story file for A/B testing |
| 3.3-3.5 | Backlog | Add "CONDITIONAL: BELLE-2 wins" to acceptance criteria |
| 3.6 | Backlog | Update to work with winning model |

### Artifact Conflicts

**PRD (Product Requirements Document):**

| Section | Conflict | Change Required |
|---------|----------|-----------------|
| FR003 | Specifies "BELLE-2 for Chinese/Mandarin" | Update: "empirically validated model (A/B comparison)" |
| NFR005 | Mentions Chinese priority but not selection process | Add: A/B testing methodology and metrics |
| Goals | ✅ No conflict | No changes needed |
| User Journeys | ✅ No conflict | Model selection transparent to users |

**Architecture Document:**

| Section | Conflict | Change Required |
|---------|----------|-----------------|
| AI Service Abstraction Strategy | States "BELLE-2 for Chinese" as decided | Update: "Model selected through Epic 3 A/B testing" |
| Belle2Service Class | Shows BELLE-2 as committed implementation | Add: "Conditional - pending A/B test results" |
| Optimization Pipeline Flow | Diagram shows "BELLE-2/faster-whisper" | Update: "[Selected Model: BELLE-2 or WhisperX]*" |
| GPU Requirements | VRAM specs for BELLE-2 only | Add: WhisperX requirements comparison |

**Epic 3 Tech Spec:**

| Section | Conflict | Change Required |
|---------|----------|-----------------|
| Overview | Assumes BELLE-2 as base model | Rewrite: Model selection as Epic objective |
| Architectural Approach | Two-phase plan (validation → heuristic) | Update: Three-phase (validation → A/B → optimization) |
| In Scope | Lists Stories 3.2a-3.6 | Add Story 3.2c, mark 3.2a-3.2b complete |
| ADRs | ADR-002 describes two-phase approach | Update ADR-002, add ADR-003 for model selection |

**UI/UX Specifications:**
- ✅ **No conflicts** - Model selection is backend implementation detail, transparent to users

**Other Artifacts:**
- ⚠️ `requirements.txt` - Needs conditional dependencies based on winner
- ⚠️ Docker configuration - GPU/CUDA setup varies (CUDA 11.8 vs 12.x)
- ⚠️ `.env` configuration - Model selection environment variables
- ✅ CI/CD pipelines - No changes during validation phase

### Technical Impact

**Code Changes Required:**
- ✅ Minimal - Pluggable architecture (Story 3.2a) already supports model swapping
- ➕ New isolated environment: `.venv-whisperx` with PyTorch 2.6+/CUDA 12.x
- ➕ A/B testing scripts for comprehensive comparison

**Infrastructure Changes:**
- Temporary: Dual environment management during Story 3.2c
- Post-decision: Single environment based on winner

**Deployment Impact:**
- Final CUDA version depends on winner (11.8 vs 12.x)
- PyTorch version locked by winner (<2.6 vs ≥2.6)
- GPU memory requirements vary slightly between models

---

## Section 3: Recommended Approach

### Selected Path: Direct Adjustment (Add Story 3.2c)

**Approach:** Add Story 3.2c for comprehensive BELLE-2 vs WhisperX A/B comparison within current Epic 3 structure

**Why This Path:**

1. **Evidence-Based Architecture**
   - User requirement: "哪个组件效果更好就使用哪个组件"
   - Engineering best practice: Validate, don't assume
   - Comprehensive comparison across all quality dimensions

2. **Minimal Disruption**
   - Pluggable architecture (Story 3.2a) designed for this scenario
   - No rollback of completed work required
   - Stories 3.1, 3.2a, 3.2b achievements preserved

3. **Low Risk**
   - Isolated environment methodology proven in Story 3.2b
   - No production impact during validation
   - Clear success criteria enable objective decision

4. **Timeline Acceptable**
   - +3-5 days investment for long-term architectural confidence
   - Better than discovering model limitations post-deployment
   - Potentially saves 8-12 days if WhisperX eliminates need for Stories 3.3-3.5

5. **Strategic Value**
   - WhisperX's "更加齐全的配套功能" may provide built-in optimization
   - If WhisperX wins, leverage mature ecosystem vs. self-developing
   - If BELLE-2 wins, proceed with HeuristicOptimizer as planned

**Alternatives Considered:**

**Option 2: Rollback Stories 3.1-3.2a**
- ❌ Rejected: No benefit - completed work enables this comparison
- Story 3.1 value preserved (gibberish elimination)
- Story 3.2a architecture enables clean model swap

**Option 3: Reduce MVP Scope**
- ❌ Rejected: Not necessary - A/B testing adds validation rigor, doesn't reduce features
- MVP deliverables unchanged: upload → transcribe → review → export
- Timeline extends slightly (+3-5 days) but functionality intact

### Effort Estimate

**Story 3.2c Breakdown:**

| Task | Effort | Description |
|------|--------|-------------|
| Environment setup | 0.5 day | Create `.venv-whisperx` with PyTorch 2.6+/CUDA 12.x |
| A/B test implementation | 1-2 days | Benchmark scripts for all comparison metrics |
| Test execution | 0.5 day | Run comprehensive comparison on test audio set |
| Analysis & decision | 0.5 day | Evaluate results against success criteria |
| Documentation | 0.5 day | Update phase gate report, ADRs, tech spec |
| **Total** | **3-5 days** | Depends on test suite complexity and audio corpus size |

**Overall Epic 3 Timeline Impact:**
- Original Epic 3 estimate: ~12-15 days (Stories 3.2b-3.6)
- With Story 3.2c: +3-5 days = ~15-20 days total
- Potential savings if WhisperX wins: -8-12 days (Stories 3.3-3.5 not needed)
- **Net impact: Neutral to positive on total project timeline**

### Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| WhisperX performs worse than BELLE-2 | Medium | Low | Proceed with BELLE-2 + HeuristicOptimizer as planned |
| BELLE-2 performs worse than WhisperX | Medium | Low | Switch to WhisperX, use built-in optimization |
| Comparison results inconclusive | Low | Medium | Define clear tiebreaker criteria (e.g., prioritize gibberish elimination) |
| Timeline overrun on A/B testing | Low | Low | 3-5 day buffer reasonable, can compress if needed |
| Environment setup issues (CUDA 12.x) | Medium | Low | Story 3.2b methodology proven, troubleshooting experience gained |

**Overall Risk Level:** 🟢 **LOW** - Well-scoped validation with clear fallback paths

---

## Section 4: Detailed Change Proposals

### Group A: PRD Updates

#### Change A1: FR003 - Transcription Architecture

**File:** `docs/PRD.md` (Line ~37)

**OLD:**
```markdown
- **FR003:** System shall process uploaded media files using multi-model transcription architecture (BELLE-2 for Chinese/Mandarin, WhisperX for other languages) with word-level timestamps, automatically detecting and preserving the original audio language
```

**NEW:**
```markdown
- **FR003:** System shall process uploaded media files using empirically validated transcription model (selected through A/B comparison in Epic 3: BELLE-2 vs WhisperX for Chinese/Mandarin) with word-level timestamps, automatically detecting and preserving the original audio language
```

**Rationale:** Reflects decision to validate models empirically rather than assume BELLE-2 superiority

---

#### Change A2: NFR005 - Transcription Quality

**File:** `docs/PRD.md` (Line ~78)

**OLD:**
```markdown
- **NFR005: Transcription Quality** - Subtitle segments shall conform to industry-standard length conventions for subtitle editing workflows. Segments should typically span 1-7 seconds with maximum ~200 characters to ensure usability in review and editing interfaces. Chinese/Mandarin transcription quality is prioritized as the primary use case.
```

**NEW:**
```markdown
- **NFR005: Transcription Quality** - Subtitle segments shall conform to industry-standard length conventions for subtitle editing workflows. Segments should typically span 1-7 seconds with maximum ~200 characters to ensure usability in review and editing interfaces. Chinese/Mandarin transcription quality is prioritized as the primary use case. Model selection (BELLE-2 vs WhisperX) determined through empirical A/B testing in Epic 3 across comprehensive metrics: CER/WER accuracy, segment length compliance (1-7s / ≤200 chars), gibberish elimination, processing speed, and GPU memory efficiency.
```

**Rationale:** Documents validation methodology and comparison metrics

---

### Group B: Architecture Document Updates

#### Change B1: AI Service Abstraction Strategy

**File:** `docs/architecture.md` (Lines ~652-660)

**OLD:**
```markdown
**Rationale:**
1. **Multi-model support:** BELLE-2 for Chinese/Mandarin, faster-whisper for other languages
2. **Pluggable optimization:** Interface-based optimizer design supporting multiple implementations (WhisperX wav2vec2 alignment, self-developed heuristics)
3. **Architectural flexibility:** Configuration-driven optimizer selection prevents technology lock-in, enables easy replacement when better solutions emerge
4. **Service abstraction:** Easy to add future models or optimization techniques
5. **Testing:** Mock AI service for unit tests without GPU dependency
```

**NEW:**
```markdown
**Rationale:**
1. **Multi-model support:** Chinese/Mandarin model selected through Epic 3 A/B testing (BELLE-2 vs WhisperX), faster-whisper for other languages
2. **Pluggable optimization:** Interface-based optimizer design supporting multiple implementations (WhisperX wav2vec2 alignment, self-developed heuristics)
3. **Architectural flexibility:** Configuration-driven model and optimizer selection prevents technology lock-in, enables easy replacement when better solutions emerge
4. **Service abstraction:** Easy to add future models or optimization techniques
5. **Testing:** Mock AI service for unit tests without GPU dependency

**Epic 3 Model Selection Status:** A/B comparison in progress - final selection pending comprehensive benchmark results (CER/WER, segment quality, gibberish elimination, speed, GPU memory).
```

**Rationale:** Updates point #1 to reflect validation approach, adds status tracking

---

#### Change B2: Belle2Service Class Documentation

**File:** `docs/architecture.md` (Lines ~685-696)

**OLD:**
```python
# app/ai_services/belle2_service.py - Epic 3 Chinese optimization
from .base import TranscriptionService
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

class Belle2Service(TranscriptionService):
    """BELLE-2 whisper-large-v3-zh for Chinese/Mandarin transcription"""
    def __init__(self, model_name: str = "BELLE-2/Belle-whisper-large-v3-zh", device: str = "cuda"):
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_name).to(device)
        self.processor = AutoProcessor.from_pretrained(model_name)

    async def transcribe(self, audio_path: str, language: str = "zh"):
        # Chinese-optimized decoder settings
```

**NEW:**
```python
# app/ai_services/belle2_service.py - Epic 3 Chinese optimization
# STATUS: Conditional - pending Epic 3 A/B test results (BELLE-2 vs WhisperX)
from .base import TranscriptionService
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

class Belle2Service(TranscriptionService):
    """BELLE-2 whisper-large-v3-zh for Chinese/Mandarin transcription

    Note: This implementation validated in Story 3.1 (eliminated gibberish loops).
    Final production usage pending Epic 3.2c A/B comparison vs WhisperX.
    """
    def __init__(self, model_name: str = "BELLE-2/Belle-whisper-large-v3-zh", device: str = "cuda"):
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_name).to(device)
        self.processor = AutoProcessor.from_pretrained(model_name)

    async def transcribe(self, audio_path: str, language: str = "zh"):
        # Chinese-optimized decoder settings
```

**Rationale:** Adds status comment and updates docstring to note conditional nature

---

#### Change B3: Optimization Pipeline Flow

**File:** `docs/architecture.md` (Line ~726)

**OLD:**
```
Audio Input → BELLE-2/faster-whisper Transcription →
┌─────────────────────────────────────────────────────┐
│ TimestampOptimizer Interface (Story 3.2a)          │
├─────────────────────────────────────────────────────┤
│ OptimizerFactory.create(engine="auto")             │
│                                                      │
```

**NEW:**
```
Audio Input → [Selected Model: BELLE-2 or WhisperX]* Transcription →
┌─────────────────────────────────────────────────────┐
│ TimestampOptimizer Interface (Story 3.2a)          │
├─────────────────────────────────────────────────────┤
│ OptimizerFactory.create(engine="auto")             │
│                                                      │

* Model selection pending Epic 3.2c A/B comparison results
  - BELLE-2: Validated in Story 3.1 (gibberish elimination)
  - WhisperX: Full pipeline evaluation in Story 3.2c
```

**Rationale:** Updates pipeline diagram to reflect pending decision with footnote

---

#### Change B4: GPU Environment Requirements

**File:** `docs/architecture.md` (Line ~808)

**OLD:**
```markdown
**Hardware Requirements:**
- **GPU:** NVIDIA GPU with CUDA support
- **Minimum VRAM:** 8GB (recommended 12GB+ for large-v2/BELLE-2 models)
- **CUDA Version:** 11.8 or 12.1+
- **Driver:** NVIDIA driver 520+ (for CUDA 11.8) or 530+ (for CUDA 12.1)
```

**NEW:**
```markdown
**Hardware Requirements:**
- **GPU:** NVIDIA GPU with CUDA support
- **Minimum VRAM:** 8GB (recommended 12GB+ for large models)
- **CUDA Version:** Depends on Epic 3.2c model selection
  - BELLE-2: CUDA 11.8 (PyTorch <2.6, validated in Story 3.1)
  - WhisperX: CUDA 12.x (PyTorch ≥2.6, required for CVE-2025-32434 security)
- **Driver:** NVIDIA driver 520+ (for CUDA 11.8) or 530+ (for CUDA 12.1+)

**Note:** Final CUDA version and PyTorch dependency determined by Epic 3.2c A/B test winner. Both models cannot coexist in single environment due to PyTorch version conflict.
```

**Rationale:** Documents CUDA/PyTorch dependency differences and mutual exclusivity

---

### Group C: Epic 3 Tech Spec Updates

#### Change C1: Overview Section

**File:** `docs/sprint-artifacts/tech-spec-epic-3.md` (Lines ~10-42)

**OLD:**
```markdown
## Overview

Epic 3 dramatically improves Mandarin Chinese transcription segmentation quality through a **pluggable optimizer architecture** that supports multiple timestamp optimization implementations. Story 3.1 successfully integrated BELLE-2 to eliminate repetitive "gibberish loops," but production testing revealed that BELLE-2 produces overly long subtitle segments that violate standard subtitle timestamp conventions.

### Architectural Approach

Following user requirements for **architectural flexibility over technology lock-in**, Epic 3 adopts a two-phase implementation strategy:

1. **Phase 1 (Stories 3.2a-3.2b): Pluggable Architecture + WhisperX Validation**
   - Implement `TimestampOptimizer` abstract interface enabling multiple optimizer implementations
   - Validate WhisperX wav2vec2 forced alignment as mature solution for timestamp optimization
   - Phase Gate decision: GO/NO-GO for WhisperX based on objective success criteria

2. **Phase 2 (Stories 3.3-3.5): Heuristic Optimizer Implementation** *(Conditional)*
   - Self-developed optimizer using VAD preprocessing, energy refinement, intelligent splitting
   - Activates ONLY if Phase Gate decision is NO-GO for WhisperX
   - Fallback ensures Epic 3 objectives achieved regardless of dependency conflicts

3. **Phase 3 (Story 3.6): Quality Validation Framework** *(Required)*
   - Automated CER/WER calculation and segment length statistics
   - Works with BOTH WhisperXOptimizer and HeuristicOptimizer implementations
```

**NEW:**
```markdown
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
```

**Rationale:** Reframes Epic 3 from "optimize BELLE-2" to "select best model," documents phase structure changes

---

#### Change C2: In Scope Section

**File:** `docs/sprint-artifacts/tech-spec-epic-3.md` (Lines ~45-52)

**OLD:**
```markdown
**In Scope:**

- **Pluggable Optimizer Architecture (Story 3.2a):** `TimestampOptimizer` abstract interface, `OptimizerFactory` with auto-selection logic, `OPTIMIZER_ENGINE` configuration setting
- **WhisperX Integration Validation (Story 3.2b):** Isolated dependency testing, WhisperXOptimizer implementation, performance benchmarking, quality A/B testing, Phase Gate decision report
- **Heuristic Optimizer - VAD Preprocessing (Story 3.3 - CONDITIONAL):** Voice Activity Detection filtering, silence removal, parameter optimization
- **Heuristic Optimizer - Timestamp Refinement (Story 3.4 - CONDITIONAL):** Token-level timestamp extraction, energy-based boundary refinement
- **Heuristic Optimizer - Segment Splitting (Story 3.5 - CONDITIONAL):** Intelligent splitting to meet 1-7 second conventions, Chinese text length estimation
- **Quality Validation Framework (Story 3.6 - REQUIRED):** Automated CER/WER calculation, segment length statistics, regression testing
```

**NEW:**
```markdown
**In Scope:**

- **Pluggable Optimizer Architecture (Story 3.2a):** ✅ COMPLETE - `TimestampOptimizer` abstract interface, `OptimizerFactory` with auto-selection logic, `OPTIMIZER_ENGINE` configuration setting
- **WhisperX Integration Validation (Story 3.2b):** ✅ COMPLETE - Isolated dependency testing, WhisperXOptimizer implementation, Phase Gate decision report (NO-GO: PyTorch conflict)
- **BELLE-2 vs WhisperX Model Comparison (Story 3.2c - NEW):** ⏳ IN PROGRESS - Comprehensive A/B testing across CER/WER accuracy, segment length compliance, gibberish elimination, processing speed, GPU memory efficiency. Isolated `.venv-whisperx` environment with PyTorch 2.6+/CUDA 12.x for WhisperX evaluation. Phase Gate decision: Select winner for production.
- **Heuristic Optimizer - VAD Preprocessing (Story 3.3 - CONDITIONAL):** Voice Activity Detection filtering, silence removal, parameter optimization. *Activates only if BELLE-2 wins Story 3.2c comparison.*
- **Heuristic Optimizer - Timestamp Refinement (Story 3.4 - CONDITIONAL):** Token-level timestamp extraction, energy-based boundary refinement. *Activates only if BELLE-2 wins Story 3.2c comparison.*
- **Heuristic Optimizer - Segment Splitting (Story 3.5 - CONDITIONAL):** Intelligent splitting to meet 1-7 second conventions, Chinese text length estimation. *Activates only if BELLE-2 wins Story 3.2c comparison.*
- **Quality Validation Framework (Story 3.6 - REQUIRED):** Automated CER/WER calculation, segment length statistics, regression testing. Works with winning model from Story 3.2c.
```

**Rationale:** Adds Story 3.2c, marks completed stories, clarifies conditional dependencies

---

#### Change C3: Architectural Decision Records

**File:** `docs/sprint-artifacts/tech-spec-epic-3.md` (Lines ~32-42)

**OLD:**
```markdown
### Key Architectural Decisions

**ADR-001: Pluggable TimestampOptimizer Interface**
- **Decision:** Abstract interface with multiple implementations (WhisperX, Heuristic)
- **Rationale:** Prevents technology lock-in, enables future optimizer upgrades, provides fallback strategy
- **Trade-offs:** +3-5 days implementation time vs. long-term architectural flexibility

**ADR-002: Two-Phase Implementation with Phase Gate**
- **Decision:** Prioritize mature solution (WhisperX) validation before self-developed fallback
- **Rationale:** Minimize development effort if proven solution works, de-risk through early validation
- **Trade-offs:** Sequential execution (no parallel work) vs. early risk discovery
```

**NEW:**
```markdown
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
```

**Rationale:** Updates ADR-002 to three-phase, adds ADR-003 documenting strategic pivot

---

### Group D: Sprint Status Update

#### Change D1: Add Story 3.2c

**File:** `docs/sprint-artifacts/sprint-status.yaml` (Lines ~63-68)

**OLD:**
```yaml
  epic-3: contexted
  3-1-belle2-integration: done
  3-2a-pluggable-optimizer-architecture: done
  3-2b-whisperx-integration-validation: in-progress
  3-3-heuristic-vad-preprocessing: backlog
  3-4-heuristic-timestamp-refinement: backlog
  3-5-heuristic-segment-splitting: backlog
  3-6-quality-validation-framework: backlog
  epic-3-retrospective: optional
```

**NEW:**
```yaml
  epic-3: contexted
  3-1-belle2-integration: done
  3-2a-pluggable-optimizer-architecture: done
  3-2b-whisperx-integration-validation: done
  3-2c-belle2-vs-whisperx-model-comparison: in-progress
  3-3-heuristic-vad-preprocessing: backlog
  3-4-heuristic-timestamp-refinement: backlog
  3-5-heuristic-segment-splitting: backlog
  3-6-quality-validation-framework: backlog
  epic-3-retrospective: optional
```

**Rationale:** Marks 3.2b done, adds 3.2c as current in-progress story

---

## Section 5: Implementation Handoff

### Change Scope Classification: **Moderate**

**Reasoning:**
- Requires backlog reorganization (add Story 3.2c)
- Requires Epic 3 redefinition (scope + objective changes)
- Requires multiple artifact updates (PRD, Architecture, Tech Spec)
- Does NOT require fundamental MVP replan or rollback

**Handoff Recipients:**

**Primary: Product Owner / Scrum Master**
- Create Story 3.2c file in `docs/sprint-artifacts/stories/`
- Update sprint-status.yaml (mark 3.2b done, add 3.2c)
- Review and approve all artifact edits (PRD, Architecture, Epic 3 Tech Spec)

**Secondary: Development Team**
- Execute Story 3.2c implementation:
  - Set up `.venv-whisperx` isolated environment
  - Implement A/B testing scripts
  - Run comprehensive benchmarks
  - Analyze results and make phase gate decision
- Update documentation based on A/B test winner

**Tertiary: Product Manager (User: Link)**
- Final approval of Sprint Change Proposal
- Decision authority on A/B test results if inconclusive
- Prioritization guidance for Epic 3 remaining stories

### Responsibilities

**Product Owner / Scrum Master:**
1. ✅ Approve this Sprint Change Proposal
2. ✅ Apply all 10 documented edits to project artifacts
3. ✅ Create Story 3.2c file with comprehensive acceptance criteria
4. ✅ Update sprint tracking documents
5. ✅ Communicate Epic 3 scope change to stakeholders

**Development Team:**
1. Execute Story 3.2c implementation (~3-5 days)
2. Document A/B test results in phase gate report
3. Present findings and recommendation to PO/PM
4. Based on winner, implement Phase 3 stories (3.3-3.5 or alternatives)

**Product Manager:**
1. Review and approve Sprint Change Proposal
2. Review A/B test results and phase gate recommendation
3. Make final decision if results are close/inconclusive
4. Approve Epic 3 continuation based on chosen path

### Success Criteria

**Sprint Change Proposal Success:**
- ✅ All 10 artifact edits applied correctly
- ✅ Story 3.2c created with clear acceptance criteria
- ✅ Sprint status updated (3.2b → done, 3.2c → in-progress)
- ✅ Team aligned on new Epic 3 scope and objectives

**Story 3.2c Success (A/B Testing):**
- Clear winner identified across majority of metrics
- OR: Tiebreaker decision made based on prioritized criteria (e.g., gibberish elimination > speed)
- Phase gate report documents comprehensive comparison
- Architecture decision (ADR-003) finalized with winning model

**Epic 3 Continuation Success:**
- If BELLE-2 wins: Stories 3.3-3.5 executed as planned
- If WhisperX wins: Alternative integration stories completed
- Story 3.6 validates winning model meets all quality thresholds
- Epic 3 objectives achieved regardless of model selection

---

## Section 6: Timeline and Next Steps

### Timeline Impact

**Original Epic 3 Timeline:**
- Story 3.2b: 3-5 days (validation)
- Stories 3.3-3.5: 8-12 days (heuristic optimizer)
- Story 3.6: 2-3 days (quality validation)
- **Total:** ~13-20 days

**Revised Epic 3 Timeline:**
- Story 3.2b: ✅ Complete
- Story 3.2c: 3-5 days (A/B testing) **← NEW**
- Stories 3.3-3.5: 8-12 days (if BELLE-2 wins) OR 3-5 days (if WhisperX wins)
- Story 3.6: 2-3 days (quality validation)
- **Total:** ~13-25 days (neutral to +5 days in worst case)

**Best Case:** WhisperX wins, saves 5-7 days on Stories 3.3-3.5
**Worst Case:** BELLE-2 wins, +5 days for Story 3.2c
**Most Likely:** +3-5 days total, better architectural confidence

### Immediate Next Steps

**Step 1: Approve Sprint Change Proposal** (User: Link)
- Review all 10 proposed edits
- Approve or request modifications
- Authorize Story 3.2c creation

**Step 2: Apply Artifact Edits** (PO/SM Agent or Dev)
- Execute all 10 approved edits to project files
- Verify no conflicts or formatting issues
- Commit changes with clear message: "Sprint Change: Add Story 3.2c for BELLE-2 vs WhisperX comparison"

**Step 3: Create Story 3.2c** (PO/SM Agent)
- Generate story file: `docs/sprint-artifacts/stories/3-2c-belle2-vs-whisperx-model-comparison.md`
- Include comprehensive acceptance criteria:
  - Environment setup (`.venv-whisperx` with PyTorch 2.6+/CUDA 12.x)
  - A/B testing scripts (CER/WER, segment quality, gibberish, speed, memory)
  - Test execution on representative audio corpus
  - Phase gate decision report with clear winner
- Reference all 5 comparison metrics from ADR-003

**Step 4: Execute Story 3.2c** (Dev Team)
- Begin implementation immediately after story creation
- Target completion: 3-5 days
- Daily progress updates on findings

**Step 5: Phase Gate Decision Meeting** (PM, PO, Dev)
- Review Story 3.2c results
- Make GO/NO-GO decision for each model
- Select production model
- Plan remaining Epic 3 stories based on winner

**Step 6: Continue Epic 3** (Dev Team)
- If BELLE-2 wins: Activate Stories 3.3-3.5 as planned
- If WhisperX wins: Define and execute alternative integration stories
- Complete Story 3.6 with winning model

---

## Appendix A: Story 3.2c Acceptance Criteria (Draft)

### Story 3.2c: BELLE-2 vs WhisperX Model Comparison

**As a** product team,
**I want** comprehensive empirical comparison between BELLE-2 and WhisperX for Chinese transcription,
**So that** we can make evidence-based decision on which model to use in production.

**Acceptance Criteria:**

**AC #1: Isolated WhisperX Environment Created**
- ✅ `.venv-whisperx` environment created with PyTorch 2.6+/CUDA 12.x
- ✅ WhisperX and dependencies installed successfully
- ✅ GPU acceleration validated (`torch.cuda.is_available() == True`)
- ✅ No interference with main `.venv` environment

**AC #2: Test Audio Corpus Prepared**
- ✅ Representative Chinese audio files selected (variety of speakers, durations, quality)
- ✅ Minimum 30-60 minutes total audio for statistical significance
- ✅ Ground truth transcriptions available for CER/WER calculation
- ✅ Includes challenging cases: long meetings, multiple speakers, background noise

**AC #3: A/B Testing Scripts Implemented**
- ✅ Transcription accuracy comparison (CER/WER calculation)
- ✅ Segment quality comparison (1-7s duration, ≤200 char compliance rate)
- ✅ Gibberish elimination comparison (qualitative + quantitative)
- ✅ Processing speed comparison (real-time factor)
- ✅ GPU memory usage comparison

**AC #4: Comprehensive Benchmark Executed**
- ✅ BELLE-2 results captured across all 5 metrics
- ✅ WhisperX results captured across all 5 metrics
- ✅ Results logged with timestamps and environment details
- ✅ Raw outputs saved for manual review

**AC #5: Phase Gate Decision Report Completed**
- ✅ Side-by-side comparison table with all metrics
- ✅ Clear winner identified OR tiebreaker rationale provided
- ✅ GO/NO-GO recommendation with confidence level
- ✅ ADR-003 finalized with selected model
- ✅ Lessons learned and risk assessment documented

**AC #6: Epic 3 Path Forward Defined**
- ✅ If BELLE-2 wins: Stories 3.3-3.5 scoped and ready
- ✅ If WhisperX wins: Alternative integration stories defined
- ✅ Story 3.6 acceptance criteria updated for winning model
- ✅ Dependencies and environment requirements documented

**Definition of Done:**
- All 6 ACs satisfied
- Phase gate report reviewed by PM (Link)
- Production model decision approved
- Epic 3 remaining stories updated based on winner

---

## Appendix B: Comparison Metrics Detail

### Metric 1: Transcription Accuracy (CER/WER)

**Character Error Rate (CER) for Chinese:**
```
CER = (Substitutions + Deletions + Insertions) / Total Characters
Target: Lower is better
Threshold: <10% (industry standard for Chinese ASR)
```

**Word Error Rate (WER) for reference:**
```
WER = (Substitutions + Deletions + Insertions) / Total Words
Target: Lower is better
```

**Comparison Approach:**
- Use ground truth transcriptions from test corpus
- Calculate CER/WER for BELLE-2 vs WhisperX outputs
- Winner: Lowest CER (primary) and WER (secondary)

---

### Metric 2: Segment Length Compliance

**1-7 Second Duration Compliance:**
```
Compliance Rate = (Segments within 1-7s) / Total Segments
Target: ≥95%
```

**≤200 Character Compliance:**
```
Compliance Rate = (Segments ≤200 chars) / Total Segments
Target: ≥95%
```

**Comparison Approach:**
- Analyze raw transcription output (before optimization)
- Calculate compliance rates for both models
- Winner: Higher compliance rate (closer to subtitle standards)

---

### Metric 3: Gibberish Elimination

**Qualitative Assessment:**
- Manual review of transcription outputs
- Identify repetitive loops, nonsensical text, hallucinations
- Rate severity: None / Minor / Major

**Quantitative Proxy:**
- Repetition detection (n-gram analysis)
- Perplexity scores (language model confidence)
- User story 3.1 success: BELLE-2 eliminated gibberish vs baseline

**Comparison Approach:**
- Test on same audio that showed gibberish with original Whisper
- Score: BELLE-2 (known good) vs WhisperX (unknown)
- Winner: Fewer/no gibberish artifacts

---

### Metric 4: Processing Speed

**Real-Time Factor (RTF):**
```
RTF = Processing Time / Audio Duration
Target: RTF ≤ 0.5 (2x real-time or faster)
Example: 60 min audio processed in ≤30 min
```

**Comparison Approach:**
- Measure GPU processing time for same audio files
- Calculate RTF for BELLE-2 vs WhisperX
- Winner: Lower RTF (faster processing)

---

### Metric 5: GPU Memory Efficiency

**Peak VRAM Usage:**
```
Measure: nvidia-smi during transcription
Target: ≤8GB (fits on most GPUs)
```

**Comparison Approach:**
- Monitor GPU memory during transcription
- Record peak usage for BELLE-2 vs WhisperX
- Winner: Lower peak VRAM (better scalability)

---

## Appendix C: Decision Matrix Template

### BELLE-2 vs WhisperX Comparison Results

| Metric | Weight | BELLE-2 | WhisperX | Winner |
|--------|--------|---------|----------|--------|
| **CER Accuracy** | 30% | [TBD]% | [TBD]% | [TBD] |
| **Segment Compliance** | 25% | [TBD]% | [TBD]% | [TBD] |
| **Gibberish Elimination** | 25% | [TBD] | [TBD] | [TBD] |
| **Processing Speed (RTF)** | 10% | [TBD]x | [TBD]x | [TBD] |
| **GPU Memory (GB)** | 10% | [TBD] | [TBD] | [TBD] |
| **TOTAL WEIGHTED SCORE** | 100% | **[TBD]** | **[TBD]** | **[TBD]** |

**Tiebreaker Criteria (if scores within 5%):**
1. Gibberish elimination (user pain point from Story 3.1)
2. Segment compliance (Epic 3 primary objective)
3. CER accuracy (transcription quality)
4. Processing speed (user experience)
5. GPU memory (deployment cost)

**Final Decision:** [BELLE-2 / WhisperX]

**Confidence Level:** [High / Medium / Low]

**Rationale:** [2-3 sentences explaining decision based on metrics and tiebreakers]

---

## Document Control

**Version:** 1.0
**Status:** PENDING APPROVAL
**Author:** PM Agent (John) + Dev (Claude Code)
**Approver:** Link (Product Manager)
**Date Created:** 2025-11-14
**Last Updated:** 2025-11-14

**Change Log:**
- 2025-11-14 v1.0: Initial Sprint Change Proposal created

**Next Review:** After user approval and Story 3.2c completion

---

**END OF SPRINT CHANGE PROPOSAL**
