# CryptoViz V3.0 - Data Lakehouse Pipeline 🚀

Pipeline temps réel de données crypto avec architecture data lakehouse moderne, partitioning optimisé et interfaces de monitoring.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Scraper      │───▶│    Redpanda     │───▶│  Spark Stream   │───▶│  MinIO (S3)     │
│   Multi-API     │    │   (Kafka)       │    │   Processing    │    │  Partitioned    │
│ • CoinMarketCap │    │ • crypto-raw-data│    │ • Partitioning  │    │ • Y/M/D struct  │
│ • CoinGecko     │    │ • Real-time     │    │ • Y/M/D columns │    │ • Parquet       │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │                       │
         ▼                       ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                            Dashboard Streamlit                                          │
│          • Lecture temps réel MinIO • Graphiques interactifs • Métriques live          │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

## ✨ Fonctionnalités V3.0

### 🔄 Pipeline Temps Réel
- **Scraping multi-sources** : CoinMarketCap + CoinGecko (17 cryptos)
- **Streaming haute performance** : Apache Spark + Redpanda (Kafka)
- **Partitioning intelligent** : Structure année/mois/jour optimisée pour analytics
- **Stockage S3** : MinIO avec compression Snappy

### 📊 Data Lakehouse
- **Structure partitionnée** : `year=2025/month=09/day=05/`
- **Format optimisé** : Apache Parquet pour requêtes rapides
- **Compression** : Snappy pour réduction espace disque
- **Métadonnées** : Schema evolution et historique complet

### 🎯 Monitoring & UI
- **Redpanda Console** : Monitoring Kafka topics temps réel
- **MinIO Browser** : Gestion buckets S3 et exploration données
- **Dashboard Streamlit** : Visualisations crypto interactives
- **Métriques** : CPU, mémoire, throughput pipeline

## 🚀 Démarrage Rapide

### Prerequisites
```bash
# Docker & Docker Compose requis
docker --version && docker-compose --version
```

### 1. Clonage et Configuration
```bash
git clone <repo-url>
cd crypto-viz
cp .env.example .env
# Éditer .env avec vos API keys
```

### 2. Lancement Pipeline Complet
```bash
# Démarrage complet (tous services)
docker-compose -f docker-compose-v3-final.yml up -d

# Vérification état services
docker ps --filter network=crypto-viz_crypto-net
```

### 3. Interfaces Disponibles
- **Dashboard** : http://localhost:8501
- **Redpanda Console** : http://localhost:8090
- **MinIO Browser** : http://localhost:9001 (cryptoviz/cryptoviz2024)

## 📁 Structure Données

### Buckets MinIO
```
crypto-data-partitioned/          # 🎯 Données actuelles (Y/M/D)
├── year=2025/
│   ├── month=09/
│   │   ├── day=05/
│   │   │   ├── part-00000-xxx.snappy.parquet
│   │   │   └── part-00001-xxx.snappy.parquet
│   │   └── day=06/...
│   └── month=10/...
└── year=2024/...

crypto-data/                      # 📚 Archive historique
├── part-00000-legacy.parquet     # Format non-partitionné (historique)
└── ...
```

### Schema Données
```json
{
  "name": "Bitcoin",
  "symbol": "BTC", 
  "price": 67891.23,
  "market_cap": 1337000000000.0,
  "volume_24h": 28500000000.0,
  "change_1h": 0.15,
  "change_24h": 2.34,
  "change_7d": -1.23,
  "source": "coinmarketcap",
  "timestamp": "2025-09-05 20:12:00",
  "ingestion_timestamp": "2025-09-05T20:12:00.123456",
  "year": 2025,
  "month": 9,
  "day": 5
}
```

## ⚙️ Configuration Services

### Variables d'Environnement
```bash
# APIs
COINMARKETCAP_API_KEY=your-api-key

# MinIO S3
MINIO_ACCESS_KEY=cryptoviz
MINIO_SECRET_KEY=cryptoviz2024
MINIO_ENDPOINT=http://minio:9000

# Kafka/Redpanda
REDPANDA_BROKERS=redpanda:9092
```

