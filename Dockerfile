# Complete Self System Dockerfile
# =====================================
# Multi-stage build for production and development

# =====================================
# Base image
# =====================================
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create and set working directory
WORKDIR /app

# =====================================
# Builder stage
# =====================================
FROM base as builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user -r requirements.txt

# =====================================
# Runtime stage
# =====================================
FROM base as runtime

# Install runtime dependencies for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Playwright dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    # Voice dependencies
    portaudio19-dev \
    espeak \
    # Cleanup
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create directories
RUN mkdir -p storage/vector storage/logs plugins generated_skills tests

# Install Playwright browsers
RUN python -m playwright install chromium --with-deps

# Set default environment variables
ENV AI_API_KEY="" \
    AI_BASE_URL="http://localhost:11434/v1" \
    AI_MODEL="llama3.1" \
    AI_EMBEDDING_MODEL="nomic-embed-text"

# Expose port for optional API server
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sqlite3; conn = sqlite3.connect('storage/self_system.db'); conn.close()" || exit 1

# Default command
CMD ["python", "app/main.py"]

# =====================================
# Development stage (extends runtime)
# =====================================
FROM runtime as development

# Install development dependencies
RUN pip install --user pytest pytest-cov black flake8 mypy

# Set development environment
ENV FLASK_ENV=development \
    PYTHONDONTWRITEBYTECODE=0

# Default command for development
CMD ["python", "app/main.py"]
