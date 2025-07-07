# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHON_PATH="/app/" \
    POETRY_VIRTUALENVS_CREATE=false

# Install system dependencies and Poetry
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry

# Set work directory
WORKDIR /app

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock /app/

# Copy source code
COPY src/ /app/src/

# Install dependencies without dev dependencies
# and create a non-root user for better security
RUN poetry install --without dev --no-interaction --no-ansi && \
    groupadd -r appuser && useradd -r -g appuser appuser && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

ENV PORT=8000
CMD ["poetry", "run", "agent"]