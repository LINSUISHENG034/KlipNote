# Story 1.1: Project Scaffolding and Development Environment

Status: ready-for-dev

## Story

As a developer,
I want the project structure and development environment configured,
so that I can begin building features on a solid foundation.

## Acceptance Criteria

1. Backend: FastAPI project initialized with proper directory structure (api/, models/, services/, tasks/)
2. Frontend: Vue 3 + Vite project initialized with component structure
3. Dependencies installed: FastAPI, Celery, Redis, Vue 3, Vite
4. WhisperX integrated as git submodule at `ai_services/whisperx/`
5. Git repository configured with .gitignore for Python and Node
6. Basic README with setup instructions
7. Local development servers can run (backend on port 8000, frontend on port 5173)

## Tasks / Subtasks

- [ ] Task 1: Initialize backend FastAPI project structure (AC: #1, #3)
  - [ ] Create backend directory structure: app/, app/services/, app/tasks/, app/ai_services/, app/models.py, app/main.py, app/config.py, app/celery_utils.py
  - [ ] Create requirements.txt with dependencies: fastapi==0.120.x, uvicorn, celery[redis]==5.5.3+, redis==5.x, pydantic==2.x, pydantic-settings==2.x, python-multipart, python-ffmpeg, pytest==7.x, pytest-mock==3.x (NOTE: torch and torchaudio installed separately in Dockerfile with CUDA-specific index)
  - [ ] Create Dockerfile for Python 3.12 with GPU support (CUDA 11.8+): Install ffmpeg via apt-get, install torch==2.1.2 torchaudio==2.1.2 with --index-url https://download.pytorch.org/whl/cu118, then install requirements.txt
  - [ ] Create docker-compose.yaml with services: web, worker, redis (with healthcheck: redis-cli ping), flower. Add depends_on with service_healthy condition for web and worker to wait for redis healthcheck
  - [ ] Create .env.example file with template values: CELERY_BROKER_URL, CELERY_RESULT_BACKEND, WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, UPLOAD_DIR, MAX_FILE_SIZE, MAX_DURATION_HOURS, CORS_ORIGINS

- [ ] Task 2: Initialize frontend Vue 3 + Vite project (AC: #2, #3)
  - [ ] Run: `npm create vue@latest klipnote-frontend -- --typescript --router --pinia`
  - [ ] Verify directory structure created: src/, src/components/, src/views/, src/stores/, src/router/, src/services/, src/types/
  - [ ] Install frontend dependencies

- [ ] Task 3: Integrate WhisperX as git submodule (AC: #4)
  - [ ] Add WhisperX as git submodule: `git submodule add https://github.com/m-bain/whisperX.git backend/app/ai_services/whisperx`
  - [ ] Initialize and update submodules: `git submodule update --init --recursive`
  - [ ] Create ai_services/base.py with abstract TranscriptionService interface
  - [ ] Create ai_services/whisperx_service.py implementing TranscriptionService
  - [ ] Create ai_services/__init__.py with service factory pattern

- [ ] Task 4: Configure Git repository (AC: #5)
  - [ ] Create .gitignore for backend (Python, Docker, uploads/, __pycache__, *.pyc, .env)
  - [ ] Create .gitignore for frontend (node_modules/, dist/, .DS_Store)
  - [ ] Add .gitmodules file for WhisperX submodule
  - [ ] Commit initial project structure

- [ ] Task 5: Create basic README with setup instructions (AC: #6)
  - [ ] Document system requirements: NVIDIA GPU with 8GB+ VRAM, CUDA 11.8+, nvidia-docker2, Python 3.12+, Node.js 20.x LTS
  - [ ] Document backend setup: Docker Compose commands, environment variables
  - [ ] Document frontend setup: npm install, npm run dev
  - [ ] Document GPU setup validation steps
  - [ ] Include quick start guide for local development

- [ ] Task 6: Validate development servers run successfully (AC: #7)
  - [ ] Test backend: `docker-compose up` should start web, worker, redis, flower services
  - [ ] Verify backend accessible at http://localhost:8000/docs (FastAPI auto-docs)
  - [ ] Test frontend: `npm run dev` should start Vite dev server at http://localhost:5173
  - [ ] Verify GPU access in worker container: `nvidia-smi` command works
  - [ ] Test Celery worker connection: `celery -A app.celery_utils inspect ping`

- [ ] Task 7: Setup testing infrastructure (Testing Strategy requirement)
  - [ ] Backend: Configure pytest with pytest.ini, create tests/ directory with conftest.py
  - [ ] Frontend: Verify Vitest configured (from create-vue), create initial test structure
  - [ ] Document test execution commands in README

## Dev Notes

### Architectural Patterns and Constraints

**Critical Technical Decisions (Based on Engineering Review):**

1. **FFmpeg Binary Installation (CRITICAL):**
   - `python-ffmpeg` in requirements.txt is only a Python wrapper - it does NOT install the ffmpeg binary
   - WhisperX and torchaudio require the actual ffmpeg command-line tool to process media files
   - **Solution:** Install ffmpeg via apt-get in Dockerfile BEFORE Python dependencies
   - **Failure Mode:** Without this, Story 1.3 transcription tasks will fail immediately with "ffmpeg: command not found"

2. **PyTorch CUDA Version Binding (CRITICAL):**
   - Generic `torch==2.x` from PyPI will install CPU-only version or wrong CUDA version
   - PyTorch must be compiled for the exact CUDA version in the Docker image (11.8)
   - **Solution:** Install PyTorch with CUDA 11.8-specific index URL in Dockerfile: `--index-url https://download.pytorch.org/whl/cu118`
   - **Specific Versions:** torch==2.1.2 torchaudio==2.1.2 (tested with CUDA 11.8)
   - **Failure Mode:** Without this, `torch.cuda.is_available()` returns False, GPU not detected, NFR001 performance targets impossible

3. **Docker Compose Startup Order (IMPORTANT):**
   - Without health checks, web/worker services may start before Redis is ready to accept connections
   - **Solution:** Add Redis health check (`redis-cli ping`) and `depends_on` with `condition: service_healthy` for web/worker
   - **Failure Mode:** Race condition causing web/worker crashes, restart loops, unstable development environment

4. **Environment Variable Template (GOOD PRACTICE):**
   - `.env.example` provides template for required configuration
   - New developers/agents know exactly which variables to configure
   - Variables: CELERY_BROKER_URL, CELERY_RESULT_BACKEND, WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, UPLOAD_DIR, MAX_FILE_SIZE, MAX_DURATION_HOURS, CORS_ORIGINS

**Backend Architecture (FastAPI + Celery + Redis):**
- **Service Separation:** Web service (FastAPI), worker service (Celery), message broker (Redis)
- **AI Service Abstraction:** WhisperX integrated as git submodule with abstract interface pattern for future extensibility (Deepgram, Faster-Whisper alternatives)
- **Configuration Management:** Pydantic Settings loading from .env file (CELERY_BROKER_URL, CELERY_RESULT_BACKEND, WHISPER_MODEL, WHISPER_DEVICE)
- **GPU Environment:** Docker Compose with nvidia-docker2 runtime for GPU access, CUDA 11.8+ required
- **Model Caching:** Docker volume for WhisperX models at /root/.cache/whisperx to avoid re-download

**Frontend Architecture (Vue 3 + Vite):**
- **Starter Template:** Official create-vue with TypeScript, Vue Router, Pinia
- **Build Tooling:** Vite for fast HMR and optimized production builds
- **Project Structure:** src/views/ (pages), src/components/ (reusable UI), src/stores/ (Pinia), src/services/ (API client), src/types/ (TypeScript interfaces)
- **API Client:** Native fetch() API (no external HTTP library)

**Git Submodule Strategy:**
- WhisperX as submodule tracks upstream updates while maintaining version control
- Submodule path: backend/app/ai_services/whisperx/
- Initialize with: `git submodule add` then `git submodule update --init --recursive`

**Testing Infrastructure:**
- Backend: pytest + pytest-mock for unit/integration tests, 70%+ coverage target
- Frontend: Vitest + @vue/test-utils for component tests, 60%+ coverage target
- Test organization defined in architecture.md Testing Strategy section

### Source Tree Components to Touch

**Backend Files to Create:**
```
backend/
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── pytest.ini
├── tests/
│   └── conftest.py
└── app/
    ├── __init__.py
    ├── main.py (FastAPI app initialization, placeholder endpoints)
    ├── config.py (Pydantic Settings)
    ├── celery_utils.py (Celery instance configuration)
    ├── models.py (placeholder for future Pydantic models)
    ├── ai_services/
    │   ├── __init__.py (service factory)
    │   ├── base.py (abstract TranscriptionService)
    │   └── whisperx_service.py (WhisperXService implementation)
    ├── services/
    │   └── __init__.py
    └── tasks/
        └── __init__.py
```

**Critical: Dockerfile Structure (addresses FFmpeg and PyTorch CUDA issues):**
```dockerfile
# Base image with CUDA 11.8 support
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Install system dependencies including ffmpeg (CRITICAL - required by WhisperX)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    ffmpeg \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch with CUDA 11.8 support (CRITICAL - must use specific index URL)
RUN pip install --no-cache-dir \
    torch==2.1.2 \
    torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu118

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Critical: docker-compose.yaml Structure (addresses startup race condition):**
```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 1s
      timeout: 3s
      retries: 30

  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    volumes:
      - ./uploads:/uploads
    depends_on:
      redis:
        condition: service_healthy

  worker:
    build: .
    command: celery -A app.celery_utils worker --loglevel=info
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ./uploads:/uploads
      - whisperx-models:/root/.cache/whisperx
    depends_on:
      redis:
        condition: service_healthy

  flower:
    build: .
    command: celery -A app.celery_utils flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      redis:
        condition: service_healthy

volumes:
  whisperx-models:
```

**Critical: .env.example Template:**
```bash
# Redis Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# WhisperX Configuration
WHISPER_MODEL=large-v2
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# File Storage
UPLOAD_DIR=/uploads
MAX_FILE_SIZE=2147483648  # 2GB in bytes
MAX_DURATION_HOURS=2

# CORS (Development - update for production)
CORS_ORIGINS=["http://localhost:5173"]
```

**Frontend Files Created by create-vue:**
```
frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── .gitignore
├── README.md
└── src/
    ├── main.ts
    ├── App.vue
    ├── router/
    │   └── index.ts
    ├── stores/
    │   (placeholder - will add transcription.ts in Story 1.6)
    ├── views/
    │   (placeholder - will add UploadView, ProgressView, EditorView later)
    ├── components/
    │   (placeholder - will add components in subsequent stories)
    ├── services/
    │   (to be created - will add api.ts in Story 1.2)
    └── types/
        (to be created - will add api.ts for TypeScript interfaces)
```

**Git Files:**
- .gitmodules (defines WhisperX submodule)
- Root .gitignore (if monorepo) or separate .gitignore in backend/ and frontend/

### Testing Standards Summary

**Test Framework Setup (This Story):**
- Backend pytest configuration in pytest.ini
- Frontend Vitest configuration from create-vue starter
- Create initial test directory structure (tests/conftest.py for backend)
- Document test execution commands

**Testing Requirements for Subsequent Stories:**
- Story 1.2+: Write unit/integration tests for each new feature
- All API endpoints: 70%+ backend coverage
- All Vue components: 60%+ frontend coverage
- E2E tests deferred to Story 2.7 (MVP release validation)

**Test Execution Commands (to document in README):**
```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm run test:unit -- --coverage
```

### Project Structure Notes

**Alignment with Unified Project Structure:**
- Backend follows manual Docker Compose pattern (architecture.md decision: "Manual Setup with Docker Compose")
- Frontend follows official create-vue starter structure (architecture.md decision: "Official Vue CLI")
- Project structure documented in architecture.md sections: "Project Structure and Boundaries" and "Starter Template Decisions"
- No conflicts detected - structure aligns with architecture decisions

**Detected Variances:** None - this is the foundational story establishing the structure

### References

- [Source: docs/architecture.md#Starter-Template-Decisions] - Frontend/backend initialization approach
- [Source: docs/architecture.md#Project-Structure-and-Boundaries] - Complete project structure reference
- [Source: docs/architecture.md#AI-Service-Abstraction-Strategy] - WhisperX git submodule pattern and abstract interface
- [Source: docs/architecture.md#GPU-Environment-Requirements] - Docker GPU configuration, CUDA requirements
- [Source: docs/architecture.md#Testing-Strategy] - Test framework setup requirements
- [Source: docs/tech-spec-epic-1.md#Dependencies-and-Integrations] - Exact dependency versions (FastAPI 0.120.x, Celery 5.5.3+, etc.)
- [Source: docs/tech-spec-epic-1.md#Docker-Compose-Architecture] - Docker service configuration details
- [Source: docs/epics.md#Story-1.1] - Acceptance criteria and prerequisites
- [Source: temp/06_story-1-1-recommendation.md] - Engineering review identifying critical ffmpeg binary installation, PyTorch CUDA binding, Docker Compose health checks, and .env.example template requirements

## Dev Agent Record

### Context Reference

- docs/stories/1-1-project-scaffolding-and-development-environment.context.xml

### Agent Model Used

<!-- Model name and version will be added during story execution -->

### Debug Log References

<!-- Debug logs will be added during story execution -->

### Completion Notes List

<!-- Completion notes will be added during story execution by dev agent -->

### File List

<!-- File list (NEW/MODIFIED/DELETED) will be added during story execution by dev agent -->
