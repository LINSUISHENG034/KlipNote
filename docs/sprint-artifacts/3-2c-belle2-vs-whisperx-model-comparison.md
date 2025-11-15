# Story 3.2c: BELLE-2 vs WhisperX Model Comparison

**Epic:** Epic 3 - Chinese Transcription Model Selection & Quality Optimization
**Story ID:** 3.2c
**Status:** done
**Priority:** High
**Effort Estimate:** 3-5 days
**Dependencies:** Story 3.2b (WhisperX dependency validation complete)

---

## User Story

**As a** product team,
**I want** comprehensive empirical comparison between BELLE-2 and WhisperX for Chinese transcription,
**So that** we can make evidence-based decision on which model to use in production.

---

## Context

### Background

Story 3.2b's phase gate validation revealed that WhisperX cannot coexist with BELLE-2 in a single environment due to irreconcilable PyTorch dependency conflicts:

- **Security Requirement:** CVE-2025-32434 requires PyTorch ≥2.6
- **WhisperX Dependency:** Enforces PyTorch ≥2.6 (via transformers library)
- **BELLE-2 Dependency:** Validated with CUDA 11.8 / PyTorch <2.6 in Story 3.1
- **Irreconcilable Conflict:** Cannot satisfy both security and BELLE-2 compatibility requirements

The original Epic 3 plan assumed BELLE-2 as the base transcription model requiring timestamp optimization. However, user analysis suggests conducting comprehensive A/B comparison between BELLE-2 and WhisperX as **primary transcription models** to make evidence-based architectural decision rather than assuming BELLE-2 superiority.

### Strategic Rationale

**User Requirement:** "我想对BELLE-2和WhisperX进行充分的对比，哪个组件效果更好就使用哪个组件"

**Key Considerations:**
- WhisperX has "更加齐全的配套功能" (more complete supporting features)
- Evidence-based decision preferred over assumption
- WhisperX's built-in optimization may eliminate need for Stories 3.3-3.5 (potential 8-12 day savings)
- Long-term architectural confidence worth +3-5 day validation investment

---

## Acceptance Criteria

### AC #1: Isolated WhisperX Environment Created

**Requirements:**
- ✅ `.venv-whisperx` environment created separately from main `.venv`
- ✅ PyTorch 2.6+ installed with CUDA 12.x support
- ✅ WhisperX and all dependencies installed successfully
- ✅ GPU acceleration validated (`torch.cuda.is_available() == True`)
- ✅ No interference with main `.venv` environment (BELLE-2 still functional)

