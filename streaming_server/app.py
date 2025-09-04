from flask import Flask, Response, jsonify
from flask_cors import CORS
import json
import time
import logging
import threading
from datetime import datetime
import queue
import os
from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configuration
app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin depuis le dashboard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Stats globales du streaming
streaming_stats = {
    'connected_clients': 0,
    'messages_sent': 0,
    'uptime': datetime.now(),
    'last_data_received': None,
    'redpanda_status': 'disconnected'
}

class RedpandaStreamingManager:
    """Gestionnaire centralisé du streaming avec Redpanda"""
    
    def __init__(self):
        self.clients = {}  # Dict des clients connectés
        self.running = False
        self.consumer = None
        self.consumer_thread = None
        
    def start(self):
        """Démarre le gestionnaire de streaming"""
        if self.running:
            logger.info("⚠️ Streaming Manager déjà démarré")
            return
            
        self.running = True
        
        try:
            # Configuration Redpanda Consumer
            brokers = os.getenv("REDPANDA_BROKERS", "redpanda:9092")
            
            self.consumer = KafkaConsumer(
                'crypto-streaming',  # Topic pour streaming temps réel
                bootstrap_servers=[brokers],
                group_id='crypto-streaming-consumer',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda m: m.decode('utf-8') if m else None,
                auto_offset_reset='latest',  # Nouveaux messages seulement
                enable_auto_commit=True,
                session_timeout_ms=30000, heartbeat_interval_ms=10000  # Timeout court pour réactivité
            )
            
            streaming_stats['redpanda_status'] = 'connected'
            logger.info("✅ Connexion Redpanda établie")
            logger.info(f"📡 Brokers: {brokers}")
            logger.info(f"📊 Topic: crypto-streaming")
            
        except Exception as e:
            logger.error(f"❌ Erreur connexion Redpanda: {e}")
            streaming_stats['redpanda_status'] = 'error'
            return False
        
        # Démarrer le thread d'écoute Redpanda
        self.consumer_thread = threading.Thread(target=self._listen_redpanda, daemon=True)
        self.consumer_thread.start()
        
        logger.info("🚀 Streaming Manager démarré avec succès")
        return True
    
    def _listen_redpanda(self):
        """Écoute les messages Redpanda et les diffuse aux clients"""
        logger.info("👂 Démarrage écoute Redpanda...")
        
        try:
            for message in self.consumer:
                if not self.running:
                    break
                    
                try:
                    # Décoder le message
                    crypto_data = message.value
                    streaming_stats['last_data_received'] = datetime.now()
                    
                    crypto_name = crypto_data.get('name', 'Unknown')
                    logger.info(f"📡 Nouvelle donnée: {crypto_name} - Diffusion à {len(self.clients)} clients")
                    
                    # Préparer le message pour SSE
                    sse_message = {
                        'type': 'crypto_update',
                        'data': crypto_data,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'redpanda'
                    }
                    
                    # Diffuser à tous les clients connectés
                    self._broadcast_to_clients(json.dumps(sse_message))
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Erreur parsing JSON: {e}")
                except Exception as e:
                    logger.error(f"❌ Erreur traitement message: {e}")
                    
        except KafkaError as e:
            logger.error(f"❌ Erreur Kafka: {e}")
            streaming_stats['redpanda_status'] = 'error'
        except Exception as e:
            logger.error(f"❌ Erreur Redpanda listen: {e}")
            streaming_stats['redpanda_status'] = 'error'
    
    def _broadcast_to_clients(self, message):
        """Diffuse un message à tous les clients connectés"""
        if not self.clients:
            return
            
        dead_clients = []
        
        for client_id, client_queue in list(self.clients.items()):
            try:
                # Mettre le message dans la queue du client (non-bloquant)
                client_queue.put_nowait(message)
                streaming_stats['messages_sent'] += 1
                
            except queue.Full:
                # Queue du client pleine - client trop lent, on le déconnecte
                logger.warning(f"⚠️ Client {client_id} queue pleine - déconnexion")
                dead_clients.append(client_id)
                
            except Exception as e:
                logger.error(f"❌ Erreur envoi à client {client_id}: {e}")
                dead_clients.append(client_id)
        
        # Nettoyer les clients déconnectés
        for client_id in dead_clients:
            self.remove_client(client_id)
    
    def add_client(self, client_id):
        """Ajouter un client au streaming"""
        client_queue = queue.Queue(maxsize=50)  # Buffer de 50 messages max
        self.clients[client_id] = client_queue
        streaming_stats['connected_clients'] = len(self.clients)
        
        logger.info(f"➕ Client {client_id} connecté (total: {len(self.clients)})")
        
        # Message de bienvenue
        welcome_msg = {
            'type': 'welcome',
            'message': 'Streaming CryptoViz Redpanda connecté',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat(),
            'backend': 'redpanda'
        }
        
        try:
            client_queue.put_nowait(json.dumps(welcome_msg))
        except:
            pass
            
        return client_queue
    
    def remove_client(self, client_id):
        """Retirer un client du streaming"""
        if client_id in self.clients:
            del self.clients[client_id]
            streaming_stats['connected_clients'] = len(self.clients)
            logger.info(f"➖ Client {client_id} déconnecté (total: {len(self.clients)})")

