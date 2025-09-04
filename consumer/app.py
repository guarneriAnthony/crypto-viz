import json
import duckdb
import time
import os
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError

def init_database():
    """Initialise la base de données"""
    try:
        conn = duckdb.connect('/data/crypto_analytics.duckdb')
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                name VARCHAR,
                symbol VARCHAR,
                price DOUBLE,
                percent_change_24h DOUBLE,
                market_cap DOUBLE,
                source VARCHAR,
                timestamp TIMESTAMP,
                ingestion_timestamp TIMESTAMP,
                producer_id VARCHAR,
                schema_version VARCHAR
            )
        """)
        
        conn.close()
        print("✅ Base de données initialisée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation DB: {e}")
        return False

def main():
    """Fonction principale simplifiée"""
    print("🚀 Consumer Redpanda Simple démarré...")
    
    # Attendre Redpanda
    time.sleep(15)
    
    # Initialiser la base
    if not init_database():
        print("🔥 Impossible d'initialiser la base")
        return
    
    # Configuration consumer
    brokers = os.getenv("REDPANDA_BROKERS", "redpanda:9092")
    
    try:
        consumer = KafkaConsumer(
            'crypto-raw-data',
            bootstrap_servers=[brokers],
            group_id='crypto-batch-consumer-simple',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            enable_auto_commit=True,  # Auto commit pour simplifier
            max_poll_records=5
        )
        
        print("✅ Consumer Redpanda connecté")
        print("📥 En attente des messages...")
        
        message_count = 0
        batch = []
        
        for message in consumer:
            try:
                crypto_data = message.value
                batch.append(crypto_data)
                message_count += 1
                
                print(f"📥 Message {message_count}: {crypto_data.get('name', 'Unknown')} - ${crypto_data.get('price', 0):.2f}")
                
                # Traiter par batch de 5
                if len(batch) >= 5:
                    print(f"🔄 Traitement batch de {len(batch)} messages...")
                    
                    # Insérer en base
                    try:
                        conn = duckdb.connect('/data/crypto_analytics.duckdb')
                        
                        for item in batch:
                            conn.execute("""
                                INSERT INTO crypto_prices (
                                    name, symbol, price, percent_change_24h, market_cap, 
                                    source, timestamp, ingestion_timestamp, producer_id, schema_version
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                item.get('name', ''),
                                item.get('symbol', ''),
                                item.get('price', 0),
                                item.get('percent_change_24h', 0),
                                item.get('market_cap', 0),
                                item.get('source', 'unknown'),
                                item.get('timestamp'),
                                item.get('ingestion_timestamp'),
                                item.get('producer_id', 'unknown'),
                                item.get('schema_version', '2.0')
                            ))
                        
                        conn.close()
                        print(f"✅ Batch de {len(batch)} enregistrements sauvegardé")
                        batch = []
                        
                    except Exception as e:
                        print(f"❌ Erreur sauvegarde: {e}")
                        
            except Exception as e:
                print(f"❌ Erreur traitement message: {e}")
                continue
                
    except KeyboardInterrupt:
        print("🛑 Arrêt demandé")
    except Exception as e:
        print(f"❌ Erreur consumer: {e}")
    finally:
        try:
            consumer.close()
        except:
            pass
        print("🔒 Consumer fermé")

if __name__ == "__main__":
    main()
