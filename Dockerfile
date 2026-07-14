FROM python:3.11-slim

# Install uv binary directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Prevents uv from creating a virtual environment inside the container
ENV UV_SYSTEM_PYTHON=1 

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt update -y && \
    apt install -y --no-install-recommends \
    gcc \
    libgl1 \
    libglib2.0-0 \
    gettext && \
    rm -rf /var/lib/apt/lists/*

# Add a user with ID 1000 early to use for COPY --chown
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

# Copy dependency files (choose the option below that matches your progress)
# Option A: If you kept requirements.txt
COPY requirements.txt .
# Option B: If you switched to pyproject.toml & uv.lock (Recommended)
# COPY pyproject.toml uv.lock ./

# Install dependencies using uv (blazing fast)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

# (If using Option B above, replace the line above with: uv sync --frozen)

# Copy application code with proper ownership
COPY --chown=appuser:appuser ./assetmanagement .

# Set execute permission for entrypoint.sh
COPY --chown=appuser:appuser docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set the default user to appuser
USER appuser

# Set the entrypoint
ENTRYPOINT ["bash", "/docker-entrypoint.sh"]