#!/bin/bash
# KlipNote Multi-Worker Deployment Prerequisites Check
# Epic 4 - Multi-Model Production Architecture
# Run this script before deploying to validate system requirements

set -euo pipefail

# Color output for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "KlipNote Multi-Worker Prerequisites Check"
echo "=================================================="
echo ""

# Track overall success
PREREQ_MET=true

# -----------------------------------------------------------------------------
# Check 1: NVIDIA Driver
# -----------------------------------------------------------------------------
echo -n "Checking NVIDIA Driver... "
if command -v nvidia-smi &> /dev/null; then
    DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -n 1)
    CUDA_VERSION=$(nvidia-smi | grep -oP 'CUDA Version: \K[0-9.]+' || echo "unknown")

    # Extract major version number
    DRIVER_MAJOR=$(echo "$DRIVER_VERSION" | cut -d. -f1)

    if [ "$DRIVER_MAJOR" -ge 530 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "  Driver: $DRIVER_VERSION (>= 530 required)"
        echo "  CUDA: $CUDA_VERSION"
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Driver: $DRIVER_VERSION (< 530)"
        echo "  ERROR: NVIDIA driver >=530 required for CUDA 11.8 + 12.x compatibility"
        PREREQ_MET=false
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  ERROR: nvidia-smi not found. Install NVIDIA drivers from:"
    echo "  https://www.nvidia.com/Download/index.aspx"
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Check 2: CUDA 11.8 Support
# -----------------------------------------------------------------------------
echo -n "Checking CUDA 11.8 Support (BELLE-2 worker)... "
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  Docker can access GPU with CUDA 11.8 runtime"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  ERROR: Cannot run CUDA 11.8 containers. Check nvidia-docker2 installation."
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Check 3: CUDA 12.x Support
# -----------------------------------------------------------------------------
echo -n "Checking CUDA 12.x Support (WhisperX worker)... "
if docker run --rm --gpus all nvidia/cuda:12.3.2-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  Docker can access GPU with CUDA 12.x runtime"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  ERROR: Cannot run CUDA 12.x containers. Check nvidia-docker2 installation."
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Check 4: Docker Version
# -----------------------------------------------------------------------------
echo -n "Checking Docker... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -n 1)
    DOCKER_MAJOR=$(echo "$DOCKER_VERSION" | cut -d. -f1)
    DOCKER_MINOR=$(echo "$DOCKER_VERSION" | cut -d. -f2)

    if [ "$DOCKER_MAJOR" -gt 20 ] || ([ "$DOCKER_MAJOR" -eq 20 ] && [ "$DOCKER_MINOR" -ge 10 ]); then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "  Docker: $DOCKER_VERSION (>= 20.10 required)"
    else
        echo -e "${YELLOW}⚠ WARNING${NC}"
        echo "  Docker: $DOCKER_VERSION (< 20.10)"
        echo "  Recommended: Upgrade to Docker 20.10+ for best GPU support"
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  ERROR: Docker not found. Install from: https://docs.docker.com/get-docker/"
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Check 5: Docker Compose Version
# -----------------------------------------------------------------------------
echo -n "Checking Docker Compose... "
if docker compose version &> /dev/null; then
    # Compose V2 (docker compose)
    COMPOSE_VERSION=$(docker compose version --short)
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  Docker Compose: $COMPOSE_VERSION (V2)"
elif command -v docker-compose &> /dev/null; then
    # Compose V1 (docker-compose)
    COMPOSE_VERSION=$(docker-compose --version | grep -oP '\d+\.\d+\.\d+' | head -n 1)
    COMPOSE_MAJOR=$(echo "$COMPOSE_VERSION" | cut -d. -f1)
    COMPOSE_MINOR=$(echo "$COMPOSE_VERSION" | cut -d. -f2)

    if [ "$COMPOSE_MAJOR" -gt 1 ] || ([ "$COMPOSE_MAJOR" -eq 1 ] && [ "$COMPOSE_MINOR" -ge 29 ]); then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "  Docker Compose: $COMPOSE_VERSION (V1, >= 1.29 required)"
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  Docker Compose: $COMPOSE_VERSION (< 1.29)"
        echo "  ERROR: Upgrade to Compose 1.29+ or migrate to Compose V2"
        PREREQ_MET=false
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  ERROR: Docker Compose not found. Install from:"
    echo "  https://docs.docker.com/compose/install/"
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Check 6: GPU VRAM
# -----------------------------------------------------------------------------
echo -n "Checking GPU VRAM... "
if command -v nvidia-smi &> /dev/null; then
    VRAM_MB=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -n 1)
    VRAM_GB=$((VRAM_MB / 1024))

    if [ "$VRAM_GB" -ge 12 ]; then
        echo -e "${GREEN}✓ PASS${NC}"
        echo "  VRAM: ${VRAM_GB}GB (>= 12GB recommended)"
    elif [ "$VRAM_GB" -ge 8 ]; then
        echo -e "${YELLOW}⚠ WARNING${NC}"
        echo "  VRAM: ${VRAM_GB}GB (8-12GB - minimum, may limit model size)"
        echo "  Recommended: 12GB+ for large models"
    else
        echo -e "${RED}✗ FAIL${NC}"
        echo "  VRAM: ${VRAM_GB}GB (< 8GB)"
        echo "  ERROR: Minimum 8GB VRAM required, 12GB+ recommended"
        PREREQ_MET=false
    fi
