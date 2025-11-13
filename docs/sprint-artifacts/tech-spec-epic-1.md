# Epic Technical Specification: Foundation & Core Transcription Workflow

Date: 2025-11-04
Author: Link
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational technical infrastructure for KlipNote by implementing the complete backend API architecture (FastAPI + Celery + WhisperX) and basic Vue 3 frontend interface. This epic delivers end-to-end capability for users to upload media files through a web interface, process them asynchronously using GPU-accelerated WhisperX transcription, and view the resulting time-stamped subtitle segments. Upon completion, the core AI transcription workflow will be validated, proving technical feasibility of the self-hosted GPU approach and establishing the API-first architecture pattern that enables all future development.

## Objectives and Scope

**In Scope:**
- Project scaffolding: FastAPI backend with Docker Compose, Vue 3 frontend with Vite
- WhisperX integration as git submodule with AI service abstraction layer
- Backend upload endpoint accepting multipart/form-data file uploads (MP3, MP4, WAV, M4A)
- File validation (format, duration ≤2 hours, size ≤2GB)
- Celery + Redis async task queue for transcription processing
- WhisperX transcription with word-level timestamps
- Stage-based progress tracking in Redis (5 stages: queued, loading model, transcribing, aligning, complete)
- Status and result API endpoints (GET /status/{job_id}, GET /result/{job_id})
- Frontend upload interface with drag-and-drop support
- Frontend progress monitoring with 3-second polling
- Frontend transcription display showing scrollable subtitle segments with timestamps
- Complete upload → transcribe → display workflow validated end-to-end

**Out of Scope (Deferred to Epic 2):**
- Media playback capabilities (audio/video player integration)
- Click-to-timestamp navigation and subtitle synchronization
- Inline subtitle editing functionality
- Export capabilities (SRT/TXT format generation)
- Data flywheel persistence (original vs edited transcriptions)
- localStorage-based edit recovery
- Concurrent multi-job management UI
- Real-time progress streaming (using polling for MVP)

## System Architecture Alignment

This epic implements the foundational layers of KlipNote's architecture as defined in architecture.md:

**Backend Components:**
- FastAPI web service (main.py) with CORS middleware for cross-origin requests
- Celery worker service for async GPU-bound transcription tasks
- Redis service (dual role: message broker + result backend)
- AI services abstraction layer (ai_services/base.py, ai_services/whisperx_service.py)
- WhisperX as git submodule at ai_services/whisperx/

**Frontend Components:**
- Vue 3 + TypeScript application initialized via create-vue starter
- Vue Router for page navigation (upload → progress → results)
- Pinia store for job state management (job_id, status, segments)
- Native fetch() API for backend communication
- Vite build tooling for fast HMR and optimized production bundles

**Architectural Constraints Honored:**
- Job ID format: UUID v4 for all job references
- File storage: Job-based folder structure at /uploads/{job_id}/
- API response format: Direct JSON with FastAPI standard error format
- Transcription data format: JSON array with float timestamps (seconds)
- Progress tracking: Redis key pattern `job:{job_id}:status` with stage-based messaging
- CORS configuration: Development origins (localhost:5173 ↔ localhost:8000)
- GPU environment: Docker Compose with nvidia-docker2 runtime, CUDA 11.8+
- NFR001 Performance: WhisperX GPU mode targets 1-2x real-time transcription speed

## Detailed Design

### Services and Modules

| Module/Service | Responsibility | Inputs | Outputs | Owner/Location |
|----------------|----------------|--------|---------|----------------|
| **FastAPI Web (main.py)** | HTTP API endpoints, request validation, CORS middleware | HTTP requests, uploaded files | JSON responses, job_id | backend/app/main.py |
| **Celery Worker** | Async task execution, GPU resource management | Job queue messages from Redis | Task results to Redis | backend/app/tasks/transcription.py |
| **Redis Service** | Message broker, result backend, status storage | Celery messages, status updates | Queued jobs, cached results | Docker container (redis:7-alpine) |
| **FileHandler Service** | File upload/storage, path resolution, validation | UploadFile, job_id | File paths, validation results | backend/app/services/file_handler.py |
| **TranscriptionService (Abstract)** | AI transcription interface | audio_path, language | List[Dict] segments | backend/app/ai_services/base.py |
| **WhisperXService** | WhisperX implementation, GPU inference | audio_path | Timestamped segments | backend/app/ai_services/whisperx_service.py |
| **Vue Router** | Client-side navigation | Route paths | Page components | frontend/src/router/index.ts |
| **Pinia Store (transcription)** | Client state management | API responses, user actions | Reactive state | frontend/src/stores/transcription.ts |
| **API Client** | Backend communication | job_id, file objects | Typed responses | frontend/src/services/api.ts |

### Data Models and Contracts

**Backend (Pydantic Models - app/models.py):**

```python
from pydantic import BaseModel
from typing import Literal

class UploadResponse(BaseModel):
    """Response from POST /upload endpoint"""
    job_id: str  # UUID v4 format

class StatusResponse(BaseModel):
    """Response from GET /status/{job_id} endpoint"""
    status: Literal['pending', 'processing', 'completed', 'failed']
    progress: int  # 0-100 percentage
    message: str  # User-facing stage description
    created_at: str  # ISO 8601 UTC timestamp
    updated_at: str  # ISO 8601 UTC timestamp

class TranscriptionSegment(BaseModel):
    """Individual subtitle segment with word-level timestamps"""
    start: float  # Start time in seconds
    end: float    # End time in seconds
    text: str     # Transcribed text content

class TranscriptionResult(BaseModel):
    """Response from GET /result/{job_id} endpoint"""
    segments: list[TranscriptionSegment]
```

