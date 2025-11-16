# KlipNote Multi-Worker Deployment Guide

**Epic 4 - Multi-Model Production Architecture**
**Date**: 2025-11-15
**Version**: 1.0.0

---

## Overview

This guide covers deploying KlipNote with **multi-worker Docker Compose architecture**, supporting both BELLE-2 and WhisperX transcription models in isolated GPU environments.

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Web Service                          │
│  • Receives uploads (POST /upload)                               │
│  • Routes jobs to belle2 or whisperx queues                      │
│  • Configuration: DEFAULT_TRANSCRIPTION_MODEL env var            │
└────────────┬──────────────────────────────────────────────────┬─┘
             │                                                    │
             │                Redis (broker + backend)           │
             │                                                    │
    ┌────────┴─────────────┐                        ┌────────────┴──────────┐
    │  belle2-worker       │                        │  whisperx-worker      │
    │  Queue: 'belle2'     │                        │  Queue: 'whisperx'    │
    │  CUDA 11.8           │                        │  CUDA 12.x            │
    │  PyTorch < 2.6       │                        │  PyTorch >= 2.6       │
    │  Chinese-optimized   │                        │  Multi-language       │
    └──────────────────────┘                        └───────────────────────┘
```

---

## Prerequisites

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **GPU** | NVIDIA GPU with 8GB VRAM | 12GB+ VRAM (RTX 3060, A4000, A6000) |
| **NVIDIA Driver** | ≥530.x (supports CUDA 11.8 + 12.x) | Latest stable driver |
| **Docker** | 20.10.0+ | Latest Docker Engine |
| **Docker Compose** | 1.29.0+ (Compose V2 recommended) | 2.29.7+ |
| **Disk Space** | 50GB (models + images) | 100GB+ |
| **RAM** | 16GB | 32GB+ |

### GPU Compatibility Validation

**Verify NVIDIA driver supports both CUDA 11.8 and 12.x:**

```bash
nvidia-smi
```

Expected output:
```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 550.54.15      Driver Version: 550.54.15      CUDA Version: 12.4             |
|---------------------------+----------------------+---------------------------------------|
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC             |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M.            |
|===============================+======================+=====================================|
|   0  NVIDIA RTX 4090     On   | 00000000:01:00.0  On |                  Off             |
| 30%   45C    P8    20W / 450W |   1024MiB / 24564MiB |      5%      Default            |
+---------------------------+----------------------+---------------------------------------+
```

**Critical**: CUDA Version in `nvidia-smi` output should be ≥12.1 (forward-compatible with both 11.8 and 12.x containers).

**Verify Docker GPU runtime:**

```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi
```

Both commands should successfully display GPU information.

---

## Installation Steps

### Step 1: Clone Repository and Navigate to Backend

```bash
cd /path/to/KlipNote/backend
```

### Step 2: Create Environment File

```bash
cp .env.example .env
```

**Edit `.env` with your configuration:**

```bash
# Redis and Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Epic 4: Model Selection
DEFAULT_TRANSCRIPTION_MODEL=auto  # "belle2" | "whisperx" | "auto"

# WhisperX Settings
WHISPER_MODEL=large-v2
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

# BELLE-2 Settings
BELLE2_MODEL_NAME=BELLE-2/Belle-whisper-large-v3-zh

# Optimization Settings (Epic 3)
ENABLE_OPTIMIZATION=true
OPTIMIZER_ENGINE=auto

# File Storage
UPLOAD_DIR=/uploads
MAX_FILE_SIZE=2147483648  # 2GB
MAX_DURATION_HOURS=2

# CORS Origins
CORS_ORIGINS='["http://localhost:5173", "http://localhost:5174"]'
```

**Model Selection Options:**

- `DEFAULT_TRANSCRIPTION_MODEL=belle2`: All jobs route to BELLE-2 worker (Chinese-optimized)
- `DEFAULT_TRANSCRIPTION_MODEL=whisperx`: All jobs route to WhisperX worker (multi-language)
- `DEFAULT_TRANSCRIPTION_MODEL=auto`: Automatic routing (Chinese→belle2, others→whisperx)

### Step 3: Create Uploads Directory

```bash
mkdir -p ./uploads
chmod 777 ./uploads  # Docker containers need write access
```

### Step 4: Build Docker Images

**Build both worker images:**

```bash
# BELLE-2 worker (CUDA 11.8)
docker build -f Dockerfile.belle2 -t klipnote-worker-cuda118:latest .

# WhisperX worker (CUDA 12.x)
docker build -f Dockerfile.whisperx -t klipnote-worker-cuda12:latest .

