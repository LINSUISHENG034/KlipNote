# Story 2.4: Inline Subtitle Editing

Status: done

## Story

As a user,
I want to edit subtitle text directly in the interface,
So that I can correct transcription errors before export.

## Acceptance Criteria

1. Clicking subtitle text makes it editable (contenteditable or input field)
2. Changes update immediately in component state
3. Tab/Enter key saves edit and moves to next subtitle
4. Escape key cancels edit and reverts changes
5. Edited subtitles visually distinguished from unedited (subtle indicator)
6. Multiple subtitles can be edited in succession
7. Edits persist in localStorage (key: `klipnote_edits_{job_id}`) - auto-saved with throttling (500ms)
8. localStorage prevents data loss from browser refresh or accidental navigation (satisfies FR-020 & NFR-003)

## Tasks / Subtasks

- [x] Task 1: Implement edit mode state management in Pinia store (AC: #1, #2, #4)
  - [x] Add `originalSegments` state field to preserve original text for revert
  - [x] Implement `setEditingSegment(id)` action (already scaffolded in Story 2.3)
  - [x] Implement `updateSegmentText(index, newText)` action with immediate state update
  - [x] Implement `cancelEdit(index)` action to revert from originalSegments
  - [x] Test: Store correctly tracks editing state
  - [x] Test: Segment text updates immediately on change
  - [x] Test: Cancel reverts to original text

- [x] Task 2: Add contenteditable editing to SubtitleList.vue (AC: #1, #2, #4, #5)
  - [x] Add double-click handler to subtitle text span (enable edit mode)
  - [x] Switch text span to contenteditable div or input field when `editingSegmentId === index`
  - [x] Bind input value to `store.segments[index].text` with v-model or manual @input
  - [x] Call `store.updateSegmentText(index, newText)` on input change
  - [x] Add `.edited` CSS class for segments with text different from originalSegments
  - [x] Add visual indicator (e.g., subtle colored dot or border accent)
  - [x] Test: Double-click enables edit mode
  - [x] Test: Typing updates segment text in real-time
  - [x] Test: Edited segments show visual distinction

- [x] Task 3: Implement keyboard navigation (AC: #3, #4, #6)
  - [x] Add @keydown.tab handler: Save current edit, move focus to next segment (index + 1)
  - [x] Add @keydown.enter handler: Save current edit, move to next segment
  - [x] Add @keydown.esc handler: Call `store.cancelEdit(index)`, exit edit mode
  - [x] Prevent default Tab behavior (don't leave page)
  - [x] Handle edge case: Tab on last segment (stay on last, exit edit mode)
  - [x] Test: Tab saves and moves to next
  - [x] Test: Enter saves and moves to next
  - [x] Test: Escape reverts and exits edit mode
  - [x] Test: Multiple segments can be edited in succession

- [x] Task 4: Implement localStorage auto-save with throttling (AC: #7, #8)
  - [x] Install lodash-es if not already installed: `npm install lodash-es`
  - [x] Import throttle from lodash-es in transcription store
  - [x] Create throttled save function: `throttledSave(jobId, segments, originalSegments)` with 500ms delay
  - [x] Implement `saveToLocalStorage(jobId, segments)` helper function
  - [x] Add watch() on `state.segments` with `{ deep: true }` option
  - [x] Call `throttledSave()` in watch callback (only if jobId present)
  - [x] localStorage structure: `{ job_id, segments, last_saved: ISO timestamp }`
  - [x] Test: Edits auto-save to localStorage after 500ms
  - [x] Test: localStorage key format: `klipnote_edits_{job_id}`
  - [x] Test: JSON structure includes job_id, segments, last_saved

- [x] Task 5: Implement localStorage recovery on page load (AC: #8)
  - [x] Add `loadFromLocalStorage(jobId)` action to transcription store
  - [x] Check for `klipnote_edits_{jobId}` key on EditorView mount or store init
  - [x] If exists: Parse JSON, validate structure, load segments into store
  - [x] If exists: Show user notification: "Restored unsaved edits from [timestamp]"
  - [x] Priority: localStorage segments override API result (preserve user work)
  - [x] Store both segments and originalSegments (original = API result, segments = potentially edited)
  - [x] Test: Page refresh restores edited segments
  - [x] Test: User notified of restoration with timestamp
  - [x] Test: localStorage data takes precedence over API

- [x] Task 6: Handle localStorage edge cases and errors (AC: #8)
  - [x] Wrap localStorage.setItem in try/catch for QuotaExceededError
  - [x] On quota exceeded: Log warning, show user toast notification, disable auto-save
  - [x] Wrap JSON.parse in try/catch for corrupted data
  - [x] On parse error: Log warning, fall back to API result, clear corrupted key
  - [x] Test: QuotaExceededError handled gracefully (warn user, continue without auto-save)
  - [x] Test: Corrupted JSON falls back to API result
  - [x] Test: Missing localStorage API (incognito mode) degrades gracefully

- [x] Task 7: Integrate editing with existing click-to-timestamp functionality (AC: #1, #6)
  - [x] Verify click handler guard from Story 2.3 prevents seek during edit
  - [x] Ensure `store.setEditingSegment(null)` called when user clicks outside editing segment
  - [x] Add blur event handler to contenteditable: Exit edit mode on focus loss
  - [x] Test: Click-to-timestamp blocked when `editingSegmentId !== null` (already implemented in Story 2.3)
  - [x] Test: Clicking outside edited segment saves and exits edit mode
  - [x] Test: Editing does not interfere with subtitle highlighting during playback

- [x] Task 8: Add unit tests for editing functionality (AC: all)
  - [x] Create/update `frontend/src/__tests__/components/SubtitleList.test.ts`
  - [x] Test: Double-click enables edit mode
  - [x] Test: Input updates segment text in store
  - [x] Test: Tab/Enter saves and moves to next
  - [x] Test: Escape reverts to original text
  - [x] Test: Edited segments have visual indicator
  - [x] Test: Multiple edits in succession work correctly
  - [x] Create `frontend/src/__tests__/stores/transcription.test.ts` (if not exists)
  - [x] Test: `updateSegmentText()` updates store immediately
  - [x] Test: `cancelEdit()` reverts from originalSegments
  - [x] Test: localStorage save throttling (500ms delay)
  - [x] Test: localStorage recovery on page load
  - [x] Run: `npm run test:unit` and verify all tests pass

- [ ] Task 9: Manual browser testing and validation (AC: all)
  - [ ] Start frontend dev server: `cd frontend && npm run dev`
  - [ ] Navigate to results page with existing transcription
  - [ ] Test double-click on subtitle text → editable field appears
  - [ ] Type corrections → text updates in real-time
  - [ ] Press Tab → saves, moves to next subtitle
  - [ ] Press Escape during edit → reverts to original text
  - [ ] Edit multiple segments → all retain changes
  - [ ] Wait 500ms → check browser DevTools localStorage (key present)
  - [ ] Refresh page → edits restored automatically
  - [ ] Test notification appears: "Restored unsaved edits from [timestamp]"
  - [ ] Verify edited subtitles have visual distinction (dot/border/color)

## Dev Notes

### Learnings from Previous Story

**From Story 2-3-click-to-timestamp-navigation (Status: done)**

**Critical Infrastructure Already Built (DO NOT RECREATE):**

✅ **Pinia Store Extensions:**
- `editingSegmentId` state field added (Story 2.3 prep)
- `setEditingSegment(id)` action implemented (Story 2.3 prep)
- SubtitleList already reads directly from store (no props needed)
- Click handler guard already prevents seek when `editingSegmentId !== null`

✅ **Component Architecture:**
- SubtitleList.vue migrated from props-based to store-based (no :segments prop binding)
- ResultsView.vue no longer passes segments as prop
- Component structure ready for inline editing integration

✅ **Integration Points Verified:**
- MediaPlayer watches `store.currentTime` for seeking
- SubtitleList watches `store.activeSegmentIndex` for highlighting
- No circular dependencies or conflicts

**Story 2.4 Adds (Extensions Only):**
- `originalSegments` field to store (NEW) - for cancel/revert functionality
- `updateSegmentText(index, text)` action (NEW) - immediate state update
- `cancelEdit(index)` action (NEW) - revert from originalSegments
- `loadFromLocalStorage(jobId)` action (NEW) - recovery on page load
- `saveToLocalStorage(jobId, segments)` helper (NEW) - persistence layer
- Contenteditable editing UI in SubtitleList.vue (NEW)
- Keyboard navigation handlers (Tab/Enter/Escape) (NEW)
- localStorage watch with throttled auto-save (NEW)
- Visual indicator for edited segments (NEW)

**Files to Modify (NOT create):**
- `frontend/src/stores/transcription.ts` - Add originalSegments, editing actions, localStorage logic
- `frontend/src/components/SubtitleList.vue` - Add contenteditable, keyboard handlers, edit mode UI
- `frontend/src/views/EditorView.vue` or `ResultsView.vue` - Call localStorage recovery on mount
- `frontend/src/__tests__/components/SubtitleList.test.ts` - Add editing tests
- `frontend/src/__tests__/stores/transcription.test.ts` - Add store tests for editing
- `frontend/package.json` - Add lodash-es dependency (if not already present from Story 2.2/2.3)

**Do NOT modify:**
- `frontend/src/components/MediaPlayer.vue` - No changes needed (state sync already working)
- `frontend/src/views/ResultsView.vue` - Minimal changes (only localStorage recovery call if needed)

[Source: docs/stories/2-3-click-to-timestamp-navigation.md#Dev-Agent-Record]

### Architectural Patterns and Constraints

**Inline Editing with localStorage Persistence Pattern:**

This story implements KlipNote's editing interface that enables users to correct transcription errors inline while preventing data loss through browser-based localStorage persistence (FR-020, NFR-003). The implementation balances immediate responsiveness with data durability through throttled auto-save.

**localStorage Persistence Architecture:**

```typescript
// Pinia Store Extensions (transcription.ts)
export const useTranscriptionStore = defineStore('transcription', {
  state: () => ({
    // Existing from Stories 2.2-2.3:
    segments: [],                // Current (potentially edited) segments
    activeSegmentIndex: -1,
    editingSegmentId: null,      // Already added in Story 2.3

    // NEW in Story 2.4:
    originalSegments: [],        // Pristine segments from API (for cancel/revert)
  }),

  actions: {
    // NEW in Story 2.4:
    updateSegmentText(index: number, newText: string) {
      if (index >= 0 && index < this.segments.length) {
        this.segments[index].text = newText
      }
    },

    cancelEdit(index: number) {
      if (index >= 0 && index < this.segments.length && this.originalSegments[index]) {
        this.segments[index].text = this.originalSegments[index].text
        this.editingSegmentId = null
      }
    },

    loadFromLocalStorage(jobId: string) {
      const key = `klipnote_edits_${jobId}`
      const saved = localStorage.getItem(key)

      if (saved) {
        try {
          const data = JSON.parse(saved)

          // Validate structure
          if (data.segments && Array.isArray(data.segments)) {
            // Priority: localStorage overrides API
            this.segments = data.segments

            console.log(`Restored edits from ${data.last_saved}`)
            // TODO: Show user notification
          }
        } catch (error) {
          console.error('Failed to parse localStorage edits:', error)
          // Fall back to API result (already loaded)
          localStorage.removeItem(key)
        }
      }
    },

    saveToLocalStorage(jobId: string) {
      const key = `klipnote_edits_${jobId}`
      const data = {
        job_id: jobId,
        segments: this.segments,
        last_saved: new Date().toISOString()
      }

      try {
        localStorage.setItem(key, JSON.stringify(data))
      } catch (error) {
        if (error instanceof DOMException && error.name === 'QuotaExceededError') {
          console.warn('localStorage quota exceeded. Auto-save disabled.')
          // TODO: Show user warning notification
        } else {
          console.error('localStorage save failed:', error)
        }
      }
    }
  }
})
```

**localStorage Watch Pattern (Throttled Auto-Save):**

```typescript
// In transcription store setup or EditorView component
import { watch } from 'vue'
import { throttle } from 'lodash-es'

// Create throttled save function (500ms delay)
const throttledSave = throttle((jobId: string, segments: Segment[]) => {
  store.saveToLocalStorage(jobId)
}, 500)

// Watch segments array for changes (deep watch for nested properties)
watch(() => store.segments, (newSegments) => {
  if (store.jobId && newSegments.length > 0) {
    throttledSave(store.jobId, newSegments)
  }
}, { deep: true })
```

**SubtitleList.vue Editing Implementation:**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()
const editingIndex = computed(() => store.editingSegmentId)

function handleDoubleClick(index: number) {
  store.setEditingSegment(index)
}

function handleInput(index: number, event: Event) {
  const target = event.target as HTMLElement
  const newText = target.textContent || ''
  store.updateSegmentText(index, newText)
}

function handleKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Tab' || event.key === 'Enter') {
    event.preventDefault()

    // Save current edit and move to next
    store.setEditingSegment(null)

    // Move to next segment (if not last)
    if (index < store.segments.length - 1) {
      store.setEditingSegment(index + 1)
    }
  } else if (event.key === 'Escape') {
    event.preventDefault()

    // Cancel edit and revert
    store.cancelEdit(index)
  }
}

function handleBlur(index: number) {
  // Exit edit mode when focus lost
  if (editingIndex.value === index) {
    store.setEditingSegment(null)
  }
}

function isEdited(index: number): boolean {
  return store.originalSegments[index] &&
         store.segments[index].text !== store.originalSegments[index].text
}
</script>

<template>
  <div class="subtitle-list">
    <div
      v-for="(segment, index) in store.segments"
      :key="index"
      :class="{
        active: index === store.activeSegmentIndex,
        clickable: store.editingSegmentId === null,
        editing: index === editingIndex,
        edited: isEdited(index)
      }"
      @click="handleClick(segment, index)"
      @dblclick="handleDoubleClick(index)"
    >
      <span class="timestamp">{{ formatTime(segment.start) }}</span>

      <!-- Editable text -->
      <span
        v-if="index !== editingIndex"
        class="text"
      >
        {{ segment.text }}
        <span v-if="isEdited(index)" class="edit-indicator">●</span>
      </span>

      <div
        v-else
        class="text-editor"
        contenteditable="true"
        @input="handleInput(index, $event)"
        @keydown="handleKeydown(index, $event)"
        @blur="handleBlur(index)"
        v-text="segment.text"
      ></div>
    </div>
  </div>
</template>

<style scoped>
/* Existing styles from Story 2.3 */
.subtitle-list {
  max-height: 600px;
  overflow-y: auto;
  scroll-behavior: smooth;
}

.subtitle-list > div {
  padding: 12px 16px;
  border-bottom: 1px solid #e0e0e0;
  transition: background-color 150ms ease;
}

.subtitle-list > div.clickable {
  cursor: pointer;
}

.subtitle-list > div.clickable:hover {
  background-color: #f5f5f5;
}

.subtitle-list > div.active {
  background-color: #e3f2fd;
  font-weight: 600;
  border-left: 4px solid #2196f3;
}

/* NEW in Story 2.4: Editing styles */
.subtitle-list > div.editing {
  background-color: #fff9c4;
  border-left: 4px solid #fbc02d;
}

.subtitle-list > div.edited .edit-indicator {
  color: #ff9800;
  margin-left: 6px;
  font-size: 0.7rem;
}

.text-editor {
  outline: 2px solid #fbc02d;
  padding: 4px 8px;
  border-radius: 4px;
  background-color: white;
  min-height: 24px;
}

.text-editor:focus {
  outline-color: #f57c00;
}

.timestamp {
  color: #666;
  font-size: 0.9rem;
  margin-right: 12px;
  font-family: monospace;
}

.text {
  color: #333;
}
</style>
```

**Recovery on Page Load:**

```vue
<!-- EditorView.vue or ResultsView.vue -->
<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'
import { fetchTranscriptionResult } from '@/services/api'

const route = useRoute()
const store = useTranscriptionStore()

onMounted(async () => {
  const jobId = route.params.jobId as string

  // First: Load from API (original transcription)
  const result = await fetchTranscriptionResult(jobId)
  store.segments = result.segments
  store.originalSegments = JSON.parse(JSON.stringify(result.segments)) // Deep copy

  // Second: Check localStorage for edits (overrides API if present)
  store.loadFromLocalStorage(jobId)
})
</script>
```

**Edge Cases Handled:**

1. **QuotaExceededError:** Catch, log warning, show user notification, disable auto-save (continue editing without persistence)
2. **Corrupted JSON in localStorage:** Catch parse error, log warning, fall back to API result, clear corrupted key
3. **Missing localStorage API:** Graceful degradation (incognito mode) - editing works, no auto-save
4. **Click during editing:** Guard from Story 2.3 prevents seek when `editingSegmentId !== null`
5. **Tab on last segment:** Stay on last segment, exit edit mode (don't wrap to first)
6. **Focus loss during edit:** Blur handler saves changes and exits edit mode
7. **Multiple browser tabs:** Last write wins (acceptable for MVP single-user workflow)
8. **Escape on unsaved edit:** Reverts to originalSegments (pristine API text)
9. **API fetch failure after localStorage recovery:** localStorage data preserved (user work not lost)

[Source: docs/architecture.md#localStorage-Persistence-for-Edit-Recovery, docs/tech-spec-epic-2.md#Workflow-2-Inline-Subtitle-Editing]

### Source Tree Components to Touch

**Files to Modify:**

```
frontend/src/
├── stores/
│   └── transcription.ts         # MODIFY: Add originalSegments, updateSegmentText(), cancelEdit(), localStorage logic
├── components/
│   └── SubtitleList.vue         # MODIFY: Add contenteditable, keyboard handlers, edit mode UI, visual indicators
├── views/
│   └── ResultsView.vue          # MODIFY: Call store.loadFromLocalStorage() on mount (after API fetch)
└── __tests__/
    ├── components/
    │   └── SubtitleList.test.ts # MODIFY: Add editing tests (double-click, keyboard nav, visual indicators)
    └── stores/
        └── transcription.test.ts # MODIFY: Add store tests (edit actions, localStorage)
```

**Dependencies to Add:**

```
frontend/package.json            # Verify lodash-es present (should be from Story 2.2/2.3)
```

**Files NOT to Touch:**

```
frontend/src/
├── components/
│   └── MediaPlayer.vue          # DO NOT MODIFY: State sync already working, no changes needed
├── services/
│   └── api.ts                   # NO CHANGES: No new API calls in this story
└── router/
    └── index.ts                 # NO CHANGES: Routes already configured
```

**Expected Component State After Story 2.4:**

```
frontend/src/
├── stores/
│   └── transcription.ts         # Extended with originalSegments, editing actions, localStorage
├── components/
│   ├── MediaPlayer.vue          # Unchanged from Story 2.3
│   └── SubtitleList.vue         # Enhanced with inline editing, keyboard nav, visual indicators
└── views/
    └── ResultsView.vue          # Enhanced with localStorage recovery on mount
```

**localStorage Integration:**

- Auto-save triggered by watch() on `store.segments` (deep watch)
- Throttled with 500ms delay using lodash-es throttle()
- Key pattern: `klipnote_edits_{job_id}`
- Recovery on page load: Check localStorage before displaying segments
- Priority: localStorage edits override API result (preserve user work)

### Testing Standards Summary

**Frontend Testing Requirements:**

- **Framework:** Vitest + @vue/test-utils (already configured from Epic 1)
- **Coverage Target:** 70%+ frontend coverage (maintain Epic 1 standard)
- **Test Files:** Update `SubtitleList.test.ts`, update `transcription.test.ts`

**Test Cases for Story 2.4:**

```typescript
// frontend/src/__tests__/components/SubtitleList.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SubtitleList from '@/components/SubtitleList.vue'
import { useTranscriptionStore } from '@/stores/transcription'

describe('SubtitleList - Inline Editing', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('enables edit mode on double-click', async () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Original text' }
    ]
    store.originalSegments = JSON.parse(JSON.stringify(store.segments))

    const wrapper = mount(SubtitleList)
    const subtitleText = wrapper.find('.text')

    await subtitleText.trigger('dblclick')

    expect(store.editingSegmentId).toBe(0)
    expect(wrapper.find('.text-editor').exists()).toBe(true)
  })

  it('updates segment text on input', async () => {
    const store = useTranscriptionStore()
    store.segments = [{ start: 0.5, end: 3.2, text: 'Original' }]
    store.originalSegments = JSON.parse(JSON.stringify(store.segments))
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    const editor = wrapper.find('.text-editor')

    // Simulate contenteditable input
    editor.element.textContent = 'Edited text'
    await editor.trigger('input')

    expect(store.segments[0].text).toBe('Edited text')
  })

  it('saves and moves to next on Tab key', async () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Segment 1' },
      { start: 3.5, end: 7.8, text: 'Segment 2' }
    ]
    store.originalSegments = JSON.parse(JSON.stringify(store.segments))
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    const editor = wrapper.find('.text-editor')

    await editor.trigger('keydown.tab')

    // Should exit current, enter next
    expect(store.editingSegmentId).toBe(1)
  })

  it('reverts to original text on Escape key', async () => {
    const store = useTranscriptionStore()
    const originalText = 'Original text'
    store.segments = [{ start: 0.5, end: 3.2, text: 'Edited text' }]
    store.originalSegments = [{ start: 0.5, end: 3.2, text: originalText }]
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    const editor = wrapper.find('.text-editor')

    await editor.trigger('keydown.esc')

    expect(store.segments[0].text).toBe(originalText)
    expect(store.editingSegmentId).toBeNull()
  })

  it('shows visual indicator for edited segments', async () => {
    const store = useTranscriptionStore()
    store.segments = [{ start: 0.5, end: 3.2, text: 'Edited text' }]
    store.originalSegments = [{ start: 0.5, end: 3.2, text: 'Original text' }]

    const wrapper = mount(SubtitleList)
    const segment = wrapper.find('.subtitle-list > div')

    expect(segment.classes()).toContain('edited')
    expect(wrapper.find('.edit-indicator').exists()).toBe(true)
  })

  it('allows multiple edits in succession', async () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Segment 1' },
      { start: 3.5, end: 7.8, text: 'Segment 2' },
      { start: 8.0, end: 12.0, text: 'Segment 3' }
    ]
    store.originalSegments = JSON.parse(JSON.stringify(store.segments))

    const wrapper = mount(SubtitleList)
    const segments = wrapper.findAll('.subtitle-list > div')

    // Edit first segment
    await segments[0].trigger('dblclick')
    expect(store.editingSegmentId).toBe(0)

    // Tab to second
    await wrapper.find('.text-editor').trigger('keydown.tab')
    expect(store.editingSegmentId).toBe(1)

    // Tab to third
    await wrapper.find('.text-editor').trigger('keydown.tab')
    expect(store.editingSegmentId).toBe(2)
  })
})

