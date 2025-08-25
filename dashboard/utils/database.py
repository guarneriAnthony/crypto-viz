"""
Utilitaires partagés pour accéder aux données DuckDB
"""
import duckdb
import pandas as pd
from datetime import datetime

def get_connection():
    """
    Retourne une connexion DuckDB
    🧠 CONCEPT : Centraliser la connexion DB évite la duplication de code
    """
    return duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=True)

def get_crypto_data(crypto_name, hours_back=24, source=None):
    """
    Récupère les données d'une crypto pour les prédictions
    
    Args:
        crypto_name: Nom de la crypto (ex: 'Bitcoin')
        hours_back: Nombre d'heures à récupérer
        source: Source spécifique ou None pour toutes
    
    Returns:
        DataFrame avec colonnes: timestamp, price, source
    
    🧠 CONCEPT : Cette fonction prépare les données pour l'analyse ML
    """
    conn = get_connection()
    
    # Construire la requête SQL
    source_filter = ""
    if source:
        source_filter = f"AND source = '{source}'"
    
    query = f"""
        SELECT timestamp, price, source
        FROM crypto_prices 
        WHERE name = '{crypto_name}'
        AND timestamp >= current_timestamp - INTERVAL {hours_back} hours
        {source_filter}
        ORDER BY timestamp ASC
    """
    
    try:
        df = conn.execute(query).fetchdf()
        conn.close()
        return df
    except Exception as e:
        conn.close()
        print(f"Erreur récupération données: {e}")
        return pd.DataFrame()

def get_available_cryptos():
    """
    Liste des cryptos disponibles avec statistiques
    🧠 CONCEPT : Aide l'utilisateur à choisir quoi analyser
    """
    conn = get_connection()
    
    query = """
        SELECT 
            name,
            COUNT(*) as points,
            MAX(timestamp) as last_update,
            AVG(price) as avg_price
        FROM crypto_prices 
        WHERE timestamp >= current_timestamp - INTERVAL 24 hours
        GROUP BY name
        ORDER BY points DESC
    """
    
    try:
        df = conn.execute(query).fetchdf()
        conn.close()
        return df
    except Exception as e:
        conn.close()
        return pd.DataFrame()
