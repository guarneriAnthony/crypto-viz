import json
import duckdb
import time
import os
import threading
from datetime import datetime, timedelta
from kafka import KafkaConsumer
from kafka.errors import CommitFailedError, KafkaError

def check_table_structure():
    """Vérifie et affiche la structure de la table"""
    try:
        conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=True)
        
        # Vérifier si la table existe
        tables = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'crypto_prices'").fetchone()
        
        if not tables or tables[0] == 0:
            print("⚠️ Table crypto_prices n'existe pas encore", flush=True)
            conn.close()
            return None
            
        # Obtenir la structure
        structure = conn.execute("DESCRIBE crypto_prices").fetchall()
        print("📊 Structure actuelle de la table:", flush=True)
        for i, (name, type_info, null_info, key, default, extra) in enumerate(structure):
            print(f"   {i+1}. {name} ({type_info})", flush=True)
        
        conn.close()
        return [col[0] for col in structure]  # Retourner les noms des colonnes
        
    except Exception as e:
        print(f"❌ Erreur inspection table: {e}", flush=True)
        return None

def init_database():
    """Initialise la base de données - compatible avec table existante"""
    try:
        conn = duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=False)
        
        # Vérifier la structure existante
        existing_columns = check_table_structure()
        
        if existing_columns is None:
            # Table n'existe pas - créer la version standard
            print("🆕 Création nouvelle table crypto_prices", flush=True)
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
        else:
            print(f"✅ Table existante trouvée avec {len(existing_columns)} colonnes", flush=True)
            
            # Ajouter les nouvelles colonnes si elles n'existent pas
            new_columns = [
                ('ingestion_timestamp', 'TIMESTAMP'),
                ('producer_id', 'VARCHAR'),
                ('schema_version', 'VARCHAR')
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        conn.execute(f"ALTER TABLE crypto_prices ADD COLUMN {col_name} {col_type}")
                        print(f"✅ Colonne {col_name} ajoutée", flush=True)
                    except Exception as e:
                        print(f"⚠️ Erreur ajout colonne {col_name}: {e}", flush=True)
        
        conn.close()
        print("✅ Base de données initialisée", flush=True)
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation DB: {e}", flush=True)
        return False

def cleanup_old_data_simple():
    """Nettoyage simple - garde 7 jours"""
    try:
        print("🧹 Nettoyage automatique des données...", flush=True)
        conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=False)
        
        cutoff_date = datetime.now() - timedelta(days=7)
        before_count = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        
        conn.execute("DELETE FROM crypto_prices WHERE timestamp < ?", [cutoff_date])
        conn.execute("VACUUM")
        
        after_count = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        conn.close()
        
        print(f"✅ Nettoyage: {before_count - after_count:,} enregistrements supprimés", flush=True)
        return True
        
    except Exception as e:
        print(f"❌ Erreur nettoyage: {e}", flush=True)
        return False

def start_cleanup_scheduler():
    """Lance le nettoyage automatique"""
    def cleanup_worker():
        last_cleanup = time.time()
        while True:
            if time.time() - last_cleanup > 6 * 3600:  # 6 heures
                cleanup_old_data_simple()
                last_cleanup = time.time()
            time.sleep(3600)
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    print("📅 Nettoyage automatique activé (toutes les 6h)", flush=True)