else
    echo -e "${YELLOW}⚠ SKIP${NC}"
    echo "  Cannot check VRAM (nvidia-smi not available)"
fi
echo ""

# -----------------------------------------------------------------------------
# Check 7: Disk Space
# -----------------------------------------------------------------------------
echo -n "Checking Disk Space... "
AVAILABLE_GB=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')

if [ "$AVAILABLE_GB" -ge 100 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  Available: ${AVAILABLE_GB}GB (>= 100GB recommended)"
elif [ "$AVAILABLE_GB" -ge 50 ]; then
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo "  Available: ${AVAILABLE_GB}GB (50-100GB - minimum)"
    echo "  Recommended: 100GB+ for models + Docker images"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  Available: ${AVAILABLE_GB}GB (< 50GB)"
    echo "  ERROR: Minimum 50GB required (Docker images ~30GB + models ~6GB)"
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Check 8: Memory (RAM)
# -----------------------------------------------------------------------------
echo -n "Checking System RAM... "
RAM_GB=$(free -g | grep Mem: | awk '{print $2}')

if [ "$RAM_GB" -ge 32 ]; then
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  RAM: ${RAM_GB}GB (>= 32GB recommended)"
elif [ "$RAM_GB" -ge 16 ]; then
    echo -e "${YELLOW}⚠ WARNING${NC}"
    echo "  RAM: ${RAM_GB}GB (16-32GB - minimum)"
    echo "  Recommended: 32GB+ for best performance"
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "  RAM: ${RAM_GB}GB (< 16GB)"
    echo "  ERROR: Minimum 16GB RAM required, 32GB+ recommended"
    PREREQ_MET=false
fi
echo ""

# -----------------------------------------------------------------------------
# Final Summary
# -----------------------------------------------------------------------------
echo "=================================================="
if [ "$PREREQ_MET" = true ]; then
    echo -e "${GREEN}✓ ALL PREREQUISITES MET${NC}"
    echo ""
    echo "System is ready for KlipNote multi-worker deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. Build Docker images:"
    echo "     docker build -f Dockerfile.belle2 -t klipnote-worker-cuda118:latest ."
    echo "     docker build -f Dockerfile.whisperx -t klipnote-worker-cuda12:latest ."
    echo ""
    echo "  2. Start services:"
    echo "     docker-compose -f docker-compose.multi-model.yaml up -d"
    echo ""
    echo "  3. Monitor deployment:"
    echo "     http://localhost:5555 (Flower dashboard)"
    echo ""
    exit 0
else
    echo -e "${RED}✗ SOME PREREQUISITES NOT MET${NC}"
    echo ""
    echo "Please address the failed checks above before deploying."
    echo ""
    echo "For detailed installation instructions, see:"
    echo "  docs/deployment/multi-worker-deployment-guide.md"
    echo ""
    exit 1
fi
