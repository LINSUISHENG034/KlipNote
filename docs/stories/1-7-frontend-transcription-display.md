# Story 1.7: Frontend Transcription Display

Status: done

## Story

As a user,
I want to view the transcription results in a readable format,
So that I can verify the AI transcription quality.

## Acceptance Criteria

1. Results page calls GET /result/{job_id} on load
2. Displays subtitle segments as scrollable list
3. Each segment shows timestamp (MM:SS format) and text
4. Clear visual separation between subtitle segments
5. Handles long transcriptions (100+ segments) with smooth scrolling
6. Loading state while fetching results
7. Error handling if result fetch fails

## Tasks / Subtasks

- [x] Task 1: Create timestamp formatting utility (AC: #3)
  - [x] Create frontend/src/utils/formatters.ts
  - [x] Implement formatTime(seconds: number): string function
  - [x] Convert float seconds to MM:SS format (e.g., 65.5 → "01:05")
  - [x] Handle edge cases: 0 seconds, hours (over 60 minutes), negative values
  - [x] Test: formatTime(0) = "00:00", formatTime(65) = "01:05", formatTime(3661) = "61:01"

- [x] Task 2: Create SubtitleList component (AC: #2, #3, #4, #5)
  - [x] Create frontend/src/components/SubtitleList.vue
  - [x] Accept segments prop (array of Segment objects)
  - [x] Render each segment with timestamp and text
  - [x] Use formatTime() utility for timestamp display
  - [x] Apply CSS for visual separation between segments
  - [x] Implement scrollable container (max-height with overflow-y: auto)
  - [x] Test: Render with 3 segments, verify all displayed
  - [x] Test: Render with 100+ segments, verify smooth scrolling

- [x] Task 3: Implement ResultsView with data loading (AC: #1, #6)
  - [x] Open frontend/src/views/ResultsView.vue (replace placeholder)
  - [x] Extract job_id from route params using useRoute()
  - [x] Access transcription store using useTranscriptionStore()
  - [x] On mount: Check if segments already loaded (from Story 1.6 auto-nav)
  - [x] If segments empty: Call store.fetchResult(jobId) to load data
  - [x] Add loading state: isLoading ref, display loading message/spinner
  - [x] Test: Mount with job_id, verify fetchResult called if segments empty
  - [x] Test: Mount with segments pre-loaded, verify no fetch triggered

- [x] Task 4: Integrate SubtitleList into ResultsView (AC: #2)
  - [x] Import SubtitleList component in ResultsView.vue
  - [x] Pass store.segments to SubtitleList as prop
  - [x] Add conditional rendering: Show SubtitleList only if segments loaded
  - [x] Test: Verify SubtitleList receives segments prop correctly
  - [x] Test: Empty segments array displays appropriate message

- [x] Task 5: Implement error handling (AC: #7)
  - [x] Add errorMessage ref in ResultsView
  - [x] Wrap fetchResult() in try/catch block
  - [x] On error: Set errorMessage with user-friendly text
  - [x] Display error message UI (distinct from loading state)
  - [x] Add retry button that clears error and refetches
  - [x] Test: Mock 404 error, verify error message displayed
  - [x] Test: Retry button clears error and calls fetchResult again

- [x] Task 6: Add responsive layout and styling (AC: #4, #5)
  - [x] Style ResultsView: Page layout with header, subtitle list container
  - [x] Style SubtitleList: Segment cards with timestamp + text layout
  - [x] Implement responsive breakpoints (mobile: 320px, tablet: 768px, desktop: 1024px)
  - [x] Ensure smooth scrolling performance (CSS: scroll-behavior: smooth)
  - [x] Add hover effects on subtitle segments for future interaction (Epic 2)
  - [x] Test: View on mobile viewport (320px), verify readable layout
  - [x] Test: View with 200 segments, verify no performance degradation

- [x] Task 7: Write comprehensive frontend tests (AC: #1-7)
  - [x] Create frontend/src/__tests__/utils/formatters.test.ts
  - [x] Test: formatTime() with various inputs (0, 65, 3661, edge cases)
  - [x] Create frontend/src/__tests__/components/SubtitleList.test.ts
  - [x] Test: Renders segments correctly with timestamp and text
  - [x] Test: Handles empty segments array gracefully
  - [x] Test: Scrollable container works with 100+ segments
  - [x] Create frontend/src/__tests__/views/ResultsView.test.ts
  - [x] Test: Calls fetchResult on mount if segments empty
  - [x] Test: Displays loading state during fetch
  - [x] Test: Displays error message on fetch failure
  - [x] Test: Renders SubtitleList with loaded segments
  - [x] Run: npm run test:unit -- --coverage, verify 60%+ coverage

## Dev Notes

### Learnings from Previous Story

**From Story 1-6-frontend-progress-monitoring (Status: done)**

- **Frontend Infrastructure Complete**: Vue 3 + Vite + TypeScript project fully operational on port 5173
- **Pinia Store Ready**: `frontend/src/stores/transcription.ts` already has segments state management
  - State includes: `segments: Segment[]`, `jobId`, `status`
  - Actions include: `fetchResult(jobId)` for loading transcription results
  - Store fully tested with 100% coverage
- **API Client Available**: `frontend/src/services/api.ts` has `fetchResult()` function
  - Endpoint: GET /result/{job_id}
  - Returns: `{segments: [{start: number, end: number, text: string}]}`
  - Error handling: 404 returns "Result not ready yet or job not found"
- **TypeScript Types Defined**: `frontend/src/types/api.ts` has complete interfaces
  - `Segment`: `{start: number, end: number, text: string}`
  - `TranscriptionResult`: `{segments: Segment[]}`
- **Router Configuration**: `frontend/src/router/index.ts` has /results/:jobId route
  - Route already configured and tested in Story 1.6
  - Navigation triggered by ProgressView on completion
- **ResultsView Placeholder Created**: Basic placeholder exists, needs full implementation
  - File: `frontend/src/views/ResultsView.vue`
  - Current state: Minimal placeholder for AC#4 auto-navigation
  - **This story replaces placeholder with full implementation**
- **Testing Framework**: Vitest + @vue/test-utils configured and working
  - 101 tests passing overall, 62.75% coverage achieved
  - Testing patterns established for components, stores, views

**Key Integration Points for This Story:**
- Use existing Pinia store - DO NOT create new state management
- Use existing `fetchResult()` API function - DO NOT reimplement
- Use existing TypeScript Segment interface - matches backend exactly
- ResultsView route already configured - just implement component logic
- Story 1.6 auto-navigation: ProgressView calls `store.fetchResult()` before navigating to /results/:jobId
  - **Optimization**: Check if segments already loaded before fetching again
- Follow established Vue SFC structure and testing patterns from Story 1.5/1.6

**Files Created in Story 1.6 (REUSE):**
- `frontend/src/stores/transcription.ts` - State management
- `frontend/src/services/api.ts` (extended with fetchResult)
- `frontend/src/types/api.ts` (extended with TranscriptionResult, Segment)
- `frontend/src/views/ResultsView.vue` - Placeholder to replace
- `frontend/src/router/index.ts` - Route already added

[Source: docs/stories/1-6-frontend-progress-monitoring.md#Dev-Agent-Record]

### Architectural Patterns and Constraints

**Component Structure (from architecture.md):**

```vue
<!-- Standard Vue 3 SFC Pattern -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'
import SubtitleList from '@/components/SubtitleList.vue'

const route = useRoute()
const store = useTranscriptionStore()

const jobId = ref(route.params.jobId as string)
const isLoading = ref(false)
const errorMessage = ref<string | null>(null)

onMounted(async () => {
  // Check if segments already loaded (from Story 1.6 auto-nav)
  if (store.segments.length === 0) {
    isLoading.value = true
    try {
      await store.fetchResult(jobId.value)
    } catch (error) {
      errorMessage.value = 'Failed to load transcription results. Please try again.'
    } finally {
      isLoading.value = false
    }
  }
})

async function handleRetry() {
  errorMessage.value = null
  isLoading.value = true
  try {
    await store.fetchResult(jobId.value)
  } catch (error) {
    errorMessage.value = 'Failed to load transcription results. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="results-view">
    <h1>Transcription Results</h1>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading">
      <p>Loading transcription...</p>
    </div>

    <!-- Error State -->
    <div v-else-if="errorMessage" class="error">
      <p class="error-message">{{ errorMessage }}</p>
      <button @click="handleRetry" class="retry-button">Retry</button>
    </div>

    <!-- Results Display -->
    <div v-else-if="store.segments.length > 0">
      <SubtitleList :segments="store.segments" />
    </div>

    <!-- Empty State -->
    <div v-else class="empty">
      <p>No transcription results available.</p>
    </div>
  </div>
</template>

<style scoped>
.results-view {
  max-width: 900px;
  margin: 2rem auto;
  padding: 2rem;
}

.loading, .error, .empty {
  text-align: center;
  padding: 3rem;
}

.error-message {
  color: #c62828;
  margin-bottom: 1rem;
}

.retry-button {
  padding: 0.75rem 2rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background-color: #359268;
}

@media (max-width: 768px) {
  .results-view {
    padding: 1rem;
  }
}
</style>
```

**SubtitleList Component Pattern:**

```vue
<script setup lang="ts">
import type { Segment } from '@/types/api'
import { formatTime } from '@/utils/formatters'

defineProps<{
  segments: Segment[]
}>()
</script>

<template>
  <div class="subtitle-list">
    <div
      v-for="(segment, index) in segments"
      :key="index"
      class="subtitle-segment"
    >
      <span class="timestamp">{{ formatTime(segment.start) }}</span>
      <span class="text">{{ segment.text }}</span>
    </div>
  </div>
</template>

<style scoped>
.subtitle-list {
  max-height: 600px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  padding: 1rem;
}

.subtitle-segment {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  margin-bottom: 0.5rem;
  background-color: #f5f5f5;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.subtitle-segment:hover {
  background-color: #e3f2fd;
  cursor: pointer;  /* Preparation for Epic 2 click-to-timestamp */
}

.timestamp {
  flex-shrink: 0;
  width: 60px;
  font-weight: 600;
  color: #1976d2;
  font-family: monospace;
}

.text {
  flex-grow: 1;
  line-height: 1.6;
  color: #333;
}

/* Smooth scrolling */
.subtitle-list {
  scroll-behavior: smooth;
}

/* Mobile responsive */
@media (max-width: 768px) {
  .subtitle-segment {
    flex-direction: column;
    gap: 0.5rem;
  }

  .timestamp {
    width: auto;
  }
}
</style>
```

**Timestamp Formatting Utility:**

```typescript
// utils/formatters.ts
/**
 * Convert float seconds to MM:SS format
 * @param seconds - Float seconds (e.g., 65.5)
 * @returns Formatted time string (e.g., "01:05")
 */
export function formatTime(seconds: number): string {
  if (seconds < 0) return "00:00"

  const totalSeconds = Math.floor(seconds)
  const minutes = Math.floor(totalSeconds / 60)
  const remainingSeconds = totalSeconds % 60

  const mm = String(minutes).padStart(2, '0')
  const ss = String(remainingSeconds).padStart(2, '0')

  return `${mm}:${ss}`
}
```

[Source: docs/architecture.md#Component-Structure-Pattern, docs/architecture.md#Frontend-API-Client]

### Source Tree Components to Touch

**New Files to Create:**

```
frontend/src/
├── utils/
│   └── formatters.ts               # NEW: Timestamp formatting utility
├── components/
│   └── SubtitleList.vue            # NEW: Subtitle segment display component
└── __tests__/
    ├── utils/
    │   └── formatters.test.ts      # NEW: Formatter tests
    ├── components/
    │   └── SubtitleList.test.ts    # NEW: SubtitleList component tests
    └── views/
        └── ResultsView.test.ts     # NEW: ResultsView tests
```

**Existing Files to Modify:**

```
frontend/src/
└── views/
    └── ResultsView.vue             # MODIFY: Replace placeholder with full implementation
```

**Files Already Exist (DO NOT modify):**
- `frontend/src/stores/transcription.ts` - Pinia store ready to use
- `frontend/src/services/api.ts` - fetchResult() function available
- `frontend/src/types/api.ts` - Segment, TranscriptionResult interfaces defined
- `frontend/src/router/index.ts` - /results/:jobId route configured

### Testing Standards Summary

**Frontend Testing Requirements (from Testing Strategy):**

- **Framework**: Vitest + @vue/test-utils
- **Coverage Target**: 60%+ for frontend components
- **Test Organization**:
  - Utility tests in `__tests__/utils/`
  - Component tests in `__tests__/components/`
  - View tests in `__tests__/views/`

**Test Scenarios to Cover:**

**1. Formatter Tests (src/__tests__/utils/formatters.test.ts):**
- formatTime(0) returns "00:00"
- formatTime(65) returns "01:05"
- formatTime(3661) returns "61:01" (over 1 hour)
- formatTime(-10) returns "00:00" (negative handling)
- formatTime(0.7) returns "00:00" (decimal rounding)

**2. SubtitleList Component Tests (src/__tests__/components/SubtitleList.test.ts):**
- Render: Displays all segments from props
- Timestamp formatting: Uses formatTime() correctly
- Visual separation: Each segment has distinct container
- Empty state: Handles empty segments array gracefully
- Scrolling: Container is scrollable with max-height
- Accessibility: Proper semantic HTML structure

**3. ResultsView Tests (src/__tests__/views/ResultsView.test.ts):**
- Mount: Extracts jobId from route params correctly
- Data loading: Calls store.fetchResult() if segments empty
- Optimization: Skips fetch if segments already loaded
- Loading state: Displays loading message during fetch
- Success state: Renders SubtitleList with segments
- Error state: Displays error message on fetch failure
- Retry action: Clears error and refetches on retry button click
- Empty state: Displays message when no segments available

**Mock Strategies:**
- **API Calls**: Mock store.fetchResult() using vi.fn()
- **Router**: Mock useRoute() to provide test jobId
- **Store**: Create test Pinia instance with mock segments data
- **Segments Data**: Use fixture with 3-5 test segments for basic tests, 100+ for scrolling tests

**Test Execution:**
```bash
cd frontend
npm run test:unit -- --coverage
# Target: 60%+ coverage on new components/utils
```

[Source: docs/architecture.md#Testing-Strategy]

### Project Structure Notes

**Alignment with Unified Project Structure:**

This story completes Epic 1's foundational workflow by adding the final display layer:

- **Story 1.5**: Upload interface sends files to backend
- **Story 1.6**: Progress monitoring tracks job status with polling
- **Story 1.7**: Results display shows completed transcriptions ← **This story**

**End-to-End Workflow Complete:**
```
User uploads file (1.5)
  ↓
Progress monitoring polls status (1.6)
  ↓
Auto-navigation to results on completion (1.6)
  ↓
Display transcription segments (1.7) ← **Completes Epic 1**
```

**Preparation for Epic 2:**
- SubtitleList component designed with hover effects (preparation for click-to-timestamp)
- ResultsView provides container for future media player integration (Story 2.2)
- Segment display format ready for highlighting during playback (Story 2.3)
- Component structure supports inline editing additions (Story 2.4)

**No Conflicts Detected:**
- Story builds on existing infrastructure without breaking changes
- All dependencies from Stories 1.4, 1.5, 1.6 satisfied
- Component hierarchy follows Vue best practices
- Responsive design consistent with Story 1.5/1.6 patterns

### References

- [Source: docs/epics.md#Story-1.7] - User story statement and acceptance criteria
- [Source: docs/tech-spec-epic-1.md#Data-Models-and-Contracts] - Segment JSON format specification
- [Source: docs/tech-spec-epic-1.md#APIs-and-Interfaces] - GET /result/{job_id} endpoint specification
- [Source: docs/tech-spec-epic-1.md#Workflows-and-Sequencing] - Display transcription workflow step
- [Source: docs/architecture.md#Component-Structure-Pattern] - Vue SFC structure and patterns
- [Source: docs/architecture.md#TypeScript-Type-Definitions] - Segment, TranscriptionResult interfaces
- [Source: docs/architecture.md#Frontend-API-Client] - Native fetch() pattern for API calls
- [Source: docs/architecture.md#Testing-Strategy] - Vitest setup, coverage targets, mock strategies
- [Source: docs/stories/1-6-frontend-progress-monitoring.md#Dev-Agent-Record] - Previous story learnings and infrastructure

## Dev Agent Record

### Context Reference

- docs/stories/1-7-frontend-transcription-display.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Completion Notes
**Completed:** 2025-11-06
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

### Debug Log References

**Implementation Strategy:**
- Created timestamp formatting utility (formatters.ts) with edge case handling
- Built SubtitleList component with scrollable container and visual separation
- Replaced ResultsView placeholder with full implementation including:
  - Loading state with spinner animation
  - Error handling with retry button
  - Optimization: Checks if segments already loaded (from Story 1.6 auto-nav)
  - Responsive design with 3 breakpoints (320px, 768px, 1024px)
- Authored comprehensive tests for all components (28 new test cases)
- All 129 tests passing with 66.98% coverage (exceeds 60%+ target)

### Completion Notes List

✅ **Story 1.7 Complete - Frontend Transcription Display**

**Implementation Summary:**
- Created timestamp formatting utility with MM:SS format conversion
- Built SubtitleList component with scrollable display for 100+ segments
- Implemented full ResultsView with loading, error, empty, and success states
- Added responsive design supporting mobile (320px), tablet (768px), desktop (1024px)
- Included hover effects on segments (preparation for Epic 2 click-to-timestamp)

**Test Coverage:**
- formatters.ts: 100% coverage (9 test cases)
- SubtitleList.vue: 100% coverage (8 test cases)
- ResultsView.vue: 98.11% coverage (11 test cases)
- Overall project: 66.98% coverage, 129/129 tests passing

**Acceptance Criteria Validation:**
1. ✅ Results page calls GET /result/{job_id} on load - Implemented in onMounted with optimization
2. ✅ Displays subtitle segments as scrollable list - SubtitleList component with max-height and overflow-y
3. ✅ Each segment shows timestamp (MM:SS format) and text - formatTime() utility used
4. ✅ Clear visual separation between subtitle segments - CSS styling with distinct cards
5. ✅ Handles long transcriptions (100+ segments) with smooth scrolling - Tested with 150 segments
6. ✅ Loading state while fetching results - Spinner animation and loading message
7. ✅ Error handling if result fetch fails - User-friendly error message with retry button

**Epic 1 Completion:**
This story completes the Epic 1 foundational workflow:
- Upload → Progress Monitoring → Results Display ✅
- End-to-end transcription workflow fully functional

**Preparation for Epic 2:**
- Hover effects on subtitle segments for future click-to-timestamp
- Component structure supports media player integration
- ResultsView layout ready for inline editing features

### File List

**New Files Created:**
- frontend/src/utils/formatters.ts
- frontend/src/components/SubtitleList.vue
- frontend/src/__tests__/utils/formatters.test.ts
- frontend/src/__tests__/components/SubtitleList.test.ts
- frontend/src/__tests__/views/ResultsView.test.ts

**Files Modified:**
- frontend/src/views/ResultsView.vue (replaced placeholder with full implementation)
