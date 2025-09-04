#!/usr/bin/env python3
"""
Consumer batch simple pour recréer DuckDB
"""
import os
import json
import time
import duckdb
from kafka import KafkaConsumer
from datetime import datetime

def setup_duckdb():
    """Créer table DuckDB"""
    conn = duckdb.connect('data/crypto_analytics.duckdb')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS crypto_prices (
            name VARCHAR,
            symbol VARCHAR,
            price DOUBLE,
            market_cap DOUBLE,
            volume_24h DOUBLE,
            change_1h DOUBLE,
            change_24h DOUBLE,
            change_7d DOUBLE,
            source VARCHAR,
            timestamp TIMESTAMP,
            ingestion_timestamp TIMESTAMP
        )
    """)
    conn.close()

def consume_and_store():
    """Consommer Redpanda et stocker dans DuckDB"""
    consumer = KafkaConsumer(
        'crypto-raw-data',
        bootstrap_servers=['redpanda:9092'],
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        consumer_timeout_ms=5000  # 5s timeout
    )
    
    conn = duckdb.connect('data/crypto_analytics.duckdb')
    
    count = 0
    for message in consumer:
        try:
            data = message.value
            
            conn.execute("""
                INSERT INTO crypto_prices VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name', ''),
                data.get('symbol', ''),
                float(data.get('price', 0)),
                float(data.get('market_cap', 0)),
                float(data.get('volume_24h', 0)),
                float(data.get('change_1h', 0)),
                float(data.get('change_24h', 0)),
                float(data.get('change_7d', 0)),
                data.get('source', ''),
                data.get('timestamp', ''),
                data.get('ingestion_timestamp', '')
            ))
            
            count += 1
            print(f"✅ {data['name']} ({data['source']}) - ${data['price']}")
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
    
    conn.close()
    print(f"📊 {count} records traités")

if __name__ == "__main__":
    print("🔄 Setup DuckDB...")
    setup_duckdb()
    
    print("📡 Consommation Redpanda...")
    consume_and_store()
    
    print("✅ Consumer batch terminé")
