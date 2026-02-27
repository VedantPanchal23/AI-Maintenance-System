# ═══════════════════════════════════════════════════════════════
# Backend Dockerfile — Predictive Maintenance API
# Multi-stage build with CUDA support for PyTorch GPU inference
# ═══════════════════════════════════════════════════════════════

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Dependencies stage ──
FROM base AS deps

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install PyTorch CPU for Docker (GPU version requires nvidia-docker)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# ── Production stage ──
FROM base AS production

COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

COPY . .

# Create directories for ML models and logs
RUN mkdir -p /app/ml_models /app/logs

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
