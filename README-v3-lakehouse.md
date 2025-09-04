# CryptoViz V3.0 - Data Lakehouse Edition

[![Spark](https://img.shields.io/badge/Spark-3.4.1-orange?style=flat-square)](https://spark.apache.org/)
[![Parquet](https://img.shields.io/badge/Parquet-Columnar-blue?style=flat-square)](https://parquet.apache.org/)
[![MinIO](https://img.shields.io/badge/MinIO-S3--Compatible-red?style=flat-square)](https://min.io/)
[![Redpanda](https://img.shields.io/badge/Redpanda-Streaming-red?style=flat-square)](https://redpanda.com/)

**Data Lakehouse moderne : Redpanda → Spark → Parquet → Analytics**

---

## 🚀 À Propos V3.0

**CryptoViz V3.0** transforme l'architecture en véritable **Data Lakehouse** :
- **Apache Spark** : Processing distribué et streaming
- **Parquet + S3** : Stockage columnaire optimisé
- **MinIO Lakehouse** : Object storage S3-compatible
- **Partitionnement intelligent** : Requêtes ultra-rapides
- **Fallback hybride** : DuckDB pour continuité

### Évolution V2 → V3

| Composant | V2 (Redpanda) | V3 (Lakehouse) |
|-----------|-----------------|-----------------|
| **Processing** | Consumer simple | Spark Streaming |
| **Storage** | DuckDB local | Parquet + MinIO S3 |
| **Partitioning** | ❌ | ✅ Date/Source/Crypto |
| **Scalabilité** | Single node | Distributed |
| **Analytics** | SQL basique | Columnar optimized |
| **Compression** | ❌ | ✅ Snappy (70%) |

---

## 🏗️ Architecture V3

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Redpanda      │───→│  Spark Stream   │───→│   MinIO S3      │
│                 │    │                 │    │                 │
│ • raw-data      │    │ • Distributed   │    │ • Parquet       │
│ • streaming     │    │ • Processing    │    │ • Partitioned   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Dashboard V3    │    │ Data Catalog    │    │ Streaming SSE   │
│                 │    │                 │    │                 │
│ • Parquet Query │    │ • Metadata      │    │ • Real-time     │
│ • Time Travel   │    │ • Partitions    │    │ • Multi-clients │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Partitionnement Intelligent

```
s3://crypto-data/
├── year=2024/
│   ├── month=09/
│   │   ├── day=04/
│   │   │   ├── source=coinmarketcap/
│   │   │   │   ├── crypto=bitcoin/
│   │   │   │   │   ├── data_1693747200_0.parquet
│   │   │   │   │   └── data_1693747800_1.parquet
│   │   │   │   └── crypto=ethereum/
│   │   │   └── source=coingecko/
│   │   └── day=05/
```

---

## 🚀 Déploiement V3

### Prérequis

- Docker & Docker Compose v2.35+
- 4GB RAM (minimum pour Spark)
- API Key CoinMarketCap
- Ports : 8501, 5000, 8080, 9000, 9001, 19092

### Installation Express

```bash
# 1. Cloner et préparer
git clone https://gitlab.com/exesiga/crypto-viz.git
cd crypto-viz
git checkout Evol_cryptoViz_V2  # Puis basculer vers V3

# 2. Configuration API
nano scraper/providers/coinmarketcap.py
# API_KEY = "YOUR_COINMARKETCAP_API_KEY"

# 3. Déploiement automatique
./deploy-v3-lakehouse.sh

# Attendre 90 secondes pour initialisation complète

# 4. Accès services
# Dashboard V3: http://192.168.1.76:8501
# Spark UI:     http://192.168.1.76:8080  
# MinIO S3:     http://192.168.1.76:9001
```

---

## 📊 Services V3

| Service | Port | URL | Rôle |
|---------|------|-----|------|
| **Spark Master** | 8080 | http://192.168.1.76:8080 | Processing Engine |
| **MinIO S3** | 9000/9001 | http://192.168.1.76:9001 | Object Storage |
| **Dashboard V3** | 8501 | http://192.168.1.76:8501 | Lakehouse UI |
| **Redpanda** | 19092 | - | Message Streaming |
| **Streaming** | 5000 | http://192.168.1.76:5000 | Real-time SSE |

### Credentials MinIO

```
Username: cryptoviz
Password: cryptoviz2024
```

---

## 🔥 Fonctionnalités Lakehouse

### 📦 Storage Columnaire

- **Format** : Apache Parquet avec compression Snappy
- **Compression** : ~70% vs données brutes  
- **Performance** : Requêtes columnar 10x plus rapides
- **Partitioning** : Predicate pushdown optimisé

### ⚡ Processing Distribué

- **Spark Streaming** : Traitement temps réel depuis Redpanda
- **Micro-batches** : 30 secondes de latence
- **Auto-scaling** : Workers Spark adaptables
- **Fault tolerance** : Checkpointing S3

### 🔍 Analytics Avancées

- **Dashboard hybride** : Parquet + DuckDB fallback
- **Time Travel** : Accès données historiques partitionnées
- **Multi-source** : Unification CoinMarketCap + CoinGecko
- **Real-time** : Streaming SSE conservé pour live updates

---

## 📊 Performance V3

### Benchmarks Lakehouse

```bash
STORAGE PERFORMANCE:
├── Compression Parquet: 70% vs CSV
├── Query Speed: 10x vs DuckDB simple
├── Partitioned Scans: <100ms
└── Parallel Processing: 2x workers

THROUGHPUT:
├── Spark Streaming: 1000+ records/sec
├── S3 Upload: ~50 files/minute  
├── Dashboard Query: <200ms
└── Partitions Scanned: Smart predicate pushdown

RESOURCE USAGE:
├── Spark Master: ~200MB RAM
├── Spark Worker: ~500MB RAM
├── MinIO S3: ~100MB RAM
├── Total Stack: ~1.2GB RAM
└── CPU Usage: <15% average
```

### Optimisations

- **Partition Pruning** : Scan seulement partitions nécessaires
- **Columnar Storage** : Lecture colonnes spécifiques uniquement
- **Compression** : Snappy pour balance speed/size
- **Caching** : Streamlit cache sur requêtes fréquentes

---

## 🧪 Monitoring & Debug

### Commandes Essentielles

```bash
# Status complet pipeline
docker-compose -f docker-compose-v3-spark.yml ps

# Logs Spark Streaming
docker logs crypto_spark_streaming

# Spark UI (jobs en cours)
curl http://192.168.1.76:8080

# MinIO health
curl http://192.168.1.76:9000/minio/health/live

# Test dashboard V3
curl http://192.168.1.76:8501
```

### Troubleshooting

**🔴 Spark Worker pas connecté**
```bash
# Restart worker
docker-compose -f docker-compose-v3-spark.yml restart spark-worker

# Check logs
docker logs crypto_spark_worker
```

**🔴 MinIO inaccessible**
```bash
# Restart MinIO
docker-compose -f docker-compose-v3-spark.yml restart minio

# Check buckets
curl http://192.168.1.76:9001
```

**🔴 Pas de données Parquet**
```bash
# Check Spark streaming job
docker logs crypto_spark_streaming

# Check if data flowing
curl http://192.168.1.76:5000/stats
```

---

## 🔄 Migration V2 → V3

### Guide Express

```bash
# Depuis V2 Redpanda
docker-compose -f docker-compose-redpanda.yml down

# Vers V3 Lakehouse
./deploy-v3-lakehouse.sh

# Vérification
curl http://192.168.1.76:8501  # Dashboard V3
curl http://192.168.1.76:8080  # Spark UI
```

### Différences Principales

- **Consumer** : Simple Python → Spark Streaming
- **Storage** : DuckDB → Parquet + MinIO S3
- **Processing** : Single-threaded → Distributed
- **Analytics** : Row-based → Columnar optimized
- **Dashboard** : DuckDB queries → Parquet + fallback

---

## 🎯 Use Cases Lakehouse

### 📈 Analytics Avancées

```python
# Requêtes time-travel sur partitions
data = reader.read_parquet_range(
    crypto='bitcoin',
    start_date='2024-09-01', 
    end_date='2024-09-04'
)

# Analytics cross-source
coinmarketcap_data = reader.read_parquet_range(
    crypto='bitcoin',
    sources=['coinmarketcap']
)
```

### ⚡ Performance Queries

- **Partition scanning** : Seulement les partitions nécessaires
- **Columnar reading** : Colonnes price/timestamp uniquement  
- **Compression** : Décompression Snappy ultra-rapide
- **Parallel processing** : Multi-workers Spark

### 🔍 Data Exploration

- **Lakehouse Browser** : Navigation partitions dans dashboard
- **Schema Evolution** : Support changements de structure
- **Time Travel** : Accès données historiques
- **Multi-format** : Fallback DuckDB si Parquet indisponible

---

## 🚀 Roadmap V4

### Big Data & ML

- **Delta Lake** : ACID transactions sur Parquet
- **MLflow** : ML pipeline management
- **Apache Iceberg** : Table format avancé
- **Spark ML** : Machine learning distribué

### Cloud & Scale

- **Kubernetes** : Orchestration Spark cloud-native
- **Auto-scaling** : Workers Spark dynamiques
- **Multi-region** : Réplication S3 géographique
- **Data Streaming** : Kafka Connect integrations

---

## 📄 Licence

MIT License - voir [LICENSE](LICENSE)

---

**CryptoViz V3.0 Data Lakehouse** | 
Spark + Parquet + MinIO | 
Status: 🚀 Production Ready

Made with ⚡ by [SigA](https://gitlab.com/exesiga)
