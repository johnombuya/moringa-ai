# Dockerfile - AfyaPlus Service Platform Containerisation
# Base image: Python 3.11 slim variant for small attack surface and lean footprint (~140MB)
FROM python:3.11-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# Install runtime curl for container health check probe
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Layer caching optimization: copy requirements first so dependency installation
# is cached across source code modifications
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code after dependencies to maximize Docker layer cache hits
COPY . .

# Security hardening: run as an unprivileged non-root service user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose service port
EXPOSE 8000

# Container liveness health check targeting the unauthenticated /health probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch the FastAPI service via Uvicorn ASGI server
CMD ["uvicorn", "triage_api:app", "--host", "0.0.0.0", "--port", "8000"]
