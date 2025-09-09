"""
CryptoViz  V4.0 - Reader SIMPLIFIÉ qui fonctionne vraiment
Lecture directe des données partitionnées
"""

import os
import pandas as pd
import s3fs
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)

class PartitionedDataReader:
    """Reader SIMPLIFIÉ pour données partitionnées - Version qui fonctionne"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "cryptoviz")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
        
        self.bucket = "crypto-data-partitioned"
        
        self.fs = s3fs.S3FileSystem(
            endpoint_url=self.minio_endpoint,
            key=self.minio_access_key,
            secret=self.minio_secret_key
        )
        
        logger.info(f"Reader initialisé pour {self.bucket}")
    
    def get_all_parquet_files(self) -> List[str]:
        """Récupère tous les fichiers Parquet disponibles"""
        try:
            all_files = self.fs.find(f"{self.bucket}/")
            parquet_files = [f for f in all_files if f.endswith('.parquet')]
            logger.info(f"Fichiers Parquet trouvés: {len(parquet_files)}")
            return parquet_files
        except Exception as e:
            logger.error(f"Erreur récupération fichiers: {e}")
            return []
    
    def read_all_data(self) -> pd.DataFrame:
        """Lit toutes les données disponibles"""
        try:
            parquet_files = self.get_all_parquet_files()
            
            if not parquet_files:
                logger.warning("Aucun fichier Parquet trouvé")
                return pd.DataFrame()
            
            # Lire tous les fichiers
            dfs = []
            for file_path in parquet_files:
                try:
                    df = pd.read_parquet(f"s3://{file_path}", filesystem=self.fs)
                    dfs.append(df)
                except Exception as e:
                    logger.warning(f"Erreur lecture {file_path}: {e}")
                    continue
            
            if dfs:
                combined_df = pd.concat(dfs, ignore_index=True)
                
                # Conversion timestamp
                if 'timestamp' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                elif 'timestamp_dt' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp_dt'])
                
                # Tri par timestamp
                if 'timestamp' in combined_df.columns:
                    combined_df = combined_df.sort_values('timestamp')
                
                logger.info(f"Données combinées: {len(combined_df)} lignes")
                return combined_df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Erreur lecture données: {e}")
            return pd.DataFrame()
    
    def read_recent_data(self, hours: int = 24) -> pd.DataFrame:
        """Lit les données récentes"""
        try:
            df = self.read_all_data()
            
            if df.empty:
                return df
            
            if 'timestamp' in df.columns:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                recent_df = df[df['timestamp'] >= cutoff_time]
                logger.info(f"Données récentes ({hours}h): {len(recent_df)} lignes")
                return recent_df
            
            # Si pas de timestamp, retourner tout
            return df
            
        except Exception as e:
            logger.error(f"Erreur données récentes: {e}")
            return pd.DataFrame()
    
    def read_latest_batch(self, limit: int = 100) -> pd.DataFrame:
        """Lit les dernières données"""
        try:
            df = self.read_all_data()
            
            if df.empty:
                return df
            
            # Retourner les dernières lignes
            latest_df = df.tail(limit)
            logger.info(f"Dernier batch: {len(latest_df)} lignes")
            return latest_df
            
        except Exception as e:
            logger.error(f"Erreur dernier batch: {e}")
            return pd.DataFrame()
    
    def get_crypto_data(self, symbol: str, hours: int = 24) -> pd.DataFrame:
        """Données pour un crypto spécifique"""
        try:
            df = self.read_recent_data(hours=hours)
            
            if df.empty or 'symbol' not in df.columns:
                return pd.DataFrame()
            
            crypto_df = df[df['symbol'] == symbol].copy()
            logger.info(f"Données {symbol}: {len(crypto_df)} lignes")
            return crypto_df
            
        except Exception as e:
            logger.error(f"Erreur données {symbol}: {e}")
            return pd.DataFrame()
    
    def get_summary_stats(self) -> Dict:
        """Statistiques du dataset"""
        try:
            df = self.read_all_data()
            
            if df.empty:
                return {}
            
            files_count = len(self.get_all_parquet_files())
            unique_cryptos = list(df['symbol'].unique()) if 'symbol' in df.columns else []
            
            # Période couverte
            date_range = "N/A"
            if 'timestamp' in df.columns:
                min_date = df['timestamp'].min().strftime('%Y-%m-%d %H:%M')
                max_date = df['timestamp'].max().strftime('%Y-%m-%d %H:%M')
                date_range = f"{min_date} à {max_date}"
            
            stats = {
                'total_files': files_count,
                'total_records': len(df),
                'date_range': date_range,
                'available_cryptos': unique_cryptos,
                'cryptos_count': len(unique_cryptos)
            }
            
            logger.info(f"Stats: {len(df)} lignes, {len(unique_cryptos)} cryptos")
            return stats
            
        except Exception as e:
            logger.error(f"Erreur statistiques: {e}")
            return {}
    
    def get_available_partitions(self) -> List[Dict]:
        """Compatibilité - retourne info sur les données"""
        try:
            files = self.get_all_parquet_files()
            if files:
                return [{
                    'year': 2025,
                    'month': 9,
                    'day': 5,
                    'files_count': len(files),
                    'date': '2025-09-05'
                }]
            return []
        except:
            return []
    
    def read_partition(self, year: int, month: int, day: int) -> pd.DataFrame:
        """Compatibilité - retourne toutes les données"""
        return self.read_all_data()

def get_partitioned_reader():
    """Factory pour créer le reader"""
    return PartitionedDataReader()