// frontend/src/__tests__/stores/transcription.test.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTranscriptionStore } from '@/stores/transcription'

describe('TranscriptionStore - Editing Actions', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('updateSegmentText updates segment immediately', () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.0, end: 2.5, text: 'Original text' }
    ]

    store.updateSegmentText(0, 'New text')

    expect(store.segments[0].text).toBe('New text')
  })

  it('cancelEdit reverts to original text', () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.0, end: 2.5, text: 'Edited text' }
    ]
    store.originalSegments = [
      { start: 0.0, end: 2.5, text: 'Original text' }
    ]
    store.editingSegmentId = 0

    store.cancelEdit(0)

    expect(store.segments[0].text).toBe('Original text')
    expect(store.editingSegmentId).toBeNull()
  })

  it('saveToLocalStorage persists segments with correct key', () => {
    const store = useTranscriptionStore()
    const jobId = 'test-job-123'
    store.jobId = jobId
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Test segment' }
    ]

    store.saveToLocalStorage(jobId)

    const saved = localStorage.getItem(`klipnote_edits_${jobId}`)
    expect(saved).not.toBeNull()

    const parsed = JSON.parse(saved!)
    expect(parsed.job_id).toBe(jobId)
    expect(parsed.segments).toHaveLength(1)
    expect(parsed.segments[0].text).toBe('Test segment')
    expect(parsed.last_saved).toBeDefined()
  })

  it('loadFromLocalStorage restores saved segments', () => {
    const jobId = 'test-job-123'
    const editedSegments = [
      { start: 0.5, end: 3.2, text: 'Edited text' }
    ]

    localStorage.setItem(
      `klipnote_edits_${jobId}`,
      JSON.stringify({
        job_id: jobId,
        segments: editedSegments,
        last_saved: new Date().toISOString()
      })
    )

    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Original text' }
    ]

    store.loadFromLocalStorage(jobId)

    expect(store.segments[0].text).toBe('Edited text')
  })

  it('handles QuotaExceededError gracefully', () => {
    const store = useTranscriptionStore()
    const originalSetItem = localStorage.setItem

    localStorage.setItem = vi.fn(() => {
      const error = new DOMException('QuotaExceededError')
      error.name = 'QuotaExceededError'
      throw error
    })

    const consoleSpy = vi.spyOn(console, 'warn')

    store.jobId = 'test-job-123'
    store.segments = [{ start: 0.5, end: 3.2, text: 'Text' }]
    store.saveToLocalStorage('test-job-123')

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('quota exceeded')
    )

    localStorage.setItem = originalSetItem
  })

  it('handles corrupted JSON gracefully', () => {
    const jobId = 'test-job-123'
    localStorage.setItem(`klipnote_edits_${jobId}`, 'corrupted-json{')

    const store = useTranscriptionStore()
    const consoleSpy = vi.spyOn(console, 'error')

    store.loadFromLocalStorage(jobId)

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Failed to parse'),
      expect.any(Error)
    )

    // Should clear corrupted key
    expect(localStorage.getItem(`klipnote_edits_${jobId}`)).toBeNull()
  })
})

