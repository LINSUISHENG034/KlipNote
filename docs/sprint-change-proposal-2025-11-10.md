# Sprint Change Proposal - Mandarin Transcription Quality Enhancement

**Project:** KlipNote
**Date:** 2025-11-10
**Author:** John (Product Manager Agent)
**Prepared for:** Link
**Change Scope:** MODERATE - Add Epic 3 (6 stories)
**Sprint Duration:** 1-2 weeks (~27-44 hours)

---

## Executive Summary

This proposal addresses a post-MVP quality enhancement opportunity: improving KlipNote's Mandarin transcription quality to match the Whisper Desktop reference baseline. Technical research has been completed, identifying a two-track solution (BELLE-2 for accuracy + SenseVoice for latency) that leverages the existing ai_services abstraction architecture. This work requires adding Epic 3 with 6 stories, with no impact on delivered MVP functionality.

**Recommendation:** Approve Epic 3 implementation via 1-2 week sprint starting immediately.

---

## 1. Issue Summary

### Problem Statement

KlipNote's Mandarin (Chinese) transcription quality falls short of the Whisper Desktop reference baseline, resulting in user trust issues. The current WhisperX engine is optimized for English and lacks necessary tuning for Mandarin: beam search optimization, temperature fallback strategies, and language-specific suppression settings. This quality gap undermines user confidence and limits adoption in Mandarin-speaking markets.

### Discovery Context

- **When:** Post-MVP delivery (Epic 1 & 2 completed successfully)
- **How:** User feedback + proactive technical research
- **Documentation:** docs/research-technical-2025-11-09.md
- **Trigger:** Strategic enhancement opportunity, not a blocking defect

### Supporting Evidence

1. **Technical Research Completed (2025-11-09):**
   - Evaluated 4 ASR alternatives: BELLE-2, SenseVoice, Paraformer, FireRedASR
   - Identified two-track solution: BELLE-2 (accuracy) + SenseVoice (latency)
   - Validated hardware compatibility (RTX 3070 Ti 16GB constraints)
   - Established quality validation methodology (diff harness vs Const-me reference)

2. **Technical Constraints (from domain-brief.md):**
   - GPU budget: Limited to self-hosted RTX 3070 Ti for 10-20 concurrent users
   - Local/offline requirement: Cannot rely on cloud ASR APIs
   - Latency target: ≤2× realtime processing to maintain UX
   - Current stack: WhisperX optimized for English, Mandarin suffers

3. **User Impact:**
   - Quality gap vs. reference implementation (Whisper Desktop) erodes trust
   - Mandarin market adoption limited by transcription errors
   - Data flywheel quality compromised (poor AI output = poor training data)

### Scope Classification

- **Type:** Technical enhancement + strategic market positioning
- **Phase:** Post-MVP (all MVP requirements delivered successfully)
- **Priority:** HIGH (user trust + competitive positioning)
- **Urgency:** MEDIUM (not blocking, but impactful for growth)

---

## 2. Impact Analysis

### Epic Impact Summary

```
├── Epic 1 (Foundation & Core Transcription): ✅ Complete, NO CHANGES
├── Epic 2 (Integrated Review & Export): ✅ Complete, NO CHANGES
└── Epic 3 (Mandarin Quality Enhancement): 🆕 NEW EPIC REQUIRED
```

**Epic 3 Details:**
- **Title:** "Mandarin Transcription Quality Enhancement"
- **Purpose:** Upgrade ASR engine with language-specific optimizations
- **Stories:** 6 stories (integration, routing, validation, pilot, monitoring, docs)
- **Estimated Effort:** 27-44 hours (~1-2 week sprint)
- **Dependencies:** None (leverages existing architecture)
- **Deliverable:** Multi-model ASR support with Mandarin quality parity to reference

### Artifact Impact Assessment

#### 1. PRD (docs/PRD.md)

**Section: Functional Requirements - File Upload & Processing**

**⚠️ FR003 - Update:**
```
OLD: "FR003: System shall process uploaded media files using WhisperX transcription
      engine with word-level timestamps..."

NEW: "FR003: System shall process uploaded media files using AI transcription services
      (WhisperX, BELLE-2, SenseVoice, or compatible alternatives) with word-level
      timestamps, automatically detecting and preserving the original audio language"
```

