# KlipNote

Audio transcription service with GPU-accelerated WhisperX, built with FastAPI and Vue 3.

## System Requirements

### Hardware Requirements
- **NVIDIA GPU** with 8GB+ VRAM (for GPU-accelerated transcription)
- **CUDA** 11.8 or higher
- Sufficient disk space for Docker images and model caching (~10GB)

### Software Requirements
- **Docker** and **Docker Compose** (latest version)
- **nvidia-docker2** (for GPU support in containers)
- **Python** 3.12+ (for backend local development)
- **Node.js** 20.x LTS (for frontend local development)
- **Git** with submodule support

### GPU Setup Validation

Verify your GPU is accessible to Docker:

```bash
# Test NVIDIA Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Expected output: Should display your GPU information
```

If the command fails, ensure nvidia-docker2 is properly installed and configured.

## Quick Start Guide

### 1. Clone Repository with Submodules

```bash
git clone <repository-url> klipnote
cd klipnote
git submodule update --init --recursive
```

### 2. Backend Setup (Docker Compose)

#### Create Environment File

```bash
cd backend
cp .env.example .env
# Edit .env if needed (defaults should work for local development)
```

#### Start All Services

```bash
# Build and start all services (web, worker, redis, flower)
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

#### Verify Backend Services

- **API Documentation**: http://localhost:8000/docs (FastAPI auto-generated docs)
- **API Health Check**: http://localhost:8000/health
- **Flower Dashboard**: http://localhost:5555 (Celery task monitoring)
- **Redis**: http://localhost:6379

#### Test GPU Access in Worker Container

```bash
# Access worker container
docker-compose exec worker bash

# Inside container, verify GPU access
nvidia-smi

# Exit container
exit
```

#### Test Celery Worker Connection

```bash
# Ping Celery workers
docker-compose exec worker celery -A app.celery_utils inspect ping
```

#### Environment Variables Reference

Key environment variables (see `.env.example` for complete list):

- `CELERY_BROKER_URL`: Redis connection for Celery task queue
- `CELERY_RESULT_BACKEND`: Redis connection for task results
- `WHISPER_MODEL`: WhisperX model (tiny, base, small, medium, large-v2, large-v3)
- `WHISPER_DEVICE`: Device for inference (cuda for GPU, cpu for CPU)
- `WHISPER_COMPUTE_TYPE`: Compute precision (float16 for GPU, float32 for CPU)
- `UPLOAD_DIR`: Directory for uploaded audio files
- `MAX_FILE_SIZE`: Maximum upload file size in bytes
- `CORS_ORIGINS`: Allowed frontend origins for CORS

### 3. Frontend Setup (Vue 3 + Vite)

```bash
cd frontend

# Install dependencies (already done during project initialization)
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:5173
```

#### Frontend Development Commands

```bash
# Run development server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run unit tests
npm run test:unit

# Run unit tests with coverage
npm run test:unit -- --coverage

# Lint and fix code
npm run lint
```

### 4. Full Stack Development Workflow

```bash
# Terminal 1: Backend services
cd backend
docker-compose up

# Terminal 2: Frontend dev server
cd frontend
npm run dev
```

Access:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower**: http://localhost:5555

## API Usage

### Upload Audio/Video File

Upload media files for transcription using the `/upload` endpoint.

**Endpoint:** `POST /upload`

**Supported Formats:**
- MP3 (audio/mpeg)
- MP4 (video/mp4)
- WAV (audio/wav)
- M4A (audio/x-m4a, audio/mp4)

**File Requirements:**
- **Maximum file size:** 2GB
- **Maximum duration:** 2 hours
- **Content-Type:** multipart/form-data

**Example using cURL:**

```bash
# Upload an audio file
curl -X POST "http://localhost:8000/upload" \
     -F "file=@/path/to/your/audio.mp3"

# Expected response:
# {
#   "job_id": "550e8400-e29b-41d4-a716-446655440000"
# }
```

**Example using Python:**

```python
import requests

