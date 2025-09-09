"""
Hybrid Data Manager - Solution définitive pour historique MinIO + Stream Kafka
Gère automatiquement les 7000+ fichiers Parquet avec filtrage intelligent
FIXÉE: Consumer Kafka maintenant actif en permanence sans timeout
"""

import os
import pandas as pd
import s3fs
import json
import threading
import time
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional, Tuple
from kafka import KafkaConsumer

logger = logging.getLogger(__name__)

class HybridDataManager:
    """
    Data Manager définitif pour architecture hybride production-ready
    - Historique MinIO (filtré intelligemment pour éviter 7000+ fichiers)
    - Stream Kafka temps réel (connexion permanente FIXÉE)
    - Fusion automatique et dédoublonnage
    - Cache optimisé
    """
    
    def __init__(self, 
                 minio_endpoint: str = None,
                 minio_user: str = None, 
                 minio_password: str = None,
                 kafka_brokers: List[str] = None,
                 kafka_topic: str = 'crypto-streaming'):
        
        # Configuration MinIO
        self.minio_endpoint = minio_endpoint or os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.minio_user = minio_user or os.getenv("MINIO_ROOT_USER", "cryptoviz")
        self.minio_password = minio_password or os.getenv("MINIO_ROOT_PASSWORD", "cryptoviz2024")
        self.bucket = "crypto-data-partitioned"
        
        # Configuration Kafka
        self.kafka_brokers = kafka_brokers or ['redpanda:9092']
        self.kafka_topic = kafka_topic
        
        # État interne
        self._historical_data = pd.DataFrame()
        self._live_buffer = deque(maxlen=2000)  # Buffer circulaire
        self._combined_data = pd.DataFrame()
        self._last_historical_load = None
        self._kafka_consumer_active = False
        self._kafka_thread = None
        self._kafka_should_stop = False  # Flag pour arrêt propre
        
        # Configuration de performance
        self.default_hours_back = 24
        self.default_max_files = 100
        self.historical_refresh_interval = 3600  # 1h entre recharges auto
        
        # Initialisation connexions
        self._init_minio()
        
        logger.info("   HybridDataManager initialisé (version FIXÉE)")
    
    def _init_minio(self):
        """Initialise la connexion MinIO"""
        try:
            self.fs = s3fs.S3FileSystem(
                endpoint_url=self.minio_endpoint,
                key=self.minio_user,
                secret=self.minio_password
            )
            logger.info("✅ Connexion MinIO établie")
        except Exception as e:
            logger.error(f"❌ Erreur connexion MinIO: {e}")
            self.fs = None
    
    def _get_recent_partitions(self, hours_back: int = 24) -> List[str]:
        """Récupère les partitions récentes pour éviter 7000+ fichiers"""
        if not self.fs:
            return []
        
        try:
            now = datetime.now()
            recent_files = []
            days_to_check = (hours_back // 24) + 2
            
            logger.info(f"🔍 Recherche fichiers dans les {days_to_check} derniers jours")
            
            for i in range(days_to_check):
                date = now - timedelta(days=i)
                partition_path = f"{self.bucket}/year={date.year}/month={date.month}/day={date.day}"
                
                try:
                    files = self.fs.find(partition_path)
                    parquet_files = [f for f in files if f.endswith('.parquet')]
                    recent_files.extend(parquet_files)
                    
                    if parquet_files:
                        logger.debug(f"📁 {date.strftime('%Y-%m-%d')}: {len(parquet_files)} fichiers")
                        
                except Exception:
                    continue
            
            logger.info(f"  {len(recent_files)} fichiers trouvés (filtrage intelligent)")
            return recent_files
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération partitions: {e}")
            return []
    
    def _smart_file_sampling(self, files: List[str], max_files: int) -> List[str]:
        """Échantillonnage intelligent des fichiers"""
        if len(files) <= max_files:
            return files
        
        # Trier par nom pour avoir les plus récents
        sorted_files = sorted(files, reverse=True)
        sampled_files = sorted_files[:max_files]
        
        logger.info(f"  Échantillonnage: {len(sampled_files)}/{len(files)} fichiers")
        return sampled_files
    
    def load_historical_data(self, hours_back: int = None, max_files: int = None, force_reload: bool = False) -> bool:
        """
        Charge les données historiques de manière optimisée
        Returns: True si chargement réussi
        """
        hours_back = hours_back or self.default_hours_back
        max_files = max_files or self.default_max_files
        
        # Vérifier si recharge nécessaire
        if not force_reload and self._last_historical_load:
            time_since_load = datetime.now() - self._last_historical_load
            if time_since_load.total_seconds() < self.historical_refresh_interval:
                logger.debug(f"  Historique récent ({time_since_load.total_seconds():.0f}s), pas de recharge")
                return True
        
        if not self.fs:
            logger.warning("⚠️ Pas de connexion MinIO")
            return False
        
        try:
            start_time = time.time()
            logger.info(f"🔍 Chargement historique: {hours_back}h, max {max_files} fichiers")
            
            # Étape 1: Récupérer fichiers récents
            recent_files = self._get_recent_partitions(hours_back)
            if not recent_files:
                logger.warning("⚠️ Aucun fichier récent trouvé")
                return False
            
            # Étape 2: Échantillonnage
            files_to_load = self._smart_file_sampling(recent_files, max_files)
            
            # Étape 3: Chargement
            dfs = []
            loaded_count = 0
            
            for file_path in files_to_load:
                try:
                    df = pd.read_parquet(f"s3://{file_path}", filesystem=self.fs)
                    if not df.empty:
                        dfs.append(df)
                        loaded_count += 1
                        
                        if loaded_count % 20 == 0:
                            logger.info(f"📈 Chargé {loaded_count}/{len(files_to_load)} fichiers...")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Erreur fichier {file_path}: {e}")
                    continue
            
            if not dfs:
                logger.warning("⚠️ Aucune donnée valide chargée")
                return False
            
            # Étape 4: Consolidation
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Normalisation timestamps
            if 'timestamp' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            elif 'timestamp_dt' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp_dt'])
                combined_df = combined_df.rename(columns={'timestamp_dt': 'timestamp'})
            
            # Filtrage temporel
            if 'timestamp' in combined_df.columns:
                cutoff_time = datetime.now() - timedelta(hours=hours_back)
                combined_df = combined_df[combined_df['timestamp'] >= cutoff_time]
                combined_df = combined_df.sort_values('timestamp')
            
            # Dédoublonnage
            if 'symbol' in combined_df.columns and 'timestamp' in combined_df.columns:
                combined_df = combined_df.drop_duplicates(['symbol', 'timestamp'], keep='last')
            
            # Marquage source
            combined_df['data_source'] = 'historical'
            
            # Mise à jour état
            self._historical_data = combined_df
            self._last_historical_load = datetime.now()
            
            load_time = time.time() - start_time
            cryptos_count = combined_df['symbol'].nunique() if 'symbol' in combined_df.columns else 0
            
            logger.info(f"✅ Historique chargé: {len(combined_df)} lignes, {cryptos_count} cryptos en {load_time:.1f}s")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement historique: {e}")
            return False
    
    def start_kafka_consumer(self):
        """Démarre le consumer Kafka en arrière-plan avec reconnexion automatique"""
        if self._kafka_consumer_active:
            return True
        
        def kafka_worker():
            """Worker Kafka avec reconnexion automatique et sans timeout"""
            retry_count = 0
            max_retries = 5
            retry_delay = 5
            
            while not self._kafka_should_stop:
                consumer = None
                try:
                    logger.info(f"  Tentative de connexion Kafka (essai {retry_count + 1})...")
                    
                    consumer = KafkaConsumer(
                        self.kafka_topic,
                        bootstrap_servers=self.kafka_brokers,
                        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                        # CORRECTION PRINCIPALE: Suppression du timeout
                        # consumer_timeout_ms=None,  # Pas de timeout !
                        auto_offset_reset='latest',
                        enable_auto_commit=True,
                        group_id='hybrid_data_manager',
                        # Configuration de reconnexion robuste
                        reconnect_backoff_ms=1000,
                        reconnect_backoff_max_ms=10000,
                        heartbeat_interval_ms=3000,
                        session_timeout_ms=30000,
                        # Éviter les déconnexions fréquentes
                        connections_max_idle_ms=600000,  # 10 minutes
                        max_poll_records=500,
                        fetch_min_bytes=1,
                        fetch_max_wait_ms=500
                    )
                    
                    self._kafka_consumer_active = True
                    retry_count = 0  # Reset du compteur en cas de succès
                    logger.info(f"  Kafka consumer connecté: {self.kafka_topic}")
                    
                    # Boucle de consommation INFINIE
                    for message in consumer:
                        if self._kafka_should_stop:
                            break
                            
                        try:
                            data = message.value
                            
                            # Enrichir avec métadonnées
                            data['data_source'] = 'live'
                            data['received_at'] = datetime.now().isoformat()
                            
                            if 'timestamp' not in data:
                                data['timestamp'] = data['received_at']
                            
                            # Ajouter au buffer
                            self._live_buffer.append(data)
                            
                            logger.debug(f"📨 Live: {data.get('symbol', 'Unknown')} = ${data.get('price', 0)}")
                            
                        except Exception as e:
                            logger.warning(f"⚠️ Erreur traitement message Kafka: {e}")
                            continue
                    
                except Exception as e:
                    logger.error(f"❌ Erreur Kafka consumer (essai {retry_count + 1}): {e}")
                    self._kafka_consumer_active = False
                    
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ Abandon après {max_retries} tentatives")
                        break
                    
                    logger.info(f"  Reconnexion dans {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay = min(retry_delay * 2, 60)  # Exponential backoff
                    
                finally:
                    if consumer:
                        try:
                            consumer.close()
                        except:
                            pass
            
            self._kafka_consumer_active = False
            logger.info("🛑 Kafka consumer arrêté")
        
        self._kafka_should_stop = False
        self._kafka_thread = threading.Thread(target=kafka_worker, daemon=True)
        self._kafka_thread.start()
        
        # Attendre démarrage
        time.sleep(2)
        return self._kafka_consumer_active
    
    def stop_kafka_consumer(self):
        """Arrêt propre du consumer Kafka"""
        if self._kafka_consumer_active:
            logger.info("🛑 Arrêt du consumer Kafka...")
            self._kafka_should_stop = True
            if self._kafka_thread and self._kafka_thread.is_alive():
                self._kafka_thread.join(timeout=10)
        
    def get_combined_data(self, auto_load_historical: bool = True) -> pd.DataFrame:
        """
        Retourne les données combinées (historique + live)
        auto_load_historical: Charge automatiquement l'historique si nécessaire
        """
        try:
            # Chargement automatique historique si nécessaire
            if auto_load_historical and self._historical_data.empty:
                logger.info("  Auto-chargement historique...")
                self.load_historical_data()
            
            # Démarrage automatique Kafka si nécessaire
            if not self._kafka_consumer_active:
                logger.info("  Auto-démarrage Kafka consumer...")
                self.start_kafka_consumer()
            
            # Conversion buffer live en DataFrame
            live_df = pd.DataFrame()
            if self._live_buffer:
                live_data = list(self._live_buffer)
                live_df = pd.DataFrame(live_data)
                
                # Normalisation timestamps live
                if 'received_at' in live_df.columns:
                    live_df['timestamp'] = pd.to_datetime(live_df['received_at'])
            
            # Combinaison des données
            historical_df = self._historical_data.copy()
            
            if not historical_df.empty and not live_df.empty:
                # Colonnes communes
                common_cols = set(historical_df.columns) & set(live_df.columns)
                
                if common_cols and len(common_cols) >= 3:  # Au minimum symbol, price, timestamp
                    hist_subset = historical_df[list(common_cols)]
                    live_subset = live_df[list(common_cols)]
                    
                    combined = pd.concat([hist_subset, live_subset], ignore_index=True)
                    
                    # Tri et dédoublonnage final
                    if 'timestamp' in combined.columns:
                        combined = combined.sort_values('timestamp')
                        
                        if 'symbol' in combined.columns:
                            # Garder les données live en priorité
                            combined = combined.drop_duplicates(['symbol', 'timestamp'], keep='last')
                    
                    self._combined_data = combined
                    return combined
            
            elif not live_df.empty:
                self._combined_data = live_df
                return live_df
            elif not historical_df.empty:
                self._combined_data = historical_df
                return historical_df
            
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"❌ Erreur combinaison données: {e}")
            return self._historical_data if not self._historical_data.empty else pd.DataFrame()
    
    def get_status(self) -> Dict:
        """Retourne le statut du data manager"""
        combined_data = self.get_combined_data(auto_load_historical=False)
        
        historical_count = len(self._historical_data)
        live_count = len(self._live_buffer)
        combined_count = len(combined_data)
        
        cryptos_count = combined_data['symbol'].nunique() if 'symbol' in combined_data.columns and not combined_data.empty else 0
        
        return {
            'historical_loaded': not self._historical_data.empty,
            'historical_count': historical_count,
            'kafka_active': self._kafka_consumer_active,
            'live_buffer_count': live_count,
            'combined_count': combined_count,
            'active_cryptos': cryptos_count,
            'last_historical_load': self._last_historical_load.isoformat() if self._last_historical_load else None,
            'minio_connected': self.fs is not None,
            'kafka_thread_alive': self._kafka_thread.is_alive() if self._kafka_thread else False
        }
    
    def refresh_historical(self, hours_back: int = None, max_files: int = None):
        """Force le refresh des données historiques"""
        return self.load_historical_data(hours_back, max_files, force_reload=True)

    def __del__(self):
        """Nettoyage à la destruction"""
        try:
            self.stop_kafka_consumer()
        except:
            pass

# Instance globale singleton
_global_data_manager = None

def get_data_manager() -> HybridDataManager:
    """Factory pour obtenir l'instance globale du data manager"""
    global _global_data_manager
    if _global_data_manager is None:
        _global_data_manager = HybridDataManager()
    return _global_data_manager