# Instance globale du gestionnaire
streaming_manager = RedpandaStreamingManager()

@app.route('/stream')
def stream():
    """Endpoint principal de streaming SSE"""
    client_id = f"client_{int(time.time() * 1000)}"  # ID unique basé sur timestamp
    
    def generate():
        # Ajouter le client
        client_queue = streaming_manager.add_client(client_id)
        
        try:
            while True:
                try:
                    # Attendre un message (timeout 30s pour heartbeat)
                    message = client_queue.get(timeout=30)
                    yield f"data: {message}\n\n"
                    
                except queue.Empty:
                    # Pas de message - envoyer heartbeat
                    heartbeat = {
                        'type': 'heartbeat',
                        'timestamp': datetime.now().isoformat(),
                        'backend': 'redpanda',
                        'stats': {
                            'connected_clients': streaming_stats['connected_clients'],
                            'messages_sent': streaming_stats['messages_sent'],
                            'redpanda_status': streaming_stats['redpanda_status']
                        }
                    }
                    yield f"data: {json.dumps(heartbeat)}\n\n"
                    
        except GeneratorExit:
            # Client fermé la connexion proprement
            streaming_manager.remove_client(client_id)
        except Exception as e:
            logger.error(f"❌ Erreur streaming client {client_id}: {e}")
            streaming_manager.remove_client(client_id)
    
    return Response(
        generate(),
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Cache-Control',
            'X-Accel-Buffering': 'no'  # Disable nginx buffering
        }
    )

@app.route('/stats')
def get_stats():
    """Endpoint pour les statistiques du streaming"""
    current_stats = streaming_stats.copy()
    current_stats['uptime_seconds'] = (datetime.now() - current_stats['uptime']).total_seconds()
    current_stats['uptime'] = current_stats['uptime'].isoformat()
    current_stats['backend'] = 'redpanda'
    
    if current_stats['last_data_received']:
        current_stats['last_data_received'] = current_stats['last_data_received'].isoformat()
    
    return jsonify(current_stats)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test Redpanda via consumer status
        redpanda_status = 'ok' if streaming_manager.consumer else 'error'
    except:
        redpanda_status = 'error'
    
    health_status = {
        'status': 'healthy' if redpanda_status == 'ok' else 'unhealthy',
        'redpanda': redpanda_status,
        'streaming': 'active' if streaming_manager.running else 'inactive',
        'clients': len(streaming_manager.clients) if streaming_manager.clients else 0,
        'timestamp': datetime.now().isoformat(),
        'backend': 'redpanda'
    }
    
    return jsonify(health_status), 200 if redpanda_status == 'ok' else 500

@app.route('/test')
def test():
    """Endpoint de test pour vérifier le streaming"""
    test_data = {
        'name': 'TestCoin',
        'symbol': 'TEST',
        'price': 42.42,
        'percent_change_24h': 1.23,
        'market_cap': 1000000,
        'source': 'test',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ingestion_timestamp': datetime.now().isoformat(),
        'producer_id': 'test-endpoint',
        'schema_version': '2.0'
    }
    
    # Simuler la réception d'un message
    sse_message = {
        'type': 'crypto_update',
        'data': test_data,
        'timestamp': datetime.now().isoformat(),
        'source': 'test-endpoint'
    }
    
    # Diffuser à tous les clients connectés
    streaming_manager._broadcast_to_clients(json.dumps(sse_message))
    
    return jsonify({
        'message': 'Test data broadcasted to streaming clients',
        'data': test_data,
        'clients_notified': len(streaming_manager.clients),
        'backend': 'redpanda'
    })

if __name__ == "__main__":
    logger.info("🌐 Démarrage Serveur de Streaming CryptoViz avec Redpanda...")
    
    # Attendre que Redpanda soit disponible
    logger.info("⏳ Attente de la disponibilité Redpanda...")
    time.sleep(15)
    
    # Démarrer le streaming manager
    if streaming_manager.start():
        logger.info("✅ Redpanda Streaming Manager initialisé")
    else:
        logger.error("❌ Échec initialisation Redpanda Streaming Manager")
    
    logger.info("🚀 Serveur prêt sur http://0.0.0.0:5000")
    logger.info("📡 Endpoints disponibles:")
    logger.info("   • /stream - Streaming SSE")
    logger.info("   • /stats - Statistiques")
    logger.info("   • /health - Health check")
    logger.info("   • /test - Test manuel")
    logger.info("🔧 Backend: Redpanda")
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