**Validation:**
```bash
cd backend
python -m venv .venv-whisperx
.venv-whisperx/Scripts/activate
pip install torch>=2.6.0 torchaudio whisperx
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

**Success Criteria:**
- PyTorch version ≥2.6.0
- CUDA available = True
- WhisperX imports without errors
- Main `.venv` remains unchanged (verify BELLE-2 still works)

---

### AC #2: Test Audio Corpus Prepared

**Requirements:**
- ✅ Representative Chinese audio files selected covering variety of scenarios
- ✅ Minimum 30-60 minutes total audio for statistical significance
- ✅ Ground truth transcriptions available for CER/WER calculation
- ✅ Includes challenging cases that demonstrate model capabilities

**Test Corpus Composition:**

| Category | Audio Type | Duration | Purpose |
|----------|-----------|----------|---------|
| Clean speech | Mandarin meeting recording | 10-15 min | Baseline accuracy |
| Multiple speakers | Team discussion | 10-15 min | Speaker handling |
| Background noise | Office environment | 5-10 min | Robustness |
| Long form | Conference talk | 15-20 min | Segment quality at scale |
| Gibberish test | Same audio from Story 3.1 | 5-10 min | Validate gibberish elimination |

**Ground Truth Sources:**
- Human-reviewed transcriptions from Story 3.1 testing
- Professional transcription service output (for reference)
- Known "gibberish loop" examples from pre-Story 3.1 baseline

**Success Criteria:**
- Total audio ≥30 minutes
- All 5 categories represented
- Ground truth available for ≥80% of test audio
- Corpus saved in organized directory: `backend/test_audio_corpus/`

---

### AC #3: A/B Testing Scripts Implemented

**Requirements:**
- ✅ Automated scripts for all 5 comparison metrics
- ✅ Supports both BELLE-2 (.venv) and WhisperX (.venv-whisperx) execution
- ✅ Results logged in structured format (JSON) for analysis
- ✅ Error handling for failed transcriptions

**Script Files:**

**1. `backend/scripts/ab_test_accuracy.py`**
- Transcribes test corpus with both models
- Calculates CER (Character Error Rate) for Chinese
- Calculates WER (Word Error Rate) for reference
- Compares against ground truth transcriptions
- Outputs: `ab_accuracy_results.json`

**2. `backend/scripts/ab_test_segments.py`**
- Analyzes raw transcription segment lengths
- Calculates 1-7 second duration compliance rate
- Calculates ≤200 character compliance rate
- Computes mean/median/95th percentile segment duration
- Outputs: `ab_segments_results.json`

**3. `backend/scripts/ab_test_gibberish.py`**
- Tests on known gibberish-prone audio from Story 3.1
- Automated repetition detection (n-gram analysis)
- Manual review checklist for qualitative assessment
- Scores: None / Minor / Major gibberish artifacts
- Outputs: `ab_gibberish_results.json` + manual review notes

**4. `backend/scripts/ab_test_performance.py`**
- Measures GPU processing time for same audio files
- Calculates Real-Time Factor (RTF = processing_time / audio_duration)
- Target: RTF ≤ 0.5 (2x real-time or faster)
- Outputs: `ab_performance_results.json`

**5. `backend/scripts/ab_test_memory.py`**
- Monitors GPU memory usage during transcription
- Records peak VRAM usage via `nvidia-smi`
- Target: ≤8GB (fits on most GPUs)
- Outputs: `ab_memory_results.json`

**Success Criteria:**
- All 5 scripts executable in both environments
- JSON output format consistent across scripts
- Clear error messages for failed tests
- Execution time: <4 hours total for full test suite

---

### AC #4: Comprehensive Benchmark Executed

**Requirements:**
- ✅ BELLE-2 results captured across all 5 metrics
- ✅ WhisperX results captured across all 5 metrics
- ✅ Results logged with timestamps and environment details
- ✅ Raw transcription outputs saved for manual review

**Execution Process:**

**Phase 1: BELLE-2 Baseline**
```bash
cd backend
source .venv/Scripts/activate
python scripts/ab_test_accuracy.py --model belle2
python scripts/ab_test_segments.py --model belle2
python scripts/ab_test_gibberish.py --model belle2
python scripts/ab_test_performance.py --model belle2
python scripts/ab_test_memory.py --model belle2
```

**Phase 2: WhisperX Comparison**
```bash
cd backend
source .venv-whisperx/Scripts/activate
python scripts/ab_test_accuracy.py --model whisperx
python scripts/ab_test_segments.py --model whisperx
python scripts/ab_test_gibberish.py --model whisperx
python scripts/ab_test_performance.py --model whisperx
python scripts/ab_test_memory.py --model whisperx
```

**Phase 3: Results Consolidation**
```bash
python scripts/consolidate_ab_results.py
# Generates: ab_test_summary.json + ab_test_report.md
```

**Output Artifacts:**
- `backend/ab_test_results/belle2/` - All BELLE-2 results
- `backend/ab_test_results/whisperx/` - All WhisperX results
- `backend/ab_test_results/ab_test_summary.json` - Consolidated comparison
- `backend/ab_test_results/ab_test_report.md` - Human-readable summary

**Success Criteria:**
- All tests completed without critical errors
- Both models tested on identical audio corpus
- Results reproducible (same audio → consistent metrics)
- Execution metadata captured (timestamp, GPU model, CUDA version)

---

### AC #5: Phase Gate Decision Report Completed

**Requirements:**
- ✅ Side-by-side comparison table with all 5 metrics
- ✅ Clear winner identified OR tiebreaker rationale provided
- ✅ GO/NO-GO recommendation with confidence level
- ✅ ADR-003 finalized with selected model
- ✅ Lessons learned and risk assessment documented

**Report Structure:**

**File:** `backend/phase-gate-story-3-2c.md` (update existing phase gate doc)

**Section 1: Executive Summary**
- Final decision: [BELLE-2 / WhisperX]
- Confidence level: [High / Medium / Low]
- Key differentiator: [Which metric was decisive]

**Section 2: Comparison Results**

| Metric | Weight | BELLE-2 | WhisperX | Winner | Notes |
|--------|--------|---------|----------|--------|-------|
| **CER Accuracy** | 30% | X.XX% | X.XX% | [Model] | [Key findings] |
| **Segment Compliance** | 25% | XX% | XX% | [Model] | [Key findings] |
| **Gibberish Elimination** | 25% | [Score] | [Score] | [Model] | [Key findings] |
| **Processing Speed (RTF)** | 10% | X.XXx | X.XXx | [Model] | [Key findings] |
| **GPU Memory (GB)** | 10% | X.X GB | X.X GB | [Model] | [Key findings] |
| **TOTAL WEIGHTED SCORE** | 100% | **XX.X** | **XX.X** | **[Model]** | |

**Section 3: Tiebreaker Decision (if scores within 5%)**
- Primary criterion: Gibberish elimination (user pain point from Story 3.1)
- Secondary: Segment compliance (Epic 3 primary objective)
- Tertiary: CER accuracy (transcription quality)

**Section 4: GO/NO-GO Recommendation**
- **GO:** [Winning Model] for production deployment
- **NO-GO:** [Losing Model] - document why it didn't win
- **Rationale:** 2-3 sentences explaining decision based on metrics

**Section 5: Implementation Impact**
- If BELLE-2 wins: Activate Stories 3.3-3.5 (HeuristicOptimizer)
- If WhisperX wins: Define Stories 3.3-alt through 3.5-alt (WhisperX integration)
- Epic 3 timeline impact: [X days added/saved]

**Success Criteria:**
- Decision made with >80% confidence (not 50/50 toss-up)
- Clear winner across ≥3 of 5 metrics
- Tiebreaker applied if needed with documented rationale
- Team alignment on decision (PM approval obtained)

---

### AC #6: Epic 3 Path Forward Defined

**Requirements:**
- ✅ If BELLE-2 wins: Stories 3.3-3.5 scoped and ready
- ✅ If WhisperX wins: Alternative integration stories defined
- ✅ Story 3.6 acceptance criteria updated for winning model
- ✅ Dependencies and environment requirements documented

**If BELLE-2 Wins:**

**Path:** Proceed with Stories 3.3-3.5 (HeuristicOptimizer) as originally planned

**Deliverables:**
- Story 3.3 ready: VAD Preprocessing acceptance criteria confirmed
- Story 3.4 ready: Timestamp Refinement acceptance criteria confirmed
- Story 3.5 ready: Segment Splitting acceptance criteria confirmed
- Environment: Continue using `.venv` with CUDA 11.8 / PyTorch <2.6
- Cleanup: Archive `.venv-whisperx` (no longer needed)

**If WhisperX Wins:**

**Path:** Define alternative Stories 3.3-alt through 3.5-alt for WhisperX integration

**Story 3.3-alt: WhisperX Production Environment Setup**
- Migrate main `.venv` to PyTorch 2.6+ / CUDA 12.x
- Install WhisperX as primary transcription model
- Remove BELLE-2 dependencies
- Update Docker configuration for CUDA 12.x

**Story 3.4-alt: WhisperX Optimizer Integration**
- Implement WhisperXOptimizer using WhisperX's built-in forced alignment
- Configure optimization parameters (beam size, temperature, etc.)
- Integrate with existing OptimizerFactory

**Story 3.5-alt: BELLE-2 Removal and Cleanup**
- Remove Belle2Service implementation
- Update architecture documentation
- Archive Story 3.1 learnings (gibberish elimination reference)
- Clean up deprecated dependencies

**Deliverables:**
- Stories 3.3-alt through 3.5-alt drafted with acceptance criteria
- Environment migration plan documented
- Dependency conflict resolution validated
- CUDA 12.x GPU requirements confirmed

**Common (Both Paths):**

**Story 3.6 Updates:**
- Acceptance criteria adapted to winning model
- Quality thresholds: CER/WER, segment compliance
- Regression testing against A/B test baseline
- Production validation before Epic 3 completion

**Success Criteria:**
- Path forward clearly documented within 24 hours of decision
- Next story (3.3 or 3.3-alt) ready for immediate start
- No blockers to Epic 3 continuation
- Team aligned on execution plan

---

## Definition of Done

**Story 3.2c is complete when:**

1. ✅ All 6 Acceptance Criteria satisfied
2. ✅ Phase gate decision report reviewed by PM (Link)
3. ✅ Production model decision approved and documented
4. ✅ Epic 3 remaining stories updated based on winner
5. ✅ Sprint Change Proposal (2025-11-14) fully executed
6. ✅ ADR-003 finalized in tech spec
7. ✅ Code committed with clear message: "Complete Story 3.2c: BELLE-2 vs WhisperX A/B testing - [Winning Model] selected"

---

## Technical Notes

### Environment Isolation Strategy

**Why Two Environments:**
- BELLE-2: Requires PyTorch <2.6 (CUDA 11.8 compatible)
- WhisperX: Requires PyTorch ≥2.6 (CVE-2025-32434 security)
- Cannot satisfy both in single environment

**Testing Protocol:**
- Identical audio corpus for both models
- Same hardware (GPU, VRAM)
- Controlled variables: Only model implementation differs
- Statistical significance: ≥30 min audio across diverse scenarios

### Comparison Metrics Weighting Rationale

| Metric | Weight | Justification |
|--------|--------|---------------|
| CER Accuracy | 30% | Primary quality indicator for Chinese transcription |
| Segment Compliance | 25% | Epic 3's core objective (subtitle-length segments) |
| Gibberish Elimination | 25% | User pain point from Story 3.1, critical for usability |
| Processing Speed | 10% | Important for UX but secondary to quality |
| GPU Memory | 10% | Deployment consideration but not quality blocker |

**Tiebreaker Priority:**
1. Gibberish elimination (user-facing quality issue)
2. Segment compliance (Epic 3 success criterion)
3. CER accuracy (transcription correctness)

### Risk Mitigation

**Risk:** WhisperX performs worse than BELLE-2
**Mitigation:** Proceed with BELLE-2 + HeuristicOptimizer as planned (no loss)

**Risk:** BELLE-2 performs worse than WhisperX
**Mitigation:** Switch to WhisperX, use built-in optimization (potentially save 8-12 days)

**Risk:** Comparison results inconclusive (within 5%)
**Mitigation:** Apply tiebreaker criteria with clear prioritization

**Risk:** Timeline overrun on A/B testing (>5 days)
**Mitigation:** 3-5 day buffer reasonable, can compress test suite if needed

---

## References

**Related Documents:**
- **Sprint Change Proposal:** `docs/sprint-change-proposal-2025-11-14.md`
- **Epic 3 Tech Spec:** `docs/sprint-artifacts/tech-spec-epic-3.md`
- **Phase Gate Report (3.2b):** `docs/phase-gate-story-3-2b.md`
- **ADR-003:** Epic 3 Tech Spec - Evidence-Based Model Selection

**Related Stories:**
- **Story 3.1:** BELLE-2 Integration (gibberish elimination baseline)
- **Story 3.2a:** Pluggable Optimizer Architecture (enables model swap)
- **Story 3.2b:** WhisperX Dependency Validation (discovered PyTorch conflict)
- **Stories 3.3-3.5:** HeuristicOptimizer (conditional on BELLE-2 winning)
- **Story 3.6:** Quality Validation Framework (works with winner)

---

## Implementation Plan

### Day 1: Environment Setup & Corpus Preparation
- Create `.venv-whisperx` with PyTorch 2.6+/CUDA 12.x
- Organize test audio corpus (30-60 min total)
- Prepare ground truth transcriptions
- Validate both environments functional

### Day 2-3: A/B Testing Scripts Implementation
- Build accuracy comparison script (CER/WER)
- Build segment quality analysis script
- Build gibberish detection script
- Build performance benchmarking script
- Build GPU memory monitoring script

### Day 3-4: Benchmark Execution
- Run BELLE-2 tests on full corpus
- Run WhisperX tests on full corpus
- Consolidate results
- Generate comparison report

### Day 4-5: Analysis & Decision
- Analyze results across all 5 metrics
- Apply weighting formula
- Determine winner (or apply tiebreaker)
- Write phase gate decision report
- Get PM approval
- Define Epic 3 path forward (Stories 3.3-3.5 or 3.3-alt through 3.5-alt)

---

**Story Created:** 2025-11-14
**Last Updated:** 2025-11-14
**Owner:** Dev Team
**Reviewer:** PM (Link)
**Status:** In Progress
