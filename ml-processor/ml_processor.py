"""
ML Processor - Architecture standard pour prédictions temps réel
Consomme Kafka → Calcule ML → Stocke Redis → Dashboard consomme Redis

Architecture: Kafka → ML Processor → Redis → Streamlit (ultra-rapide)
"""
import json
import os
import time
import redis
import pandas as pd
import numpy as np
from kafka import KafkaConsumer
from datetime import datetime, timedelta
from collections import deque
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MLModels:
    """Modèles ML légers pour calcul temps réel"""
    
    @staticmethod
    def moving_average(prices, window=20):
        """Moyenne mobile"""
        if len(prices) < window:
            return prices[-1] if prices else 0
        return np.mean(prices[-window:])
    
    @staticmethod 
    def linear_trend(prices, timestamps, steps=1):
        """Tendance linéaire"""
        if len(prices) < 2:
            return [prices[-1] if prices else 0] * steps
        
        # Régression linéaire simple
        x = np.arange(len(prices))
        coeffs = np.polyfit(x, prices, 1)
        
        predictions = []
        for i in range(1, steps + 1):
            next_pred = coeffs[0] * (len(prices) + i) + coeffs[1]
            predictions.append(max(0, next_pred))
        
        return predictions
    
    @staticmethod
    def momentum(prices, window=10, steps=1):
        """Prédiction par momentum"""
        if len(prices) < window:
            return [prices[-1] if prices else 0] * steps
        
        recent = prices[-window:]
        changes = np.diff(recent)
        avg_change = np.mean(changes)
        
        predictions = []
        current = prices[-1]
        
        for i in range(steps):
            # Momentum décroissant
            momentum_effect = avg_change * (0.8 ** i)
            current += momentum_effect
            predictions.append(max(0, current))
        
        return predictions

class CryptoMLProcessor:
    """Processeur ML temps réel - Architecture standard"""
    
    def __init__(self):
        # Redis pour stockage haute performance
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True
        )
        
        # Consumer Kafka
        self.consumer = KafkaConsumer(
            'crypto-raw-data',
            bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:9092')],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='ml-processor-group'
        )
        
        # Buffers en mémoire pour chaque crypto
        self.crypto_buffers = {}
        self.buffer_size = 100  # Garder 100 derniers points par crypto
        
        logger.info("✅ ML Processor initialisé")
        logger.info(f"Redis: {os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}")
        logger.info(f"Kafka: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:9092')}")
    
    def test_connections(self):
        """Test des connexions Redis et Kafka"""
        try:
            # Test Redis
            self.redis_client.ping()
            logger.info("✅ Redis connection OK")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
        
        try:
            # Test Kafka (déjà fait dans __init__)
            logger.info("✅ Kafka consumer OK")
            return True
        except Exception as e:
            logger.error(f"❌ Kafka connection failed: {e}")
            return False
    
    def add_to_buffer(self, symbol, price, timestamp):
        """Ajoute un point de données au buffer crypto"""
        if symbol not in self.crypto_buffers:
            self.crypto_buffers[symbol] = {
                'prices': deque(maxlen=self.buffer_size),
                'timestamps': deque(maxlen=self.buffer_size),
                'last_update': time.time()
            }
        
        buffer = self.crypto_buffers[symbol]
        buffer['prices'].append(float(price))
        buffer['timestamps'].append(timestamp)
        buffer['last_update'] = time.time()
    
    def calculate_predictions(self, symbol):
        """Calcule les prédictions ML pour une crypto"""
        if symbol not in self.crypto_buffers:
            return None
        
        buffer = self.crypto_buffers[symbol]
        prices = list(buffer['prices'])
        timestamps = list(buffer['timestamps'])
        
        if len(prices) < 10:  # Minimum de données requis
            return None
        
        try:
            # Calcul des prédictions avec les différents modèles
            current_price = prices[-1]
            
            predictions = {
                'symbol': symbol,
                'current_price': current_price,
                'last_update': datetime.now().isoformat(),
                'predictions': {
                    'moving_average_1h': MLModels.moving_average(prices, 20),
                    'moving_average_6h': [MLModels.moving_average(prices, 20)] * 6,
                    'linear_trend_1h': MLModels.linear_trend(prices, timestamps, 1)[0],
                    'linear_trend_6h': MLModels.linear_trend(prices, timestamps, 6),
                    'momentum_1h': MLModels.momentum(prices, 10, 1)[0],
                    'momentum_6h': MLModels.momentum(prices, 10, 6)
                },
                'confidence': {
                    'moving_average': 0.6,
                    'linear_trend': 0.7,
                    'momentum': 0.5
                },
                'signals': {}
            }
            
            # Signaux de trading
            ma_pred = predictions['predictions']['moving_average_1h']
            change_pct = ((ma_pred - current_price) / current_price) * 100
            
            if change_pct > 2:
                predictions['signals']['trading'] = 'BUY'
                predictions['signals']['strength'] = 'HIGH'
            elif change_pct < -2:
                predictions['signals']['trading'] = 'SELL'
                predictions['signals']['strength'] = 'HIGH'
            else:
                predictions['signals']['trading'] = 'HOLD'
                predictions['signals']['strength'] = 'MEDIUM'
            
            predictions['signals']['change_pct'] = change_pct
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul prédictions {symbol}: {e}")
            return None
    
    def store_predictions(self, predictions):
        """Stocke les prédictions dans Redis avec TTL"""
        try:
            symbol = predictions['symbol']
            
            # Stockage avec TTL de 5 minutes
            key = f"ml:predictions:{symbol}"
            self.redis_client.setex(
                key, 
                300,  # TTL 5 minutes
                json.dumps(predictions)
            )
            
            # Mettre à jour la liste des cryptos disponibles
            self.redis_client.sadd("ml:available_cryptos", symbol)
            self.redis_client.expire("ml:available_cryptos", 600)  # TTL 10 minutes
            
            logger.info(f"💾 Prédictions {symbol} stockées (prix: {predictions['current_price']:.2f})")
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage Redis {symbol}: {e}")
    
    def process_message(self, message):
        """Traite un message Kafka"""
        try:
            data = message.value
            
            # Extraire les données
            symbol = data.get('symbol')
            price = data.get('price')
            timestamp = data.get('timestamp')
            
            if not all([symbol, price, timestamp]):
                return
            
            # Ajouter au buffer
            self.add_to_buffer(symbol, price, timestamp)
            
            # Calculer et stocker les prédictions
            predictions = self.calculate_predictions(symbol)
            if predictions:
                self.store_predictions(predictions)
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
    
    def run(self):
        """Boucle principale de traitement"""
        logger.info("🚀 Démarrage ML Processor...")
        
        if not self.test_connections():
            logger.error("❌ Connexions échouées")
            return
        
        message_count = 0
        start_time = time.time()
        
        try:
            for message in self.consumer:
                self.process_message(message)
                message_count += 1
                
                # Statistiques toutes les 100 messages
                if message_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = message_count / elapsed
                    logger.info(f"📊 Messages traités: {message_count}, Rate: {rate:.1f}/s")
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt ML Processor")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
        finally:
            self.consumer.close()

if __name__ == "__main__":
    processor = CryptoMLProcessor()
    processor.run()