# Web service (optional - uses standard Dockerfile)
docker build -f Dockerfile -t klipnote-web:latest .
```

**Build time estimate:** 15-30 minutes per image (downloads ~10GB total).

**Verify images:**

```bash
docker images | grep klipnote
```

Expected output:
```
klipnote-worker-cuda118    latest    abc123def456    5 minutes ago    15.2GB
klipnote-worker-cuda12     latest    def789abc012    10 minutes ago   16.8GB
klipnote-web               latest    ghi345jkl678    2 minutes ago    2.1GB
```

### Step 5: Start Multi-Worker Services

**Option A: Full Multi-Worker Deployment (Both Models)**

```bash
docker-compose -f docker-compose.multi-model.yaml up -d
```

**Option B: Single-Worker Deployment (MVP - One Model Only)**

Edit `docker-compose.multi-model.yaml` and comment out one worker:

```yaml
# For BELLE-2 only:
  # whisperx-worker:  # Comment out WhisperX worker
  #   ...

# For WhisperX only:
  # belle2-worker:  # Comment out BELLE-2 worker
  #   ...
```

Then start:

```bash
docker-compose -f docker-compose.multi-model.yaml up -d
```

### Step 6: Verify Deployment

**Check all services are running:**

```bash
docker-compose -f docker-compose.multi-model.yaml ps
```

Expected output:
```
NAME                         STATUS              PORTS
klipnote-belle2-worker       Up 2 minutes
klipnote-whisperx-worker     Up 2 minutes
klipnote-web                 Up 2 minutes        0.0.0.0:8000->8000/tcp
klipnote-redis               Up 2 minutes        0.0.0.0:6379->6379/tcp
klipnote-flower              Up 2 minutes        0.0.0.0:5555->5555/tcp
```

**Check worker logs:**

```bash
# BELLE-2 worker
docker-compose -f docker-compose.multi-model.yaml logs -f belle2-worker

# WhisperX worker
docker-compose -f docker-compose.multi-model.yaml logs -f whisperx-worker
```

**Expected startup logs:**

```
belle2-worker     | Validating CUDA 11.8 for BELLE-2 worker...
belle2-worker     | PyTorch version: 2.5.1+cu118
belle2-worker     | GPU: NVIDIA RTX 4090
belle2-worker     | GPU Memory: 24.0 GB
belle2-worker     | BELLE-2 worker ready: CUDA 11.8, PyTorch 2.5.1+cu118, Queue: belle2
belle2-worker     | [2025-11-15 10:30:00,123: INFO/MainProcess] Connected to redis://redis:6379/0
belle2-worker     | [2025-11-15 10:30:00,456: INFO/MainProcess] celery@belle2 ready.
```

**Access Flower monitoring dashboard:**

```
http://localhost:5555
```

Verify both `belle2@...` and `whisperx@...` workers show as "online" in Flower UI.

### Step 7: Test Transcription Job

**Upload test audio:**

```bash
curl -X POST "http://localhost:8000/upload" \
     -F "file=@/path/to/test-audio.mp3"
```

Response:
```json
{"job_id": "550e8400-e29b-41d4-a716-446655440000"}
```

**Monitor job routing (check web service logs):**

```bash
docker-compose -f docker-compose.multi-model.yaml logs -f web | grep "Routing transcription"
```

Expected output:
```
web | INFO: Routing transcription job 550e8400-... to queue 'belle2' (model: auto)
```

**Check job status:**

```bash
curl -X GET "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
```

**Retrieve result (when status="completed"):**

```bash
curl -X GET "http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000"
```

---

## Configuration Reference

### Environment Variables (Complete List)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEFAULT_TRANSCRIPTION_MODEL` | `auto` | Model selection: `belle2`, `whisperx`, or `auto` |
| `CELERY_BROKER_URL` | `redis://redis:6379/0` | Redis broker URL for Celery |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/0` | Redis result backend for Celery |
| `WHISPER_MODEL` | `large-v2` | WhisperX model size |
| `WHISPER_DEVICE` | `cuda` | WhisperX device (`cuda` or `cpu`) |
| `WHISPER_COMPUTE_TYPE` | `float16` | WhisperX compute type |
| `BELLE2_MODEL_NAME` | `BELLE-2/Belle-whisper-large-v3-zh` | BELLE-2 HuggingFace model ID |
| `ENABLE_OPTIMIZATION` | `true` | Enable Epic 3 enhancement pipeline |
| `OPTIMIZER_ENGINE` | `auto` | Timestamp optimization strategy |
| `UPLOAD_DIR` | `/uploads` | Media storage directory (inside container) |
| `MAX_FILE_SIZE` | `2147483648` | Maximum upload size (2GB in bytes) |
| `MAX_DURATION_HOURS` | `2` | Maximum audio duration (hours) |

### Model Selection Strategy

**AUTO Mode (`DEFAULT_TRANSCRIPTION_MODEL=auto`):**

- Automatic routing based on language detection
- Chinese language codes (zh, zh-cn, zh-tw, cmn, mandarin) → belle2 queue
- All other languages → whisperx queue
- Fallback to whisperx if language detection fails

**Explicit Model Selection:**

- `belle2`: Force all jobs to BELLE-2 worker (optimal for Chinese audio)
- `whisperx`: Force all jobs to WhisperX worker (optimal for multi-language, English audio)

---

## Monitoring and Observability

### Flower Dashboard

**Access:** `http://localhost:5555`

