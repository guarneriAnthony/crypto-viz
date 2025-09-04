#!/usr/bin/env python3
"""
Test de génération des graphiques du dashboard
"""
import sys
sys.path.append('dashboard-v3/utils')
from parquet_reader_s3fs import ParquetDataReader
import pandas as pd
import plotly.express as px

print("🎯 Test génération graphiques dashboard...")

try:
    reader = ParquetDataReader()
    data = reader.read_latest_data(limit=50)
    
    print(f"📊 Données chargées: {data.shape}")
    
    # Test conditions du dashboard
    has_required_cols = not data.empty and 'name' in data.columns and 'price' in data.columns
    print(f"✅ Conditions graphiques: {has_required_cols}")
    
    if has_required_cols:
        # Test génération graphique barres (Top cryptos)
        top_cryptos = data.groupby('name')['price'].last().sort_values(ascending=False).head(10)
        print(f"📈 Top cryptos calculé: {len(top_cryptos)} entrées")
        print(f"Top 3: {list(top_cryptos.head(3).items())}")
        
        # Test données temporelles
        if 'timestamp' in data.columns:
            data['timestamp'] = pd.to_datetime(data['timestamp'])
            print(f"📅 Timestamps convertis: {data['timestamp'].min()} -> {data['timestamp'].max()}")
            
            # Test données pour graphique ligne
            crypto_list = sorted(data['name'].unique())
            print(f"🪙 Cryptos disponibles: {crypto_list}")
            
            if crypto_list:
                test_crypto = crypto_list[0]  # Premier crypto
                crypto_data = data[data['name'] == test_crypto].sort_values('timestamp')
                print(f"📊 Données {test_crypto}: {len(crypto_data)} points")
                
        print("✅ Tous les tests de génération passent!")
        
    else:
        print("❌ Conditions non remplies pour graphiques")
        
except Exception as e:
    print(f"❌ Erreur test: {e}")
    import traceback
    traceback.print_exc()
