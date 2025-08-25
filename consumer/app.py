import redis
import json
import duckdb
import time
from datetime import datetime
import os

# Configuration Redis
redis_client = redis.Redis(host="redis", port=6379, db=0)
QUEUE_NAME = "crypto_data"

def init_database():
    """Initialise la base de données et la table"""
    try:
        # DuckDB gère automatiquement la concurrence depuis la v0.8+
        conn = duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=False)
        
        # Créer la table si elle n'existe pas avec la colonne source
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crypto_prices (
                name VARCHAR,
                symbol VARCHAR,
                price DOUBLE,
                percent_change_24h DOUBLE,
                market_cap DOUBLE,
                source VARCHAR,
                timestamp TIMESTAMP
            )
        """)
        
        # Ajouter la colonne source si elle n'existe pas (pour la rétrocompatibilité)
        try:
            conn.execute("ALTER TABLE crypto_prices ADD COLUMN source VARCHAR")
            print("ℹ️  Colonne source ajoutée à la table existante", flush=True)
        except Exception as e:
            if 'already exists' in str(e).lower():
                pass  # La colonne existe déjà
            else:
                print(f"⚠️  Erreur lors de l'ajout de la colonne source: {e}", flush=True)
        
        conn.close()
        print("✅ Base de données initialisée", flush=True)
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation DB: {e}", flush=True)
        return False

def process_batch(data_batch):
    """Traite un lot de données avec une seule transaction"""
    if not data_batch:
        return False
        
    retry_count = 3
    for attempt in range(retry_count):
        try:
            conn = duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=False)
            
            # Utiliser une transaction pour l'efficacité
            conn.begin()
            
            # Préparer les données pour insertion en batch
            insert_data = []
            for crypto_item in data_batch:
                insert_data.append((
                    crypto_item['name'],
                    crypto_item['symbol'],
                    crypto_item['price'],
                    crypto_item['percent_change_24h'],
                    crypto_item['market_cap'],
                    crypto_item.get('source', 'coinmarketcap'),  # Par défaut coinmarketcap si pas spécifié
                    crypto_item['timestamp']
                ))
            
            # Insertion en batch plus efficace avec la nouvelle colonne source
            conn.executemany("""
                INSERT INTO crypto_prices 
                (name, symbol, price, percent_change_24h, market_cap, source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, insert_data)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Batch de {len(data_batch)} enregistrements traités", flush=True)
            return True
            
        except Exception as e:
            print(f"❌ Tentative {attempt + 1}/{retry_count} - Erreur: {e}", flush=True)
            try:
                conn.rollback()
                conn.close()
            except:
                pass
                
            if attempt < retry_count - 1:
                time.sleep(1 + attempt)  # Backoff progressif
            else:
                print(f"🔥 Échec définitif du batch après {retry_count} tentatives", flush=True)
                return False

def process_data():
    """Lit les données de Redis et les stocke dans DuckDB"""
    print("🚀 Consumer démarré (avec support multi-sources)...", flush=True)
    
    # Initialiser la base avec plusieurs tentatives
    for attempt in range(3):
        if init_database():
            break
        print(f"Tentative d'initialisation {attempt + 1}/3 échouée, retry dans 3s...", flush=True)
        time.sleep(3)
    else:
        print("🔥 Impossible d'initialiser la base de données, arrêt du consumer", flush=True)
        return
    
    batch = []
    batch_size = 10
    last_batch_time = time.time()
    
    print("📥 En attente des données Redis...", flush=True)
    
    while True:
        try:
            # Récupère une donnée de la queue (avec timeout)
            data = redis_client.brpop(QUEUE_NAME, timeout=5)
            
            if data:
                # Convertit JSON en dictionnaire Python
                crypto_item = json.loads(data[1])
                batch.append(crypto_item)
                source = crypto_item.get('source', 'coinmarketcap')
                print(f"📥 Batch +1: {crypto_item['name']} ({source}) ({len(batch)}/{batch_size})", flush=True)
                
                # Traiter le batch si plein ou si timeout
                if len(batch) >= batch_size or (time.time() - last_batch_time) > 30:
                    print(f"🔄 Traitement batch de {len(batch)} éléments...", flush=True)
                    if process_batch(batch):
                        batch = []
                        last_batch_time = time.time()
                    else:
                        # En cas d'échec, garder seulement les plus récents pour éviter l'accumulation
                        batch = batch[-batch_size//2:] if len(batch) > batch_size//2 else batch
                        print(f"⚠️ Échec batch, conservation de {len(batch)} éléments", flush=True)
                        
            else:
                # Timeout - traiter le batch existant s'il y en a
                if batch:
                    print(f"⏰ Timeout Redis, traitement batch partiel ({len(batch)} items)", flush=True)
                    if process_batch(batch):
                        batch = []
                        last_batch_time = time.time()
                else:
                    print("💤 Aucune nouvelle donnée...", flush=True)
                
        except redis.exceptions.ConnectionError as e:
            print(f"🔌 Erreur connexion Redis: {e}, retry dans 10s...", flush=True)
            time.sleep(10)
        except Exception as e:
            print(f"💥 Erreur dans la boucle principale: {e}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    process_data()
