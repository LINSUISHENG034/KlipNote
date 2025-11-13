# Epic Technical Specification: Integrated Review & Export Experience

Date: 2025-11-07
Author: Link
Epic ID: 2
Status: Draft

---

## Overview

Epic 2 delivers KlipNote's differentiated user experience by implementing the integrated review interface with media playback, click-to-timestamp navigation, inline subtitle editing, and export capabilities. Building upon Epic 1's transcription foundation, this epic introduces the novel click-to-timestamp synchronization pattern that enables rapid verification workflow, allowing users to instantly jump to any moment in the recording by clicking a subtitle segment. The implementation includes a data flywheel foundation that captures both AI-generated and human-edited transcriptions during export, establishing the training data pipeline for continuous model improvement. Upon completion, users will have a complete MVP workflow: upload → transcribe → review with synchronized playback → edit corrections → export to SRT/TXT formats for LLM processing.

## Objectives and Scope

**In Scope:**
- Media playback API endpoint (GET /media/{job_id}) with HTTP Range request support for seeking
- Frontend HTML5 media player integration with automatic video/audio element selection
- Click-to-timestamp navigation with <1 second response time (NFR001)
- Bidirectional synchronization: subtitle list ↔ media player with active segment highlighting
- Inline subtitle editing with contenteditable fields and keyboard navigation (Tab/Enter/Escape)
- localStorage-based edit persistence with 500ms throttled auto-save (FR-020, NFR-003)
- Edit recovery on browser refresh and accidental navigation
- Export API endpoint (POST /export/{job_id}) generating SRT and TXT formats
- Data flywheel implementation: capture original + edited transcriptions with metadata
- Frontend export functionality with format selection and browser download trigger
- Touch device support for mobile/tablet click-to-timestamp interaction
- Complete MVP validation across target browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

**Out of Scope (Deferred Post-MVP):**
- Server-Sent Events (SSE) for real-time progress streaming (polling sufficient)
- Advanced crash recovery and offline mode support
- VTT export format (SRT and TXT sufficient for MVP)
- Edit analytics dashboard and quality metrics visualization
- Multi-job management UI with concurrent transcription display
- Composables architecture refactor (functional but not necessary for MVP)
- Speaker diarization and automatic speaker labeling
- AI-powered correction suggestions based on edit patterns

## System Architecture Alignment

This epic extends KlipNote's architecture by adding media serving capabilities to the backend and implementing the novel click-to-timestamp synchronization pattern in the frontend, as defined in architecture.md sections "Novel Architectural Patterns" and "HTTP Range Request Support".

**Backend Extensions:**
- Media serving endpoint (main.py) using FastAPI `FileResponse` with automatic HTTP Range request handling for smooth seeking
- Export service module (services/export_service.py) for SRT/TXT generation following subtitle format specifications
- Data flywheel storage pattern: separate files for original vs edited transcriptions at `/uploads/{job_id}/edited.json`
- Export API endpoint handling multipart requests with edited subtitle arrays

**Frontend Extensions:**
- MediaPlayer.vue component implementing HTML5 video/audio player with state synchronization
- Enhanced SubtitleList.vue with click handlers, active segment highlighting, and auto-scroll behavior
- Pinia store extensions: `currentTime` (commanded seek), `playbackTime` (actual position), `activeSegmentIndex`, `isPlaying`, `editingSegmentId`
- localStorage persistence layer with throttled auto-save (500ms) using `klipnote_edits_{job_id}` key pattern
- ExportButton.vue component triggering download via POST /export/{job_id}

**Architectural Patterns Maintained:**
- Click-to-timestamp synchronization: Bidirectional state flow through Pinia store with incremental segment search (O(1) for playback, O(n) for seeking)
- localStorage recovery: Auto-save on edit changes, restore on page load, clear after export (optional)
- API contracts: TypeScript interfaces match Pydantic models for type safety
- File naming: `transcript-{job_id}.{ext}` convention for downloaded exports
- Error handling: FastAPI HTTPException + TypeScript try/catch with user-friendly messages
- Performance optimizations: Throttled timeupdate events (250ms), incremental segment matching, smooth scroll behavior

**Components Referenced:**
- FastAPI FileResponse (built-in Range support)
- HTML5 media elements (native browser controls)
- Vue 3 Composition API with watch() for reactive state synchronization
- Pinia stores for cross-component state management
- localStorage API for browser-based persistence

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner/Location |
|----------------|----------------|--------|---------|----------------|
| **Media Serving Endpoint (main.py)** | Stream uploaded media files with HTTP Range support for seeking | job_id from URL path, Range headers | Media file with 206 Partial Content or 200 OK | backend/app/main.py GET /media/{job_id} |
| **Export Service** | Generate SRT and TXT files from subtitle segments | List of TranscriptionSegment, format choice | Formatted file content (bytes) | backend/app/services/export_service.py |
| **Export Endpoint (main.py)** | Handle export requests, trigger data flywheel storage | job_id, ExportRequest body | FileResponse download | backend/app/main.py POST /export/{job_id} |
| **MediaPlayer Component** | HTML5 video/audio player with state sync | mediaUrl, store state | Player DOM element, playback events | frontend/src/components/MediaPlayer.vue |
| **SubtitleList Component** | Subtitle display with click handlers, highlighting, editing | segments array, activeSegmentIndex | Click events, edit events | frontend/src/components/SubtitleList.vue (enhanced from Epic 1) |
| **ExportButton Component** | Export UI with format selection | job_id, segments array | Export API call trigger | frontend/src/components/ExportButton.vue |
| **Transcription Store Extensions** | State management for player sync and editing | User actions, API responses | Reactive state: currentTime, playbackTime, activeSegmentIndex, isPlaying, editingSegmentId | frontend/src/stores/transcription.ts (extends Epic 1) |
| **localStorage Persistence** | Auto-save edits, restore on load | segments array, job_id | Persisted edit state | Integrated in SubtitleList.vue and store watch() |
| **API Client Extensions** | Export API calls | job_id, ExportRequest | File download response | frontend/src/services/api.ts |

### Data Models and Contracts

**Backend Pydantic Models (app/models.py) - New for Epic 2:**

```python
from pydantic import BaseModel
from typing import Literal

class ExportRequest(BaseModel):
    """Request body for POST /export/{job_id} endpoint"""
    segments: list[TranscriptionSegment]  # Edited subtitle array
    format: Literal['srt', 'txt']         # Export format choice

class ExportMetadata(BaseModel):
    """Metadata stored with edited transcription for data flywheel"""
    job_id: str
    original_segment_count: int
    edited_segment_count: int
    export_timestamp: str     # ISO 8601 UTC
    format_requested: str     # 'srt' or 'txt'
    changes_detected: int     # Number of segments with text differences
```

**Frontend TypeScript Interfaces (src/types/api.ts) - New for Epic 2:**

```typescript
export interface ExportRequest {
  segments: Segment[]
  format: 'srt' | 'txt'
}

export interface LocalStorageEdit {
  job_id: string
  segments: Segment[]
  last_saved: string  // ISO 8601 timestamp
}

// Store state extensions
export interface TranscriptionState {
  // ... existing from Epic 1 (jobId, segments, status)
  currentTime: number           // Commanded seek position (seconds)
  playbackTime: number          // Actual player position (seconds)
  activeSegmentIndex: number    // Currently highlighted segment (-1 if none)
  isPlaying: boolean            // Player play/pause state
  editingSegmentId: number | null  // Track which segment is being edited
}
```

**File Storage Structure Extensions:**

```
/uploads/
  /{job_id}/
    original.{ext}           # Uploaded media file (from Epic 1)
    transcription.json       # WhisperX original output (from Epic 1)
    edited.json              # Human-edited version (NEW - Epic 2)
    export_metadata.json     # Export metadata for data flywheel (NEW - Epic 2)
```

**edited.json Structure:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "segments": [
    {"start": 0.5, "end": 3.2, "text": "User-edited text here"},
    {"start": 3.5, "end": 7.8, "text": "Another edited segment"}
  ],
  "metadata": {
    "original_segment_count": 45,
    "edited_segment_count": 45,
    "export_timestamp": "2025-11-07T14:30:00Z",
    "format_requested": "srt",
    "changes_detected": 7
  }
}
```

**localStorage Structure:**

```json
// Key: klipnote_edits_{job_id}
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "segments": [
    {"start": 0.5, "end": 3.2, "text": "Edited subtitle text"},
    {"start": 3.5, "end": 7.8, "text": "Another edited subtitle"}
  ],
  "last_saved": "2025-11-07T14:35:22Z"
}
```

**SRT Export Format:**

```
1
00:00:00,500 --> 00:00:03,200
Edited subtitle text

2
00:00:03,500 --> 00:00:07,800
Another edited subtitle

