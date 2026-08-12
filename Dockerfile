FROM python:3.11-slim

# Install uv binary directly from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Prevents uv from creating a virtual environment inside the container
ENV UV_SYSTEM_PYTHON=1 
ENV UV_PROJECT_ENVIRONMENT="/usr/local"

# Create and set working directory
WORKDIR /app
# this command will crete app directory in the container image and 
# cd into it, it now replaces assetmanagement directory.

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
# COPY requirements.txt .
# Option B: If you switched to pyproject.toml & uv.lock (Recommended)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (blazing fast)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# (If using Option B above, replace the line above with: uv sync --frozen)

# Copy application code with proper ownership
COPY --chown=appuser:appuser ./assetmanagement .
# this command here copies all the files from assetmanagement from my 
# laptop to the /app of the container image
# it also sets the ownership of the of the app to appuser
# Adding --chown=appuser:appuser ensures appuser actually owns the 
# application code inside /app so it can read, write, or create files there later.

# Set execute permission for entrypoint.sh
COPY --chown=appuser:appuser docker-entrypoint.sh /docker-entrypoint.sh
#Copies docker-entrypoint.sh from your computer into /docker-entrypoint.sh inside the container image, giving ownership to appuser.
RUN chmod +x /docker-entrypoint.sh
#it makes this file executable

# Set the default user to appuser
# USER appuser

# Set the entrypoint
ENTRYPOINT ["bash", "/docker-entrypoint.sh"]