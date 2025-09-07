"""
Client Redis pour prédictions ML - Architecture standard
Ultra-rapide: Redis → Dashboard (millisecondes vs minutes)
"""
import redis
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class RedisMLClient:
    """Client Redis pour accès ultra-rapide aux prédictions ML"""
    
    def __init__(self):
        self.client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
    
    def test_connection(self) -> bool:
        """Test rapide de connexion Redis"""
        try:
            return self.client.ping()
        except:
            return False
    
    def get_available_cryptos(self) -> List[str]:
        """Liste des cryptos avec prédictions ML disponibles"""
        try:
            cryptos = self.client.smembers("ml:available_cryptos")
            return list(cryptos) if cryptos else []
        except:
            return []
    
    def get_predictions(self, symbol: str) -> Optional[Dict]:
        """Récupère les prédictions ML pour une crypto"""
        try:
            key = f"ml:predictions:{symbol}"
            data = self.client.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Erreur récupération prédictions {symbol}: {e}")
            return None
    
    def get_all_predictions(self) -> Dict[str, Dict]:
        """Récupère toutes les prédictions ML disponibles"""
        try:
            cryptos = self.get_available_cryptos()
            predictions = {}
            
            for symbol in cryptos:
                pred = self.get_predictions(symbol)
                if pred:
                    predictions[symbol] = pred
            
            return predictions
        except Exception as e:
            print(f"Erreur récupération toutes prédictions: {e}")
            return {}
    
    def get_ml_stats(self) -> Dict:
        """Statistiques du système ML"""
        try:
            stats = {
                'connection': self.test_connection(),
                'available_cryptos': len(self.get_available_cryptos()),
                'last_update': datetime.now().isoformat(),
                'data_source': 'Redis (temps réel)'
            }
            return stats
        except:
            return {
                'connection': False,
                'available_cryptos': 0,
                'last_update': None,
                'data_source': 'Redis (indisponible)'
            }

# Fonctions compatibles avec l'ancienne API pour le dashboard
def get_crypto_predictions(symbol: str) -> Optional[Dict]:
    """API compatible: récupère prédictions pour une crypto"""
    client = RedisMLClient()
    return client.get_predictions(symbol)

def get_available_ml_cryptos() -> List[str]:
    """API compatible: liste des cryptos ML disponibles"""
    client = RedisMLClient()
    return client.get_available_cryptos()

def test_ml_connection() -> bool:
    """API compatible: test connexion ML"""
    client = RedisMLClient()
    return client.test_connection()

# Mapping des noms pour compatibilité
CRYPTO_NAME_MAPPING = {
    'Bitcoin': 'BTC',
    'Ethereum': 'ETH', 
    'Binance Coin': 'BNB',
    'Cardano': 'ADA',
    'Solana': 'SOL',
    'XRP': 'XRP',
    'Polkadot': 'DOT',
    'Dogecoin': 'DOGE',
    'Avalanche': 'AVAX',
    'Shiba Inu': 'SHIB',
    'Polygon': 'MATIC',
    'Litecoin': 'LTC'
}

def normalize_crypto_name(name: str) -> str:
    """Convertit nom crypto vers symbol"""
    return CRYPTO_NAME_MAPPING.get(name, name.upper())
