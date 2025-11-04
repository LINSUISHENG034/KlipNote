# KlipNote Development Guide

**Quick Reference for Developers and AI Agents**

---

## Prerequisites

### Required Software
- **OS:** Windows 10/11
- **Python:** 3.12.x (managed via `uv`)
- **Node.js:** 20.x LTS
- **Docker:** Docker Desktop with GPU support
- **Git:** Version control
- **Tools:** uv (Python package manager)

### Hardware Requirements
- **GPU:** NVIDIA GPU with 8GB+ VRAM (for WhisperX transcription)
- **CUDA:** Version 11.8 or 12.1+
- **Driver:** NVIDIA driver 520+ (for CUDA 11.8) or 530+ (for CUDA 12.1)

---

## Initial Setup

### 1. Install uv (Python Package Manager)

**Windows (PowerShell as Administrator):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Verify Installation:**
```bash
uv --version
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment with Python 3.12
uv venv --python 3.12

# Activate environment (Git Bash)
source .venv/Scripts/activate

# OR Activate (PowerShell)
.venv\Scripts\Activate.ps1

# OR Activate (CMD)
.venv\Scripts\activate.bat

# Install dependencies
uv pip install -r requirements.txt

# Verify environment
python --version  # Should show 3.12.x
which python      # Should point to backend/.venv/Scripts/python.exe
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Verify
npm run dev  # Should start Vite dev server on http://localhost:5173
```

### 4. Docker Setup

```bash
cd backend

# Start services (web, worker, redis, flower)
docker-compose up -d

# Verify all services running
docker ps  # Should show 4 containers

# View logs
docker-compose logs -f
```

---

## Development Workflow

### Backend Development

**CRITICAL: Always activate virtual environment first!**

```bash
cd backend
source .venv/Scripts/activate  # Git Bash
# OR
.venv\Scripts\Activate.ps1      # PowerShell
```

**Verify Activation:**
```bash
which python
# Expected: /e/Projects/KlipNote/backend/.venv/Scripts/python

python --version
# Expected: Python 3.12.x
```

**Adding New Dependencies:**
```bash
# Inside activated .venv
uv pip install <package-name>

# Update requirements.txt
uv pip freeze > requirements.txt
```

**Running Backend Tests:**
```bash
# Ensure .venv is activated
uv run pytest tests/ -v

# With coverage report
uv run pytest tests/ --cov=app --cov-report=html
```

**Running FastAPI Development Server:**
```bash
# Inside activated .venv
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development

**No activation needed - npm manages isolation automatically.**

```bash
cd frontend

# Development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint

# Build for production
npm run build

# Run tests
npm run test:unit
```

### Docker Development

**Starting Services:**
```bash
cd backend
docker-compose up -d
```

**Stopping Services:**
```bash
docker-compose down
```

**Rebuilding After Code Changes:**
```bash
docker-compose up -d --build
```

**Viewing Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f worker
```

**Accessing Flower (Celery Monitoring):**
```
http://localhost:5555
```

---

## Environment Troubleshooting

### Issue: AI agent uses global Python instead of .venv

**Symptom:** Commands run in wrong environment, dependencies installed globally

**Fix:**
1. Verify `.venv` exists: `ls backend/.venv/Scripts/python.exe`
2. Activate environment: `source backend/.venv/Scripts/activate`
3. Verify: `which python` should show `backend/.venv/Scripts/python`

**For AI Agents:**
Before running ANY backend Python command, always include:
```bash
cd backend && source .venv/Scripts/activate && <command>
```

### Issue: "python not found" after creating venv

**Fix:**
- Ensure Python 3.12 is installed: `python3.12 --version`
- Specify full path: `uv venv --python C:\Python312\python.exe`
- Or install Python 3.12 from: https://www.python.org/downloads/

### Issue: uv command not found

**Fix:**
- Re-run installation: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- Restart terminal to refresh PATH
- Verify: `uv --version`

### Issue: Docker containers fail to start