```

**TXT Export Format:**

```
Edited subtitle text Another edited subtitle
```
(Plain text, space-separated, no timestamps)

### APIs and Interfaces

**API Endpoint Specifications (Epic 2 Additions):**

| Method | Endpoint | Description | Request | Response | Error Codes |
|--------|----------|-------------|---------|----------|-------------|
| GET | `/media/{job_id}` | Stream uploaded media file with HTTP Range support | None (Range header optional) | Media file (video/audio) with Content-Type and Range headers | 404 (job not found), 416 (invalid range) |
| POST | `/export/{job_id}` | Export edited transcription in SRT or TXT format | `ExportRequest` JSON body | File download (SRT or TXT) | 404 (job not found), 400 (invalid format) |

**Detailed Endpoint Specifications:**

**GET /media/{job_id}**

```python
@app.get("/media/{job_id}")
async def serve_media(job_id: str, request: Request):
    """
    Stream media file with HTTP Range request support for seeking

    Automatically handles:
    - Range requests for partial content (206 Partial Content)
    - Full file serving (200 OK)
    - Correct Content-Type based on file extension
    - Content-Length and Accept-Ranges headers

    Validation:
    - job_id must exist in /uploads/{job_id}/
    - Media file (original.*) must be present

    Returns:
    - FileResponse with automatic Range support
    - Headers: Content-Type, Content-Length, Accept-Ranges: bytes
    - Status: 200 (full file) or 206 (partial content)

    Error Responses:
    - 404: Job ID not found or media file missing
    """
    file_path = f"/uploads/{job_id}/original.*"  # Glob to find extension
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Media file not found")

    return FileResponse(
        file_path,
        media_type=get_media_type(file_path),
        filename=os.path.basename(file_path)
    )
```

**Example Request:**

```bash
# Full file request
curl -X GET "http://localhost:8000/media/550e8400-e29b-41d4-a716-446655440000"

# Range request (seeking)
curl -X GET "http://localhost:8000/media/550e8400-e29b-41d4-a716-446655440000" \
     -H "Range: bytes=1024-2047"
```

**Example Response (Full File):**

```
HTTP/1.1 200 OK
Content-Type: audio/mpeg
Content-Length: 5242880
Accept-Ranges: bytes

[binary media data]
```

**Example Response (Range Request):**

```
HTTP/1.1 206 Partial Content
Content-Type: audio/mpeg
Content-Range: bytes 1024-2047/5242880
Content-Length: 1024
Accept-Ranges: bytes

[partial binary media data]
```

---

**POST /export/{job_id}**

```python
@app.post("/export/{job_id}")
async def export_transcription(job_id: str, request: ExportRequest):
    """
    Export edited transcription with data flywheel storage

    Process:
    1. Load original transcription from /uploads/{job_id}/transcription.json
    2. Compare with edited segments to detect changes
    3. Generate SRT or TXT file based on format parameter
    4. Store edited version to /uploads/{job_id}/edited.json (data flywheel)
    5. Store export metadata to /uploads/{job_id}/export_metadata.json
    6. Return generated file as download

    Validation:
    - job_id must exist
    - format must be 'srt' or 'txt'
    - segments array must not be empty

    Returns:
    - FileResponse with appropriate Content-Disposition header
    - Filename: transcript-{job_id}.{ext}

    Error Responses:
    - 404: Job ID not found
    - 400: Invalid format or empty segments
    """
    # Generate export file
    if request.format == 'srt':
        content = export_service.generate_srt(request.segments)
        media_type = "application/x-subrip"
        filename = f"transcript-{job_id}.srt"
    else:  # txt
        content = export_service.generate_txt(request.segments)
        media_type = "text/plain"
        filename = f"transcript-{job_id}.txt"

    # Data flywheel: store edited version
    save_edited_transcription(job_id, request.segments, request.format)

    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/export/550e8400-e29b-41d4-a716-446655440000" \
     -H "Content-Type: application/json" \
     -d '{
       "segments": [
         {"start": 0.5, "end": 3.2, "text": "Edited text"},
         {"start": 3.5, "end": 7.8, "text": "Another segment"}
       ],
       "format": "srt"
     }'
```

**Example Response (SRT):**

```
HTTP/1.1 200 OK
Content-Type: application/x-subrip
Content-Disposition: attachment; filename=transcript-550e8400-e29b-41d4-a716-446655440000.srt

1
00:00:00,500 --> 00:00:03,200
Edited text

2
00:00:03,500 --> 00:00:07,800
Another segment
```

**Frontend API Client Methods (src/services/api.ts):**

```typescript
export async function exportTranscription(
  jobId: string,
  segments: Segment[],
  format: 'srt' | 'txt'
): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/export/${jobId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ segments, format })
  })

  if (!response.ok) {
    throw new Error(`Export failed: ${response.statusText}`)
  }

  return response.blob()
}

export function getMediaUrl(jobId: string): string {
  return `${API_BASE_URL}/media/${jobId}`
}
```

### Workflows and Sequencing

**Workflow 1: Click-to-Timestamp Navigation**

```
User clicks subtitle segment (SubtitleList.vue)
  ↓
[Event Handler] handleClick(segment, index)
  ↓
[Check] if editingSegmentId !== null
  └─> [Warn] "Cannot seek while editing" → ABORT
  ↓
[Store Action] seekTo(segment.start)
  └─> Updates store.currentTime = segment.start
  ↓
[MediaPlayer.vue] watch(() => store.currentTime)
  ↓
[Validate] if |player.currentTime - newTime| > 0.5s
  ↓
[Seek] player.currentTime = newTime
  ↓
[Conditional Play] if store.isPlaying → player.play()
  ↓
[Player Event] @timeupdate fires (throttled 250ms)
  ↓
[Store Action] updatePlaybackTime(currentTime)
  ↓
[Incremental Search] updateActiveSegment(time)
  - Check current segment (fast path O(1))
  - Check next segment (playback fast path O(1))
  - Fallback: full search O(n)
  ↓
[Store Update] activeSegmentIndex = matched index
  ↓
[SubtitleList.vue] watch(() => store.activeSegmentIndex)
  ↓
[Auto-scroll] segmentRefs[newIndex].scrollIntoView({behavior: 'smooth', block: 'center'})
  ↓
[Visual] Segment highlighted via :class="{ active: index === activeSegmentIndex }"
```

**Performance Metrics:**
- Click to seek: <500ms (NFR001 requirement: <1s)
- Highlight update: ~250ms (throttled timeupdate interval)
- Auto-scroll: ~300ms (smooth behavior)

---

**Workflow 2: Inline Subtitle Editing**

```
User clicks subtitle text in SubtitleList.vue
  ↓
[Event Handler] enableEdit(segment, index)
  ↓
[Store Action] setEditingSegment(index)
  └─> Updates store.editingSegmentId = index
  ↓
[Component] Makes text contenteditable or shows input field
  ↓
[User Input] Types corrections in real-time
  ↓
[Store Update] segments[index].text = newText (reactive)
  ↓
[Watch] watch(() => state.segments, ..., { deep: true })
  ↓
[Throttled Save] throttledSave(jobId, segments) [500ms delay]
  ↓
[localStorage] setItem(`klipnote_edits_${jobId}`, JSON.stringify({...}))
  ↓
[User Action] Presses Tab/Enter or clicks outside
  ↓
[Event Handler] finishEdit()
  ↓
[Store Action] setEditingSegment(null)
  └─> Clears store.editingSegmentId
  ↓
[Optional] Move focus to next segment (Tab/Enter)
  ↓
[Visual] Edited segment marked with subtle indicator
```

**Edge Cases:**
- Escape key: Reverts to original text, calls setEditingSegment(null)
- Click subtitle during edit: Blocked by editingSegmentId check
- Page refresh during edit: localStorage restored on next load

---

**Workflow 3: localStorage Recovery on Page Load**

```
User navigates to EditorView.vue (with job_id param)
  ↓
[Component] onMounted() lifecycle hook
  ↓
[Check localStorage] key = `klipnote_edits_${job_id}`
  ↓
[Conditional Branch]
  ├─> [If exists] Load saved edits
  │     ↓
  │   [Parse JSON] const saved = JSON.parse(localStorage.getItem(key))
  │     ↓
  │   [Validate] Check segments array structure
  │     ↓
  │   [Store Update] store.segments = saved.segments
  │     ↓
  │   [UI Feedback] "Restored unsaved edits from [timestamp]"
  │     ↓
  │   [Priority] localStorage overrides API result (user work preserved)
  │
  └─> [If not exists] Fetch from API
        ↓
      [API Call] await api.fetchTranscriptionResult(job_id)
        ↓
      [Store Update] store.segments = result.segments
```

**Error Handling:**
- localStorage full: Catch QuotaExceededError, warn user
- Corrupted JSON: Catch parse error, fall back to API
- Stale data: Display last_saved timestamp for user decision

---

**Workflow 4: Export with Data Flywheel**

```
User clicks Export button (ExportButton.vue)
  ↓
