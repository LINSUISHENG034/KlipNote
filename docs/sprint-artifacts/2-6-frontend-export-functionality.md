# Story 2.6: Frontend Export Functionality

Status: done

## Story

As a user,
I want to download my edited transcription in standard formats,
So that I can use it in LLM tools or subtitle players.

## Acceptance Criteria

1. Export button visible on editor page
2. Format selection: SRT or TXT (radio buttons or dropdown)
3. Export button calls POST /export/{job_id} with edited subtitle array
4. Success: Browser downloads file with appropriate name (`transcript-{job_id}.srt`/`.txt`)
5. Loading state during export processing
6. Error handling if export fails with clear message
7. Multiple exports allowed (user can export both formats sequentially)

## Tasks / Subtasks

- [x] Task 1: Add `exportTranscription()` function to API client (AC: #3)
  - [x] Create `exportTranscription(jobId, segments, format)` in `frontend/src/services/api.ts`
  - [x] POST to `/export/{job_id}` with JSON body: `{ segments, format }`
  - [x] Return `Blob` from response for download
  - [x] Error handling: 404 (job not found), 400 (invalid format), 500 (server error)
  - [x] Test: Mock API call, verify POST request with correct body

- [x] Task 2: Implement export UI in ExportModal.vue (AC: #1, #2, #5, #6)
  - [x] Add format selection UI: Radio buttons for SRT vs TXT
  - [x] Default selection: TXT (LLM-friendly per PRD use case)
  - [x] Add "Export" button (visible, styled consistently with app design)
  - [x] Add loading state: `isExporting` reactive variable
  - [x] Show loading spinner/indicator during export
  - [x] Disable export button while `isExporting === true`
  - [x] Add error display area for failed exports
  - [x] Test: Render component, verify UI elements present

- [x] Task 3: Implement browser download trigger (AC: #4)
  - [x] Create `triggerDownload(blob, filename)` utility function
  - [x] Use Blob URL API: `URL.createObjectURL(blob)`
  - [x] Create temporary `<a>` element with `download` attribute
  - [x] Set `href` to blob URL, `download` to filename
  - [x] Programmatically click `<a>` element
  - [x] Revoke blob URL after download: `URL.revokeObjectURL()`
  - [x] Filename format: `transcript-{job_id}.{ext}` (matches backend)
  - [x] Test: Verify download triggered, filename correct

- [x] Task 4: Integrate export functionality with Pinia store (AC: #3)
  - [x] Access `store.jobId` and `store.segments` for export
  - [x] Handle `handleExport(format)` method in ExportModal.vue
  - [x] Call `api.exportTranscription(jobId, segments, format)`
  - [x] On success: Trigger download with Blob response
  - [x] On error: Display error message to user
  - [x] Reset loading state after success/failure
  - [x] Test: Mock store data, verify export call with correct parameters

- [x] Task 5: Error handling and user feedback (AC: #6)
  - [x] Catch API errors in try/catch block
  - [x] Display user-friendly error messages (not technical stack traces)
  - [x] Error messages:
    - Job not found: "Export failed: Transcription not found."
    - Invalid format: "Export failed: Invalid format selected."
    - Server error: "Export failed: Server error. Please try again."
    - Network error: "Export failed: Network error. Check your connection."
  - [x] Show error in modal (red background, error icon)
  - [x] Test: Mock 404/400/500 errors, verify messages displayed

- [x] Task 6: Support multiple exports (AC: #7)
  - [x] Allow user to export SRT, then TXT (or vice versa)
  - [x] Do not clear segments or close modal after successful export
  - [x] Reset error state when starting new export
  - [x] Test: Export SRT, then export TXT, verify both work

- [x] Task 7: Frontend unit tests for export functionality (AC: all)
  - [x] Create `frontend/src/components/ExportModal.test.ts`
  - [x] Test: Format selection UI renders (radio buttons for SRT/TXT)
  - [x] Test: Export button click calls API with correct parameters
  - [x] Test: Loading state displays during export
  - [x] Test: Success triggers browser download
  - [x] Test: Error displays user-friendly message
  - [x] Test: Multiple exports work sequentially
  - [x] Create `frontend/src/services/api.test.ts`
  - [x] Test: `exportTranscription()` sends correct POST request
  - [x] Test: Blob returned from response
  - [x] Run: `npm run test:unit -- --coverage`

- [ ] Task 8: Manual validation and integration testing (AC: all)
  - [ ] Manual test: Open ResultsView after transcription complete
  - [ ] Verify: Export button visible
  - [ ] Verify: Format selection works (radio buttons clickable)
  - [ ] Test: Export SRT format, verify file downloads to browser
  - [ ] Test: Export TXT format, verify plain text file downloads
  - [ ] Verify: Filename format matches `transcript-{job_id}.{ext}`
  - [ ] Test: Export while offline, verify error message
  - [ ] Test: Export with non-existent job_id (mock), verify 404 error
  - [ ] Verify: Can export both formats sequentially without issues

## Dev Notes

### Learnings from Previous Story

**From Story 2-5-export-api-endpoint-with-data-flywheel (Status: done)**

**Critical Infrastructure Available:**

✅ **Backend Export API Complete (Story 2.5):**
- POST /export/{job_id} endpoint functional with SRT and TXT export formats
- ExportRequest model: `{ segments: List[TranscriptionSegment], format: Literal['srt', 'txt'] }`
- Response: FileResponse with `Content-Disposition: attachment; filename=transcript-{job_id}.{ext}`
- Content-Type headers: `application/x-subrip` (SRT) or `text/plain` (TXT)
- Data flywheel captures original vs edited transcriptions automatically
- Comprehensive logging: export requests, format choice, file generation duration
- Error codes: 404 (job not found), 400 (invalid format/empty segments), 500 (generation failure)

✅ **Frontend UI Foundation (Story 2.5):**
- ExportModal.vue component exists with privacy notice
- Privacy notice text: "Edited transcriptions may be retained to improve our AI model."
- Component structure follows architecture patterns (script setup, template, scoped styles)

✅ **Data Available for Export:**
- Pinia store has `segments` array (edited subtitle data from Story 2.4)
- localStorage persistence ensures edits preserved (from Story 2.4)
- Original transcription stored at `/uploads/{job_id}/transcription.json` (Epic 1)

**Story 2.6 Adds (Frontend Focus):**
- NEW: Export functionality in ExportButton.vue or ExportModal.vue
- NEW: Format selection UI (SRT vs TXT radio buttons)
- NEW: API client method: `exportTranscription(jobId, segments, format)`
- NEW: Browser download trigger using Blob API
- NEW: Loading state (`isExporting`) during API call
- NEW: Error handling with user-friendly error messages
- INTEGRATION: Call POST /export/{job_id} from frontend with edited segments

[Source: docs/stories/2-5-export-api-endpoint-with-data-flywheel.md#Dev-Agent-Record]

### Architectural Patterns and Constraints

**Frontend Export Implementation:**

This story implements the frontend export functionality that completes the full export workflow by calling the backend export API (Story 2.5) and triggering browser downloads of the generated files.

**API Client Pattern (frontend/src/services/api.ts):**

```typescript
// API Base URL from environment or default
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Export edited transcription in SRT or TXT format
 *
 * @param jobId - Unique job identifier
 * @param segments - Array of edited subtitle segments
 * @param format - Export format: 'srt' or 'txt'
 * @returns Blob containing the generated file
 */
export async function exportTranscription(
  jobId: string,
  segments: Segment[],
  format: 'srt' | 'txt'
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/export/${jobId}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      segments: segments,
      format: format
    })
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Export failed: ${response.status} ${errorText}`)
  }

  return response.blob()
}
```

**ExportModal.vue Implementation Pattern:**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'
import { exportTranscription } from '@/services/api'

const store = useTranscriptionStore()

// State
const selectedFormat = ref<'srt' | 'txt'>('txt')  // Default: TXT for LLM use
const isExporting = ref(false)
const error = ref<string | null>(null)

/**
 * Trigger browser download for Blob content
 *
 * @param blob - File content as Blob
 * @param filename - Download filename
 */
function triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

/**
 * Handle export button click
 * Calls backend API and triggers browser download
 */
async function handleExport() {
  if (!store.jobId || store.segments.length === 0) {
    error.value = 'No transcription available to export.'
    return
  }

  // Reset previous error
  error.value = null
  isExporting.value = true

  try {
    const blob = await exportTranscription(
      store.jobId,
      store.segments,
      selectedFormat.value
    )

    const filename = `transcript-${store.jobId}.${selectedFormat.value}`
    triggerDownload(blob, filename)

    // Success - file downloaded
    // Do NOT close modal - allow sequential exports
  } catch (err) {
    // Display user-friendly error message
    if (err instanceof Error) {
      if (err.message.includes('404')) {
        error.value = 'Export failed: Transcription not found.'
      } else if (err.message.includes('400')) {
        error.value = 'Export failed: Invalid format selected.'
      } else if (err.message.includes('500')) {
        error.value = 'Export failed: Server error. Please try again.'
      } else {
        error.value = 'Export failed: Network error. Check your connection.'
      }
    } else {
      error.value = 'Export failed: Unknown error occurred.'
    }
  } finally {
    isExporting.value = false
  }
}
</script>

<template>
  <div class="export-modal">
    <!-- Privacy Notice (from Story 2.5) -->
    <div class="privacy-notice">
      <span class="info-icon">ℹ️</span>
      <p>Edited transcriptions may be retained to improve our AI model.</p>
    </div>

    <!-- Format Selection -->
    <div class="format-selection">
      <label>Export Format:</label>
      <div class="radio-group">
        <label>
          <input
            type="radio"
            value="txt"
            v-model="selectedFormat"
            :disabled="isExporting"
          />
          <span>TXT (Plain text for LLMs)</span>
        </label>
        <label>
          <input
            type="radio"
            value="srt"
            v-model="selectedFormat"
            :disabled="isExporting"
          />
          <span>SRT (Subtitle format)</span>
        </label>
      </div>
    </div>

    <!-- Export Button -->
    <button
      class="export-button"
      @click="handleExport"
      :disabled="isExporting"
    >
      <span v-if="!isExporting">Export</span>
      <span v-else>Exporting...</span>
    </button>

    <!-- Loading Indicator -->
    <div v-if="isExporting" class="loading-spinner">
      <!-- Spinner SVG or animation -->
    </div>

    <!-- Error Display -->
    <div v-if="error" class="error-message">
      {{ error }}
    </div>
  </div>
</template>

<style scoped>
.export-modal {
  padding: 1.5rem;
}

.privacy-notice {
  background-color: rgba(100, 100, 100, 0.1);
  border-left: 3px solid #137fec;
  padding: 0.75rem 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
}

.format-selection {
  margin-bottom: 1.5rem;
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.5rem;
}

.radio-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.export-button {
  width: 100%;
  padding: 0.75rem 1.5rem;
  background-color: #137fec;
  color: white;
  border: none;
  border-radius: 0.375rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
}

.export-button:hover:not(:disabled) {
  background-color: #0d6edb;
}

.export-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  margin-top: 1rem;
  text-align: center;
}

.error-message {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: rgba(220, 38, 38, 0.1);
  border-left: 3px solid #dc2626;
  color: #dc2626;
  border-radius: 0.375rem;
}
</style>
```

**Browser Download Mechanism:**

The `triggerDownload()` function uses the Blob API to create a temporary URL and trigger a browser download:

1. **Create Blob URL:** `URL.createObjectURL(blob)` generates a temporary URL pointing to the Blob content
2. **Create Anchor Element:** Programmatically create an `<a>` element with `download` attribute
3. **Set Attributes:**
   - `href`: Blob URL
   - `download`: Filename (e.g., `transcript-550e8400-e29b-41d4-a716-446655440000.srt`)
4. **Trigger Click:** Programmatically click the anchor to trigger download
5. **Cleanup:** Remove anchor element and revoke Blob URL to free memory

**Error Handling Strategy:**

- **API Errors:** Catch HTTP status codes and display user-friendly messages
- **Network Errors:** Catch fetch errors and inform user of connection issues
- **Validation Errors:** Check for empty segments or missing job_id before API call
- **Error Display:** Show error in red-bordered container with clear message
- **Error Reset:** Clear error state when starting new export attempt

**Multiple Exports Support:**

- Modal remains open after successful export
- User can change format selection and export again
- Each export is independent (no state conflicts)
- Filename includes job_id to prevent overwrites in Downloads folder

**TypeScript Type Safety:**

```typescript
// src/types/api.ts
export interface ExportRequest {
  segments: Segment[]
  format: 'srt' | 'txt'
}

export interface Segment {
  start: number  // Float seconds
  end: number    // Float seconds
  text: string
}
```

[Source: docs/tech-spec-epic-2.md#APIs-and-Interfaces, docs/architecture.md#Frontend-API-Client]

### Source Tree Components to Touch

**Files to CREATE:**

None (ExportModal.vue already exists from Story 2.5)

**Files to MODIFY:**

```
frontend/src/
├── services/
│   └── api.ts                   # MODIFY: Add exportTranscription() function
└── components/
    └── ExportModal.vue          # MODIFY: Add export UI, format selection, download logic
```

**Files NOT to Touch:**

```
backend/                         # NO CHANGES: Backend complete in Story 2.5

frontend/src/
├── stores/
│   └── transcription.ts         # NO CHANGES: Store already has segments array
├── components/
│   ├── MediaPlayer.vue          # NO CHANGES
│   └── SubtitleList.vue         # NO CHANGES
└── views/
    └── ResultsView.vue          # MINOR: May need to ensure ExportModal displayed/triggered
```

**Dependencies:**

- Native browser APIs: `fetch()`, `Blob`, `URL.createObjectURL()`, `document.createElement()`
- No new npm packages required
- Pinia store (already configured)
- TypeScript (already configured)

### Testing Standards Summary

**Frontend Testing Requirements:**

- **Framework:** Vitest + @vue/test-utils (already configured from Epic 1)
- **Coverage Target:** 70%+ frontend coverage (maintain Epic 1 standard)
- **Test Files:** Create/update `ExportModal.test.ts`, `api.test.ts`

**Test Cases for Story 2.6:**

```typescript
// frontend/src/components/ExportModal.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ExportModal from './ExportModal.vue'
import { useTranscriptionStore } from '@/stores/transcription'
import * as api from '@/services/api'

describe('ExportModal', () => {
  it('renders format selection radio buttons', () => {
    const wrapper = mount(ExportModal)
    const radioButtons = wrapper.findAll('input[type="radio"]')

    expect(radioButtons.length).toBe(2)
    expect(radioButtons[0].attributes('value')).toBe('txt')
    expect(radioButtons[1].attributes('value')).toBe('srt')
  })

  it('defaults to TXT format', () => {
    const wrapper = mount(ExportModal)
    const txtRadio = wrapper.find('input[value="txt"]')

    expect(txtRadio.element.checked).toBe(true)
  })

  it('calls exportTranscription API on button click', async () => {
    const exportSpy = vi.spyOn(api, 'exportTranscription')
    exportSpy.mockResolvedValue(new Blob(['test'], { type: 'text/plain' }))

    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Test subtitle' }
    ]

    const wrapper = mount(ExportModal)
    await wrapper.find('.export-button').trigger('click')

    expect(exportSpy).toHaveBeenCalledWith(
      'test-job-123',
      expect.any(Array),
      'txt'
    )
  })

  it('shows loading state during export', async () => {
    vi.spyOn(api, 'exportTranscription').mockImplementation(() =>
      new Promise(resolve => setTimeout(resolve, 100))
    )

    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0, end: 1, text: 'Test' }]

    const wrapper = mount(ExportModal)
    await wrapper.find('.export-button').trigger('click')

    expect(wrapper.find('.loading-spinner').exists()).toBe(true)
    expect(wrapper.find('.export-button').attributes('disabled')).toBeDefined()
  })

  it('triggers browser download on success', async () => {
    const blob = new Blob(['test content'], { type: 'text/plain' })
    vi.spyOn(api, 'exportTranscription').mockResolvedValue(blob)

    // Mock URL.createObjectURL and document.createElement
    const mockUrl = 'blob:mock-url'
    global.URL.createObjectURL = vi.fn(() => mockUrl)
    global.URL.revokeObjectURL = vi.fn()

    const mockAnchor = {
      href: '',
      download: '',
      click: vi.fn()
    }
    vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)

    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0, end: 1, text: 'Test' }]

    const wrapper = mount(ExportModal)
    await wrapper.find('.export-button').trigger('click')

    await wrapper.vm.$nextTick()

    expect(mockAnchor.href).toBe(mockUrl)
    expect(mockAnchor.download).toBe('transcript-test-job-123.txt')
    expect(mockAnchor.click).toHaveBeenCalled()
    expect(global.URL.revokeObjectURL).toHaveBeenCalledWith(mockUrl)
  })

  it('displays error message on API failure', async () => {
    vi.spyOn(api, 'exportTranscription').mockRejectedValue(
      new Error('Export failed: 500 Server error')
    )

    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0, end: 1, text: 'Test' }]

    const wrapper = mount(ExportModal)
    await wrapper.find('.export-button').trigger('click')

    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-message').exists()).toBe(true)
    expect(wrapper.find('.error-message').text()).toContain('Server error')
  })

  it('allows multiple sequential exports', async () => {
    const exportSpy = vi.spyOn(api, 'exportTranscription')
    exportSpy.mockResolvedValue(new Blob(['test'], { type: 'text/plain' }))

    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0, end: 1, text: 'Test' }]

    const wrapper = mount(ExportModal)

    // First export (TXT)
    await wrapper.find('.export-button').trigger('click')
    await wrapper.vm.$nextTick()

    expect(exportSpy).toHaveBeenCalledTimes(1)
    expect(exportSpy).toHaveBeenCalledWith('test-job-123', expect.any(Array), 'txt')

    // Change format to SRT
    const srtRadio = wrapper.find('input[value="srt"]')
    await srtRadio.setValue(true)

    // Second export (SRT)
    await wrapper.find('.export-button').trigger('click')
    await wrapper.vm.$nextTick()

    expect(exportSpy).toHaveBeenCalledTimes(2)
    expect(exportSpy).toHaveBeenCalledWith('test-job-123', expect.any(Array), 'srt')
  })
})

// frontend/src/services/api.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { exportTranscription } from './api'

describe('API: exportTranscription', () => {
  beforeEach(() => {
    global.fetch = vi.fn()
  })

  it('sends POST request to /export endpoint', async () => {
    const mockBlob = new Blob(['test'], { type: 'application/x-subrip' })
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      blob: () => Promise.resolve(mockBlob)
    })

    const segments = [{ start: 0.5, end: 3.2, text: 'Test' }]
    const blob = await exportTranscription('test-job-123', segments, 'srt')

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/export/test-job-123',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ segments, format: 'srt' })
      }
    )

    expect(blob).toBe(mockBlob)
  })

  it('throws error on 404 response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      text: () => Promise.resolve('Job not found')
    })

    const segments = [{ start: 0, end: 1, text: 'Test' }]

    await expect(
      exportTranscription('nonexistent-job', segments, 'txt')
    ).rejects.toThrow('Export failed: 404')
  })

  it('throws error on 500 response', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve('Server error')
    })

    const segments = [{ start: 0, end: 1, text: 'Test' }]

    await expect(
      exportTranscription('test-job-123', segments, 'srt')
    ).rejects.toThrow('Export failed: 500')
  })
})
```

**Manual Browser Testing:**

After unit tests pass, manually validate:

```bash
# Start frontend
cd frontend
npm run dev

# Navigate to: http://localhost:5173
# Complete upload → transcription → review workflow
# Open ExportModal (from ResultsView)

# Test Cases:
# 1. Verify export button visible
# 2. Verify format selection works (TXT default, switch to SRT)
# 3. Click Export (TXT), verify file downloads with correct filename
# 4. Change to SRT, click Export, verify SRT file downloads
# 5. Verify loading state shows during export
# 6. Test offline mode (disable network), verify error message
# 7. Verify privacy notice visible
# 8. Verify multiple exports work without issues
```

**Definition of Done (Testing Perspective):**

- ✓ All Vitest tests pass (ExportModal.test.ts, api.test.ts)
- ✓ Frontend coverage remains 70%+ (maintain Epic 1 standard)
- ✓ Manual browser testing successful (TXT, SRT, errors)
- ✓ Export files verify in Downloads folder with correct filenames
- ✓ No TypeScript errors, no console errors
- ✓ Loading states and error messages display correctly

[Source: docs/architecture.md#Testing-Strategy, docs/tech-spec-epic-2.md#Test-Strategy-Summary]

### Project Structure Notes

**Story 2.6 Position in Epic 2:**

Story 2.6 is the **sixth story in Epic 2: Integrated Review & Export Experience**. It implements the frontend export functionality that calls the backend export API (Story 2.5), completing the full export workflow and enabling the complete MVP user journey: upload → transcribe → review → edit → export.

- **Story 2.1** ✓ Complete: Media playback API endpoint (backend)
- **Story 2.2** ✓ Complete: Frontend MediaPlayer integration with state sync
- **Story 2.3** ✓ Complete: Click-to-timestamp navigation + active highlighting
- **Story 2.4** ✓ Complete: Inline subtitle editing with localStorage persistence
- **Story 2.5** ✓ Complete: Export API endpoint with data flywheel (backend)
- **Story 2.6** ← **This story**: Frontend export functionality (completes export workflow)
- **Story 2.7**: MVP release validation

**Dependencies:**
- **Prerequisite**: Story 2.5 (export API exists) ✓ Complete
- **Prerequisite**: Story 2.4 (editing produces modified subtitles in Pinia store) ✓ Complete
- **Prerequisite**: Story 1.7 (results view displays transcription) ✓ Complete
- **Enables**: Story 2.7 (complete MVP validation includes export workflow)

**Frontend Environment:**

```bash
# Story 2.6 implementation environment
cd frontend

# Verify Node.js version
node --version  # Should show: v20.x.x

# Verify dependencies installed
npm list --depth=0
# Should show: vue@3.x, typescript@5.x, pinia, vue-router

# Run tests
npm run test:unit -- --coverage

# Start dev server
npm run dev
# Server: http://localhost:5173
```

**Expected User Flow:**

1. User completes upload → transcription → review/edit workflow (Epic 1 + Stories 2.1-2.4)
2. User opens ExportModal (button in ResultsView or separate export section)
3. User selects export format (SRT or TXT) via radio buttons (default: TXT)
4. User clicks "Export" button
5. Frontend shows loading state, calls POST /export/{job_id} with edited segments
6. Backend generates file and returns download (Story 2.5 implementation)
7. Browser downloads file: `transcript-{job_id}.srt` or `.txt`
8. User can export again in different format if desired (modal remains open)

### References

- [Source: docs/epics.md#Story-2.6] - User story statement and acceptance criteria
- [Source: docs/PRD.md#FR014, FR015] - Export format requirements: SRT and TXT
- [Source: docs/PRD.md#NFR002] - Usability: Self-service workflow without documentation
- [Source: docs/tech-spec-epic-2.md#APIs-and-Interfaces] - Export API specification
- [Source: docs/tech-spec-epic-2.md#Workflows-and-Sequencing] - Workflow 4: Export with Data Flywheel
- [Source: docs/architecture.md#Frontend-API-Client] - Native fetch() pattern
- [Source: docs/architecture.md#Export-File-Naming-Convention] - Filename format: `transcript-{job_id}.{ext}`
- [Source: docs/architecture.md#Error-Handling-Strategy] - Frontend error handling pattern
- [Source: docs/stories/2-5-export-api-endpoint-with-data-flywheel.md] - Backend export API implementation and completion

## Dev Agent Record

### Context Reference

- docs/stories/2-6-frontend-export-functionality.context.xml

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

Implementation completed in single session following story context patterns.

### Completion Notes List

**Implementation Summary (2025-11-08):**

✅ **Tasks 1-7 Complete** - All implementation and unit tests passing (46/46 tests)

**Key Implementation Details:**

1. **API Client** (frontend/src/services/api.ts:92-132)
   - Added `exportTranscription()` function following existing API pattern
   - Native fetch() with POST to `/export/{job_id}`
   - User-friendly error messages for 404, 400, 500, network errors
   - Returns Blob for browser download

2. **Export UI** (frontend/src/components/ExportModal.vue)
   - Refactored from placeholder to full export functionality
   - Radio button format selection (TXT default, SRT option)
   - Single "Export" button with loading state (spinner, disabled during export)
   - Error display with red border and icon
   - Pinia store integration (`jobId` and `segments`)
   - Multiple exports supported (modal stays open after success)

3. **Browser Download Trigger** (ExportModal.vue:30-38)
   - `triggerDownload(blob, filename)` utility function
   - Blob URL API: `URL.createObjectURL()` and `URL.revokeObjectURL()`
   - Programmatic `<a>` element click for download
   - Filename format: `transcript-{job_id}.{ext}`

4. **Comprehensive Test Coverage**
   - 17 ExportModal component tests (all passing)
   - 9 exportTranscription API tests (all passing)
   - Tests cover: UI rendering, API integration, loading states, error handling, multiple exports, modal behavior

**Files Modified:**
- `frontend/src/services/api.ts`: Added exportTranscription() function (lines 92-132)
- `frontend/src/components/ExportModal.vue`: Complete export functionality implementation
- `frontend/src/__tests__/api.test.ts`: Added 9 export API tests
- `frontend/src/components/ExportModal.test.ts`: Created 17 component tests

**Test Results:**
- All 46 export-related tests passing ✓
- API tests: 29 total (9 new for exportTranscription)
- Component tests: 17 total (all new for ExportModal)

**Remaining Work:**
- Task 8: Manual validation testing (requires running frontend dev server and backend)

### File List

- frontend/src/services/api.ts (modified)
- frontend/src/components/ExportModal.vue (modified)
- frontend/src/__tests__/api.test.ts (modified)
- frontend/src/components/ExportModal.test.ts (created)
