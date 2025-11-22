# KlipNote Sprint Change Proposal
## Epic 4 API Enablement & Developer Tools

**Date:** 2025-11-22
**Project:** KlipNote - Zero-friction audio/video transcription
**Proposal Type:** Epic Scope Extension
**Estimated Impact:** +4-6 hours development, <1 business day delay
**Prepared by:** John (Product Manager)
**For Review by:** Link (Product Owner)

---

## Executive Summary

**Issue Identified:**
Epic 4 (Stories 4.1-4.6) successfully delivered a complete Enhancement Pipeline framework (VAD, Timestamp Refinement, Segment Splitting), but the functionality is **not API-accessible**, creating a critical usability gap.

**Proposed Solution:**
Add 3 new stories (4.7-4.9) to Epic 4 to expose enhancement configuration via API and develop HTTP-based CLI tools, transforming enhancement features from "exists" to "usable."

**Impact:**
- **MVP Scope:** Expanded from "Epic 1-3 + Epic 4 (Partial)" to "Epic 1-4 (Complete)"
- **Timeline:** +4-6 hours development (<1 business day)
- **Value:** Enhancement features become production-ready, NFR005 compliance guaranteed via API
- **Risk:** Low (incremental changes, backward compatible)

**Recommendation:** **APPROVE** - Minimal cost, high value, expert-validated solution

---

## 1. Problem Statement

### 1.1 Trigger Context

**Triggering Event:** Post-Epic 4 completion (Stories 4.1-4.6 marked `done`)

**Discovery:** During preparation for model selection decision (original Story 4.7), the team identified that:
- Enhancement components are **implemented** but **not API-exposed**
- No HTTP-based tools exist to test production workflows
- Belle2 (.venv) and WhisperX (.venv-whisperx) environment isolation complicates cross-model testing

**Expert Consultation:** Expert review (`docs/improvement/solution-design-2025-11-22.md`) recommended "API First + HTTP Thin Client" strategy with 4-6h effort estimate.

### 1.2 Core Problems

**Problem 1: API Layer Gap**
- **Current State:** Enhancement pipeline only configurable via backend `.env` variables
- **Impact:** Frontend and API clients cannot dynamically control VAD/refine/split settings per request
- **Evidence:** `/upload` endpoint lacks `enhancement_config` parameter

**Problem 2: Missing CLI Tools**
- **Current State:** Existing CLI tools (`compare_models.py`, `validate_quality.py`) directly import Python modules
- **Impact:** Cannot test production HTTP workflows, Docker container integration testing difficult
- **Evidence:** No HTTP-based client exists for end-to-end API testing

**Problem 3: Environment Conflicts**
- **Current State:** Belle2 (.venv) and WhisperX (.venv-whisperx) require separate virtual environments
- **Impact:** Cross-model comparison requires frequent environment switching, reducing developer productivity
- **Evidence:** PyTorch version conflicts (CUDA 11.8 vs CUDA 12.x)

### 1.3 Impact Assessment

**Functional Impact:**
- ✅ Enhancement components work correctly (validated in Stories 4.2-4.6)
- ❌ Enhancement features **not accessible** via API
- ❌ NFR005 compliance (1-7s segments, ≤200 chars) **cannot be guaranteed** at API layer

**PRD Alignment:**
- ⚠️ **Goal 5:** "Ensure transcription accuracy meets production standards" - partially achieved
- ⚠️ **NFR005:** Segment length compliance - not controllable via API
- ❌ **FR003c (missing):** Dynamic enhancement configuration via API

**Developer Productivity:**
- ❌ Cross-model testing requires virtual environment switching
- ❌ No rapid API workflow validation tools
- ❌ Docker container testing via direct Python imports (fragile)

---

## 2. Epic Impact Analysis

### 2.1 Current Epic Status

**Epic 4: Multi-Model Transcription Framework & Composable Enhancements**

**Completed Stories:**
- ✅ Story 4.1: Enhancement metadata schema
- ✅ Story 4.2: VAD preprocessing component
- ✅ Story 4.3: Timestamp refinement component
- ✅ Story 4.4: Segment splitting component
- ✅ Story 4.5: Enhancement pipeline composition
- ✅ Story 4.6: Multi-model quality validation framework

**Epic Status:** `contexted` (awaiting finalization)

### 2.2 Required Epic Changes

**Proposed Addition:** 3 new stories to Epic 4