[UI] Shows format selection (SRT or TXT radio buttons)
  ↓
[User] Selects format and confirms
  ↓
[Component] handleExport(format)
  ↓
[Store] Retrieves current segments (edited version)
  ↓
[API Call] exportTranscription(job_id, segments, format)
  ↓
[Frontend] POST /export/{job_id} with ExportRequest body
  ↓
[Backend] export_transcription(job_id, request)
  ↓
[Load Original] Read /uploads/{job_id}/transcription.json
  ↓
[Compare] Diff original vs edited segments
  ├─> Count changes_detected
  └─> Identify modified text fields
  ↓
[Generate Export]
  ├─> [SRT] export_service.generate_srt(segments)
  └─> [TXT] export_service.generate_txt(segments)
  ↓
[Data Flywheel Storage]
  ├─> Save edited.json with segments + metadata
  └─> Save export_metadata.json with comparison stats
  ↓
[Response] Return file with Content-Disposition header
  ↓
[Frontend] Receives Blob response
  ↓
[Browser Download] Trigger download via:
  - Create blob URL
  - Create temporary <a> element
  - Set href to blob URL, download attribute to filename
  - Click programmatically
  - Revoke blob URL
  ↓
[Optional] Clear localStorage after successful export
  └─> localStorage.removeItem(`klipnote_edits_${job_id}`)
  ↓
[UI Feedback] "Export successful: transcript-{job_id}.{ext}"
```

**Data Flywheel Captured:**
- Original AI transcription (transcription.json)
- Human-edited version (edited.json)
- Comparison metadata (changes count, timestamp)
- Format preference (SRT vs TXT usage patterns)

**Future Use:**
- Training data for model fine-tuning
- Quality metrics (edit frequency per segment)
- User correction patterns (common misrecognitions)
- Language model improvement validation

## Non-Functional Requirements

### Performance

**NFR001 Performance Targets (Epic 2 Scope):**

| Metric | Target | Implementation Strategy | Validation Method |
|--------|--------|------------------------|-------------------|
| Media playback start | <2 seconds | FastAPI FileResponse with HTTP Range support, browser-native HTML5 player | Manual testing with network throttling |
| Timestamp seeking | <1 second | Throttled timeupdate (250ms), incremental segment search O(1) | Click-to-timestamp response time measurement |
| Subtitle highlighting latency | ~250ms | Throttled playback position updates, reactive Vue watch() | Visual observation during playback |
| Edit auto-save delay | 500ms | Throttled localStorage writes using lodash-es throttle() | Monitor localStorage update frequency |
| Export generation | <3 seconds | In-memory SRT/TXT generation, async file I/O | Backend timing logs |
| localStorage restoration | <500ms | Synchronous JSON.parse on page load | Performance.now() measurement |

**Performance Optimizations Implemented:**

1. **Incremental Segment Search:** O(1) complexity for normal playback by checking current/next segments before full search
2. **Throttled timeupdate Events:** Limit store updates to 4x/second (250ms) instead of 60fps
3. **HTTP Range Requests:** FastAPI FileResponse built-in support enables smooth seeking without loading entire media file
4. **localStorage Throttling:** 500ms delay prevents excessive writes during rapid editing
5. **Smooth Scroll Behavior:** CSS-accelerated scrollIntoView() for auto-scroll without layout thrashing
6. **Blob URL for Downloads:** Browser-native download mechanism for export files

**Performance Constraints:**

- **Media File Size:** Seeking performance degrades for files >500MB on slow networks (mitigated by Range requests)
- **localStorage Limits:** 5-10MB browser limit (1 hour transcription ≈ 100KB, sufficient for MVP)
- **Subtitle Count:** >1000 segments may cause slight lag in full search fallback (rare for 2-hour limit)

**Monitoring:**

- Browser DevTools Performance tab for React/Vue rendering bottlenecks
- Network tab for Range request validation and response times
- Console timing logs for export generation duration

### Security

**NFR002 Security Requirements (Epic 2 Scope):**

**File Access Control:**
- Media serving endpoint validates job_id exists before serving files (prevents directory traversal)
- File paths constructed using os.path.join() with sanitized job_id (UUID v4 format validation)
- No user-supplied path components in file access operations
- 404 errors for non-existent job_id (no information disclosure)

**Data Privacy - Data Flywheel:**
- Export endpoint stores both original and edited transcriptions for model training (FR016)
- Privacy notice requirement: Users must be informed during export flow (Story 2.5 AC8)
- Stored data: segments only, no user PII captured
- File permissions: Backend-only access, not exposed via API endpoints
- Future consideration: Opt-out mechanism for data collection (post-MVP)

**localStorage Security:**
- Client-side storage only (no sensitive data, no authentication tokens)
- Data scope: Edited subtitle text (non-sensitive transcription content)
- Same-origin policy enforced by browser (data isolated per domain)
- No cross-site scripting risk (segments rendered with Vue's default text interpolation, not v-html)

**CORS Configuration (from Epic 1, maintained):**
- Development: Allow localhost:5173 (frontend) → localhost:8000 (backend)
- Production: Restrict to production frontend domain
- Credentials allowed for future session management
- All HTTP methods allowed (GET, POST for MVP scope)

**Input Validation:**
- Export endpoint validates format parameter: Literal['srt', 'txt'] (Pydantic)
- Segments array validation: Non-empty, valid TranscriptionSegment structure
- job_id validation: UUID v4 format (36 characters, standard format)

**Content-Type Handling:**
- Media endpoint sets correct Content-Type based on file extension (prevents MIME confusion)
- Export responses use application/x-subrip (SRT) or text/plain (TXT)
- Content-Disposition: attachment prevents browser execution

**Threats Mitigated:**
- ✅ Directory traversal (job_id validation, no user paths)
- ✅ XSS (Vue default text rendering, no v-html)
- ✅ MIME confusion (explicit Content-Type headers)
- ✅ Unauthorized file access (job_id-based isolation)

**Threats Deferred (Post-MVP):**
- Authentication/Authorization (ephemeral design, no login)
- Rate limiting (single-user deployment assumption)
- HTTPS enforcement (deployment concern, not application)
- CSRF protection (no sessions/cookies in MVP)

### Reliability/Availability

**NFR003 Reliability Requirements (Epic 2 Scope):**

**Browser-Based Edit Persistence:**
- localStorage auto-save with 500ms throttling prevents data loss from:
  - Browser refresh (intentional or accidental)
  - Back button navigation (accidental)
  - Tab close warning (browser default behavior)
- Recovery mechanism: Automatic restoration on EditorView.vue mount
- Data priority: localStorage overrides API result (user work preserved)
- Success criteria: 0% data loss for "normal operation" scenarios (FR-020, NFR-003)

**localStorage Failure Handling:**
- QuotaExceededError: Catch, warn user, continue without auto-save
- Corrupted JSON: Catch parse error, log warning, fall back to API
- Missing localStorage: Graceful degradation, warn about reduced reliability

**Media Playback Reliability:**
- HTML5 player handles corrupted files gracefully (native error events)
- Range request failures: Fall back to full file download (browser behavior)
- Unsupported formats: Clear error message, no crash
- Network interruptions: Player shows buffering, retries automatically

**Export Process Reliability:**
- Validation before generation: Check segments array not empty
- File I/O errors: Catch, return 500 with clear error message
- Large exports (>1000 segments): No memory issues (streaming approach)
- Concurrent exports: No file locking issues (job_id-based isolation)

**Error Recovery Strategies:**

| Failure Scenario | Detection | Recovery | User Impact |
|-----------------|-----------|----------|-------------|
| localStorage full | QuotaExceededError | Warn user, disable auto-save | Manual export reminder |
| Media file missing | 404 on /media/{job_id} | Show error message | Cannot review audio |
| Export generation fails | Exception in export_service | Return 500, log error | Retry button |
| Browser refresh during edit | Page unload | localStorage auto-restore | Seamless resume |
| Network timeout on export | Fetch timeout | Show error, retry button | Manual retry |

**Data Durability (Data Flywheel):**
- Original transcription: Persisted in /uploads/{job_id}/transcription.json (from Epic 1)
- Edited transcription: Persisted in /uploads/{job_id}/edited.json on export
- Export metadata: Persisted in /uploads/{job_id}/export_metadata.json
- No data loss once export completes (file system durability)

**Availability Targets:**
- Service uptime: Not applicable (single-user self-hosted)
- Media serving: Synchronous, no queuing (immediate availability)
- Export generation: <3 seconds, synchronous response
- localStorage writes: Fire-and-forget with error handling

**Degraded Operation Modes:**
- localStorage unavailable: Edit functionality works, no auto-save (warn user)
- Range requests unsupported: Full file download (slow seeking, but functional)
- Browser too old: Feature detection, graceful degradation messages

### Observability

**Logging Requirements (Epic 2 Scope):**

**Backend Logging (Python logging module):**

```python
import logging

