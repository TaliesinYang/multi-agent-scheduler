# Multi-Agent Scheduler - Production Docker Image
# Python 3.11 slim base for minimal size
FROM python:3.11-slim

# Metadata
LABEL maintainer="Multi-Agent Scheduler Team"
LABEL description="Multi-Agent Intelligent Scheduler - Production Ready"
LABEL version="3.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 scheduler && \
    mkdir -p /app /app/data /app/logs && \
    chown -R scheduler:scheduler /app

# Set working directory
WORKDIR /app

# Copy requirements first (for better layer caching)
COPY --chown=scheduler:scheduler requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=scheduler:scheduler . .

# Switch to non-root user
USER scheduler

# Create necessary directories
RUN mkdir -p \
    /app/data/checkpoints \
    /app/data/traces \
    /app/logs

# Expose ports
# 8000: Health check and metrics API
# 6831: Jaeger tracing (UDP)
EXPOSE 8000 6831/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Default command
CMD ["python", "-m", "src.main"]