**Frontend (TypeScript Interfaces - src/types/api.ts):**

```typescript
export interface UploadResponse {
  job_id: string
}

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

**Redis Data Structures:**

```json
// Key: job:{job_id}:status
// Value: JSON string
{
  "status": "processing",
  "progress": 40,
  "message": "Transcribing audio...",
  "created_at": "2025-11-04T10:30:00Z",
  "updated_at": "2025-11-04T10:31:15Z"
}

// Key: job:{job_id}:result
// Value: JSON string
{
  "segments": [
    {"start": 0.5, "end": 3.2, "text": "Hello, welcome to the meeting."},
    {"start": 3.5, "end": 7.8, "text": "Today we'll discuss quarterly results."}
  ]
}
```

**File System Storage:**

```
/uploads/
  /{job_id}/
    original.{ext}       # Uploaded media file (MP3, MP4, WAV, M4A)
    transcription.json   # WhisperX output (Epic 1 scope)
    # edited.json        # Human edits (Epic 2 scope - data flywheel)
```

### APIs and Interfaces

**API Endpoint Specifications (Epic 1 Scope):**

| Method | Endpoint | Description | Request | Response | Error Codes |
|--------|----------|-------------|---------|----------|-------------|
| POST | `/upload` | Upload media file for transcription | `multipart/form-data` with `file` field | `{job_id: "uuid"}` | 400 (invalid format/duration/size), 500 (storage error) |
| GET | `/status/{job_id}` | Get transcription job status and progress | None | `StatusResponse` JSON | 404 (job not found) |
| GET | `/result/{job_id}` | Retrieve transcription results | None | `TranscriptionResult` JSON | 404 (job not found or incomplete) |

**Detailed Endpoint Specifications:**

**POST /upload**
```python
@app.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile) -> UploadResponse:
    """
    Upload media file and queue transcription job

    Validations:
    - File format: MP3, MP4, WAV, M4A (FFmpeg supported formats)
    - Duration: ≤2 hours (checked via ffprobe)
    - File size: ≤2GB (practical limit)

    Returns:
    - job_id: UUID v4 for tracking transcription progress

    Errors:
    - 400: Unsupported format, excessive duration/size
    - 500: File storage failure, task queue failure
    """
```

**GET /status/{job_id}**
```python
@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str) -> StatusResponse:
    """
    Retrieve current status and progress of transcription job

    Progress Stages:
    - 10%: "Task queued..."
    - 20%: "Loading AI model..."
    - 40%: "Transcribing audio..." (longest stage)
    - 80%: "Aligning timestamps..."
    - 100%: "Processing complete!"

    Returns:
    - status: pending | processing | completed | failed
    - progress: 0-100 integer percentage
    - message: User-friendly stage description
    - timestamps: ISO 8601 UTC strings

    Errors:
    - 404: Job ID not found in Redis
    """
```

**GET /result/{job_id}**
```python
@app.get("/result/{job_id}", response_model=TranscriptionResult)
async def get_result(job_id: str) -> TranscriptionResult:
    """
    Retrieve completed transcription result

    Returns:
    - segments: Array of {start, end, text} objects
      - start/end: Float seconds with decimal precision
      - text: Transcribed subtitle text

    Errors:
    - 404: Job ID not found or job not completed
    - Returns error details if job status is 'failed'
    """
```

**CORS Configuration:**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Celery Task Interface:**
```python
from celery import shared_task

@shared_task(bind=True)
def transcribe_audio(self, job_id: str, file_path: str) -> dict:
    """
    Async transcription task using WhisperX

    Arguments:
    - job_id: UUID v4 for progress/result storage
    - file_path: Absolute path to uploaded media file

    Side Effects:
    - Updates Redis key job:{job_id}:status with progress stages
    - Stores final result in Redis key job:{job_id}:result
    - Saves transcription.json to /uploads/{job_id}/

    Returns:
    - dict: {"segments": [...]} on success

    Error Handling:
    - Catches exceptions, updates status to 'failed'
    - Stores error message in status for user feedback
    """
```

### Workflows and Sequencing

**End-to-End Upload → Transcription → Display Workflow:**

```
1. USER ACTION: Upload File
   ├─> Frontend: UploadView.vue handles file selection
   ├─> Frontend: api.uploadFile() sends multipart POST /upload
   └─> Backend: FastAPI receives file
       ├─> Generate UUID v4 as job_id
       ├─> Validate file format (MP3/MP4/WAV/M4A)
       ├─> Validate duration ≤2 hours (ffprobe)
       ├─> Save to /uploads/{job_id}/original.{ext}
       ├─> Queue Celery task: transcribe_audio.delay(job_id, file_path)
       ├─> Initialize Redis job:{job_id}:status = {status: "pending", progress: 10, ...}
       └─> Return {job_id: "uuid"} to frontend

2. FRONTEND: Navigate to Progress View
   ├─> Router navigates to /progress/{job_id}
   ├─> ProgressView.vue starts polling loop
   └─> Every 3 seconds: api.fetchStatus(job_id)