logger = logging.getLogger(__name__)

# Media serving logs
logger.info(f"Serving media file for job {job_id}, file: {filename}")
logger.warning(f"Range request for job {job_id}: bytes={start}-{end}")
logger.error(f"Media file not found for job {job_id}", exc_info=True)

# Export generation logs
logger.info(f"Export requested: job={job_id}, format={format}, segments={len(segments)}")
logger.info(f"Data flywheel: Detected {changes_count} edited segments for job {job_id}")
logger.info(f"Export generated: {filename} ({file_size_bytes} bytes) in {duration_ms}ms")
logger.error(f"Export failed for job {job_id}: {error_message}", exc_info=True)
```

**Log Levels:**
- **INFO:** Media serving, export requests, data flywheel operations, successful completions
- **WARNING:** Range request headers (for debugging seeking issues), fallback behaviors
- **ERROR:** File not found, export generation failures, I/O errors, validation errors

**Frontend Logging (Console):**

```typescript
// Development only (stripped in production build)
console.log(`[MediaPlayer] Seeking to ${timestamp}s`)
console.log(`[SubtitleList] Active segment: ${activeSegmentIndex}`)
console.log(`[localStorage] Saved edits: ${segments.length} segments`)
console.error(`[Export] Failed:`, error)

// Production: Errors only
console.error(`Export failed: ${error.message}`)
```

**Metrics to Track:**

| Metric | Signal | Collection Method | Purpose |
|--------|--------|------------------|---------|
| Media file requests | INFO logs: "Serving media file..." | Backend logger | Track media access patterns |
| Range request usage | WARNING logs: "Range request..." | Backend logger | Validate seeking optimization |
| Export format preference | INFO logs: "Export requested: format=..." | Backend logger | Data flywheel analytics |
| Edit frequency | Data flywheel: changes_detected count | export_metadata.json | Model training insights |
| Export duration | INFO logs: "Export generated... in Xms" | Backend logger | Performance monitoring |
| localStorage failures | ERROR logs in browser console | Frontend catch blocks | Reliability monitoring |

**Operational Visibility:**

**Story 2.1 (Media API):**
- Log all media serving requests with job_id and filename
- Log Range request details for seeking debugging
- Log 404 errors with job_id for troubleshooting

**Story 2.5 (Export API):**
- Log export requests with format, segment count, job_id
- Log data flywheel captures: changes detected, metadata stored
- Log export generation duration for performance tracking
- Log comparison results: original vs edited segment counts

**Story 2.4 (localStorage):**
- Console log localStorage saves (development only)
- Console error for QuotaExceededError with guidance
- Console warn for corrupted JSON with fallback notice

**Debugging Aids:**

**Click-to-Timestamp Issues:**
```typescript
// Store action logging
console.log(`[Store] seekTo(${time}) - currentTime updated`)
console.log(`[Store] updateActiveSegment(${time}) - index=${newIndex}`)
```

**Export Problems:**
```python
# Detailed export logging
logger.debug(f"Original segments: {len(original_segments)}")
logger.debug(f"Edited segments: {len(edited_segments)}")
logger.debug(f"Changes detected: {changes}")
logger.info(f"Generated SRT: {len(srt_content)} characters")
```

**Performance Tracking:**
```python
import time

start = time.time()
content = export_service.generate_srt(segments)
duration_ms = (time.time() - start) * 1000
logger.info(f"SRT generation: {duration_ms:.2f}ms")
```

**No External Monitoring (MVP):**
- No Sentry/error tracking service
- No APM (Application Performance Monitoring)
- No centralized logging (stdout only)
- Post-MVP: Consider adding structured logging (JSON format) for log aggregation

## Dependencies and Integrations

**Backend Dependencies (New for Epic 2 - additions to requirements.txt):**

| Package | Version | Purpose | Stories Using |
|---------|---------|---------|---------------|
| python-magic | latest | MIME type detection for media files | Story 2.1 |
| aiofiles | latest | Async file I/O for export generation | Story 2.5 |

**Frontend Dependencies (New for Epic 2 - additions to package.json):**

| Package | Version | Purpose | Stories Using |
|---------|---------|---------|---------------|
| lodash-es | ^4.17.21 | Throttle utility for timeupdate events and localStorage saves | Stories 2.2, 2.3, 2.4 |

**Existing Dependencies Leveraged from Epic 1:**

**Backend:**
- FastAPI: FileResponse for media serving with Range support (Story 2.1)
- Pydantic: ExportRequest model validation (Story 2.5)
- Redis: Not used in Epic 2 (data persistence via file system)
- Python built-in modules: os, glob, datetime, json

**Frontend:**
- Vue 3: watch() for reactive state synchronization (Stories 2.2, 2.3, 2.4)
- Pinia: Store extensions for player state management (Stories 2.2, 2.3, 2.4)
- TypeScript: Type safety for new API contracts (Stories 2.1, 2.5)
- Vue Router: Already configured in Epic 1, no changes needed
- Native fetch API: Export API calls (Story 2.6)

**Browser APIs:**
- HTML5 video/audio elements: Native media playback (Story 2.2)
- localStorage API: Browser-based edit persistence (Story 2.4)
- Blob API: Export file download mechanism (Story 2.6)
- scrollIntoView API: Subtitle auto-scroll (Story 2.3)

**External Integrations:**
- None (Epic 2 is entirely self-contained)

**Integration Points Between Components:**

**MediaPlayer ↔ Pinia Store:**
- Input: `store.currentTime` (commanded seek position)
- Output: `store.playbackTime` (actual position via @timeupdate event)
- Output: `store.isPlaying` (play/pause state via @play, @pause events)

**SubtitleList ↔ Pinia Store:**
- Input: `store.segments` (subtitle array for rendering)
- Input: `store.activeSegmentIndex` (highlight active segment)
- Input: `store.editingSegmentId` (track editing mode)
- Output: Click events trigger `store.seekTo(time)`
- Output: Edit events update `store.segments[index].text`

**localStorage ↔ Pinia Store:**
- Input: `store.segments` (auto-save on changes via watch())
- Output: Restored segments on page load (override API)
- Key: `klipnote_edits_{job_id}`

**ExportButton ↔ Backend API:**
- POST /export/{job_id} with ExportRequest body
- Response: Blob file download (SRT or TXT)

**Dependency Management Commands:**

```bash
# Backend - Add new dependencies
cd backend
source .venv/Scripts/activate  # Windows Git Bash
uv pip install python-magic aiofiles
uv pip freeze > requirements.txt

# Frontend - Add lodash-es
cd frontend
npm install lodash-es
npm install --save-dev @types/lodash-es  # TypeScript types
```

**Docker Compose Changes:**
- No changes required (existing services sufficient)
- Volumes already mount /uploads directory (Epic 1)
- No new services needed for Epic 2

**Configuration Updates:**

```python
# backend/app/config.py - Add media serving config
class Settings(BaseSettings):
    # ... existing from Epic 1

    # Media Serving (Epic 2)
    MEDIA_CHUNK_SIZE: int = 1024 * 1024  # 1MB chunks for streaming
    ALLOWED_MEDIA_TYPES: list[str] = [
        "audio/mpeg",       # MP3
        "audio/mp4",        # M4A
        "audio/wav",        # WAV
        "video/mp4"         # MP4
    ]
