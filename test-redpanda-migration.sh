#!/bin/bash

# Récupérer l'IP de la machine
MACHINE_IP=$(ip route get 1.1.1.1 | awk '{print $7}' | head -1)
echo "🔧 IP détectée: $MACHINE_IP"

echo "🚀 TEST DE MIGRATION REDIS → REDPANDA"
echo "======================================"

echo "📋 1. Arrêt des services existants..."
docker-compose down

echo "📋 2. Nettoyage des volumes (optionnel)..."
read -p "Nettoyer les volumes existants ? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    docker volume prune -f
    echo "✅ Volumes nettoyés"
fi

echo "📋 3. Build des nouvelles images..."
docker-compose -f docker-compose-redpanda.yml build

echo "📋 4. Démarrage avec Redpanda..."
docker-compose -f docker-compose-redpanda.yml up -d

echo "📋 5. Attente du démarrage des services..."
echo "⏳ Attente 45 secondes pour l'initialisation complète..."
for i in {45..1}; do
    echo -ne "\r⏳ $i secondes restantes..."
    sleep 1
done
echo -e "\n✅ Attente terminée"

echo "📋 6. Vérification des services..."
docker-compose -f docker-compose-redpanda.yml ps

echo "📋 7. Vérification santé Redpanda..."
curl -s http://$MACHINE_IP:9644/v1/status/ready && echo "✅ Redpanda API OK" || echo "❌ Redpanda API KO"

echo "📋 8. Test streaming server..."
curl -s http://$MACHINE_IP:5000/health | jq '.' 2>/dev/null && echo "✅ Streaming Server OK" || echo "❌ Streaming Server KO"

echo "📋 9. Test streaming stats..."
curl -s http://$MACHINE_IP:5000/stats | jq '.backend' 2>/dev/null

echo "📋 10. Test dashboard..."
curl -s http://$MACHINE_IP:8501 > /dev/null && echo "✅ Dashboard accessible" || echo "❌ Dashboard inaccessible"

echo ""
echo "🌐 URLS D'ACCÈS:"
echo "=================="
echo "📊 Dashboard:        http://$MACHINE_IP:8501"
echo "📡 Streaming:        http://$MACHINE_IP:5000"
echo "🔧 Console Redpanda: http://$MACHINE_IP:8080"
echo "📈 API Redpanda:     http://$MACHINE_IP:9644"

echo ""
echo "📋 COMMANDES DE TEST:"
echo "======================="
echo "# Test streaming manual:"
echo "curl http://$MACHINE_IP:5000/test"
echo ""
echo "# Stream temps réel:"
echo "curl -N http://$MACHINE_IP:5000/stream"
echo ""
echo "# Logs services:"
echo "docker-compose -f docker-compose-redpanda.yml logs -f scraper"
echo "docker-compose -f docker-compose-redpanda.yml logs -f consumer"
echo "docker-compose -f docker-compose-redpanda.yml logs -f streaming_server"

echo ""
echo "🎉 Migration terminée ! Services démarrés avec Redpanda sur $MACHINE_IP"
