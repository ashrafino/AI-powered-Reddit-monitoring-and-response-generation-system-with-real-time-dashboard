# Multi-stage build for faster builds and smaller images
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --upgrade pip && \
    pip install --user --no-warn-script-location -r /tmp/requirements.txt

# Production stage
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/app/.local/bin:$PATH"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash app

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/app/.local

# Copy initialization script
COPY docker/init.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/init.sh

# Copy application code
COPY --chown=app:app . /app

USER app

ENTRYPOINT ["/usr/local/bin/init.sh"]

ENV PORT=8000
EXPOSE 8000

# Use gunicorn for production
CMD ["gunicorn", "app.main:app", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000", "--workers", "1"]