// localStorage throttling test
describe('TranscriptionStore - localStorage Auto-Save', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('throttles localStorage saves to 500ms', async () => {
    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0.5, end: 3.2, text: 'Original' }]

    // Make rapid changes
    store.updateSegmentText(0, 'Change 1')
    store.updateSegmentText(0, 'Change 2')
    store.updateSegmentText(0, 'Change 3')

    // Should not save yet (throttled)
    expect(localStorage.getItem(`klipnote_edits_${store.jobId}`)).toBeNull()

    // Fast-forward 500ms
    vi.advanceTimersByTime(500)

    // Now should be saved (only latest change)
    const saved = localStorage.getItem(`klipnote_edits_${store.jobId}`)
    const parsed = JSON.parse(saved!)
    expect(parsed.segments[0].text).toBe('Change 3')
  })
})
```

**Manual Browser Testing (Critical for AC #7, #8):**

After Vitest tests pass, manually validate in browsers:

```bash
# Start frontend dev server
cd frontend
npm run dev

# Navigate to: http://localhost:5173/results/{valid-job-id}
# (Use job_id from previous transcription in Epic 1/2)

# Manual Test Checklist:
# 1. Double-click subtitle text → becomes editable
# 2. Type corrections → updates in real-time
# 3. Press Tab → saves, moves to next subtitle
# 4. Press Escape → reverts to original text
# 5. Edit multiple segments → all changes persist
# 6. Open DevTools → Application → Local Storage → verify key present
# 7. Refresh page → edits restored automatically
# 8. Verify notification: "Restored unsaved edits from [timestamp]"
# 9. Edited subtitles show visual indicator (dot/border/color)
# 10. Click subtitle during edit → seek blocked (from Story 2.3)
```

**Definition of Done (Testing Perspective):**

- ✓ All Vitest tests pass (SubtitleList.test.ts, transcription.test.ts)
- ✓ Frontend coverage remains 70%+ (maintain Epic 1 standard)
- ✓ Manual browser test successful (Chrome, Firefox)
- ✓ localStorage auto-save verified (DevTools inspection)
- ✓ Page refresh recovery tested (edits preserved)
- ✓ Visual indicators for edited segments confirmed
- ✓ No TypeScript errors, no console errors
- ✓ Keyboard navigation (Tab/Enter/Escape) working smoothly

[Source: docs/architecture.md#Testing-Strategy, docs/tech-spec-epic-2.md#Test-Strategy-Summary]

### Project Structure Notes

**Story 2.4 Position in Epic 2:**

Story 2.4 is the **fourth story in Epic 2: Integrated Review & Export Experience**. It builds on Stories 2.2-2.3's media player and click-to-timestamp infrastructure to enable inline editing of subtitle text with browser-based persistence, completing the review interface before export functionality.

- **Story 2.1** ✓ Complete: Media playback API endpoint (backend)
- **Story 2.2** ✓ Complete: Frontend MediaPlayer integration with state sync
- **Story 2.3** ✓ Complete: Click-to-timestamp navigation + active highlighting
- **Story 2.4** ← **This story**: Inline subtitle editing with localStorage persistence
- **Story 2.5**: Export API with data flywheel
- **Story 2.6**: Frontend export functionality
- **Story 2.7**: MVP release validation

**Dependencies:**

- **Prerequisite**: Story 2.3 (editingSegmentId infrastructure, click handler guards) ✓ Complete
- **Prerequisite**: Story 1.7 (SubtitleList component exists) ✓ Complete
- **Enables**: Story 2.5 (export needs edited segments from localStorage)
- **Enables**: Story 2.7 (editing is critical MVP feature to validate)

**Frontend Environment:**

```bash
# Story 2.4 implementation environment
cd frontend