**Story 4.7: Enhancement API Layer Development (1-2 hours)**
- Modify POST `/upload` endpoint to accept optional `enhancement_config` JSON parameter
- Update `EnhancementFactory.create_pipeline()` to support config injection
- Implement configuration priority: API param > env vars > defaults
- Maintain backward compatibility (missing config → use env vars)

**Story 4.8: HTTP CLI Tool Development (2-3 hours)**
- Create `backend/app/cli/klip_client.py` with commands: upload, status, result, test-flow
- Dependencies: `requests`/`httpx` only (no PyTorch/transformers)
- Environment-independent: decoupled from .venv and .venv-whisperx
- Comprehensive usage documentation

**Story 4.9: Model Testing & Documentation (1 hour)**
- Validate Belle2 and WhisperX workflows using new CLI tool
- Document test results for model selection decision
- Update README and architecture docs with Developer Tools section

**Epic Status Update:** `contexted` → `in_progress` → `done` (after 4.7-4.9 completion)

### 2.3 Impact on Other Epics

**Epic 1-3:** ✅ No impact (completed)
**Future Epics:** ✅ No impact (Epic 5+ not yet defined)
**Dependencies:** ✅ None - all changes contained within Epic 4

---

## 3. Artifact Conflict Analysis

### 3.1 PRD Modifications Required

**Document:** `docs/prd.md`

**Change 1: Epic 4 MVP Scope Redefinition (Lines 224-238)**

**Before:**
```markdown
Epic 4: Multi-Model Transcription Framework & Composable Enhancements 📋 POST-MVP

MVP Scope: Epics 1-3 + Validated Single Model Selection
- Epic 4 (Partial): Stories 4.6b + 4.7
  - Story 4.6b: Hand-verified accuracy baselines
  - Story 4.7: MVP model selection decision

Post-MVP: Epic 4 Remainder (Multi-Model Production Deployment)
```

**After:**
```markdown
Epic 4: Multi-Model Transcription Framework & Composable Enhancements ✅ MVP (Enhanced)

MVP Scope: Epics 1-4 (Core Enhancement Framework + API Layer)
- Epic 4 Stories 4.1-4.6: ✅ COMPLETE (Enhancement components)
- Epic 4 Stories 4.7-4.9: 🔄 IN PROGRESS (API enablement)
  - Story 4.7: Enhancement API layer (exposure via /upload endpoint)
  - Story 4.8: HTTP CLI tools (developer productivity)
  - Story 4.9: Model testing & documentation

Post-MVP: Frontend UI enhancement controls, advanced presets, multi-model production
```

**Change 2: Add FR003c (After Line 38)**

```markdown
- **FR003c:** System shall expose enhancement pipeline configuration via API parameters,
  enabling dynamic control of VAD, timestamp refinement, and segment splitting components
  on a per-request basis
```

**Change 3: Add NFR002b (After Line 74)**

```markdown
- **NFR002b: Developer Productivity:** Developers shall be able to test complete API
  workflows using HTTP-based CLI tools without environment-specific setup complexity
  or virtual environment switching
```

### 3.2 Architecture Document Modifications

**Document:** `docs/architecture.md`

**Change 1: API Endpoint Design Extension (§2156-2161)**

**Add new section:**

```markdown
### API Endpoint: POST /upload (Enhanced)

**Parameters:**
- `file` (required, multipart): Media file
- `model` (optional, form): belle2|whisperx|auto (default: auto)
- `language` (optional, form): zh|en|auto (default: auto)
- `enhancement_config` (optional, form): JSON string for enhancement configuration

**enhancement_config Structure:**
```json
{
  "pipeline": "vad,refine,split",
  "vad": {
    "engine": "silero",
    "threshold": 0.5,
    "min_silence_duration": 1.0
  },
  "refine": {
    "enabled": true
  },
  "split": {
    "max_duration": 7.0,
    "max_chars": 200
  }
}
```

**Configuration Priority:**
1. API `enhancement_config` parameter (highest)
2. Environment variables (.env)
3. Default values (lowest)

**Backward Compatibility:** Omitting `enhancement_config` uses environment configuration
```

**Change 2: Add Developer Tools Section (New §2800+)**

