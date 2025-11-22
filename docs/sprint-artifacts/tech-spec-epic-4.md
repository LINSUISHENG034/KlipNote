# Epic Technical Specification: Multi-Model Transcription Framework & Composable Enhancements

Date: 2025-11-15
Author: Link
Epic ID: 4
Status: Draft

---

## Overview

Epic 4 operationalizes the multi-model architecture foundation established in Epic 3 by enabling production deployment of both BELLE-2 and WhisperX transcription models with isolated runtime environments. Building on the pluggable optimizer architecture (Story 3.2a), this epic evolves the framework toward model-agnostic enhancement components that work across any transcription engine. The core challenge addressed is PyTorch dependency conflicts (BELLE-2 requires CUDA 11.8/PyTorch <2.6, WhisperX requires CUDA 12.x/PyTorch ≥2.6) while enabling runtime model selection and composable enhancement pipelines (VAD preprocessing, timestamp refinement, segment splitting).

This epic transforms KlipNote from a single-model MVP into a production-grade multi-model platform where users and administrators can select optimal transcription engines and enhancement configurations based on content characteristics (language, audio quality, use case). The deliverable provides strategic flexibility: support multiple models today, easily integrate future models (SenseVoice, Faster-Whisper, Deepgram) tomorrow, and continuously refine quality through model-agnostic enhancements.

**Epic 4 Extension (Stories 4.7-4.9):** Following completion of core enhancement framework (Stories 4.1-4.6), Epic 4 extends to include API enablement layer. Stories 4.7-4.9 expose enhancement pipeline configuration via public API, provide HTTP-based developer tools for testing, and validate cross-model performance. This completes the transition from internal implementation to usable feature accessible to both developers and end users.

## Objectives and Scope

**In Scope:**
- Multi-environment production deployment architecture (Docker Compose with model-specific worker containers)
- Runtime transcription model selection (BELLE-2, WhisperX, configurable default via API or environment)
- Model-agnostic enhancement components: VAD preprocessing, timestamp refinement, segment splitting
- Composable enhancement pipeline framework (chain components in configurable order)
- Multi-model quality validation and regression testing framework
- Environment isolation strategy preventing PyTorch dependency conflicts
- **API enablement layer:** Enhancement configuration exposed via POST /upload endpoint (Story 4.7)
- **HTTP-based CLI tools:** Developer testing tools independent of AI environments (Story 4.8)
- **Cross-model testing & documentation:** Quality validation using CLI tools, final documentation updates (Story 4.9)

**Out of Scope (Deferred to Future Epics):**
- Additional transcription models beyond BELLE-2 and WhisperX (SenseVoice, Faster-Whisper, Deepgram)
- Speaker diarization and automatic speaker identification
- Real-time streaming transcription support
- Advanced audio preprocessing (noise reduction, volume normalization beyond VAD)
- User-facing model selection UI in frontend (admin/config-driven selection only for Epic 4)
- Translation and multilingual transcription beyond WhisperX native capabilities
- Cloud-hosted multi-region model deployment

## System Architecture Alignment

Epic 4 directly implements the multi-model architecture strategy defined in architecture.md §656-870 (AI Service Abstraction Strategy & GPU Environment Requirements). The design leverages:

1. **Existing Abstractions (Epic 1 & 3):**
   - `TranscriptionService` abstract interface (§656-730) - enables model swapping without caller changes
   - `TimestampOptimizer` interface and `OptimizerFactory` (Story 3.2a) - pluggable optimization foundation
   - Git submodule pattern for WhisperX integration (§809-813)

2. **Architecture Evolution (§831-868):**
   - Docker Compose multi-worker architecture with isolated CUDA environments
   - Celery task routing (`@app.task(queue='belle2')` or `queue='whisperx'`)
   - Model-specific Docker images (`klipnote-worker-cuda118`, `klipnote-worker-cuda12`)
   - Zero environment conflicts through container isolation

3. **Alignment with Cross-Cutting Concerns:**
   - Development vs. Production Environment Strategy (§956-1038): Local `.venv` experiments promote to Docker production configs
   - Configuration Promotion Workflow (§1002-1030): Validated parameters migrate from dev `.env` to docker-compose.yaml
   - Testing Strategy (§1040-1305): Multi-model regression testing extends pytest/Vitest patterns

**Architectural Constraints Addressed:**
- PyTorch dependency conflicts resolved via isolated worker containers
- GPU resource management: One model per worker, horizontal scaling for concurrent jobs
- Backward compatibility: MVP single-model deployment remains valid Epic 4 subset (one-worker config)

## Detailed Design

### Services and Modules

**Multi-Model Worker Architecture:**

| Service | Responsibility | Inputs | Outputs | Owner |
|---------|---------------|--------|---------|-------|
| `belle2-worker` | BELLE-2 transcription worker with CUDA 11.8/PyTorch <2.6 environment | Audio file path, job_id, language | Transcription segments JSON | Backend/DevOps |
| `whisperx-worker` | WhisperX transcription worker with CUDA 12.x/PyTorch ≥2.6 environment | Audio file path, job_id, language | Transcription segments JSON | Backend/DevOps |
| `ModelRouter` | Celery task routing logic directing jobs to appropriate worker queue | Model selection (belle2/whisperx/auto), job metadata | Celery task routing decision | Backend |
| `VoiceActivityDetector` | Standalone VAD preprocessing component (WebRTC-based) | Audio waveform, aggressiveness config | Filtered audio segments, silence statistics | Backend |
| `TimestampRefiner` | Energy-based timestamp boundary refinement component | Segments array, audio waveform | Refined segments with optimized boundaries | Backend |
| `SegmentSplitter` | Subtitle-length segment splitting/merging component | Segments array, language config | Split/merged segments meeting constraints | Backend |
| `EnhancementPipeline` | Composable pipeline orchestrator for chaining enhancement components | Segments, audio path, pipeline config | Enhanced segments, processing metrics | Backend |
| `QualityValidator` | Multi-model quality metrics calculator (CER/WER, segment stats) | Original segments, reference transcripts, model metadata | Quality metrics JSON, regression test results | Backend/QA |

**Docker Compose Service Definitions:**

```yaml
# docker-compose.yaml (Epic 4 multi-worker configuration)
services:
  web:
    image: klipnote-web:latest
    ports: ["8000:8000"]
    depends_on: [redis]
    environment:
      - DEFAULT_TRANSCRIPTION_MODEL=belle2  # Story 4.7 decision

  belle2-worker:
    image: klipnote-worker-cuda118:latest
    depends_on: [redis]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - MODEL=belle2
      - CELERY_QUEUE=belle2

  whisperx-worker:
    image: klipnote-worker-cuda12:latest
    depends_on: [redis]
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - MODEL=whisperx
      - CELERY_QUEUE=whisperx

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
```

**Enhancement Component Architecture:**

```python
# app/ai_services/enhancement/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any

class EnhancementComponent(ABC):
    """Base interface for model-agnostic enhancement components"""

    @abstractmethod
    def process(self, segments: List[Dict], audio_path: str, **kwargs) -> List[Dict]:
        """Process segments and return enhanced version"""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Return processing metrics (duration, modifications count, etc.)"""
        pass

# app/ai_services/enhancement/vad.py
class VoiceActivityDetector(EnhancementComponent):
    def __init__(self, aggressiveness: int = 3):
        self.aggressiveness = aggressiveness

    def process(self, segments, audio_path, **kwargs):
        # WebRTC VAD implementation
        pass

# app/ai_services/enhancement/refiner.py
class TimestampRefiner(EnhancementComponent):
    def __init__(self, search_window_ms: int = 200):
        self.search_window_ms = search_window_ms

    def process(self, segments, audio_path, **kwargs):
        # Energy-based refinement implementation
        pass

# app/ai_services/enhancement/splitter.py
class SegmentSplitter(EnhancementComponent):
    def __init__(self, max_duration: float = 7.0, max_chars: int = 200):
        self.max_duration = max_duration
        self.max_chars = max_chars

    def process(self, segments, audio_path=None, **kwargs):
        # Segment splitting/merging implementation
        pass

# app/ai_services/enhancement/pipeline.py
class EnhancementPipeline:
    def __init__(self, components: List[EnhancementComponent]):
        self.components = components

    def process(self, segments, audio_path, **kwargs):
        result = segments
        metrics = {}
        for component in self.components:
            result = component.process(result, audio_path, **kwargs)
            metrics[component.__class__.__name__] = component.get_metrics()
        return result, metrics
```

