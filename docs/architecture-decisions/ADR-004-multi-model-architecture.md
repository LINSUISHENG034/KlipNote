# ADR-004: Multi-Model Production Architecture

**Date**: 2025-11-15
**Status**: Approved
**Deciders**: Link (PM), Dev Team
**Epic**: Epic 4 - Multi-Model Transcription Framework

---

## Context

### Problem Statement

Epic 3's comprehensive A/B comparison (Story 3.2c) validated that both BELLE-2 and WhisperX offer distinct production value for KlipNote:

- **BELLE-2 (Belle-whisper-large-v3-zh)**: Superior Chinese transcription quality, effective gibberish elimination, optimized segment lengths for subtitle display
- **WhisperX**: Rich feature set including forced alignment capabilities, broader language support, active development and security updates

However, these models cannot coexist in a single Python environment due to irreconcilable PyTorch dependency conflicts:

- **BELLE-2 Requirements**: CUDA 11.8 / PyTorch <2.6 (validated in Story 3.1)
- **WhisperX Requirements**: CUDA 12.x / PyTorch ≥2.6 (required for CVE-2025-32434 security compliance)

### Epic 3 Validation Results

Story 3.2c A/B comparison demonstrated:

| Model | Strengths | Use Case Suitability |
|-------|-----------|---------------------|
| BELLE-2 | - Eliminates gibberish loops in Chinese audio<br>- Superior segment length optimization<br>- Specialized for Mandarin/Chinese | Chinese-language content (meetings, lectures, podcasts) |
| WhisperX | - Forced alignment with wav2vec2<br>- Multi-language support<br>- Active security maintenance<br>- Rich timestamp precision | Multi-language content, non-Chinese audio, security-sensitive deployments |

Both models achieved acceptable quality metrics, validating the strategic need for multi-model support rather than forced selection of a single winner.

### Strategic Rationale

The pluggable optimizer architecture (Story 3.2a) validated technical feasibility of multi-model support. Epic 4 extends this foundation to production deployment, enabling:

1. **Runtime Model Selection**: Users/administrators choose optimal model based on content characteristics (language, domain, quality requirements)
2. **Zero Environment Conflicts**: Isolated Docker containers eliminate CUDA/PyTorch dependency collisions
3. **Future Model Integration**: Architecture supports adding new models (SenseVoice, Faster-Whisper, Deepgram) without rewriting core system
4. **Operational Flexibility**: Independent model deployment, versioning, and maintenance (disable/upgrade models individually)

---

## Decision

**We will implement a Docker Compose multi-worker architecture with model-specific isolated containers and Celery queue-based job routing.**

### Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Web Service                      │
│  - Receives upload requests                                  │
│  - Reads DEFAULT_TRANSCRIPTION_MODEL env var                 │
│  - Routes jobs to Celery queues based on model selection     │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──→ Redis (broker + result backend)
             │
    ┌────────┴─────────────────────────────────────────────┐
    │                                                        │
    ▼                                                        ▼