```markdown
## Developer Tools & Testing Infrastructure

### HTTP-based CLI Tool: klip_client.py

**Purpose:** Enable API workflow testing and cross-model validation without
environment-specific dependencies

**Architecture:**
- **Location:** `backend/app/cli/klip_client.py`
- **Dependencies:** `requests` or `httpx` (no PyTorch/transformers)
- **Independence:** Decoupled from Belle2 (.venv) and WhisperX (.venv-whisperx)

**Commands:**
```bash
# Upload with enhancement configuration
python klip_client.py upload \
  --file test-audio.mp3 \
  --model belle2 \
  --config '{"pipeline":"vad,split","split":{"max_duration":5.0}}'

# Poll job status
python klip_client.py status <job_id> [--watch]

# Fetch transcription result
python klip_client.py result <job_id> [--output result.json]

# Automated end-to-end test
python klip_client.py test-flow --file test-audio.mp3
```

**Benefits:**
1. Environment Independence: No virtual environment switching
2. Production Testing: Tests actual Docker containers via HTTP
3. Developer Productivity: Rapid iteration on API changes
4. CI/CD Integration: Automated workflow validation
```

### 3.3 Epics Document Modifications

**Document:** `docs/epics.md`

**Add to Epic 4 section:**

```markdown
### Story 4.7: Enhancement API Layer Development

**User Story:**
As a developer, I want to control enhancement pipeline configuration via API parameters,
so that I can dynamically adjust VAD/refine/split settings per transcription request.

**Acceptance Criteria:**
1. POST /upload accepts optional `enhancement_config` JSON parameter
2. EnhancementFactory.create_pipeline() supports config_dict injection
3. Configuration priority: API param > env vars > defaults
4. Backward compatible: missing enhancement_config uses env vars
5. Pydantic model validation for enhancement_config structure
6. API tests cover enhancement_config parameter scenarios
7. TypeScript type definitions updated (if frontend integration planned)

**Estimated Effort:** 1-2 hours

---

### Story 4.8: HTTP CLI Tool Development

**User Story:**
As a developer, I want an HTTP-based CLI tool to test API workflows, so that I can
validate end-to-end transcription without virtual environment switching.

**Acceptance Criteria:**
1. Create `backend/app/cli/klip_client.py` with commands: upload, status, result, test-flow
2. Dependencies: requests/httpx only (no PyTorch/transformers)
3. Support for enhancement_config parameter in upload command
4. --watch flag for status polling
5. JSON output format for result command
6. Automated test-flow validates: upload → poll → fetch → validate
7. README documentation with usage examples

**Estimated Effort:** 2-3 hours

---

### Story 4.9: Model Testing & Documentation

**User Story:**
As a product manager, I want validated test results for Belle2 and WhisperX using the
new CLI tool, so that I can make a data-driven model selection decision.

**Acceptance Criteria:**
1. Run klip_client.py test-flow for Belle2 with test samples
2. Run klip_client.py test-flow for WhisperX with test samples
3. Compare results using enhancement configurations
4. Document findings in decision log
5. Update README with CLI tool usage examples
6. Update architecture.md with Developer Tools section

**Estimated Effort:** 1 hour
```

### 3.4 Sprint Status Modifications

**Document:** `docs/sprint-artifacts/sprint-status.yaml`

```yaml
epic-4:
  status: in_progress  # Changed from: contexted
  stories:
    # ... existing 4.1-4.6 stories (all done) ...

    "4.7":
      title: "Enhancement API Layer Development"
      status: todo
      context_file: null

    "4.8":
      title: "HTTP CLI Tool Development"
      status: todo
      context_file: null

    "4.9":
      title: "Model Testing & Documentation"
      status: todo
      context_file: null
```

### 3.5 UI/UX Impact

**Result:** ✅ **No UI/UX changes required**

**Rationale:**
- All 3 stories target backend API and developer tools
- Frontend continues using enhancement features via .env configuration
- Future enhancement controls in frontend UI remain Post-MVP scope

---

## 4. Path Forward Evaluation

### 4.1 Option 1: Direct Adjustment (RECOMMENDED)

**Approach:** Add Stories 4.7-4.9 to Epic 4, complete API layer and dev tools

**Effort:** Low (4-6 hours development)
**Risk:** Low (incremental, backward compatible)
**Technical Debt:** Zero (complete feature delivery)
**Business Value:** ✅ High (Enhancement features become usable)

**Conclusion:** ✅ **VIABLE - Strongly Recommended**