```

**External File Dependencies:**

| File | Purpose | Source | Epic 2 Usage |
|------|---------|--------|--------------|
| /uploads/{job_id}/original.* | Media playback source | Epic 1 (user upload) | Story 2.1 (served via GET /media) |
| /uploads/{job_id}/transcription.json | Original AI transcription | Epic 1 (WhisperX output) | Story 2.5 (comparison for data flywheel) |
| /uploads/{job_id}/edited.json | Human-edited transcription | Epic 2 (export storage) | Story 2.5 (data flywheel output) |
| /uploads/{job_id}/export_metadata.json | Export metadata | Epic 2 (export storage) | Story 2.5 (data flywheel analytics) |

## Acceptance Criteria (Authoritative)

**Epic-Level Success Criteria:**

1. ✓ Complete integrated review and editing interface operational
2. ✓ Click-to-timestamp navigation delivering <1 second response time (NFR001)
3. ✓ localStorage-based edit persistence preventing data loss on browser refresh (FR-020, NFR-003)
4. ✓ Export functionality generating SRT and TXT formats with data flywheel capture
5. ✓ All 7 stories (2.1-2.7) completed with acceptance criteria met
6. ✓ End-to-end workflow validated: Upload → Transcribe → Review → Edit → Export

**Story-Level Acceptance Criteria:**

**Story 2.1: Media Playback API Endpoint**
1. GET /media/{job_id} endpoint serves uploaded media file
2. Endpoint supports HTTP Range requests for seeking
3. Returns correct Content-Type header based on file format
4. Returns 404 for non-existent job_id
5. Handles partial content requests (206 status code)
6. Works with HTML5 video/audio elements in all target browsers
7. API endpoint documented in FastAPI auto-docs

**Story 2.2: Frontend Media Player Integration**
1. Integrated HTML5 video/audio player displayed above subtitle list
2. Player automatically selects correct element (video/audio) based on media type
3. Standard controls visible: play, pause, seek bar, volume, current time
4. Player loads media from GET /media/{job_id} endpoint
5. On load: Check localStorage for existing edits (key: `klipnote_edits_{job_id}`) and restore if present
6. Seeking works smoothly (Range request support validated)
7. Responsive layout: player scales appropriately on mobile/tablet
8. Player state persists during subtitle editing (doesn't reload unnecessarily)

**Story 2.3: Click-to-Timestamp Navigation**
1. Clicking any subtitle segment seeks media player to that segment's start time
2. Player automatically starts playing after seek
3. Currently playing segment is visually highlighted
4. Highlight updates automatically as playback progresses
5. Click response time <1 second (per NFR001)
6. Works on touch devices (tap interaction)
7. Visual feedback on hover/touch to indicate clickability

**Story 2.4: Inline Subtitle Editing**
1. Clicking subtitle text makes it editable (contenteditable or input field)
2. Changes update immediately in component state
3. Tab/Enter key saves edit and moves to next subtitle
4. Escape key cancels edit and reverts changes
5. Edited subtitles visually distinguished from unedited (subtle indicator)
6. Multiple subtitles can be edited in succession
7. Edits persist in localStorage (key: `klipnote_edits_{job_id}`) - auto-saved with throttling (500ms)
8. localStorage prevents data loss from browser refresh or accidental navigation (satisfies FR-020 & NFR-003)

**Story 2.5: Export API Endpoint with Data Flywheel**
1. POST /export/{job_id} endpoint accepts edited subtitle array in request body
2. Generates SRT file format from edited subtitles
3. Generates TXT file format (plain text, no timestamps) from edited subtitles
4. Stores both original transcription and edited version on server with job_id reference
5. Stores metadata: edit timestamp, number of changes, export format requested
6. Returns exported files for download (multipart response or separate endpoints)
7. API endpoint documented in FastAPI auto-docs
8. Privacy notice: Inform users that edited transcriptions may be retained for model improvement

**Story 2.6: Frontend Export Functionality**
1. Export button visible on editor page
2. Format selection: SRT or TXT (radio buttons or dropdown)
3. Export button calls POST /export/{job_id} with edited subtitle array
4. Success: Browser downloads file with appropriate name (job_id-transcript.srt/.txt)
5. Loading state during export processing
6. Error handling if export fails with clear message
7. Multiple exports allowed (user can export both formats sequentially)

**Story 2.7: MVP Release Checklist & Final Validation**
1. Complete workflow tested: Upload → Progress → View → Edit → Export on 5+ different media files
2. Cross-browser testing completed: Chrome, Firefox, Safari (desktop + mobile)
3. Error handling verified for all failure scenarios (upload fail, transcription fail, network errors)
4. Performance validated: meets NFR001 targets (load <3s, playback <2s, seek <1s)
5. Mobile responsiveness verified on tablet and phone devices
6. Basic documentation updated: README with user instructions and developer setup
7. No critical bugs blocking MVP release
8. Error scenario testing: file size exceeded (>2GB), network timeout, WhisperX model download failure, concurrent job limits, corrupted media files
9. Safari-specific media seeking behavior tested (Safari playback controls may differ from Chrome/Firefox)

## Traceability Mapping

| AC ID | Acceptance Criterion | Spec Section(s) | Component(s)/API(s) | Test Idea |
|-------|---------------------|-----------------|---------------------|-----------|
| **Story 2.1** ||||
| 2.1.1 | GET /media serves media file | APIs, Data Models | GET /media/{job_id}, FileResponse | Test with test audio file, verify response |
| 2.1.2 | HTTP Range support | APIs, Performance | FileResponse Range handling | Send Range header, verify 206 response |
| 2.1.3 | Correct Content-Type | APIs, Services | MIME type detection | Test MP3/MP4/WAV, verify headers |
| 2.1.4 | 404 for non-existent job | APIs, Reliability | Error handling | Test random UUID, verify 404 response |
| 2.1.5 | Partial content requests | APIs, Performance | HTTP 206 status | Test seek in browser, verify Range requests |
| 2.1.6 | Works with HTML5 elements | APIs, Services | HTML5 video/audio | Load in MediaPlayer, verify playback |
| 2.1.7 | Documented in /docs | APIs | FastAPI auto-docs | Navigate to /docs, verify endpoint |
| **Story 2.2** ||||
| 2.2.1 | Player displayed above subtitles | Services, Detailed Design | MediaPlayer.vue, EditorView.vue | Component test: verify rendering |
| 2.2.2 | Auto-selects video/audio element | Services | MediaPlayer.vue | Test with MP3 (audio) and MP4 (video) |
| 2.2.3 | Standard controls visible | Services | HTML5 native controls | Visual test: verify controls present |
| 2.2.4 | Loads from /media endpoint | APIs, Services | MediaPlayer.vue, api.ts | Mock API, verify src attribute |
| 2.2.5 | Checks localStorage on load | Workflows, Services | localStorage recovery | Test with saved edits, verify restoration |
| 2.2.6 | Seeking works smoothly | Performance, APIs | Range requests, MediaPlayer | Manual test: seek multiple times |
| 2.2.7 | Responsive layout | Performance, Services | CSS media queries | Test on mobile/tablet viewports |
| 2.2.8 | Player state persists | Reliability, Services | MediaPlayer.vue | Edit subtitle, verify no reload |
| **Story 2.3** ||||
| 2.3.1 | Click seeks to segment start | Workflows, Services | SubtitleList click handler, store.seekTo() | Click segment, verify currentTime updated |
| 2.3.2 | Auto-play after seek | Workflows | MediaPlayer watch currentTime | Click segment while paused, verify playback |
| 2.3.3 | Active segment highlighted | Workflows, Services | SubtitleList.vue :class binding | Visual test during playback |
| 2.3.4 | Highlight updates with playback | Workflows, Performance | updateActiveSegment() incremental search | Play audio, verify highlight moves |
| 2.3.5 | Response time <1 second | Performance, NFR001 | Throttled updates, seek logic | Performance.now() measurement |
| 2.3.6 | Touch device support | Services | Touch event handlers | Test on tablet, verify tap works |
| 2.3.7 | Visual feedback on hover | Services | CSS hover states | Hover segment, verify cursor/style change |
| **Story 2.4** ||||
| 2.4.1 | Click makes editable | Services | SubtitleList enableEdit() | Click text, verify contenteditable |
| 2.4.2 | Changes update immediately | Services, Data Models | Pinia store segments array | Type text, verify store updated |
| 2.4.3 | Tab/Enter saves and moves | Services | Keyboard event handlers | Press Tab, verify move to next |
| 2.4.4 | Escape reverts changes | Services | Escape handler | Edit text, press Escape, verify reverted |
| 2.4.5 | Edited visually distinguished | Services | CSS class for edited | Edit segment, verify indicator displayed |
| 2.4.6 | Multiple edits in succession | Services | setEditingSegment() logic | Edit 3 segments, verify all work |
| 2.4.7 | Persist to localStorage | Workflows, Data Models | throttled localStorage writes | Edit, wait 500ms, verify localStorage |
| 2.4.8 | Prevents data loss on refresh | Reliability, NFR003 | localStorage recovery | Refresh during edit, verify restored |
| **Story 2.5** ||||
| 2.5.1 | POST /export accepts segments | APIs, Data Models | POST /export/{job_id}, ExportRequest | Test with segment array, verify accepted |
| 2.5.2 | Generates SRT format | APIs, Services | export_service.generate_srt() | Export SRT, validate format |
| 2.5.3 | Generates TXT format | APIs, Services | export_service.generate_txt() | Export TXT, validate plain text |
| 2.5.4 | Stores original + edited | Workflows, Data Flywheel | /uploads/{job_id}/edited.json | Export, verify both files present |
| 2.5.5 | Stores metadata | Data Models, Data Flywheel | export_metadata.json | Export, verify metadata fields |
| 2.5.6 | Returns file for download | APIs | FileResponse with Content-Disposition | Test download triggered in browser |
| 2.5.7 | Documented in /docs | APIs | FastAPI auto-docs | Navigate to /docs, verify endpoint |
| 2.5.8 | Privacy notice | Security, NFR002 | UI notice in ExportButton | Verify notice displayed before export |
| **Story 2.6** ||||
| 2.6.1 | Export button visible | Services | ExportButton.vue | Component test: verify rendered |
| 2.6.2 | Format selection UI | Services | Radio buttons or dropdown | Visual test: select SRT/TXT |
| 2.6.3 | Calls POST /export | APIs, Services | api.exportTranscription() | Mock API, verify request sent |
| 2.6.4 | Browser downloads file | Services | Blob download mechanism | Export, verify file in Downloads |
| 2.6.5 | Loading state during export | Services, Reliability | isExporting reactive variable | Click export, verify loading indicator |
| 2.6.6 | Error handling with message | Reliability | Try/catch, error display | Mock 500 error, verify message shown |
| 2.6.7 | Multiple exports allowed | Services | No state blocking | Export SRT, then TXT, verify both work |
| **Story 2.7** ||||
| 2.7.1 | Complete workflow tested | All | End-to-end integration | Playwright E2E test suite |
| 2.7.2 | Cross-browser testing | Performance, NFR004 | All components | Manual tests: Chrome, Firefox, Safari |
| 2.7.3 | Error scenarios verified | Reliability, NFR003 | Error handling logic | Test all error paths systematically |
| 2.7.4 | Performance targets met | Performance, NFR001 | All performance optimizations | Measure: load, playback, seek times |
| 2.7.5 | Mobile responsiveness | Performance, NFR004 | Responsive CSS | Test on real devices: tablet, phone |
| 2.7.6 | Documentation updated | N/A | README.md | Manual review of instructions |
| 2.7.7 | No critical bugs | All | Bug tracking | Final QA pass, regression tests |
| 2.7.8 | Error scenario testing | Reliability | Error handling | Test network errors, file errors, etc. |
| 2.7.9 | Safari-specific behavior | Performance, NFR004 | Safari playback | Manual test on Safari desktop/iOS |

## Risks, Assumptions, Open Questions

**Risks:**

| ID | Risk | Impact | Likelihood | Mitigation Strategy |
|----|------|--------|------------|---------------------|
| R1 | Safari media seeking behavior differs from Chrome/Firefox | Medium | Medium | Story 2.7 AC9 mandates Safari-specific testing. Document known limitations if found. Test on both Safari desktop (macOS) and Safari mobile (iOS). Fallback: disable seek optimization for Safari if needed. |
| R2 | localStorage quota exceeded on long transcriptions | Medium | Low | Implement QuotaExceededError handling in Story 2.4. Warn user and disable auto-save. 1-hour transcription ≈ 100KB (well under 5-10MB limit), but multiple tabs may accumulate data. |
| R3 | Media player performance degrades with large files (>500MB) on slow networks | Medium | Medium | HTTP Range requests (Story 2.1) mitigate by loading chunks. Test with network throttling in Story 2.7. Accept risk for MVP (2GB limit implies some large files). Future: Add file size warning in UI. |
| R4 | Click-to-timestamp accuracy issues with WhisperX timestamp alignment | High | Low | WhisperX provides word-level timestamps (proven accuracy). Test with various audio quality levels in Story 2.3. If issues found, implement ±0.5s seek buffer. |
| R5 | localStorage conflicts across multiple browser tabs | Low | Medium | Accept risk for MVP (single-user workflow assumption). "Last write wins" behavior is acceptable. Future: Add tab synchronization via storage events. |
| R6 | Export generation slow for very long transcriptions (>1000 segments) | Low | Low | SRT/TXT generation is in-memory string manipulation (fast). Test with 1000+ segments in Story 2.5. If slow, implement streaming generation. Current synchronous approach acceptable for 2-hour transcription limit (~200-400 segments). |
| R7 | SRT format compatibility issues with specific subtitle players | Medium | Medium | Follow standard SRT specification (Story 2.5). Test with VLC, browser subtitle loaders, and common video editors in Story 2.7. Document any known compatibility issues. |

**Assumptions:**

| ID | Assumption | Validation Strategy |
|----|------------|---------------------|
| A1 | Users primarily work on one transcription at a time (single-tab workflow) | Confirmed in PRD user journey. localStorage conflicts across tabs deferred to post-MVP. |
| A2 | Browser localStorage available and not disabled by user/policy | Feature detection in Story 2.4. Graceful degradation if unavailable (warn user about no auto-save). |
| A3 | HTML5 video/audio elements support all uploaded media formats | Epic 1 validates formats at upload (MP3, MP4, WAV, M4A). Browsers support these natively. Test in Story 2.2. |
| A4 | Users accept "ephemeral" design - no server-side session persistence | Confirmed in PRD and architecture. localStorage sufficient for MVP. Data persists only during editing session. |
| A5 | Editing frequency low (users edit <20% of segments on average) | Based on WhisperX accuracy expectations. Validate via data flywheel analytics post-launch (Story 2.5 metadata). |
| A6 | Export files downloaded immediately (not queued for async generation) | Confirmed in architecture. SRT/TXT generation fast enough for synchronous response (<3 seconds target). |
| A7 | Users understand privacy notice about data collection for model training | Story 2.5 AC8 requires notice. Assume users in corporate deployment accept this. Future: Add opt-out mechanism. |

**Open Questions:**

| ID | Question | Resolution Approach | Blocked Story |
|----|----------|---------------------|---------------|
| Q1 | Should localStorage edits be cleared after successful export, or persist indefinitely? | Decision: Keep persistence (don't clear). Allows users to re-download in different formats. Future: Add "Clear edits" button. | None (implement persistence by default) |
| Q2 | What visual indicator should distinguish edited vs unedited subtitles? | Design decision in Story 2.4 implementation: Subtle colored dot or border accent. Avoid distracting users during playback. | None (design during Story 2.4) |
| Q3 | Should clicking subtitle during active editing be blocked or just warn? | Decision made in architecture: Block seek, log console warning. Prevents confusion from sudden time jumps mid-edit. | None (documented in Workflows) |
| Q4 | How to handle user clicking "Export" without making any edits (no changes detected)? | Allow export anyway (user may want original in SRT/TXT format). Data flywheel captures "0 changes" in metadata. | None |
| Q5 | Should media player auto-play on page load, or wait for user click? | UX decision in Story 2.2: Do NOT auto-play (browsers block auto-play anyway). User initiates playback via controls or click-to-timestamp. | None |
| Q6 | What happens if user uploads new file while localStorage contains edits from previous job_id? | No conflict - job_id-specific keys (`klipnote_edits_{job_id}`). Each transcription isolated. Old edits persist until manually cleared (browser storage management). | None |

**Dependencies on Epic 1:**

- ✅ Upload functionality operational (Story 1.2)
- ✅ Transcription workflow complete (Story 1.3)
- ✅ Status and result APIs functional (Story 1.4)
- ✅ Frontend displays transcription results (Story 1.7)
- ✅ File storage structure established (/uploads/{job_id}/)
- ✅ Pinia store initialized (transcription.ts)

**Known Limitations (Accepted for MVP):**

- No server-side edit history or undo/redo (localStorage-only persistence)
- No collaborative editing (single-user design)
- No real-time sync across browser tabs (localStorage conflicts possible)
- No edit analytics dashboard (data flywheel captures data, no visualization)
- No automated correction suggestions (future AI feature)
- No speaker diarization in UI (WhisperX supports it, but deferred to post-MVP)

**Post-MVP Enhancements Enabled by Epic 2:**

- Fine-tuning WhisperX model using captured edit data (data flywheel)
- Edit frequency heatmaps (identify commonly corrected segments)
- User correction pattern analysis (improve model on specific error types)
- Quality metrics dashboard (WER reduction over time)
- Automated suggestion system ("Did you mean...?" based on edit history)

## Test Strategy Summary

**Testing Framework Setup (Leverages Epic 1):**

- **Backend:** pytest + pytest-mock (already configured)
- **Frontend:** Vitest + @vue/test-utils (already configured)
- **E2E:** Playwright for end-to-end workflow tests (Story 2.7)
- **Browser Testing:** BrowserStack or manual testing for cross-browser validation

**Test Coverage Targets (Epic 2):**

- Backend API endpoints (media, export): 70%+ code coverage
- Backend export service: 80%+ code coverage (critical for data flywheel)
- Frontend components (MediaPlayer, enhanced SubtitleList, ExportButton): 70%+ coverage
- Click-to-timestamp pattern: 80%+ coverage (novel architecture feature)
- localStorage persistence: 80%+ coverage (critical for NFR-003)
- E2E critical paths: 100% (review → edit → export workflow)

**Test Levels and Scope:**

**1. Unit Tests**

**Backend (pytest):**

```python
# tests/test_api_media.py (Story 2.1)
def test_serve_media_success(client):
    """Test media file serving with correct Content-Type"""
    response = client.get('/media/test-job-123')
    assert response.status_code == 200
    assert 'audio/mpeg' in response.headers['Content-Type']