**➕ FR021 - Add New:**
```
"FR021: System shall support multiple transcription models with language-specific
 optimizations, allowing automatic model selection based on detected audio language"
```

**Impact:** Minor wording update, formalizes multi-model architecture
**MVP Status:** NO IMPACT (MVP complete)

#### 2. Architecture (docs/architecture.md)

**Section: Technology Foundation (Line 30)**
```
OLD: "Backend: FastAPI + Celery + Redis + WhisperX"
NEW: "Backend: FastAPI + Celery + Redis + ASR Services (WhisperX, BELLE-2, SenseVoice)"
```

**Section: AI Services Module**
- ➕ Add: app/ai_services/belle_whisper_service.py
- ➕ Add: app/ai_services/sensevoice_service.py
- ✏️ Update: get_transcription_service() factory with language routing

**Section: GPU Environment Requirements**
- ➕ Add: BELLE-2 VRAM requirements (~1.55B params, same as Whisper large)
- ➕ Add: SenseVoice ONNX runtime requirements
- ✏️ Update: Model cache directory structure

**Section: Testing Strategy**
- ➕ Add: Mock fixtures for new services (mock_belle, mock_sensevoice)
- ➕ Add: Integration tests for model routing logic

**Impact:** Moderate updates, but architecture ALREADY supports this change
**Risk:** LOW (abstraction layer was designed for model swapping)

#### 3. UI/UX Specifications

**Impact:** NONE
**Rationale:** Quality improvement is transparent to users
**Optional Future:** Model selection UI (defer to later epic)

#### 4. Deployment & Infrastructure

**Files Affected:**
- `backend/requirements.txt` → Add: belle-whisper, sensevoice, funasr packages
- `backend/Dockerfile` → Update: Model cache volume mappings
- `docker-compose.yaml` → Update: Volume size (5GB → 10GB for multi-model cache)

**Impact:** Standard dependency updates, follows existing patterns

#### 5. Testing Artifacts

**New Test Files:**
- `tests/test_belle_whisper_service.py`
- `tests/test_sensevoice_service.py`
- `tests/test_model_routing.py`
- `tests/integration/test_mandarin_quality.py`

**Impact:** Significant test expansion, clear scope

#### 6. Documentation

**Files to Update:**
- `README.md` → Add "Multi-Model Support" section
- `docs/SETUP.md` → Add model installation instructions

**New Files:**
- `docs/MODELS.md` → Model comparison, selection guide, troubleshooting

**Impact:** Standard documentation updates

### MVP Impact

**MVP Status:** ✅ COMPLETE (Epic 1 & 2 delivered successfully)

**MVP Goals - Impact Analysis:**
1. "Enable self-service transcription workflow" → ✅ NO IMPACT (maintained)
2. "Eliminate cost and duration barriers" → ✅ NO IMPACT (staying local/offline)
3. "Validate data flywheel foundation" → ✅ ENHANCED (better quality data)
4. "Prove technical feasibility" → ✅ NO IMPACT (validated)

**NFR Impact:**
- NFR001 (Performance): MAINTAINED OR IMPROVED
  - BELLE-2: Same as current (1-2× realtime)
  - SenseVoice: BETTER (0.07× realtime, 15× faster)
- NFR002 (Usability): MAINTAINED (transparent to users)
- NFR003 (Reliability): MAINTAINED (existing patterns)
- NFR004 (Compatibility): MAINTAINED (no UI changes)

**Conclusion:** This is a QUALITY ENHANCEMENT that strengthens MVP outcomes without disrupting delivered functionality. MVP definition remains unchanged.

---

## 3. Recommended Approach

### Selected Strategy: Option 1 - Direct Adjustment (Add Epic 3)

**Implementation Strategy: Two-Track Incremental Delivery**

### Track 1: Quick Win - BELLE-2 Integration (Stories 3.1, 3.2, 3.3)

**Story 3.1: BELLE-2 Whisper-Large-v3-zh Integration**
- Implement BelleWhisperService class following WhisperXService pattern
- Add model to ai_services factory
- Configure model download and caching (Hugging Face transformers)
- **Effort:** 5-8 hours
- **Value:** Drop-in replacement, 24-65% CER improvement on benchmarks