**Check GPU Access:**
```bash
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**If GPU not accessible:**
- Verify Docker Desktop GPU support enabled: Settings > Resources > WSL Integration
- Install nvidia-docker2: See GPU Setup section in README.md
- Check NVIDIA driver: `nvidia-smi` (should show GPU info)

### Issue: npm install fails or slow

**Fix:**
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be v20.x)

### Issue: Port already in use

**Backend (port 8000):**
```bash
# Windows: Find process using port
netstat -ano | findstr :8000

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

**Frontend (port 5173):**
```bash
# Same as above, replace 8000 with 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

---

## Project Structure

```
KlipNote/
├── backend/           # Python FastAPI + Celery
│   ├── .venv/         # Virtual environment (git-ignored)
│   ├── app/           # Application code
│   │   ├── main.py    # FastAPI application
│   │   ├── config.py  # Pydantic Settings
│   │   ├── celery_utils.py  # Celery configuration
│   │   ├── models.py  # Pydantic models
│   │   ├── ai_services/  # WhisperX integration
│   │   ├── services/     # Business logic
│   │   └── tasks/        # Celery tasks
│   ├── tests/         # Backend tests
│   ├── requirements.txt
│   ├── docker-compose.yaml
│   └── Dockerfile
│
├── frontend/          # Vue 3 + TypeScript
│   ├── node_modules/  # Dependencies (git-ignored)
│   ├── src/           # Source code
│   │   ├── components/  # Reusable UI components
│   │   ├── views/       # Page components
│   │   ├── stores/      # Pinia stores
│   │   ├── router/      # Vue Router
│   │   ├── services/    # API client
│   │   └── types/       # TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
├── docs/              # Architecture & stories
│   ├── architecture.md
│   ├── PRD.md
│   └── stories/
│
└── DEVELOPMENT.md     # This file
```

---

## Environment Isolation Verification

### Before Running Backend Commands

**Always check you're in the correct environment:**

```bash
# Check current Python location
which python
# Expected: /e/Projects/KlipNote/backend/.venv/Scripts/python

# If NOT in virtual environment, activate it:
cd backend
source .venv/Scripts/activate

# Verify packages are isolated
python -m pip list
# Should show ONLY project dependencies, not global packages
```

### Before Running Frontend Commands

```bash
# Check Node.js version
node --version
# Expected: v20.x.x