### Data Models and Contracts

**Model Selection Request:**
```python
# app/models.py
from pydantic import BaseModel
from typing import Literal, Optional

class TranscriptionRequest(BaseModel):
    """Extended upload request with model selection"""
    job_id: str
    file_path: str
    language: str = "auto"
    model: Literal["belle2", "whisperx", "auto"] = "auto"
    enable_enhancements: bool = True
    enhancement_pipeline: Optional[str] = "vad,refine,split"  # Comma-separated component names
```

**Enhancement Configuration:**
```python
class EnhancementConfig(BaseModel):
    """Configuration for enhancement pipeline components"""
    vad_enabled: bool = True
    vad_aggressiveness: int = 3  # 0-3

    refine_enabled: bool = True
    refine_search_window_ms: int = 200

    split_enabled: bool = True
    split_max_duration: float = 7.0
    split_max_chars: int = 200
```

**Quality Metrics Schema:**
```python
class QualityMetrics(BaseModel):
    """Multi-model quality validation results"""
    model_name: str  # "belle2" or "whisperx"
    pipeline_config: str  # "vad,refine,split" or "none"

    # Accuracy metrics
    cer: Optional[float]  # Character Error Rate (if reference available)
    wer: Optional[float]  # Word Error Rate (if reference available)

    # Segment length statistics
    segment_count: int
    mean_duration: float
    median_duration: float
    p95_duration: float
    duration_compliance_pct: float  # % segments in 1-7s range

    # Character length statistics
    mean_chars: int
    p95_chars: int
    char_compliance_pct: float  # % segments ≤200 chars

    # Processing metrics
    transcription_time: float  # seconds
    enhancement_time: float  # seconds
    total_time: float  # seconds
```

**Celery Task Routing Configuration:**
```python
# app/celery_utils.py
from celery import Celery

app = Celery('klipnote')

# Task routing based on model selection
app.conf.task_routes = {
    'app.tasks.transcribe_belle2': {'queue': 'belle2'},
    'app.tasks.transcribe_whisperx': {'queue': 'whisperx'},
}

# Model selection logic
def route_transcription_task(model: str, language: str) -> str:
    """Determine which queue to route transcription job to"""
    if model == "belle2":
        return "belle2"
    elif model == "whisperx":
        return "whisperx"
    elif model == "auto":
        # Auto-selection logic (can be sophisticated in future)
        if language in ["zh", "zh-CN", "zh-TW"]:
            return "belle2"  # Prefer BELLE-2 for Chinese
        else:
            return "whisperx"  # WhisperX for other languages
    else:
        raise ValueError(f"Unknown model: {model}")
```

### APIs and Interfaces

**Extended Upload Endpoint (No API Changes - Config-Driven):**
```
POST /upload
Request: multipart/form-data (file)
Response: {"job_id": "uuid"}

Note: Model selection controlled via environment variable DEFAULT_TRANSCRIPTION_MODEL
Epic 4 maintains backward compatibility - frontend unchanged
```

**New Admin/Config Endpoints (Optional for Story 4.7):**
```python
# app/main.py
@app.get("/admin/models")
async def list_available_models():
    """List available transcription models and their status"""
    return {
        "models": [
            {"name": "belle2", "status": "available", "queue": "belle2"},
            {"name": "whisperx", "status": "available", "queue": "whisperx"}
        ],
        "default": settings.DEFAULT_TRANSCRIPTION_MODEL
    }

@app.get("/admin/workers")
async def get_worker_status():
    """Get Celery worker status for each model queue"""
    inspector = app.celery_app.control.inspect()
    return {
        "belle2_workers": inspector.stats(destination=['belle2@worker']),
        "whisperx_workers": inspector.stats(destination=['whisperx@worker'])
    }
```

**Enhancement Pipeline Interface (Internal):**
```python
# app/ai_services/enhancement/__init__.py
def create_pipeline(config: EnhancementConfig) -> EnhancementPipeline:
    """Factory function to create enhancement pipeline from config"""
    components = []

    if config.vad_enabled:
        components.append(VoiceActivityDetector(config.vad_aggressiveness))

    if config.refine_enabled:
        components.append(TimestampRefiner(config.refine_search_window_ms))

    if config.split_enabled:
        components.append(SegmentSplitter(config.split_max_duration, config.split_max_chars))

    return EnhancementPipeline(components)
```

### Workflows and Sequencing

#### Story Sequencing Strategy

Epic 4 enables **parallel development tracks** to accelerate delivery while maintaining integration safety:

**Track 1: Production Architecture (Story 4.1)**
- Owner: DevOps/Backend Architect
- Duration: 2-3 days
- Deliverables: Docker Compose config, Celery routing, deployment guide
- Dependencies: Epic 3 complete
- Outputs: Architecture Decision Record (ADR), docker-compose.yaml, routing logic

**Track 2: Enhancement Components (Stories 4.2-4.4)**
- Owner: Backend Developer
- Duration: 5-7 days (can start in parallel with Track 1)
- Deliverables: VAD, TimestampRefiner, SegmentSplitter components
- Dependencies: Epic 3 complete (specifically Story 3.2a pluggable architecture pattern)
- Development Environment: Local `.venv` (per architecture.md §956-1038)
- Outputs: Three standalone enhancement components with unit tests

**Parallel Execution Rationale:**
- Stories 4.2-4.4 are pure component development (no Docker dependency)
- Development happens in local `.venv` environment
- Components tested independently before integration
- Reduces critical path by ~3 days

**Integration Checkpoint (Story 4.5)**
- Prerequisites: **BOTH** Track 1 (4.1) AND Track 2 (4.2-4.4) complete
- Validates: Component integration with production architecture
- Critical Integration Points:
  - Enhancement pipeline hooks into Celery transcription tasks
  - Pipeline configuration promotion from dev `.env` to docker-compose.yaml
  - Cross-model compatibility (components work with both BELLE-2 and WhisperX)

**Validation Phase (Stories 4.6-4.7)**
- Story 4.6 requires: Story 4.1 (multi-worker deployment) + Story 4.5 (pipeline framework)
- Story 4.7 synthesizes: All Epic 4 learnings into MVP model selection decision

**Updated Story Dependencies:**

```
Epic 3 Complete
  ├─→ Story 4.1: Multi-Model Production Architecture Design
  │     (Docker, Celery routing, deployment strategy)
  │
  └─→ Story 4.2: VAD Preprocessing Component
        (Can start in parallel with 4.1)
        ↓
      Story 4.3: Timestamp Refinement Component
        ↓
      Story 4.4: Segment Splitting Component
        ↓
      Story 4.5: Enhancement Pipeline Composition Framework
        ← Prerequisites: 4.1 (routing) + 4.2 + 4.3 + 4.4 (components)
        ↓
      Story 4.6: Multi-Model Quality Validation Framework
        ← Prerequisites: 4.1 (deployment) + 4.5 (pipeline)
        ↓
      Story 4.7: Enhancement API Layer Development
        ← Prerequisites: 4.6 (quality validation complete)
        ↓
      Story 4.8: HTTP CLI Tool Development
        ← Prerequisites: 4.7 (API layer complete)
        ↓
      Story 4.9: Model Testing & Documentation
        ← Prerequisites: 4.8 (CLI tool complete)
```

#### Multi-Model Job Processing Flow

```
1. Upload Endpoint receives file
   ↓
2. ModelRouter.route_transcription_task(model="auto", language="zh")
   └→ Returns queue name: "belle2" (Chinese detected)
   ↓
3. Celery dispatches task to belle2 queue
   ↓
4. belle2-worker (CUDA 11.8 container) picks up task
   ↓
5. Belle2Service.transcribe(audio_path) → raw segments
   ↓
6. EnhancementPipeline.process(segments, audio_path)
   ├→ VoiceActivityDetector: Filter silence
   ├→ TimestampRefiner: Optimize boundaries
   └→ SegmentSplitter: Split long segments
   ↓
7. Store enhanced segments in Redis/JSON
   ↓
8. Update job status to "completed"
   ↓
9. Frontend polls /result/{job_id} → receives enhanced segments
```

**Configuration Promotion Workflow (Dev → Production):**