# Upload file
with open("/path/to/your/audio.mp3", "rb") as f:
    response = requests.post(
        "http://localhost:8000/upload",
        files={"file": ("audio.mp3", f, "audio/mpeg")}
    )

data = response.json()
job_id = data["job_id"]
print(f"Upload successful! Job ID: {job_id}")
```

**Example using JavaScript/Fetch:**

```javascript
// Upload file from file input
const fileInput = document.querySelector('input[type="file"]');
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/upload', {
    method: 'POST',
    body: formData
})
.then(response => response.json())
.then(data => {
    console.log('Upload successful! Job ID:', data.job_id);
})
.catch(error => console.error('Upload failed:', error));
```

**Response Codes:**

- **200 OK**: File uploaded successfully, returns `job_id`
- **400 Bad Request**: Invalid file format or duration exceeds limit
- **413 Payload Too Large**: File size exceeds 2GB limit
- **422 Unprocessable Entity**: Missing file in request
- **500 Internal Server Error**: Storage or processing error

**Common Error Messages:**

```json
// Invalid format
{
  "detail": "Unsupported file format. Allowed: MP3, MP4, WAV, M4A. Received: text/plain"
}

// Duration too long
{
  "detail": "File duration exceeds 2-hour limit. File duration: 3.50 hours"
}

// File too large
{
  "detail": "File size exceeds maximum limit of 2.0GB"
}
```

**Interactive API Documentation:**

Visit http://localhost:8000/docs for interactive API documentation with:
- Request/response schemas
- Try-it-out functionality
- Full parameter descriptions
- Example requests and responses

### Async Transcription Processing (Story 1.3)

After uploading a file via `/upload`, transcription is processed asynchronously by a Celery worker with GPU acceleration. The job progresses through 5 stages:

**Progress Stages:**

1. **10% - Task Queued**: Job accepted and queued for processing
2. **20% - Loading AI Model**: WhisperX model loading (cached after first run)
3. **40% - Transcribing Audio**: Active transcription with GPU (longest stage)
4. **80% - Aligning Timestamps**: Word-level timestamp alignment
5. **100% - Processing Complete**: Results saved to Redis and disk

**Processing Time:**
- Expected speed: 1-2x real-time (1 hour audio = 30-60 min processing with GPU)
- First run slower due to model download (~1.5GB)
- Subsequent runs use cached model for faster startup

**Monitoring:**
- **Flower Dashboard**: http://localhost:5555 (real-time Celery task monitoring)
- **Worker Logs**: `docker-compose logs -f worker`
- **Status API**: Coming in Story 1.4 (`GET /status/{job_id}`)

**Result Storage:**
- Redis: `job:{job_id}:status` and `job:{job_id}:result` keys
- Disk: `/uploads/{job_id}/transcription.json`

**Example transcription.json format:**
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
      "text": "Let's begin with today's agenda."
    }
  ]
}
```

## Project Structure

```
klipnote/
├── backend/                 # FastAPI backend with Celery workers
│   ├── app/
│   │   ├── ai_services/    # AI service abstraction layer
│   │   │   ├── whisperx/   # WhisperX git submodule
│   │   │   ├── base.py     # Abstract TranscriptionService interface
│   │   │   └── whisperx_service.py  # WhisperX implementation
│   │   ├── services/       # Business logic services
│   │   ├── tasks/          # Celery async tasks
│   │   ├── main.py         # FastAPI app initialization
│   │   ├── config.py       # Configuration management
│   │   ├── celery_utils.py # Celery worker configuration
│   │   └── models.py       # Pydantic data models
│   ├── tests/              # Backend tests (pytest)
│   ├── Dockerfile          # Backend container configuration
│   ├── docker-compose.yaml # Multi-service orchestration
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variable template
│
├── frontend/               # Vue 3 + TypeScript frontend
│   ├── src/
│   │   ├── components/    # Reusable Vue components
│   │   ├── views/         # Page-level components
│   │   ├── stores/        # Pinia state management
│   │   ├── router/        # Vue Router configuration
│   │   ├── services/      # API client services
│   │   └── types/         # TypeScript type definitions
│   ├── package.json       # Node dependencies
│   └── vite.config.ts     # Vite build configuration
│
└── docs/                  # Project documentation
```

