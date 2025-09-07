FROM python:3.11-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code de l'application
COPY ml_processor.py .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV KAFKA_BOOTSTRAP_SERVERS=redpanda:9092
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379

CMD ["python3", "ml_processor.py"]