### 4.2 Option 2: Rollback

**Approach:** Revert Stories 4.2-4.5 (Enhancement components)

**Effort:** High (12-14 hours)
**Risk:** High (regression bugs, wasted investment)
**Technical Debt:** Increases (need to redevelop later)
**Business Value:** ❌ Negative (loss of completed work)

**Conclusion:** ❌ **NOT VIABLE - Not Recommended**

### 4.3 Option 3: MVP Scope Reduction

**Approach:** Remove Epic 4 from MVP, defer to Post-MVP

**Effort:** Medium (6 hours documentation rollback)
**Risk:** Medium (violates NFR005 commitment)
**Technical Debt:** Accumulates (zombie code)
**Business Value:** ⚠️ Reduced (NFR005 not guaranteed)

**Conclusion:** ⚠️ **VIABLE but NOT Recommended**

### 4.4 Selected Path: Option 1

**Justification:**

**1. Minimal Effort (4-6h vs 12-14h or 6h with value loss)**

| Option | Dev Time | Risk | Tech Debt | Value |
|--------|----------|------|-----------|-------|
| **Option 1 ✅** | 4-6h | Low | Zero | High |
| Option 2 ❌ | 12-14h | High | New | Negative |
| Option 3 ⚠️ | 6h | Medium | Accumulates | Reduced |

**2. Lowest Risk**
- ✅ Backward compatible (optional API parameter)
- ✅ Isolated failure domain (CLI tool independent)
- ✅ Incremental changes (no refactoring of completed work)
- ✅ Expert-validated design (detailed in solution-design.md)

**3. Zero Technical Debt**
- ✅ API layer completes Enhancement feature delivery
- ✅ No "zombie code" or incomplete features
- ✅ Developer toolchain complete, improves long-term efficiency

**4. PRD Alignment**
- ✅ **Goal 5:** "Ensure transcription accuracy meets production standards"
- ✅ **NFR005:** API-controllable segment length compliance (1-7s, ≤200 chars)
- ✅ **NFR002b (new):** Developer productivity via HTTP CLI

**5. Team Morale**
- ✅ Positive closure for Epic 4 (complete delivery)
- ✅ Avoids rollback frustration
- ✅ Dev tools improve future efficiency

**Trade-offs Acknowledged:**
- ⚠️ Short-term: +4-6 hours development time
- ✅ Long-term: Zero tech debt, enhanced productivity

---

## 5. MVP Impact Statement

**MVP Scope Change:**

**Before:**
```
MVP = Epic 1-3 + Epic 4 (Partial: Stories 4.6b + 4.7)
```

**After:**
```
MVP = Epic 1-4 (Complete)
  - Epic 1-3: ✅ COMPLETE
  - Epic 4 Stories 4.1-4.6: ✅ COMPLETE (Enhancement components)
  - Epic 4 Stories 4.7-4.9: 🔄 IN PROGRESS (API enablement)
```

**Timeline Impact:**
- Original plan: Epic 1-3 completion = MVP ready
- Adjusted: Requires +4-6 hours for Epic 4 finalization
- **Total delay: <1 business day**

**Value Enhancement:**
- ✅ Enhancement features: "exists" → "usable"
- ✅ NFR005 compliance: guaranteed via API
- ✅ Developer productivity: HTTP CLI tools

**No Scope Creep:**
- This is **feature completion**, not new feature addition
- Epic 4 core work already done (Stories 4.1-4.6)
- Stories 4.7-4.9 are **enablement layer** for existing functionality

---

## 6. Implementation Plan

### Phase 1: Documentation Updates (1 hour)

**Owner:** Architect + Scrum Master

**Tasks:**
- [ ] **PRD Update** (`docs/prd.md`)
  - Modify Epic 4 MVP scope definition (lines 224-238)
  - Add FR003c (enhancement API requirement)
  - Add NFR002b (developer productivity)

- [ ] **Architecture Update** (`docs/architecture.md`)
  - Extend API endpoint design section (§2156-2161)
  - Add Developer Tools section (new §2800+)
  - Document configuration priority logic

- [ ] **Epics Update** (`docs/epics.md`)
  - Add Story 4.7 detailed specification
  - Add Story 4.8 detailed specification
  - Add Story 4.9 detailed specification

- [ ] **Sprint Status Update** (`docs/sprint-artifacts/sprint-status.yaml`)
  - Change epic-4 status: `contexted` → `in_progress`
  - Add stories 4.7-4.9 entries (status: `todo`)

