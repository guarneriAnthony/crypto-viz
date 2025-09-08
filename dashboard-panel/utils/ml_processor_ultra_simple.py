"""
ML Processor ULTRA Simplifié (sans WebSocket)
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
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedMLModels:
    """Modèles ML avancés avec ensemble learning"""
    
    @staticmethod
    def weighted_moving_average(prices: List[float], weights: List[float] = None) -> float:
        if len(prices) < 2:
            return prices[-1] if prices else 0
        
        if weights is None:
            weights = [0.5 ** i for i in range(len(prices))]
            weights.reverse()
        
        weights = weights[-len(prices):]
        weighted_sum = sum(p * w for p, w in zip(prices, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else prices[-1]
    
    @staticmethod
    def polynomial_regression(prices: List[float], degree: int = 2, steps: int = 1) -> List[float]:
        if len(prices) < degree + 1:
            return [prices[-1] if prices else 0] * steps
        
        x = np.arange(len(prices))
        try:
            coeffs = np.polyfit(x, prices, degree)
            predictions = []
            
            for i in range(1, steps + 1):
                next_x = len(prices) + i
                pred = sum(coeff * (next_x ** (degree - idx)) 
                          for idx, coeff in enumerate(coeffs))
                predictions.append(max(0, pred))
            
            return predictions
        except:
            return [prices[-1]] * steps
    
    @staticmethod
    def ensemble_prediction(prices: List[float]) -> Dict:
        if len(prices) < 10:
            return {'prediction': prices[-1] if prices else 0, 'confidence': 0.3}
        
        current = prices[-1]
        predictions = []
        confidences = []
        
        # Moyenne mobile pondérée
        wma_pred = AdvancedMLModels.weighted_moving_average(prices)
        predictions.append(wma_pred)
        confidences.append(0.7)
        
        # Régression polynomiale
        poly_pred = AdvancedMLModels.polynomial_regression(prices, degree=2, steps=1)[0]
        predictions.append(poly_pred)
        confidences.append(0.6)
        
        # Prédiction pondérée
        total_weight = sum(confidences)
        ensemble_pred = sum(p * c for p, c in zip(predictions, confidences)) / total_weight
        
        # Signal
        change_pct = ((ensemble_pred - current) / current) * 100
        
        if change_pct > 3:
            signal = 'STRONG_BUY'
        elif change_pct > 1:
            signal = 'BUY'
        elif change_pct < -3:
            signal = 'STRONG_SELL'
        elif change_pct < -1:
            signal = 'SELL'
        else:
            signal = 'HOLD'
        
        return {
            'prediction': ensemble_pred,
            'confidence': np.mean(confidences),
            'signal': signal,
            'change_pct': change_pct,
            'individual_predictions': {
                'weighted_ma': wma_pred,
                'polynomial': poly_pred
            }
        }

class CryptoMLProcessorUltraSimple:
    """Processeur ML Ultra Simplifié"""
    
    def __init__(self):
        # Redis
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_connect_timeout=5
        )
        
        # Kafka Consumer
        self.consumer = KafkaConsumer(
            'crypto-raw-data',
            bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:9092')],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='ml-ultra-processor-simple'
        )
        
        # Buffers
        self.crypto_buffers = {}
        self.buffer_size = 100
        
        # Métriques
        self.metrics = {
            'processed_messages': 0,
            'predictions_generated': 0,
            'start_time': time.time()
        }
        
        logger.info("🚀 ML Processor ULTRA Simple initialisé")
    
    def add_to_buffer(self, symbol: str, price: float, timestamp: str, volume: float = None):
        if symbol not in self.crypto_buffers:
            self.crypto_buffers[symbol] = {
                'prices': deque(maxlen=self.buffer_size),
                'timestamps': deque(maxlen=self.buffer_size),
                'volumes': deque(maxlen=self.buffer_size)
            }
        
        buffer = self.crypto_buffers[symbol]
        buffer['prices'].append(float(price))
        buffer['timestamps'].append(timestamp)
        buffer['volumes'].append(float(volume or 0))
    
    def calculate_predictions(self, symbol: str) -> Optional[Dict]:
        if symbol not in self.crypto_buffers:
            return None
        
        buffer = self.crypto_buffers[symbol]
        prices = list(buffer['prices'])
        
        if len(prices) < 20:
            return None
        
        try:
            current_price = prices[-1]
            current_time = datetime.now().isoformat()
            
            # Prédictions ensemble
            ensemble_result = AdvancedMLModels.ensemble_prediction(prices)
            
            # Volatilité
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns[-20:]) * 100
            
            predictions = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': current_time,
                'ensemble_prediction': {
                    'value': ensemble_result['prediction'],
                    'confidence': ensemble_result['confidence'],
                    'signal': ensemble_result['signal'],
                    'change_pct': ensemble_result['change_pct']
                },
                'technical_indicators': {
                    'volatility': volatility,
                    'support': min(prices[-50:]) if len(prices) >= 50 else min(prices),
                    'resistance': max(prices[-50:]) if len(prices) >= 50 else max(prices)
                },
                'individual_models': ensemble_result.get('individual_predictions', {}),
                'performance_metrics': {
                    'data_points': len(prices),
                    'last_update': current_time
                }
            }
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul prédictions {symbol}: {e}")
            return None
    
    def store_predictions(self, predictions: Dict):
        try:
            symbol = predictions['symbol']
            timestamp = datetime.now()
            
            # Stockage principal
            main_key = f"ml:ultra:predictions:{symbol}"
            self.redis_client.setex(main_key, 300, json.dumps(predictions))
            
            # Index des cryptos disponibles
            self.redis_client.sadd("ml:ultra:available_cryptos", symbol)
            self.redis_client.expire("ml:ultra:available_cryptos", 600)
            
            # Métriques globales
            perf_key = "ml:ultra:performance"
            perf_data = {
                'total_predictions': self.metrics['predictions_generated'],
                'total_messages': self.metrics['processed_messages'],
                'uptime_seconds': time.time() - self.metrics['start_time'],
                'last_update': timestamp.isoformat()
            }
            self.redis_client.setex(perf_key, 300, json.dumps(perf_data))
            
            self.metrics['predictions_generated'] += 1
            
            # Log
            change_pct = predictions['ensemble_prediction']['change_pct']
            color = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "🟡"
            logger.info(f"{color} {symbol}: ${predictions['current_price']:.4f} → "
                       f"${predictions['ensemble_prediction']['value']:.4f} "
                       f"({change_pct:+.2f}%) [{predictions['ensemble_prediction']['signal']}]")
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage Redis {symbol}: {e}")
    
    def process_message(self, message):
        try:
            data = message.value
            
            symbol = data.get('symbol')
            price = data.get('price')
            timestamp = data.get('timestamp')
            volume = data.get('volume')
            
            if not all([symbol, price, timestamp]):
                return
            
            # Ajouter au buffer
            self.add_to_buffer(symbol, price, timestamp, volume)
            
            # Calculer et stocker les prédictions
            predictions = self.calculate_predictions(symbol)
            if predictions:
                self.store_predictions(predictions)
            
            self.metrics['processed_messages'] += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
    
    def run(self):
        logger.info("🎯 Démarrage ML Processor ULTRA Simple...")
        
        # Test Redis
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connecté")
        except Exception as e:
            logger.error(f"❌ Redis: {e}")
            return
        
        try:
            # Boucle principale
            for message in self.consumer:
                self.process_message(message)
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt gracieux ML Processor ULTRA Simple")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
        finally:
            self.consumer.close()
            logger.info("👋 ML Processor ULTRA Simple arrêté")

if __name__ == "__main__":
    processor = CryptoMLProcessorUltraSimple()
    processor.run()