```
Development Phase (Stories 4.2-4.4):
1. Experiment with enhancement parameters in local .venv
2. Tune VAD aggressiveness, refine search window, split thresholds
3. Validate with quality metrics on test corpus
   ↓
Production Promotion (Story 4.5):
4. Copy validated params from dev .env to docker-compose.yaml
5. Document rationale in ADR (Architecture Decision Record)
6. Deploy with Docker Compose
7. Monitor quality metrics in production (Story 4.6)
```

**Rollback Strategy:**

- Story 4.1 establishes single-worker fallback mode (backward compatible with MVP)
- Story 4.5 enhancement pipeline has `ENABLE_ENHANCEMENTS=false` kill switch
- Docker Compose can disable individual workers (e.g., comment out `whisperx-worker` service)
- Quality regression detected by Story 4.6 triggers rollback to previous config

## Non-Functional Requirements

### Performance

**NFR-E4-001: Multi-Model Processing Performance Parity**
- Target: Both BELLE-2 and WhisperX workers achieve 1-2x real-time transcription speed (1 hour audio = 30-60 min processing)
- Baseline: Maintain NFR001 performance targets from Epic 1-3
- Validation: Story 4.6 benchmarks both models on identical test corpus
- Degradation Threshold: >10% slowdown vs. single-model MVP triggers investigation

**NFR-E4-002: Enhancement Pipeline Overhead**
- Target: Full enhancement pipeline (VAD + Refine + Split) adds ≤25% overhead to transcription time
- Calculation: `enhancement_time / transcription_time ≤ 0.25`
- Example: 30-minute transcription allows max 7.5 minutes for enhancements
- Validation: Story 4.5 integration tests measure pipeline overhead
- Mitigation: If exceeded, components can be disabled individually via config

**NFR-E4-003: Worker Startup and Model Loading Time**
- Target: Worker containers start and load models in <5 minutes (warm start: <10 seconds)
- Cold Start (first boot): WhisperX model download + BELLE-2 model download = ~3GB total
- Warm Start (cached models): Model loading from disk cache
- Impact: Affects horizontal scaling responsiveness
- Validation: Story 4.1 deployment testing on clean Docker environment

**NFR-E4-004: Concurrent Job Processing**
- Target: Each worker processes 1 transcription job at a time (no concurrent jobs per worker)
- Horizontal Scaling: Deploy multiple worker containers for parallelism (e.g., 2x belle2-worker, 2x whisperx-worker)
- GPU Resource: One worker = one GPU (avoid VRAM contention)
- Validation: Story 4.6 stress testing with 5+ concurrent jobs

**NFR-E4-005: Configuration Hot-Reload**
- Target: Enhancement pipeline config changes via environment variables, require container restart
- Not Required: Zero-downtime config changes (acceptable Epic 4 constraint)
- Deployment Pattern: Blue-green deployment for config changes
- Validation: Story 4.5 documents restart procedure

### Security

**NFR-E4-006: Container Isolation**
- Requirement: BELLE-2 and WhisperX workers run in isolated Docker containers with no shared filesystem access
- Rationale: Prevent PyTorch dependency conflicts, limit security blast radius
- Implementation: Each worker has dedicated `/uploads/{job_id}` volume mount (read-only after transcription)
- Validation: Story 4.1 Docker Compose config review