class RedpandaCryptoConsumer:
    """Consumer Redpanda pour traitement batch des données crypto"""
    
    def __init__(self):
        brokers = os.getenv("REDPANDA_BROKERS", "redpanda:9092")
        
        # Configuration Kafka Consumer
        self.consumer = KafkaConsumer(
            'crypto-raw-data',  # Topic pour batch processing
            bootstrap_servers=[brokers],
            group_id='crypto-batch-consumer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda m: m.decode('utf-8') if m else None,
            auto_offset_reset='latest',  # Commencer par les nouveaux messages
            enable_auto_commit=False,    # Commit manuel pour plus de contrôle
            max_poll_records=10,         # Traiter 10 messages à la fois
            consumer_timeout_ms=30000     # Timeout 5s
        )
        
        print("✅ Redpanda Consumer initialisé", flush=True)
        print(f"📡 Brokers: {brokers}", flush=True)
        print(f"📊 Topic: crypto-raw-data", flush=True)
        print(f"👥 Group ID: crypto-batch-consumer", flush=True)

    def process_batch(self, crypto_batch):
        """Traite un lot de données avec support des nouvelles colonnes"""
        if not crypto_batch:
            return False
        
        retry_count = 3
        for attempt in range(retry_count):
            try:
                if attempt > 0:
                    wait_time = 2 ** attempt
                    print(f"⏳ Attente {wait_time}s avant tentative {attempt + 1}...", flush=True)
                    time.sleep(wait_time)
                
                conn = duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=False)
                conn.begin()
                
                # Préparer les données avec toutes les colonnes
                insert_data = []
                for crypto_item in crypto_batch:
                    values = (
                        crypto_item.get('name', ''),
                        crypto_item.get('symbol', ''),
                        crypto_item.get('price', 0),
                        crypto_item.get('percent_change_24h', 0),
                        crypto_item.get('market_cap', 0),
                        crypto_item.get('source', 'unknown'),
                        crypto_item.get('timestamp', datetime.now().isoformat()),
                        crypto_item.get('ingestion_timestamp', datetime.now().isoformat()),
                        crypto_item.get('producer_id', 'unknown'),
                        crypto_item.get('schema_version', '1.0')
                    )
                    insert_data.append(values)
                
                # Insertion avec toutes les colonnes
                conn.executemany("""
                    INSERT INTO crypto_prices (
                        name, symbol, price, percent_change_24h, market_cap, 
                        source, timestamp, ingestion_timestamp, producer_id, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, insert_data)
                
                conn.commit()
                conn.close()
                
                print(f"✅ Batch de {len(crypto_batch)} enregistrements traités", flush=True)
                return True
                
            except Exception as e:
                print(f"❌ Tentative {attempt + 1}/{retry_count} - Erreur: {e}", flush=True)
                try:
                    conn.rollback()
                    conn.close()
                except:
                    pass
                    
                if attempt < retry_count - 1:
                    time.sleep(1 + attempt)
                else:
                    print(f"🔥 Échec définitif du batch", flush=True)
                    return False

    def consume_messages(self):
        """Boucle principale de consommation des messages"""
        batch = []
        batch_size = 10
        last_commit_time = time.time()
        
        print("📥 En attente des messages Redpanda...", flush=True)
        
        try:
            for message in self.consumer:
                try:
                    # Décoder le message
                    crypto_data = message.value
                    
                    # Ajouter au batch
                    batch.append(crypto_data)
                    
                    print(f"📥 Batch +1: {crypto_data.get('name', 'Unknown')} ({len(batch)}/{batch_size})", flush=True)
                    
                    # Traiter le batch si plein ou timeout
                    if len(batch) >= batch_size or (time.time() - last_commit_time) > 30:
                        print(f"🔄 Traitement batch de {len(batch)} éléments...", flush=True)
                        
                        if self.process_batch(batch):
                            # Commit les offsets après succès
                            self.consumer.commit()
                            batch = []
                            last_commit_time = time.time()
                            print(f"✅ Batch traité et commité", flush=True)
                        else:
                            # En cas d'échec, garder la moitié du batch
                            batch = batch[-batch_size//2:] if len(batch) > batch_size//2 else []
                            print(f"⚠️ Échec batch, conservation de {len(batch)} éléments", flush=True)
                    
                except Exception as e:
                    print(f"❌ Erreur traitement message: {e}", flush=True)
                    continue
                    
        except KeyboardInterrupt:
            print("🛑 Arrêt demandé par l'utilisateur", flush=True)
        except Exception as e:
            print(f"❌ Erreur consumer: {e}", flush=True)
        finally:
            # Traiter le batch restant
            if batch:
                print(f"🔄 Traitement du batch final ({len(batch)} éléments)...", flush=True)
                self.process_batch(batch)
                self.consumer.commit()
            
            print("🔒 Fermeture du consumer", flush=True)
            self.consumer.close()

def main():
    """Fonction principale"""
    print("🚀 Consumer Redpanda avec détection automatique de structure démarré...", flush=True)
    
    # Attendre que Redpanda soit disponible
    print("⏳ Attente de la disponibilité Redpanda...", flush=True)
    time.sleep(15)
    
    # Initialiser la base
    for attempt in range(3):
        if init_database():
            break
        print(f"Tentative d'initialisation {attempt + 1}/3 échouée, retry dans 3s...", flush=True)
        time.sleep(3)
    else:
        print("🔥 Impossible d'initialiser la base de données", flush=True)
        return
    
    # Démarrer le nettoyage automatique
    start_cleanup_scheduler()
    
    # Créer et lancer le consumer
    consumer = RedpandaCryptoConsumer()
    consumer.consume_messages()

if __name__ == "__main__":
    main()
