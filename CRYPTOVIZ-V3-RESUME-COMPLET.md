# 🚀 CryptoViz V3.0 - Data Lakehouse
## Résumé Complet du Projet

### 🎯 QU'EST-CE QUE CRYPTOVIZ ?

**CryptoViz** est une plateforme d'analytics crypto-monnaies temps réel qui a évolué à travers 3 versions architecturales majeures pour devenir un **Data Lakehouse moderne**.

**Mission** : Collecter, traiter et visualiser en temps réel les données de prix et métriques des cryptomonnaies depuis plusieurs sources APIs, avec une architecture évolutive et performante.

---

### 🏗️ ARCHITECTURE V3.0 - DATA LAKEHOUSE

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        📊 CRYPTOVIZ V3.0 - DATA LAKEHOUSE                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  🌐 APIs    │    │  🌐 APIs    │    │  🌐 APIs    │    │  🌐 APIs    │
│ CoinGecko   │    │CoinMarketCap│    │ Binance     │    │ Autres...   │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                  │                  │
       └──────────────────┼──────────────────┼──────────────────┘
                          │                  │
               ┌──────────▼──────────┐      │
               │  📥 CRYPTO SCRAPER  │      │
               │   (Data Collector)  │      │
               │                     │      │
               │ • Multi-providers   │      │
               │ • Rate limiting     │      │
               │ • Error handling    │      │
               └──────────┬──────────┘      │
                          │                  │
                          ▼                  │
               ┌──────────────────────┐     │
               │   📡 STREAMING       │     │
               │      SERVER          │     │
               │  (Kafka Producer)    │     │
               │                      │     │
               │ • Dual topics        │     │
               │ • Batch + Streaming  │     │
               │ • JSON serialization │     │
               └──────────┬───────────┘     │
                          │                  │
                          ▼                  │
               ┌──────────────────────┐     │
               │  🐾 REDPANDA         │     │
               │  (Message Broker)    │     │
               │                      │     │
               │ • Kafka-compatible   │     │
               │ • Port 19092         │     │
               │ • 3 partitions       │     │
               │ • Topics:            │     │
               │   - crypto-raw-data  │     │
               │   - crypto-streaming │     │
               └──────────┬───────────┘     │
                          │                  │
                          ▼                  │
               ┌──────────────────────┐     │
               │ ⚡ APACHE SPARK      │     │
               │   STREAMING          │     │
               │                      │     │
               │ • Master (8081)      │     │
               │ • Worker             │     │
               │ • Streaming Job      │     │
               │ • Real-time ETL      │     │
               │ • Schema validation  │     │
               │ • Data enrichment    │     │
               └──────────┬───────────┘     │
                          │                  │
                          ▼                  │
               ┌──────────────────────┐     │
               │  📦 MINIO S3         │     │
               │  (Object Storage)    │     │
               │                      │     │
               │ • Port 9002          │     │
               │ • Bucket: crypto-data│     │
               │ • Parquet format     │     │
               │ • Snappy compression │     │
               │ • Partitioning:      │     │
               │   /year/month/day/   │     │
               │   source/crypto/     │     │
               └──────────┬───────────┘     │
                          │                  │
                          ▼                  │
               ┌──────────────────────┐     │
               │ 📊 DASHBOARD V3      │     │
               │   (Streamlit)        │     │
               │                      │     │
               │ • Port 8501          │     │
               │ • s3fs reader        │     │
               │ • Parquet queries    │     │
               │ • Interactive viz    │     │
               │ • Real-time charts   │     │
               │ • DuckDB fallback    │     │
               └──────────────────────┘     │
                                            │
         ┌──────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ 💾 DUCKDB       │