**NFR-E4-007: Model Weight Integrity**
- Requirement: Verify HuggingFace model checksums before loading (prevent model poisoning)
- Implementation: Use `transformers` library built-in integrity checks
- Fallback: If checksum fails, log error and fail task (don't silently use corrupted model)
- Validation: Story 4.2-4.4 unit tests mock checksum failure scenarios

**NFR-E4-008: API Backward Compatibility**
- Requirement: Existing MVP API contracts unchanged (POST /upload, GET /status, GET /result)
- Model Selection: Configuration-driven only (no user-facing model selection in Epic 4 API)
- Rationale: Frontend remains unchanged, reduces Epic 4 scope
- Validation: Story 4.7 integration tests verify MVP test suite still passes

**NFR-E4-009: Secrets Management**
- Requirement: No hardcoded credentials in Docker images or docker-compose.yaml
- HuggingFace Tokens: Passed via environment variables if needed for gated models
- Redis Credentials: Environment variables only (not in source control)
- Validation: Story 4.1 security review of docker-compose.yaml

### Reliability/Availability

**NFR-E4-010: Worker Failure Isolation**
- Requirement: Failure of one worker (e.g., belle2-worker crash) doesn't affect other workers
- Implementation: Separate Celery queues, independent worker processes
- Recovery: Docker Compose restart policy: `restart: unless-stopped`
- Validation: Story 4.6 chaos testing (kill worker during job processing)

**NFR-E4-011: Graceful Degradation - Single Worker Mode**
- Requirement: If one model's worker fails, system continues processing jobs with remaining worker
- Fallback: ModelRouter detects unavailable queue, routes to available worker with warning logged
- User Impact: Some jobs may use non-optimal model (e.g., WhisperX for Chinese if belle2-worker down)
- Validation: Story 4.5 implements queue health check in ModelRouter

**NFR-E4-012: Enhancement Pipeline Failure Recovery**
- Requirement: If enhancement component fails (e.g., VAD crashes), return raw transcription segments as fallback
- Error Handling: Catch exceptions in `EnhancementPipeline.process()`, log error, return input segments unchanged
- User Impact: User receives transcription (unenhanced) rather than job failure
- Validation: Story 4.5 unit tests inject exceptions in each component

**NFR-E4-013: Model Compatibility Regression Detection**
- Requirement: Story 4.6 quality validation framework detects >15% quality degradation vs. Epic 3 baselines
- Metrics: CER/WER increase, segment length distribution shift
- Response: Quality regression triggers Epic 4 rollback to single-model MVP config
- Validation: Story 4.6 includes regression test suite with Epic 3 baseline transcripts

**NFR-E4-014: Zero-Downtime Rollback**
- Requirement: Ability to rollback from multi-worker to single-worker config in <10 minutes
- Procedure: Update docker-compose.yaml (comment out one worker), `docker-compose up -d`
- Data Loss: None (Redis job data persists, only worker availability changes)
- Validation: Story 4.7 documents rollback procedure with timing measurements

### Observability

**NFR-E4-015: Multi-Model Job Routing Visibility**
- Requirement: Each transcription job logs which model was selected and why
- Log Format: `INFO: Job {job_id} routed to queue 'belle2' (reason: language='zh', model='auto')`
- Destination: Stdout (Docker captures for aggregation)
- Validation: Story 4.1 implements structured logging in ModelRouter

**NFR-E4-016: Enhancement Pipeline Metrics**
- Requirement: Each enhancement component reports processing time and modification count
- Metrics Example:
  - `VoiceActivityDetector: 500 segments → 480 segments (20 silence removed), 3.2s`
  - `TimestampRefiner: 480 boundaries refined, 1.8s`
  - `SegmentSplitter: 480 → 520 segments (40 split), 2.1s`
- Storage: Logged to stdout, optionally stored in Redis job metadata
- Validation: Story 4.5 implements `get_metrics()` interface for all components

**NFR-E4-017: Worker Health Monitoring**
- Requirement: Celery Flower dashboard accessible for real-time worker monitoring
- Metrics Exposed:
  - Active workers per queue (belle2, whisperx)
  - Queue lengths (pending jobs)
  - Worker uptime, task success/failure rates
- Access: `http://localhost:5555` (Flower web UI)
- Validation: Story 4.1 configures Flower service in docker-compose.yaml

**NFR-E4-018: Quality Metrics Baseline Tracking**
- Requirement: Story 4.6 stores quality metrics for each model+pipeline configuration
- Format: `quality_metrics/{model}_{pipeline_config}_{timestamp}.json`
- Retention: Minimum 10 baseline runs for statistical significance
- Usage: Enables trend analysis (is quality improving/degrading over time?)
- Validation: Story 4.6 implements metrics persistence and CLI query tool

**NFR-E4-019: GPU Resource Utilization Logging**
- Requirement: Log GPU memory usage before/after model loading
- Example: `INFO: CUDA device 0: 6.2GB / 12GB used (BELLE-2 model loaded)`
- Warning Threshold: Log warning if GPU memory >90% utilized
- Validation: Story 4.1 adds GPU logging to worker initialization

## Dependencies and Integrations

### External Dependencies

**Python Packages (Multi-Environment):**

| Package | Version | Environment | Purpose | Epic 4 Story |
|---------|---------|-------------|---------|--------------|
| `torch` | `<2.6.0` | belle2-worker | PyTorch for BELLE-2 (CUDA 11.8) | 4.1 |
| `torch` | `>=2.6.0` | whisperx-worker | PyTorch for WhisperX (CUDA 12.x) | 4.1 |
| `transformers` | `>=4.40.0` | belle2-worker | HuggingFace BELLE-2 model loading | 3.1 (existing) |
| `whisperx` | `latest` | whisperx-worker | WhisperX transcription library (git submodule) | 3.2b (existing) |
| `webrtcvad` | `2.0.10` | Both workers | Voice Activity Detection | 4.2 |
| `librosa` | `0.10.x` | Both workers | Audio waveform analysis for timestamp refinement | 4.3 |
| `jiwer` | `3.0.x` | Both workers | CER/WER calculation | 4.6 |
| `celery[redis]` | `5.5.3` | All workers + web | Task queue (existing) | 1.3 (existing) |
| `redis` | `5.0.x` (Python client) | All workers + web | Redis client (existing) | 1.3 (existing) |

**System Dependencies (Docker Images):**

| Dependency | Version | Purpose | Image |
|------------|---------|---------|-------|
| CUDA Toolkit | `11.8` | GPU support for BELLE-2 | `klipnote-worker-cuda118` |
| CUDA Toolkit | `12.1+` | GPU support for WhisperX | `klipnote-worker-cuda12` |
| NVIDIA Driver | `>=530` | Host GPU driver (both models) | Host system |
| FFmpeg | `6.x` | Audio preprocessing (existing) | Both worker images |
| Python | `3.12.x` | Runtime environment (existing) | Both worker images |

**Docker Base Images:**

```dockerfile
# Dockerfile.belle2 (Story 4.1)
FROM nvidia/cuda:11.8.0-base-ubuntu22.04
RUN apt-get update && apt-get install -y python3.12 python3-pip ffmpeg
COPY requirements-belle2.txt /app/
RUN pip install -r /app/requirements-belle2.txt
# ... rest of Dockerfile

# Dockerfile.whisperx (Story 4.1)
FROM nvidia/cuda:12.1.0-base-ubuntu22.04
RUN apt-get update && apt-get install -y python3.12 python3-pip ffmpeg
COPY requirements-whisperx.txt /app/
RUN pip install -r /app/requirements-whisperx.txt
# ... rest of Dockerfile
```

### Internal Integration Points

**Celery Task Integration:**

```python
# app/tasks/transcription.py (Modified in Story 4.5)
from app.ai_services import Belle2Service, WhisperXService
from app.ai_services.enhancement import create_pipeline
from app.config import settings

@shared_task(queue='belle2')
def transcribe_belle2(job_id: str, file_path: str, language: str = "zh"):
    """BELLE-2 transcription task with enhancement pipeline"""
    # 1. Transcribe
    service = Belle2Service()
    segments = service.transcribe(file_path, language)

    # 2. Enhance (if enabled)
    if settings.ENABLE_ENHANCEMENTS:
        pipeline = create_pipeline(settings.enhancement_config)
        segments, metrics = pipeline.process(segments, file_path)
        logger.info(f"Enhancement metrics: {metrics}")

    # 3. Store result
    store_result(job_id, segments)

@shared_task(queue='whisperx')
def transcribe_whisperx(job_id: str, file_path: str, language: str = "auto"):
    """WhisperX transcription task with enhancement pipeline"""
    # Same pattern as belle2, different service
    service = WhisperXService()
    segments = service.transcribe(file_path, language)

    if settings.ENABLE_ENHANCEMENTS:
        pipeline = create_pipeline(settings.enhancement_config)
        segments, metrics = pipeline.process(segments, file_path)

    store_result(job_id, segments)
```

**ModelRouter Integration with Upload Endpoint:**

```python
# app/main.py (Modified in Story 4.1)
from app.tasks.transcription import transcribe_belle2, transcribe_whisperx
from app.ai_services.model_router import route_transcription_task

@app.post("/upload")
async def upload_file(file: UploadFile):
    job_id = str(uuid.uuid4())
    file_path = save_uploaded_file(file, job_id)

    # Detect language (existing FFmpeg/audio analysis logic)
    language = detect_language(file_path)  # e.g., "zh", "en", "auto"

    # Route to appropriate worker queue
    queue_name = route_transcription_task(
        model=settings.DEFAULT_TRANSCRIPTION_MODEL,  # "auto", "belle2", or "whisperx"
        language=language
    )

    # Dispatch task to selected queue
    if queue_name == "belle2":
        transcribe_belle2.apply_async(args=[job_id, file_path, language])
    elif queue_name == "whisperx":
        transcribe_whisperx.apply_async(args=[job_id, file_path, language])

    logger.info(f"Job {job_id} routed to queue '{queue_name}' (language={language})")

    return {"job_id": job_id}
```

**Redis Integration (Existing - Extended in Epic 4):**

- Job status keys: `job:{job_id}:status` (no changes)
- Job result keys: `job:{job_id}:result` (now includes enhancement metrics)
- New: Worker health keys: `worker:{queue}:heartbeat` (Story 4.5 for graceful degradation)

**Flower Monitoring Integration:**

```yaml
# docker-compose.yaml (Story 4.1)
services:
  flower:
    image: mher/flower:2.0
    command: celery --broker=redis://redis:6379/0 flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
```

### Dependency Management Strategy

**Separate Requirements Files (Story 4.1):**

```
backend/
├── requirements-common.txt      # Shared dependencies (FastAPI, Celery, Redis)
├── requirements-belle2.txt      # BELLE-2 specific (torch<2.6, transformers)
├── requirements-whisperx.txt    # WhisperX specific (torch>=2.6, whisperx)
└── requirements-enhancement.txt # Enhancement components (webrtcvad, librosa, jiwer)
```

**Docker Image Build Strategy:**

```bash
# Story 4.1: Build separate images for each environment
docker build -f Dockerfile.belle2 -t klipnote-worker-cuda118:latest .
docker build -f Dockerfile.whisperx -t klipnote-worker-cuda12:latest .
```

**Volume Mounts (Shared Data):**

```yaml
# docker-compose.yaml
volumes:
  uploads_data:  # Shared volume for uploaded media files
  belle2_models: # BELLE-2 model cache (~3GB)
  whisperx_models: # WhisperX model cache (~3GB)

services:
  belle2-worker:
    volumes:
      - uploads_data:/uploads:ro  # Read-only after transcription
      - belle2_models:/root/.cache/huggingface

  whisperx-worker:
    volumes:
      - uploads_data:/uploads:ro
      - whisperx_models:/root/.cache/whisperx
```

### Integration Testing Strategy (Story 4.6)

**Multi-Model Integration Test Suite:**

```python
# tests/integration/test_multi_model_flow.py
import pytest

@pytest.mark.integration
def test_belle2_worker_full_flow(test_audio_chinese):
    """Validate BELLE-2 worker end-to-end"""
    job_id = upload_file(test_audio_chinese)
    wait_for_completion(job_id, timeout=120)

    result = get_result(job_id)
    assert result["segments"]
    assert "belle2" in get_job_metadata(job_id)["model_used"]

@pytest.mark.integration
def test_whisperx_worker_full_flow(test_audio_english):
    """Validate WhisperX worker end-to-end"""
    job_id = upload_file(test_audio_english)
    wait_for_completion(job_id, timeout=120)

    result = get_result(job_id)
    assert result["segments"]
    assert "whisperx" in get_job_metadata(job_id)["model_used"]

@pytest.mark.integration
def test_enhancement_pipeline_integration(test_audio):
    """Validate VAD + Refine + Split pipeline"""
    # Enable all enhancements via config
    job_id = upload_file(test_audio)
    result = get_result(job_id)

    metrics = get_enhancement_metrics(job_id)
    assert "VoiceActivityDetector" in metrics
    assert "TimestampRefiner" in metrics
    assert "SegmentSplitter" in metrics

@pytest.mark.integration
def test_worker_failure_graceful_degradation():
    """Validate system continues if one worker fails"""
    # Kill belle2-worker
    docker_kill("belle2-worker")

    # Upload Chinese audio (would normally use belle2)
    job_id = upload_file(test_audio_chinese)

    # Should fallback to whisperx with warning logged
    result = get_result(job_id)
    assert result["segments"]
    assert "fallback" in get_job_logs(job_id)
```

### Upgrade/Migration Path (Epic 3 → Epic 4)

**Phase 1: MVP Single-Worker (Current State after Story 4.7)**
```yaml
# docker-compose.yaml (MVP config)
services:
  web: ...
  worker:  # Single worker with selected model
    image: klipnote-worker-cuda118  # OR cuda12 based on Story 4.7 decision
    environment:
      - MODEL=belle2  # Selected model
  redis: ...
```

**Phase 2: Epic 4 Multi-Worker (Post-MVP)**
```yaml
# docker-compose.yaml (Epic 4 full config)
services:
  web: ...
  belle2-worker: ...
  whisperx-worker: ...
  redis: ...
  flower: ...  # Monitoring added
```

**Migration Steps (Story 4.7 Documents):**
1. Build both Docker images (belle2, whisperx)
2. Update docker-compose.yaml to multi-worker config
3. Run `docker-compose up -d` (deploys both workers)
4. Verify both queues active in Flower dashboard
5. Test sample jobs routed to each worker
6. Monitor quality metrics (Story 4.6 framework)

## Acceptance Criteria (Authoritative)

### Story 4.1: Multi-Model Production Architecture Design

**AC-4.1-1:** Architecture Decision Record (ADR) documents multi-environment production strategy
- ADR file created in `docs/architecture/adr-epic4-multi-worker.md`
- Covers: PyTorch conflict resolution, Docker isolation strategy, Celery routing design
- Includes: Rationale, alternatives considered, consequences

**AC-4.1-2:** Docker Compose configuration supports model-specific containers
- `docker-compose.yaml` defines `belle2-worker` and `whisperx-worker` services
- Each worker has isolated CUDA environment (11.8 vs 12.x)
- GPU resource reservations configured (`deploy.resources.reservations.devices`)

**AC-4.1-3:** Celery task routing directs jobs to appropriate worker based on model selection
- `app/celery_utils.py` implements task routes for `belle2` and `whisperx` queues
- `ModelRouter.route_transcription_task()` function implements auto-selection logic
- Logs routing decisions with rationale

**AC-4.1-4:** Environment isolation prevents PyTorch version conflicts
- Separate Dockerfiles (`Dockerfile.belle2`, `Dockerfile.whisperx`) with different base images
- `requirements-belle2.txt` locks `torch<2.6.0`
- `requirements-whisperx.txt` locks `torch>=2.6.0`

**AC-4.1-5:** Model selection configuration via environment variables
- `DEFAULT_TRANSCRIPTION_MODEL` environment variable supports "belle2", "whisperx", "auto"
- `app/config.py` Pydantic settings validate model selection value
- Invalid values raise configuration error on startup

**AC-4.1-6:** Documentation updated with deployment guide and environment requirements
- `docs/deployment/multi-worker-setup.md` created with setup instructions
- GPU requirements documented (NVIDIA driver >=530, CUDA 11.8 + 12.x)
- Troubleshooting section for common deployment issues

### Story 4.2: Model-Agnostic VAD Preprocessing Component

**AC-4.2-1:** `VoiceActivityDetector` component implemented as standalone preprocessing step
- `app/ai_services/enhancement/vad.py` implements `EnhancementComponent` interface
- `process()` method accepts segments array, returns filtered segments
- `get_metrics()` returns silence statistics (removed count, duration)

**AC-4.2-2:** Works with any transcription model output (BELLE-2, WhisperX)
- Unit tests validate compatibility with both model's segment formats
- Integration tests run VAD on outputs from both `Belle2Service` and `WhisperXService`

**AC-4.2-3:** WebRTC VAD integrated with configurable aggressiveness (0-3)
- `webrtcvad` library integrated in `requirements-enhancement.txt`
- Constructor accepts `aggressiveness` parameter (0=least aggressive, 3=most aggressive)
- Invalid aggressiveness values raise `ValueError`

**AC-4.2-4:** VAD filtering removes silence segments >1s duration
- Segments with >1 second continuous silence removed from output
- Statistics track: original segment count, filtered count, total silence duration
- Edge case: Segments with <1s silence preserved

**AC-4.2-5:** Processing completes in <5 minutes for 1-hour audio
- Performance test validates processing time on 60-minute audio file
- Logs warning if processing exceeds 5-minute threshold

**AC-4.2-6:** Unit tests with mocked audio, integration tests on noisy samples
- `tests/unit/test_vad.py` mocks audio with `pytest-mock`
- `tests/integration/test_vad_integration.py` uses real noisy audio samples

**AC-4.2-7:** Component can be enabled/disabled via configuration
- `EnhancementConfig.vad_enabled` boolean flag
- When `False`, VAD component not added to pipeline
- Configuration change requires worker restart (documented)

### Story 4.3: Model-Agnostic Timestamp Refinement Component

**AC-4.3-1:** `TimestampRefiner` component works with any model's segment output
- `app/ai_services/enhancement/refiner.py` implements `EnhancementComponent` interface
- Tested with BELLE-2 and WhisperX segment formats

**AC-4.3-2:** Energy-based refinement analyzes audio waveform (librosa)
- `librosa` library integrated for waveform analysis
- Computes RMS energy or spectral energy across audio

**AC-4.3-3:** Boundary refinement searches ±200ms for optimal split point (minimum energy)
- Constructor accepts `search_window_ms` parameter (default: 200)
- Algorithm searches window around original boundary for local energy minimum
- Selects boundary with lowest energy within window

**AC-4.3-4:** Timestamp alignment maintains <200ms accuracy vs. original outputs
- Validation compares refined timestamps to original BELLE-2/WhisperX outputs
- Fails if any boundary shifts >200ms (indicates algorithm error)
- Logs warning if >5% of boundaries shift >100ms

**AC-4.3-5:** Processing completes in <5 minutes for 500 segments
- Performance test on 500-segment transcription
- Logs warning if exceeded

**AC-4.3-6:** Works with both BELLE-2 and WhisperX segment formats
- Integration tests validate refinement on both models' outputs
- No model-specific logic in refiner code

**AC-4.3-7:** Component can be enabled/disabled via configuration
- `EnhancementConfig.refine_enabled` boolean flag

### Story 4.4: Model-Agnostic Segment Splitting Component

**AC-4.4-1:** `SegmentSplitter` component works with any model's segment output
- `app/ai_services/enhancement/splitter.py` implements `EnhancementComponent` interface
- No model-specific dependencies

**AC-4.4-2:** Segments >7 seconds split at natural boundaries (punctuation, pauses)
- Constructor accepts `max_duration` parameter (default: 7.0)
- Splitting algorithm prefers punctuation marks (。！？，；) as split points
- Falls back to pause detection if no punctuation available

**AC-4.4-3:** Chinese text length estimation implemented (character count × 0.4s)
- Heuristic: ~150-180 chars/minute speaking rate for Mandarin = ~2.5-3 chars/second
- Conservative estimate: 0.4s per character ensures readability
- Constructor accepts `max_chars` parameter (default: 200)

**AC-4.4-4:** Short segments <1s merged when safe
- Merging logic checks: adjacent segment timestamps, text length constraints
- Only merges if combined duration <7s and combined chars <200
- Preserves segment boundaries if merging would violate constraints

**AC-4.4-5:** 95% of output segments meet 1-7s, <200 char constraints
- Validation script calculates compliance percentage
- Test fails if compliance <95%
- Logs statistics: mean duration, P95 duration, mean chars, P95 chars

**AC-4.4-6:** Processing completes in <3 minutes for 500 segments
- Performance benchmark on 500-segment test case

**AC-4.4-7:** Works with both BELLE-2 and WhisperX segment formats
- Integration tests on both models' outputs

**AC-4.4-8:** Component can be enabled/disabled via configuration
- `EnhancementConfig.split_enabled` boolean flag

### Story 4.5: Enhancement Pipeline Composition Framework

**AC-4.5-1:** `EnhancementPipeline` class supports dynamic component chaining
- `app/ai_services/enhancement/pipeline.py` accepts list of `EnhancementComponent` instances
- `process()` method chains components in order
- Returns: (enhanced_segments, aggregated_metrics)

**AC-4.5-2:** Configuration-driven pipeline definition (environment variables)
- `ENHANCEMENT_PIPELINE` environment variable: comma-separated component names ("vad,refine,split")
- `create_pipeline()` factory function parses config and instantiates components
- Invalid component names raise `ValueError`

**AC-4.5-3:** Pipeline examples work: "VAD only", "VAD + Refine", "VAD + Refine + Split", "No enhancements"
- Unit tests validate all pipeline combinations
- "No enhancements" = empty pipeline, returns input segments unchanged

**AC-4.5-4:** Component execution order configurable
- Order determined by comma-separated list order
- "vad,split,refine" executes in that sequence

**AC-4.5-5:** Pipeline metrics collected (processing time per component)
- `get_metrics()` returns dict: `{"VoiceActivityDetector": {...}, "TimestampRefiner": {...}}`
- Includes: component name, processing time, modifications count

**AC-4.5-6:** Error handling: component failures don't crash entire pipeline
- Pipeline catches exceptions from individual components
- Logs error, returns input segments (fallback to raw transcription)
- User receives unenhanced transcription rather than job failure (graceful degradation)

**AC-4.5-7:** Documentation includes configuration guide and common pipeline recipes
- `docs/enhancement-pipeline.md` documents:
  - Component descriptions
  - Configuration syntax
  - Recommended recipes for different use cases (Chinese audio, noisy audio, subtitle editing)

**AC-4.5-8:** Prerequisites: Story 4.1 (routing) + Story 4.2-4.4 (components) complete
- Integration test validates pipeline works with Celery task routing
- Multi-worker deployment successfully applies pipeline to jobs

### Story 4.6: Multi-Model Quality Validation Framework

**AC-4.6-1:** Quality validator calculates CER/WER using jiwer library
- `app/ai_services/quality/validator.py` implements `calculate_cer()` and `calculate_wer()`
- Requires reference transcripts for comparison
- Returns `None` if reference unavailable (not an error)

**AC-4.6-2:** Segment length statistics calculated (mean, median, P95, % meeting constraints)
- `calculate_segment_stats()` function computes:
  - Duration: mean, median, P95, compliance % (1-7s range)
  - Characters: mean, P95, compliance % (≤200 chars)

**AC-4.6-3:** Cross-model comparison reports (BELLE-2 vs WhisperX with same enhancements)
- CLI tool: `python -m app.cli.compare_models --model1 belle2 --model2 whisperx --corpus test_audio/`
- Generates side-by-side comparison table with metrics

**AC-4.6-4:** Baseline regression testing against Epic 3 A/B test results
- `tests/regression/test_epic3_baseline.py` validates quality hasn't degraded
- Loads Epic 3 baseline metrics from `tests/regression/epic3_baselines.json`
- Fails if CER/WER increases >15% or segment compliance drops >10%

**AC-4.6-5:** Quality metrics stored per model+enhancement configuration
- Format: `backend/quality_metrics/{model}_{pipeline}_{timestamp}.json`
- Example: `belle2_vad-refine-split_20251115_143022.json`

**AC-4.6-6:** CLI tool for manual validation and baseline generation
- `python -m app.cli.validate_quality --model belle2 --pipeline "vad,refine,split" --corpus test_audio/`
- Outputs: JSON metrics file + human-readable summary

**AC-4.6-7:** Unit tests verify metric calculations with known inputs
- Synthetic test cases with known CER/WER values
- Validates calculation accuracy

**AC-4.6-8:** Integration test validates metrics across both models
- Runs validation on same audio corpus through both workers
- Verifies metrics generated for both

### Story 4.7: Enhancement API Layer Development

**AC-4.7-1:** POST /upload accepts optional `enhancement_config` JSON parameter (form field)
- Endpoint signature updated to accept `enhancement_config: Optional[str]` parameter
- Parameter accepted as JSON string in multipart form data
- Backward compatible: omitting parameter uses environment configuration

**AC-4.7-2:** EnhancementFactory.create_pipeline() supports config_dict injection
- `create_pipeline()` function accepts optional `config_dict` parameter
- Configuration priority implemented: API param > env vars > defaults
- Factory parses config and instantiates components accordingly

**AC-4.7-3:** Pydantic model validation for enhancement_config structure
- `EnhancementConfigRequest` Pydantic model validates JSON structure
- Validates pipeline component names ("vad", "refine", "split")
- Validates parameter ranges (e.g., VAD threshold 0.0-1.0)
- Invalid configurations return 400 Bad Request with clear error messages

**AC-4.7-4:** API tests cover enhancement_config parameter scenarios
- Valid configuration with all components
- Valid configuration with partial components (e.g., only VAD)
- Invalid JSON format (returns 400)
- Invalid pipeline component names (returns 400)
- Invalid parameter values (returns 400 with specific error)

**AC-4.7-5:** Error responses include clear messages indicating which parameter is invalid
- Example: "Invalid pipeline component 'invalid_component'. Valid components: vad, refine, split"
- Example: "VAD threshold must be between 0.0 and 1.0"
- HTTP 400 status code for all validation errors

**AC-4.7-6:** TypeScript type definitions updated (if frontend integration planned)
- `frontend/src/types/api.ts` includes `EnhancementConfig` interface (optional)
- Matches backend Pydantic model structure

**AC-4.7-7:** Backward compatible: missing enhancement_config uses env vars
- Integration test validates: omitting parameter → uses environment variables
- No breaking changes to existing API contracts

**AC-4.7-8:** Configuration priority implemented and tested
- Test validates: API parameter overrides environment variable
- Test validates: Environment variable overrides default value
- Documentation updated in architecture.md

**Estimated Effort:** 1-2 hours

---

### Story 4.8: HTTP CLI Tool Development

**AC-4.8-1:** Create `backend/app/cli/klip_client.py` with 4 commands
- `upload`: Upload file with optional model and enhancement_config
- `status`: Poll job status with optional --watch flag
- `result`: Fetch transcription result with optional --output file
- `test-flow`: Automated end-to-end test (upload → poll → fetch → validate)

**AC-4.8-2:** Dependencies: requests/httpx only (no PyTorch/transformers)
- `requirements.txt` or separate `requirements-cli.txt` includes HTTP client library
- No AI model dependencies in CLI tool
- Environment-independent: works without .venv or .venv-whisperx activation

**AC-4.8-3:** Support for enhancement_config parameter in upload command
- Command-line argument: `--config '{"pipeline":"vad,split"}'`
- JSON string passed to API as enhancement_config parameter
- Example usage documented in CLI help and README

**AC-4.8-4:** --watch flag for status polling
- Status command with `--watch` polls every 3 seconds until completion/failure
- Prints progress updates to console
- Exits on completion or error

**AC-4.8-5:** JSON output format for result command
- `--output` flag saves result to file
- Default: prints JSON to stdout (can pipe to jq)
- Format matches API response structure

**AC-4.8-6:** Automated test-flow validates end-to-end workflow
- Upload succeeds and returns job_id
- Status polling works (prints progress updates)
- Result fetch succeeds
- Basic validation (segments exist, format correct)

**AC-4.8-7:** README documentation with usage examples
- `backend/app/cli/README.md` includes:
  - Installation instructions
  - Command usage for each subcommand
  - Enhancement config examples
  - Troubleshooting common errors (connection refused, timeout, etc.)

**Estimated Effort:** 2-3 hours

---

### Story 4.9: Model Testing & Documentation

**AC-4.9-1:** Run `klip_client.py test-flow` for Belle2 with test samples
- zh_medium_audio1 (medium-length Chinese audio)
- zh_short_video1 (short video sample)
- Record: response time, CER/WER results, segment statistics

**AC-4.9-2:** Run `klip_client.py test-flow` for WhisperX with same samples
- Same test corpus as Belle2
- Compare results side-by-side

**AC-4.9-3:** Compare results using enhancement configurations
- Baseline (no enhancements)
- VAD only
- VAD + refinement
- Full pipeline (VAD + refinement + splitting)

**AC-4.9-4:** Document findings in decision log
- Side-by-side metric comparison table
- Enhancement pipeline effectiveness analysis
- Recommendation for default configuration
- File location: `docs/decisions/enhancement-pipeline-effectiveness.md`

**AC-4.9-5:** Update main README.md with CLI tools section
- Developer Tools overview
- klip_client.py installation
- Common usage examples
- Link to detailed CLI README

**AC-4.9-6:** Update architecture.md Developer Tools section
- Verify completeness of Developer Tools section added in Phase 1
- Ensure alignment with actual CLI implementation

**AC-4.9-7:** Verify all test results meet quality baselines
- CER ≤ 10% for Chinese audio
- WER ≤ 15% for Chinese audio
- Segment length compliance ≥ 90% (1-7s, ≤200 chars)

**Estimated Effort:** 1 hour

## Traceability Mapping

| Acceptance Criteria | Spec Section | Component/API | Test Strategy |
|-------------------|--------------|---------------|---------------|
| AC-4.1-1 to AC-4.1-6 | Detailed Design § Services and Modules | Docker Compose, ModelRouter, Celery routing | Integration tests validate worker isolation and routing logic |
| AC-4.2-1 to AC-4.2-7 | Detailed Design § Enhancement Component Architecture | VoiceActivityDetector | Unit tests (mocked audio) + Integration tests (real noisy audio) |
| AC-4.3-1 to AC-4.3-7 | Detailed Design § Enhancement Component Architecture | TimestampRefiner | Unit tests (synthetic segments) + Integration tests (both models) |
| AC-4.4-1 to AC-4.4-8 | Detailed Design § Enhancement Component Architecture | SegmentSplitter | Unit tests (edge cases) + Quality validation (95% compliance) |
| AC-4.5-1 to AC-4.5-8 | Detailed Design § Workflows and Sequencing | EnhancementPipeline, create_pipeline() factory | Integration tests (all pipeline combinations) + Error injection tests |
| AC-4.6-1 to AC-4.6-8 | Dependencies § Integration Testing Strategy | QualityValidator, CLI tools | Regression tests (Epic 3 baselines) + Cross-model comparison |
| AC-4.7-1 to AC-4.7-8 | APIs and Interfaces § Extended Upload Endpoint | POST /upload enhancement_config parameter | API tests (valid/invalid configurations), backward compatibility tests |
| AC-4.8-1 to AC-4.8-7 | Developer Tools § HTTP CLI Tool | klip_client.py (upload, status, result, test-flow) | End-to-end CLI tests, environment independence validation |
| AC-4.9-1 to AC-4.9-7 | Test Strategy § Multi-Model Integration | Belle2/WhisperX cross-model testing | Quality baseline validation, documentation review |
| NFR-E4-001 to NFR-E4-005 | NFR § Performance | All workers | Performance benchmarks (Story 4.6) |
| NFR-E4-006 to NFR-E4-009 | NFR § Security | Docker isolation, Model integrity | Security review (Story 4.1) + Checksum validation tests |
| NFR-E4-010 to NFR-E4-014 | NFR § Reliability | Worker failure handling, Graceful degradation | Chaos tests (kill worker during processing), Rollback procedure validation |
| NFR-E4-015 to NFR-E4-019 | NFR § Observability | Logging, Flower, Metrics | Log output validation, Flower dashboard accessibility, Metrics storage verification |

## Risks, Assumptions, Open Questions

### Risks

**R-E4-001: PyTorch Dependency Conflict Recurrence (Medium)**
- **Risk:** Future PyTorch updates may introduce new CUDA compatibility issues
- **Impact:** Worker containers fail to build or run
- **Mitigation:** Lock PyTorch versions in requirements files, test upgrades in staging before production
- **Owner:** Story 4.1 (DevOps)
- **Probability:** Medium | **Impact:** High

**R-E4-002: Enhancement Pipeline Performance Degradation (Medium)**
- **Risk:** Full pipeline (VAD + Refine + Split) exceeds 25% overhead target on complex audio
- **Impact:** User experience degradation (longer wait times)
- **Mitigation:** Individual component toggle flags allow disabling expensive components, performance profiling in Story 4.5
- **Owner:** Story 4.5 (Backend)
- **Probability:** Medium | **Impact:** Medium

**R-E4-003: GPU Resource Exhaustion (High)**
- **Risk:** Concurrent jobs exceed available GPU memory, causing OOM errors
- **Impact:** Worker crashes, job failures
- **Mitigation:** One job per worker constraint (NFR-E4-004), Docker GPU resource limits, queue depth monitoring
- **Owner:** Story 4.1 (DevOps) + Story 4.6 (Monitoring)
- **Probability:** High | **Impact:** High

**R-E4-004: Quality Regression Undetected (Medium)**
- **Risk:** Epic 4 changes degrade transcription quality but regression tests miss it
- **Impact:** MVP ships with lower quality than Epic 3 baseline
- **Mitigation:** Story 4.6 comprehensive baseline testing, >15% degradation threshold triggers rollback
- **Owner:** Story 4.6 (QA)
- **Probability:** Low | **Impact:** High

**R-E4-005: Model Router Auto-Selection Logic Failure (Low)**
- **Risk:** Language detection errors cause Chinese audio routed to WhisperX (suboptimal) or vice versa
- **Impact:** User receives lower quality transcription
- **Mitigation:** Extensive language detection testing, manual model override via config (Story 4.7 technical debt)
- **Owner:** Story 4.1 (Backend)
- **Probability:** Low | **Impact:** Medium

**R-E4-006: Docker Image Size Bloat (Low)**
- **Risk:** Both worker images >20GB each (models + dependencies)
- **Impact:** Slow deployment, high storage costs
- **Mitigation:** Multi-stage Docker builds, model caching volumes, layer optimization
- **Owner:** Story 4.1 (DevOps)
- **Probability:** Medium | **Impact:** Low

**R-E4-007: Parallel Development Track Merge Conflicts (Medium)**
- **Risk:** Track 1 (architecture) and Track 2 (components) produce conflicting code at Story 4.5 integration
- **Impact:** Integration delays, rework
- **Mitigation:** Clear interface contracts defined upfront, frequent communication between track owners
- **Owner:** Story 4.5 (Tech Lead)
- **Probability:** Medium | **Impact:** Medium

### Assumptions

**A-E4-001: NVIDIA Driver Availability**
- Assumption: Production host has NVIDIA driver ≥530 installed and functional
- Validation: Story 4.1 deployment testing documents driver requirements
- Risk if False: Worker containers won't access GPU, transcription fails

**A-E4-002: HuggingFace Model Availability**
- Assumption: Both BELLE-2 and WhisperX models remain publicly downloadable from HuggingFace
- Validation: Cold-start deployment test in Story 4.1
- Risk if False: Worker initialization fails, manual model download required

**A-E4-003: Redis Persistence Not Critical**
- Assumption: Job metadata loss (Redis restart) acceptable for Epic 4 (users can re-upload)
- Validation: Documented in Story 4.1 limitations
- Risk if False: User complaints about lost jobs, need Redis persistence config

**A-E4-004: Single GPU Per Worker Sufficient**
- Assumption: One GPU handles one concurrent job's transcription workload
- Validation: Epic 3 Story 3.2c validated single-GPU capacity for both models
- Risk if False: Need multi-GPU support (out of scope for Epic 4)

**A-E4-005: Frontend Unchanged for Epic 4**
- Assumption: Backend model selection doesn't require frontend changes (config-driven only)
- Validation: Story 4.7 verifies API backward compatibility
- Risk if False: Frontend work required, Epic 4 scope expands

**A-E4-006: Epic 3 Baseline Metrics Available**
- Assumption: Story 3.2c produced reliable baseline metrics for regression testing
- Validation: Story 4.6 loads `tests/regression/epic3_baselines.json`
- Risk if False: Create new baselines in Story 4.6 (extra work)

**A-E4-007: Parallel Tracks Can Execute Independently**
- Assumption: Stories 4.2-4.4 (components) don't need Story 4.1 (Docker) until Story 4.5
- Validation: Local `.venv` development validated in Epic 3
- Risk if False: Sequential development required, timeline extends +3 days

### Open Questions

**OQ-E4-001: MVP Model Selection Criteria (Story 4.7)**
- Question: Should MVP prioritize CER/WER (accuracy) or segment quality (subtitle compliance)?
- Impact: Determines which model selected for MVP
- Decision Maker: Product Manager (John) + Tech Lead
- Deadline: Story 4.7 execution
- Current Thinking: Lean toward BELLE-2 for Chinese focus, but WhisperX if broader language support valued

**OQ-E4-002: Enhancement Pipeline Default Configuration (Story 4.5)**
- Question: Should MVP default to full pipeline (vad,refine,split) or minimal (none)?
- Impact: Performance vs. quality trade-off
- Decision Maker: Tech Lead + UX Designer (Sally)
- Deadline: Story 4.5 execution
- Current Thinking: Start conservative (no enhancements), enable via config after validation

**OQ-E4-003: Worker Horizontal Scaling Strategy (Story 4.1)**
- Question: How many workers per model should default `docker-compose.yaml` deploy?
- Options: 1x each (minimal), 2x each (better throughput)
- Impact: GPU resource requirements, deployment complexity
- Decision Maker: DevOps + Product Manager
- Deadline: Story 4.1 execution
- Current Thinking: 1x each for MVP, document scaling instructions for future

**OQ-E4-004: Quality Validation Corpus Size (Story 4.6)**
- Question: How many test audio files needed for statistically significant quality validation?
- Options: 10 files (fast), 30 files (better), 100 files (comprehensive)
- Impact: Story 4.6 timeline, baseline accuracy
- Decision Maker: QA Lead (Murat) + Data Analyst
- Deadline: Story 4.6 execution
- Current Thinking: Start with 30 files (Epic 3 corpus), expand if variance too high

**OQ-E4-005: Flower Dashboard Authentication (Story 4.1)**
- Question: Should Flower monitoring dashboard require authentication or remain open on localhost?
- Impact: Security vs. convenience trade-off
- Decision Maker: DevOps + Security Review
- Deadline: Story 4.1 execution
- Current Thinking: No auth for localhost-only deployment, add HTTP Basic Auth if exposed

**OQ-E4-006: Enhancement Component Execution Order (Story 4.5)**
- Question: Is "vad,refine,split" the optimal pipeline order or should it be configurable?
- Impact: Enhancement quality, flexibility
- Decision Maker: Tech Lead + Backend Developer
- Deadline: Story 4.5 execution
- Current Thinking: Make order configurable via comma-separated list, document recommended orders

**OQ-E4-007: Rollback Testing Frequency (Story 4.6)**
- Question: How often should multi-worker → single-worker rollback be tested?
- Options: Once (Story 4.7 handoff), Monthly (CI/CD), Per deployment
- Impact: Rollback reliability confidence
- Decision Maker: DevOps + QA Lead
- Deadline: Story 4.7 execution
- Current Thinking: Test once in Story 4.7, document procedure, add to deployment checklist

## Test Strategy Summary

### Unit Testing Strategy

**Component-Level Tests (Stories 4.2-4.4):**
- Framework: pytest with pytest-mock
- Coverage Target: ≥85% for enhancement components
- Mock Strategy:
  - Audio files: Use `pytest-mock` to mock librosa/webrtcvad libraries
  - Segment data: Synthetic segment arrays with known properties
- Key Test Cases:
  - VAD: Test aggressiveness levels 0-3, edge cases (all silence, no silence)
  - Refiner: Boundary shift validation, search window edge cases
  - Splitter: Long segments (>7s), short segments (<1s), Chinese character handling
- Execution: `pytest tests/unit/` (fast, <5 minutes)

**Model Router Tests (Story 4.1):**
- Test auto-selection logic for different language codes
- Validate queue name mapping ("auto" + "zh" → "belle2")
- Test invalid model/language combinations

**Pipeline Tests (Story 4.5):**
- Test all pipeline combinations (8 total: empty, vad only, refine only, split only, vad+refine, vad+split, refine+split, all)
- Error injection tests (component throws exception)
- Metrics aggregation tests

### Integration Testing Strategy

**Multi-Worker Integration Tests (Stories 4.1, 4.5, 4.6):**
- Framework: pytest with Docker Compose testcontainers
- Environment: Spin up full stack (web, belle2-worker, whisperx-worker, redis, flower)
- Coverage Target: All API endpoints + both worker queues
- Key Test Scenarios:
  - Upload Chinese audio → verify belle2-worker processes it
  - Upload English audio → verify whisperx-worker processes it
  - Upload with enhancements enabled → verify pipeline applied
  - Kill one worker → verify system continues with remaining worker
- Execution: `pytest tests/integration/ -m multiworker` (slow, ~15 minutes)

**Enhancement Pipeline Integration Tests (Story 4.5):**
- Real audio files: 5-minute Chinese audio, 5-minute English audio, noisy audio sample
- Validate: Raw segments vs. enhanced segments differ as expected
- Metrics: VAD removes silence, refiner shifts boundaries, splitter increases segment count

**Cross-Model Quality Validation Tests (Story 4.6):**
- Corpus: 30 audio files (Chinese: 20, English: 10)
- Process each file through both BELLE-2 and WhisperX workers
- Generate quality metrics JSON for each
- Validate: Metrics match expected ranges from Epic 3 baselines

### Regression Testing Strategy

**Epic 3 Baseline Regression (Story 4.6):**
- Load baseline metrics from `tests/regression/epic3_baselines.json`
- Re-transcribe Epic 3 test corpus with Epic 4 configuration
- Assert: CER/WER degradation ≤15%, segment compliance degradation ≤10%
- Execution: `pytest tests/regression/test_epic3_baseline.py`

**MVP Backward Compatibility Regression (Story 4.7):**
- Execute all Epic 1-3 integration tests against Epic 4 codebase
- Assert: All tests pass (API contracts unchanged)
- Validates: Frontend remains functional, no breaking changes

### Performance Testing Strategy

**Worker Performance Benchmarks (Story 4.6):**
- Test Cases:
  - 10-minute audio: Both models, with/without enhancements
  - 60-minute audio: Both models, with/without enhancements
- Metrics:
  - Transcription time (target: 1-2x real-time, NFR-E4-001)
  - Enhancement overhead (target: ≤25%, NFR-E4-002)
  - Total end-to-end time
- Tools: Custom benchmark script with timing decorators

**Concurrent Job Stress Testing (Story 4.6):**
- Scenario: Submit 10 jobs simultaneously
- Expected Behavior: 2 process concurrently (one per worker), 8 queued
- Metrics: Queue depth, worker utilization, job completion time
- Validates: NFR-E4-004 (one job per worker)

**Enhancement Component Performance (Stories 4.2-4.5):**
- Individual benchmarks per component:
  - VAD: 60-minute audio → <5 minutes processing
  - Refiner: 500 segments → <5 minutes processing
  - Splitter: 500 segments → <3 minutes processing
- Alerts: Log warning if thresholds exceeded

### Manual Testing Checklist (Story 4.7)

**Deployment Validation:**
- [ ] Build both Docker images successfully (belle2, whisperx)
- [ ] `docker-compose up -d` starts all services without errors
- [ ] Flower dashboard accessible at `http://localhost:5555`
- [ ] Both workers show "active" status in Flower
- [ ] GPU memory visible in worker logs (nvidia-smi output)

**Functional Validation:**
- [ ] Upload Chinese audio → BELLE-2 worker processes it (check logs)
- [ ] Upload English audio → WhisperX worker processes it (check logs)
- [ ] Enhancement pipeline applied (check result metadata for component metrics)
- [ ] Export functionality still works (SRT/TXT download)
- [ ] Frontend unchanged (no visual regressions)

**Rollback Validation:**
- [ ] Comment out one worker in docker-compose.yaml
- [ ] `docker-compose up -d` → single-worker mode
- [ ] Upload job → processes successfully on remaining worker
- [ ] Rollback completes in <10 minutes (NFR-E4-014)

**Documentation Validation:**
- [ ] Deployment guide accurate (can follow steps on clean system)
- [ ] Troubleshooting section addresses common issues
- [ ] Epic 4 handoff documentation complete (architecture, stories, testing)

### Test Automation Strategy

**CI/CD Pipeline (Story 4.7):**
```yaml
# .github/workflows/epic4-ci.yml
name: Epic 4 Multi-Worker CI

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/unit/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
    steps:
      - uses: actions/checkout@v3
      - run: docker-compose -f docker-compose.test.yaml up -d
      - run: pytest tests/integration/ -m multiworker
      - run: docker-compose down

  regression-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pytest tests/regression/test_epic3_baseline.py
```

**Test Execution Frequency:**
- Unit tests: Every commit (fast, <5 min)
- Integration tests: Every PR merge (moderate, ~15 min)
- Regression tests: Nightly + pre-release (slow, ~30 min)
- Performance benchmarks: Weekly + pre-release (very slow, ~1 hour)
- Manual testing: Pre-release only (Story 4.7 checklist)
