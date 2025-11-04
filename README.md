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
