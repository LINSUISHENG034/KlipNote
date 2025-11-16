# Sprint Change Proposal - Frontend Model Selection Story Addition

**Date:** 2025-11-16
**Project:** KlipNote
**Trigger:** Story 4.1 completion revealed missing frontend model selection story
**Scope:** Minor - Single story addition
**Status:** Pending approval

---

## 1. Issue Summary

### Problem Statement

Epic 4 successfully implemented multi-model backend architecture (Story 4.1 ✅), enabling both BELLE-2 and WhisperX to coexist with isolated Docker environments. However, Epic 4 lacks an explicit story for the frontend UI that allows users to select which transcription model to use at upload time.

This was always part of Epic 4's vision ("runtime model selection") but was not explicitly written as a story in the epic breakdown.

### Context

- **When discovered:** After Story 4.1 completion (2025-11-16)
- **How discovered:** User inquiry about prioritizing frontend integration for practical testing
- **Current state:** Multi-model backend works via API, but no user-facing UI for model selection

### Evidence

1. **Epic 4 goal states:** "Enable runtime model selection and component composition"
2. **Story 4.7 exists** but focuses on selecting ONE default model for MVP, not building the selection UI
3. **Backend implementation (Story 4.1)** already supports model routing via task queues
4. **No story covers:** Frontend dropdown/radio buttons for model choice

---

## 2. Impact Analysis

### Epic Impact

**Epic 4: Multi-Model Transcription Framework**

- **Status:** Can be completed, but missing critical user-facing component
- **Required change:** Add Story 4.1b between Story 4.1 and Story 4.2
- **Priority shift:** Story 4.1b should be implemented before enhancement components (4.2-4.6) to enable practical testing workflow

**Remaining Epics:** No future epics defined, no impact

### Story Impact

**Current Stories (4.2-4.7):** No breaking changes
- Stories 4.2-4.6: Enhancement components work independently
- Story 4.7: Still about choosing default model, not building UI (which 4.1b now handles)

**Future Stories:** Benefit from having testable model selection UI

### Artifact Conflicts

**PRD:**
- ✅ No conflicts - this enhances PRD delivery
- No requirement modifications needed

**Architecture Document:**
- ⚠️ Needs update: Upload API contract to include `model` parameter
- ⚠️ Needs addition: Document model selection UI component

**UI/UX Specifications:**
- ⚠️ Needs addition: Model selection control design (currently no UI/UX doc for Epic 4)

**Other Artifacts:**
- Testing strategy: Enables manual testing workflow
- Documentation: User guide needs model selection instructions

---

## 3. Recommended Approach

### Selected Path: Direct Adjustment (Add Story 4.1b)

**Rationale:**

1. **Low effort, high value:** 2-4 hour implementation that unblocks testing for all Epic 4 work
2. **Always intended:** This was part of Epic 4 vision, just not explicitly documented
3. **Enables pragmatic development:** Manual testing becomes straightforward
4. **No disruption:** Doesn't invalidate any existing work or future stories
5. **Minimal risk:** Straightforward UI implementation, backend already supports it

### Alternatives Considered

| Option | Viability | Reasoning |
|--------|-----------|-----------|
| Skip story, test via API tools | ❌ Rejected | Poor developer experience, doesn't validate user workflow |
| Defer to post-MVP | ❌ Rejected | Defeats purpose of multi-model framework in Epic 4 |
| Combine with Story 4.7 | ❌ Rejected | Story 4.7 is about default selection strategy, not UI implementation |
| **Add Story 4.1b** | ✅ **Selected** | Minimal disruption, high pragmatic value, aligns with Epic 4 vision |

### Effort & Risk Assessment

- **Implementation effort:** Low (2-4 hours)
- **Technical risk:** Low (frontend dropdown + API param)
- **Schedule impact:** None (can be completed within current sprint)
- **Scope impact:** Additive, not scope creep

---

## 4. Detailed Change Proposals

### Change 1: Add Story 4.1b to epics.md

**File:** `E:\Projects\KlipNote\docs\epics.md`
**Location:** Epic 4, after Story 4.1, before Story 4.2

**Addition:**

```markdown
**Story 4.1b: Frontend Model Selection UI** 📋 PLANNED

As a user,
I want to select which transcription model to use before uploading my file,
So that I can choose between BELLE-2 and WhisperX based on my specific needs.

**Acceptance Criteria:**
1. Upload view displays model selection control (radio buttons or dropdown)
2. Model options: "BELLE-2 (Mandarin-optimized)" and "WhisperX (Multi-language)"
3. Default selection: BELLE-2 (configurable via environment variable)
4. Selected model stored in component state (Pinia store)
5. Upload API call includes `model` parameter based on user selection
6. Model selection persists in localStorage for user convenience
7. Tooltip/help text explains key differences between models
8. Responsive design: model selection works on mobile/tablet
9. Backend validates model parameter and routes to appropriate worker
10. Integration test: Upload with each model, verify correct worker processes job

**Prerequisites:** Story 4.1 (multi-model backend architecture)
```

**Justification:** Bridges backend capability (Story 4.1) with user-facing interaction, delivering on Epic 4's "runtime model selection" promise.

