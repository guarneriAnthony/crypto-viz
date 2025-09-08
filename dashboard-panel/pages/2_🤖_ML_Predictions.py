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
import asyncio
import websockets
from threading import Thread
import warnings
warnings.filterwarnings('ignore')

# Configuration des logs avec style
class ColoredFormatter(logging.Formatter):
    """Formatter coloré pour les logs"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Vert  
        'WARNING': '\033[33m',  # Jaune
        'ERROR': '\033[31m',    # Rouge
        'CRITICAL': '\033[35m', # Magenta
        'ENDC': '\033[0m'       # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['ENDC'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['ENDC']}"
        return super().format(record)

# Setup logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AdvancedMLModels:
    """Modèles ML avancés avec ensemble learning et détection d'anomalies"""
    
    @staticmethod
    def weighted_moving_average(prices: List[float], weights: List[float] = None) -> float:
        """Moyenne mobile pondérée avec poids exponentiels"""
        if len(prices) < 2:
            return prices[-1] if prices else 0
        
        if weights is None:
            # Poids exponentiels (plus de poids aux valeurs récentes)
            weights = [0.5 ** i for i in range(len(prices))]
            weights.reverse()
        
        weights = weights[-len(prices):]
        weighted_sum = sum(p * w for p, w in zip(prices, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else prices[-1]
    
    @staticmethod
    def polynomial_regression(prices: List[float], degree: int = 2, steps: int = 1) -> List[float]:
        """Régression polynomiale pour prédictions non-linéaires"""
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
    def bollinger_bands_prediction(prices: List[float], window: int = 20) -> Dict:
        """Prédiction basée sur les bandes de Bollinger"""
        if len(prices) < window:
            return {'prediction': prices[-1] if prices else 0, 'signal': 'HOLD', 'confidence': 0.5}
        
        recent_prices = prices[-window:]
        mean = np.mean(recent_prices)
        std = np.std(recent_prices)
        current = prices[-1]
        
        upper_band = mean + (2 * std)
        lower_band = mean - (2 * std)
        
        # Prédiction basée sur la position dans les bandes
        if current <= lower_band:
            prediction = mean  # Retour vers la moyenne
            signal = 'BUY'
            confidence = min(0.9, (mean - current) / mean * 2)
        elif current >= upper_band:
            prediction = mean  # Retour vers la moyenne
            signal = 'SELL'
            confidence = min(0.9, (current - mean) / mean * 2)
        else:
            prediction = current + (mean - current) * 0.1  # Légère convergence
            signal = 'HOLD'
            confidence = 0.6
        
        return {
            'prediction': prediction,
            'signal': signal,
            'confidence': confidence,
            'bands': {'upper': upper_band, 'middle': mean, 'lower': lower_band}
        }
    
    @staticmethod
    def rsi_momentum_prediction(prices: List[float], window: int = 14) -> Dict:
        """Prédiction basée sur RSI (Relative Strength Index)"""
        if len(prices) < window + 1:
            return {'prediction': prices[-1] if prices else 0, 'rsi': 50, 'signal': 'HOLD'}
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-window:])
        avg_loss = np.mean(losses[-window:])
        
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        current = prices[-1]
        
        # Prédiction basée sur RSI
        if rsi < 30:  # Survente
            prediction = current * 1.02  # +2%
            signal = 'STRONG_BUY'
        elif rsi > 70:  # Surachat
            prediction = current * 0.98  # -2%
            signal = 'STRONG_SELL'
        elif rsi < 40:
            prediction = current * 1.01
            signal = 'BUY'
        elif rsi > 60:
            prediction = current * 0.99
            signal = 'SELL'
        else:
            prediction = current
            signal = 'HOLD'
        
        return {
            'prediction': prediction,
            'rsi': rsi,
            'signal': signal,
            'confidence': abs(50 - rsi) / 50  # Plus loin de 50 = plus confiant
        }
    
    @staticmethod
    def ensemble_prediction(prices: List[float], timestamps: List = None) -> Dict:
        """Prédiction d'ensemble combinant plusieurs modèles"""
        if len(prices) < 10:
            return {'prediction': prices[-1] if prices else 0, 'confidence': 0.3}
        
        current = prices[-1]
        predictions = []
        confidences = []
        
        # 1. Moyenne mobile pondérée
        wma_pred = AdvancedMLModels.weighted_moving_average(prices)
        predictions.append(wma_pred)
        confidences.append(0.7)
        
        # 2. Régression polynomiale
        poly_pred = AdvancedMLModels.polynomial_regression(prices, degree=2, steps=1)[0]
        predictions.append(poly_pred)
        confidences.append(0.6)
        
        # 3. Bandes de Bollinger
        bb_result = AdvancedMLModels.bollinger_bands_prediction(prices)
        predictions.append(bb_result['prediction'])
        confidences.append(bb_result['confidence'])
        
        # 4. RSI Momentum
        rsi_result = AdvancedMLModels.rsi_momentum_prediction(prices)
        predictions.append(rsi_result['prediction'])
        confidences.append(rsi_result['confidence'])
        
        # Prédiction pondérée par les confidences
        total_weight = sum(confidences)
        ensemble_pred = sum(p * c for p, c in zip(predictions, confidences)) / total_weight
        
        # Calcul du signal global
        change_pct = ((ensemble_pred - current) / current) * 100
        
        if change_pct > 3:
            signal = 'STRONG_BUY'
            strength = 'VERY_HIGH'
        elif change_pct > 1:
            signal = 'BUY'
            strength = 'HIGH'
        elif change_pct < -3:
            signal = 'STRONG_SELL'
            strength = 'VERY_HIGH'
        elif change_pct < -1:
            signal = 'SELL'
            strength = 'HIGH'
        else:
            signal = 'HOLD'
            strength = 'MEDIUM'
        
        return {
            'prediction': ensemble_pred,
            'confidence': np.mean(confidences),
            'signal': signal,
            'strength': strength,
            'change_pct': change_pct,
            'individual_predictions': {
                'weighted_ma': wma_pred,
                'polynomial': poly_pred,
                'bollinger': bb_result['prediction'],
                'rsi_momentum': rsi_result['prediction']
            },
            'bollinger_bands': bb_result.get('bands', {}),
            'rsi': rsi_result.get('rsi', 50)
        }

