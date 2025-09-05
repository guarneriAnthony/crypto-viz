FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tous les fichiers de l'application
COPY . .

# Variables d'environnement Panel
ENV PYTHONPATH=/app
ENV PANEL_ALLOW_WEBSOCKET_ORIGIN=*
ENV BOKEH_ALLOW_WEBSOCKET_ORIGIN=*

# Exposition du port
EXPOSE 5006

# DASHBOARD STREAMING KAFKA
CMD ["python", "kafka_streaming_dashboard.py"]
