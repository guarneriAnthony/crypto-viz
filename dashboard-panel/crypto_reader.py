import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os
from io import BytesIO
import pyarrow as pa
import pyarrow.parquet as pq
from minio import Minio
from minio.error import S3Error
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoDataReader:
    def __init__(self):
        # Configuration MinIO - CORRECTION DE L'ENDPOINT
        self.minio_endpoint = os.getenv('MINIO_ENDPOINT', '192.168.1.76:9002')  # IP directe au lieu du nom du service
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin') 
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket_name = 'crypto-data-partitioned'
        
        try:
            # Connexion MinIO avec gestion d'erreur
            self.client = Minio(
                self.minio_endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=False
            )
            logger.info(f"Initialized CryptoDataReader with MinIO endpoint: {self.minio_endpoint}")
            
            # Test immédiat de la connexion
            self.connection_ok = self.test_connection()
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None
            self.connection_ok = False

    def get_latest_crypto_data(self, limit_hours=24):
        """Récupère les dernières données crypto depuis MinIO"""
        
        if not self.connection_ok or not self.client:
            logger.warning("MinIO not available, using demo data")
            return self._get_demo_data()
            
        try:
            # Date actuelle pour le partitioning
            now = datetime.now()
            year = now.year
            month = now.month 
            day = now.day
            
            # Préfixe pour les données d'aujourd'hui
            prefix = f"year={year}/month={month}/day={day}/"
            
            logger.info(f"Fetching crypto data from prefix: {prefix}")
            
            # Liste des objets dans le bucket
            objects = list(self.client.list_objects(
                self.bucket_name, 
                prefix=prefix,
                recursive=True
            ))
            
            if not objects:
                logger.warning("No objects found in MinIO, using demo data")
                return self._get_demo_data()
            
            # Lire tous les fichiers Parquet trouvés
            all_data = []
            
            for obj in objects:
                if obj.object_name.endswith('.parquet'):
                    try:
                        # Télécharger le fichier
                        response = self.client.get_object(self.bucket_name, obj.object_name)
                        parquet_data = response.read()
                        
                        # Lire le Parquet
                        df = pd.read_parquet(BytesIO(parquet_data))
                        all_data.append(df)
                        
                        logger.info(f"Loaded {len(df)} rows from {obj.object_name}")
                        
                        # Limiter à quelques fichiers pour éviter la surcharge
                        if len(all_data) >= 5:
                            break
                        
                    except Exception as e:
                        logger.error(f"Error reading {obj.object_name}: {e}")
                        continue
            
            if not all_data:
                logger.warning("No parquet data found, using demo data")
                return self._get_demo_data()
                
            # Concaténer toutes les données
            combined_df = pd.concat(all_data, ignore_index=True)
            
            # Conversion du timestamp si nécessaire
            if 'timestamp' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            
            # Trier par timestamp décroissant
            if 'timestamp' in combined_df.columns:
                combined_df = combined_df.sort_values('timestamp', ascending=False)
            
            # Filtrer les dernières heures
            if 'timestamp' in combined_df.columns and limit_hours:
                cutoff_time = now - timedelta(hours=limit_hours)
                combined_df = combined_df[combined_df['timestamp'] >= cutoff_time]
            
            logger.info(f"Returning {len(combined_df)} crypto data points from MinIO")
            return combined_df
            
        except S3Error as e:
            logger.error(f"MinIO S3 Error: {e}")
            return self._get_demo_data()
        except Exception as e:
            logger.error(f"Error fetching crypto data: {e}")
            return self._get_demo_data()

    def get_crypto_summary(self):
        """Récupère le résumé des cryptos avec derniers prix et variations"""
        try:
            df = self.get_latest_crypto_data(limit_hours=2)
            
            if df.empty:
                logger.info("No real data available, using demo summary")
                return self._get_demo_summary()
            
            # Grouper par crypto et calculer les métriques
            summary = {}
            
            if 'symbol' in df.columns and 'price' in df.columns:
                for symbol in df['symbol'].unique():
                    symbol_data = df[df['symbol'] == symbol].copy()
                    
                    if len(symbol_data) > 0:
                        # Prix actuel (plus récent)
                        current_price = float(symbol_data.iloc[0]['price'])
                        
                        # Prix précédent pour calculer la variation
                        if len(symbol_data) > 1:
                            previous_price = float(symbol_data.iloc[-1]['price'])
                            change_pct = ((current_price - previous_price) / previous_price) * 100
                        else:
                            change_pct = np.random.uniform(-5, 5)  # Random si pas assez de données
                        
                        # Volume si disponible
                        volume = float(symbol_data.iloc[0].get('volume', 0)) if 'volume' in symbol_data.columns else np.random.uniform(1000000, 100000000)
                        
                        summary[symbol] = {
                            'symbol': symbol,
                            'price': current_price,
                            'change_24h': change_pct,
                            'volume_24h': volume,
                            'data_points': len(symbol_data)
                        }
            
            if not summary:
                logger.info("No symbol data parsed, using demo summary")
                return self._get_demo_summary()
                
            logger.info(f"Generated real summary for {len(summary)} cryptocurrencies")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating crypto summary: {e}")
            return self._get_demo_summary()

    def get_price_history(self, symbol='BTC', hours=24):
        """Récupère l'historique des prix pour un crypto donné"""
        try:
            df = self.get_latest_crypto_data(limit_hours=hours)
            
            if df.empty or 'symbol' not in df.columns:
                logger.info(f"No real data for price history of {symbol}, using demo")
                return self._get_demo_price_history(symbol)
            
            # Filtrer par symbole
            symbol_data = df[df['symbol'] == symbol].copy()
            
            if symbol_data.empty:
                logger.info(f"No data for {symbol}, using demo price history")
                return self._get_demo_price_history(symbol)
            
            # S'assurer qu'on a les colonnes nécessaires
            if 'timestamp' in symbol_data.columns and 'price' in symbol_data.columns:
                # Trier par timestamp croissant pour l'historique
                symbol_data = symbol_data.sort_values('timestamp')
                
                result = {
                    'timestamps': symbol_data['timestamp'].tolist(),
                    'prices': symbol_data['price'].tolist(),
                    'symbol': symbol
                }
                
                logger.info(f"Returning real price history for {symbol}: {len(result['prices'])} points")
                return result
            
            return self._get_demo_price_history(symbol)
            
        except Exception as e:
            logger.error(f"Error fetching price history for {symbol}: {e}")
            return self._get_demo_price_history(symbol)

    def _get_demo_data(self):
        """Données de démonstration si MinIO n'est pas accessible"""
        logger.info("Using demo data as fallback")
        
        # Générer des données de démo réalistes
        symbols = ['BTC', 'ETH', 'LTC', 'SOL']
        base_prices = {'BTC': 52000, 'ETH': 3200, 'LTC': 180, 'SOL': 140}
        
        demo_data = []
        now = datetime.now()
        
        for symbol in symbols:
            base_price = base_prices[symbol]
            
            # Générer 100 points de données sur les dernières 24h
            for i in range(100):
                timestamp = now - timedelta(minutes=i*15)  # Données toutes les 15 min
                
                # Prix avec variation aléatoire
                price_variation = np.random.normal(0, base_price * 0.01)  # 1% de volatilité
                price = base_price + price_variation
                
                volume = np.random.uniform(1000000, 50000000)
                
                demo_data.append({
                    'timestamp': timestamp,
                    'symbol': symbol,
                    'price': price,
                    'volume': volume
                })
        
        return pd.DataFrame(demo_data)

    def _get_demo_summary(self):
        """Résumé de démo"""
        return {
            'BTC': {
                'symbol': 'BTC',
                'price': 52291.0,
                'change_24h': 0.25,
                'volume_24h': 65200000,
                'data_points': 0  # 0 indique données de démo
            },
            'ETH': {
                'symbol': 'ETH', 
                'price': 3245.0,
                'change_24h': -2.15,
                'volume_24h': 45600000,
                'data_points': 0
            },
            'LTC': {
                'symbol': 'LTC',
                'price': 180.5,
                'change_24h': 1.85,
                'volume_24h': 28900000,
                'data_points': 0
            },
            'SOL': {
                'symbol': 'SOL',
                'price': 142.3,
                'change_24h': -0.75,
                'volume_24h': 19800000,
                'data_points': 0
            }
        }

    def _get_demo_price_history(self, symbol):
        """Historique de prix de démo"""
        base_prices = {'BTC': 52000, 'ETH': 3200, 'LTC': 180, 'SOL': 140}
        base_price = base_prices.get(symbol, 1000)
        
        # Générer 100 points sur 24h
        timestamps = []
        prices = []
        now = datetime.now()
        
        current_price = base_price
        for i in range(100):
            timestamp = now - timedelta(minutes=i*15)
            # Prix avec marche aléatoire réaliste
            change = np.random.normal(0, base_price * 0.005)  # 0.5% de volatilité
            current_price = max(current_price + change, base_price * 0.8)  # Prix minimum à 80% du prix de base
            
            timestamps.append(timestamp)
            prices.append(current_price)
        
        return {
            'timestamps': list(reversed(timestamps)),
            'prices': list(reversed(prices)),
            'symbol': symbol
        }

    def test_connection(self):
        """Test la connexion à MinIO"""
        try:
            if not self.client:
                return False
                
            bucket_exists = self.client.bucket_exists(self.bucket_name)
            if bucket_exists:
                logger.info(f"✅ Successfully connected to MinIO bucket: {self.bucket_name}")
                return True
            else:
                logger.warning(f"❌ Bucket {self.bucket_name} does not exist")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to connect to MinIO: {e}")
            return False