**Features:**
- Real-time worker status (belle2@..., whisperx@...)
- Queue lengths (pending jobs in belle2 and whisperx queues)
- Task success/failure rates
- Worker uptime and task history

**Screenshot of healthy deployment:**
```
Workers (2 active):
  ✅ belle2@klipnote-belle2-worker    | Active | Tasks: 5 (succeeded), 0 (failed)
  ✅ whisperx@klipnote-whisperx-worker | Active | Tasks: 3 (succeeded), 0 (failed)
```

### Log Aggregation

**View all logs:**
```bash
docker-compose -f docker-compose.multi-model.yaml logs -f
```

**Filter specific service:**
```bash
docker-compose -f docker-compose.multi-model.yaml logs -f belle2-worker
docker-compose -f docker-compose.multi-model.yaml logs -f whisperx-worker
docker-compose -f docker-compose.multi-model.yaml logs -f web
```

**Search for errors:**
```bash
docker-compose -f docker-compose.multi-model.yaml logs | grep ERROR
```

### GPU Resource Monitoring

**Monitor GPU usage during transcription:**

```bash
watch -n 1 nvidia-smi
```

Expected behavior:
- One worker active → ~6-12GB VRAM used
- Both workers active → Sequential processing (GPU shared)

---

## Troubleshooting

### Issue: Worker Fails to Start with CUDA Version Mismatch

**Symptoms:**
```
belle2-worker | ERROR: CUDA 11.8 required, found CUDA 12.3
```

**Solution:**
- Verify NVIDIA driver version: `nvidia-smi`
- Driver ≥530 required for CUDA 11.8 + 12.x compatibility
- Update driver: https://www.nvidia.com/Download/index.aspx

---

### Issue: Worker Shows "Unhealthy" in Flower

**Symptoms:**
- Worker appears offline in Flower dashboard
- Tasks stuck in "pending" state

**Diagnosis:**

```bash
# Check worker logs
docker-compose -f docker-compose.multi-model.yaml logs belle2-worker

# Verify worker can ping Celery
docker exec klipnote-belle2-worker celery -A app.celery_utils inspect ping
```

**Solution:**
- Restart worker: `docker-compose -f docker-compose.multi-model.yaml restart belle2-worker`
- Check Redis connectivity: `docker-compose -f docker-compose.multi-model.yaml logs redis`

---

### Issue: Model Download Timeout on First Job

**Symptoms:**
```
belle2-worker | Downloading model... (This may take 10-15 minutes on first run)
```

**Expected Behavior:**
- First job per worker downloads ~3GB model from HuggingFace
- Subsequent jobs use cached model (instant startup)

**Optimization:**
- Pre-download models during Docker build (uncomment lines in Dockerfiles)
- Or manually pre-download: `docker exec klipnote-belle2-worker python -c "from transformers import AutoModelForSpeechSeq2Seq; AutoModelForSpeechSeq2Seq.from_pretrained('BELLE-2/Belle-whisper-large-v3-zh')"`

---

### Issue: Jobs Stuck in Queue (No Active Worker)

**Symptoms:**
- Job remains "pending" indefinitely
- Flower shows 0 active workers for target queue

**Diagnosis:**

```bash
# Check which queues have active workers
docker exec klipnote-web python -c "from app.celery_utils import celery_app; print(celery_app.control.inspect().active_queues())"
```

**Solution:**
- Verify worker is running: `docker ps | grep worker`
- Check worker subscribed to correct queue: `docker logs klipnote-belle2-worker | grep "belle2"`
- Restart workers: `docker-compose -f docker-compose.multi-model.yaml restart belle2-worker whisperx-worker`

---

### Issue: GPU Out of Memory (OOM)

**Symptoms:**
```
RuntimeError: CUDA out of memory. Tried to allocate 2.00 GiB (GPU 0; 12.00 GiB total capacity)
```

