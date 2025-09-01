from flask import Flask, Response, jsonify
from flask_cors import CORS
import redis
import json
import time
import logging
import threading
from datetime import datetime
import queue

# Configuration
app = Flask(__name__)
CORS(app)  # Permettre les requêtes cross-origin depuis le dashboard
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis connection
redis_client = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

# Stats globales du streaming
streaming_stats = {
    'connected_clients': 0,
    'messages_sent': 0,
    'uptime': datetime.now(),
    'last_data_received': None,
    'redis_status': 'disconnected'
}

class StreamingManager:
    """Gestionnaire centralisé du streaming"""
    
    def __init__(self):
        self.clients = {}  # Dict des clients connectés
        self.running = False
        self.pubsub = None
        self.redis_thread = None
        
    def start(self):
        """Démarre le gestionnaire de streaming"""
        if self.running:
            logger.info("⚠️ Streaming Manager déjà démarré")
            return
            
        self.running = True
        
        try:
            # Test de connexion Redis
            redis_client.ping()
            streaming_stats['redis_status'] = 'connected'
            logger.info("✅ Connexion Redis établie")
        except Exception as e:
            logger.error(f"❌ Erreur connexion Redis: {e}")
            streaming_stats['redis_status'] = 'error'
            return False
        
        # Configurer Redis Pub/Sub
        self.pubsub = redis_client.pubsub()
        self.pubsub.subscribe('crypto_updates')
        logger.info("📡 Abonnement à Redis 'crypto_updates'")
        
        # Démarrer le thread d'écoute Redis
        self.redis_thread = threading.Thread(target=self._listen_redis, daemon=True)
        self.redis_thread.start()
        
        logger.info("🚀 Streaming Manager démarré avec succès")
        return True
    
    def _listen_redis(self):
        """Écoute les messages Redis et les diffuse aux clients"""
        logger.info("👂 Démarrage écoute Redis Pub/Sub...")
        
        try:
            for message in self.pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    data = message['data']
                    streaming_stats['last_data_received'] = datetime.now()
                    
                    try:
                        # Parser pour obtenir le nom de la crypto
                        crypto_data = json.loads(data)
                        crypto_name = crypto_data.get('name', 'Unknown')
                        
                        logger.info(f"📡 Nouvelle donnée: {crypto_name} - Diffusion à {len(self.clients)} clients")
                        
                        # Préparer le message pour SSE
                        sse_message = {
                            'type': 'crypto_update',
                            'data': crypto_data,
                            'timestamp': datetime.now().isoformat()
                        }
                        
                        # Diffuser à tous les clients connectés
                        self._broadcast_to_clients(json.dumps(sse_message))
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Erreur parsing JSON: {e}")
                    except Exception as e:
                        logger.error(f"❌ Erreur traitement message: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Erreur Redis listen: {e}")
            streaming_stats['redis_status'] = 'error'
    
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
            'message': 'Streaming CryptoViz connecté',
            'client_id': client_id,
            'timestamp': datetime.now().isoformat()
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
streaming_manager = StreamingManager()

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
                        'stats': {
                            'connected_clients': streaming_stats['connected_clients'],
                            'messages_sent': streaming_stats['messages_sent'],
                            'redis_status': streaming_stats['redis_status']
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
    
    if current_stats['last_data_received']:
        current_stats['last_data_received'] = current_stats['last_data_received'].isoformat()
    
    return jsonify(current_stats)

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test Redis
        redis_client.ping()
        redis_status = 'ok'
    except:
        redis_status = 'error'
    
    health_status = {
        'status': 'healthy' if redis_status == 'ok' else 'unhealthy',
        'redis': redis_status,
        'streaming': 'active' if streaming_manager.running else 'inactive',
        'clients': len(streaming_manager.clients) if streaming_manager.clients else 0,
        'timestamp': datetime.now().isoformat()
    }
    
    return jsonify(health_status), 200 if redis_status == 'ok' else 500

@app.route('/test')
def test():
    """Endpoint de test pour déclencher une donnée factice"""
    test_data = {
        'name': 'TestCoin',
        'symbol': 'TEST',
        'price': 42.42,
        'percent_change_24h': 1.23,
        'market_cap': 1000000,
        'source': 'test',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Publier sur Redis
    redis_client.publish('crypto_updates', json.dumps(test_data))
    
    return jsonify({
        'message': 'Test data published',
        'data': test_data
    })

if __name__ == "__main__":
    logger.info("🌐 Démarrage Serveur de Streaming CryptoViz...")
    
    # Démarrer le streaming manager
    if streaming_manager.start():
        logger.info("✅ Streaming Manager initialisé")
    else:
        logger.error("❌ Échec initialisation Streaming Manager")
    
    logger.info("🚀 Serveur prêt sur http://0.0.0.0:5000")
    logger.info("📡 Endpoints disponibles:")
    logger.info("   • /stream - Streaming SSE")
    logger.info("   • /stats - Statistiques")
    logger.info("   • /health - Health check")
    logger.info("   • /test - Test manuel")
    
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)