**Dependencies:** PM approval
**Deliverable:** Updated documentation suite

---

### Phase 2: Story 4.7 - Enhancement API Layer (1-2 hours)

**Owner:** Developer

**Tasks:**
- [ ] **Backend API Modification**
  - Modify `backend/app/main.py` POST /upload endpoint
    - Add `enhancement_config: Optional[str]` parameter
    - JSON parsing and validation
  - Modify `backend/app/models.py`
    - Add `EnhancementConfigModel` Pydantic model
  - Modify `backend/app/ai_services/enhancement/factory.py`
    - `create_pipeline()` accepts `config_dict` parameter
    - Implement priority logic: API > env > defaults

- [ ] **Testing**
  - Create `tests/test_api_enhancement_config.py`
    - Test valid enhancement_config
    - Test invalid JSON format
    - Test backward compatibility (missing config)

**Dependencies:** Phase 1 complete
**Deliverable:** API accepts enhancement_config parameter

---

### Phase 3: Story 4.8 - HTTP CLI Tool (2-3 hours)

**Owner:** Developer

**Tasks:**
- [ ] **CLI Tool Implementation**
  - Create `backend/app/cli/klip_client.py`
    - Implement `upload` command (with enhancement_config support)
    - Implement `status` command (with --watch polling)
    - Implement `result` command (JSON output)
    - Implement `test-flow` command (end-to-end automation)
  - Update `requirements.txt`: add `requests` or `httpx`

- [ ] **Documentation**
  - Create `backend/app/cli/README.md`
    - Installation instructions
    - Command usage examples
    - Troubleshooting guide

**Dependencies:** Phase 2 complete
**Deliverable:** HTTP CLI tool ready

---

### Phase 4: Story 4.9 - Model Testing & Documentation (1 hour)

**Owner:** Developer → Product Manager

**Tasks:**
- [ ] **Model Validation**
  - Run `klip_client.py test-flow` for Belle2
    - Test sample: zh_medium_audio1
    - Record response time, CER/WER results
  - Run `klip_client.py test-flow` for WhisperX
    - Same test sample
    - Compare results

- [ ] **Documentation Finalization**
  - Update main `README.md` with CLI tools section
  - Record test results in decision log
  - Verify architecture.md Developer Tools section complete

**Dependencies:** Phase 3 complete
**Deliverable:** Validated test results, complete documentation

---

### Phase 5: Epic 4 Closure (30 minutes)

**Owner:** Scrum Master + Product Manager

**Tasks:**
- [ ] **Status Updates**
  - Update `sprint-status.yaml`: mark stories 4.7-4.9 as `done`
  - Update `sprint-status.yaml`: epic-4 status → `done`

- [ ] **Acceptance**
  - Verify all acceptance criteria met
  - End-to-end smoke test
  - Epic 4 retrospective (optional)

**Dependencies:** Phase 4 complete
**Deliverable:** Epic 4 COMPLETE

---

## 7. Agent Handoff Plan

### Product Manager (Link)

**Responsibilities:**
- ✅ Approve this Sprint Change Proposal
- ✅ Update PRD document (or delegate to Architect)
- ✅ Epic 4 final acceptance
- ✅ Model selection decision (based on Story 4.9 results)

**Action Items:**
1. Review and approve this proposal
2. Confirm MVP scope adjustment acceptable
3. Update `docs/prd.md` (or assign to Architect)
4. Phase 5: Epic 4 delivery acceptance

---

### Architect Agent

**Responsibilities:**
- ✅ Update Architecture documentation
- ✅ Technical solution review
- ✅ API design validation

**Action Items:**
1. Update `docs/architecture.md`:
   - API endpoint extension specification
   - Developer Tools section
   - Configuration priority documentation
2. Review Story 4.7 API design for backward compatibility
3. Review Story 4.8 CLI architecture for environment independence

---

### Developer Agent

**Responsibilities:**
- ✅ Implement Stories 4.7-4.9 code changes
- ✅ Write tests
- ✅ Update technical documentation

**Action Items:**

**Story 4.7 (1-2h):**
1. Modify `backend/app/main.py` POST /upload
2. Modify `backend/app/models.py` add EnhancementConfigModel
3. Modify `backend/app/ai_services/enhancement/factory.py`
4. Write API tests `tests/test_api_enhancement_config.py`

