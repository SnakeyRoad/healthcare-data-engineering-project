# Healthcare Data Engineering Project - Python Environment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create non-root user for security
RUN groupadd -r healthcare && useradd -r -g healthcare healthcare \
    && chown -R healthcare:healthcare /app

# Create necessary directories
RUN mkdir -p data/raw data/processed data/quality_reports logs \
    && chown -R healthcare:healthcare data logs

# Switch to non-root user
USER healthcare

# Expose port for optional web interface
EXPOSE 8000

# Default command (can be overridden)
CMD ["python", "scripts/main.py"]