3. BACKEND: Celery Worker Processes Task
   ├─> Celery picks up task from Redis queue
   ├─> Update status: {status: "processing", progress: 20, message: "Loading AI model..."}
   ├─> WhisperXService.transcribe(file_path) executes:
   │   ├─> Load model (GPU allocation, ~3-10 seconds)
   │   ├─> Update: {progress: 40, message: "Transcribing audio..."}
   │   ├─> Run transcription (1-2x real-time for GPU, ~30-60 min for 1hr audio)
   │   ├─> Update: {progress: 80, message: "Aligning timestamps..."}
   │   └─> Align word-level timestamps (WhisperX feature)
   ├─> Save result to Redis job:{job_id}:result = {segments: [...]}
   ├─> Save result to /uploads/{job_id}/transcription.json
   └─> Update: {status: "completed", progress: 100, message: "Processing complete!"}

4. FRONTEND: Poll Detects Completion
   ├─> api.fetchStatus(job_id) returns status: "completed"
   ├─> Stop polling loop
   ├─> Router navigates to /results/{job_id}
   └─> EditorView.vue loads

5. DISPLAY: Fetch and Render Results
   ├─> EditorView.vue: api.fetchResult(job_id)
   ├─> Backend: GET /result/{job_id} returns TranscriptionResult
   ├─> Pinia store updates: store.segments = response.segments
   └─> SubtitleList.vue renders scrollable segments with timestamps
```

**Error Handling Workflow:**

```
Error During Upload:
   ├─> Backend validation fails (format/duration/size)
   └─> Return 400 with {"detail": "Human-readable error message"}
       └─> Frontend displays error toast/message

Error During Transcription:
   ├─> WhisperX throws exception (GPU error, corrupted file, etc.)
   ├─> Celery task catches exception
   ├─> Update Redis: {status: "failed", message: "Transcription failed: {error}"}
   └─> Frontend poll detects failed status
       └─> Display error message with retry option

Job ID Not Found:
   ├─> User requests non-existent job_id
   ├─> Backend queries Redis, no key found
   └─> Return 404 with {"detail": "Job not found"}
       └─> Frontend displays "Job not found" error
```

**Data Flow Diagram (Text-based):**

```
┌─────────────┐                                    ┌─────────────┐
│   Browser   │                                    │  FastAPI    │
│  (Vue 3)    │                                    │   Server    │
└──────┬──────┘                                    └──────┬──────┘
       │                                                  │
       │ POST /upload (multipart file)                   │
       │────────────────────────────────────────────────>│
       │                                                  │ Save file
       │                                                  │ Queue task
       │                                                  │
       │<────────────────────────────────────────────────│
       │              {job_id: "uuid"}                    │
       │                                                  │
       │                                           ┌──────▼──────┐
       │                                           │   Celery    │
       │                                           │   Worker    │
       │                                           └──────┬──────┘
       │                                                  │
       │                                                  │ Transcribe
       │                                                  │ with WhisperX
       │                                                  │
       │                                           ┌──────▼──────┐
       │                                           │    Redis    │
       │                                           │  (status &  │
       │                                           │   result)   │
       │                                           └──────┬──────┘
       │                                                  │
       │ GET /status/{job_id} (every 3s)                 │
       │────────────────────────────────────────────────>│
       │                                                  │ Query Redis
       │<────────────────────────────────────────────────│
       │      {status:"processing", progress: 40}        │
       │                                                  │
       │ ... (polling continues) ...                     │
       │                                                  │
       │ GET /status/{job_id}                            │
       │────────────────────────────────────────────────>│
       │<────────────────────────────────────────────────│
       │      {status:"completed", progress: 100}        │
       │                                                  │
       │ GET /result/{job_id}                            │
       │────────────────────────────────────────────────>│
       │                                                  │ Query Redis
       │<────────────────────────────────────────────────│
       │        {segments: [{start, end, text}, ...]}    │
       │                                                  │
       │ RENDER: SubtitleList component                  │
       │                                                  │
