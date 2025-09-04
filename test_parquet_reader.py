#!/usr/bin/env python3
"""
Test du nouveau ParquetDataReader avec s3fs
"""
import sys
sys.path.append('dashboard-v3/utils')

from parquet_reader_s3fs import ParquetDataReader
import pandas as pd

# Test du reader
print("🔍 Test du nouveau ParquetDataReader avec s3fs...")

try:
    reader = ParquetDataReader()
    print("✅ Reader initialisé")
    
    # Test lecture des données
    data = reader.read_latest_data(limit=20)
    
    if not data.empty:
        print(f"✅ Données récupérées: {data.shape[0]} lignes, {data.shape[1]} colonnes")
        
        if 'name' in data.columns:
            cryptos = sorted(data['name'].unique())
            print(f"🪙 Cryptos trouvées: {cryptos}")
        
        if 'timestamp' in data.columns:
            print(f"📅 Derniers timestamps: {data['timestamp'].max()}")
            
        print("\n📊 Échantillon de données:")
        print(data.head(3).to_string())
        
    else:
        print("❌ Aucune donnée récupérée")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
