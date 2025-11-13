# Story 1.6: Frontend Progress Monitoring

Status: done

## Story

As a user,
I want to see real-time progress while my file is transcribing,
So that I know the system is working and how long to wait.

## Acceptance Criteria

1. Progress page polls GET /status/{job_id} every 3 seconds
2. Progress bar or percentage displayed visually
3. Status message shows current state ("Task queued...", "Loading AI model...", "Transcribing audio...", "Aligning timestamps...", "Processing complete!")
4. On completion: Automatically navigates to results view
5. On error: Displays error message with retry option
6. User can safely navigate away and return using job_id (in URL)
7. Polling stops when job completes or fails

## Tasks / Subtasks

- [x] Task 1: Create Pinia store for job state management (AC: #1, #4, #7)
  - [x] Create frontend/src/stores/transcription.ts
  - [x] Define state: job_id, status, progress, message, segments
  - [x] Implement fetchStatus() action to call GET /status/{job_id}
  - [x] Implement fetchResult() action to call GET /result/{job_id}
  - [x] Add error handling in actions (try/catch with user-friendly messages)
  - [x] Test: Import store in a component, verify state updates on fetchStatus()

- [x] Task 2: Update API client with status and result endpoints (AC: #1, #4)
  - [x] Open frontend/src/services/api.ts
  - [x] Add fetchStatus(jobId: string): Promise<StatusResponse> function
  - [x] Add fetchResult(jobId: string): Promise<TranscriptionResult> function
  - [x] Update frontend/src/types/api.ts with StatusResponse interface
  - [x] Test: Mock API, verify fetch calls to correct endpoints

- [x] Task 3: Create ProgressBar component (AC: #2)
  - [x] Create frontend/src/components/ProgressBar.vue
  - [x] Accept progress prop (0-100 number)
  - [x] Render visual progress bar with percentage text
  - [x] Style with CSS: filled section vs empty section, smooth transition
  - [x] Ensure responsive layout (mobile, tablet, desktop)
  - [x] Test: Render with progress=50, verify 50% filled

- [x] Task 4: Create ProgressView page with polling (AC: #1, #2, #3, #6, #7)
  - [x] Create frontend/src/views/ProgressView.vue
  - [x] Extract job_id from route params: useRoute().params.job_id
  - [x] On mount: Start polling using setInterval(3000ms)
  - [x] Call store.fetchStatus() every 3 seconds
  - [x] Display ProgressBar component with store.progress
  - [x] Display status message from store.message
  - [x] On unmount: Clear interval to stop polling
  - [x] Store polling interval ID in component state for cleanup
  - [x] Test: Mount component, verify fetchStatus called every 3 seconds

- [x] Task 5: Implement auto-navigation on completion (AC: #4, #7)
  - [x] In ProgressView.vue: Watch store.status for "completed"
  - [x] When status === "completed": Stop polling (clearInterval)
  - [x] Call store.fetchResult() to load transcription segments
  - [x] Navigate to /results/{job_id} using router.push()
  - [x] Test: Mock completed status, verify navigation occurs

- [x] Task 6: Implement error handling with retry option (AC: #5, #7)
  - [x] In ProgressView.vue: Watch store.status for "failed"
  - [x] When status === "failed": Stop polling (clearInterval)
  - [x] Display error message from store.message
  - [x] Show retry button that restarts polling from beginning
  - [x] Retry action: Reset store state, navigate back to upload page
  - [x] Test: Mock failed status, verify error message and retry button displayed

- [x] Task 7: Add progress route to Vue Router (AC: #6)
  - [x] Open frontend/src/router/index.ts
  - [x] Add route: { path: '/progress/:jobId', component: ProgressView, name: 'progress' }
  - [x] Verify route params extraction works
  - [x] Test: Navigate to /progress/test-job-123, verify jobId accessible

- [x] Task 8: Update UploadView to navigate to progress page (AC: #6)
  - [x] Open frontend/src/views/UploadView.vue
  - [x] After successful upload (POST /upload returns job_id)
  - [x] Navigate to /progress/{job_id} using router.push()
  - [x] Test: Upload file, verify navigation to progress page

- [x] Task 9: Write comprehensive frontend tests (AC: #1-7)
  - [x] Create frontend/src/__tests__/stores/transcription.test.ts
  - [x] Test: fetchStatus() updates store.status, progress, message
  - [x] Test: fetchResult() updates store.segments
  - [x] Test: Error handling in store actions
  - [x] Create frontend/src/__tests__/components/ProgressBar.test.ts
  - [x] Test: Progress bar renders correctly with various progress values
  - [x] Test: Percentage text displays correctly
  - [x] Create frontend/src/__tests__/views/ProgressView.test.ts
  - [x] Test: Polling starts on mount, stops on unmount
  - [x] Test: Auto-navigation on completed status
  - [x] Test: Error display and retry on failed status
  - [x] Run: npm run test:unit -- --coverage, verify 60%+ coverage

## Dev Notes

### Learnings from Previous Story

**From Story 1-5-frontend-upload-interface (Status: done)**

- **Frontend Architecture Established**: Vue 3 + Vite + TypeScript project running on port 5173
- **Router Configuration**: Vue Router configured at frontend/src/router/index.ts with home route
- **API Client Pattern**: Native fetch() in frontend/src/services/api.ts with FormData and error handling
- **Type Safety**: TypeScript interfaces in frontend/src/types/api.ts (UploadResponse, ErrorResponse)
- **Component Structure**: Vue SFC pattern established (script setup, template, style order)
- **Responsive Design**: Mobile-first approach with breakpoints at 320px, 768px, 1024px
- **Error Handling**: User-friendly messages from backend `detail` field, try/catch in API calls
- **Testing Framework**: Vitest + @vue/test-utils configured with 60+ tests passing
- **Upload Flow Complete**: UploadView navigates to /progress/{job_id} after successful upload

**Key Integration Points for This Story:**
- Use established API client pattern in services/api.ts for status/result endpoints
- Follow Vue SFC component structure for ProgressView and ProgressBar
- Use router.push() navigation pattern already established
- Backend GET /status and GET /result endpoints ready (from Story 1.4)
- TypeScript types need StatusResponse and TranscriptionResult interfaces
- Follow responsive design patterns from FileUpload/UploadView

[Source: docs/stories/1-5-frontend-upload-interface.md#Dev-Agent-Record]

### Architectural Patterns and Constraints

**Pinia Store Pattern (from architecture.md):**

```typescript
// stores/transcription.ts - State Management for Job Lifecycle
import { defineStore } from 'pinia'
import type { Segment, StatusResponse } from '@/types/api'
import * as api from '@/services/api'

export const useTranscriptionStore = defineStore('transcription', {
  state: () => ({
    jobId: null as string | null,
    status: 'pending' as 'pending' | 'processing' | 'completed' | 'failed',
    progress: 0,
    message: '',
    segments: [] as Segment[],
    error: null as string | null
  }),

  getters: {
    isProcessing: (state) => state.status === 'processing' || state.status === 'pending',
    isCompleted: (state) => state.status === 'completed',
    isFailed: (state) => state.status === 'failed'
  },

  actions: {
    async fetchStatus(jobId: string) {
      try {
        const response = await api.fetchStatus(jobId)
        this.jobId = jobId
        this.status = response.status
        this.progress = response.progress
        this.message = response.message
        this.error = null
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to fetch status'
        throw error
      }
    },

    async fetchResult(jobId: string) {
      try {
        const response = await api.fetchResult(jobId)
        this.segments = response.segments
        this.error = null
      } catch (error) {
        this.error = error instanceof Error ? error.message : 'Failed to fetch result'
        throw error
      }
    },

    reset() {
      this.jobId = null
      this.status = 'pending'
      this.progress = 0
      this.message = ''
      this.segments = []
      this.error = null
    }
  }
})
```

**API Client Extensions (services/api.ts):**

```typescript
import type { StatusResponse, TranscriptionResult } from '@/types/api'

const API_BASE_URL = 'http://localhost:8000'

export async function fetchStatus(jobId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/status/${jobId}`)

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Job not found. Please check the job ID.')
    }
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch status')
  }

  return response.json()
}

export async function fetchResult(jobId: string): Promise<TranscriptionResult> {
  const response = await fetch(`${API_BASE_URL}/result/${jobId}`)

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Result not ready yet or job not found.')
    }
    const error = await response.json()
    throw new Error(error.detail || 'Failed to fetch result')
  }

  return response.json()
}
```

**TypeScript Type Definitions (types/api.ts):**

```typescript
export interface StatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number  // 0-100
  message: string
  created_at: string  // ISO 8601
  updated_at: string  // ISO 8601
}

export interface Segment {
  start: number  // Float seconds
  end: number    // Float seconds
  text: string
}

export interface TranscriptionResult {
  segments: Segment[]
}
```

**ProgressView.vue Pattern:**

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'
import ProgressBar from '@/components/ProgressBar.vue'

const route = useRoute()
const router = useRouter()
const store = useTranscriptionStore()

const jobId = ref(route.params.jobId as string)
const pollingInterval = ref<number | null>(null)
const errorMessage = ref<string | null>(null)

// Start polling on mount
onMounted(() => {
  startPolling()
})

// Cleanup on unmount
onUnmounted(() => {
  stopPolling()
})

// Watch for completion - auto-navigate to results
watch(() => store.status, async (newStatus) => {
  if (newStatus === 'completed') {
    stopPolling()
    try {
      await store.fetchResult(jobId.value)
      router.push(`/results/${jobId.value}`)
    } catch (error) {
      errorMessage.value = 'Failed to load results. Please try again.'
    }
  } else if (newStatus === 'failed') {
    stopPolling()
    errorMessage.value = store.message || 'Transcription failed. Please try again.'
  }
})

function startPolling() {
  // Poll immediately
  pollStatus()

  // Then poll every 3 seconds
  pollingInterval.value = window.setInterval(pollStatus, 3000)
}

function stopPolling() {
  if (pollingInterval.value !== null) {
    clearInterval(pollingInterval.value)
    pollingInterval.value = null
  }
}

async function pollStatus() {
  try {
    await store.fetchStatus(jobId.value)
  } catch (error) {
    console.error('Polling error:', error)
    // Continue polling on transient errors
  }
}

function handleRetry() {
  errorMessage.value = null
  store.reset()
  router.push('/')
}
</script>

<template>
  <div class="progress-view">
    <h1>Processing Your Transcription</h1>
    <p class="job-id">Job ID: {{ jobId }}</p>

    <ProgressBar :progress="store.progress" />

    <p class="status-message">{{ store.message }}</p>

    <div v-if="errorMessage || store.isFailed" class="error-section">
      <p class="error-message">{{ errorMessage || store.message }}</p>
      <button @click="handleRetry" class="retry-button">
        Retry with New File
      </button>
    </div>

    <p class="tip">
      You can safely navigate away from this page.
      Bookmark this URL to check progress later.
    </p>
  </div>
</template>

<style scoped>
.progress-view {
  max-width: 600px;
  margin: 2rem auto;
  padding: 2rem;
}

.job-id {
  font-size: 0.9rem;
  color: #666;
  font-family: monospace;
}

.status-message {
  margin: 1.5rem 0;
  font-size: 1.1rem;
  color: #333;
  text-align: center;
}

.error-section {
  margin-top: 2rem;
  padding: 1rem;
  background-color: #ffebee;
  border-radius: 4px;
}

.error-message {
  color: #c62828;
  margin-bottom: 1rem;
}

.retry-button {
  padding: 0.75rem 2rem;
  font-size: 1rem;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.retry-button:hover {
  background-color: #359268;
}

.tip {
  margin-top: 2rem;
  font-size: 0.9rem;
  color: #999;
  text-align: center;
}

@media (max-width: 768px) {
  .progress-view {
    padding: 1rem;
  }
}
</style>
```

**ProgressBar.vue Pattern:**

```vue
<script setup lang="ts">
defineProps<{
  progress: number  // 0-100
}>()
</script>

<template>
  <div class="progress-bar-container">
    <div class="progress-bar">
      <div
        class="progress-bar-fill"
        :style="{ width: `${progress}%` }"
      />
    </div>
    <p class="progress-text">{{ progress }}%</p>
  </div>
</template>

<style scoped>
.progress-bar-container {
  margin: 2rem 0;
}

.progress-bar {
  width: 100%;
  height: 30px;
  background-color: #e0e0e0;
  border-radius: 15px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background-color: #42b983;
  transition: width 0.3s ease;
}

.progress-text {
  margin-top: 0.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
  text-align: center;
}
</style>
```

[Source: docs/architecture.md#State-Management-Patterns, docs/architecture.md#Component-Structure-Pattern]

### Source Tree Components to Touch

**New Files to Create:**

```
frontend/src/
├── stores/
│   └── transcription.ts          # NEW: Pinia store for job state management
├── components/
│   └── ProgressBar.vue           # NEW: Progress visualization component
└── views/
    └── ProgressView.vue          # NEW: Progress monitoring page
```

**Existing Files to Modify:**

```
frontend/src/
├── router/
│   └── index.ts                  # ADD: /progress/:jobId route
├── services/
│   └── api.ts                    # ADD: fetchStatus() and fetchResult() functions
├── types/
│   └── api.ts                    # ADD: StatusResponse, TranscriptionResult, Segment interfaces
└── views/
    └── UploadView.vue            # MODIFY: Navigate to /progress after upload
```

**Files NOT to Touch:**
- Backend API endpoints (already implemented in Stories 1.2-1.4)
- FileUpload.vue (complete in Story 1.5)
- EditorView.vue, SubtitleList.vue (Story 1.7 will create)

### Testing Standards Summary

**Frontend Testing Requirements (from Testing Strategy):**

- **Framework**: Vitest + @vue/test-utils
- **Coverage Target**: 60%+ for frontend components
- **Test Organization**: Store tests in `__tests__/stores/`, component tests in `__tests__/components/`, view tests in `__tests__/views/`

**Test Scenarios to Cover:**

**1. Pinia Store Tests (src/__tests__/stores/transcription.test.ts):**
- State initialization: Default values set correctly
- fetchStatus() success: Updates status, progress, message
- fetchStatus() failure: Sets error, throws exception
- fetchResult() success: Updates segments array
- fetchResult() failure: Sets error, throws exception
- Getters: isProcessing, isCompleted, isFailed return correct values
- reset() action: Clears all state

**2. ProgressBar Component Tests (src/__tests__/components/ProgressBar.test.ts):**
- Render: Progress bar displays with correct width
- Percentage text: Shows correct number (0%, 50%, 100%)
- Transition: CSS transition applied for smooth animation
- Edge cases: progress=0, progress=100, progress=50

**3. ProgressView Tests (src/__tests__/views/ProgressView.test.ts):**
- Mount: Polling starts immediately (fetchStatus called)
- Polling interval: fetchStatus called every 3 seconds
- Unmount: clearInterval called to stop polling
- Completed status: Navigation to /results/{job_id} triggered
- Failed status: Error message displayed, retry button shown
- Retry action: Navigates back to upload page
- Job ID display: Route params extracted correctly

**Mock Strategies:**
- **API Calls**: Mock fetchStatus() and fetchResult() using vitest.mock
- **Router**: Mock useRouter() and useRoute(), verify push() and params
- **Intervals**: Use vitest fake timers (vi.useFakeTimers) to test polling
- **Store**: Create test Pinia instance, verify state changes

**Test Execution:**
```bash
cd frontend
npm run test:unit -- --coverage
# Target: 60%+ coverage on new components/store
```

[Source: docs/architecture.md#Testing-Strategy]

### Project Structure Notes

**Alignment with Unified Project Structure:**

This story extends the foundational frontend architecture established in Story 1.5 by adding:

- **State Management**: Pinia store (transcription.ts) provides centralized job state accessible across all views
- **Polling Pattern**: setInterval/clearInterval for 3-second status checks, cleaned up on unmount to prevent memory leaks
- **Route Parameters**: URL contains job_id (/progress/:jobId) enabling bookmark/share, satisfies AC #6
- **Auto-navigation**: Vue Router watch pattern for status changes, seamless flow to results page
- **Error Recovery**: Explicit error states with user-facing retry action, enhances reliability (NFR-003)

**Integration with Previous Stories:**
- **Story 1.4**: GET /status and GET /result endpoints provide backend data
- **Story 1.5**: UploadView navigation hands off job_id to ProgressView

**Preparation for Story 1.7:**
- Pinia store segments array will be consumed by SubtitleList component
- Router navigation to /results/:jobId will load EditorView

No conflicts detected - this story fits naturally between upload (1.5) and display (1.7).

### References

- [Source: docs/epics.md#Story-1.6] - User story statement and acceptance criteria
- [Source: docs/tech-spec-epic-1.md#Progress-Tracking-Structure] - Redis status format, 5-stage progress messages
- [Source: docs/tech-spec-epic-1.md#APIs-and-Interfaces] - GET /status and GET /result endpoint specifications
- [Source: docs/tech-spec-epic-1.md#Workflows-and-Sequencing] - End-to-end polling and navigation flow
- [Source: docs/architecture.md#State-Management-Patterns] - Pinia store organization and action patterns
- [Source: docs/architecture.md#Component-Structure-Pattern] - Vue SFC structure (script/template/style order)
- [Source: docs/architecture.md#Frontend-API-Client] - Native fetch() pattern, error handling strategy
- [Source: docs/architecture.md#TypeScript-Type-Definitions] - StatusResponse, TranscriptionResult, Segment interfaces
- [Source: docs/architecture.md#Testing-Strategy] - Vitest setup, coverage targets, mock strategies

## Dev Agent Record

### Context Reference

- docs/stories/1-6-frontend-progress-monitoring.context.xml

### Agent Model Used

claude-sonnet-4-5-20250929

### Debug Log References

### Completion Notes
**Completed:** 2025-11-06
**Definition of Done:** All acceptance criteria met, code reviewed, tests passing

### Completion Notes List

**Date: 2025-11-06**

✅ **Pinia Store Implementation (Task 1)**
- Created frontend/src/stores/transcription.ts with complete state management
- Implemented fetchStatus() and fetchResult() actions with proper error handling
- Added getters for convenient status checking (isProcessing, isCompleted, isFailed)
- 100% test coverage achieved with comprehensive store tests

✅ **API Client Extensions (Task 2)**
- Extended frontend/src/services/api.ts with fetchStatus() and fetchResult() functions
- Added StatusResponse, Segment, and TranscriptionResult interfaces to types/api.ts
- Followed established error handling patterns (404 checks, detail parsing)
- 100% coverage on all new API functions

✅ **ProgressBar Component (Task 3)**
- Created reusable ProgressBar.vue component with props-based API
- Implemented smooth CSS transition animation (0.3s ease)
- Responsive design with mobile-first approach
- 100% test coverage including prop updates and rendering

✅ **ProgressView with Polling (Tasks 4-6)**
- Created ProgressView.vue with 3-second polling using setInterval
- Proper cleanup: clearInterval on unmount prevents memory leaks
- Auto-navigation on completion after loading segments
- Error handling with retry functionality (resets store, navigates to home)
- Watch pattern for status changes enables reactive UI updates
- 97.01% test coverage with fake timers for polling tests

✅ **Router Integration (Task 7-8)**
- Router already had /progress/:job_id route configured
- UploadView already navigating to progress page with job_id
- Route parameter extraction using job_id (underscore, not camelCase)

✅ **Comprehensive Testing (Task 9)**
- Created 3 new test files: transcription.test.ts, ProgressBar.test.ts, ProgressView.test.ts
- Extended api.test.ts with 8 new tests for fetchStatus/fetchResult
- Added 33 new tests total (101 tests passing overall)
- **Final coverage: 62.75%** (exceeds 60% requirement)
- Used vitest fake timers to test polling without waiting 3 real seconds
- Mocked Vue Router and Pinia for isolated component testing

**Key Technical Decisions:**
- Used window.setInterval instead of setTimeout recursion for cleaner polling control
- Polling continues on transient errors (network timeouts) but stops on failed/completed status
- Error state stored in both component local ref and store for flexible UI rendering
- Auto-navigation calls fetchResult() before router.push() to ensure data ready for next view
- Created ResultsView placeholder to support AC#4 auto-navigation (full implementation in Story 1.7)

### File List

**New Files Created:**
- frontend/src/stores/transcription.ts
- frontend/src/components/ProgressBar.vue
- frontend/src/views/ResultsView.vue (placeholder for auto-navigation)
- frontend/src/__tests__/transcription.test.ts
- frontend/src/__tests__/ProgressBar.test.ts
- frontend/src/__tests__/ProgressView.test.ts

**Modified Files:**
- frontend/src/types/api.ts (added StatusResponse, Segment, TranscriptionResult)
- frontend/src/services/api.ts (added fetchStatus, fetchResult functions)
- frontend/src/views/ProgressView.vue (replaced placeholder with full implementation)
- frontend/src/__tests__/api.test.ts (added 8 tests for new API functions)
- frontend/src/router/index.ts (added /results/:job_id route for auto-navigation)
- frontend/src/views/ResultsView.vue (created placeholder for AC#4 auto-navigation)
