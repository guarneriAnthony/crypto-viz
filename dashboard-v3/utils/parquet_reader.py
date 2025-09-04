"""
CryptoViz V3 - Parquet Data Reader
Lecteur intelligent pour données Parquet depuis MinIO S3
"""

import os
import boto3
import pandas as pd
import streamlit as st
from typing import List, Optional
import duckdb

class ParquetDataReader:
    """Lecteur de données Parquet avec fallback DuckDB"""
    
    def __init__(self):
        self.minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
        self.minio_access_key = os.getenv("MINIO_ACCESS_KEY", "cryptoviz")
        self.minio_secret_key = os.getenv("MINIO_SECRET_KEY", "cryptoviz2024")
        
        # Client S3 pour MinIO
        self.s3_client = boto3.client(
            's3',
            endpoint_url=self.minio_endpoint,
            aws_access_key_id=self.minio_access_key,
            aws_secret_access_key=self.minio_secret_key
        )
    
    def read_latest_data(self, limit: int = 100) -> pd.DataFrame:
        """Lit les dernières données disponibles"""
        try:
            # Lister tous les fichiers Parquet
            response = self.s3_client.list_objects_v2(
                Bucket='crypto-data',
                Prefix='part-'  # Fichiers Spark
            )
            
            dataframes = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('.parquet') and obj['Size'] > 0:
                        try:
                            parquet_obj = self.s3_client.get_object(
                                Bucket='crypto-data',
                                Key=obj['Key']
                            )
                            df = pd.read_parquet(parquet_obj['Body'])
                            dataframes.append(df)
                            
                            if len(dataframes) >= 10:
                                break
                                
                        except Exception as e:
                            continue
            
            if dataframes:
                combined_df = pd.concat(dataframes, ignore_index=True)
                if 'timestamp' in combined_df.columns:
                    combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
                    combined_df = combined_df.sort_values('timestamp', ascending=False)
                return combined_df.head(limit)
            else:
                return pd.DataFrame()
                
        except Exception as e:
            st.error(f"Erreur lecture Parquet: {e}")
            return pd.DataFrame()
    
    def get_available_dates(self) -> List[str]:
        """Récupère les dates disponibles"""
        try:
            from datetime import datetime
            return [datetime.now().strftime('%Y-%m-%d')]
        except Exception:
            return []
    
    def get_available_cryptos(self, date_filter: Optional[str] = None) -> List[str]:
        """Récupère les cryptos disponibles"""
        try:
            data = self.read_latest_data(limit=100)
            if not data.empty and 'name' in data.columns:
                return sorted(data['name'].unique().tolist())
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
            return self.read_latest_data()
        else:
            return self.fallback_to_duckdb()

@st.cache_resource(ttl=300)
def get_data_reader():
    """Factory avec cache pour le reader"""
    return ParquetDataReader()
