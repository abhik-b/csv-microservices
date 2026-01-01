# api-service
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/src:$PYTHONPATH  


RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL api related files
COPY src/ ./src/
COPY templates/ ./templates/

RUN mkdir -p uploads outputs

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]