```

## Non-Functional Requirements

### Performance

**NFR001: Processing and Response Time Targets**

| Operation | Target | Epic 1 Implementation |
|-----------|--------|-----------------------|
| Transcription Processing | 1-2x real-time (1 hour audio = 30-60 min) | WhisperX GPU mode (large-v2 model) with CUDA 11.8+ |
| UI Load Time | <3 seconds | Vite optimized build, code splitting, minimal dependencies |
| Media Playback Start | <2 seconds (Epic 2) | N/A for Epic 1 scope |
| Timestamp Seek Response | <1 second (Epic 2) | N/A for Epic 1 scope |
| API Response Time | <500ms for status/result queries | Redis in-memory lookups, minimal processing |
| File Upload | Streaming upload, progress feedback | FastAPI streaming upload, chunked transfer |

**Performance Implementation Details:**

- **GPU Acceleration:** WhisperX configured with CUDA device, float16 compute type
- **Model Caching:** Docker volume persists WhisperX models at /root/.cache/whisperx to avoid re-download
- **Redis Response:** In-memory key-value lookups complete in <10ms
- **Frontend Optimization:** Vite production build with tree-shaking, async component loading
- **Polling Throttle:** 3-second interval balances responsiveness with server load

### Security

**NFR002: Authentication and Authorization**

- **MVP Scope:** No authentication required (internal corporate deployment assumed)
- **Access Control:** Network-level security (firewall, VPN) handles access restriction
- **Future Consideration:** User authentication deferred to post-MVP (PRD out-of-scope section)

**Input Validation:**

- **File Upload Validation:**
  - File format whitelist: MP3, MP4, WAV, M4A (reject all other MIME types)
  - File size limit: 2GB maximum (prevent resource exhaustion)
  - Duration validation: ≤2 hours via ffprobe (prevent excessive GPU usage)
  - Filename sanitization: UUID-based storage prevents path traversal attacks

- **API Parameter Validation:**
  - job_id format: UUID v4 validation (prevents injection attacks)
  - Pydantic models enforce type safety on all endpoints
  - HTTPException with clear error messages (no stack trace exposure)

**Data Handling:**

- **File Storage Security:**
  - Uploaded files stored in isolated /uploads directory
  - Job-based folder structure prevents cross-job access
  - Original filenames discarded (use job_id for storage)

- **Sensitive Data:**
  - No PII collection in Epic 1 (transcription content only)
  - No logging of transcription content (only job_id, status, errors)

- **CORS Policy:**
  - Development: Restricted to localhost:5173 origin
  - Production: Configure specific allowed origin(s), never use wildcard "*"

**Threat Mitigation:**

| Threat | Mitigation Strategy |
|--------|---------------------|
| Path Traversal | UUID-based file storage, no user-controlled paths |
| Command Injection | No shell command execution with user input; ffprobe uses safe API |
| XSS | Vue 3 auto-escapes template output by default |
| CSRF | Not applicable (no sessions/cookies in MVP) |
| DoS via Large Files | 2GB file size limit, 2-hour duration limit |
| Malicious File Upload | MIME type validation, ffprobe pre-processing check |

### Reliability/Availability

**NFR003: Completion Rate and Error Recovery**

**Target:** 90%+ transcription completion rate (successful upload → export)

**Reliability Strategies:**

- **Task Retry Logic:**
  - Celery configured with automatic retry on transient failures
  - Max retries: 3 attempts with exponential backoff
  - Permanent failures (corrupted file, unsupported codec) marked as 'failed' immediately

- **Error State Management:**
  - All errors captured in Redis job:{job_id}:status with descriptive messages
  - Frontend polls detect failed status and display user-friendly error messages
  - Error logging includes job_id, timestamp, exception details for debugging

- **Graceful Degradation:**
  - GPU unavailable → Celery task fails with clear error (CPU mode not production-ready)
  - Redis unavailable → FastAPI returns 500 error, frontend displays retry option
  - Disk full → Upload endpoint returns 500, user notified to contact admin

**Data Durability:**

- **Upload Files:** Persisted to disk at /uploads/{job_id}/original.{ext}
- **Transcription Results:** Dual storage (Redis + disk JSON file) ensures durability
- **Redis Persistence:** Configure RDB snapshots (save 900 1, save 300 10) for recovery
- **No Data Loss Guarantee:** Files persist across container restarts via Docker volumes

**Frontend Resilience:**

- **Browser Refresh:** Navigation loss acceptable for Epic 1 (job_id in URL allows manual recovery)
- **Epic 2 Enhancement:** localStorage persistence for edit recovery (deferred)
- **Network Errors:** Fetch API catches errors, displays "Connection failed, retrying..."
- **Polling Resilience:** Continue polling on transient 500 errors, stop only on 404 or user action

**Availability Targets:**

- **MVP Scope:** Single-server deployment, no high availability requirements
- **Expected Uptime:** Best-effort (internal corporate tool)
- **Recovery Time:** Manual Docker container restart, <5 minute recovery
- **Future Enhancement:** Load balancing, multi-worker deployment (post-MVP)

### Observability

**Logging Requirements:**

- **Backend Logging (Python logging module):**
  - **INFO Level:**
    - Job lifecycle events: "Job {job_id} created", "Transcription started", "Transcription completed"
    - API requests: "{method} {endpoint} - {status_code} - {duration_ms}ms"
    - Worker events: "Celery worker started", "Task {task_id} received"
  - **ERROR Level:**
    - Transcription failures: "WhisperX failed for job {job_id}: {error}" with exc_info=True
    - File operation errors: "Failed to save file {path}: {error}"
    - Redis connection errors: "Redis unavailable: {error}"
  - **Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
  - **Output:** stdout (Docker captures for log aggregation)

- **Frontend Logging:**
  - **Development:** console.log() for debugging, console.error() for errors
  - **Production:** Minimal logging, errors only (no sensitive data)
  - **No external logging service for MVP** (Sentry deferred to post-MVP)

**Metrics and Monitoring:**

- **Celery Flower Dashboard:**
  - URL: http://localhost:5555 (development)
  - Provides real-time view of:
    - Active tasks, queued tasks, completed tasks
    - Worker status and resource usage
    - Task execution time histograms
    - Failure rates and error logs

- **Key Metrics to Monitor:**
  - Transcription processing time (per job)
  - Task queue depth (number of pending jobs)
  - Success/failure rate (completed vs failed status)
  - GPU utilization (via nvidia-smi if available)
  - Disk usage in /uploads directory

- **Health Check Endpoints (Future):**
  - GET /health → {status: "ok", redis: "connected", worker: "active"}
  - Not implemented in Epic 1 (add in future iterations)

**Debugging Support:**

- **Job Tracing:**
  - job_id present in all logs for end-to-end tracing
  - Redis keys: job:{job_id}:status and job:{job_id}:result queryable via redis-cli
  - File artifacts preserved at /uploads/{job_id}/ for manual inspection

- **FastAPI Auto-Generated Documentation:**
  - Swagger UI: http://localhost:8000/docs
  - ReDoc: http://localhost:8000/redoc
  - Interactive API testing without Postman

- **Error Transparency:**
  - User-facing error messages in frontend (non-technical language)
  - Detailed error logs on backend (technical details for developers)
  - No stack traces exposed to users (security best practice)

## Dependencies and Integrations

**Backend Dependencies (Python 3.12+):**

| Package | Version | Purpose | Epic 1 Scope |
|---------|---------|---------|--------------|
| fastapi | 0.120.x | Web framework, API endpoints, auto-docs | ✓ Core |
| uvicorn | latest | ASGI server for FastAPI | ✓ Core |
| celery | 5.5.3+ | Async task queue | ✓ Core |
| redis | 5.x | Python Redis client | ✓ Core |
| pydantic | 2.x | Data validation, settings management | ✓ Core |
| pydantic-settings | 2.x | Environment variable configuration | ✓ Core |
| python-multipart | latest | Multipart file upload handling | ✓ Core |
| python-ffmpeg | latest | Media file validation (duration check) | ✓ Story 1.2 |
| whisperx | latest (git submodule) | AI transcription engine | ✓ Story 1.3 |
| torch | 2.x | PyTorch for WhisperX | ✓ Story 1.3 |
| torchaudio | latest | Audio processing | ✓ Story 1.3 |
| pytest | 7.x | Testing framework | ✓ Story 1.1 |
| pytest-mock | 3.x | Mocking for tests | ✓ Story 1.1 |

**Frontend Dependencies (Node.js 20.x LTS):**

| Package | Version | Purpose | Epic 1 Scope |
|---------|---------|---------|--------------|
| vue | 3.x | Frontend framework | ✓ Core |
| vue-router | 4.x | Client-side routing | ✓ Story 1.5 |
| pinia | latest | State management | ✓ Story 1.6 |
| typescript | 5.x | Type safety | ✓ Core |
| vite | latest | Build tool, dev server | ✓ Core |
| vitest | latest | Testing framework | ✓ Story 1.1 |
| @vue/test-utils | latest | Component testing | ✓ Story 1.1 |

**Infrastructure Dependencies:**

| Service | Version | Purpose | Epic 1 Scope |
|---------|---------|---------|--------------|
| Redis | 7.x-alpine | Message broker, result backend, caching | ✓ Core |
| Docker | 24.x+ | Containerization | ✓ Core |
| Docker Compose | 2.x+ | Multi-container orchestration | ✓ Core |
| nvidia-docker2 | latest | GPU access in Docker | ✓ Story 1.1 |
| CUDA | 11.8+ or 12.1+ | GPU acceleration for WhisperX | ✓ Story 1.3 |

**Git Submodule Integration:**

```bash
# WhisperX as git submodule
git submodule add https://github.com/m-bain/whisperX.git backend/app/ai_services/whisperx
git submodule update --init --recursive
```

**External Integrations:**

- **WhisperX Repository:** https://github.com/m-bain/whisperX (MIT License)
- **FFmpeg:** System dependency for media file inspection (already in WhisperX container)
- **NVIDIA GPU Drivers:** Host system requirement for CUDA support

**Configuration Management:**

```python
# backend/app/config.py (Pydantic Settings)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    # WhisperX
    WHISPER_MODEL: str = "large-v2"
    WHISPER_DEVICE: str = "cuda"  # or "cpu" for dev
    WHISPER_COMPUTE_TYPE: str = "float16"

    # File Storage
    UPLOAD_DIR: str = "/uploads"
    MAX_FILE_SIZE: int = 2 * 1024 * 1024 * 1024  # 2GB
    MAX_DURATION_HOURS: int = 2

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    class Config:
        env_file = ".env"
