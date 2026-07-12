FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt update -y && \
    apt install -y --no-install-recommends \
    gcc \
    libgl1 \
    libglib2.0-0 \
    gettext

# Install dependencies
COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    pip -r requirements.txt

# Copy application code
COPY ./assetmanagement .

# Set execute permission for entrypoint.sh
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Add a user with ID 1000
RUN adduser --disabled-password --gecos "" --uid 1000 appuser

# Set the default user to appuser
USER appuser

# Set the entrypoint
ENTRYPOINT ["sh", "/docker-entrypoint.sh"]