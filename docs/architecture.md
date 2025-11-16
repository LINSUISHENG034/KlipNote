# Decision Architecture - KlipNote

## Project Context

**Project:** KlipNote - Zero-friction audio/video transcription with integrated review
**Epics:** 2 epics, 14 stories
**Level:** 2 (Medium project)

### Core Functionality
- Web-based transcription using WhisperX (GPU-accelerated, self-hosted)
- Upload → Async Processing → Integrated Review → Export workflow
- Click-to-timestamp navigation synchronized with media player
- Inline subtitle editing with data flywheel (AI vs human edits)
- Export to SRT/TXT formats for LLM processing

### Critical NFRs
- **Performance**: Transcription 1-2x real-time, UI load <3s, playback <2s, seek <1s
- **Usability**: Self-service for non-technical users, no documentation required
- **Reliability**: 90%+ completion rate, browser-based ephemeral state
- **Compatibility**: Desktop/tablet/mobile browsers, Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### Unique Architectural Challenges
- Real-time subtitle synchronization with <1s response time
- Data flywheel: capture original + edited transcriptions for training data
- Ephemeral stateless design: no auth, no sessions, browser-only state
- Async GPU job processing with progress polling
- HTTP Range request support for media seeking

### Technology Foundation (from PRD)
- Backend: FastAPI + Celery + Redis + WhisperX
- Frontend: Vue 3 + Vite
- Media: MP3, MP4, WAV, M4A (FFmpeg)

---

## Starter Template Decisions

### Frontend: Official Vue CLI (create-vue)

**Command:**
```bash
npm create vue@latest klipnote-frontend -- --typescript --router --pinia
```

**Rationale:**
- Vue Router: Enables upload → progress → results page navigation
- Pinia: State management for job_id, transcription data, editing state
- TypeScript: Type safety for API contracts and component props
- Official tooling: Always up-to-date with Vue ecosystem best practices

**Architectural Decisions Provided by Starter:**
- Build tooling: Vite (fast HMR, optimized production builds)
- Vue 3 Composition API as default pattern
- TypeScript configuration (tsconfig.json)
- Project structure: src/, components/, views/, stores/, router/
- ESLint + Prettier for code quality