**Story 3.2: Language Detection & Model Routing Logic**
- Implement language detection (leverage WhisperX's built-in detection)
- Create model selection algorithm: Mandarin → BELLE-2, Others → WhisperX
- Update get_transcription_service() factory with routing logic
- **Effort:** 3-5 hours
- **Value:** Automatic model selection, zero user friction

**Story 3.3: Quality Validation Framework (Diff Harness)**
- Create Const-me reference transcript comparison tool
- Implement CER (Character Error Rate) calculation utilities
- Build automated quality regression tests
- **Effort:** 5-8 hours
- **Value:** Objective quality validation, prevents regressions

**Track 1 Subtotal:** 13-21 hours (~3-5 days)
**Track 1 Outcome:** Mandarin quality parity with reference, validated via diff harness

### Track 2: Performance Optimization - SenseVoice Pilot (Stories 3.4, 3.5, 3.6)

**Story 3.4: SenseVoice-Small ONNX Pilot Implementation**
- Implement SenseVoiceService class with ONNX runtime
- Integrate FunASR tooling for VAD and chunking
- Benchmark latency on RTX 3070 Ti (target: ≤1.5× realtime)
- **Effort:** 8-13 hours
- **Value:** 15× throughput vs Whisper, better concurrency support

**Story 3.5: Model Performance Monitoring & Logging**
- Add model name to transcription job logs
- Track performance metrics per model (latency, throughput)
- Implement model usage analytics
- **Effort:** 3-5 hours
- **Value:** Operational visibility, data-driven optimization

**Story 3.6: Documentation & Deployment Updates**
- Update README with multi-model support information
- Create docs/MODELS.md with model comparison guide
- Update Docker configuration for new models
- **Effort:** 3-5 hours
- **Value:** Team knowledge transfer, smooth deployment

**Track 2 Subtotal:** 14-23 hours (~4-6 days)
**Track 2 Outcome:** Low-latency mode validated, monitoring in place, docs complete

### Total Effort

**Total Effort:** 27-44 hours (1-2 week sprint for 1 developer)

### Rationale

**✅ Technical Feasibility: HIGH**
- Architecture already designed with ai_services abstraction for model swapping
- Research phase complete with validated technical approach
- Hardware constraints verified (models fit RTX 3070 Ti 16GB)
- No breaking changes to existing functionality

**✅ Risk Mitigation: EXCELLENT**
- Incremental delivery allows validation at each step
- WhisperX remains as fallback if new models fail
- Diff harness provides objective quality gate
- Can abort Track 2 if Track 1 sufficient

**✅ Business Value: HIGH**
- Addresses immediate user trust issue (Mandarin quality gap)
- Validates data flywheel with better training data
- Competitive positioning in Mandarin market
- Quick win available (BELLE-2 in ~1 week)

**✅ Resource Efficiency: OPTIMAL**
- Leverages completed research (no discovery work needed)
- Follows established architecture patterns (minimal learning curve)
- 1-2 week timeline is reasonable for high-impact work
- No external dependencies or coordination overhead

**✅ Long-term Sustainability: STRONG**
- Modular design enables future language optimizations
- Test coverage expansion follows existing patterns
- Documentation ensures team knowledge transfer
- Monitoring provides data for continuous improvement

### Alternatives Considered & Rejected

- **❌ Option 2 (Rollback):** No rollback scenario exists, would destroy working MVP
- **❌ Option 3 (MVP Review):** Already post-MVP, no scope reduction needed
- **❌ Hybrid Approach:** Adds complexity without benefit, Option 1 is cleaner

### Success Criteria

1. **BELLE-2:** ≤5% CER delta vs Const-me reference on noisy meetings
2. **SenseVoice:** ≤1.5× realtime latency on RTX 3070 Ti, accuracy within ~5% of BELLE-2
3. **Zero regression** in existing WhisperX functionality (all tests pass)
4. **Quality diff harness** operational and integrated into CI
5. **Documentation complete** (README, MODELS.md, architecture updates)

---

## 4. Detailed Change Proposals

### PRD Changes

#### Change 1: Update FR003
**File:** docs/PRD.md
**Section:** Functional Requirements - File Upload & Processing (Line ~37)

**Before:**
```markdown
- **FR003:** System shall process uploaded media files using WhisperX transcription
  engine with word-level timestamps, automatically detecting and preserving the
  original audio language
```

**After:**
```markdown
- **FR003:** System shall process uploaded media files using AI transcription services
  (WhisperX, BELLE-2, SenseVoice, or compatible alternatives) with word-level
  timestamps, automatically detecting and preserving the original audio language
```

**Rationale:** Enables model flexibility while maintaining quality requirements. Reflects architectural capability to support multiple ASR models.

---

#### Change 2: Add FR021
**File:** docs/PRD.md
**Section:** Functional Requirements - After FR020 (Line ~67)

**Add New Requirement:**
```markdown
- **FR021:** System shall support multiple transcription models with language-specific
  optimizations, allowing automatic model selection based on detected audio language
```

**Rationale:** Formalizes multi-model architecture support, enabling language-specific quality improvements (e.g., BELLE-2 for Mandarin, WhisperX for other languages).

---

### Architecture Changes

#### Change 3: Update Technology Foundation
**File:** docs/architecture.md
**Section:** Technology Foundation (Line 30)

**Before:**
```markdown
- Backend: FastAPI + Celery + Redis + WhisperX
```

**After:**
```markdown
- Backend: FastAPI + Celery + Redis + ASR Services (WhisperX, BELLE-2, SenseVoice)
```

**Rationale:** Reflect multi-model support in technology stack overview.

---

#### Change 4: Expand AI Services Module
**File:** docs/architecture.md
**Section:** AI Services Module

**Add New Implementations:**
- `app/ai_services/belle_whisper_service.py` - BELLE-2 Whisper integration
- `app/ai_services/sensevoice_service.py` - SenseVoice ONNX integration

**Update Factory Pattern:**
```python
# app/ai_services/__init__.py
def get_transcription_service(language: str = None) -> TranscriptionService:
    """
    Factory for transcription services with language-based routing.

    Routing logic:
    - Mandarin (zh, zh-CN, zh-TW) → BelleWhisperService
    - Other languages → WhisperXService (default)
    - Future: Add more language-optimized models
    """
    if language and language.startswith('zh'):
        return BelleWhisperService()
    return WhisperXService()
```

**Rationale:** Implements language-aware model selection while maintaining abstraction pattern.

---

### Story File Creation

The following story files will be created by the Scrum Master agent:

1. `docs/stories/3-1-belle2-integration.md`
2. `docs/stories/3-2-model-routing-logic.md`
3. `docs/stories/3-3-quality-validation-framework.md`
4. `docs/stories/3-4-sensevoice-pilot.md`
5. `docs/stories/3-5-monitoring-logging.md`
6. `docs/stories/3-6-documentation-deployment.md`

Each story file will include:
- User story format
- Detailed acceptance criteria
- Technical implementation notes
- Testing requirements
- Definition of Done

---

## 5. Implementation Handoff

### Change Scope Classification: MODERATE

**Scope Breakdown:**
- Technical Complexity: MODERATE (new model integrations, routing logic)
- Architecture Impact: LOW (leverages existing abstraction)
- Team Coordination: LOW (single developer, no external dependencies)
- Documentation: MODERATE (new model guide, architecture updates)
- **Overall: MODERATE SCOPE** → Route to Scrum Master + Development Team

### Handoff Recipients & Responsibilities

#### 1. Scrum Master (SM) Agent - PRIMARY HANDOFF

**Responsibilities:**
- Create Epic 3 in sprint-status.yaml
  - Epic ID: `epic-3`
  - Status: `backlog` → `contexted` (after tech spec if needed)
- Create 6 story files in `docs/stories/`
- Update sprint-status.yaml with Epic 3 entries
- Schedule 1-2 week sprint

**Timeline:** 1-2 hours for story creation

**Deliverable to Dev Team:** Story files with acceptance criteria, ready-for-dev status

#### 2. Development Team (Dev) Agent - IMPLEMENTATION

**Responsibilities:**
- Implement all 6 stories following acceptance criteria
- Write unit tests with new mock fixtures
- Write integration tests for model routing
- Update deployment configurations
- Update documentation

**Timeline:** 27-44 hours (1-2 weeks full-time)

**Deliverable to SM:** Completed stories with tests passing, ready for review

#### 3. Product Manager (PM) Agent - OPTIONAL REVIEW

**Responsibilities:**
- Review Sprint Change Proposal (this document)
- Approve PRD updates (FR003, FR021)
- Validate alignment with product vision
- Sign off on Epic 3 completion

**Trigger:** After Epic 3 implementation complete

**Deliverable:** Updated PRD with formal approval

### Reference Documents

- **Sprint Change Proposal:** docs/sprint-change-proposal-2025-11-10.md (this document)
- **Technical Research:** docs/research-technical-2025-11-09.md
- **Domain Brief:** docs/domain-brief.md
- **Current PRD:** docs/PRD.md
- **Current Architecture:** docs/architecture.md
- **Sprint Status:** docs/sprint-status.yaml

### Success Criteria for Handoff

1. ✅ SM creates all Epic 3 story files
2. ✅ SM updates sprint-status.yaml with Epic 3 entries
3. ✅ Dev team acknowledges sprint scope and capacity
4. ✅ All reference documents accessible to dev team
5. ✅ Quality validation approach understood

### Timeline

```
├─ T+0 (Today): Sprint Change Proposal approved
├─ T+1 day: SM creates story files and updates sprint status
├─ T+2 days: Dev team begins Story 3.1 (BELLE-2 integration)
├─ T+5 days: Track 1 complete (Stories 3.1-3.3)
├─ T+10 days: Track 2 complete (Stories 3.4-3.6)
└─ T+12 days: Epic 3 complete, ready for PM review
```

**Total Duration:** ~2 weeks from approval to completion

---

## 6. High-Level Action Plan

### Phase 1: Foundation (Week 1, Days 1-3)

**Action 1.1: Create Epic 3 Structure**
- Create docs/epics/epic-3-mandarin-quality.md
- Update sprint-status.yaml with Epic 3 entries
- **Duration:** 1 hour

**Action 1.2: Story 3.1 - BELLE-2 Integration**
- Implement BelleWhisperService class
- Update ai_services factory
- Configure model download (Hugging Face)
- **Duration:** 5-8 hours
- **Deliverable:** BELLE-2 model operational

**Action 1.3: Story 3.2 - Model Routing Logic**
- Implement language detection
- Create routing algorithm (Mandarin → BELLE-2)
- Update factory with selection logic
- **Duration:** 3-5 hours
- **Deliverable:** Automatic model selection working

**Action 1.4: Story 3.3 - Quality Validation**
- Build diff harness against Const-me references
- Implement CER calculation
- Create automated regression tests
- **Duration:** 5-8 hours
- **Deliverable:** Quality gate operational

**Phase 1 Gate:** BELLE-2 quality validated ≤5% CER delta, proceed to Phase 2

### Phase 2: Optimization (Week 1-2, Days 4-7)

**Action 2.1: Story 3.4 - SenseVoice Pilot**
- Implement SenseVoiceService with ONNX
- Integrate FunASR tooling
- Benchmark on RTX 3070 Ti
- **Duration:** 8-13 hours
- **Deliverable:** Low-latency mode available

**Action 2.2: Story 3.5 - Monitoring & Logging**
- Add model tracking to job logs
- Implement performance metrics
- Create usage analytics
- **Duration:** 3-5 hours
- **Deliverable:** Operational visibility

**Action 2.3: Story 3.6 - Documentation**
- Update README, architecture docs
- Create MODELS.md guide
- Update deployment configs
- **Duration:** 3-5 hours
- **Deliverable:** Complete documentation

**Phase 2 Gate:** All tests passing, documentation complete, ready for production

### Phase 3: Deployment (Week 2, Day 8)

**Action 3.1: Artifact Updates**
- Update PRD (FR003, add FR021)
- Update architecture.md sections
- Update sprint-status.yaml (mark Epic 3 done)
- **Duration:** 2 hours

**Action 3.2: Production Deployment**
- Deploy updated Docker containers
- Verify model downloads
- Monitor initial transcriptions
- **Duration:** 2 hours

---

## 7. Risk Mitigation

### Technical Risks

**Risk 1: BELLE-2 quality does not meet ≤5% CER target**
- **Likelihood:** LOW (research validates approach)
- **Impact:** MEDIUM (Track 1 value reduced)
- **Mitigation:** Diff harness provides early validation; can tune beam search parameters
- **Fallback:** Keep WhisperX as default, mark BELLE-2 as experimental

**Risk 2: SenseVoice ONNX integration complexity exceeds estimate**
- **Likelihood:** MEDIUM (new runtime, less documentation)
- **Impact:** LOW (Track 2 is optional enhancement)
- **Mitigation:** Track 1 delivers standalone value; Track 2 can be deferred
- **Fallback:** Skip Story 3.4, proceed with BELLE-2 only

**Risk 3: Model cache storage exceeds 10GB limit**
- **Likelihood:** LOW (models total ~6-7GB)
- **Impact:** LOW (infrastructure adjustment)
- **Mitigation:** Monitor storage during Story 3.1; expand volume if needed
- **Fallback:** Implement model pruning or on-demand download

### Schedule Risks

**Risk 4: Sprint extends beyond 2 weeks**
- **Likelihood:** LOW (effort estimates conservative)
- **Impact:** MEDIUM (delays other work)
- **Mitigation:** Track 1 (high value) prioritized; Track 2 can slip if needed
- **Fallback:** Ship Track 1, defer Track 2 to next sprint

### Operational Risks

**Risk 5: Production deployment causes WhisperX regression**
- **Likelihood:** VERY LOW (architecture isolates services)
- **Impact:** HIGH (breaks existing functionality)
- **Mitigation:** Comprehensive test suite, WhisperX tests remain in place
- **Fallback:** Immediate rollback via git revert, WhisperX remains operational

---

## 8. Approval & Sign-Off

**Proposal Status:** ✅ APPROVED

**Approved By:** Link
**Approval Date:** 2025-11-10
**Approval Method:** Verbal confirmation during Course Correction workflow

**Next Actions:**
1. ✅ Generate Sprint Change Proposal document (COMPLETE)
2. → Load Scrum Master (SM) agent
3. → SM creates Epic 3 story files
4. → Dev team begins sprint

---

## 9. Appendix

### A. Epic 3 Story Summary

| Story ID | Title | Effort | Track | Dependencies |
|----------|-------|--------|-------|--------------|
| 3.1 | BELLE-2 Integration | 5-8h | 1 | None |
| 3.2 | Model Routing Logic | 3-5h | 1 | 3.1 |
| 3.3 | Quality Validation Framework | 5-8h | 1 | 3.1, 3.2 |
| 3.4 | SenseVoice Pilot | 8-13h | 2 | 3.1, 3.2 |
| 3.5 | Monitoring & Logging | 3-5h | 2 | 3.1, 3.2 |
| 3.6 | Documentation | 3-5h | 2 | All |

**Total:** 27-44 hours

### B. Model Comparison Reference

| Model | Accuracy (AISHELL-1 CER) | Throughput | VRAM | Use Case |
|-------|-------------------------|------------|------|----------|
| WhisperX | ~8% | 1-2× RT | 6GB | General purpose (current) |
| BELLE-2 | ~2.78% | 1-2× RT | 6GB | Mandarin quality (Track 1) |
| SenseVoice | ~5% (est.) | 0.07× RT | 4GB | Low-latency Mandarin (Track 2) |

### C. Quality Validation Methodology

**Diff Harness Components:**
1. Reference transcripts from Const-me Whisper Desktop
2. CER (Character Error Rate) calculator
3. Automated comparison script
4. Regression test suite

**Quality Gate:**
- BELLE-2 must achieve ≤5% CER delta vs Const-me on 3+ noisy meeting samples
- Zero hallucination loops (manual review)
- Timestamp stability within ±0.5s (automated check)

---

**Document Version:** 1.0
**Generated By:** BMad Course Correction Workflow
**Workflow Version:** 4-implementation/correct-course
**Generation Date:** 2025-11-10

---

_This Sprint Change Proposal was generated using the BMad Method Course Correction workflow, which systematically analyzes change impacts, evaluates path options, and produces actionable implementation plans with clear handoff responsibilities._
