# Dashboard Panel - CryptoViz V3.0

## 📁 Structure Organisée

### 🚀 Fichiers Principaux (Production)
- `kafka_streaming_dashboard.py` - **Dashboard principal actuel** (utilisé par Docker)
- `app.py` - Point d'entrée Panel/Bokeh 
- `Dockerfile` - Configuration Docker
- `requirements.txt` - Dépendances Python

### 🧩 Composants Modulaires
- `components/` - Composants réutilisables
  - `charts.py` - Graphiques Bokeh
  - `layout.py` - Layouts et templates
  - `metrics.py` - Métriques et indicateurs
  - `sparklines.py` - Mini-graphiques de tendance
- `utils/` - Utilitaires
  - `parquet_reader_partitioned.py` - Lecture données MinIO

### 🎨 Interface Moderne (En Développement)
- `modern_ui_wip/` - Nouvelle interface style CoinMarketCap
  - `modern_crypto_dashboard.py` - Dashboard moderne
  - `modern_streaming_dashboard.py` - Version streaming
  - `simple_modern_test.py` - Version test avec données simulées

### 🗃️ Archives
- `archive_old_dashboards/` - Anciens fichiers (sauvegardés)
- `crypto_modern_ui.py` - Interface moderne v1
- `crypto_reader.py` - Ancien lecteur de données

## 🌐 Accès au Dashboard

**URL Principale :** http://192.168.1.76:5006  
**Dashboard actuel :** Real Crypto Kafka Stream Dashboard

## 🔧 Développement

### Dashboard Fonctionnel (main)
```bash
# Tourne actuellement en Docker
docker-compose up -d crypto-dashboard-panel
```

### Interface Moderne (branch: moderne-ui)
```bash
# En développement sur cette branche
git checkout moderne-ui
# Modifications progressives pour créer interface style CoinMarketCap
```

## 📝 Notes

- ✅ Version stable : `kafka_streaming_dashboard.py`
- 🚧 Version moderne : En développement dans `modern_ui_wip/`
- 🎯 Objectif : Interface moderne style CoinMarketCap
- 🔄 Streaming : Données temps réel depuis Kafka/MinIO