class AnomalyDetector:
    """Détecteur d'anomalies et événements de marché"""
    
    @staticmethod
    def detect_price_anomalies(prices: List[float], threshold: float = 3.0) -> Dict:
        """Détecte les anomalies de prix avec Z-score"""
        if len(prices) < 20:
            return {'is_anomaly': False, 'score': 0, 'type': 'normal'}
        
        recent = prices[-20:]
        mean = np.mean(recent[:-1])  # Exclure le dernier point
        std = np.std(recent[:-1])
        current = prices[-1]
        
        if std == 0:
            return {'is_anomaly': False, 'score': 0, 'type': 'normal'}
        
        z_score = abs((current - mean) / std)
        
        if z_score > threshold:
            anomaly_type = 'spike_up' if current > mean else 'spike_down'
            return {
                'is_anomaly': True,
                'score': z_score,
                'type': anomaly_type,
                'severity': 'critical' if z_score > 4 else 'high'
            }
        
        return {'is_anomaly': False, 'score': z_score, 'type': 'normal'}
    
    @staticmethod
    def detect_volume_anomalies(volumes: List[float]) -> Dict:
        """Détecte les anomalies de volume"""
        if len(volumes) < 10:
            return {'is_anomaly': False, 'type': 'normal'}
        
        recent_avg = np.mean(volumes[-10:-1])
        current = volumes[-1]
        
        if current > recent_avg * 3:
            return {'is_anomaly': True, 'type': 'volume_surge', 'ratio': current / recent_avg}
        elif current < recent_avg * 0.3:
            return {'is_anomaly': True, 'type': 'volume_drop', 'ratio': current / recent_avg}
        
        return {'is_anomaly': False, 'type': 'normal', 'ratio': current / recent_avg}

