# Epic Technical Specification: Multi-Model Transcription Foundation

Date: 2025-11-10
Author: Link
Epic ID: 3
Status: Draft

---

## Overview

Epic 3 establishes a multi-model transcription foundation to dramatically improve Mandarin Chinese ASR accuracy while maintaining KlipNote's offline, self-hosted architecture. The current WhisperX pipeline produces severe quality issues on Mandarin audio—generating repetitive "gibberish loops" (e.g., "我用了一尾" repeated dozens of times in `case1` reference transcripts)—while the Const-me Whisper Desktop benchmark demonstrates that high-quality Mandarin transcription is achievable using the same base models with proper decoder configuration.

This epic delivers a pluggable ASR architecture that integrates **BELLE-2 whisper-large-v3-zh** (a full fine-tune of Whisper large-v3 achieving 24-65% relative CER reduction) as the default Mandarin decoder, adds **model routing logic** to automatically select optimal engines per language/use-case, and establishes a **quality validation framework** comparing outputs against reference transcripts (Const-me baseline). A pilot implementation of **SenseVoice-Small** (FunAudioLLM's non-autoregressive model achieving ~15× faster inference) validates low-latency paths for future optimization.

The epic also implements comprehensive **monitoring and logging** to track WER/CER metrics across models, plus deployment tooling and documentation for maintaining multiple ASR runtimes within the RTX 3070 Ti 16GB GPU constraint.

## Objectives and Scope

**In Scope:**

- **BELLE-2 Integration (Story 3.1):** Replace current Whisper decoder with BELLE-2 whisper-large-v3-zh for Mandarin audio, preserving timestamp alignment and existing WhisperX tooling
- **Model Routing Logic (Story 3.2):** Implement ASR engine abstraction layer with automatic language detection and model selection (Whisper for English, BELLE-2 for Mandarin, extensible for future engines)
- **Quality Validation Framework (Story 3.3):** Build automated regression harness comparing transcription outputs against Const-me reference transcripts, measuring WER/CER and timestamp stability
- **SenseVoice Pilot (Story 3.4):** Integrate FunASR SenseVoice-Small ONNX runtime as optional backend, benchmark latency and accuracy on RTX 3070 Ti hardware
- **Monitoring & Logging (Story 3.5):** Add structured logging for model selection decisions, transcription quality metrics, and performance tracking (latency, throughput, GPU utilization)
- **Documentation & Deployment (Story 3.6):** Document multi-model architecture, create deployment guides for BELLE-2 and SenseVoice runtimes, update user-facing accuracy expectations

**Out of Scope:**

- **Paraformer integration:** Deferred to post-Epic 3 (research identified as viable but BELLE-2 + SenseVoice sufficient for MVP)
- **FireRedASR integration:** Requires ≥40GB VRAM (exceeds RTX 3070 Ti constraint); future consideration for high-accuracy mode
- **Fine-tuning on custom data:** Epic 3 uses pretrained models; domain adaptation left for Phase 2
- **Real-time streaming transcription:** Focus on batch/offline processing; streaming deferred to future epic
- **Multi-language mixing within single file:** Initial routing assumes single dominant language per audio file
- **Advanced model ensembling:** Simple routing logic only; weighted ensemble or confidence-based fallback left for future optimization

**Success Criteria:**

- Mandarin transcription quality matches or exceeds Const-me Whisper Desktop baseline (measured via automated WER/CER comparison on `case1` reference corpus)
- Zero regression in English transcription accuracy
- Timestamp alignment stability maintained across all models (click-to-timestamp functionality unaffected)
- Model switching overhead <5 seconds per job
- SenseVoice pilot demonstrates ≤1.5× realtime latency on RTX 3070 Ti (validates future optimization path)

## System Architecture Alignment

**Components Referenced:**

1. **AI Services Layer (`app/ai_services/`):** Epic 3 expands the existing `TranscriptionService` abstract interface (architecture.md lines 666-706) to support multiple implementations:
   - `whisperx_service.py` (existing)
   - `belle2_service.py` (new - Story 3.1)
   - `sensevoice_service.py` (new - Story 3.4)
   - `model_router.py` (new - Story 3.2)

2. **Celery Tasks (`app/tasks/transcription.py`):** Modified to invoke `model_router.select_engine()` before transcription, log model selection decisions, and capture quality metrics

3. **File Storage (`/uploads/{job_id}/`):** Extended to store:
   - `model_metadata.json` (selected engine, language detected, model version)
   - `quality_metrics.json` (WER/CER if reference available, confidence scores)

4. **Redis Progress Tracking:** Status messages updated to include model selection info (e.g., "Loading BELLE-2 model for Mandarin...", "Transcribing with SenseVoice-Small...")

**Constraints Satisfied:**

- **GPU Memory (NFR-004, Architecture Decision):** BELLE-2 maintains Whisper large-v3 footprint (~1.55B parameters, fits within RTX 3070 Ti 16GB); SenseVoice-Small (~220M parameters) fits comfortably with headroom for concurrency
- **Performance (NFR-001):** BELLE-2 targets same 1-2× realtime throughput as current Whisper; SenseVoice pilot aims for <1× realtime (70ms per 10s audio per research)
- **Compatibility (NFR-004):** Model routing transparent to frontend; existing API contracts (`/upload`, `/status`, `/result`) unchanged
- **Reliability (NFR-003):** Quality validation framework prevents deployment of regression-prone models

**Architecture Pattern Extensions:**

- **Service Abstraction (architecture.md lines 650-706):** Epic 3 proves the AI service abstraction strategy by adding two new implementations without frontend changes
- **Pluggable Runtime Strategy:** BELLE-2 uses HuggingFace Transformers (existing), SenseVoice requires FunASR runtime (containerized separately to isolate dependencies)
- **Quality Gate Integration:** Regression harness (Story 3.3) runs as part of CI/CD before model promotions, aligning with Testing Strategy (architecture.md lines 806-1071)

## Detailed Design

### Services and Modules

| Module | Responsibility | Inputs | Outputs | Owner |
|--------|---------------|--------|---------|-------|
| **`belle2_service.py`** | BELLE-2 Whisper-L3-zh transcription for Mandarin audio | Audio file path, language="zh" | Segment list with timestamps | Story 3.1 |
| **`sensevoice_service.py`** | FunASR SenseVoice-Small ONNX runtime wrapper | Audio file path, config params | Segment list with timestamps | Story 3.4 |
| **`model_router.py`** | Language detection and ASR engine selection logic | Audio file path, user preferences | Selected engine instance | Story 3.2 |
| **`quality_validator.py`** | WER/CER calculation and regression checking | Hypothesis transcript, reference transcript | Quality metrics dict | Story 3.3 |
| **`transcription_logger.py`** | Structured logging for model selection, performance metrics | Job metadata, timing data, model selection | Log entries to stdout/file | Story 3.5 |
| **`model_manager.py`** | Lazy model loading, caching, GPU memory management | Model name, device config | Loaded model instance | Story 3.1, 3.4 |

**Module Implementation Notes:**

- **`belle2_service.py`:** Implements `TranscriptionService` interface, uses HuggingFace Transformers to load BELLE-2 model, configures Chinese-specific decoder settings (forced language ID, temperature fallback, beam search)
- **`model_router.py`:** Uses Whisper-small for fast 30-second language detection, maintains engine registry, logs selection decisions with reasoning
- **`quality_validator.py`:** Uses `jiwer` library for WER/CER calculation, implements repetition detection via n-gram counting, compares against reference transcripts in `/reference/{job_id}/` directory
- **`model_manager.py`:** Lazy-loads models to conserve GPU memory, implements LRU cache for frequently-used models, monitors VRAM usage

### Data Models and Contracts

**Model Metadata (stored as `model_metadata.json`):**
```python
class ModelMetadata(BaseModel):
    job_id: str
    selected_engine: str  # "whisperx", "belle2", "sensevoice"
    model_version: str  # e.g., "BELLE-2/Belle-whisper-large-v3-zh"
    detected_language: str  # "en", "zh", "auto"
    user_language_hint: Optional[str]
    model_load_time_ms: float
    selection_reason: str  # "user_hint", "detected_chinese", "default"
    timestamp: str  # ISO 8601
```

**Quality Metrics (stored as `quality_metrics.json`):**
```python
class QualityMetrics(BaseModel):
    job_id: str
    wer: Optional[float]  # None if no reference
    cer: Optional[float]
    timestamp_drift_ms: Optional[float]
    has_repetitions: bool
    passes_threshold: bool
    reference_available: bool
    validation_timestamp: str
```

**Transcription Segment (unchanged from Epic 1):**
```python
class TranscriptionSegment(BaseModel):
    start: float  # seconds
    end: float    # seconds
    text: str
```

**Router Configuration:**
```python
class RouterConfig(BaseModel):
    enable_belle2: bool = True
    enable_sensevoice: bool = False  # Pilot mode
    default_engine: str = "whisperx"
    language_detection_duration: int = 30  # seconds
    quality_validation_enabled: bool = True
    cer_threshold: float = 0.15
```

### APIs and Interfaces

**No new external API endpoints required.** Epic 3 changes are backend-only; existing endpoints remain unchanged:

- `POST /upload` → Unchanged
- `GET /status/{job_id}` → Enhanced status messages include model info
- `GET /result/{job_id}` → Unchanged (returns same segment format)
- `GET /media/{job_id}` → Unchanged
- `POST /export/{job_id}` → Unchanged

**Enhanced Status Response (backward compatible):**
```json
{
  "status": "processing",
  "progress": 40,
  "message": "Transcribing audio with BELLE-2 (Mandarin mode)...",
  "created_at": "2025-11-10T10:30:00Z",
  "updated_at": "2025-11-10T10:31:15Z",
  "model_info": {
    "engine": "belle2",
    "detected_language": "zh",
    "model_version": "BELLE-2/Belle-whisper-large-v3-zh"
  }
}
```

**Internal Service Interface (TranscriptionService abstract):**
```python
class TranscriptionService(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str = "auto") -> List[Dict]:
        """Returns: [{"start": 0.5, "end": 3.2, "text": "..."}]"""
        pass

    @abstractmethod
    def get_model_info(self) -> Dict:
        """Return model metadata for logging."""
        pass
```

### Workflows and Sequencing

**Transcription Job Flow (Epic 3 Enhanced):**

```
1. User uploads audio → POST /upload
   ↓
2. Celery task starts: transcribe_audio(job_id, file_path)
   ↓
3. Model Selection (NEW)
   - ModelRouter.select_engine(file_path, user_hint)
   - Quick language detection (30s sample)
   - Decision: WhisperX vs BELLE-2 vs SenseVoice
   - Log selection decision
   ↓
4. Model Loading (NEW)
   - ModelManager.load_model(selected_engine)
   - Update Redis: "Loading BELLE-2 model for Mandarin..."
   ↓
5. Transcription Processing
   - Engine-specific transcribe() call
   - Progress updates: "Transcribing audio with BELLE-2..."
   ↓
6. Quality Validation (NEW, if reference available)
   - QualityValidator.validate_against_reference()
   - Calculate WER/CER, detect repetitions
   - Store quality_metrics.json
   ↓
7. Metadata Storage (NEW)
   - Save model_metadata.json
   - Log performance metrics
   ↓
8. Store transcription.json → Redis status: "completed"
```

**Model Router Decision Tree:**

```
Audio File → User language hint?
  ├─ Yes (zh) → BELLE-2
  ├─ Yes (en) → WhisperX
  └─ No → Language Detection (30s sample)
       ↓
    Detected "zh"?
      ├─ Yes → BELLE-2
      └─ No → WhisperX (default)
```

## Non-Functional Requirements

### Performance

**Targets (from PRD NFR-001):**

- **Transcription Speed:** Maintain 1-2× realtime throughput for BELLE-2 (same as current Whisper large-v3); SenseVoice pilot targets <1× realtime (≤70ms per 10s audio)
- **Model Selection Overhead:** Language detection must complete in <5 seconds (30-second audio sample processed by Whisper-small)
- **Model Loading Time:** First load ≤30 seconds for BELLE-2 (model download on first use), subsequent loads <5 seconds (from cache)
- **Memory Footprint:** BELLE-2 maintains ~6GB VRAM (same as Whisper large-v3), SenseVoice-Small ~2GB VRAM, leaving headroom for 1-2 concurrent jobs on RTX 3070 Ti 16GB

**Performance Validation:**

- Benchmark 1-hour Mandarin audio on RTX 3070 Ti: BELLE-2 must complete in 30-60 minutes
- SenseVoice pilot must demonstrate <60 minutes for same 1-hour audio (validates 15× speedup claim)
- Quality validation overhead <2 seconds per job (WER/CER calculation on 1-hour transcript)
- Model router decision logic <100ms (excluding 5s language detection)

**Degradation Strategy:**

- If BELLE-2 load fails → fallback to WhisperX with warning log
- If GPU memory insufficient → queue job and retry after model unload
- If language detection times out → default to WhisperX (safe fallback)

### Security

**Threat Model Updates:**

Epic 3 introduces new attack surfaces related to model loading and external dependencies:

1. **Model Poisoning Risk:** BELLE-2 and SenseVoice models loaded from HuggingFace/ModelScope could be compromised
   - **Mitigation:** Pin exact model versions in requirements, verify SHA256 checksums on first download, document trusted model sources

2. **Dependency Chain Risk:** FunASR runtime (SenseVoice) introduces new Python dependencies
   - **Mitigation:** Isolate FunASR in separate Docker container, use `requirements-sensevoice.txt` for clear dependency boundaries, run security scans (`safety check`)

3. **Resource Exhaustion:** Multiple concurrent model loads could exhaust GPU memory
   - **Mitigation:** ModelManager enforces max concurrent models (default: 2), implements LRU eviction policy

**Security Requirements:**

- All model downloads use HTTPS (HuggingFace, ModelScope enforced)
- Model files stored in protected directory (`/models/` with restricted permissions)
- No user-provided model paths accepted (prevent path traversal)
- Logging sanitizes file paths to prevent information disclosure

**Privacy Considerations (from Domain Brief):**

- All processing remains local/offline (no cloud API calls)
- Model weights and inference entirely on user-controlled hardware
- No telemetry or model usage data transmitted externally
- Quality metrics stored locally alongside transcription results

### Reliability/Availability

**Failure Handling:**

1. **Model Load Failure:** Log error, fallback to WhisperX, update Redis status with fallback message
2. **Language Detection Failure:** Log warning, default to WhisperX, mark metadata as "unknown" language
3. **Quality Validation Failure:** Log error but do not block transcription, mark validation status as "error"
4. **VRAM Exhaustion:** Return HTTP 503, Celery retries with exponential backoff (3 attempts)

**Availability Targets:**

- Same 90%+ completion rate as Epic 1 (NFR-003)
- Model fallback strategy prevents hard failures
- Quality validation failures do not impact user-facing functionality
- Graceful degradation: English transcription always available (WhisperX fallback)

**Monitoring Requirements (Story 3.5):**

- Track model selection distribution (% BELLE-2 vs WhisperX vs SenseVoice)
- Alert if BELLE-2 load failure rate >10%
- Alert if language detection failure rate >5%
- Monitor GPU memory utilization (alert if >90% sustained)

### Observability

**Structured Logging Requirements (Story 3.5):**

```python
# Model Selection Logging
logger.info("model_selection", extra={
    "job_id": job_id,
    "detected_language": "zh",
    "selected_engine": "belle2",
    "selection_reason": "detected_chinese",
    "detection_confidence": 0.95,
    "detection_duration_ms": 4200
})

# Transcription Performance Logging
logger.info("transcription_complete", extra={
    "job_id": job_id,
    "engine": "belle2",
    "audio_duration_s": 3600,
    "processing_duration_s": 2100,
    "realtime_factor": 1.72,
    "vram_used_mb": 6200,
    "segment_count": 450
})

# Quality Validation Logging
logger.info("quality_validation", extra={
    "job_id": job_id,
    "engine": "belle2",
    "wer": 0.12,
    "cer": 0.06,
    "has_repetitions": False,
    "passes_threshold": True,
    "reference_available": True
})
```

**Metrics to Track (Story 3.5):**

- **Model Usage:** Count of jobs per engine (belle2, whisperx, sensevoice)
- **Language Distribution:** Count of detected languages (zh, en, other)
- **Quality Metrics:** Average WER/CER by engine and language
- **Performance:** P50/P95/P99 transcription latency by engine
- **Reliability:** Model load failure rate, fallback trigger rate
- **Resource Utilization:** GPU memory usage per engine, model cache hit rate

## Dependencies and Integrations

### Python Dependencies (Backend)

**New Dependencies for Epic 3:**

```txt
# Epic 3 - Multi-Model Transcription
transformers==4.36.0          # BELLE-2 model loading (HuggingFace)
jiwer==3.0.3                  # WER/CER calculation for quality validation
funasr==1.0.12                # SenseVoice runtime (Story 3.4)
onnxruntime-gpu==1.16.3       # SenseVoice ONNX inference
modelscope==1.11.0            # Alternative model hub for BELLE-2/SenseVoice
```

**Dependency Management:**

- Use `uv pip install` for all backend dependencies (per architecture.md)
- Pin exact versions to ensure reproducibility
- Separate `requirements-sensevoice.txt` for FunASR pilot (optional dependencies)
- Run `uv pip freeze > requirements.txt` after adding new packages

### Model Weights and Storage

**Model Download Locations:**

| Model | Source | Size | Download Path |
|-------|--------|------|---------------|
| BELLE-2 whisper-large-v3-zh | HuggingFace | ~3.1 GB | `/root/.cache/huggingface/hub/` |
| Whisper-small (language detection) | OpenAI | ~461 MB | `/root/.cache/whisper/` |
| SenseVoice-Small ONNX | ModelScope | ~220 MB | `/root/.cache/funasr/` |
| WhisperX large-v3 (existing) | OpenAI | ~2.9 GB | `/root/.cache/whisperx/` |

**Cache Volume Configuration:**

```yaml
# docker-compose.yaml
services:
  worker:
    volumes:
      - model-cache:/root/.cache  # Persist model downloads
      - ./uploads:/uploads

volumes:
  model-cache:
    driver: local
```

**First-Run Model Download Strategy:**

- Models downloaded on-demand during first job execution
- Download progress logged to Redis status: "Downloading BELLE-2 model (3.1 GB)... 45%"
- Subsequent jobs use cached models (fast startup)
- Environment variable `PRELOAD_MODELS=true` to download all models on container start

### Integration Points

**Existing System Integration:**

1. **Celery Tasks:** Add model router invocation before transcription, import `ModelRouter`, call `select_engine()`
2. **Redis Progress Tracking:** Enhanced status messages include `model_info` field (backward compatible)
3. **File Storage:** Add `model_metadata.json` and `quality_metrics.json` alongside existing files

**External System Integration:**

1. **HuggingFace Hub:** Download BELLE-2 model weights (public model, no auth required)
2. **ModelScope (optional):** Alternative source for China region or blocked networks

### Third-Party Tools

- **jiwer:** WER/CER calculation (MIT license)
- **HuggingFace Transformers:** BELLE-2 and Whisper model loading (Apache 2.0)
- **FunASR:** SenseVoice runtime (MIT license, Alibaba DAMO Academy)
- **ONNX Runtime:** Accelerated inference for SenseVoice (MIT license)

### Version Compatibility Matrix

| Component | Epic 1 Version | Epic 3 Version | Breaking Changes |
|-----------|---------------|----------------|------------------|
| Python | 3.12.x | 3.12.x | None |
| PyTorch | 2.1.0+cu118 | 2.1.0+cu118 | None |
| Transformers | N/A | 4.36.0 | None (additive) |
| jiwer | N/A | 3.0.3 | None (new) |
| FunASR | N/A | 1.0.12 | None (optional) |

## Acceptance Criteria (Authoritative)

**Epic-Level Acceptance Criteria:**

1. **Mandarin Quality Target:** BELLE-2 transcription on `reference/zh_quality_optimization/case1` audio achieves CER ≤0.15 and eliminates repetitive "gibberish loops" present in current pipeline
2. **English Quality Preservation:** WhisperX transcription on English test audio maintains same quality as Epic 1 baseline (zero regression)
3. **Model Routing Accuracy:** Language detection correctly identifies Mandarin vs English with ≥95% accuracy on test corpus (30 audio samples)
4. **Performance Baseline:** BELLE-2 transcription completes within 1-2× realtime on RTX 3070 Ti hardware (validated with 1-hour audio)
5. **Backward Compatibility:** All existing API endpoints function identically for frontend clients
6. **Deployment Readiness:** Documentation complete for deploying BELLE-2 on self-hosted infrastructure

**Story-Level Acceptance Criteria:**

**Story 3.1: BELLE-2 Integration**
1. `belle2_service.py` implements `TranscriptionService` interface with Chinese-optimized decoder settings
2. BELLE-2 model downloads from HuggingFace on first use, subsequent loads from cache in <5 seconds
3. Transcription output format matches existing WhisperX format
4. Timestamp alignment stability verified via click-to-timestamp navigation tests
5. Unit tests mock BELLE-2 model to avoid GPU dependency during CI
6. Integration test transcribes 5-minute Mandarin audio and verifies CER improvement
7. Memory footprint validated: ~6GB VRAM usage
8. Fallback mechanism tested: BELLE-2 load failure defaults to WhisperX with warning

**Story 3.2: Model Routing Logic**
1. `model_router.py` implements language detection using Whisper-small on 30-second samples
2. Router selects BELLE-2 for Mandarin (zh/zh-CN/zh-TW), WhisperX for English
3. User language hint overrides automatic detection
4. Model selection decisions logged with reasoning
5. Language detection completes in <5 seconds
6. Unit tests cover all routing branches

**Story 3.3: Quality Validation Framework**
1. `quality_validator.py` calculates WER/CER using `jiwer` library
2. Repetition loop detection via n-gram counting (3+ repetitions of 3-5 word phrases)
3. Regression harness compares against reference files in `/reference/{job_id}/`
4. Quality metrics stored in `quality_metrics.json`
5. Validation runs automatically if reference available, doesn't block job on failure
6. CLI tool provided for manual validation
7. Test suite validates `case1`: current pipeline fails, BELLE-2 passes

**Story 3.4: SenseVoice Pilot**
1. `sensevoice_service.py` implements `TranscriptionService` using FunASR ONNX runtime
2. Pilot mode enabled via `ENABLE_SENSEVOICE=true` environment variable
3. Latency benchmark: 1-hour audio completes in <60 minutes on RTX 3070 Ti
4. Accuracy benchmark: CER within ±5% of BELLE-2 on 10 Mandarin samples
5. FunASR dependencies isolated in `requirements-sensevoice.txt`
6. Integration test verifies segment format compatibility
7. Documentation includes setup instructions and known limitations

**Story 3.5: Monitoring & Logging**
1. Structured logging for model selection, performance metrics, quality validation
2. Log aggregation script generates daily reports (model usage, WER/CER, failures)
3. Alert thresholds configured for failure rates and resource usage
4. Logs output to stdout in JSON format
5. Sample Grafana dashboard mockup created
6. Documentation includes log schema reference and troubleshooting queries

**Story 3.6: Documentation & Deployment**
1. Architecture documentation updated with multi-model ASR section
2. Deployment guide created (`docs/deployment-epic3.md`)
3. User-facing documentation updated with accuracy expectations
4. README updated with new dependencies and environment variables
5. Migration guide created for Epic 2 → Epic 3 upgrade
6. Troubleshooting guide covers model downloads, VRAM, detection issues
7. Performance tuning guide documents optimization strategies
8. All examples tested on fresh Windows 10 + RTX 3070 Ti environment

## Traceability Mapping

| Acceptance Criterion | Spec Section(s) | Component(s)/API(s) | Test Idea |
|---------------------|----------------|---------------------|-----------|
| **AC1: Mandarin Quality (CER ≤0.15)** | Detailed Design → Belle2Service, Quality Validation | `belle2_service.py`, `quality_validator.py` | Integration test: transcribe `case1` audio, assert CER ≤0.15, assert no repetition loops detected |
| **AC2: English Quality Preservation** | Model Router → Fallback Logic | `model_router.py`, `whisperx_service.py` | Regression test: transcribe Epic 1 English baseline audio, compare WER against stored baseline, assert delta <0.02 |
| **AC3: Model Routing Accuracy (≥95%)** | Detailed Design → Model Router Decision Tree | `model_router.py` | Unit test: 30 labeled audio samples (15 zh, 15 en), assert language detection accuracy ≥95%, verify correct engine selected |
| **AC4: Performance (1-2× realtime)** | NFR Performance → Transcription Speed | `belle2_service.py`, Celery worker | Benchmark test: transcribe 1-hour Mandarin audio on RTX 3070 Ti, assert completion time 30-60 minutes, log realtime_factor |
| **AC5: Backward Compatibility** | APIs and Interfaces → No Breaking Changes | FastAPI endpoints, Redis status format | API contract test: frontend mock calls all endpoints, assert response schemas unchanged, assert new `model_info` field optional |
| **AC6: Deployment Readiness** | Documentation & Deployment (Story 3.6) | `docs/deployment-epic3.md`, README | Manual checklist: fresh VM setup following docs, verify BELLE-2 downloads, verify first transcription succeeds |
| **Story 3.1: BELLE-2 Interface** | Detailed Design → Services and Modules | `belle2_service.py` | Unit test: mock HuggingFace model, call `transcribe()`, assert returns List[Dict] with start/end/text keys |
| **Story 3.1: Timestamp Stability** | Detailed Design → Belle2Service, Workflows | `belle2_service.py`, WhisperX alignment | Integration test: transcribe 10-min audio, compare timestamps against WhisperX baseline, assert drift <200ms per segment |
| **Story 3.1: Fallback Mechanism** | NFR Reliability → Model Load Failure | `model_manager.py`, `belle2_service.py` | Fault injection test: simulate HuggingFace download failure, assert job defaults to WhisperX, assert warning logged |
| **Story 3.2: Language Detection** | Detailed Design → Model Router | `model_router.py._detect_language()` | Unit test: 30s audio samples (zh/en/mixed), assert correct language code returned, assert <5s execution time |
| **Story 3.2: User Hint Override** | Detailed Design → Model Router Decision Tree | `model_router.py.select_engine()` | Unit test: pass `user_hint="zh"` for English audio, assert BELLE-2 selected (user preference respected) |
| **Story 3.3: WER/CER Calculation** | Detailed Design → QualityValidator | `quality_validator.py` | Unit test: known hypothesis/reference pairs with known WER/CER values, assert calculations match expected within 0.01 |
| **Story 3.3: Repetition Detection** | Detailed Design → QualityValidator._detect_repetitions() | `quality_validator.py` | Unit test: synthetic transcript with repeated phrases, assert `has_repetitions=True`; normal transcript, assert `False` |
| **Story 3.3: Regression Harness** | Detailed Design → QualityValidator.validate_against_reference() | `quality_validator.py`, `/reference/{job_id}/` | Integration test: `case1` audio with known reference, assert validation detects current pipeline failure, BELLE-2 success |
| **Story 3.4: SenseVoice Latency** | NFR Performance → SenseVoice Targets | `sensevoice_service.py`, FunASR runtime | Benchmark test: 1-hour audio on RTX 3070 Ti, assert completion <60 minutes, log realtime_factor for comparison |
| **Story 3.4: SenseVoice Accuracy** | Detailed Design → SenseVoiceService | `sensevoice_service.py` | Integration test: 10 Mandarin samples, compare SenseVoice CER vs BELLE-2 CER, assert delta ≤0.05 (within ±5%) |
| **Story 3.5: Structured Logging** | NFR Observability → Logging Requirements | `transcription_logger.py`, Celery tasks | Integration test: run transcription, parse stdout logs, assert JSON format with required fields (job_id, engine, etc.) |
| **Story 3.5: Log Aggregation** | NFR Observability → Metrics to Track | Log parsing script | Functional test: generate 100 synthetic log entries, run aggregation script, assert daily report contains model usage distribution |
| **Story 3.6: Deployment Guide** | Documentation & Deployment | `docs/deployment-epic3.md` | Manual test: follow deployment guide on fresh Windows VM, verify BELLE-2 setup completes without errors |
| **Story 3.6: Migration Guide** | Documentation & Deployment | Migration guide document | Manual test: upgrade Epic 2 environment to Epic 3, verify existing jobs still work, verify new models available |

## Risks, Assumptions, Open Questions

**RISKS:**

1. **RISK: BELLE-2 Accuracy Expectations** - Research benchmarks use clean audio; noisy meeting recordings may not achieve same CER improvements
   - **Impact:** HIGH | **Likelihood:** MEDIUM
   - **Mitigation:** Validate on `case1` reference corpus before rollout; keep WhisperX fallback; document expectations conservatively

2. **RISK: GPU Memory Contention** - Multiple models simultaneously could exceed RTX 3070 Ti 16GB VRAM
   - **Impact:** MEDIUM | **Likelihood:** MEDIUM
   - **Mitigation:** ModelManager LRU cache (max 2 models); queue jobs when memory insufficient; alert at 90% VRAM

3. **RISK: Model Download Failures** - HuggingFace/ModelScope connectivity issues prevent first-time downloads
   - **Impact:** MEDIUM | **Likelihood:** LOW
   - **Mitigation:** Pre-download during deployment (`PRELOAD_MODELS=true`); offline installation docs; retry logic

4. **RISK: Timestamp Drift with BELLE-2** - Fine-tuning may affect alignment, breaking click-to-timestamp
   - **Impact:** HIGH | **Likelihood:** LOW
   - **Mitigation:** Comprehensive timestamp stability testing; regression tests vs WhisperX baseline; rollback plan if drift >200ms

5. **RISK: SenseVoice Accuracy Not Meeting Expectations** - 15× speedup claims may not translate; FunASR stability unknown
   - **Impact:** LOW | **Likelihood:** MEDIUM
   - **Mitigation:** Isolated pilot (opt-in only); comprehensive benchmarking; clear pilot status documentation

6. **RISK: Language Detection False Positives** - Whisper-small may misclassify mixed-language or accented speech
   - **Impact:** MEDIUM | **Likelihood:** MEDIUM
   - **Mitigation:** User language hint override; log confidence scores; future: confidence threshold → user confirmation

**ASSUMPTIONS:**

1. RTX 3070 Ti GPU availability unchanged from Epic 1/2
2. BELLE-2 and SenseVoice models remain publicly accessible on HuggingFace/ModelScope
3. `case1` reference transcripts accurately represent typical meeting audio quality
4. WhisperX English performance remains unchanged
5. Model licensing (Apache 2.0, MIT) allows commercial self-hosted use
6. Celery infrastructure handles model loading overhead without additional provisioning
7. Users have internet access for initial model downloads (~10GB total)

**OPEN QUESTIONS:**

1. **Q: Should language detection be exposed to frontend for user override?**
   - **Resolution:** Story 3.2 implements API parameter `language_hint`; frontend UI deferred to future epic

2. **Q: What CER threshold should trigger quality alerts?**
   - **Resolution:** Start with fixed 0.15 threshold; collect data during Epic 3; tune in Epic 4 based on observed distribution

3. **Q: Should SenseVoice pilot be enabled by default?**
   - **Resolution:** Story 3.4 implements opt-in pilot (`ENABLE_SENSEVOICE=false` default); promote in Epic 4 if benchmarks pass

4. **Q: How to handle model version updates?**
   - **Resolution:** Pin exact model revision in code; document manual upgrade process; future automation in Phase 2

## Test Strategy Summary

**Test Pyramid:**

```
         E2E Tests (Story 2.7 + Epic 3 validation)
              /\
             /  \
    Integration Tests (Stories 3.1, 3.3, 3.4)
          /          \
    Unit Tests (All stories, ~70% coverage)
```

**Testing Scope by Story:**

**Story 3.1: BELLE-2 Integration**
- Unit: Mock HuggingFace, test `belle2_service.py` methods, verify output format
- Integration: Real BELLE-2 model, transcribe 5-min audio, compare CER vs baseline
- Performance: Benchmark 1-hour audio, measure realtime factor and VRAM usage
- Regression: Transcribe `case1`, assert CER ≤0.15 and no repetition loops

**Story 3.2: Model Routing Logic**
- Unit: Mock language detection, test all routing branches, verify logging
- Integration: 30 labeled samples, measure detection accuracy (≥95%)
- Performance: Measure detection latency on various audio lengths

**Story 3.3: Quality Validation Framework**
- Unit: Test WER/CER calculation, repetition detection with synthetic transcripts
- Integration: Validate `case1` corpus (current pipeline fails, BELLE-2 passes)
- Regression: Automated harness runs on every PR

**Story 3.4: SenseVoice Pilot**
- Unit: Mock FunASR, test `sensevoice_service.py`
- Integration: 10 Mandarin samples, compare CER vs BELLE-2 (≤5% delta)
- Performance: Benchmark latency (target <1× realtime)
- Compatibility: Verify segment format matches WhisperX

**Story 3.5: Monitoring & Logging**
- Unit: Test log formatting, JSON schema compliance
- Integration: Generate 100 logs, run aggregation script
- Functional: Simulate alert conditions, verify triggers

**Story 3.6: Documentation & Deployment**
- Manual: Fresh VM setup following deployment guide
- Validation: Follow migration guide on Epic 2 environment
- Documentation: Verify all code examples execute

**Test Data Requirements:**

- Mandarin Corpus: 30 samples (15× 5-min, 15× 30-min) covering meetings, casual, technical
- English Corpus: 30 samples matching Epic 1 (regression validation)
- Reference Transcripts: Ground truth for 10 Mandarin samples
- Case1 Corpus: Existing `reference/zh_quality_optimization/case1`

**Test Environments:**

- Development: Local Windows 10 + RTX 3070 Ti, mocked GPU for CI
- Integration: Docker + GPU passthrough, full model downloads
- Staging: Production-like with GPU, 10 concurrent user load

**Continuous Integration:**

- PR Tests: Unit tests only (mocked models, no GPU), GitHub Actions
- Nightly Tests: Integration tests with real models, self-hosted GPU runner
- Release Tests: Full regression + benchmarks before Epic 3 release

**Success Metrics:**

- Unit Test Coverage: ≥70% for new `ai_services/` modules
- Integration Coverage: All critical paths covered
- Performance: All benchmarks meet NFR-001 targets
- Regression: Zero English quality loss, Mandarin CER ≤0.15 on `case1`