**Solution:**
- Ensure only 1 job per worker (default: `worker_prefetch_multiplier=1`)
- Reduce model size: `WHISPER_MODEL=medium` (instead of large-v2)
- Increase GPU VRAM: Use GPU with ≥12GB
- Scale horizontally: Deploy multiple workers with separate GPUs

---

## Scaling and Performance

### Horizontal Scaling (Multiple Workers Per Model)

**Deploy 2x belle2 workers + 2x whisperx workers:**

```bash
docker-compose -f docker-compose.multi-model.yaml up -d --scale belle2-worker=2 --scale whisperx-worker=2
```

**GPU Assignment:**
- Use `CUDA_VISIBLE_DEVICES` env var to assign specific GPUs to workers
- Example: GPU 0 for belle2, GPU 1 for whisperx

```yaml
belle2-worker:
  environment:
    - CUDA_VISIBLE_DEVICES=0  # Use first GPU only

whisperx-worker:
  environment:
    - CUDA_VISIBLE_DEVICES=1  # Use second GPU only
```

### Performance Benchmarks (Reference Values)

| Model | Audio Duration | Transcription Time | RTF (Real-Time Factor) |
|-------|----------------|-------------------|------------------------|
| BELLE-2 | 60 minutes | 30-45 minutes | 0.5-0.75x |
| WhisperX | 60 minutes | 25-40 minutes | 0.4-0.67x |

RTF < 1.0 means transcription is faster than real-time.

---

## Rollback and Disaster Recovery

### Rollback to Single-Worker (Emergency)

**Fastest rollback (< 1 minute):**

```bash
# Stop multi-worker deployment
docker-compose -f docker-compose.multi-model.yaml stop belle2-worker whisperx-worker

# Start only one worker
docker-compose -f docker-compose.multi-model.yaml start belle2-worker
```

**Alternative: Edit docker-compose.yaml and restart:**

```yaml
# Comment out failing worker
  # whisperx-worker:
  #   ...
```

```bash
docker-compose -f docker-compose.multi-model.yaml up -d
```

### Data Preservation

- **Redis Data**: Persisted in `redis_data` volume
- **Uploads**: Persisted in `./uploads` bind mount
- **Model Caches**: Persisted in `belle2_models` and `whisperx_models` volumes

**Backup critical data:**

```bash
# Backup Redis
docker exec klipnote-redis redis-cli --rdb /data/dump.rdb
docker cp klipnote-redis:/data/dump.rdb ./backups/redis-backup-$(date +%Y%m%d).rdb

# Backup uploads
tar -czf backups/uploads-backup-$(date +%Y%m%d).tar.gz ./uploads
```

---

## Maintenance and Updates

### Update Docker Images

```bash
# Rebuild images
docker build -f Dockerfile.belle2 -t klipnote-worker-cuda118:latest .
docker build -f Dockerfile.whisperx -t klipnote-worker-cuda12:latest .

# Restart services with new images
docker-compose -f docker-compose.multi-model.yaml up -d
```

### Cleanup Old Models and Images

```bash
# Remove unused Docker images
docker image prune -a

# Clear model caches (frees ~6GB)
docker volume rm klipnote_belle2_models klipnote_whisperx_models
```

---

## Security Considerations

### Production Deployment Checklist

- [ ] Enable Redis password authentication (`requirepass` in redis.conf)
- [ ] Add HTTP Basic Auth to Flower dashboard
- [ ] Restrict Flower access to localhost or VPN (firewall rule)
- [ ] Use HTTPS for web service (reverse proxy with Let's Encrypt)
- [ ] Disable CORS wildcard (`allow_origins=["*"]`) and specify exact frontend URLs
- [ ] Set environment variables via secrets (Docker Compose secrets, not .env file)
- [ ] Enable Docker Content Trust for image integrity (`export DOCKER_CONTENT_TRUST=1`)
- [ ] Regularly update base images for security patches
- [ ] Monitor HuggingFace model checksums to detect poisoning

---

## Support and Further Reading

- **Epic 4 Technical Specification**: `docs/sprint-artifacts/tech-spec-epic-4.md`
- **ADR-004 Architecture Decision**: `docs/architecture-decisions/ADR-004-multi-model-architecture.md`
- **Docker Compose Reference**: `backend/docker-compose.multi-model.yaml`
- **Model Routing Logic**: `backend/app/ai_services/model_router.py`

**For issues or questions:**
- Check troubleshooting section above
- Review Flower dashboard for worker status
- Examine worker logs: `docker-compose -f docker-compose.multi-model.yaml logs -f`
