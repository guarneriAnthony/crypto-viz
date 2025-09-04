"""
CryptoViz V3 - Parquet Data Reader (Version s3fs)
Lecteur intelligent pour données Parquet depuis MinIO S3
"""

import os
import s3fs
import pandas as pd
import streamlit as st
from typing import List, Optional
import duckdb

class ParquetDataReader:
    """Lecteur de données Parquet avec s3fs"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "cryptoviz")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
        
        # Setup s3fs
        self.fs = s3fs.S3FileSystem(
            endpoint_url=self.minio_endpoint,
            key=self.minio_access_key,
            secret=self.minio_secret_key
        )
    
    def read_latest_data(self, limit: int = 100) -> pd.DataFrame:
        """Lit les dernières données Parquet disponibles"""
        try:
            # Lister tous les fichiers Parquet
            files = self.fs.ls('crypto-data/')
            parquet_files = [f for f in files if f.endswith('.parquet')]
            
            if not parquet_files:
                return pd.DataFrame()
            
            # Lire les derniers fichiers (max 10)
            recent_files = parquet_files[-10:]  # Derniers créés
            dataframes = []
            
            for file_path in recent_files:
                try:
                    with self.fs.open(f's3://{file_path}', 'rb') as f:
                        df = pd.read_parquet(f)
                        dataframes.append(df)
                except Exception as e:
                    continue
            
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                
                # Tri par timestamp le plus récent
                if 'timestamp' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                    combined_df = combined_df.sort_values('timestamp', ascending=False)
                
                # Déduplication par nom + source + timestamp
                if 'name' in combined_df.columns and 'source' in combined_df.columns:
                    combined_df = combined_df.drop_duplicates(['name', 'source', 'timestamp'], keep='first')
                
                return combined_df.head(limit)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Erreur lecture Parquet: {e}")
            return pd.DataFrame()
    
    def get_available_dates(self) -> List[str]:
        """Récupère les dates disponibles"""
        try:
            from datetime import datetime, timedelta
            
            # Pour les fichiers Parquet non-partitionnés, on retourne les derniers jours
            today = datetime.now()
            dates = []
            for i in range(7):  # 7 derniers jours
                date = (today - timedelta(days=i)).strftime('%Y-%m-%d')
                dates.append(date)
            return dates
        except Exception:
            return []
    
    def get_available_cryptos(self, date_filter: Optional[str] = None) -> List[str]:
        """Récupère les cryptos disponibles"""
        try:
            data = self.read_latest_data(limit=500)
            if not data.empty and 'name' in data.columns:
                cryptos = sorted(data['name'].unique().tolist())
                return cryptos
            else:
                return []
        except Exception:
            return []
    
    def fallback_to_duckdb(self) -> pd.DataFrame:
        """Fallback vers DuckDB si Parquet indisponible"""
        try:
            conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=True)
            df = conn.execute("""
                SELECT * FROM crypto_prices 
                ORDER BY timestamp DESC 
                LIMIT 100
            """).fetchdf()
            conn.close()
            return df
        except Exception as e:
            st.error(f"Erreur DuckDB fallback: {e}")
            return pd.DataFrame()
    
    def get_crypto_data(self, crypto: Optional[str] = None, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None, use_parquet: bool = True) -> pd.DataFrame:
        """Interface unifiée pour récupérer les données"""
        if use_parquet:
            data = self.read_latest_data()
            if data.empty:
                st.warning("📦 Aucune donnée Parquet disponible, fallback vers DuckDB")
                return self.fallback_to_duckdb()
            return data
        else:
            return self.fallback_to_duckdb()

@st.cache_resource(ttl=60)  # Cache 1 minute pour données temps réel
def get_data_reader():
    """Factory avec cache pour le reader"""
    return ParquetDataReader()
