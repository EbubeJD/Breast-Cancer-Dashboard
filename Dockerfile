FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /install

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --prefix=/install -r requirements.txt


FROM python:3.12-slim AS runtime

LABEL maintainer="METABRIC Dashboard <noreply@example.com>"
LABEL description="METABRIC Breast Cancer Interactive Dashboard"
LABEL version="2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local

RUN useradd -m -u 1000 appuser

COPY --chown=appuser:appuser . .

RUN mkdir -p /app/logs /app/cache && \
    chown -R appuser:appuser /app

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8050/ || exit 1

USER appuser

EXPOSE 8050

CMD gunicorn --bind 0.0.0.0:${PORT:-8050} --workers 2 --worker-class sync --worker-tmp-dir /dev/shm --max-requests 500 --max-requests-jitter 50 --timeout 120 --access-logfile - --error-logfile - --log-level info app:server
