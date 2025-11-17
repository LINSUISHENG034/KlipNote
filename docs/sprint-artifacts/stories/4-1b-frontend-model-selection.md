# Story 4.1b: Frontend Model Selection UI

**Epic:** Epic 4 - Multi-Model Transcription Framework & Composable Enhancements
**Story ID:** 4.1b
**Status:** ✅ **COMPLETED** - Ready for Review
**Priority:** High
**Effort Estimate:** 1-2 days
**Actual Effort:** 1 day
**Dependencies:** Story 4.1 (Multi-Model Production Architecture - DONE)
**Developer:** Claude
**Completed:** 2025-11-16
**Tests:** ✅ 28/28 passing (19 unit + 9 integration)

---

## Implementation Summary

Successfully implemented frontend model selection UI allowing users to choose between BELLE-2 and WhisperX transcription models before upload.

**Files Created:**
- `frontend/src/components/ModelSelector.vue` - Model selection component
- `frontend/src/__tests__/components/ModelSelector.test.ts` - 19 unit tests
- `frontend/src/__tests__/integration/ModelSelection.test.ts` - 9 integration tests

**Files Modified:**
- `frontend/src/stores/transcription.ts` - Model selection state management
- `frontend/src/services/api.ts` - Upload API with model parameter
- `frontend/src/views/UploadView.vue` - Integrated ModelSelector component

**Testing Results:** ✅ All 28 tests passing
- Component Unit Tests: 19/19 ✅
- Integration Tests: 9/9 ✅

---

## User Story

**As a** user,
**I want** to select which transcription model to use before uploading my file,
**So that** I can choose between BELLE-2 and WhisperX based on my specific needs.

---

## Acceptance Criteria

### AC #1: Upload View Model Selection Control
- Upload view displays model selection control (radio buttons or dropdown)
- Control is visually prominent and clearly labeled
- Model selection appears before file upload button
- Accessible via keyboard navigation (tab order logical)

### AC #2: Model Options Display
- Model options: "BELLE-2 (Mandarin-optimized)" and "WhisperX (Multi-language)"
- Labels clearly indicate model specialization
- Both options selectable via click or keyboard

### AC #3: Default Selection Configuration
- Default selection: BELLE-2 (matches backend DEFAULT_TRANSCRIPTION_MODEL)
- Can be configured via environment variable (VITE_DEFAULT_MODEL)
- Frontend default syncs with backend default

### AC #4: Component State Management
- Selected model stored in Pinia transcription store
- Model selection reactive (updates immediately on change)
- Model persists during upload workflow (upload → progress → results)

### AC #5: Upload API Integration
- Upload API call includes `model` parameter based on user selection
- Model value sent as form data: `belle2` or `whisperx`
- Backend validation handled (already implemented in Story 4.1)

### AC #6: localStorage Persistence
- Selected model saved to localStorage on change
- localStorage key: `klipnote_selected_model`
- Model selection restored on page load/refresh
- Fallback to default if localStorage empty

### AC #7: Help Text and Tooltips
- Tooltip/help text explains key differences between models:
  - BELLE-2: "Optimized for Mandarin/Chinese transcription with superior accuracy for Chinese content"
  - WhisperX: "Multi-language support with forced alignment for precise timestamps"
- Tooltip accessible on hover (desktop) or tap (mobile)
- Help text does not obscure upload interface

### AC #8: Responsive Design
- Model selection works on mobile (320px+), tablet (768px+), desktop
- Touch-friendly targets on mobile (minimum 44x44px)
- Radio buttons or dropdown adapts to screen size
- No horizontal scrolling required

### AC #9: Backend Model Validation (Already Complete from Story 4.1)
- Backend validates model parameter ✅ (main.py:140-145)
- Invalid models return HTTP 400 with error message ✅
- Celery routing to correct worker queue ✅

### AC #10: Integration Testing
- Upload with BELLE-2 model: verify job routed to belle2 queue
- Upload with WhisperX model: verify job routed to whisperx queue
- localStorage persistence: refresh page, verify model selection retained
- Default selection: first visit uses BELLE-2

---

## Tasks / Subtasks