│ (Fallback DB)   │
│                 │  
│ • OLAP engine   │
│ • Local storage │
│ • Fast queries  │
│ • Backup data   │
└─────────────────┘
```

---

### 🧬 COMPOSANTS DÉTAILLÉS

#### 1️⃣ **CRYPTO SCRAPER** (Collecteur de données)
- **Rôle** : Collecter les données crypto depuis les APIs externes
- **Technologies** : Python, aiohttp, asyncio
- **Providers supportés** :
  - 🟢 **CoinGecko** (gratuit, rate limit 50 req/min)
  - 🟡 **CoinMarketCap** (API key, rate limit flexible)
  - 🔵 **Extensible** (architecture modulaire pour nouveaux providers)
- **Fonctionnalités** :
  - Rate limiting automatique
  - Retry avec backoff exponentiel
  - Validation des données
  - Monitoring des erreurs

#### 2️⃣ **STREAMING SERVER** (Kafka Producer)
- **Rôle** : Publier les données dans Redpanda/Kafka
- **Technologies** : Python, kafka-python
- **Topics** :
  - `crypto-raw-data` → Données brutes pour batch processing
  - `crypto-streaming` → Données temps réel pour stream processing
- **Configuration** :
  - Sérialisation JSON
  - Compression automatique
  - Acknowledgment = ALL
  - Batching optimisé (16KB, 10ms linger)

#### 3️⃣ **REDPANDA** (Message Broker)
- **Rôle** : Message broker compatible Kafka
- **Avantages** :
  - Plus léger que Kafka
  - Compatible 100% avec l'API Kafka
  - Déploiement single-node simplifié
- **Configuration** :
  - Port 19092 (externe)
  - 3 partitions par topic
  - Réplication factor = 1

#### 4️⃣ **APACHE SPARK STREAMING** (ETL temps réel)
- **Rôle** : Traitement des données en streaming vers le Data Lake
- **Architecture** :
  - **Spark Master** (port 8081) - Orchestration
  - **Spark Worker** - Exécution des tâches
  - **Streaming Job** - Application métier
- **Traitement** :
  - Lecture depuis Redpanda
  - Validation et nettoyage des données
  - Enrichissement (calcul de métriques)
  - Partitionnement intelligent
  - Écriture Parquet optimisée

#### 5️⃣ **MINIO S3** (Data Lake Storage)
- **Rôle** : Stockage objet compatible S3 pour le Data Lake
- **Format** : Apache Parquet avec compression Snappy
- **Partitionnement** :
  ```
  s3://crypto-data/
  ├── year=2025/
  │   └── month=09/
  │       └── day=04/
  │           ├── source=coingecko/
  │           │   ├── crypto=bitcoin/
  │           │   └── crypto=ethereum/
  │           └── source=coinmarketcap/
  │               ├── crypto=bitcoin/
  │               └── crypto=ethereum/
  ```
- **Avantages** :
  - Stockage columnaire performant
  - Compression ~70%
  - Query pushdown
  - Schema evolution

#### 6️⃣ **DASHBOARD V3** (Interface utilisateur)
- **Rôle** : Visualisation interactive des données
- **Technologies** : Streamlit, Plotly, s3fs, pandas
- **Fonctionnalités** :
  - Lecture directe depuis MinIO avec s3fs
  - Graphiques temps réel interactifs
  - Métriques de performance
  - Sélection multi-crypto et multi-source
  - Mode Lakehouse + Fallback DuckDB
- **Onglets** :
  - **📈 Dashboard** : Graphiques principaux
  - **🔍 Explorer** : Navigation dans les données
  - **⚡ Performance** : Métriques Lakehouse
  - **📊 Management** : Administration des partitions

#### 7️⃣ **DUCKDB** (Fallback Database)
- **Rôle** : Base OLAP de secours et cache local
- **Utilisation** :
  - Fallback si MinIO indisponible
  - Cache pour requêtes fréquentes
  - Développement et tests

---

### 🔄 FLUX DE DONNÉES

```
APIs → Scraper → Streaming Server → Redpanda → Spark → MinIO → Dashboard
 ↓                                                              ↑
DuckDB ←←←←←←←←←←←←← Fallback Consumer ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←┘
```

**1. Collecte** : Scraper interroge les APIs toutes les 30s
**2. Publication** : Streaming Server publie vers Redpanda
**3. Traitement** : Spark consume et traite en micro-batches
**4. Stockage** : Données Parquet partitionnées dans MinIO
**5. Visualisation** : Dashboard lit depuis MinIO avec s3fs
**6. Fallback** : DuckDB comme solution de secours

---

### 🎯 POURQUOI CETTE ARCHITECTURE ?

#### **Performance** :
- Format Parquet columnaire → Requêtes 10x plus rapides
- Partitionnement intelligent → Scan sélectif des données
- Spark distribué → Scalabilité horizontale
- Cache multi-niveaux → Latence réduite

#### **Fiabilité** :
- Message broker découplé → Résistance aux pannes
- Stockage objet → Durabilité 99.999999999%
- Fallback DuckDB → Continuité de service
- Retry automatique → Auto-guérison

#### **Évolutivité** :
- Architecture microservices → Scaling indépendant
- Schema evolution → Ajout de champs sans impact
- Providers modulaires → Nouvelles sources facilement
- Format ouvert → Interopérabilité

#### **Observabilité** :
- Métriques Spark → Monitoring des performances
- Logs structurés → Debugging facilité
- Dashboard admin → Vue d'ensemble temps réel

---

### 📊 DONNÉES COLLECTÉES

**Cryptomonnaies supportées** : Bitcoin, Ethereum, Binance Coin, Tether, Solana, Ripple, Dogecoin, etc.

**Métriques par crypto** :
- Prix actuel (USD)
- Market cap
- Volume 24h
- Variations (1h, 24h, 7d)
- Timestamp précis
- Source de la donnée

**Enrichissement automatique** :
- Partitions temporelles
- Métadonnées d'ingestion
- Offsets Kafka
- Temps de processing

---

### 🚀 ÉVOLUTIONS FUTURES

**Court terme** :
- Alertes temps réel
- Plus de cryptos et métriques
- API REST pour accès externe

**Moyen terme** :
- Machine Learning (prédictions prix)
- Streaming analytics avancées
- Multi-tenancy

**Long terme** :
- Architecture multi-cloud
- Real-time OLAP avec Apache Druid
- GraphQL API

---

### 🛠️ DÉPLOIEMENT

**Prérequis** : Docker, Docker Compose
**Commandes** :
```bash
# Démarrage complet
docker-compose -f docker-compose-v3-spark.yml up -d

# Accès aux interfaces
- Dashboard: http://localhost:8501
- Spark UI: http://localhost:8081  
- MinIO UI: http://localhost:9001
- Redpanda Console: http://localhost:9644
```

**Ressources recommandées** :
- CPU: 4+ cores
- RAM: 8+ GB
- Stockage: 20+ GB SSD

---

### 🎯 RÉSUMÉ EXÉCUTIF

**CryptoViz V3.0** est une plateforme Data Lakehouse moderne qui transforme les données crypto en temps réel en insights actionnables. L'architecture distribué avec Spark + MinIO + Redpanda offre performance, fiabilité et évolutivité pour traiter des millions de points de données crypto quotidiennement.

**Valeur ajoutée** : Pipeline 100% temps réel, format ouvert Parquet, fallback intégré, monitoring complet, interface utilisateur intuitive.

**Status** : ✅ Production Ready