### Tuning Performance
```bash
# Spark Streaming
SPARK_EXECUTOR_MEMORY=1g
SPARK_DRIVER_MEMORY=512m
BATCH_INTERVAL=60s              # Traitement par batch de 60s

# Scraper
SCRAPE_INTERVAL=60s             # Collecte toutes les 60s
MAX_CRYPTOS=17                  # Top 17 cryptos
```

## 🔧 Commandes Maintenance

### Monitoring
```bash
# État pipeline complet
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Logs services
docker logs crypto_spark_streaming --tail 20
docker logs crypto_scraper --tail 20
docker logs crypto_redpanda --tail 20

# Vérification données MinIO
docker exec crypto_minio mc ls --recursive local/crypto-data-partitioned/
```

### Debug & Troubleshooting
```bash
# Test connectivité Kafka
docker exec crypto_redpanda rpk topic list
docker exec crypto_redpanda rpk topic consume crypto-raw-data --num 5

# Test MinIO
docker exec crypto_minio mc ls local/

# Restart services
docker-compose -f docker-compose-v3-final.yml restart spark-streaming
```

## 📈 Métriques & Performance

### Throughput Typique
- **Ingestion** : ~17 records/minute (1 crypto/3.5s)
- **Latence E2E** : < 2 minutes (scrape → dashboard)
- **Stockage** : ~5KB/record (compression Snappy)
- **Partitions** : Auto-création quotidienne

### Optimisations V3.0
- ✅ Partitioning Y/M/D pour requêtes analytiques rapides
- ✅ Compression Parquet/Snappy (-70% espace disque)
- ✅ Streaming micro-batch (60s) vs polling
- ✅ Cache Streamlit intelligent
- ✅ JAR Kafka auto-téléchargement Spark

## 🔄 Évolutions Futures

### Roadmap V3.1
- [ ] Migration Dashboard Streamlit → Panel/Bokeh (WebSocket)
- [ ] Intégration Spark SQL pour analytics avancées
- [ ] ML Pipeline (prédictions prix)
- [ ] Alertes temps réel (seuils prix)
- [ ] API REST exposition données

### Améliorations Architecture
- [ ] Auto-scaling Spark Workers
- [ ] Backup automatique MinIO → Cloud S3
- [ ] Monitoring Prometheus/Grafana
- [ ] CI/CD Pipeline automatisé

## 🐛 Problèmes Connus

### Limitations
- **Rate Limiting** : APIs publiques limitées (60 req/min)
- **Données historiques** : Limitées aux derniers collectés
- **Single Point** : Une instance par service (pas HA)

### Solutions
- Utiliser des API keys premium pour rate limits plus élevés
- Implémenter backup/restore pour données historiques
- Configurer réplication services critiques

## 🤝 Contribution

### Development Setup
```bash
# Clone repo
git clone <repo-url>
cd crypto-viz

# Tests unitaires
python -m pytest tests/

# Linting
flake8 src/
black src/
```

### Architecture Decisions
- **Parquet** : Format colonnaire optimisé analytics
- **Partitioning Y/M/D** : Compatible Spark, Hive, Trino
- **Redpanda** : Plus performant que Kafka vanilla
- **MinIO** : Compatible S3, déploiement local simple

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE) pour détails.

---

## 🔗 Links Utiles

- [Apache Spark Streaming Guide](https://spark.apache.org/docs/latest/structured-streaming-programming-guide.html)
- [MinIO Documentation](https://docs.min.io/)
- [Redpanda Kafka API](https://docs.redpanda.com/)
- [CoinMarketCap API](https://coinmarketcap.com/api/)

**CryptoViz V3.0** - Pipeline Data Lakehouse moderne pour analytics crypto temps réel 🚀
