# Base image with CUDA 12.3 support for GPU-accelerated WhisperX
# CUDA 12.3.2 + cuDNN 9 required for ctranslate2 4.5.0+ and modern AI/ML ecosystem
FROM nvidia/cuda:12.3.2-cudnn9-devel-ubuntu22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including ffmpeg (CRITICAL - required by WhisperX)
# WhisperX and torchaudio require the actual ffmpeg command-line tool, not just python-ffmpeg wrapper
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.11 \
    python3-pip \
    python3.11-dev \
    ffmpeg \
    git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

WORKDIR /app

# Install PyTorch with CUDA 12.1 support (CRITICAL - must use specific index URL)
# Generic torch from PyPI installs CPU-only or wrong CUDA version
# CUDA 12.1 wheels are compatible with CUDA 12.3 runtime (forward compatibility)
# This ensures torch.cuda.is_available() returns True for GPU acceleration
RUN pip install --no-cache-dir \
    torch \
    torchvision \
    torchaudio \
    --index-url https://download.pytorch.org/whl/cu121

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire backend directory to maintain app package structure
COPY . /app

# Set PYTHONPATH to include the app directory and whisperx submodule
# whisperx is a git submodule at app/ai_services/whisperx/ and needs to be in the import path
ENV PYTHONPATH="/app:/app/app/ai_services/whisperx"

# Expose FastAPI port
EXPOSE 8000

# Default command - runs FastAPI web server
# Use app.main:app since 'app' is a Python package directory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