def test_serve_media_range_request(client):
    """Test HTTP Range request support"""
    response = client.get(
        '/media/test-job-123',
        headers={'Range': 'bytes=0-1023'}
    )
    assert response.status_code == 206
    assert 'Content-Range' in response.headers

def test_serve_media_not_found(client):
    """Test 404 for non-existent job"""
    response = client.get('/media/nonexistent-job')
    assert response.status_code == 404

# tests/test_api_export.py (Story 2.5)
def test_export_srt_format(client):
    """Test SRT export generation"""
    segments = [
        {"start": 0.5, "end": 3.2, "text": "Test subtitle"},
        {"start": 3.5, "end": 7.8, "text": "Another segment"}
    ]
    response = client.post(
        '/export/test-job-123',
        json={'segments': segments, 'format': 'srt'}
    )
    assert response.status_code == 200
    assert 'application/x-subrip' in response.headers['Content-Type']
    assert '00:00:00,500 --> 00:00:03,200' in response.text

def test_export_txt_format(client):
    """Test TXT export generation"""
    segments = [{"start": 0.5, "end": 3.2, "text": "Test"}]
    response = client.post(
        '/export/test-job-123',
        json={'segments': segments, 'format': 'txt'}
    )
    assert response.status_code == 200
    assert response.text == "Test"