## Testing

### Backend Tests (pytest)

```bash
cd backend

# Run all tests
docker-compose exec web pytest tests/ -v

# Run with coverage report
docker-compose exec web pytest tests/ -v --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Frontend Tests (Vitest)

```bash
cd frontend

# Run unit tests
npm run test:unit

# Run with coverage
npm run test:unit -- --coverage

# Run in watch mode
npm run test:unit -- --watch
```

## Troubleshooting

### Upload Issues

**Upload fails with "Unsupported file format":**
- Ensure file is in supported format: MP3, MP4, WAV, or M4A
- Check file extension matches actual format
- Verify Content-Type header is correct

**Upload fails with "File duration exceeds 2-hour limit":**
- Media file is longer than 2 hours
- Split file into shorter segments
- Or adjust `MAX_DURATION_HOURS` in `.env` (requires restart)

**Upload fails with "File size exceeds maximum limit":**
- File is larger than 2GB
- Compress or reduce quality of media file
- Or adjust `MAX_FILE_SIZE` in `.env` (requires restart)

**Upload succeeds but ffprobe validation fails:**
- FFmpeg/ffprobe not installed in Docker container
- Verify Dockerfile includes: `RUN apt-get update && apt-get install -y ffmpeg`
- Rebuild containers: `docker-compose up --build`

### Backend Issues

**Docker Compose fails to start:**
- Ensure Docker and nvidia-docker2 are installed
- Check GPU is accessible: `nvidia-smi`
- Verify port 8000, 5555, 6379 are not in use

**Worker can't access GPU:**
- Verify nvidia-docker2 runtime is configured
- Check Docker Compose GPU configuration in `docker-compose.yaml`
- Test GPU access: `docker run --rm --gpus all nvidia/cuda:11.8.0-base nvidia-smi`

**Redis connection errors:**
- Wait for Redis health check to complete (check `docker-compose logs redis`)
- Verify Redis is running: `docker-compose ps`

### Frontend Issues

**Dependencies not installing:**
- Ensure Node.js 20.x LTS is installed: `node --version`
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules` and `package-lock.json`, then `npm install`

**Port 5173 already in use:**
- Change Vite port in `vite.config.ts`
- Or kill process using port: `lsof -ti:5173 | xargs kill` (Unix/Mac)

## Architecture Highlights

### Critical Technical Decisions

1. **FFmpeg Binary Installation**: Installed via apt-get in Dockerfile (not just python-ffmpeg wrapper). Required by WhisperX for media processing.

2. **PyTorch CUDA Binding**: Installed with CUDA 11.8-specific index URL (`--index-url https://download.pytorch.org/whl/cu118`) to ensure GPU acceleration.

3. **Docker Compose Health Checks**: Redis service has health check; web/worker services wait for Redis to be healthy before starting. Prevents race condition crashes.

4. **AI Service Abstraction**: WhisperX integrated via abstract `TranscriptionService` interface, enabling future alternatives (Deepgram, Faster-Whisper).

### Technology Stack

**Backend:**
- FastAPI 0.120.x (async web framework)
- Celery 5.5.3+ (distributed task queue)
- Redis 7 (message broker + result backend)
- WhisperX (GPU-accelerated transcription)
- PyTorch 2.1.2 with CUDA 11.8
- pytest (testing framework)

**Frontend:**
- Vue 3 (progressive JavaScript framework)
- TypeScript 5 (type safety)
- Vite (build tool + dev server)
- Vue Router 4 (routing)
- Pinia (state management)
- Vitest (testing framework)

**Infrastructure:**
- Docker + Docker Compose (containerization)
- nvidia-docker2 (GPU support)
- CUDA 11.8+ (GPU acceleration)

## License

[Add license information]

## Contributing

[Add contribution guidelines]
