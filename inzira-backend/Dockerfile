# syntax=docker/dockerfile:1
FROM python:3.10-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    INZIRA_ENV=production

WORKDIR /app

# System deps for psycopg2, cryptography, spaCy
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-prod.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-prod.txt

COPY . .

# Ensure opportunity registry is never stripped by ignore globs mid-build.
COPY registry.db /app/registry.db

RUN useradd -m -u 1000 user \
    && mkdir -p /app/models /home/user/.cache \
    && chmod +x scripts/start_production.sh \
    && chown -R user:user /app /home/user

USER user
ENV HOME=/home/user \
    USER=user \
    TORCHINDUCTOR_CACHE_DIR=/tmp/torch-cache \
    TORCH_COMPILE_DISABLE=1

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=30s --start-period=180s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["bash", "scripts/start_production.sh"]