---

### Change 2: Update sprint-status.yaml

**File:** `E:\Projects\KlipNote\docs\sprint-artifacts\sprint-status.yaml`
**Location:** Epic 4 development_status section

**OLD:**
```yaml
  epic-4: contexted
  4-1-multi-model-production-architecture: done
  4-2-model-agnostic-vad-preprocessing: backlog
```

**NEW:**
```yaml
  epic-4: contexted
  4-1-multi-model-production-architecture: done
  4-1b-frontend-model-selection: backlog
  4-2-model-agnostic-vad-preprocessing: backlog
```

**Justification:** Inserts new story into tracking system with backlog status.

---

### Change 3: Update Architecture API Contract

**File:** `E:\Projects\KlipNote\docs\architecture.md`
**Location:** Frontend API Client section (around line 416)

**OLD:**
```typescript
export async function uploadFile(file: File) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) throw new Error(await response.text())
  return response.json()
}
```

**NEW:**
```typescript
export async function uploadFile(file: File, model: 'belle2' | 'whisperx' = 'belle2') {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('model', model)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData
  })

  if (!response.ok) throw new Error(await response.text())
  return response.json()
}
```

**Justification:** Documents API contract change to support model parameter. Backend already implements this routing from Story 4.1.

---

## 5. Implementation Handoff

### Change Scope Classification

**Scope:** ✅ **Minor** - Direct implementation by development team

This is a straightforward story addition within existing epic structure. No backlog reorganization or fundamental replan needed.

### Implementation Sequence

**Immediate (This Sprint):**

1. ✅ **PM (This session):** Approve Sprint Change Proposal
2. **PM:** Update epics.md with Story 4.1b
3. **PM:** Update sprint-status.yaml with 4-1b entry
4. **PM:** Update architecture.md with API contract
5. **SM:** Create story file `4-1b-frontend-model-selection.md` in stories folder
6. **SM:** Mark story as "drafted" in sprint-status.yaml
7. **Dev:** Implement Story 4.1b (estimated 2-4 hours)

**Story Priority:**

Story 4.1b should be implemented **before** Stories 4.2-4.6 because:
- Enables manual testing of Story 4.1's multi-model backend
- Provides practical development workflow for enhancement components
- Delivers user-visible value earlier

### Handoff Recipients & Responsibilities

| Role | Responsibility | Deliverable |
|------|---------------|-------------|
| **Product Manager** | Document story, update artifacts | Updated epics.md, sprint-status.yaml, architecture.md |
| **Scrum Master** | Draft story file, update tracking | Story file created, status updated to "drafted" |
| **Developer** | Implement frontend model selection | Working model selection UI integrated with backend |

### Success Criteria

**Story 4.1b is considered complete when:**

1. ✅ Upload view has visible model selection control
2. ✅ Users can choose between BELLE-2 and WhisperX
3. ✅ Upload API includes model parameter
4. ✅ Backend routes jobs to correct worker based on selection
5. ✅ Integration tests verify both models work via UI
6. ✅ Model preference persists in localStorage

---

## 6. Timeline & Dependencies

### Dependencies

- **Story 4.1b depends on:** Story 4.1 ✅ (already complete)
- **Stories 4.2-4.7:** No hard dependencies, but benefit from 4.1b

### Timeline Impact

- **Implementation time:** 2-4 hours
- **Sprint impact:** None - fits within current sprint capacity
- **MVP timeline:** No delay - additive story

### Risk Mitigation

**Identified Risks:**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Backend model param not supported | Low | Medium | Story 4.1 already implemented routing; verify in acceptance testing |
| UI complexity underestimated | Low | Low | Simple dropdown/radio buttons; well-defined acceptance criteria |
| Testing overhead | Low | Low | Integration tests reuse existing upload test infrastructure |

**Overall Risk Level:** ✅ **Low**

---

## 7. Approval & Next Steps

### Approval Status

- [x] **Product Manager approval:** ✅ APPROVED (2025-11-16)
- [x] **Stakeholder notification:** Complete

### Next Steps Upon Approval

1. **PM:** Execute artifact updates (epics.md, sprint-status.yaml, architecture.md)
2. **SM:** Create story file `docs/stories/4-1b-frontend-model-selection.md`
3. **SM:** Update sprint-status.yaml: `4-1b-frontend-model-selection: drafted`
4. **Dev:** Implement Story 4.1b following acceptance criteria
5. **SM:** Code review when Story 4.1b complete
6. **PM:** Verify story delivers on Epic 4 "runtime model selection" goal

---

## 8. Summary

**Change Type:** Story addition
**Scope:** Minor - single story within existing epic
**Effort:** Low (2-4 hours)
**Risk:** Low
**Value:** High (enables testing, delivers on Epic 4 vision)

**Recommendation:** ✅ **Approve and implement Story 4.1b immediately**

This change addresses a gap in Epic 4 planning without disrupting any existing work. It enables practical testing of the multi-model backend and delivers on Epic 4's promise of runtime model selection.

---

**Document prepared by:** Product Manager (John)
**Date:** 2025-11-16
**Status:** Awaiting approval
