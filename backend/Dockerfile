# ============================================
# Stage 1: Base Image
# ============================================
FROM python:3.14-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium chromium-driver wget curl gnupg ca-certificates fonts-liberation \
    libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcups2 \
    libdbus-1-3 libdrm2 libgbm1 libgtk-3-0 libnspr4 libnss3 \
    libwayland-client0 libxcomposite1 libxdamage1 libxfixes3 libxkbcommon0 \
    libxrandr2 xdg-utils procps lsb-release \
    && ln -s /usr/bin/chromium /usr/bin/google-chrome || true \
    && rm -rf /var/lib/apt/lists/*


# ============================================
# Stage 2: Install dependencies via UV
# ============================================
FROM base AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml ./

RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache -r pyproject.toml

# ============================================
# Stage 3: Runtime
# ============================================
FROM base AS runtime

RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

WORKDIR /app
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv
COPY --chown=appuser:appuser ./app ./app

ENV PATH="/opt/venv/bin:$PATH" \
    VIRTUAL_ENV="/opt/venv"

USER appuser
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
