# Base image with CUDA 11.8 support for GPU-accelerated WhisperX
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies including ffmpeg (CRITICAL - required by WhisperX)
# WhisperX and torchaudio require the actual ffmpeg command-line tool, not just python-ffmpeg wrapper
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    python3.12-dev \
    ffmpeg \
    git \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -s /usr/bin/python3.12 /usr/bin/python && \
    ln -s /usr/bin/pip3 /usr/bin/pip

WORKDIR /app

# Install PyTorch with CUDA 11.8 support (CRITICAL - must use specific index URL)
# Generic torch from PyPI installs CPU-only or wrong CUDA version
# This ensures torch.cuda.is_available() returns True for GPU acceleration
RUN pip install --no-cache-dir \
    torch==2.1.2 \
    torchaudio==2.1.2 \
    --index-url https://download.pytorch.org/whl/cu118

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app

# Expose FastAPI port
EXPOSE 8000

# Default command - runs FastAPI web server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
