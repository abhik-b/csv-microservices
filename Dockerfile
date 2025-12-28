#1 Use official Python image
FROM python:3.11-slim

#2 Set working directory
WORKDIR /app

#3 Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src

#4 Install system dependencies (PostgreSQL client, etc.)
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

#5 Copy requirements file
COPY requirements.txt .

#6 Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

#7 Copy application code
COPY . .

RUN mkdir -p /app/uploads /app/output

#8 Expose port & run fastapi
EXPOSE 8000
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Below does not work
# CMD ["fastapi", "run", "src/app/main.py", "--host", "0.0.0.0", "--port", "8000"]
