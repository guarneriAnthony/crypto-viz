import redis
import json
import duckdb
import time
from datetime import datetime, timedelta
import os
import threading

# Configuration Redis
redis_client = redis.Redis(host="redis", port=6379, db=0)
QUEUE_NAME = "crypto_data"

def check_table_structure():
    """Vérifie et affiche la structure de la table"""
    try:
        conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=True)
        
        # Vérifier si la table existe
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='crypto_prices'").fetchall()
        
        if not tables:
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
                    timestamp TIMESTAMP
                )
            """)
        else:
            print(f"✅ Table existante trouvée avec {len(existing_columns)} colonnes", flush=True)
        
        conn.close()
        print("✅ Base de données initialisée", flush=True)
        return True
        
    except Exception as e:
        print(f"❌ Erreur d'initialisation DB: {e}", flush=True)
        return False

def get_insert_query():
    """Génère la requête d'insertion adaptée à la structure de table"""
    try:
        conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=True)
        structure = conn.execute("DESCRIBE crypto_prices").fetchall()
        conn.close()
        
        columns = [col[0] for col in structure]
        print(f"📝 Colonnes détectées: {columns}", flush=True)
        
        # Vérifier si on a un ID auto-incrémenté
        if 'id' in [col.lower() for col in columns]:
            # Table avec ID - exclure l'ID de l'insertion
            non_id_columns = [col for col in columns if col.lower() != 'id']
            placeholders = ', '.join(['?' for _ in non_id_columns])
            column_names = ', '.join(non_id_columns)
            query = f"INSERT INTO crypto_prices ({column_names}) VALUES ({placeholders})"
            print(f"🔧 Mode ID auto: INSERT INTO crypto_prices ({column_names}) VALUES ({placeholders})", flush=True)
        else:
            # Table standard - insérer toutes les colonnes
            placeholders = ', '.join(['?' for _ in columns])
            query = f"INSERT INTO crypto_prices VALUES ({placeholders})"
            print(f"🔧 Mode standard: INSERT INTO crypto_prices VALUES ({placeholders})", flush=True)
            
        return query, columns
        
    except Exception as e:
        print(f"❌ Erreur génération requête: {e}", flush=True)
        # Fallback sur requête standard
        return "INSERT INTO crypto_prices VALUES (?, ?, ?, ?, ?, ?)", ['name', 'symbol', 'price', 'percent_change_24h', 'market_cap', 'timestamp']

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

def process_batch(data_batch):
    """Traite un lot de données - adapté à la structure avec colonne source"""
    if not data_batch:
        return False
    
    retry_count = 3
    for attempt in range(retry_count):
        try:
            conn = duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=False)
            conn.begin()
            
            # Préparer les données avec la colonne source
            insert_data = []
            for crypto_item in data_batch:
                # Ordre exact des colonnes : name, symbol, price, percent_change_24h, market_cap, source, timestamp
                values = (
                    crypto_item['name'],
                    crypto_item['symbol'],
                    crypto_item['price'],
                    crypto_item['percent_change_24h'],
                    crypto_item['market_cap'],
                    'coinmarketcap',  # NOUVELLE colonne source
                    crypto_item['timestamp']
                )
                insert_data.append(values)
            
            # Insertion avec toutes les 7 colonnes
            conn.executemany("""
                INSERT INTO crypto_prices (name, symbol, price, percent_change_24h, market_cap, source, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, insert_data)
            
            conn.commit()
            conn.close()
            
            print(f"✅ Batch de {len(data_batch)} enregistrements traités (source: coinmarketcap)", flush=True)
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
                print(f"🔍 Debug - Query: {insert_query}", flush=True)
                print(f"🔍 Debug - Colonnes: {columns}", flush=True)
                print(f"🔍 Debug - Exemple data: {data_batch[0] if data_batch else 'None'}", flush=True)
                return False

def process_data():
    """Fonction principale"""
    print("🚀 Consumer avec détection automatique de structure démarré...", flush=True)
    
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
    
    batch = []
    batch_size = 10
    last_batch_time = time.time()
    
    print("📥 En attente des données Redis...", flush=True)
    
    while True:
        try:
            data = redis_client.brpop(QUEUE_NAME, timeout=5)
            
            if data:
                crypto_item = json.loads(data[1])
                batch.append(crypto_item)
                print(f"📥 Batch +1: {crypto_item['name']} ({len(batch)}/{batch_size})", flush=True)
                
                if len(batch) >= batch_size or (time.time() - last_batch_time) > 30:
                    print(f"🔄 Traitement batch de {len(batch)} éléments...", flush=True)
                    if process_batch(batch):
                        batch = []
                        last_batch_time = time.time()
                    else:
                        batch = batch[-batch_size//2:] if len(batch) > batch_size//2 else batch
                        print(f"⚠️ Échec batch, conservation de {len(batch)} éléments", flush=True)
                        
            else:
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