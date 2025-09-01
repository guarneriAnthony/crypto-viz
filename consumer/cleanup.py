import duckdb
import logging
from datetime import datetime, timedelta
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_old_data(retention_days=7):
    """
    Supprime les données plus anciennes que X jours
    Garde seulement 1 point par heure pour les données > 24h
    """
    try:
        conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=False)
        
        # 1. Compter les enregistrements avant
        before_count = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        
        # 2. Supprimer les données très anciennes (> retention_days)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        conn.execute("""
            DELETE FROM crypto_prices 
            WHERE timestamp < ?
        """, [cutoff_date])
        
        # 3. Échantillonner les données anciennes (garde 1 point/heure pour > 24h)
        yesterday = datetime.now() - timedelta(days=1)
        
        # Cette requête garde seulement le premier enregistrement de chaque heure
        conn.execute("""
            DELETE FROM crypto_prices 
            WHERE timestamp < ? 
            AND ROWID NOT IN (
                SELECT MIN(ROWID)
                FROM crypto_prices
                WHERE timestamp < ?
                GROUP BY name, 
                         EXTRACT(year FROM timestamp),
                         EXTRACT(month FROM timestamp), 
                         EXTRACT(day FROM timestamp),
                         EXTRACT(hour FROM timestamp)
            )
        """, [yesterday, yesterday])
        
        # 4. VACUUM pour récupérer l'espace
        conn.execute("VACUUM")
        
        # 5. Statistiques finales
        after_count = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        conn.close()
        
        # 6. Calculer la taille du fichier
        if os.path.exists('/data/crypto_analytics.duckdb'):
            db_size = os.path.getsize('/data/crypto_analytics.duckdb') / 1024 / 1024  # MB
        else:
            db_size = 0
        
        # 7. Affichage des résultats
        logger.info(f"✅ Nettoyage terminé:")
        logger.info(f"   📊 Avant: {before_count:,} enregistrements")
        logger.info(f"   📊 Après: {after_count:,} enregistrements")
        logger.info(f"   🗑️ Supprimés: {before_count - after_count:,}")
        logger.info(f"   💽 Taille DB: {db_size:.1f} MB")
        logger.info(f"   📅 Rétention: {retention_days} jours")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage: {e}")
        return False

def get_database_stats():
    """Affiche des statistiques détaillées de la base"""
    try:
        conn = duckdb.connect('/data/crypto_analytics.duckdb', read_only=True)
        
        # Statistiques générales
        total_records = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        unique_cryptos = conn.execute("SELECT COUNT(DISTINCT name) FROM crypto_prices").fetchone()[0]
        
        # Période des données
        period_result = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM crypto_prices").fetchone()
        min_date, max_date = period_result
        
        # Top 5 cryptos par nombre d'enregistrements
        top_cryptos = conn.execute("""
            SELECT name, COUNT(*) as count 
            FROM crypto_prices 
            GROUP BY name 
            ORDER BY count DESC 
            LIMIT 5
        """).fetchall()
        
        # Données récentes (dernières 24h)
        recent_count = conn.execute("""
            SELECT COUNT(*) FROM crypto_prices 
            WHERE timestamp >= ?
        """, [datetime.now() - timedelta(days=1)]).fetchone()[0]
        
        conn.close()
        
        # Taille du fichier
        if os.path.exists('/data/crypto_analytics.duckdb'):
            db_size = os.path.getsize('/data/crypto_analytics.duckdb') / 1024 / 1024  # MB
        else:
            db_size = 0
        
        print("\n" + "="*60)
        print("📊 STATISTIQUES BASE DE DONNÉES")
        print("="*60)
        print(f"📈 Total enregistrements: {total_records:,}")
        print(f"💰 Cryptomonnaies uniques: {unique_cryptos}")
        print(f"📅 Période: {min_date} → {max_date}")
        print(f"💽 Taille fichier: {db_size:.1f} MB")
        print(f"🕐 Données 24h: {recent_count:,}")
        
        print(f"\n🏆 Top 5 Cryptos:")
        for name, count in top_cryptos:
            print(f"   • {name}: {count:,} records")
            
        print("="*60)
        
        return {
            'total_records': total_records,
            'unique_cryptos': unique_cryptos,
            'db_size_mb': db_size,
            'recent_count': recent_count
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur stats: {e}")
        return None

if __name__ == "__main__":
    print("🧹 CryptoViz - Utilitaire de nettoyage")
    print("Choisissez une action:")
    print("1. Afficher les statistiques")
    print("2. Nettoyage complet (7 jours)")
    print("3. Nettoyage agressif (3 jours)")
    print("4. Nettoyage minimal (14 jours)")
    
    choice = input("Votre choix (1-4): ").strip()
    
    if choice == "1":
        get_database_stats()
    elif choice == "2":
        cleanup_old_data(retention_days=7)
        get_database_stats()
    elif choice == "3":
        cleanup_old_data(retention_days=3)
        get_database_stats()
    elif choice == "4":
        cleanup_old_data(retention_days=14)
        get_database_stats()
    else:
        print("❌ Choix invalide")