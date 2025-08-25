FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Installer les dépendances système pour numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les fichiers de l'application
COPY app.py .
COPY pages/ ./pages/
COPY utils/ ./utils/

CMD ["python", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
