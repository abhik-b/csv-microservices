# worker-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src:$PYTHONPATH

# Install system dependencies for pandas (optional)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create output directory
RUN mkdir -p uploads output

# RUN groupadd -r celeryuser && useradd -r -g celeryuser celeryuser

# # Ensure the user has permissions to the working directories
# RUN chown -R celeryuser:celeryuser /app /app/uploads /app/output

# # Switch to the non-root user
# USER celeryuser

# Default command
CMD ["celery", "-A", "src.tasks", "worker", "--loglevel=info"]