# tests/test_services_export.py
def test_generate_srt():
    """Test SRT format generation"""
    from app.services.export_service import generate_srt
    segments = [{"start": 0.5, "end": 3.2, "text": "Hello world"}]
    result = generate_srt(segments)
    assert "1\n" in result
    assert "00:00:00,500 --> 00:00:03,200\n" in result
    assert "Hello world\n" in result

def test_generate_txt():
    """Test TXT format generation"""
    from app.services.export_service import generate_txt
    segments = [
        {"start": 0.5, "end": 3.2, "text": "Hello"},
        {"start": 3.5, "end": 7.8, "text": "world"}
    ]
    result = generate_txt(segments)
    assert result == "Hello world"
```

**Frontend (Vitest):**

```typescript
// src/components/MediaPlayer.test.ts (Story 2.2)
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MediaPlayer from './MediaPlayer.vue'
import { useTranscriptionStore } from '@/stores/transcription'

describe('MediaPlayer', () => {
  it('seeks player when store.currentTime changes', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: { mediaUrl: '/media/test-job-123' }
    })

    const video = wrapper.find('video').element as HTMLVideoElement
    store.currentTime = 10.5

    await wrapper.vm.$nextTick()
    expect(video.currentTime).toBe(10.5)
  })

  it('updates store.playbackTime on timeupdate event', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: { mediaUrl: '/media/test-job-123' }
    })

    const video = wrapper.find('video').element as HTMLVideoElement
    video.currentTime = 5.0
    await video.dispatchEvent(new Event('timeupdate'))

    // Wait for throttled update (250ms)
    await new Promise(resolve => setTimeout(resolve, 300))
    expect(store.playbackTime).toBe(5.0)
  })

  it('syncs isPlaying state with player events', async () => {
    const store = useTranscriptionStore()
    const wrapper = mount(MediaPlayer, {
      props: { mediaUrl: '/media/test-job-123' }
    })

    const video = wrapper.find('video').element
    await video.dispatchEvent(new Event('play'))
    expect(store.isPlaying).toBe(true)

    await video.dispatchEvent(new Event('pause'))
    expect(store.isPlaying).toBe(false)
  })
})

// src/components/SubtitleList.test.ts (Stories 2.3, 2.4)
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SubtitleList from './SubtitleList.vue'
import { useTranscriptionStore } from '@/stores/transcription'

describe('SubtitleList - Click-to-Timestamp', () => {
  it('calls store.seekTo() when subtitle clicked', async () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Test subtitle' }
    ]

    const wrapper = mount(SubtitleList)
    await wrapper.find('.subtitle-segment').trigger('click')

    expect(store.currentTime).toBe(0.5)
  })

  it('highlights active segment based on store.activeSegmentIndex', async () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Segment 1' },
      { start: 3.5, end: 7.8, text: 'Segment 2' }
    ]
    store.activeSegmentIndex = 1

    const wrapper = mount(SubtitleList)
    const segments = wrapper.findAll('.subtitle-segment')

    expect(segments[0].classes()).not.toContain('active')
    expect(segments[1].classes()).toContain('active')
  })

  it('blocks seek when editing', async () => {
    const store = useTranscriptionStore()
    store.segments = [{ start: 0.5, end: 3.2, text: 'Test' }]
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    const initialTime = store.currentTime

    await wrapper.find('.subtitle-segment').trigger('click')

    // currentTime should not change when editing
    expect(store.currentTime).toBe(initialTime)
  })
})

describe('SubtitleList - Inline Editing', () => {
  it('enables edit mode on click', async () => {
    const store = useTranscriptionStore()
    store.segments = [{ start: 0.5, end: 3.2, text: 'Original text' }]

    const wrapper = mount(SubtitleList)
    await wrapper.find('.subtitle-text').trigger('click')

    expect(store.editingSegmentId).toBe(0)
    expect(wrapper.find('input').exists()).toBe(true)
  })

  it('updates segment text on input', async () => {
    const store = useTranscriptionStore()
    store.segments = [{ start: 0.5, end: 3.2, text: 'Original' }]
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    const input = wrapper.find('input')
    await input.setValue('Edited text')

    expect(store.segments[0].text).toBe('Edited text')
  })

  it('saves and moves to next on Tab key', async () => {
    const store = useTranscriptionStore()
    store.segments = [
      { start: 0.5, end: 3.2, text: 'Segment 1' },
      { start: 3.5, end: 7.8, text: 'Segment 2' }
    ]
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    await wrapper.find('input').trigger('keydown.tab')

    expect(store.editingSegmentId).toBe(1)
  })

  it('reverts changes on Escape key', async () => {
    const store = useTranscriptionStore()
    const originalText = 'Original text'
    store.segments = [{ start: 0.5, end: 3.2, text: originalText }]
    store.editingSegmentId = 0

    const wrapper = mount(SubtitleList)
    const input = wrapper.find('input')
    await input.setValue('Edited text')
    await input.trigger('keydown.esc')

    expect(store.segments[0].text).toBe(originalText)
    expect(store.editingSegmentId).toBeNull()
  })
})

// src/components/ExportButton.test.ts (Story 2.6)
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ExportButton from './ExportButton.vue'
import * as api from '@/services/api'

describe('ExportButton', () => {
  it('calls export API with selected format', async () => {
    const exportSpy = vi.spyOn(api, 'exportTranscription')
    const wrapper = mount(ExportButton, {
      props: { jobId: 'test-job-123' }
    })

    await wrapper.find('input[value="srt"]').setChecked()
    await wrapper.find('button.export').trigger('click')

    expect(exportSpy).toHaveBeenCalledWith(
      'test-job-123',
      expect.any(Array),
      'srt'
    )
  })

  it('triggers browser download on successful export', async () => {
    vi.spyOn(api, 'exportTranscription').mockResolvedValue(
      new Blob(['test content'], { type: 'application/x-subrip' })
    )

    const wrapper = mount(ExportButton, {
      props: { jobId: 'test-job-123' }
    })

    await wrapper.find('button.export').trigger('click')

    // Verify blob URL created and download triggered
    // (mock document.createElement and URL.createObjectURL)
  })

  it('shows error message on export failure', async () => {
    vi.spyOn(api, 'exportTranscription').mockRejectedValue(
      new Error('Export failed')
    )

    const wrapper = mount(ExportButton, {
      props: { jobId: 'test-job-123' }
    })

    await wrapper.find('button.export').trigger('click')
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-message').text()).toContain('Export failed')
  })
})
```

**localStorage Tests:**

```typescript
// tests/localstorage.test.ts
import { describe, it, expect, beforeEach } from 'vitest'
import { useTranscriptionStore } from '@/stores/transcription'