**Story 4.8 (2-3h):**
1. Create `backend/app/cli/klip_client.py`
2. Implement 4 commands: upload, status, result, test-flow
3. Update `requirements.txt` add requests/httpx
4. Create `backend/app/cli/README.md`

**Story 4.9 (1h):**
1. Run klip_client.py tests for Belle2 and WhisperX
2. Document test results
3. Update main README.md

---

### Scrum Master / Project Coordinator

**Responsibilities:**
- ✅ Update Sprint backlog
- ✅ Track progress
- ✅ Coordinate dependencies

**Action Items:**
1. Update `docs/sprint-artifacts/sprint-status.yaml`:
   - epic-4: `contexted` → `in_progress`
   - Add stories 4.7-4.9 (status: `todo`)
2. Update `docs/epics.md` add stories 4.7-4.9 specs
3. Monitor Phase 1-5 execution progress
4. Update status → `done` after Epic 4 completion

---

## 8. Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| API design requires rework | Low | Medium | Architect pre-review before implementation |
| CLI tool environment issues | Low | Low | Test requests/httpx dependencies early |
| Backward compatibility break | Very Low | High | Comprehensive API tests, optional parameter |
| Testing reveals model issues | Medium | Low | Expected - use results for model selection |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| PM approval delayed | Low | Low | Fast-track review (target <4 hours) |
| Phase 2 overruns estimate | Medium | Low | Buffer included in 1-2h estimate |
| Phase 3 CLI complexity | Low | Medium | Scope to MVP commands only |

### Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Stakeholder pushback on scope | Very Low | Medium | Clear communication: feature completion, not scope creep |
| Team morale if delayed | Low | Low | Transparent communication, <1 day delay |

**Overall Risk Level:** ✅ **LOW**

---

## 9. Success Criteria

### Technical Success
- ✅ POST /upload accepts `enhancement_config` parameter
- ✅ Backward compatible: existing clients continue working
- ✅ `klip_client.py` enables cross-model testing without environment switching
- ✅ End-to-end test-flow validates: upload → poll → fetch → validate
- ✅ All acceptance criteria for Stories 4.7-4.9 met

### Business Success
- ✅ Epic 4 delivers complete, usable Enhancement functionality
- ✅ NFR005 compliance (segment length) guaranteed via API
- ✅ Developer productivity improved (HTTP CLI tools)
- ✅ Model selection decision data-driven (Story 4.9 results)

### Timeline Success
- ✅ Total delay: <1 business day
- ✅ Phase 1-5 completed within 5-7 hours total
- ✅ Epic 4 marked `done` by end of week

---

## 10. Approval Request

**Requesting Approval From:** Link (Product Owner)

**This proposal requests approval to:**

1. ✅ Expand Epic 4 scope by adding Stories 4.7-4.9
2. ✅ Redefine MVP to include complete Epic 4 (vs partial)
3. ✅ Invest 4-6 hours development time for API enablement
4. ✅ Update PRD, Architecture, Epics, and Sprint Status documents
5. ✅ Accept <1 business day delay to MVP delivery

**Approval Options:**

**[ ] APPROVE** - Proceed with Epic 4 extension as proposed
**[ ] APPROVE WITH CONDITIONS** - Specify conditions: _______________
**[ ] REJECT** - Provide alternative approach: _______________

**Signature:** ________________________
**Date:** ________________________

---

## Appendices

### Appendix A: Expert Consultation Reference

**Document:** `docs/improvement/solution-design-2025-11-22.md`

**Key Recommendations:**
- API First Strategy: Expose enhancement_config via /upload endpoint
- HTTP Thin Client: Develop klip_client.py based on requests/httpx
- Unified Validation: Use API + CLI for cross-model testing

**Effort Estimate:** 4-6 hours (1-2h API + 2-3h CLI + 1h validation)

### Appendix B: Related Documents

- **Problem Analysis:** `docs/improvement/project-status-and-gaps-2025-11-22.md`
- **Solution Design:** `docs/improvement/solution-design-2025-11-22.md`
- **Current PRD:** `docs/prd.md`
- **Architecture:** `docs/architecture.md`
- **Epics:** `docs/epics.md`
- **Sprint Status:** `docs/sprint-artifacts/sprint-status.yaml`

---

**End of Sprint Change Proposal**