# Verify lodash-es installed (from Story 2.2/2.3)
npm list lodash-es
# Should show: lodash-es@4.17.21

# If not installed:
npm install lodash-es

# Run dev server
npm run dev
# Server: http://localhost:5173

# Run tests
npm run test:unit

# Build for production (optional validation)
npm run build
```

**State Management Continuity (Story 1.6 → 2.2 → 2.3 → 2.4):**

- **Story 1.6** created Pinia store with: `jobId`, `segments`, `status`, `progress`
- **Story 2.2** extended store with: `currentTime`, `playbackTime`, `isPlaying`
- **Story 2.3** extended store with: `activeSegmentIndex`, `editingSegmentId`, `updateActiveSegment()`, `setEditingSegment()`
- **Story 2.4** extends store with: `originalSegments`, `updateSegmentText()`, `cancelEdit()`, `loadFromLocalStorage()`, `saveToLocalStorage()`

This incremental approach ensures each story builds upon the previous foundation without breaking existing functionality. All state additions are backwards-compatible extensions.

**localStorage Characteristics (NFR-003):**

- **Key pattern:** `klipnote_edits_{job_id}` (job-specific isolation)
- **Save frequency:** Throttled to 500ms (prevents excessive writes)
- **Storage size:** ~100KB for 1-hour transcription (well under 5-10MB browser limit)
- **Data priority:** localStorage overrides API result (preserve user work)
- **Edge case handling:** QuotaExceededError, corrupted JSON, missing API all handled gracefully
- **Total user experience:** Edit → Auto-save 500ms → Refresh → Restored automatically ✓

### References

- [Source: docs/epics.md#Story-2.4] - User story statement and acceptance criteria
- [Source: docs/prd.md#FR009] - Inline editing requirement: "System shall allow users to edit subtitle text inline within the web interface"
- [Source: docs/prd.md#FR020] - localStorage persistence: "System shall persist user edits to browser localStorage to prevent data loss during browser refresh or accidental navigation"
- [Source: docs/prd.md#NFR003] - Reliability requirement: "Browser-based state shall prevent data loss during normal operation including page refresh and accidental navigation"
- [Source: docs/architecture.md#localStorage-Persistence-for-Edit-Recovery] - Complete implementation pattern with localStorage key format, save strategy, restoration priority, edge case handling
- [Source: docs/tech-spec-epic-2.md#Workflow-2-Inline-Subtitle-Editing] - Detailed workflow with implementation steps, edge cases, error handling
- [Source: docs/tech-spec-epic-2.md#Data-Models-and-Contracts] - localStorage structure, TypeScript interfaces, Pydantic models
- [Source: docs/tech-spec-epic-2.md#Performance] - Throttled auto-save rationale (500ms delay), localStorage limits
- [Source: docs/stories/2-3-click-to-timestamp-navigation.md] - Editing infrastructure prepared (editingSegmentId, setEditingSegment, click guards)

## Dev Agent Record

### Context Reference

- `docs/stories/2-4-inline-subtitle-editing.context.xml`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
