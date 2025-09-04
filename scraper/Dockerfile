FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Installer les dépendances système pour python-snappy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libsnappy-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY providers/ ./providers/
CMD ["python", "./app.py"]