describe('localStorage Persistence', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('auto-saves edits to localStorage', async () => {
    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0.5, end: 3.2, text: 'Edited text' }]

    // Wait for throttled save (500ms)
    await new Promise(resolve => setTimeout(resolve, 600))

    const saved = localStorage.getItem('klipnote_edits_test-job-123')
    expect(saved).not.toBeNull()
    const parsed = JSON.parse(saved!)
    expect(parsed.segments[0].text).toBe('Edited text')
  })

  it('restores edits on page load', () => {
    const editData = {
      job_id: 'test-job-123',
      segments: [{ start: 0.5, end: 3.2, text: 'Restored text' }],
      last_saved: new Date().toISOString()
    }
    localStorage.setItem(
      'klipnote_edits_test-job-123',
      JSON.stringify(editData)
    )

    const store = useTranscriptionStore()
    store.loadFromLocalStorage('test-job-123')

    expect(store.segments[0].text).toBe('Restored text')
  })

  it('handles QuotaExceededError gracefully', async () => {
    // Mock localStorage.setItem to throw QuotaExceededError
    const originalSetItem = localStorage.setItem
    localStorage.setItem = vi.fn(() => {
      throw new DOMException('QuotaExceededError')
    })

    const store = useTranscriptionStore()
    store.jobId = 'test-job-123'
    store.segments = [{ start: 0.5, end: 3.2, text: 'Text' }]

    // Should not crash, should log warning
    await new Promise(resolve => setTimeout(resolve, 600))

    localStorage.setItem = originalSetItem
  })
})
```

**2. Integration Tests**

**Backend Integration:**

```python
# tests/integration/test_media_export_flow.py
def test_complete_media_export_workflow(client, tmp_path):
    """Test full workflow: upload → media serving → export"""
    # Setup: Upload file (Epic 1)
    upload_response = client.post(
        '/upload',
        files={'file': ('test.mp3', b'fake audio', 'audio/mpeg')}
    )
    job_id = upload_response.json()['job_id']

    # Test: Serve media
    media_response = client.get(f'/media/{job_id}')
    assert media_response.status_code == 200

    # Test: Export with edits
    export_response = client.post(
        f'/export/{job_id}',
        json={
            'segments': [
                {'start': 0.5, 'end': 3.2, 'text': 'Edited subtitle'}
            ],
            'format': 'srt'
        }
    )
    assert export_response.status_code == 200

    # Verify: Data flywheel files created
    assert (tmp_path / job_id / 'edited.json').exists()
    assert (tmp_path / job_id / 'export_metadata.json').exists()
```

**Frontend Integration:**

```typescript
// tests/integration/review-edit-export.test.ts
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import EditorView from '@/views/EditorView.vue'
import { createPinia } from 'pinia'

describe('Review → Edit → Export Flow', () => {
  it('completes full editing workflow', async () => {
    const pinia = createPinia()
    const wrapper = mount(EditorView, {
      global: { plugins: [pinia] },
      props: { jobId: 'test-job-123' }
    })

    // Wait for media and transcription to load
    await wrapper.vm.$nextTick()

    // Test: Media player rendered
    expect(wrapper.find('video').exists()).toBe(true)

    // Test: Click subtitle seeks player
    await wrapper.find('.subtitle-segment').trigger('click')
    const video = wrapper.find('video').element as HTMLVideoElement
    expect(video.currentTime).toBeGreaterThan(0)

    // Test: Edit subtitle
    await wrapper.find('.subtitle-text').trigger('click')
    await wrapper.find('input').setValue('Edited text')

    // Test: Export
    await wrapper.find('.export-button').trigger('click')
    // Verify export API called (mock)
  })
})
```

**3. End-to-End Tests (Playwright - Story 2.7)**

```typescript
// e2e/tests/review-edit-export.spec.ts
import { test, expect } from '@playwright/test'

test('complete review, edit, and export workflow', async ({ page }) => {
  // Setup: Upload file and get to results page (Epic 1 flow)
  await page.goto('/')
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles('fixtures/test-audio.mp3')
  await page.click('button:has-text("Upload")')

  await expect(page.locator('text=Transcription Complete')).toBeVisible({ timeout: 120000 })

  // Test: Media player present
  await expect(page.locator('video, audio')).toBeVisible()

  // Test: Click-to-timestamp navigation
  const firstSubtitle = page.locator('.subtitle-segment').first()
  await firstSubtitle.click()

  // Verify player seeked (check currentTime via JS)
  const currentTime = await page.evaluate(() => {
    const player = document.querySelector('video, audio') as HTMLMediaElement
    return player.currentTime
  })
  expect(currentTime).toBeGreaterThan(0)

  // Test: Inline editing
  const subtitleText = page.locator('.subtitle-text').first()
  await subtitleText.click()
  await page.keyboard.type(' EDITED')
  await page.keyboard.press('Tab')

  // Verify edit saved
  await expect(subtitleText).toContainText('EDITED')

  // Test: Export
  await page.click('button:has-text("Export")')
  await page.click('input[value="srt"]')
  await page.click('button:has-text("Download")')

  // Verify download triggered (wait for download event)
  const download = await page.waitForEvent('download')
  expect(download.suggestedFilename()).toMatch(/transcript-.*\.srt/)
})

test('localStorage persists edits across page refresh', async ({ page }) => {
  // ... upload and navigate to results ...

  // Edit subtitle
  await page.locator('.subtitle-text').first().click()
  await page.keyboard.type(' EDITED')
  await page.keyboard.press('Tab')

  // Refresh page
  await page.reload()

  // Verify edit persisted
  await expect(page.locator('.subtitle-text').first()).toContainText('EDITED')
})

test('error handling for failed export', async ({ page, context }) => {
  // Mock API to return error
  await context.route('**/export/**', route => {
    route.fulfill({
      status: 500,
      body: JSON.stringify({ detail: 'Export failed' })
    })
  })

  // ... navigate to results ...

  await page.click('button:has-text("Export")')
  await expect(page.locator('text=Export failed')).toBeVisible()
  await expect(page.locator('button:has-text("Retry")')).toBeVisible()
})
```

**4. Manual Testing Checklist**

**Story 2.1 (Media API):**
- [ ] Upload MP3, verify GET /media/{job_id} returns audio
- [ ] Upload MP4, verify GET /media/{job_id} returns video
- [ ] Test Range request in browser DevTools Network tab
- [ ] Verify Content-Type headers correct for each format
- [ ] Test 404 error for non-existent job_id

**Story 2.2 (Media Player):**
- [ ] Media player displays above subtitle list
- [ ] Audio files show audio element, video files show video element
- [ ] Native controls work (play, pause, seek, volume)
- [ ] Seeking works smoothly (no buffering delays)
- [ ] Responsive on mobile/tablet screens

**Story 2.3 (Click-to-Timestamp):**
- [ ] Click subtitle, verify player seeks to start time
- [ ] Player auto-plays after seek
- [ ] Active subtitle highlights during playback
- [ ] Highlight updates as playback progresses
- [ ] Response time <1 second (measure with stopwatch)
- [ ] Touch interaction works on tablet

**Story 2.4 (Inline Editing):**
- [ ] Click subtitle text, becomes editable
- [ ] Type text, updates immediately
- [ ] Tab key moves to next subtitle
- [ ] Enter key saves edit
- [ ] Escape key reverts changes
- [ ] Edited subtitles have visual indicator
- [ ] Refresh page, edits persist (localStorage)

**Story 2.5 (Export API):**
- [ ] Export SRT, verify format correct in text editor
- [ ] Export TXT, verify plain text (no timestamps)
- [ ] Verify edited.json file created on server
- [ ] Verify export_metadata.json has correct fields
- [ ] Privacy notice displayed before export

**Story 2.6 (Export UI):**
- [ ] Export button visible
- [ ] Format selection (SRT/TXT) works
- [ ] Click export, file downloads to browser
- [ ] Filename format: transcript-{job_id}.{ext}
- [ ] Loading indicator during export
- [ ] Error message if export fails
- [ ] Can export both formats sequentially

**Story 2.7 (MVP Validation):**
- [ ] Complete workflow on 5+ different files
- [ ] Test Chrome (desktop + mobile)
- [ ] Test Firefox (desktop + mobile)
- [ ] Test Safari (desktop + iOS)
- [ ] Test Edge (desktop)
- [ ] Performance: UI load <3s, playback <2s, seek <1s
- [ ] Mobile responsiveness on actual devices
- [ ] All error scenarios tested (network, file errors, etc.)

**Test Execution Commands:**

```bash
# Backend unit tests
cd backend
source .venv/Scripts/activate
pytest tests/ -v --cov=app --cov-report=html

# Frontend unit tests
cd frontend
npm run test:unit -- --coverage

# E2E tests (Story 2.7)
npx playwright test
npx playwright test --headed  # With browser visible
npx playwright test --debug   # Step-through debugging
```

**Test Data Requirements:**

- **Audio files:** test-short.mp3 (10s), test-medium.mp3 (5min), test-long.mp3 (1hr)
- **Video files:** test-short.mp4 (10s), test-medium.mp4 (5min)
- **Corrupted files:** test-corrupted.mp3 (for error handling)
- **Transcription fixtures:** JSON files with known segments for mocking

**Definition of Done (Testing Perspective):**

- ✓ All unit tests pass
- ✓ All integration tests pass
- ✓ All E2E tests pass
- ✓ Code coverage targets met (70% backend, 70% frontend, 80% critical paths)
- ✓ Manual testing checklist completed for all stories
- ✓ Cross-browser testing completed (Chrome, Firefox, Safari, Edge)
- ✓ Performance targets validated (NFR001)
- ✓ No critical bugs blocking epic completion
- ✓ Test fixtures and mock data committed to repository
