#!/bin/bash

# Script de déploiement CryptoViz V3.0 - Data Lakehouse
echo "🚀 DÉPLOIEMENT CRYPTOVIZ V3.0 - DATA LAKEHOUSE"
echo "=============================================="

# Récupérer l'IP de la machine
MACHINE_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)
echo "🔧 IP détectée: $MACHINE_IP"

echo "📋 1. Arrêt des services V2..."
docker-compose -f docker-compose-redpanda.yml down

echo "📋 2. Build des nouvelles images V3..."
docker-compose -f docker-compose-v3-spark.yml build

echo "📋 3. Démarrage stack Data Lakehouse..."
docker-compose -f docker-compose-v3-spark.yml up -d

echo "📋 4. Attente initialisation (90 secondes)..."
echo "⏳ Services complexes en cours de démarrage..."
for i in {90..1}; do
    echo -ne "\r⏳ $i secondes restantes..."
    sleep 1
done
echo -e "\n✅ Attente terminée"

echo "📋 5. Vérification des services..."
echo ""
echo "🔥 REDPANDA:"
curl -s http://$MACHINE_IP:9644/v1/status/ready && echo " ✅ Redpanda API OK" || echo " ❌ Redpanda API KO"

echo "📦 MINIO S3:"
curl -s http://$MACHINE_IP:9002/minio/health/live && echo " ✅ MinIO OK" || echo " ❌ MinIO KO"

echo "⚡ SPARK MASTER:"
curl -s http://$MACHINE_IP:8081 > /dev/null && echo " ✅ Spark UI accessible" || echo " ❌ Spark UI inaccessible"

echo "🌊 STREAMING SERVER:"
curl -s http://$MACHINE_IP:5000/health | jq '.status' 2>/dev/null && echo " ✅ Streaming OK" || echo " ❌ Streaming KO"

echo "📊 DASHBOARD V3:"
curl -s http://$MACHINE_IP:8501 > /dev/null && echo " ✅ Dashboard V3 accessible" || echo " ❌ Dashboard V3 inaccessible"

echo ""
echo "🌐 URLS D'ACCÈS V3.0:"
echo "======================="
echo "📊 Dashboard V3:      http://$MACHINE_IP:8501"
echo "📡 Streaming API:     http://$MACHINE_IP:5000"
echo "⚡ Spark Master UI:   http://$MACHINE_IP:8081"
echo "📦 MinIO Console:     http://$MACHINE_IP:9002"
echo "🔧 Redpanda Console:  http://$MACHINE_IP:8090"

echo ""
echo "🔍 COMMANDES DE MONITORING:"
echo "============================="
echo "# Logs Spark Streaming:"
echo "docker logs crypto_spark_streaming"
echo ""
echo "# Status pipeline complet:"
echo "docker-compose -f docker-compose-v3-spark.yml ps"
echo ""
echo "# Logs tous services:"
echo "docker-compose -f docker-compose-v3-spark.yml logs -f"
echo ""
echo "# Test MinIO S3:"
echo "curl http://$MACHINE_IP:9002"
echo ""
echo "# Spark Jobs actifs:"
echo "curl -s http://$MACHINE_IP:8081/api/v1/applications | jq '.[].name'"

echo ""
echo "📊 ARCHITECTURE V3 DÉPLOYÉE:"
echo "============================="
echo "🔥 Redpanda    → Message Streaming"
echo "⚡ Spark       → Distributed Processing"
echo "📦 MinIO S3    → Object Storage (Lakehouse)"
echo "🧠 Parquet     → Columnar Data Format"
echo "📊 Dashboard   → Lakehouse Analytics UI"
echo "🌊 Streaming   → Real-time SSE (conservé)"

echo ""
echo "🎯 DATA FLOW V3:"
echo "=================="
echo "Scraper → Redpanda → Spark Stream → Parquet (S3) → Dashboard"
echo "                  ↘ Streaming SVR → SSE Live → Browser"

echo ""
echo "🎉 CryptoViz V3.0 Data Lakehouse déployé avec succès !"
echo "Accès principal: http://$MACHINE_IP:8501"