class CryptoMLProcessorUltra:
    """Processeur ML Ultra avec fonctionnalités avancées"""
    
    def __init__(self):
        # Configuration Redis avec optimisations
        self.redis_client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            max_connections=20
        )
        
        # Consumer Kafka optimisé
        self.consumer = KafkaConsumer(
            'crypto-raw-data',
            bootstrap_servers=[os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:9092')],
            value_deserializer=lambda x: json.loads(x.decode('utf-8')),
            auto_offset_reset='latest',
            group_id='ml-ultra-processor',
            fetch_max_wait_ms=1000,
            fetch_min_bytes=1024,
            max_poll_records=100
        )
        
        # Buffers étendus pour analyses complexes
        self.crypto_buffers = {}
        self.buffer_size = 200  # Plus de données historiques
        self.anomaly_detector = AnomalyDetector()
        
        # Métriques de performance
        self.metrics = {
            'processed_messages': 0,
            'predictions_generated': 0,
            'anomalies_detected': 0,
            'start_time': time.time(),
            'last_performance_log': time.time()
        }
        
        # WebSocket pour notifications temps réel
        self.websocket_clients = set()
        self.websocket_server = None
        
        logger.info("🚀 ML Processor ULTRA initialisé")
        self._log_startup_info()
    
    def _log_startup_info(self):
        """Log des informations de démarrage avec style"""
        logger.info("=" * 60)
        logger.info(" CRYPTO ML PROCESSOR ULTRA")
        logger.info("=" * 60)
        logger.info(f" Redis: {os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', 6379)}")
        logger.info(f" Kafka: {os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'redpanda:9092')}")
        logger.info(f" Modèles: Ensemble, Bollinger, RSI, Anomalies")
        logger.info(f" Buffer: {self.buffer_size} points par crypto")
        logger.info("=" * 60)
    
    async def websocket_handler(self, websocket, path):
        """Gestionnaire WebSocket pour notifications temps réel"""
        self.websocket_clients.add(websocket)
        logger.info(f" Nouveau client WebSocket connecté ({len(self.websocket_clients)} total)")
        
        try:
            await websocket.wait_closed()
        finally:
            self.websocket_clients.remove(websocket)
    
    async def broadcast_alert(self, alert_data):
        """Diffuse une alerte à tous les clients WebSocket"""
        if self.websocket_clients:
            message = json.dumps(alert_data)
            await asyncio.gather(
                *[client.send(message) for client in self.websocket_clients],
                return_exceptions=True
            )
    
    def start_websocket_server(self):
        """Démarre le serveur WebSocket en arrière-plan"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            start_server = websockets.serve(
                self.websocket_handler, 
                "0.0.0.0", 
                8765
            )
            
            loop.run_until_complete(start_server)
            loop.run_forever()
        
        websocket_thread = Thread(target=run_server, daemon=True)
        websocket_thread.start()
        logger.info(" Serveur WebSocket démarré sur port 8765")
    
    def add_to_buffer(self, symbol: str, price: float, timestamp: str, volume: float = None):
        """Ajoute des données enrichies au buffer"""
        if symbol not in self.crypto_buffers:
            self.crypto_buffers[symbol] = {
                'prices': deque(maxlen=self.buffer_size),
                'timestamps': deque(maxlen=self.buffer_size),
                'volumes': deque(maxlen=self.buffer_size),
                'last_update': time.time(),
                'total_updates': 0,
                'last_anomaly': None
            }
        
        buffer = self.crypto_buffers[symbol]
        buffer['prices'].append(float(price))
        buffer['timestamps'].append(timestamp)
        buffer['volumes'].append(float(volume or 0))
        buffer['last_update'] = time.time()
        buffer['total_updates'] += 1
    
    def calculate_advanced_predictions(self, symbol: str) -> Optional[Dict]:
        """Calcule des prédictions avancées avec ensemble learning"""
        if symbol not in self.crypto_buffers:
            return None
        
        buffer = self.crypto_buffers[symbol]
        prices = list(buffer['prices'])
        volumes = list(buffer['volumes'])
        timestamps = list(buffer['timestamps'])
        
        if len(prices) < 20:
            return None
        
        try:
            current_price = prices[-1]
            current_time = datetime.now().isoformat()
            
            # 1. Prédictions ensemble
            ensemble_result = AdvancedMLModels.ensemble_prediction(prices, timestamps)
            
            # 2. Détection d'anomalies
            price_anomaly = self.anomaly_detector.detect_price_anomalies(prices)
            volume_anomaly = self.anomaly_detector.detect_volume_anomalies(volumes) if volumes else {'is_anomaly': False}
            
            # 3. Prédictions multi-horizon
            short_term = AdvancedMLModels.polynomial_regression(prices, degree=1, steps=1)[0]  # 1 étape
            medium_term = AdvancedMLModels.polynomial_regression(prices, degree=2, steps=6)      # 6 étapes
            long_term = AdvancedMLModels.polynomial_regression(prices, degree=3, steps=24)       # 24 étapes
            
            # 4. Calcul de volatilité
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns[-20:]) * 100  # Dernières 20 valeurs en %
            
            # 5. Support et résistance
            recent_prices = prices[-50:] if len(prices) >= 50 else prices
            resistance = max(recent_prices)
            support = min(recent_prices)
            
            predictions = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': current_time,
                'ensemble_prediction': {
                    'value': ensemble_result['prediction'],
                    'confidence': ensemble_result['confidence'],
                    'signal': ensemble_result['signal'],
                    'strength': ensemble_result['strength'],
                    'change_pct': ensemble_result['change_pct']
                },
                'multi_horizon': {
                    'short_term_1h': short_term,
                    'medium_term_6h': medium_term,
                    'long_term_24h': long_term
                },
                'technical_indicators': {
                    'bollinger_bands': ensemble_result.get('bollinger_bands', {}),
                    'rsi': ensemble_result.get('rsi', 50),
                    'volatility': volatility,
                    'support': support,
                    'resistance': resistance
                },
                'anomalies': {
                    'price': price_anomaly,
                    'volume': volume_anomaly
                },
                'individual_models': ensemble_result.get('individual_predictions', {}),
                'performance_metrics': {
                    'data_points': len(prices),
                    'last_update': current_time,
                    'processing_time': time.time() - buffer['last_update']
                }
            }
            
            # Générer des alertes si nécessaire
            await self._check_and_send_alerts(predictions)
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul prédictions {symbol}: {e}")
            return None
    
    async def _check_and_send_alerts(self, predictions: Dict):
        """Vérifie et envoie des alertes basées sur les prédictions"""
        symbol = predictions['symbol']
        ensemble = predictions['ensemble_prediction']
        anomalies = predictions['anomalies']
        
        alerts = []
        
        # Alerte signal fort
        if ensemble['strength'] in ['HIGH', 'VERY_HIGH']:
            alerts.append({
                'type': 'trading_signal',
                'symbol': symbol,
                'signal': ensemble['signal'],
                'confidence': ensemble['confidence'],
                'change_pct': ensemble['change_pct'],
                'timestamp': predictions['timestamp']
            })
        
        # Alerte anomalie
        if anomalies['price']['is_anomaly']:
            alerts.append({
                'type': 'price_anomaly',
                'symbol': symbol,
                'anomaly_type': anomalies['price']['type'],
                'severity': anomalies['price'].get('severity', 'medium'),
                'score': anomalies['price']['score'],
                'timestamp': predictions['timestamp']
            })
        
        # Envoyer les alertes
        for alert in alerts:
            await self.broadcast_alert(alert)
            self.metrics['anomalies_detected'] += 1
    
    def store_advanced_predictions(self, predictions: Dict):
        """Stocke les prédictions avancées avec indexation optimisée"""
        try:
            symbol = predictions['symbol']
            timestamp = datetime.now()
            
            # Stockage principal avec TTL
            main_key = f"ml:ultra:predictions:{symbol}"
            self.redis_client.setex(main_key, 300, json.dumps(predictions))
            
            # Index par signal de trading
            signal = predictions['ensemble_prediction']['signal']
            signal_key = f"ml:ultra:signals:{signal}"
            self.redis_client.sadd(signal_key, symbol)
            self.redis_client.expire(signal_key, 300)
            
            # Historique des prédictions (garder 24h)
            history_key = f"ml:ultra:history:{symbol}"
            history_entry = {
                'timestamp': timestamp.isoformat(),
                'prediction': predictions['ensemble_prediction']['value'],
                'actual': predictions['current_price'],
                'confidence': predictions['ensemble_prediction']['confidence']
            }
            self.redis_client.lpush(history_key, json.dumps(history_entry))
            self.redis_client.ltrim(history_key, 0, 144)  # Garder 144 entrées (24h à 10min)
            self.redis_client.expire(history_key, 86400)
            
            # Métadonnées globales
            self.redis_client.sadd("ml:ultra:available_cryptos", symbol)
            self.redis_client.expire("ml:ultra:available_cryptos", 600)
            
            # Métriques de performance
            perf_key = "ml:ultra:performance"
            perf_data = {
                'total_predictions': self.metrics['predictions_generated'],
                'total_messages': self.metrics['processed_messages'],
                'anomalies_detected': self.metrics['anomalies_detected'],
                'uptime_seconds': time.time() - self.metrics['start_time'],
                'last_update': timestamp.isoformat()
            }
            self.redis_client.setex(perf_key, 300, json.dumps(perf_data))
            
            self.metrics['predictions_generated'] += 1
            
            # Log avec couleurs
            change_pct = predictions['ensemble_prediction']['change_pct']
            color = "🟢" if change_pct > 0 else "🔴" if change_pct < 0 else "🟡"
            logger.info(f"{color} {symbol}: ${predictions['current_price']:.4f} → "
                       f"${predictions['ensemble_prediction']['value']:.4f} "
                       f"({change_pct:+.2f}%) [{predictions['ensemble_prediction']['signal']}]")
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage Redis {symbol}: {e}")
    
    def log_performance(self):
        """Log des métriques de performance"""
        now = time.time()
        if now - self.metrics['last_performance_log'] >= 60:  # Toutes les minutes
            uptime = now - self.metrics['start_time']
            msg_rate = self.metrics['processed_messages'] / uptime
            pred_rate = self.metrics['predictions_generated'] / uptime
            
            logger.info("=" * 50)
            logger.info(" PERFORMANCE METRICS")
            logger.info(f"  Uptime: {uptime/3600:.1f}h")
            logger.info(f" Messages: {self.metrics['processed_messages']} ({msg_rate:.1f}/s)")
            logger.info(f" Prédictions: {self.metrics['predictions_generated']} ({pred_rate:.1f}/s)")
            logger.info(f" Anomalies: {self.metrics['anomalies_detected']}")
            logger.info(f" Cryptos actives: {len(self.crypto_buffers)}")
            logger.info("=" * 50)
            
            self.metrics['last_performance_log'] = now
    
    async def process_message_async(self, message):
        """Traite un message de façon asynchrone"""
        try:
            data = message.value
            
            # Extraire et valider les données
            symbol = data.get('symbol')
            price = data.get('price')
            timestamp = data.get('timestamp')
            volume = data.get('volume')
            
            if not all([symbol, price, timestamp]):
                return
            
            # Ajouter au buffer
            self.add_to_buffer(symbol, price, timestamp, volume)
            
            # Calculer et stocker les prédictions avancées
            predictions = self.calculate_advanced_predictions(symbol)
            if predictions:
                self.store_advanced_predictions(predictions)
            
            self.metrics['processed_messages'] += 1
            
        except Exception as e:
            logger.error(f"❌ Erreur traitement message: {e}")
    
    def run(self):
        """Boucle principale ultra-optimisée"""
        logger.info(" Démarrage ML Processor ULTRA...")
        
        # Démarrer le serveur WebSocket
        self.start_websocket_server()
        
        # Test des connexions
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connecté")
        except Exception as e:
            logger.error(f"❌ Redis: {e}")
            return
        
        try:
            # Boucle de traitement principal
            for message in self.consumer:
                # Traitement synchrone (plus simple pour Redis)
                asyncio.run(self.process_message_async(message))
                
                # Log de performance périodique
                self.log_performance()
                
        except KeyboardInterrupt:
            logger.info("🛑 Arrêt gracieux ML Processor ULTRA")
        except Exception as e:
            logger.error(f"❌ Erreur fatale: {e}")
        finally:
            self.consumer.close()
            logger.info(" ML Processor ULTRA arrêté")

if __name__ == "__main__":
    processor = CryptoMLProcessorUltra()
    processor.run()