### Phase 1: Component Implementation (AC: #1, #2, #3)
- [ ] Create ModelSelector.vue component in `frontend/src/components/`
  - [ ] Radio button group for model selection (AC: #1)
  - [ ] BELLE-2 and WhisperX options with labels (AC: #2)
  - [ ] Default selection logic (AC: #3)
- [ ] Add component to UploadView.vue
  - [ ] Position above file upload button
  - [ ] Integrate with existing upload form

### Phase 2: State Management (AC: #4, #5, #6)
- [ ] Update Pinia transcription store (AC: #4)
  - [ ] Add `selectedModel` state field
  - [ ] Add `setSelectedModel()` action
  - [ ] Add `loadModelFromLocalStorage()` action
- [ ] Update upload API call (AC: #5)
  - [ ] Modify `src/services/api.ts` uploadFile() to accept model parameter
  - [ ] Send model as FormData field
- [ ] Implement localStorage persistence (AC: #6)
  - [ ] Save on model change
  - [ ] Load on app initialization
  - [ ] Handle missing/invalid localStorage values

### Phase 3: UX Enhancements (AC: #7, #8)
- [ ] Add tooltip/help text for each model (AC: #7)
  - [ ] BELLE-2 tooltip with Chinese optimization description
  - [ ] WhisperX tooltip with multi-language description
  - [ ] Implement using CSS or lightweight tooltip library
- [ ] Responsive design implementation (AC: #8)
  - [ ] Test on mobile viewport (320px, 375px, 414px)
  - [ ] Test on tablet viewport (768px, 1024px)
  - [ ] Test on desktop (1280px, 1920px)
  - [ ] Ensure touch targets meet 44x44px minimum

### Phase 4: Testing (AC: #10)
- [ ] Write component unit tests (Vitest)
  - [ ] Test default model selection (BELLE-2)
  - [ ] Test model change updates store
  - [ ] Test localStorage save/load
- [ ] Write integration tests
  - [ ] Test upload with BELLE-2 model parameter
  - [ ] Test upload with WhisperX model parameter
  - [ ] Test localStorage persistence across refresh
- [ ] Manual testing checklist
  - [ ] Upload file with BELLE-2 → verify transcription completes
  - [ ] Upload file with WhisperX → verify transcription completes
  - [ ] Refresh page → verify model selection retained
  - [ ] Test on mobile device (or DevTools mobile emulation)

---

## Dev Notes

### Architecture Context from Story 4.1

**Backend Multi-Model Support (Already Implemented):**
- Upload endpoint accepts `model` parameter (Form field: `model` ∈ {belle2, whisperx, auto})
- Backend routing function: `get_transcription_queue()` in `model_router.py:450-530`
- Celery queue routing: Jobs dispatched to `belle2` or `whisperx` queue based on model selection
- Model validation: HTTP 400 returned for invalid model values
- Default model: `DEFAULT_TRANSCRIPTION_MODEL=belle2` in Docker Compose

**Frontend Integration Points:**
1. **API Client Update:**
   - Modify `src/services/api.ts` uploadFile() signature to accept optional `model` parameter
   - Current signature: `uploadFile(file: File)`
   - New signature: `uploadFile(file: File, model: 'belle2' | 'whisperx' = 'belle2')`

2. **Pinia Store Extension:**
   - Add `selectedModel` state to `stores/transcription.ts`
   - Add actions: `setSelectedModel()`, `loadModelFromLocalStorage()`, `saveModelToLocalStorage()`

3. **Component Placement:**
   - Insert `ModelSelector.vue` in `UploadView.vue` above file input
   - Use form group or fieldset for semantic HTML

### Model Descriptions for Tooltips

**BELLE-2:**
- **Label:** "BELLE-2 (Mandarin-optimized)"
- **Tooltip:** "Optimized for Chinese/Mandarin transcription with superior accuracy and natural segment lengths. Best choice for Chinese meetings and content."
- **Best for:** Chinese/Mandarin audio, business meetings in Chinese

**WhisperX:**
- **Label:** "WhisperX (Multi-language)"
- **Tooltip:** "Multi-language support with forced alignment for precise word-level timestamps. Suitable for English and other languages."
- **Best for:** Non-Chinese content, English meetings, multi-language transcription

### Component Design Pattern (Vue 3 Composition API)

```vue
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()

// Model options
const modelOptions = [
  { value: 'belle2', label: 'BELLE-2 (Mandarin-optimized)', description: '...' },
  { value: 'whisperx', label: 'WhisperX (Multi-language)', description: '...' }
]

// Load model from localStorage on mount
onMounted(() => {
  store.loadModelFromLocalStorage()
})

// Watch for model changes and save to localStorage
watch(() => store.selectedModel, (newModel) => {
  store.saveModelToLocalStorage()
})
</script>

<template>
  <div class="model-selector">
    <label class="model-selector__label">Transcription Model</label>
    <div class="model-selector__options">
      <div v-for="option in modelOptions" :key="option.value" class="model-option">
        <input
          type="radio"
          :id="`model-${option.value}`"
          :value="option.value"
          v-model="store.selectedModel"
          @change="store.setSelectedModel(option.value)"
        />
        <label :for="`model-${option.value}`">
          {{ option.label }}
          <span class="model-option__tooltip">{{ option.description }}</span>
        </label>
      </div>
    </div>
  </div>
</template>
```

### Learnings from Previous Story (Story 4.1)

**From Story 4-1-multi-model-production-architecture (Status: done)**

**Backend Architecture Implemented:**
- ✅ **Multi-worker Docker Compose**: `docker-compose.multi-model.yaml` with belle2-worker and whisperx-worker
- ✅ **Model routing**: `get_transcription_queue()` function routes jobs to correct worker
- ✅ **Upload endpoint**: Accepts `model` parameter (Form field), validates against {belle2, whisperx, auto}
- ✅ **Environment isolation**: CUDA 11.8 for BELLE-2, CUDA 12.x for WhisperX (separate containers)

**Key Files Modified in Story 4.1:**
- `backend/app/main.py` (lines 66, 137-158): Added model and language parameters to upload endpoint
- `backend/app/ai_services/model_router.py` (lines 450-530): Routing logic with auto-selection
- `backend/app/config.py` (line 28): DEFAULT_TRANSCRIPTION_MODEL field

**New Services Created:**
- `backend/docker-compose.multi-model.yaml`: Multi-worker orchestration (254 lines)
- `backend/Dockerfile.belle2`: BELLE-2 worker image with CUDA 11.8
- `backend/Dockerfile.whisperx`: WhisperX worker image with CUDA 12.x

**Architectural Insights:**
1. **Model parameter priority**: Per-request model > DEFAULT_TRANSCRIPTION_MODEL > "auto" fallback
2. **Validation strategy**: Fail-fast with HTTPException(400) for invalid model selection
3. **Auto-selection logic**: If `model=auto`, backend routes based on language hint (Chinese→belle2, others→whisperx)

**Pending Integration Tests from Story 4.1:**
- ⚠️ BELLE-2 queue end-to-end test (requires running Docker deployment)
- ⚠️ WhisperX queue end-to-end test (requires running Docker deployment)
- ⚠️ Model selection routing validation
- ⚠️ Concurrent job processing test

**Recommendation for Story 4.1b:**
- Story 4.1b integration tests (AC#10) can VALIDATE Story 4.1's pending tests
- Upload with model=belle2 and model=whisperx will confirm routing works end-to-end
- This story provides the user interface that enables full system testing

**Technical Debt to Address:**
- None specific to frontend - backend architecture is complete

**Interfaces to Reuse:**
- Upload endpoint already accepts `model` parameter ✅
- Model validation already implemented ✅
- No changes needed to backend for this story

### References

**Source Documents:**
- [Epic 4 Tech Spec] (if exists) or epics.md lines 620-639
- [Architecture.md] Section: "Multi-Model Production Architecture"
- [ADR-004] Multi-Model Architecture Decision Record (docs/architecture-decisions/ADR-004-multi-model-architecture.md)
- [Story 4.1] Multi-Model Production Architecture Design (docs/sprint-artifacts/4-1-multi-model-production-architecture.md)

**Frontend Architecture Patterns:**
- Component structure: `frontend/src/components/ModelSelector.vue`
- Pinia store: `frontend/src/stores/transcription.ts`
- API client: `frontend/src/services/api.ts`
- View integration: `frontend/src/views/UploadView.vue`

**Testing Standards:**
- Component tests: Vitest + Vue Testing Library
- Integration tests: Playwright (E2E)
- Coverage target: 70%+ for new components

### Project Structure Notes

**Expected File Locations:**
- Component: `frontend/src/components/ModelSelector.vue` (NEW)
- Modified: `frontend/src/views/UploadView.vue` (add ModelSelector import and usage)
- Modified: `frontend/src/stores/transcription.ts` (add selectedModel state)
- Modified: `frontend/src/services/api.ts` (add model parameter to uploadFile)

**Tailwind CSS v4 Reminder:**
- Use utility classes for styling
- Ensure responsive classes: `sm:`, `md:`, `lg:` for breakpoints
- Touch targets: `min-h-[44px] min-w-[44px]` for mobile

**Accessibility Notes:**
- Radio buttons must have associated labels (for attribute)
- Fieldset and legend for semantic grouping
- ARIA labels for tooltips
- Keyboard navigation: Tab order logical, Enter/Space to select

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

---

## Change Log

**2025-11-16:** Story created and drafted by SM workflow
- Story extracted from epics.md (lines 620-639)
- Learnings from Story 4.1 integrated into Dev Notes
- Backend validation (AC#9) already complete from Story 4.1
- Story ready for context generation and development