# Verify project dependencies installed
npm list --depth=0
# Should show: vue@3.x, typescript@5.x, vue-router@4.x, pinia
```

---

## Common Development Tasks

### Adding a New Backend API Endpoint

1. Activate virtual environment: `source backend/.venv/Scripts/activate`
2. Add endpoint in `backend/app/main.py`
3. Add Pydantic models in `backend/app/models.py`
4. Write tests in `backend/tests/test_api_*.py`
5. Run tests: `uv run pytest tests/ -v`

### Adding a New Frontend Component

1. Create component: `frontend/src/components/MyComponent.vue`
2. Add TypeScript interfaces: `frontend/src/types/*.ts`
3. Write tests: `frontend/src/components/__tests__/MyComponent.test.ts`
4. Run tests: `npm run test:unit`

### Adding a New Celery Task

1. Activate virtual environment: `source backend/.venv/Scripts/activate`
2. Add task in `backend/app/tasks/*.py`
3. Use `@shared_task` decorator
4. Write tests with mocked task: `backend/tests/test_tasks_*.py`
5. Test in Docker: `docker-compose up -d worker && docker-compose logs -f worker`

---

## Testing

### Backend Tests (pytest)

```bash
cd backend
source .venv/Scripts/activate

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_api_endpoints.py -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# View coverage report
# Open: backend/htmlcov/index.html
```

### Frontend Tests (Vitest)

```bash
cd frontend

# Run all tests
npm run test:unit

# Run with coverage
npm run test:unit -- --coverage

# Run in watch mode (for development)
npm run test:unit -- --watch
```

### Docker Integration Tests

```bash
cd backend

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# Check Flower (Celery monitoring)
# Open: http://localhost:5555

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Git Workflow

### Committing Changes

```bash
# Stage changes
git add <files>

# Commit with descriptive message
git commit -m "feat: Add new endpoint for transcription status"

# Push to remote
git push origin <branch-name>
```

### Updating WhisperX Submodule

```bash
cd backend/app/ai_services/whisperx

# Pull latest changes from upstream
git fetch origin
git checkout main
git pull

# Return to project root and commit submodule update
cd ../../../..
git add backend/app/ai_services/whisperx
git commit -m "chore: Update WhisperX submodule to latest version"
```

---

## CI/CD Notes (Future)

**GitHub Actions (when implemented):**

**Backend:**
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.12'
- run: pip install uv
- run: uv venv --python 3.12
- run: source .venv/Scripts/activate && uv pip install -r requirements.txt
- run: uv run pytest tests/ --cov=app
```

**Frontend:**
```yaml
- uses: actions/setup-node@v3
  with:
    node-version: '20'
- run: npm ci  # Use ci for deterministic installs
- run: npm run test:unit -- --coverage
- run: npm run build
```

---

## Performance Tips

### Backend

- **Use `uv` instead of `pip`:** 10-100x faster dependency resolution
- **Enable Redis persistence:** Avoid losing job state on restart
- **Monitor Celery with Flower:** http://localhost:5555
- **Cache WhisperX models:** Docker volume ensures models persist across container restarts

### Frontend

- **Use Vite HMR:** Changes reflect instantly without full reload
- **Lazy load routes:** Use dynamic imports in Vue Router
- **Optimize bundle size:** Check with `npm run build` and analyze output

### Docker

- **Layer caching:** Order Dockerfile commands from least to most frequently changed
- **Multi-stage builds:** Consider for production to reduce image size
- **GPU memory:** Monitor with `nvidia-smi` while transcription tasks run

---

## Security Notes

### Secrets Management

- **NEVER commit `.env` files** - use `.env.example` as template
- **Rotate secrets regularly** - especially for production
- **Use environment variables** - not hardcoded values

### CORS Configuration

- **Development:** `CORS_ORIGINS=["http://localhost:5173"]`
- **Production:** Update to actual frontend domain
- **Never use `*` wildcard** in production

---

## Additional Resources

### Documentation
- **Architecture:** `docs/architecture.md`
- **PRD:** `docs/PRD.md`
- **Stories:** `docs/stories/`
- **README:** `README.md`

### External References
- **FastAPI:** https://fastapi.tiangolo.com/
- **Vue 3:** https://vuejs.org/guide/introduction.html
- **Celery:** https://docs.celeryq.dev/
- **WhisperX:** https://github.com/m-bain/whisperX
- **uv:** https://github.com/astral-sh/uv
- **Docker Compose:** https://docs.docker.com/compose/

### Getting Help
- Check architecture.md for technical decisions
- Review story files in docs/stories/ for implementation details
- Consult README.md for setup issues

---

**Last Updated:** 2025-11-05
**Maintained by:** KlipNote Development Team
**For Questions:** See architecture.md (Development Environment Requirements section)

---

## Quick Command Reference

| Task | Command |
|------|---------|
| **Activate Backend Env** | `cd backend && source .venv/Scripts/activate` |
| **Install Backend Package** | `uv pip install <package> && uv pip freeze > requirements.txt` |
| **Run Backend Tests** | `uv run pytest tests/ -v` |
| **Start Backend Dev Server** | `uvicorn app.main:app --reload --port 8000` |
| **Install Frontend Package** | `cd frontend && npm install <package>` |
| **Run Frontend Tests** | `npm run test:unit` |
| **Start Frontend Dev Server** | `npm run dev` |
| **Start Docker Services** | `docker-compose up -d` |
| **View Docker Logs** | `docker-compose logs -f` |
| **Stop Docker Services** | `docker-compose down` |
| **Check GPU** | `docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi` |

---

**Remember: Always activate backend virtual environment before running Python commands!**
