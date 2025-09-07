"""
Smart Historical Reader - Lecture optimisée des données historiques MinIO
Évite de charger tous les 7000+ fichiers Parquet d'un coup
"""

import os
import pandas as pd
import s3fs
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
import logging
import random

logger = logging.getLogger(__name__)

class SmartHistoricalReader:
    """Reader optimisé pour éviter de charger 7000+ fichiers Parquet"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.minio_access_key = os.getenv("MINIO_ROOT_USER", "cryptoviz")
        self.minio_secret_key = os.getenv("MINIO_ROOT_PASSWORD", "cryptoviz2024")
        
        self.bucket = "crypto-data-partitioned"
        
        try:
            self.fs = s3fs.S3FileSystem(
                endpoint_url=self.minio_endpoint,
                key=self.minio_access_key,
                secret=self.minio_secret_key
            )
            logger.info(f"✅ Smart reader initialisé pour {self.bucket}")
        except Exception as e:
            logger.error(f"❌ Erreur connexion MinIO: {e}")
            self.fs = None
    
    def get_recent_partitions_only(self, hours_back: int = 24) -> List[str]:
        """Récupère seulement les partitions récentes (dernières 24h par défaut)"""
        if not self.fs:
            return []
        
        try:
            # Calculer les dates récentes
            now = datetime.now()
            dates_to_check = []
            
            for i in range(hours_back // 24 + 2):  # +2 pour être sûr
                date = now - timedelta(days=i)
                dates_to_check.append({
                    'year': date.year,
                    'month': date.month,
                    'day': date.day
                })
            
            recent_files = []
            
            for date_info in dates_to_check:
                partition_path = f"{self.bucket}/year={date_info['year']}/month={date_info['month']}/day={date_info['day']}"
                
                try:
                    files_in_partition = self.fs.find(partition_path)
                    parquet_files = [f for f in files_in_partition if f.endswith('.parquet')]
                    recent_files.extend(parquet_files)
                    
                    if parquet_files:
                        logger.info(f"📁 Partition {date_info['year']}-{date_info['month']:02d}-{date_info['day']:02d}: {len(parquet_files)} fichiers")
                
                except Exception as e:
                    logger.debug(f"Partition {partition_path} non trouvée: {e}")
                    continue
            
            logger.info(f"🎯 Fichiers récents trouvés: {len(recent_files)} (au lieu de 7000+)")
            return recent_files
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération partitions récentes: {e}")
            return []
    
    def sample_files_smartly(self, all_files: List[str], max_files: int = 50) -> List[str]:
        """Échantillonne intelligemment les fichiers (prend les plus récents)"""
        if len(all_files) <= max_files:
            return all_files
        
        # Trier par nom (les plus récents ont des timestamps plus élevés dans le nom)
        sorted_files = sorted(all_files, reverse=True)
        
        # Prendre les plus récents
        sampled = sorted_files[:max_files]
        
        logger.info(f"📊 Échantillonnage: {len(sampled)}/{len(all_files)} fichiers sélectionnés")
        return sampled
    
    def load_recent_historical_data(self, hours_back: int = 24, max_files: int = 100) -> pd.DataFrame:
        """Charge seulement les données historiques récentes (stratégie optimisée)"""
        if not self.fs:
            logger.warning("⚠️ Pas de connexion MinIO - retour DataFrame vide")
            return pd.DataFrame()
        
        try:
            logger.info(f"🔍 Chargement données historiques: dernières {hours_back}h, max {max_files} fichiers")
            
            # Étape 1: Récupérer seulement les partitions récentes
            recent_files = self.get_recent_partitions_only(hours_back)
            
            if not recent_files:
                logger.warning("⚠️ Aucun fichier récent trouvé")
                return pd.DataFrame()
            
            # Étape 2: Échantillonner si trop de fichiers
            files_to_read = self.sample_files_smartly(recent_files, max_files)
            
            # Étape 3: Charger les fichiers sélectionnés
            dfs = []
            loaded_count = 0
            
            for file_path in files_to_read:
                try:
                    df = pd.read_parquet(f"s3://{file_path}", filesystem=self.fs)
                    
                    if not df.empty:
                        dfs.append(df)
                        loaded_count += 1
                        
                        # Progress log tous les 10 fichiers
                        if loaded_count % 10 == 0:
                            logger.info(f"📈 Chargé {loaded_count}/{len(files_to_read)} fichiers...")
                
                except Exception as e:
                    logger.warning(f"⚠️ Erreur lecture {file_path}: {e}")
                    continue
            
            if not dfs:
                logger.warning("⚠️ Aucune donnée valide trouvée")
                return pd.DataFrame()
            
            # Étape 4: Combiner et nettoyer
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Conversion timestamp
            if 'timestamp' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            elif 'timestamp_dt' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp_dt'])
            
            # Tri par timestamp et dédoublonnage
            if 'timestamp' in combined_df.columns:
                combined_df = combined_df.sort_values('timestamp')
                # Garder seulement les données dans la fenêtre temporelle
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                combined_df = combined_df[combined_df['timestamp'] >= cutoff_time]
            
            # Dédoublonnage basique (garder le plus récent par crypto+timestamp)
            if 'symbol' in combined_df.columns and 'timestamp' in combined_df.columns:
                combined_df = combined_df.drop_duplicates(subset=['symbol', 'timestamp'], keep='last')
            
            logger.info(f"✅ Données historiques chargées: {len(combined_df)} lignes depuis {loaded_count} fichiers")
            return combined_df
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement données historiques: {e}")
            return pd.DataFrame()
    
    def get_latest_data_sample(self, max_records: int = 1000) -> pd.DataFrame:
        """Récupère un échantillon des données les plus récentes (ultra-rapide)"""
        try:
            # Charger seulement les 10 fichiers les plus récents
            df = self.load_recent_historical_data(hours_back=6, max_files=10)
            
            if df.empty:
                return df
            
            # Garder seulement les plus récents
            if len(df) > max_records:
                df = df.tail(max_records)
            
            logger.info(f"⚡ Échantillon rapide: {len(df)} lignes")
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur échantillon rapide: {e}")
            return pd.DataFrame()
    
    def get_historical_summary(self) -> Dict:
        """Récupère un résumé des données historiques sans tout charger"""
        try:
            # Charger un petit échantillon pour les stats
            sample_df = self.get_latest_data_sample(max_records=500)
            
            if sample_df.empty:
                return {
                    'status': 'no_data',
                    'total_files': 0,
                    'estimated_records': 0,
                    'available_cryptos': [],
                    'date_range': 'N/A'
                }
            
            # Stats basées sur l'échantillon
            unique_cryptos = list(sample_df['symbol'].unique()) if 'symbol' in sample_df.columns else []
            
            date_range = "N/A"
            if 'timestamp' in sample_df.columns and not sample_df.empty:
                min_date = sample_df['timestamp'].min().strftime('%Y-%m-%d %H:%M')
                max_date = sample_df['timestamp'].max().strftime('%Y-%m-%d %H:%M')
                date_range = f"{min_date} à {max_date}"
            
            # Estimation du nombre total de fichiers (approximation)
            recent_files = self.get_recent_partitions_only(hours_back=24)
            estimated_total = len(recent_files) * 7  # Estimation grossière
            
            return {
                'status': 'success',
                'total_files_recent': len(recent_files),
                'estimated_total_files': estimated_total,
                'sample_records': len(sample_df),
                'available_cryptos': unique_cryptos,
                'cryptos_count': len(unique_cryptos),
                'date_range_sample': date_range
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur résumé historique: {e}")
            return {'status': 'error', 'message': str(e)}

def get_smart_reader():
    """Factory pour créer le reader intelligent"""
    return SmartHistoricalReader()
