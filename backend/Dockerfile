# Base image - lightweight for web service (no CUDA needed)
FROM python:3.11-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (ffmpeg for media validation)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install remaining Python dependencies (common dependencies for web service)
COPY requirements-common.txt .
RUN pip install --no-cache-dir -r requirements-common.txt

# Copy entire backend directory to maintain app package structure
COPY . /app

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH="/app"

# Expose FastAPI port
EXPOSE 8000

# Default command - runs FastAPI web server
# Use app.main:app since 'app' is a Python package directory
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
