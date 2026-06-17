# Production-Grade Multi-Stage Dockerfile

# ============= Stage 1: Builder =============
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /install

# Install build dependencies for scientific packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix=/install -r requirements.txt


# ============= Stage 2: Runtime =============
FROM python:3.12-slim AS runtime

LABEL maintainer="METABRIC Dashboard <noreply@example.com>"
LABEL description="METABRIC Breast Cancer Interactive Dashboard"
LABEL version="2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Install runtime dependencies only (smaller image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /install /usr/local

# Create non-root user for security
RUN useradd -m -u 1000 appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/logs /app/cache && \
    chown -R appuser:appuser /app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

# Switch to non-root user
USER appuser

EXPOSE 8050

# Production: Run with Gunicorn
# Workers = 2 * CPU + 1 (suitable for most cases)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:8050", \
     "--workers", "3", \
     "--worker-class", "sync", \
     "--worker-tmp-dir", "/dev/shm", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "50", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app:server"]