**Tailwind CSS Configuration (v4):**
- Version: 4.1.16+ (CSS-first, modern Vite integration)
- Integration: `@tailwindcss/vite` plugin (NOT `@tailwindcss/postcss`)
- Configuration approach: No `postcss.config.js` needed
- CSS import: `@import "tailwindcss";` (replaces v3's `@tailwind` directives)
- Rationale: v4 redesigned for native Vite integration, simpler config, better HMR performance

### Backend: Manual Setup with Docker Compose

**Structure:**
```
klipnote-backend/
├── docker-compose.yaml       # Orchestrates: web, worker, redis, flower
├── .env                       # Redis connection strings, config
├── requirements.txt           # FastAPI, Celery, Redis, WhisperX
├── Dockerfile                 # Python 3.11+ with GPU support
└── app/
    ├── main.py                # FastAPI app + API endpoints
    ├── config.py              # Pydantic settings from .env
    ├── celery_utils.py        # Celery instance configuration
    ├── models.py              # Pydantic models for API requests/responses
    └── tasks/
        ├── __init__.py
        └── transcription.py   # Celery tasks for WhisperX processing
```

**Rationale:**
- WhisperX requires custom GPU configuration (not in standard templates)
- Avoids database/ORM complexity not needed for MVP
- Docker Compose cleanly separates: FastAPI web, Celery worker, Redis
- Manual setup gives full control over media file handling patterns

**Architectural Decisions Provided by Manual Setup:**
- Service separation: web (FastAPI), worker (Celery), redis (broker + backend)
- Redis dual-role: Message broker + result backend
- Celery `@shared_task` pattern for task definitions
- Environment-based configuration (.env → config.py)
- Flower monitoring service for Celery task inspection

### Project Initialization Story

**Story 0.1** (before Story 1.1 in Epic 1): Project initialization using starter templates

**Acceptance Criteria:**
1. Frontend initialized: `npm create vue@latest klipnote-frontend -- --typescript --router --pinia`
2. Backend structure created following Docker Compose pattern
3. Docker Compose file configured with web, worker, redis, flower services
4. Requirements.txt includes: fastapi, celery[redis], redis, whisperx, uvicorn
5. Basic .env file with CELERY_BROKER_URL and CELERY_RESULT_BACKEND
6. Both services can start: `docker-compose up` (backend), `npm run dev` (frontend)
7. Git repository initialized with .gitignore for Python, Node, Docker

---

## Development Environment Requirements

### Platform & Tooling

- **Development Platform:** Windows 10/11
- **Python Version:** 3.12.x (managed via `uv`)
- **Python Environment Manager:** `uv` (NOT global Python, NOT conda, NOT venv)
- **Node.js Version:** 20.x LTS (for frontend)
- **Package Managers:**
  - Backend: `uv pip` (Python dependencies)
  - Frontend: `npm` (Node dependencies)

### Environment Isolation Strategy

**Backend (Python):**
- **Virtual Environment Tool:** `uv` (Astral's fast Python package installer)
- **Environment Location:** `backend/.venv/` (local to backend directory)
- **Activation Required:** YES - all backend commands MUST run inside uv environment
- **Installation Commands (Windows):**
  ```bash
  # Create virtual environment
  cd backend
  uv venv --python 3.12

  # Activate (Git Bash)
  source .venv/Scripts/activate

  # OR Activate (PowerShell)
  .venv\Scripts\Activate.ps1

  # OR Activate (CMD)
  .venv\Scripts\activate.bat

  # Install dependencies
  uv pip install -r requirements.txt
  ```

**Frontend (Node.js):**
- **Virtual Environment Tool:** `npm` (Node's built-in package manager)
- **Environment Location:** `frontend/node_modules/` (local to frontend directory)
- **Activation Required:** NO - npm manages isolation automatically
- **Installation Command:**
  ```bash
  cd frontend
  npm install
  ```

### Why uv for Backend?

1. **Speed:** 10-100x faster than pip for dependency resolution
2. **Consistency:** Reproducible builds across team members and AI agents
3. **Isolation:** Prevents global Python pollution
4. **Windows-friendly:** Works seamlessly on Windows without WSL
5. **Future-proof:** Modern tool aligned with Python ecosystem direction
6. **GPU Library Compatibility:** Full pip compatibility for WhisperX, torch, CUDA packages

### Environment Setup Validation

**Story 1.1 (Project Initialization) MUST verify:**
- [ ] `uv --version` succeeds (uv installed globally on Windows)
- [ ] `backend/.venv/` directory exists after setup
- [ ] `python --version` inside .venv shows 3.12.x
- [ ] `which python` (or `where python` in CMD) points to `backend/.venv/Scripts/python.exe`
- [ ] `frontend/node_modules/` exists after npm install
- [ ] Docker Desktop installed and GPU support configured

### Cross-Cutting Rule for ALL AI Agents

**CRITICAL - Backend Environment Activation:**

Every backend story implementation MUST:
1. **Activate uv virtual environment BEFORE running Python commands:**
   ```bash
   cd backend
   source .venv/Scripts/activate  # Git Bash
   # Verify: which python should show .venv/Scripts/python
   ```
2. **Use `uv pip install <package>` for new dependencies** (NOT `pip install`)
3. **Update `requirements.txt` after adding dependencies:**
   ```bash
   uv pip freeze > requirements.txt
   ```
4. **Verify commands run in `.venv` context:**
   ```bash
   which python  # Must show: backend/.venv/Scripts/python
   python --version  # Must show: 3.12.x
   ```

**Frontend Environment (No Activation Needed):**
- Use `npm install <package>` for dependencies
- `package.json` automatically updated by npm

**Docker Environment:**
- Docker containers use their OWN isolated Python environment
- `Dockerfile` installs dependencies from `requirements.txt`
- Development `.venv` is for LOCAL testing only (NOT copied to Docker)

### Environment Isolation Verification Pattern

**Before running backend tests or commands:**
```bash
# Check current Python environment
which python
# Expected: /e/Projects/KlipNote/backend/.venv/Scripts/python

# If NOT in virtual environment:
cd backend
source .venv/Scripts/activate

# Verify packages are isolated:
python -m pip list
# Should show ONLY project dependencies, not global packages
```

**Before running frontend commands:**
```bash
# Check Node.js version
node --version
# Expected: v20.x.x

# Verify project dependencies installed
npm list --depth=0
# Should show: vue@3.x, typescript@5.x, vue-router@4.x, pinia
```

---

## Technology Stack Decisions

### Core Technology Versions (Verified 2025-11-03)

| Technology | Version | Rationale | Affects Epics |
|------------|---------|-----------|---------------|
| Python | 3.12.x | Stable ecosystem compatibility, WhisperX support | All backend epics |
| FastAPI | 0.120.x | Latest stable, async support, auto-docs | All API epics (1.1-2.7) |
| Celery | 5.5.3 | Stable release, Redis support, Python 3.12 compatible | Epic 1 (async transcription) |
| Redis | 7.x (alpine) | Dual-role: broker + result backend, Docker optimized | Epic 1 (job queue) |
| Vue | 3.x | From create-vue starter, Composition API | All frontend epics |
| TypeScript | 5.x | From create-vue starter, type safety | All frontend epics |
| Tailwind CSS | 4.1.16+ | Modern CSS-first approach, native Vite integration via @tailwindcss/vite | All frontend epics |
| Node.js | 20.x LTS | Frontend build tooling compatibility | Development only |
| Pinia | Latest | Vue official state management | Epic 2 (review interface) |
| Vue Router | 4.x | Vue 3 compatible routing | Epic 1 & 2 (navigation) |
| WhisperX | Latest | GPU-accelerated transcription with timestamps | Epic 1 (transcription) |

### Key Architectural Decisions

#### Job ID Format
- **Decision:** UUID v4
- **Rationale:** Industry standard, built into Python (`uuid.uuid4()`), no collision risk, URL-safe
- **Format:** `550e8400-e29b-41d4-a716-446655440000` (36 characters)
- **Usage:**
  - API URLs: `/status/{job_id}`, `/result/{job_id}`, `/media/{job_id}`
  - Redis keys: `job:{job_id}:status`, `job:{job_id}:result`
  - File storage: `{job_id}/original.{ext}`
- **Affects:** Epic 1.2-1.7, Epic 2.1-2.6 (all API interactions)

#### Media File Storage Strategy
- **Decision:** Job-based folder structure on filesystem
- **Structure:**
  ```
  /uploads/
    /{job_id}/
      original.{ext}      # Uploaded file (preserves extension)
      transcription.json  # WhisperX output with timestamps
      edited.json         # Human-edited version (data flywheel)
  ```
- **Rationale:**
  - Job-based folders keep related files together
  - Original extension preserved for FFmpeg/WhisperX compatibility
  - Separate JSON files enable data flywheel (FR019: persist original + edited)
  - Simple filesystem approach (no S3/CDN needed for MVP)
- **Affects:** Epic 1.2, 1.3, 2.1, 2.5 (upload, transcription, media serving, export)

#### API Response Format
- **Decision:** Direct response with FastAPI standard error format
- **Success Response Example:**
  ```json
  {"job_id": "550e8400-...", "status": "processing", "progress": 45}
  ```
- **Error Response Example (FastAPI standard):**
  ```json
  {"detail": "File format not supported"}
  ```
- **Rationale:**
  - FastAPI native format (no custom wrapper needed)
  - HTTP status codes provide error context (200, 400, 404, 500)
  - Simpler for frontend consumption
  - Less boilerplate code
- **Affects:** All API endpoints (Epic 1.2-1.7, Epic 2.1-2.6)

#### Transcription Data Format (Subtitle Segments)
- **Decision:** JSON array with float timestamps
- **Format:**
  ```json
  {
    "segments": [
      {
        "start": 0.5,
        "end": 3.2,
        "text": "Hello, welcome to the meeting."
      },
      {
        "start": 3.5,
        "end": 7.8,
        "text": "Today we'll discuss the quarterly results."
      }
    ]
  }
  ```
- **Rationale:**
  - `start`/`end` as float seconds: WhisperX native format, precise, easy arithmetic
  - Top-level `segments` wrapper: Allows future metadata (language, duration, model version)
  - Plain text field: Preserves WhisperX output exactly
  - Straightforward SRT conversion: `start` and `end` map directly to SRT timestamps
  - Frontend can format display times (seconds → MM:SS) without data loss
- **Affects:** Epic 1.3, 1.4, 1.7, Epic 2.3-2.6 (transcription, display, editing, export)

#### Progress Tracking Structure in Redis
- **Decision:** Single JSON key per job in Redis with stage-based progress messaging
- **Redis Key Pattern:** `job:{job_id}:status`
- **Value Format:**
  ```json
  {
    "status": "processing",
    "progress": 40,
    "message": "Transcribing audio...",
    "created_at": "2025-11-03T10:30:00Z",
    "updated_at": "2025-11-03T10:31:15Z"
  }
  ```
- **Status Values:** `"pending"`, `"processing"`, `"completed"`, `"failed"`
- **Progress:** Integer 0-100 (percentage) - represents stage completion, not real-time AI progress
- **Message:** User-facing stage description (NOT fake percentage from WhisperX black box):
  - `"Task queued..."` (progress: 10)
  - `"Loading AI model..."` (progress: 20)
  - `"Transcribing audio..."` (progress: 40) - longest stage
  - `"Aligning timestamps..."` (progress: 80)
  - `"Processing complete!"` (progress: 100)
- **Rationale:**
  - Single key per job: Simple, atomic updates from Celery worker
  - JSON string: Rich status info, extensible
  - **Message field critical:** WhisperX is black-box - stage-based messaging more honest than fake percentages
  - Timestamps: Debugging and timeout detection
  - Status enum: Clear lifecycle states for frontend logic
- **Affects:** Epic 1.3, 1.4, 1.6 (Celery tasks, status API, progress monitoring)

#### CORS Configuration
- **Decision:** FastAPI CORS middleware with environment-based origins
- **Development:**
  - Frontend origin: `http://localhost:5173` (Vite default)
  - Backend origin: `http://localhost:8000` (FastAPI)
  - Allow credentials, all methods, all headers
- **Production:** Configure for production frontend domain or same-origin deployment
- **Implementation:**
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app.add_middleware(
      CORSMiddleware,
      allow_origins=["http://localhost:5173"],  # From environment variable
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
- **Rationale:**
  - Separate dev servers require CORS
  - Environment-based config: Different origins for dev/staging/prod
  - Permissive in dev, restrictive in prod
- **Affects:** All frontend API calls (Epic 1.5-1.7, Epic 2.2-2.6)

#### HTTP Range Request Support for Media Seeking
- **Decision:** Use FastAPI `FileResponse` with automatic Range request handling
- **Implementation:**
  ```python
  from fastapi.responses import FileResponse

  @app.get("/media/{job_id}")
  async def serve_media(job_id: str):
      file_path = f"/uploads/{job_id}/original.{ext}"
      return FileResponse(file_path)  # Automatic Range support
  ```
- **Rationale:**
  - `FileResponse` has built-in HTTP Range request support
  - Browsers send `Range: bytes=0-1023` automatically for media seeking
  - FastAPI responds with `206 Partial Content` and `Content-Range` headers
  - Enables smooth seeking without loading entire file
  - Meets NFR001 requirement: timestamp seeking <1 second
- **Affects:** Epic 2.1, 2.2, 2.3 (media API, player integration, click-to-timestamp)

#### Frontend API Client
- **Decision:** Native `fetch()` API (no external HTTP library)
- **Rationale:**
  - Built into modern browsers (Chrome 90+, Firefox 88+, Safari 14+)
  - TypeScript types included (@types/node)
  - Zero dependencies - simpler build
  - Sufficient for simple REST API calls
  - Less boilerplate than Axios for this use case
- **Usage Pattern:**
  ```typescript
  // services/api.ts
  const API_BASE = 'http://localhost:8000'

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
- **Affects:** All frontend API calls (Epic 1.5-1.7, Epic 2.2-2.6)

#### Export File Naming Convention
- **Decision:** `transcript-{job_id}.{ext}` format
- **Examples:**
  - SRT: `transcript-550e8400-e29b-41d4-a716-446655440000.srt`
  - TXT: `transcript-550e8400-e29b-41d4-a716-446655440000.txt`
- **Rationale:**
  - Prefix identifies file type clearly
  - Job ID ensures uniqueness (no overwrites)
  - File extension indicates format
  - Browser downloads use this name by default
- **Affects:** Epic 2.5, 2.6 (export API, frontend download)

#### localStorage Persistence for Edit Recovery
- **Decision:** Auto-save edited subtitles to browser localStorage to prevent data loss (FR-020, NFR-003)
- **localStorage Key Pattern:** `klipnote_edits_{job_id}`
- **Value Format:**
  ```json
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "segments": [
      {"start": 0.5, "end": 3.2, "text": "Edited subtitle text"},
      {"start": 3.5, "end": 7.8, "text": "Another edited subtitle"}
    ],
    "last_saved": "2025-11-03T10:35:22Z"
  }
  ```
- **Save Strategy:**
  - **Throttled auto-save:** Watch Pinia store segments array, save to localStorage every 500ms after changes
  - **On page load:** Check localStorage for key matching current job_id
  - **Restoration priority:** localStorage edits override API results (user's work takes precedence)
  - **Cleanup:** Clear localStorage entry after successful export (optional - keeps data for re-download)
- **Implementation Pattern:**
  ```typescript
  // stores/transcription.ts
  import { watch } from 'vue'
  import { throttle } from 'lodash-es'

  // Inside store setup
  const throttledSave = throttle((jobId: string, segments: Segment[]) => {
    localStorage.setItem(`klipnote_edits_${jobId}`, JSON.stringify({
      job_id: jobId,
      segments,
      last_saved: new Date().toISOString()
    }))
  }, 500)

  watch(() => state.segments, (newSegments) => {
    if (state.jobId && newSegments.length > 0) {
      throttledSave(state.jobId, newSegments)
    }
  }, { deep: true })

  // On load (in EditorView.vue or store action)
  function loadFromLocalStorage(jobId: string): Segment[] | null {
    const saved = localStorage.getItem(`klipnote_edits_${jobId}`)
    if (saved) {
      const data = JSON.parse(saved)
      return data.segments
    }
    return null
  }
  ```
- **Rationale:**
  - **Critical UX fix:** Browser refresh is "normal operation" - losing edits is unacceptable
  - **Minimal implementation:** 500ms throttle prevents excessive writes, ~20 lines of code
  - **No backend changes:** Pure frontend solution, aligns with "browser-based ephemeral" design
  - **localStorage limits:** 5-10MB sufficient (1 hour transcription ≈ 100KB JSON)
  - **Resolves NFR-003 conflict:** Satisfies "prevent data loss during normal operation" without complex server-side session management
- **Edge Cases:**
  - **Multiple tabs:** Last write wins (acceptable for MVP - single-user workflow)
  - **localStorage full:** Catch QuotaExceededError, warn user (rare for transcription data)
  - **Corrupted data:** Wrap JSON.parse in try/catch, fall back to API result
  - **Stale data:** `last_saved` timestamp allows future "resume editing" features
- **Affects:** Epic 2.2 (load check), Epic 2.4 (auto-save on edit), satisfies FR-020 & NFR-003

#### Known Risks & Mitigation Strategies

**Risk: Large File Upload (2GB) Performance**

- **Issue:** Standard HTTP file uploads of 2GB may encounter memory/timeout issues in FastAPI or client browser
- **Current Approach (MVP):** FastAPI streams uploads by default (should handle 2GB)
- **Testing Requirement:** Story 1.2 AC7 mandates testing with actual 2GB file
- **Indicators of Problem:**
  - Upload fails with memory errors or timeouts
  - Backend container OOM (Out of Memory) kills
  - Browser tab freezes during upload
- **Phase 2 Solutions (if testing reveals issues):**
  1. **Chunked Upload:** Implement tus.io resumable upload protocol
     - Frontend: Split file into 5MB chunks using `File.slice()`
     - Backend: Reassemble chunks, add completion endpoint
     - Complexity: ~2-3 days dev work
  2. **Direct-to-Storage Upload:** Pre-signed URLs to cloud storage (if moving to S3)
  3. **Client-side Compression:** Compress before upload (may impact transcription quality)
- **Mitigation for MVP:**
  - Set nginx/FastAPI timeouts appropriately (e.g., 30 minutes for upload)
  - Monitor memory usage during 2GB test
  - Document file size limits clearly in UI if issues found
  - Accept risk: 2GB uploads are edge case (most meetings <500MB)
- **Decision:** Document as known risk, test thoroughly, defer chunked upload unless proven necessary
- **Affects:** Epic 1.2 (upload endpoint), potential Phase 2 enhancement

---

## Cross-Cutting Concerns

These patterns ensure consistency across ALL epics and stories.

### Error Handling Strategy

**Backend (FastAPI):**
- Use `HTTPException` with standard status codes
  - `400 Bad Request`: Invalid file format, missing fields, validation errors
  - `404 Not Found`: Job ID doesn't exist, file not found
  - `500 Internal Server Error`: WhisperX failures, disk errors, unexpected exceptions
- Error response format: `{"detail": "Human-readable error message"}`
- Celery task errors: Catch exceptions, update job status to `"failed"`, store error in Redis

**Frontend (Vue/TypeScript):**
- Catch fetch errors and HTTP error responses
- Display user-friendly messages (avoid technical jargon)
- Error UI: Toast/alert for temporary errors, inline validation for forms
- Never expose stack traces or internal details to users

**Example Implementation:**
```python
# Backend: app/main.py
from fastapi import HTTPException

@app.post("/upload")
async def upload_file(file: UploadFile):
    if not is_allowed_format(file):
        raise HTTPException(
            status_code=400,
            detail="File format not supported. Please upload MP3, MP4, WAV, or M4A."
        )
```

```typescript
// Frontend: services/api.ts
try {
  const result = await uploadFile(file)
  return result
} catch (error) {
  showErrorToast('Upload failed. Please check your file and try again.')
  throw error
}
```

**Affects:** All epics (consistent error handling across entire app)

### Logging Strategy

**Backend (Python):**
- **Library:** Python built-in `logging` module
- **Format:** Structured logs with timestamp, log level, module, message
- **Levels:**
  - `INFO`: API requests, job lifecycle events, successful operations
  - `WARNING`: Retries, deprecated features, unusual but handled conditions
  - `ERROR`: Failures, exceptions, unrecoverable errors
  - `DEBUG`: Development only - verbose diagnostic info
- **Output:** stdout (Docker captures for log aggregation)
- **Configuration:**
  ```python
  import logging

  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  logger = logging.getLogger(__name__)
  ```

**Frontend (TypeScript):**
- **Development:** `console.log()`, `console.warn()`, `console.error()`
- **Production:** Minimal logging (errors only, no sensitive data)
- **No external logging service for MVP** (can add Sentry later)

**Example Usage:**
```python
# Backend
logger.info(f"Transcription job {job_id} started for file {filename}")
logger.error(f"WhisperX failed for job {job_id}: {error}", exc_info=True)
```

**Affects:** All epics (debugging, monitoring, operational visibility)

### Date/Time Handling

**Backend:**
- **Format:** ISO 8601 strings with UTC timezone (`"2025-11-03T10:30:00Z"`)
- **Library:** Python `datetime` module with UTC timezone
- **Storage:** ISO strings in Redis and JSON files
- **Generation:**
  ```python
  from datetime import datetime, timezone

  timestamp = datetime.now(timezone.utc).isoformat()
  # Result: "2025-11-03T10:30:00+00:00"
  ```

**Frontend:**
- **API Communication:** ISO 8601 strings (matches backend)
- **Display:** Format for users based on locale or relative time
  - Relative: "2 minutes ago", "1 hour ago"
  - Absolute: "Nov 3, 2025 10:30 AM"
- **Library:** Native `Date` object (built-in) or `date-fns` if advanced formatting needed
- **Parsing:**
  ```typescript
  const date = new Date("2025-11-03T10:30:00Z")
  const relativeTime = getRelativeTime(date)  // "2 minutes ago"
  ```

**Rationale:**
- ISO 8601: Universal standard, sortable, timezone-aware
- UTC everywhere: Avoids timezone conversion bugs
- Format on display: Users see local time, backend stores UTC

**Affects:** All epics with timestamps (job creation, progress updates, export metadata)

### AI Service Abstraction Strategy

**Decision:** Create `ai_services` module with abstract interface for transcription services, supporting multi-model architecture and pluggable optimization pipeline

**Rationale:**
1. **Multi-model support:** Chinese/Mandarin model selected through Epic 3 A/B testing (BELLE-2 vs WhisperX), faster-whisper for other languages
2. **Pluggable optimization:** Interface-based optimizer design supporting multiple implementations (WhisperX wav2vec2 alignment, self-developed heuristics)
3. **Architectural flexibility:** Configuration-driven model and optimizer selection prevents technology lock-in, enables easy replacement when better solutions emerge
4. **Service abstraction:** Easy to add future models or optimization techniques
5. **Testing:** Mock AI service for unit tests without GPU dependency

**Epic 3 Update (2025-11-15):** Both BELLE-2 and WhisperX validated in Epic 3 (Stories 3.2b-3.2c). MVP ships with single model selected via Story 4.7. Multi-model production deployment (both models available) implemented in Epic 4 using Docker Compose multi-worker architecture.

**Epic 4 Update (2025-11-16):** Enhanced metadata schema and model-agnostic component architecture enable composable enhancement pipeline with comprehensive quality tracking.

**Architecture:**
```python
# app/ai_services/base.py
from abc import ABC, abstractmethod
from typing import List, Dict

class TranscriptionService(ABC):
    @abstractmethod
    async def transcribe(self, audio_path: str, language: str = "auto") -> List[Dict]:
        """Returns list of segments: [{"start": 0.5, "end": 3.2, "text": "..."}]"""
        pass

# app/ai_services/whisperx_service.py - Epic 1 foundation
from .base import TranscriptionService
import whisperx  # Git submodule

class WhisperXService(TranscriptionService):
    def __init__(self, model_name: str = "large-v2", device: str = "cuda"):
        self.model = whisperx.load_model(model_name, device)

    async def transcribe(self, audio_path: str, language: str = "auto"):
        result = self.model.transcribe(audio_path)
        return result["segments"]

# app/ai_services/belle2_service.py - Epic 3 Chinese optimization
# STATUS: Conditional - pending Epic 3 A/B test results (BELLE-2 vs WhisperX)
from .base import TranscriptionService
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

class Belle2Service(TranscriptionService):
    """BELLE-2 whisper-large-v3-zh for Chinese/Mandarin transcription

    Note: This implementation validated in Story 3.1 (eliminated gibberish loops).
    Final production usage pending Epic 3.2c A/B comparison vs WhisperX.
    """
    def __init__(self, model_name: str = "BELLE-2/Belle-whisper-large-v3-zh", device: str = "cuda"):
        self.model = AutoModelForSpeechSeq2Seq.from_pretrained(model_name).to(device)
        self.processor = AutoProcessor.from_pretrained(model_name)

    async def transcribe(self, audio_path: str, language: str = "zh"):
        # Chinese-optimized decoder settings
        result = self.model.transcribe(
            audio_path,
            language="zh",
            beam_size=5,
            temperature=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        )
        return result["segments"]

# app/ai_services/optimization/ - Epic 3 pluggable optimization pipeline
# ├── base.py                  # TimestampOptimizer abstract interface (Story 3.2a)
# ├── factory.py               # OptimizerFactory with auto-selection (Story 3.2a)
# ├── whisperx_optimizer.py    # WhisperX wav2vec2 forced alignment (Story 3.2b)
# ├── heuristic_optimizer.py   # Self-developed VAD+refinement+splitting (Stories 3.3-3.5)
# └── quality_validator.py     # CER/WER calculation, length statistics (Story 3.6)

# app/ai_services/__init__.py
from .whisperx_service import WhisperXService
from .belle2_service import Belle2Service

# Factory pattern - configuration-driven model selection
def get_transcription_service(language: str = "auto") -> TranscriptionService:
    # Epic 3: Route based on language (simplified - full routing in Story 3.2)
    if language in ["zh", "zh-CN", "zh-TW"]:
        return Belle2Service()
    return WhisperXService()
```

**Optimization Pipeline Flow (Epic 3 - Pluggable Architecture):**
```
Audio Input → [Selected Model: BELLE-2 or WhisperX]* Transcription →
┌─────────────────────────────────────────────────────┐
│ TimestampOptimizer Interface (Story 3.2a)          │
├─────────────────────────────────────────────────────┤
│ OptimizerFactory.create(engine="auto")             │
│                                                      │
│ IF WhisperXOptimizer.is_available():                │
│   └→ WhisperX wav2vec2 forced alignment (Story 3.2b)│
│ ELSE:                                                │
│   └→ HeuristicOptimizer (Stories 3.3-3.5):          │
│      - VAD Preprocessing (Story 3.3)                 │
│      - Token Timestamp + Energy Refinement (3.4)     │
│      - Intelligent Segment Splitting (Story 3.5)     │
└─────────────────────────────────────────────────────┘
→ Quality Validation (Story 3.6) → Optimized Output

* Model selection pending Epic 3.2c A/B comparison results
  - BELLE-2: Validated in Story 3.1 (gibberish elimination)
  - WhisperX: Full pipeline evaluation in Story 3.2c
```

**Configuration (Story 3.2a - Epic 3 Complete):**
```python
# .env
OPTIMIZER_ENGINE=auto  # "whisperx" | "heuristic" | "auto"
# MVP: Single optimizer based on selected model
# Epic 4: Model-agnostic enhancement components (VAD, refine, split)
```

**Epic 4 Enhancement Pipeline (Post-MVP):**
```python
# .env
ENHANCEMENT_PIPELINE=vad,refine,split  # Composable components
VAD_ENABLED=true
TIMESTAMP_REFINE_ENABLED=true
SEGMENT_SPLIT_ENABLED=true
```

#### Timestamp Optimization Architecture

**Components**

- `TimestampOptimizer` abstract base and `TimestampSegment` typed dict ( `app/ai_services/optimization/base.py` ) define the contract shared by every optimizer.
- `OptimizationResult` dataclass standardizes return payload (`segments`, `metrics`, `optimizer_name`) to decouple downstream services from implementation details.
- `OptimizerFactory` ( `app/ai_services/optimization/factory.py` ) is the single entry point for creating optimizers and encapsulates `"whisperx"`, `"heuristic"`, and `"auto"` selection with logging.
- Stub implementations:
  - `WhisperXOptimizer` advertises availability only when forced-alignment dependencies are installed (Story 3.2b will activate the real logic).
  - `HeuristicOptimizer` is always available and currently returns pass-through segments while recording metrics (future stories add VAD/refinement/splitting).

**Configuration Surface**

- `OPTIMIZER_ENGINE` (Pydantic `Literal["whisperx","heuristic","auto"]`) defaults to `auto`, which prefers WhisperX when available and logs a fallback to heuristics otherwise.
- `ENABLE_OPTIMIZATION` feature flag (default `True`) lets us disable optimization globally without removing code paths—critical for rapid rollback during Epic 3.

**Usage Example**

```python
from app.ai_services.optimization import OptimizerFactory
from app.config import settings

def optimize_segments(segments, audio_path: str):
    if not settings.ENABLE_OPTIMIZATION:
        return segments

    optimizer = OptimizerFactory.create()  # honors settings.OPTIMIZER_ENGINE
    result = optimizer.optimize(segments, audio_path=audio_path, language="zh")
    return result.segments
```

**Benefits**

1. New optimizers (Stories 3.3–3.5) simply implement `TimestampOptimizer`—no caller changes.
2. Centralized logging/fallback decisions aid observability and troubleshooting.
3. Typed segment/result structures keep contracts self-documenting and enable static analysis.

**Git Submodule Setup:**
```bash
# In backend/ directory
git submodule add https://github.com/m-bain/whisperX.git ai_services/whisperx
git submodule update --init --recursive
```

**Future Alternative Services:**
- `sensevoice_service.py` - Low-latency FunASR alternative (deferred to Epic 4)
- `deepgram_service.py` - Cloud API alternative (post-MVP)
- `faster_whisper_service.py` - Faster local alternative (post-MVP)

**Affects:** Epic 1.3 (transcription task), Epic 3 (multi-model + optimization pipeline)

### Enhanced Data Schema Architecture (Epic 4)

**Decision:** Hierarchical metadata schema supporting rich transcription metadata, processing pipeline tracking, and multi-language optimization

**Module:** `backend/app/ai_services/schema.py` (NEW in Epic 4)

**Rationale:**
1. **Character-level timestamps:** Essential for Chinese subtitle editing and precise navigation
2. **Processing transparency:** Track which enhancements were applied (VAD, refinement, splitting)
3. **Quality metrics:** Capture confidence scores for validation and debugging
4. **Future extensibility:** Speaker embeddings prepare for diarization features
5. **Backward compatibility:** Alias pattern prevents breaking existing code

**Schema Layers:**

**Layer 1: Atomic Timing Data**
```python
# Character-level timestamps (critical for Chinese)
class CharTiming(TypedDict, total=False):
    char: str              # Single character
    start: float           # Start timestamp (seconds)
    end: float             # End timestamp (seconds)
    score: float           # Alignment confidence (0.0-1.0)

# Word-level timestamps with metadata
class WordTiming(TypedDict, total=False):
    word: str              # Word text
    start: float           # Start timestamp (seconds)
    end: float             # End timestamp (seconds)
    score: float           # Alignment confidence (0.0-1.0)
    language: str          # Language code (e.g., "zh", "en")
```

**Layer 2: Base Segment (Backward Compatible)**
```python
class BaseSegment(TypedDict):
    start: float           # Required: segment start time
    end: float             # Required: segment end time
    text: str              # Required: transcribed text
```

**Layer 3: Enhanced Segment (Rich Metadata)**
```python
class EnhancedSegment(BaseSegment, total=False):
    # Enhanced timing arrays
    words: List[WordTiming]           # Word-level timestamps
    chars: Optional[List[CharTiming]] # Character-level (Chinese critical)

    # Quality metrics
    confidence: float                  # Overall confidence (0.0-1.0)
    no_speech_prob: float              # Silence probability
    avg_logprob: float                 # Average log probability

    # Processing metadata
    source_model: Literal["belle2", "whisperx"]
    enhancements_applied: List[str]    # e.g., ["vad_silero", "timestamp_refine"]

    # Speaker diarization (future)
    speaker: Optional[str]             # Speaker ID
    speaker_embedding: Optional[List[float]]
```

**Layer 4: Result Container**
```python
class TranscriptionMetadata(TypedDict, total=False):
    language: str                      # Detected/specified language
    language_prob: float               # Language detection confidence
    duration: float                    # Total audio duration
    model_name: str                    # Transcription model used
    model_version: str                 # Model version
    processing_time: float             # Total processing time
    vad_enabled: bool                  # VAD preprocessing applied
    alignment_model: Optional[str]     # Timestamp alignment model

class TranscriptionResult(TypedDict):
    segments: List[EnhancedSegment]    # Transcription segments
    metadata: TranscriptionMetadata    # Global metadata
    stats: Dict[str, Any]              # Processing statistics
```

**Migration Strategy:**
```python
# Backward compatibility alias
TimestampSegment = EnhancedSegment

# Service layer supports both simple and enhanced modes
def transcribe_with_metadata(
    audio_path: str,
    include_metadata: bool = True
) -> TranscriptionResult:
    if include_metadata:
        return {"segments": enhanced_segments, "metadata": {...}}
    else:
        return {"segments": base_segments}  # Simple mode
```

**Component Integration:**

**VAD Component:**
```python
# VAD appends processing metadata
enhanced_segment["enhancements_applied"].append("vad_silero")
enhanced_segment["metadata"]["vad_enabled"] = True
```

**Timestamp Refiner:**
```python
# Populates character/word timing arrays
enhanced_segment["chars"] = char_timings  # Chinese segments
enhanced_segment["words"] = word_timings  # All segments
enhanced_segment["enhancements_applied"].append("timestamp_refine")
```

**Segment Splitter:**
```python
# Preserves timing arrays when splitting
split_segments = split_with_timing_preservation(segment)
for seg in split_segments:
    seg["enhancements_applied"].append("segment_split")
```

**Quality Validator:**
```python
# Leverages metadata for comprehensive analysis
avg_confidence = mean([s["confidence"] for s in segments])
chinese_char_accuracy = validate_char_timings(
    [s["chars"] for s in segments if s.get("chars")]
)
pipeline_effectiveness = analyze_enhancements_applied(segments)
```

**Benefits Delivered:**
1. **Chinese optimization:** Character-level timestamps enable precise editing
2. **Pipeline transparency:** `enhancements_applied` enables debugging and A/B testing
3. **Quality validation:** Confidence scores enable automated quality gates
4. **Model comparison:** `source_model` enables BELLE-2 vs WhisperX analysis
5. **Future-proof:** Speaker embeddings prepare for diarization (Epic 5+)

**Affects:** Epic 4 Stories 4.2-4.6 (all enhancement components)

### VAD Engine Architecture (Epic 4)

**Decision:** Multi-engine Voice Activity Detection with Silero deep-learning VAD as primary engine

**Module Structure:**
```
backend/app/ai_services/enhancement/
├── vad_manager.py              # Unified VAD interface
├── vad_engines/
│   ├── __init__.py
│   ├── base_vad.py             # Abstract VAD interface
│   ├── silero_vad.py           # Silero deep-learning VAD (PRIMARY)
│   └── webrtc_vad.py           # WebRTC signal-processing VAD (FALLBACK)
```

**Rationale:**
1. **Silero VAD superiority:** Deep-learning VAD outperforms signal-processing approaches
2. **WhisperX extraction:** Proven 70-line implementation from WhisperX codebase
3. **Model consistency:** Unified VAD across BELLE-2 and WhisperX (prevents duplicate processing)
4. **No new dependencies:** Silero uses torch.hub (already installed)
5. **Fallback strategy:** WebRTC VAD as lightweight alternative if Silero unavailable

**Abstract Interface:**
```python
# base_vad.py
from abc import ABC, abstractmethod
from typing import List, Tuple

class BaseVAD(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if VAD engine dependencies are available"""
        pass

    @abstractmethod
    def detect_speech(
        self,
        audio_path: str,
        threshold: float = 0.5
    ) -> List[Tuple[float, float]]:
        """
        Returns: List of (start, end) tuples for speech segments
        """
        pass

    @abstractmethod
    def filter_segments(
        self,
        segments: List[EnhancedSegment],
        min_silence_duration: float = 1.0
    ) -> List[EnhancedSegment]:
        """Remove segments with silence exceeding threshold"""
        pass
```

**Silero VAD Implementation:**
```python
# silero_vad.py (extracted from WhisperX)
import torch
from typing import List, Tuple

class SileroVAD(BaseVAD):
    def __init__(
        self,
        threshold: float = 0.5,
        min_silence_ms: int = 700,
        min_speech_ms: int = 250
    ):
        self.model = None
        self.threshold = threshold
        self.min_silence_ms = min_silence_ms
        self.min_speech_ms = min_speech_ms

    def is_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available() or True  # CPU fallback
        except ImportError:
            return False

    def _load_model(self):
        if self.model is None:
            # Load from torch.hub (WhisperX pattern)
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )

    def detect_speech(
        self,
        audio_path: str,
        threshold: float = None
    ) -> List[Tuple[float, float]]:
        self._load_model()
        threshold = threshold or self.threshold

        # Silero VAD processing (simplified from WhisperX)
        speech_timestamps = get_speech_timestamps(
            audio_path,
            self.model,
            threshold=threshold,
            min_silence_duration_ms=self.min_silence_ms,
            min_speech_duration_ms=self.min_speech_ms
        )

        return [(ts['start'], ts['end']) for ts in speech_timestamps]
```

**WebRTC VAD Implementation:**
```python
# webrtc_vad.py (fallback engine)
import webrtcvad

class WebRTCVAD(BaseVAD):
    def __init__(self, aggressiveness: int = 2):
        self.aggressiveness = aggressiveness  # 0-3
        self.vad = None

    def is_available(self) -> bool:
        try:
            import webrtcvad
            return True
        except ImportError:
            return False

    def _load_model(self):
        if self.vad is None:
            self.vad = webrtcvad.Vad(self.aggressiveness)

    def detect_speech(
        self,
        audio_path: str,
        threshold: float = None
    ) -> List[Tuple[float, float]]:
        # WebRTC frame-based VAD processing
        # (Implementation details)
        pass
```

**VAD Manager (Multi-Engine Support):**
```python
# vad_manager.py
class VADManager:
    def __init__(self, engine: str = "auto"):
        self.engine = self._select_engine(engine)

    def _select_engine(self, engine: str) -> BaseVAD:
        if engine == "auto":
            # Prefer Silero, fallback to WebRTC
            if SileroVAD().is_available():
                logger.info("Using Silero VAD (deep-learning)")
                return SileroVAD()
            elif WebRTCVAD().is_available():
                logger.info("Using WebRTC VAD (fallback)")
                return WebRTCVAD()
            else:
                raise RuntimeError("No VAD engine available")
        elif engine == "silero":
            return SileroVAD()
        elif engine == "webrtc":
            return WebRTCVAD()
        else:
            raise ValueError(f"Unknown VAD engine: {engine}")

    def process_segments(
        self,
        segments: List[EnhancedSegment],
        audio_path: str
    ) -> List[EnhancedSegment]:
        """Apply VAD filtering and update metadata"""
        filtered = self.engine.filter_segments(segments)

        # Update metadata
        for seg in filtered:
            seg.setdefault("enhancements_applied", [])
            seg["enhancements_applied"].append(
                f"vad_{self.engine.__class__.__name__.lower()}"
            )

        return filtered
```

**Configuration:**
```python
# config.py
VAD_ENGINE: Literal["auto", "silero", "webrtc"] = "auto"
VAD_SILERO_THRESHOLD: float = 0.5          # 0.0-1.0
VAD_SILERO_MIN_SILENCE_MS: int = 700       # Milliseconds
VAD_WEBRTC_AGGRESSIVENESS: int = 2         # 0-3
```

**WhisperX Integration:**
```python
# Disable WhisperX built-in VAD (prevents duplicate processing)
whisperx_result = whisperx_model.transcribe(
    audio_path,
    language="zh",
    vad_filter=False  # ← Disable built-in Silero VAD
)

# Apply unified VAD post-transcription
vad_manager = VADManager(engine="silero")
filtered_segments = vad_manager.process_segments(
    whisperx_result["segments"],
    audio_path
)
```

**Benefits:**
1. **Consistency:** Both BELLE-2 and WhisperX use same Silero VAD
2. **No duplication:** WhisperX built-in VAD disabled
3. **Quality:** Deep-learning VAD superior to signal processing
4. **Minimal dependencies:** torch.hub, already installed
5. **Extensibility:** Easy to add future VAD engines (e.g., pyannote.audio)

**Affects:** Epic 4.2 (VAD preprocessing story)

### GPU Environment Requirements

**Decision:** WhisperX and BELLE-2 require GPU acceleration for NFR001 performance targets (1-2x real-time transcription)

**Note:** Docker GPU setup described below is for **production deployment only**. For Epic 3 optimization development, use local `.venv` environment with direct GPU access (see "Development vs. Production Environment Strategy" section).

**Hardware Requirements:**
- **GPU:** NVIDIA GPU with CUDA support
- **Minimum VRAM:** 8GB (recommended 12GB+ for large models)
- **CUDA Version:** Depends on Epic 3.2c model selection
  - BELLE-2: CUDA 11.8 (PyTorch <2.6, validated in Story 3.1)
  - WhisperX: CUDA 12.x (PyTorch ≥2.6, required for CVE-2025-32434 security)
- **Driver:** NVIDIA driver 520+ (for CUDA 11.8) or 530+ (for CUDA 12.1+)

**Note:** Final CUDA version and PyTorch dependency determined by Epic 3.2c A/B test winner. Both models cannot coexist in single environment due to PyTorch version conflict.

**Epic 3 Outcome & Epic 4 Deployment Strategy:**

Epic 3 (Story 3.2c) confirmed both models warrant production support:
- **BELLE-2:** CUDA 11.8 / PyTorch <2.6 (validated in `.venv`)
- **WhisperX:** CUDA 12.x / PyTorch ≥2.6 (validated in `.venv-whisperx`)

**MVP Deployment (Single Model):**
- Select one model via Story 4.7 based on A/B test results
- Deploy single Docker worker container with chosen model's CUDA version
- Other model archived for Epic 4 integration

**Epic 4 Deployment (Multi-Model):**
- Docker Compose multi-worker architecture:
  ```yaml
  services:
    belle2-worker:
      image: klipnote-worker-cuda118
      environment:
        - MODEL=belle2
    whisperx-worker:
      image: klipnote-worker-cuda12
      environment:
        - MODEL=whisperx
    web:
      # Routes jobs to appropriate worker based on model selection
  ```
- Celery task routing: `@app.task(queue='belle2')` or `@app.task(queue='whisperx')`
- Zero environment conflicts: isolated containers per model

**Docker GPU Setup (Production Deployment):**

```bash
# Install nvidia-docker runtime (Ubuntu/Debian)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker

# Test GPU access in Docker
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**docker-compose.yaml GPU Configuration:**

```yaml
services:
  worker:
    # ... other config
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
```

**WhisperX Model Setup:**
- **Models Directory:** `/root/.cache/whisperx/` (inside Docker container)
- **Model Size:** large-v2 is ~3GB
- **Download:** Auto-download on first transcription (Story 1.3 implementation)
- **Persistence:** Mount cache directory as volume to avoid re-downloading:
  ```yaml
  volumes:
    - whisperx-models:/root/.cache/whisperx
  ```

**CPU Fallback Mode:**

For development/testing on machines without GPU:

```python
# app/ai_services/whisperx_service.py
class WhisperXService(TranscriptionService):
    def __init__(self, model_name: str = "large-v2", device: str = None):
        # Auto-detect device if not specified
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device
        self.model = whisperx.load_model(model_name, device)

        if device == "cpu":
            logger.warning(
                "WhisperX running on CPU. Performance: 4-6x real-time "
                "(vs 1-2x with GPU). NFR001 targets not achievable."
            )
```

**Environment Variable Configuration:**

```bash
# .env file
WHISPER_DEVICE=cuda  # or "cpu" for fallback mode
WHISPER_MODEL=large-v2
WHISPER_COMPUTE_TYPE=float16  # GPU: float16, CPU: int8 for speed
```

**Performance Expectations:**
- **GPU Mode:** 1-2x real-time (1 hour audio = 30-60 min processing) ✓ Meets NFR001
- **CPU Mode:** 4-6x real-time (1 hour audio = 4-6 hours processing) ⚠️ Does not meet NFR001
- **Recommendation:** GPU required for production, CPU acceptable for development/testing only

**Validation Steps for Story 1.1:**
1. Verify GPU available: `nvidia-smi` shows GPU
2. Test Docker GPU access: `docker run --rm --gpus all nvidia/cuda nvidia-smi`
3. Document GPU specs in project README
4. Configure docker-compose.yaml with GPU support
5. Set up model cache volume for persistence

**Affects:** Story 1.1 (environment setup), Story 1.3 (WhisperX integration), NFR001 (performance)

### Development vs. Production Environment Strategy

**Decision:** Separate development and production environments to enable rapid optimization experimentation while maintaining production stability

**Context:** Epic 3 requires extensive parameter tuning for optimization pipeline (VAD aggressiveness, timestamp refinement ranges, segment splitting thresholds). Docker container rebuilds create critical iteration bottleneck during experimentation phase.

**Strategy:**

**Development Environment (Optimization & Experimentation):**
- **Runtime:** Local Python `.venv` with direct GPU access
- **Purpose:** Rapid parameter tuning, optimization experiments, algorithm development

**Epic 3 Status (2025-11-15):**
- ✅ `.venv`: BELLE-2 validated (CUDA 11.8)
- ✅ `.venv-whisperx`: WhisperX validated (CUDA 12.x)
- 📋 MVP: One environment selected for deployment
- 📋 Epic 4: Both environments productionized with Docker multi-worker

- **Setup:**
  ```bash
  # Create virtual environment with CUDA support
  python -m venv .venv
  .venv\Scripts\activate  # Windows
  # or: source .venv/bin/activate  # Linux/Mac

  # Install dependencies with CUDA
  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
  pip install -r requirements.txt
  ```
- **Configuration:** Local `.env` file for rapid parameter changes
- **Advantages:**
  - Instant parameter changes (no container rebuild)
  - Full GPU visibility for profiling and debugging
  - Faster iteration cycles during Story 3.2-3.5 implementation
  - IDE debugging support with breakpoints

**Production Environment (Deployment):**
- **Runtime:** Docker Compose with validated configurations
- **Purpose:** Stable deployment with tested parameter sets
- **Setup:** `docker-compose.yaml` with environment variables
- **Configuration:** Environment variables in docker-compose.yaml or .env
- **Advantages:**
  - Reproducible deployment across servers
  - Isolated dependencies
  - Production-grade GPU resource management
  - Easy rollback to stable configurations

**Configuration Promotion Workflow:**

1. **Prototype** - Experiment with parameters in local `.env`:
   ```bash
   # Development .env
   ENABLE_VAD=true
   VAD_AGGRESSIVENESS=3
   SEGMENT_MAX_DURATION=7.0
   SEGMENT_MAX_CHARS=200
   ```

2. **Validate** - Run quality validation framework (Story 3.5):
   - Measure segment length statistics
   - Calculate CER/WER improvements
   - Verify click-to-timestamp alignment

3. **Promote** - Copy validated parameters to `docker-compose.yaml`:
   ```yaml
   # docker-compose.yaml
   services:
     worker:
       environment:
         - ENABLE_VAD=true
         - VAD_AGGRESSIVENESS=3
         - SEGMENT_MAX_DURATION=7.0
         - SEGMENT_MAX_CHARS=200
   ```

4. **Deploy** - Build and deploy Docker containers with validated config

**Best Practices:**
- **Document rationale:** Add comments in docker-compose.yaml explaining parameter choices
- **Version control:** Track configuration changes in git
- **Rollback plan:** Keep previous working configurations commented in docker-compose.yaml
- **Logging:** Epic 3 structured logging enables production parameter monitoring

**Affects:** Epic 3 (Stories 3.2-3.5 optimization implementation), deployment workflows

### Testing Strategy

**Decision:** Implement comprehensive testing strategy across backend, frontend, and E2E layers to ensure quality and prevent regressions.

**Framework Selection:**

| Layer | Framework | Purpose | Coverage Target |
|-------|-----------|---------|----------------|
| Backend API | pytest | API endpoint tests, Celery task tests | 70%+ |
| Backend Services | pytest + pytest-mock | Business logic, service layer tests | 70%+ |
| Frontend Components | Vitest + Vue Testing Library | Component tests, integration tests | 70%+ |
| E2E Workflows | Playwright | Cross-browser user workflow validation | Critical paths |

**Test Organization:**

```
KlipNote/
├── backend/
│   ├── tests/
│   │   ├── conftest.py              # Pytest fixtures
│   │   ├── test_api_upload.py       # Story 1.2 tests
│   │   ├── test_api_status.py       # Story 1.4 tests
│   │   ├── test_api_media.py        # Story 2.1 tests
│   │   ├── test_api_export.py       # Story 2.5 tests
│   │   ├── test_tasks_transcription.py  # Story 1.3 tests (mocked)
│   │   ├── test_services_file_handler.py
│   │   └── test_services_export.py
│   └── pytest.ini                   # Pytest configuration
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileUpload.test.ts
│   │   │   ├── ProgressBar.test.ts
│   │   │   ├── MediaPlayer.test.ts
│   │   │   ├── SubtitleList.test.ts
│   │   │   └── ExportButton.test.ts
│   │   ├── views/
│   │   │   ├── UploadView.test.ts
│   │   │   ├── ProgressView.test.ts
│   │   │   └── EditorView.test.ts
│   │   └── services/
│   │       └── api.test.ts
│   └── vitest.config.ts             # Vitest configuration
│
└── e2e/
    ├── tests/
    │   ├── upload-workflow.spec.ts   # Story 1.5-1.7 flow
    │   ├── review-edit.spec.ts       # Story 2.2-2.4 flow
    │   ├── export.spec.ts            # Story 2.6 flow
    │   └── error-scenarios.spec.ts   # Story 2.7 edge cases
    └── playwright.config.ts          # Playwright configuration
```

**Backend Testing Patterns:**

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_whisperx(mocker):
    """Mock WhisperX to avoid GPU dependency in tests"""
    mock_service = mocker.patch('app.ai_services.whisperx_service.WhisperXService')
    mock_service.return_value.transcribe.return_value = [
        {"start": 0.0, "end": 2.5, "text": "Test transcription"}
    ]
    return mock_service

# tests/test_api_upload.py (Story 1.2)
def test_upload_file_success(client):
    files = {'file': ('test.mp3', b'fake audio data', 'audio/mpeg')}
    response = client.post('/upload', files=files)
    assert response.status_code == 200
    assert 'job_id' in response.json()

def test_upload_unsupported_format(client):
    files = {'file': ('test.exe', b'fake data', 'application/exe')}
    response = client.post('/upload', files=files)
    assert response.status_code == 400
    assert 'not supported' in response.json()['detail']

# tests/test_tasks_transcription.py (Story 1.3)
def test_transcribe_audio_task(mock_whisperx):
    from app.tasks.transcription import transcribe_audio

    job_id = "test-job-123"
    file_path = "/uploads/test-job-123/original.mp3"

    result = transcribe_audio(job_id, file_path)

    assert 'segments' in result
    assert len(result['segments']) > 0
    mock_whisperx.return_value.transcribe.assert_called_once()
```

**Frontend Testing Patterns:**

```typescript
// src/components/FileUpload.test.ts (Story 1.5)
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-library'
import FileUpload from './FileUpload.vue'

describe('FileUpload', () => {
  it('accepts valid audio/video files', async () => {
    const wrapper = mount(FileUpload)
    const file = new File(['audio'], 'test.mp3', { type: 'audio/mpeg' })

    const input = wrapper.find('input[type="file"]')
    await input.setValue([file])

    expect(wrapper.emitted('file-selected')).toBeTruthy()
  })

  it('rejects unsupported file formats', async () => {
    const wrapper = mount(FileUpload)
    const file = new File(['data'], 'test.exe', { type: 'application/exe' })

    const input = wrapper.find('input[type="file"]')
    await input.setValue([file])

    expect(wrapper.text()).toContain('not supported')
  })
})

// src/components/MediaPlayer.test.ts (Story 2.2)
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-library'
import MediaPlayer from './MediaPlayer.vue'

describe('MediaPlayer', () => {
  it('seeks to timestamp on external command', async () => {
    const wrapper = mount(MediaPlayer, {
      props: { mediaUrl: '/media/test-job-123' }
    })

    const video = wrapper.find('video').element as HTMLVideoElement

    // Simulate store.currentTime update (click-to-timestamp)
    await wrapper.vm.seekTo(10.5)

    expect(video.currentTime).toBe(10.5)
  })
})
```

**E2E Testing Patterns:**

```typescript
// e2e/tests/upload-workflow.spec.ts (Story 2.7)
import { test, expect } from '@playwright/test'

test('complete upload to transcription workflow', async ({ page }) => {
  // Navigate to upload page
  await page.goto('/')

  // Upload file
  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles('fixtures/test-audio.mp3')
  await page.click('button:has-text("Upload")')

  // Wait for progress
  await expect(page.locator('.progress-bar')).toBeVisible()

  // Wait for completion (with timeout for transcription)
  await expect(page.locator('text=Transcription Complete')).toBeVisible({ timeout: 120000 })

  // Verify transcription displayed
  await expect(page.locator('.subtitle-segment')).toHaveCount.greaterThan(0)
})

test('error handling for unsupported file', async ({ page }) => {
  await page.goto('/')

  const fileInput = page.locator('input[type="file"]')
  await fileInput.setInputFiles('fixtures/test.exe')
  await page.click('button:has-text("Upload")')

  await expect(page.locator('text=not supported')).toBeVisible()
})
```

**Test Coverage Targets:**
- **Critical Paths:** 80%+ (upload, transcription, export)
- **Business Logic:** 70%+ (API endpoints, services, core components)
- **UI Components:** 60%+ (display components, utilities)
- **Overall Project:** 70%+ combined coverage

**CI/CD Integration (Future):**

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r backend/requirements.txt pytest pytest-mock pytest-cov
      - name: Run tests
        run: pytest backend/tests --cov=backend/app --cov-report=xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      - name: Install dependencies
        run: cd frontend && npm install
      - name: Run tests
        run: cd frontend && npm run test:unit -- --coverage

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Playwright
        run: npx playwright install --with-deps
      - name: Run E2E tests
        run: npx playwright test
```

**Testing Requirements by Story:**

| Story | Test Requirements |
|-------|------------------|
| 1.1 | Setup test infrastructure, configure pytest/vitest |
| 1.2 | API upload endpoint tests (valid/invalid formats, error cases) |
| 1.3 | Celery task tests with mocked WhisperX |
| 1.4 | Status/result API tests (job exists, not found, error states) |
| 1.5 | FileUpload component tests (file selection, validation) |
| 1.6 | ProgressView tests (polling, state updates) |
| 1.7 | SubtitleList display tests (rendering, formatting) |
| 2.1 | Media API tests (Range requests, content-type headers) |
| 2.2 | MediaPlayer component tests (seek, play/pause, state sync) |
| 2.3 | Click-to-timestamp integration tests (seek accuracy, highlighting) |
| 2.4 | Inline editing tests (state updates, persistence) |
| 2.5 | Export API tests (SRT/TXT generation, data flywheel storage) |
| 2.6 | Export component tests (format selection, download trigger) |
| 2.7 | Comprehensive E2E suite (workflows, error scenarios, cross-browser) |

**Mock Strategies:**

1. **WhisperX Mock:** Always mock in unit tests to avoid GPU dependency
2. **Redis Mock:** Use `fakeredis` for fast, isolated backend tests
3. **File System Mock:** Use `pytest-tmp-path` for upload/storage tests
4. **API Mock:** Use MSW (Mock Service Worker) for frontend API tests

**Affects:** All stories (testing requirement added to each story's acceptance criteria)

---

## Project Structure and Boundaries

### Complete Project Structure

```
KlipNote/
├── backend/
│   ├── docker-compose.yaml           # Orchestrates web, worker, redis, flower
│   ├── Dockerfile                    # Python 3.12 + GPU support
│   ├── .env.example                  # Template for environment variables
│   ├── .env                          # Local config (git-ignored)
│   ├── .gitignore                    # Python, Docker, uploads/
│   ├── .gitmodules                   # Git submodule configuration
│   ├── requirements.txt              # Python dependencies
│   ├── README.md                     # Backend setup instructions
│   ├── uploads/                      # Media file storage (git-ignored)
│   │   └── {job_id}/
│   │       ├── original.{ext}
│   │       ├── transcription.json
│   │       └── edited.json
│   └── app/
│       ├── __init__.py
│       ├── main.py                   # FastAPI app + routes
│       ├── config.py                 # Pydantic settings from .env
│       ├── celery_utils.py           # Celery instance configuration
│       ├── models.py                 # Pydantic models for API
│       ├── ai_services/              # AI service abstraction layer
│       │   ├── __init__.py           # Service factory
│       │   ├── base.py               # Abstract TranscriptionService interface
│       │   ├── whisperx_service.py   # WhisperX implementation
│       │   └── whisperx/             # Git submodule (m-bain/whisperX)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── file_handler.py       # Upload/storage operations
│       │   └── export_service.py     # SRT/TXT generation
│       └── tasks/
│           ├── __init__.py
│           └── transcription.py      # Celery tasks using ai_services
│
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── vite.config.ts                # Vite build configuration
│   ├── .gitignore                    # Node, dist/
│   ├── README.md                     # Frontend setup instructions
│   ├── index.html                    # HTML entry point
│   ├── public/                       # Static assets
│   └── src/
│       ├── main.ts                   # Vue app initialization
│       ├── App.vue                   # Root component
│       ├── router/
│       │   └── index.ts              # Vue Router configuration
│       ├── stores/
│       │   └── transcription.ts      # Pinia store for job state
│       ├── services/
│       │   └── api.ts                # Fetch wrapper for backend API
│       ├── views/
│       │   ├── UploadView.vue        # Story 1.5: Upload page
│       │   ├── ProgressView.vue      # Story 1.6: Progress monitoring
│       │   └── EditorView.vue        # Story 1.7, 2.2-2.4: Review/edit
│       ├── components/
│       │   ├── FileUpload.vue        # Upload form component
│       │   ├── ProgressBar.vue       # Progress visualization
│       │   ├── MediaPlayer.vue       # Story 2.2: HTML5 player
│       │   ├── SubtitleList.vue      # Story 1.7, 2.3: Subtitle display
│       │   └── ExportButton.vue      # Story 2.6: Export UI
│       └── types/
│           └── api.ts                # TypeScript interfaces for API
│
└── docs/
    ├── architecture.md               # This document
    ├── PRD.md                        # Product requirements
    └── epics.md                      # Epic and story breakdown
```

### Epic to Architecture Mapping

| Epic | Backend Components | Frontend Components | Integration Points |
|------|-------------------|---------------------|-------------------|
| **Epic 1.1** | Project scaffolding, `ai_services/base.py` | Project scaffolding | Git submodule setup |
| **Epic 1.2** | `main.py` POST /upload, `file_handler.py` | N/A | File upload endpoint |
| **Epic 1.3** | `transcription.py` Celery task, `ai_services/whisperx_service.py` | N/A | Async AI transcription |
| **Epic 1.4** | `main.py` GET /status, GET /result, Redis queries | N/A | Status/result APIs |
| **Epic 1.5** | N/A | `UploadView.vue`, `FileUpload.vue`, `api.ts` | POST /upload |
| **Epic 1.6** | N/A | `ProgressView.vue`, `ProgressBar.vue`, `api.ts` polling | GET /status/{job_id} |
| **Epic 1.7** | N/A | `EditorView.vue`, `SubtitleList.vue` | GET /result/{job_id} |
| **Epic 2.1** | `main.py` GET /media, `FileResponse` with Range support | N/A | Media streaming |
| **Epic 2.2** | N/A | `MediaPlayer.vue` (HTML5 video/audio) | GET /media/{job_id} |
| **Epic 2.3** | N/A | `SubtitleList.vue` click handler, `MediaPlayer.vue` seek | Click-to-timestamp sync |
| **Epic 2.4** | N/A | `SubtitleList.vue` inline editing, Pinia state | Browser-based editing |
| **Epic 2.5** | `main.py` POST /export, `export_service.py` SRT/TXT | N/A | Export API with data flywheel |
| **Epic 2.6** | N/A | `ExportButton.vue`, download trigger | POST /export/{job_id} |
| **Epic 2.7** | All backend components | All frontend components | End-to-end testing |

---

## Novel Architectural Patterns

### Pattern: Click-to-Timestamp Synchronization

**Purpose:** KlipNote's killer feature - bidirectional synchronization between subtitle list and media player for rapid verification workflow.

**Core Challenge:**
- Tight coupling between subtitle list and media player components
- Real-time synchronization during playback (highlight active subtitle)
- Instant seek on subtitle click (<1 second per NFR001)
- State management across independent Vue components

**Components Involved:**
1. `MediaPlayer.vue` - HTML5 video/audio player
2. `SubtitleList.vue` - Scrollable list of subtitle segments with click handling
3. `transcription.ts` (Pinia store) - Shared state coordinator

**Data Flow:**

```
User Click Subtitle (SubtitleList)
  ↓
Store: seekTo(segment.start)
  ↓
MediaPlayer: Watch currentTime, seek player
  ↓
Player starts playback (respects isPlaying state)
  ↓
Player timeupdate event fires (throttled)
  ↓
Store: updatePlaybackTime() → updateActiveSegment()
  ↓
SubtitleList: Watch activeSegmentIndex, highlight + auto-scroll
```

**State Management (Pinia Store):**

```typescript
// stores/transcription.ts
import { defineStore } from 'pinia'

export const useTranscriptionStore = defineStore('transcription', {
  state: () => ({
    segments: [] as Segment[],
    currentTime: 0,              // Commanded seek position
    playbackTime: 0,             // Actual playback position
    activeSegmentIndex: -1,      // Currently highlighted segment
    isPlaying: false,            // Synced with player state
    editingSegmentId: null as number | null  // Track editing mode
  }),

  actions: {
    seekTo(time: number) {
      this.currentTime = time
    },

    updatePlaybackTime(time: number) {
      this.playbackTime = time
      this.updateActiveSegment(time)
    },

    // Optimized incremental search (O(1) for linear playback)
    updateActiveSegment(time: number) {
      const segments = this.segments
      if (segments.length === 0) return

      const currentIndex = this.activeSegmentIndex

      // Fast path: Check current segment (99% case during playback)
      if (currentIndex >= 0 && currentIndex < segments.length) {
        const currentSeg = segments[currentIndex]
        if (time >= currentSeg.start && time < currentSeg.end) {
          return // Still in current segment
        }
      }

      // Next fast path: Check next segment (normal playback)
      const nextIndex = currentIndex + 1
      if (nextIndex < segments.length) {
        const nextSeg = segments[nextIndex]
        if (time >= nextSeg.start && time < nextSeg.end) {
          this.activeSegmentIndex = nextIndex
          return
        }
      }

      // Fallback: User seeked or scrubbed, do full search
      const index = this.segments.findIndex(
        seg => time >= seg.start && time < seg.end
      )
      this.activeSegmentIndex = index
    },

    setIsPlaying(playing: boolean) {
      this.isPlaying = playing
    },

    setEditingSegment(segmentId: number | null) {
      this.editingSegmentId = segmentId
    }
  }
})
```

**MediaPlayer.vue Implementation:**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { throttle } from 'lodash-es'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()
const playerRef = ref<HTMLVideoElement | null>(null)

// Watch for commanded seeks from subtitle clicks
watch(() => store.currentTime, (newTime) => {
  if (playerRef.value && Math.abs(playerRef.value.currentTime - newTime) > 0.5) {
    playerRef.value.currentTime = newTime
    // Respect user's playback state - only play if already playing
    if (store.isPlaying) {
      playerRef.value.play()
    }
  }
})

// Throttled timeupdate to avoid excessive store updates
const throttledTimeUpdate = throttle((currentTime: number) => {
  store.updatePlaybackTime(currentTime)
}, 250) // Update every 250ms

function onTimeUpdate() {
  if (playerRef.value) {
    throttledTimeUpdate(playerRef.value.currentTime)
  }
}

// Sync native player state to store
function onPlay() {
  store.setIsPlaying(true)
}

function onPause() {
  store.setIsPlaying(false)
}
</script>

<template>
  <video
    ref="playerRef"
    :src="mediaUrl"
    @timeupdate="onTimeUpdate"
    @play="onPlay"
    @pause="onPause"
    @ended="onPause"
    controls
  />
</template>
```

**SubtitleList.vue Implementation:**

```vue
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { useTranscriptionStore } from '@/stores/transcription'

const store = useTranscriptionStore()
const subtitleListRef = ref<HTMLDivElement | null>(null)
const segmentRefs = ref<HTMLDivElement[]>([])

function handleClick(segment: Segment, index: number) {
  // Prevent seek during editing
  if (store.editingSegmentId !== null) {
    console.warn('Cannot seek while editing. Please finish editing first.')
    return
  }
  store.seekTo(segment.start)
}

// Auto-scroll active subtitle into view
watch(() => store.activeSegmentIndex, async (newIndex) => {
  if (newIndex === -1 || !segmentRefs.value[newIndex]) return

  await nextTick()

  segmentRefs.value[newIndex]?.scrollIntoView({
    behavior: 'smooth',
    block: 'center'  // Keep active subtitle in center of viewport
  })
})
</script>

<template>
  <div class="subtitle-list" ref="subtitleListRef">
    <div
      v-for="(segment, index) in store.segments"
      :key="index"
      :class="{ active: index === store.activeSegmentIndex }"
      :ref="(el) => { if (el) segmentRefs[index] = el as HTMLDivElement }"
      @click="handleClick(segment, index)"
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
}

.active {
  background-color: #e3f2fd;
  font-weight: 600;
}
</style>
```

**Performance Optimizations:**

1. **Throttled timeupdate:** Limits store updates to ~4 times/second (250ms interval)
2. **Incremental segment search:** O(1) complexity for linear playback instead of O(n)
   - Fast path: Check current segment (99% of playback cases)
   - Next fast path: Check next segment (normal sequential playback)
   - Fallback: Full search only when user seeks/scrubs
3. **Auto-scroll with smooth behavior:** Enhances UX without performance penalty

**Edge Cases Handled:**

1. **Seek during editing:** Block seek and warn user if `editingSegmentId !== null`
2. **Playback state respect:** Don't force play on seek if user paused
3. **End of media:** `onPause` handler captures end event
4. **Rapid clicks:** Latest `currentTime` wins (Vue reactivity handles this)
5. **Empty segments:** `findIndex` returns -1, handled gracefully
6. **Player state sync:** Native controls (play/pause buttons) sync to store via events

**Implementation Sequence:**

1. **Story 2.2:** Implement `MediaPlayer.vue` with state sync (`@play`, `@pause`, `@timeupdate`)
2. **Story 2.3:** Implement `SubtitleList.vue` with click handler and active highlighting
3. **Story 2.3:** Add auto-scroll behavior for active subtitle
4. **Story 2.4:** Integrate editing mode with seek blocking

**Testing Criteria:**

- Click subtitle → player seeks within 1 second ✓
- Active subtitle highlights during playback ✓
- Active subtitle auto-scrolls into view ✓
- Paused state preserved when clicking subtitle ✓
- Native player controls sync `isPlaying` state ✓
- Cannot seek while editing a subtitle ✓

**Affects Epics:** Epic 2.2, 2.3, 2.4 (media player, click-to-timestamp, editing)

---

## Implementation Patterns

These patterns ensure ALL AI agents write compatible, consistent code.

### Frontend Build Configuration (Tailwind CSS v4)

**Critical Pattern for ALL Frontend Agents:**

Tailwind CSS v4 uses a modern, Vite-native integration approach. ALL agents implementing frontend stories MUST follow this exact configuration:

**1. Dependencies:**
```json
// package.json
{
  "dependencies": {
    "tailwindcss": "^4.1.16"
  },
  "devDependencies": {
    "@tailwindcss/vite": "^4.1.16"  // ✅ USE THIS
    // ❌ DO NOT USE: "@tailwindcss/postcss"
  }
}
```

**2. Vite Configuration Pattern:**
```typescript
// frontend/vite.config.ts
import { fileURLToPath, URL } from 'node:url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'  // ✅ MUST import

export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    tailwindcss(),  // ✅ MUST add to plugins array
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  }
})
```

**3. Main CSS Pattern:**
```css
/* frontend/src/assets/main.css */
@import "tailwindcss";  /* ✅ v4 syntax - MUST be first line */

/* Other styles below */
```

**❌ DO NOT USE (v3 syntax):**
```css
@tailwind base;      /* ❌ Old syntax */
@tailwind components;
@tailwind utilities;
```

**4. Files That Should NOT Exist:**
- `postcss.config.js` - Delete if present (v4 doesn't need it with Vite)

**Rationale:**
- Tailwind v4 redesigned for modern build tools (Vite, Turbopack)
- `@tailwindcss/vite` provides native Vite integration with better performance
- Simpler configuration reduces complexity and potential conflicts
- Unified `@import` directive replaces three separate `@tailwind` directives
- No PostCSS config needed (eliminates extra configuration file)
- Better Hot Module Replacement (HMR) performance during development

**Common Mistakes to Avoid:**
- ❌ Installing `@tailwindcss/postcss` instead of `@tailwindcss/vite`
- ❌ Using old `@tailwind base/components/utilities` syntax
- ❌ Creating unnecessary `postcss.config.js` file
- ❌ Forgetting to add `tailwindcss()` to Vite plugins array

**Affects:** All frontend stories (1.5-1.7, 2.2-2.4, 2.6)

### Naming Conventions

**Backend (Python):**
- **API Endpoints:** Lowercase with hyphens: `/upload`, `/status/{job_id}`, `/media/{job_id}`
- **Functions:** snake_case: `upload_file()`, `get_transcription_result()`, `generate_srt()`
- **Classes:** PascalCase: `TranscriptionService`, `WhisperXService`, `Settings`
- **Files:** snake_case: `file_handler.py`, `transcription.py`, `whisperx_service.py`
- **Constants:** UPPER_SNAKE_CASE: `ALLOWED_FORMATS`, `MAX_FILE_SIZE`, `REDIS_KEY_PREFIX`
- **Pydantic Models:** PascalCase: `UploadResponse`, `StatusResponse`, `TranscriptionSegment`

**Frontend (TypeScript/Vue):**
- **Components:** PascalCase: `MediaPlayer.vue`, `SubtitleList.vue`, `ProgressBar.vue`
- **Composables:** camelCase with `use` prefix: `useTranscriptionStore()`, `useMediaPlayer()`
- **Functions:** camelCase: `formatTime()`, `uploadFile()`, `handleClick()`
- **Types/Interfaces:** PascalCase: `Segment`, `ApiResponse`, `TranscriptionState`
- **Constants:** UPPER_SNAKE_CASE: `API_BASE_URL`, `POLL_INTERVAL`, `MAX_RETRIES`
- **Files:** PascalCase for components, camelCase for utilities: `api.ts`, `formatters.ts`

**Examples:**
```python
# Backend: app/tasks/transcription.py
from app.ai_services import get_transcription_service

@shared_task
def transcribe_audio(job_id: str, file_path: str) -> dict:
    service = get_transcription_service()
    result = service.transcribe(file_path)
    return {"segments": result}
```

```typescript
// Frontend: src/services/api.ts
export async function fetchTranscriptionStatus(jobId: string): Promise<StatusResponse> {
  const response = await fetch(`${API_BASE_URL}/status/${jobId}`)
  return response.json()
}
```

### API Endpoint Patterns

**REST Convention:**
- Resource-based URLs: `/media/{job_id}` not `/get_media`
- HTTP Methods: GET (read), POST (create/action), PUT (update), DELETE (remove)
- Plural vs Singular: Use singular for resources: `/status/{id}` not `/statuses/{id}`

**All API Endpoints:**

| Method | Endpoint | Purpose | Request Body | Response |
|--------|----------|---------|--------------|----------|
| POST | `/upload` | Upload media file | `multipart/form-data` with `file` field | `{"job_id": "uuid"}` |
| GET | `/status/{job_id}` | Get job status | None | `{"status": "...", "progress": 0-100, ...}` |
| GET | `/result/{job_id}` | Get transcription | None | `{"segments": [{start, end, text}]}` |
| GET | `/media/{job_id}` | Stream media file | None (Range headers) | Media file with Range support |
| POST | `/export/{job_id}` | Export with edits | `{"segments": [...], "format": "srt"\|"txt"}` | File download |

**Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid input (wrong file format, missing fields)
- `404 Not Found`: Job ID doesn't exist
- `500 Internal Server Error`: Server/processing failure

### File Organization Patterns

**Backend:**
- **Route handlers:** Live in `app/main.py` (all endpoints in one file for simplicity)
- **Business logic:** Extract to `app/services/` (file operations, export generation)
- **Background tasks:** Live in `app/tasks/` (Celery worker functions)
- **AI services:** Live in `app/ai_services/` (abstract interface + implementations)
- **Models:** Pydantic models in `app/models.py`
- **Config:** Single `app/config.py` for all settings

**Frontend:**
- **Views (pages):** `src/views/` - one view per route
- **Reusable components:** `src/components/` - shared UI components
- **State management:** `src/stores/` - Pinia stores (one per domain)
- **API client:** `src/services/api.ts` - all backend API calls
- **Types:** `src/types/api.ts` - TypeScript interfaces for API contracts
- **Utilities:** `src/utils/` - formatting, helpers (if needed)

### Component Structure Pattern (Vue)

**Standard Vue SFC Structure:**

```vue
<script setup lang="ts">
// 1. Imports (grouped: Vue, external libs, local)
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTranscriptionStore } from '@/stores/transcription'

// 2. Props and emits
const props = defineProps<{
  jobId: string
}>()

const emit = defineEmits<{
  complete: [result: string]
}>()

// 3. Store and composables
const store = useTranscriptionStore()
const router = useRouter()

// 4. Local state
const isLoading = ref(false)
const error = ref<string | null>(null)

// 5. Computed properties
const formattedStatus = computed(() => {
  return store.status.toUpperCase()
})

// 6. Methods
async function handleAction() {
  isLoading.value = true
  // ... logic
}

// 7. Lifecycle hooks (if any)
onMounted(() => {
  // ... initialization
})
</script>

<template>
  <!-- 1. Root element (single) -->
  <div class="component-name">
    <!-- 2. Content -->
  </div>
</template>

<style scoped>
/* Component-specific styles */
.component-name {
  /* styles */
}
</style>
```

### TypeScript Type Definitions

**Shared Types (src/types/api.ts):**

```typescript
// API Response Types
export interface UploadResponse {
  job_id: string
}

export interface StatusResponse {
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message: string
  created_at: string
  updated_at: string
}

export interface TranscriptionResult {
  segments: Segment[]
}

export interface Segment {
  start: number  // Float seconds
  end: number    // Float seconds
  text: string
}

export interface ExportRequest {
  segments: Segment[]
  format: 'srt' | 'txt'
}
```

**Backend Pydantic Models (app/models.py):**

```python
from pydantic import BaseModel
from typing import Literal

class UploadResponse(BaseModel):
    job_id: str

class StatusResponse(BaseModel):
    status: Literal['pending', 'processing', 'completed', 'failed']
    progress: int
    message: str
    created_at: str
    updated_at: str

class TranscriptionSegment(BaseModel):
    start: float
    end: float
    text: str

class TranscriptionResult(BaseModel):
    segments: list[TranscriptionSegment]

class ExportRequest(BaseModel):
    segments: list[TranscriptionSegment]
    format: Literal['srt', 'txt']
```

### Code Organization Rules

**ALL agents MUST follow these rules:**

1. **Single Responsibility:** Each file/function does ONE thing
2. **DRY (Don't Repeat Yourself):** Extract common logic to services/utils
3. **Type Safety:** All TypeScript code must have explicit types, all Python functions must have type hints
4. **Error Handling:** Every API call must have try/catch (frontend) or exception handling (backend)
5. **No Magic Numbers:** Extract constants: `POLL_INTERVAL = 3000` not `setTimeout(..., 3000)`
6. **Comments:** Only for complex logic, not obvious code
7. **Async/Await:** Use async/await, not .then() chains (frontend)
8. **Imports:** Group by type (Vue, libraries, local), alphabetize within groups
9. **Environment Isolation (Backend):** ALWAYS activate uv virtual environment before Python commands. Verify activation: `which python` must show `.venv/Scripts/python`. Use `uv pip install` for new dependencies (NOT global `pip`)
10. **Environment Verification (All Agents):** Backend stories: Check `python --version` shows 3.12.x from .venv. Frontend stories: Check `npm list --depth=0` shows expected packages. NEVER install packages globally on Windows system Python

**Example (Frontend):**

```typescript
// ✅ GOOD
const POLL_INTERVAL = 3000
const MAX_RETRIES = 5

async function pollStatus(jobId: string) {
  for (let i = 0; i < MAX_RETRIES; i++) {
    try {
      const status = await fetchTranscriptionStatus(jobId)
      if (status.status === 'completed') {
        return status
      }
      await sleep(POLL_INTERVAL)
    } catch (error) {
      console.error('Poll failed:', error)
      throw error
    }
  }
  throw new Error('Max retries exceeded')
}

// ❌ BAD
function pollStatus(jobId) {  // No types
  return fetchTranscriptionStatus(jobId).then(status => {  // .then() chains
    if (status.status === 'completed') {
      return status
    }
    setTimeout(() => pollStatus(jobId), 3000)  // Magic number, no error handling
  })
}
```

### State Management Patterns (Pinia)

**Store Organization:**

```typescript
// stores/transcription.ts
import { defineStore } from 'pinia'

export const useTranscriptionStore = defineStore('transcription', {
  // 1. State
  state: () => ({
    jobId: null as string | null,
    segments: [] as Segment[],
    status: 'pending' as 'pending' | 'processing' | 'completed' | 'failed',
    // ... other state
  }),

  // 2. Getters
  getters: {
    hasSegments: (state) => state.segments.length > 0,
    isProcessing: (state) => state.status === 'processing',
  },

  // 3. Actions
  actions: {
    async uploadFile(file: File) {
      const response = await api.uploadFile(file)
      this.jobId = response.job_id
    },

    async fetchStatus() {
      if (!this.jobId) return
      const response = await api.fetchStatus(this.jobId)
      this.status = response.status
    },
  }
})
```

**Rules:**
- **One store per domain:** `transcription.ts` handles all transcription-related state
- **Actions for async:** All API calls go in actions, not components
- **Getters for derived state:** Don't compute in components, use getters
- **Direct state access in components:** `store.jobId`, not `store.state.jobId`

**Affects:** ALL epics - every agent must follow these patterns

---

## Architectural Coherence Validation

### Decision Compatibility Check

✅ **Technology Stack Compatibility:**
- Python 3.12 + FastAPI 0.120.x: Compatible ✓
- Celery 5.5.3 + Redis 7.x: Compatible ✓
- Vue 3 + TypeScript 5.x + Pinia: Compatible ✓
- WhisperX GPU support + Docker: Compatible ✓

✅ **API Contract Alignment:**
- Backend Pydantic models match Frontend TypeScript interfaces ✓
- Float timestamps (seconds) consistent across backend → frontend → display ✓
- Job ID (UUID v4) format compatible with URLs and Redis keys ✓
- Status enum values identical in both services ✓

✅ **State Management Consistency:**
- Pinia store structure supports click-to-timestamp pattern ✓
- `currentTime` (commanded) vs `playbackTime` (actual) separation prevents loops ✓
- `editingSegmentId` state prevents seek conflicts ✓
- `isPlaying` synced with native player controls ✓

✅ **Performance Requirements Met:**
- NFR001: Transcription 1-2x real-time (WhisperX capability) ✓
- NFR001: UI load <3s (Vite optimized build) ✓
- NFR001: Media playback <2s (HTTP Range requests) ✓
- NFR001: Timestamp seek <1s (throttled updates + incremental search) ✓

### Epic Coverage Validation

| Epic | Architectural Support | Gaps |
|------|---------------------|------|
| Epic 1.1 | Starter templates, project structure, ai_services abstraction | None |
| Epic 1.2 | File storage strategy, upload endpoint, multipart handling | None |
| Epic 1.3 | WhisperXService, Celery tasks, Redis progress tracking | None |
| Epic 1.4 | Status/result endpoints, Redis queries, JSON segment format | None |
| Epic 1.5 | Vue Router, fetch API, file upload component pattern | None |
| Epic 1.6 | Pinia store, polling pattern, progress state management | None |
| Epic 1.7 | SubtitleList component, segment display format | None |
| Epic 2.1 | FileResponse with Range support, media serving | None |
| Epic 2.2 | MediaPlayer component, HTML5 video/audio, state sync | None |
| Epic 2.3 | Click-to-timestamp novel pattern, auto-scroll, seek logic | None |
| Epic 2.4 | Inline editing pattern, editingSegmentId state | None |
| Epic 2.5 | Export service, SRT/TXT generation, data flywheel storage | None |
| Epic 2.6 | Download trigger, file naming convention | None |
| Epic 2.7 | All architectural components | None |

**Result:** All 14 stories have complete architectural support. No gaps detected.

### Pattern Completeness Check

✅ **Naming Patterns Defined:**
- API endpoints: `/upload`, `/status/{job_id}`, etc. ✓
- Python functions: snake_case ✓
- TypeScript functions: camelCase ✓
- Components: PascalCase ✓
- Constants: UPPER_SNAKE_CASE ✓

✅ **Structure Patterns Defined:**
- Backend folder organization ✓
- Frontend folder organization ✓
- Component structure (script/template/style order) ✓
- Import grouping rules ✓

✅ **Format Patterns Defined:**
- API request/response formats ✓
- Transcription segment JSON structure ✓
- Redis key patterns ✓
- TypeScript/Pydantic type definitions ✓

✅ **Communication Patterns Defined:**
- REST API conventions ✓
- HTTP status codes ✓
- CORS configuration ✓
- Frontend API client (fetch) ✓

✅ **Lifecycle Patterns Defined:**
- Job status state machine (pending → processing → completed/failed) ✓
- Player state sync (play/pause events) ✓
- Edit mode lifecycle (setEditingSegment/blocking seeks) ✓

✅ **Location Patterns Defined:**
- Media file storage (`/uploads/{job_id}/original.{ext}`) ✓
- Transcription results storage (`/uploads/{job_id}/transcription.json`) ✓
- Export file naming (`transcript-{job_id}.{ext}`) ✓

✅ **Consistency Patterns Defined:**
- Error handling (HTTPException, try/catch) ✓
- Logging (Python logging module, console.log) ✓
- Date/time (ISO 8601 UTC everywhere) ✓
- Cross-cutting concerns documented ✓

**Result:** All 7 pattern categories fully defined. AI agents have complete guidance.

### Novel Pattern Integration Check

✅ **Click-to-Timestamp Pattern:**
- Integrates with Pinia state management ✓
- Compatible with Vue 3 Composition API ✓
- Uses throttle from lodash-es (dependency to add) ✓
- Meets NFR001 performance requirements ✓
- All edge cases documented and handled ✓

✅ **AI Service Abstraction Pattern:**
- Git submodule strategy defined ✓
- Abstract interface (TranscriptionService) allows swapping ✓
- Compatible with Celery task structure ✓
- Future extensibility (Deepgram, Faster-Whisper) ✓

**Result:** Novel patterns fully integrated and compatible with standard architecture.

### Final Coherence Assessment

**✅ PASS - Architecture is coherent and complete**

- All 10 critical decisions made and documented
- All 14 epics have architectural support
- All 7 pattern categories fully defined
- 2 novel patterns designed and integrated
- No conflicting choices detected
- Performance requirements validated
- Type safety ensured (TypeScript + Pydantic alignment)

**Ready for implementation.**

---

## Summary

**Project:** KlipNote - Zero-friction audio/video transcription with integrated review
**Architecture Approach:** Pragmatic, starter-based, with strategic abstractions
**Novel Features:** Click-to-timestamp synchronization, AI service abstraction layer

### Key Architectural Highlights

1. **Dual Starter Strategy:**
   - Frontend: Official `create-vue` with TypeScript, Router, Pinia
   - Backend: Manual Docker Compose for WhisperX GPU integration flexibility

2. **AI Service Abstraction:**
   - WhisperX as git submodule for upstream tracking
   - Abstract `TranscriptionService` interface for easy swapping
   - Future-proof for Deepgram, Faster-Whisper alternatives

3. **Click-to-Timestamp Pattern:**
   - Bidirectional sync between subtitle list and media player
   - Optimized incremental search (O(1) for linear playback)
   - Auto-scroll, state-aware seeking, edit conflict prevention
   - Throttled updates, comprehensive edge case handling

4. **Data Flywheel Foundation:**
   - Separate storage for original vs human-edited transcriptions
   - Enables continuous model improvement from user corrections
   - Export API captures both versions

5. **Type-Safe Contracts:**
   - Pydantic (backend) and TypeScript (frontend) models mirror each other
   - Explicit API contracts prevent agent mismatches
   - Float seconds for timestamps everywhere (no conversion bugs)

### Implementation Readiness

**All AI agents have:**
- ✅ Complete project structure
- ✅ Explicit naming conventions (Python snake_case, TS camelCase, etc.)
- ✅ Defined API endpoints with request/response formats
- ✅ Component patterns (Vue SFC structure, Pinia organization)
- ✅ Error handling strategy (HTTPException, try/catch)
- ✅ Logging patterns (Python logging, console.*)
- ✅ Performance guidance (throttle, incremental search)
- ✅ Novel pattern implementations (click-to-timestamp, AI abstraction)

**Next Steps:**
1. Review this architecture document
2. Proceed to Epic 1.1: Project scaffolding (run starter commands, setup git submodules)
3. Implement stories sequentially using this architecture as the consistency contract

---

_Generated by BMAD Decision Architecture Workflow v1.3.2_
_Date: 2025-11-03_
_For: Link_
_Project: KlipNote (Level 2)_