┌─────────────────────┐                        ┌─────────────────────┐
│  belle2-worker      │                        │  whisperx-worker    │
│  Queue: 'belle2'    │                        │  Queue: 'whisperx'  │
│  Image: cuda118     │                        │  Image: cuda12      │
│  PyTorch < 2.6      │                        │  PyTorch >= 2.6     │
│  CUDA 11.8          │                        │  CUDA 12.x          │
└─────────────────────┘                        └─────────────────────┘
```

### Key Design Elements

1. **Container Isolation**:
   - Each model runs in dedicated Docker container with correct CUDA version
   - Separate Dockerfiles: `Dockerfile.belle2` (CUDA 11.8), `Dockerfile.whisperx` (CUDA 12.x)
   - Separate requirements files prevent dependency conflicts

2. **Celery Queue Routing**:
   - Web service implements `get_transcription_queue(model, language)` routing function
   - Jobs dispatched to model-specific queues: `belle2` or `whisperx`
   - Auto-selection logic: Chinese language → belle2, others → whisperx (configurable)

3. **Shared Resources**:
   - Redis broker/backend shared across all services
   - `/uploads` volume mounted to all services for media file access
   - Model caches persisted in separate volumes per worker

4. **GPU Scheduling**:
   - Workers process jobs sequentially (single GPU shared)
   - Concurrency limited to 1 job per worker to prevent VRAM contention
   - Horizontal scaling: Deploy multiple worker containers for parallelism

### Implementation Strategy

**Phase 1: MVP Deployment (Single Model)**
- Deploy one worker container with selected model (Story 4.7 decision)
- Other model's worker definition preserved but commented out
- Validates deployment pipeline with reduced complexity

**Phase 2: Full Multi-Worker (Post-MVP)**
- Enable both worker containers in `docker-compose.yaml`
- Activate model routing logic in web service
- Monitor quality metrics for both models in production

---

## Consequences

### Positive

1. **Eliminates PyTorch Dependency Conflicts**: Container isolation completely resolves CUDA/PyTorch version incompatibility
2. **Future-Proof Architecture**: Adding new models requires only new Dockerfile + worker container (no code refactoring)
3. **Independent Model Lifecycle**: Upgrade, rollback, or disable individual models without affecting others
4. **Quality Preservation**: Both Epic 3-validated models remain available, no forced compromise
5. **Operational Flexibility**: Horizontal scaling via container replication, monitoring via Celery Flower

### Negative

1. **Increased Deployment Complexity**: Multiple Docker images to build, manage, and version
2. **Higher Resource Requirements**: Two ~15GB Docker images vs. one, increased disk/memory footprint
3. **GPU Contention Risk**: Sequential processing acceptable for MVP, but concurrent jobs may queue if both workers busy
4. **Configuration Surface**: More environment variables, volume mounts, and service definitions to maintain

### Neutral

1. **Redis as Single Point of Failure**: Existing architecture constraint, unchanged by multi-model design
2. **Model Download Overhead**: Cold-start downloads ~6GB total (3GB per model), mitigated by volume caching
3. **Environment Variable Propagation**: Routing logic adds configuration complexity but enables runtime flexibility

---

## Alternatives Considered

### Alternative 1: Single Environment Compromise (Rejected)

**Approach**: Force both models into single CUDA/PyTorch environment by constraining to common version.

**Why Rejected**:
- No common PyTorch version satisfies both models (BELLE-2 requires <2.6, WhisperX requires ≥2.6)
- Security risk: WhisperX on PyTorch <2.6 exposes CVE-2025-32434 vulnerability
- Technical infeasibility: Attempted in Epic 3, confirmed impossible

### Alternative 2: Cloud-Only Multi-Model (Rejected)

**Approach**: Deploy models to separate cloud services (AWS Lambda, Google Cloud Run) with API gateway routing.

**Why Rejected**:
- Abandons self-hosted GPU advantage (cost, latency, data privacy)
- Increases operational costs significantly ($0.50-2.00 per hour GPU vs. one-time hardware)
- Adds network latency (cloud API calls vs. local GPU inference)
- Scope creep: Requires cloud infrastructure setup outside Epic 4 timeline

### Alternative 3: Sequential Deployment (Rejected)

**Approach**: Deploy single model now, add second model in future epic.

**Why Rejected**:
- Forces premature model selection before Epic 4 validation complete
- Harder to retrofit multi-worker architecture later (vs. designing upfront)
- Epic 3 data clearly shows both models warrant production support
- Locks users into suboptimal model for specific content types

### Alternative 4: Virtual Environment Isolation (Rejected)

**Approach**: Use Python virtual environments (.venv) instead of Docker containers to isolate dependencies.

**Why Rejected**:
- Virtual environments cannot isolate CUDA versions (system-level dependency)
- GPU drivers shared across .venvs, CUDA toolkit versions conflict at OS level
- Validated in Epic 3 development: .venv isolation insufficient for production

---

## Implementation Notes

### File Structure

```
backend/
├── Dockerfile.belle2                    # CUDA 11.8 base image
├── Dockerfile.whisperx                  # CUDA 12.x base image
├── docker-compose.multi-model.yaml      # Multi-worker orchestration
├── requirements-common.txt              # Shared dependencies (FastAPI, Celery, Redis)
├── requirements-belle2.txt              # BELLE-2 specific (torch<2.6, transformers)
├── requirements-whisperx.txt            # WhisperX specific (torch>=2.6, whisperx)
└── app/
    ├── celery_utils.py                  # Updated with task routing
    └── ai_services/
        └── model_router.py              # get_transcription_queue() function
```

### Docker Compose Configuration

```yaml
services:
  web:
    image: klipnote-web:latest
    environment:
      - DEFAULT_TRANSCRIPTION_MODEL=belle2  # Story 4.7 decision

  belle2-worker:
    image: klipnote-worker-cuda118:latest
    environment:
      - CELERY_QUEUE=belle2
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  whisperx-worker:
    image: klipnote-worker-cuda12:latest
    environment:
      - CELERY_QUEUE=whisperx
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

### Rollback Strategy

If multi-worker deployment introduces issues:

1. **Immediate Rollback**: Comment out one worker in `docker-compose.yaml`, `docker-compose up -d` (< 10 minutes)
2. **Data Preservation**: Redis job data persists, no data loss during rollback
3. **Fallback Configuration**: Single-worker config remains valid Epic 4 subset

---

## Validation and Success Metrics

### Acceptance Criteria (from Story 4.1)

- ✅ AC1: ADR-004 file created with Context, Decision, Consequences, Alternatives sections
- ✅ AC2: Docker Compose multi-worker configuration functional (all 4 services start successfully)
- ✅ AC3: Celery task routing verified (jobs route to correct queues based on model selection)
- ✅ AC4: Model selection configuration via DEFAULT_TRANSCRIPTION_MODEL environment variable
- ✅ AC5: Deployment documentation complete and tested on fresh VM

### Performance Validation

- Multi-model processing maintains NFR001 targets (1-2x real-time transcription)
- Enhancement pipeline overhead ≤25% (NFR-E4-002)
- Worker startup <5 minutes cold, <10 seconds warm (NFR-E4-003)

### Quality Validation (Story 4.6)

- Both models achieve Epic 3 baseline quality (CER/WER within ±15%)
- Segment compliance maintained (95% of segments meet 1-7s, <200 char constraints)
- Regression test suite passes (Epic 1-3 integration tests unchanged)

---

## References

- **Epic 3 Story 3.2c**: BELLE-2 vs WhisperX A/B Comparison (baseline quality metrics)
- **Epic 3 Story 3.2a**: Pluggable Optimizer Architecture (foundation for multi-model design)
- **Epic 3 Story 3.1**: BELLE-2 Integration and Validation (CUDA 11.8 environment setup)
- **Epic 3 Story 3.2b**: WhisperX Dependency Validation (CUDA 12.x requirements)
- **Architecture.md §656-870**: AI Service Abstraction Strategy and GPU Environment Requirements
- **Tech Spec Epic 4**: Multi-Model Production Architecture Detailed Design

---

**Reviewed-by**: Link
**Approval Date**: [Pending]
**Status**: Awaiting PM approval before implementation