```

**Docker Compose Architecture:**

```yaml
services:
  web:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/uploads
    depends_on:
      - redis

  worker:
    build: ./backend
    command: celery -A app.celery_utils worker
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ./uploads:/uploads
      - whisperx-models:/root/.cache/whisperx
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  flower:
    build: ./backend
    command: celery -A app.celery_utils flower
    ports:
      - "5555:5555"
    depends_on:
      - redis

volumes:
  whisperx-models:
```

## Acceptance Criteria (Authoritative)

**Epic-Level Success Criteria:**

1. ✓ Complete backend API architecture operational (FastAPI + Celery + Redis + WhisperX)
2. ✓ Frontend application functional (Vue 3 + TypeScript + Vite + Router + Pinia)
3. ✓ End-to-end workflow validated: User uploads file → System transcribes → User views results
4. ✓ GPU-accelerated transcription achieves NFR001 performance (1-2x real-time speed)
5. ✓ All 7 stories completed with acceptance criteria met
6. ✓ Project scaffolding, development environment, and testing infrastructure established

**Story-Level Acceptance Criteria:**

**Story 1.1: Project Scaffolding and Development Environment**
1. Backend: FastAPI project initialized with directory structure (api/, models/, services/, tasks/)
2. Frontend: Vue 3 + Vite project initialized with component structure
3. Dependencies installed: FastAPI, Celery, Redis, Vue 3, Vite
4. WhisperX integrated as git submodule at `ai_services/whisperx/`
5. Git repository configured with .gitignore for Python and Node
6. Basic README with setup instructions
7. Local development servers can run (backend port 8000, frontend port 5173)

**Story 1.2: Backend API Upload Endpoint**
1. POST /upload endpoint accepts multipart/form-data file uploads
2. Validates file formats (MP3, MP4, WAV, M4A minimum)
3. Validates media duration using ffprobe - rejects files exceeding 2 hours (NFR-004)
4. Returns unique job_id for tracking
5. Saves uploaded file to server storage with job_id reference
6. Returns 400 error with clear message for unsupported formats or excessive duration
7. Handles files up to 2GB size (tested with actual 2GB file)
8. API endpoint documented in FastAPI auto-docs (/docs)

**Story 1.3: Celery Task Queue and WhisperX Integration**
1. Celery configured with Redis broker
2. Transcription task accepts job_id and file path parameters
3. WhisperX integration transcribes media file with word-level timestamps
4. Task updates progress in Redis with stage-based messages:
   - Stage 1 (progress: 10): "Task queued..."
   - Stage 2 (progress: 20): "Loading AI model..."
   - Stage 3 (progress: 40): "Transcribing audio..." (longest stage)
   - Stage 4 (progress: 80): "Aligning timestamps..."
   - Stage 5 (progress: 100): "Processing complete!"
5. Task stores transcription result as JSON with subtitle segments [{start, end, text}]
6. Task handles transcription errors and stores error state with descriptive message
7. Celery worker can be started and processes jobs successfully

**Story 1.4: Status and Result API Endpoints**
1. GET /status/{job_id} endpoint returns {status: "pending"|"processing"|"completed"|"failed", progress: 0-100}
2. GET /result/{job_id} endpoint returns transcription JSON with subtitle array
3. Status endpoint returns 404 for non-existent job_id
4. Result endpoint returns 404 if job not completed
5. Result endpoint returns error details if job failed
6. Both endpoints documented in FastAPI auto-docs

**Story 1.5: Frontend Upload Interface**
1. Landing page displays file upload form with clear instructions
2. File input accepts audio/video formats (validated client-side)
3. Upload button triggers POST /upload API call
4. Success: Stores job_id and navigates to progress page
5. Failure: Displays error message from API
6. UI works on desktop, tablet, and mobile browsers
7. Basic responsive layout (no advanced styling required for MVP)
8. Drag-and-drop file upload supported (drop zone with visual feedback)

**Story 1.6: Frontend Progress Monitoring**
1. Progress page polls GET /status/{job_id} every 3 seconds
2. Progress bar or percentage displayed visually
3. Status message shows current state ("Uploading...", "Processing...", "Complete!")
4. On completion: Automatically navigates to results view
5. On error: Displays error message with retry option
6. User can safely navigate away and return using job_id (in URL)
7. Polling stops when job completes or fails

**Story 1.7: Frontend Transcription Display**
1. Results page calls GET /result/{job_id} on load
2. Displays subtitle segments as scrollable list
3. Each segment shows timestamp (MM:SS format) and text
4. Clear visual separation between subtitle segments
5. Handles long transcriptions (100+ segments) with smooth scrolling
6. Loading state while fetching results
7. Error handling if result fetch fails

## Traceability Mapping

| AC ID | Acceptance Criterion | Spec Section(s) | Component(s)/API(s) | Test Idea |
|-------|---------------------|-----------------|---------------------|-----------|
| **Story 1.1** ||||
| 1.1.1 | Backend FastAPI project initialized | Dependencies, Services | backend/app/main.py | Verify directory structure exists |
| 1.1.2 | Frontend Vue 3 project initialized | Dependencies, Services | frontend/src/main.ts | Verify npm run dev starts successfully |
| 1.1.3 | Dependencies installed | Dependencies | requirements.txt, package.json | Test import statements work |
| 1.1.4 | WhisperX as git submodule | Dependencies, AI Services | ai_services/whisperx/ | Verify git submodule status |
| 1.1.5 | Git repository configured | N/A | .gitignore | Verify uploads/ and node_modules/ ignored |
| 1.1.6 | README with setup instructions | N/A | README.md | Manual review of documentation |
| 1.1.7 | Dev servers run successfully | N/A | FastAPI + Vite | Integration test: curl localhost:8000/docs |
| **Story 1.2** ||||
| 1.2.1 | POST /upload accepts multipart | APIs, Data Models | POST /upload, FileHandler | Test upload with FormData |
| 1.2.2 | Validates file formats | Security, APIs | FileHandler.validate_format() | Test MP3 accepted, .exe rejected |
| 1.2.3 | Validates duration ≤2 hours | Security, APIs | FileHandler.validate_duration() | Test 1hr accepted, 3hr rejected |
| 1.2.4 | Returns unique job_id | APIs, Data Models | UploadResponse | Assert UUID v4 format |
| 1.2.5 | Saves file to storage | Data Models, Services | FileHandler.save_upload() | Verify file exists at /uploads/{job_id}/ |
| 1.2.6 | Returns 400 on validation failure | APIs, Security | HTTPException | Test error message clarity |
| 1.2.7 | Handles 2GB files | Performance, APIs | FileHandler | Upload actual 2GB file, verify success |
| 1.2.8 | Documented in /docs | APIs | FastAPI auto-docs | Navigate to /docs, verify endpoint listed |
| **Story 1.3** ||||
| 1.3.1 | Celery configured with Redis | Dependencies, Services | celery_utils.py | Test celery inspect ping |
| 1.3.2 | Task accepts job_id, file_path | APIs, Data Models | transcribe_audio task | Unit test with mocked WhisperX |
| 1.3.3 | WhisperX transcribes with timestamps | Services, AI Services | WhisperXService.transcribe() | Integration test with test audio file |
| 1.3.4 | Stage-based progress updates | Data Models, Workflows | Redis job:{job_id}:status | Verify 5 progress stages occur |
| 1.3.5 | Stores result as JSON segments | Data Models | Redis + transcription.json | Assert segments format matches spec |
| 1.3.6 | Handles errors gracefully | Reliability, Services | Task exception handling | Test with corrupted audio file |
| 1.3.7 | Celery worker processes jobs | Workflows | Celery worker service | End-to-end test with real job |
| **Story 1.4** ||||
| 1.4.1 | GET /status returns status/progress | APIs, Data Models | GET /status/{job_id} | Test all status values |
| 1.4.2 | GET /result returns segments | APIs, Data Models | GET /result/{job_id} | Assert segments array present |
| 1.4.3 | Status returns 404 for missing job | APIs, Reliability | GET /status/{job_id} | Test with random UUID |
| 1.4.4 | Result returns 404 if incomplete | APIs | GET /result/{job_id} | Test with "processing" status job |
| 1.4.5 | Result returns error details if failed | APIs, Reliability | GET /result/{job_id} | Test with failed job |
| 1.4.6 | Both endpoints in /docs | APIs | FastAPI auto-docs | Manual verification |
| **Story 1.5** ||||
| 1.5.1 | Upload form displayed | Services | UploadView.vue | Component test: verify form rendered |
| 1.5.2 | File input validates formats | Services | FileUpload.vue | Test .mp3 accepted, .txt rejected |
| 1.5.3 | Upload button triggers API | Services, APIs | api.uploadFile() | Mock API, verify POST call made |
| 1.5.4 | Success navigates to progress | Workflows | Vue Router | Test navigation after 200 response |
| 1.5.5 | Failure displays error | Reliability | Error handling | Test with 400 response, verify toast |
| 1.5.6 | Works on multiple browsers | Performance, NFR004 | Responsive layout | Cross-browser E2E tests |
| 1.5.7 | Responsive layout | Performance | CSS media queries | Test on mobile/tablet viewports |
| 1.5.8 | Drag-and-drop supported | Services | FileUpload.vue | Test drop event handler |
| **Story 1.6** ||||
| 1.6.1 | Polls every 3 seconds | Workflows, Performance | ProgressView.vue | Verify polling interval timing |
| 1.6.2 | Progress bar displayed | Services | ProgressBar.vue | Component test: render with progress prop |
| 1.6.3 | Status message updated | Services, Data Models | ProgressView.vue | Test message changes with status |
| 1.6.4 | Auto-navigates on completion | Workflows | Vue Router | Mock completed status, verify route change |
| 1.6.5 | Displays error with retry | Reliability | Error handling | Test failed status, verify retry button |
| 1.6.6 | URL contains job_id | Workflows | Vue Router | Verify route params |
| 1.6.7 | Polling stops appropriately | Workflows | ProgressView.vue | Test cleanup on unmount |
| **Story 1.7** ||||
| 1.7.1 | Calls GET /result on load | Workflows, APIs | EditorView.vue, api.ts | Mock API, verify call on mount |
| 1.7.2 | Scrollable subtitle list | Services | SubtitleList.vue | Render 100+ segments, test scrolling |
| 1.7.3 | Timestamp + text displayed | Data Models, Services | SubtitleList.vue | Verify MM:SS formatting |
| 1.7.4 | Visual segment separation | Services | CSS styling | Visual regression test |
| 1.7.5 | Handles long transcriptions | Performance, Services | SubtitleList.vue | Performance test with 500 segments |
| 1.7.6 | Loading state shown | Services | EditorView.vue | Test isLoading reactive variable |
| 1.7.7 | Error handling on fetch failure | Reliability | Error handling | Mock 404 response, verify error display |

## Risks, Assumptions, Open Questions

**Risks:**

| ID | Risk | Impact | Likelihood | Mitigation Strategy |
|----|------|--------|------------|---------------------|
| R1 | Large file upload (2GB) fails with memory/timeout issues | High | Medium | Story 1.2 AC7 mandates actual 2GB upload test. Configure nginx/FastAPI timeouts (30min). Monitor memory during testing. Accept risk for MVP if upload streaming works. Document file size limits in UI. Future: Implement chunked upload (tus.io). |
| R2 | GPU unavailable during development/testing | High | Medium | Implement CPU fallback mode in WhisperXService with device auto-detection. Document performance degradation (4-6x slower). Story 1.1 validates GPU setup. |
| R3 | WhisperX model download fails on first run | Medium | Low | Celery task handles model download errors gracefully. Retry logic with exponential backoff. Update progress message: "Downloading AI model..." |
| R4 | Transcription quality insufficient for use case | High | Low | WhisperX chosen for proven accuracy (architecture decision). Accept risk for MVP. Future: Fine-tuning with data flywheel (Epic 2). |
| R5 | Concurrent job processing overwhelms GPU memory | Medium | Medium | MVP scope: Sequential processing (single worker). Document concurrency limits in README. Future: Queue management with max concurrent tasks. |
| R6 | Redis data loss on container restart | Medium | Low | Configure Redis RDB snapshots (save 900 1). Docker volumes persist data. Acceptable data loss window for MVP (ephemeral jobs). Future: Redis AOF persistence. |

**Assumptions:**

| ID | Assumption | Validation Strategy |
|----|------------|---------------------|
| A1 | Internal corporate deployment with network-level security | Confirmed in PRD scope. No authentication required for MVP. |
| A2 | Users have access to Chrome 90+, Firefox 88+, Safari 14+, or Edge 90+ | NFR004 compatibility requirement. Cross-browser testing in Story 2.7 (Epic 2). |
| A3 | GPU with 8GB+ VRAM available on deployment server | Architecture GPU environment section specifies requirement. Story 1.1 validates GPU availability. |
| A4 | Average meeting duration 30-60 minutes (not 2 hour max) | PRD user journey uses 45-minute example. 2-hour limit is safety boundary. |
| A5 | FFmpeg already installed in WhisperX Docker container | WhisperX dependency. Verify during Story 1.1 setup. |
| A6 | Single-server deployment sufficient for MVP user base (10-20 users) | PRD project goals specify 10-20 user validation. Load balancing deferred to post-MVP. |

**Open Questions:**

| ID | Question | Resolution Approach | Blocked Story |
|----|----------|---------------------|---------------|
| Q1 | What error message should display if GPU runs out of memory during transcription? | Design user-friendly message in Story 1.3 implementation: "Transcription failed: File too large for processing. Try shorter recording or contact administrator." | None |
| Q2 | Should we limit concurrent uploads or allow unlimited queuing? | Defer to Epic 2 or post-MVP. For Epic 1, allow unlimited queuing (Redis handles scale). Monitor in production. | None |
| Q3 | How long should transcription results persist in Redis/disk? | MVP: Indefinite persistence (manual cleanup). Future: TTL-based cleanup or user-initiated deletion. | None |
| Q4 | Should progress polling continue if user navigates away from tab? | Epic 1: Polling stops on page unload (simplest). Epic 2 localStorage enables resume. | None |
| Q5 | What is acceptable transcription word error rate (WER)? | Defer to production metrics. WhisperX benchmarks show <5% WER on clean audio. Monitor via data flywheel in Epic 2. | None |

## Test Strategy Summary

**Testing Framework Setup (Story 1.1):**

- **Backend:** pytest + pytest-mock for unit/integration tests
- **Frontend:** Vitest + @vue/test-utils for component tests
- **E2E:** Playwright for end-to-end workflow tests (deferred to Story 2.7 in Epic 2)

**Test Coverage Targets:**

- Backend API endpoints: 70%+ code coverage
- Backend services/tasks: 70%+ code coverage
- Frontend components: 60%+ code coverage
- Critical paths (upload → transcribe → display): 80%+ coverage

**Test Levels and Scope:**

**1. Unit Tests**

**Backend (pytest):**
- File validation logic (format, duration, size checks)
- UUID generation and validation
- Pydantic model serialization/deserialization
- Error handling and exception cases
- WhisperX service abstraction (mocked, no GPU)

**Frontend (Vitest):**
- Component rendering (FileUpload, ProgressBar, SubtitleList)
- Timestamp formatting utilities (seconds → MM:SS)
- API client functions (mocked fetch responses)
- Pinia store actions and getters
- Form validation logic

**2. Integration Tests**

**Backend:**
- API endpoint tests with TestClient (FastAPI)
- POST /upload → verify file saved, job_id generated, task queued
- GET /status → verify Redis query works
- GET /result → verify JSON response format
- Celery task execution with mocked WhisperX (no actual transcription)
- Redis connection and data persistence

**Frontend:**
- Component integration (UploadView + FileUpload interaction)
- Router navigation flows (upload → progress → results)
- Pinia store integration with components
- API client integration with mock server (MSW)

**3. End-to-End Tests (Deferred to Epic 2, Story 2.7)**

- Complete upload → transcribe → display workflow
- Error scenarios (invalid file, failed transcription)
- Cross-browser testing (Chrome, Firefox, Safari, Edge)
- Mobile responsive testing

**4. Manual Testing**

- GPU setup verification (nvidia-smi, Docker GPU access)
- WhisperX model download on first run
- 2GB file upload test (Story 1.2 AC7)
- Transcription quality validation with real audio files
- UI/UX review on different screen sizes

**Mock Strategies:**

| Component | Mock Approach | Rationale |
|-----------|---------------|-----------|
| WhisperX | pytest-mock to mock WhisperXService.transcribe() | Avoid GPU dependency in CI/CD, fast tests |
| Redis | fakeredis library for in-memory Redis | Fast, isolated tests without Redis container |
| File System | pytest tmp_path fixture | Isolated temp directories for upload tests |
| Frontend API | MSW (Mock Service Worker) | Intercept fetch calls, simulate backend responses |

**Test Data:**

- **Audio Files:** Create fixtures/ directory with test audio files:
  - `test-short.mp3` (10 seconds, valid)
  - `test-long.mp3` (5 minutes, valid)
  - `test-corrupted.mp3` (corrupted data, should fail transcription)
  - `test-large.mp4` (2GB, for Story 1.2 AC7 validation)
- **Transcription Results:** JSON fixtures with known segment data for frontend tests

**Continuous Integration (Future Enhancement):**

```yaml
# .github/workflows/test.yml (example structure)
name: Test Suite
on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run pytest
        run: |
          cd backend
          pytest tests/ --cov=app --cov-report=xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Vitest
        run: |
          cd frontend
          npm install
          npm run test:unit -- --coverage
```

**Story-Specific Testing Requirements:**

| Story | Test Requirements | Tools |
|-------|------------------|-------|
| 1.1 | Verify project structure, dev servers start | Manual verification, shell scripts |
| 1.2 | API upload endpoint tests (format, duration, size validation) | pytest, TestClient, tmp_path |
| 1.3 | Celery task tests with mocked WhisperX | pytest, pytest-mock, fakeredis |
| 1.4 | Status/result API tests (404, error states) | pytest, TestClient, fakeredis |
| 1.5 | FileUpload component tests (validation, events) | Vitest, @vue/test-utils |
| 1.6 | ProgressView polling tests (interval, navigation) | Vitest, MSW |
| 1.7 | SubtitleList rendering tests (segments, scrolling) | Vitest, @vue/test-utils |

**Test Execution Commands:**

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test:unit -- --coverage

# E2E tests (Epic 2)
npx playwright test
```

**Definition of Done (Testing Perspective):**

- ✓ All unit tests pass
- ✓ All integration tests pass
- ✓ Code coverage targets met (70% backend, 60% frontend)
- ✓ Manual testing checklist completed for critical paths
- ✓ No critical bugs blocking story completion
- ✓ Test fixtures committed to repository
