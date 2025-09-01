import time
import redis
import json
import os
from providers.coinmarketcap import CoinMarketCapProvider
from providers.coingecko import CoinGeckoProvider

# Configuration Redis
redis_client = redis.Redis(host="redis", port=6379, db=0)
QUEUE_NAME = "crypto_data"
PUBSUB_CHANNEL = "crypto_updates"

def get_crypto_data_from_providers():
    """
    Récupère les données depuis tous les providers configurés
    """
    all_crypto_data = []
    
    # Initialiser les providers
    providers = []
    
    # Provider CoinMarketCap (si API key disponible)
    api_key = os.getenv("COINMARKETCAP_API_KEY", "your-api-key-here")
    if api_key and api_key != "your-api-key-here":
        providers.append(CoinMarketCapProvider())
        print("✅ Provider CoinMarketCap activé", flush=True)
    else:
        print("⚠️ API Key CoinMarketCap manquante, provider désactivé", flush=True)
    
    # Provider CoinGecko (gratuit, toujours disponible)
    providers.append(CoinGeckoProvider())
    print("✅ Provider CoinGecko activé", flush=True)
    
    if not providers:
        print("❌ Aucun provider disponible!", flush=True)
        return []
    
    # Récupérer les données de chaque provider
    for provider in providers:
        try:
            print(f"\n🔄 Récupération depuis {provider.name}...", flush=True)
            
            crypto_data = provider.get_crypto_data()
            
            if crypto_data:
                print(f"✅ {provider.name}: {len(crypto_data)} cryptos récupérées", flush=True)
                
                # Debug : afficher les cryptos récupérées
                for crypto in crypto_data[:3]:  # Afficher les 3 premières
                    print(f"   • {crypto['name']} ({crypto['symbol']}) - ${crypto['price']:.2f} ({crypto['source']})", flush=True)
                if len(crypto_data) > 3:
                    print(f"   • ... et {len(crypto_data) - 3} autres", flush=True)
                
                all_crypto_data.extend(crypto_data)
            else:
                print(f"❌ {provider.name}: Aucune donnée récupérée", flush=True)
                
        except Exception as e:
            print(f"❌ Erreur avec {provider.name}: {e}", flush=True)
            continue
    
    print(f"\n📊 TOTAL: {len(all_crypto_data)} cryptos de tous les providers", flush=True)
    return all_crypto_data

def publish_dual(crypto_data):
    """Publication duale avec debug amélioré"""
    if not crypto_data:
        print("⚠️ Aucune donnée à publier", flush=True)
        return
    
    print(f"📡 Publication de {len(crypto_data)} éléments...", flush=True)
    
    # Grouper par source pour les statistiques
    source_counts = {}
    queue_success = 0
    pubsub_success = 0
    
    for item in crypto_data:
        source = item.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
        
        json_data = json.dumps(item)
        
        try:
            # Queue
            redis_client.lpush(QUEUE_NAME, json_data)
            queue_success += 1
            
            # Pub/Sub
            subscribers = redis_client.publish(PUBSUB_CHANNEL, json_data)
            pubsub_success += 1
            
            print(f"📡 {item['name']} ({source}): Queue ✅ | Stream ✅", flush=True)
            
        except Exception as e:
            print(f"❌ Erreur publication {item['name']}: {e}", flush=True)
    
    # Afficher les statistiques par source
    print(f"\n✅ Publication terminée:")
    print(f"   📊 Queue: {queue_success} éléments")
    print(f"   📡 Streaming: {pubsub_success} éléments")
    print(f"   📈 Par source:")
    for source, count in source_counts.items():
        print(f"      • {source}: {count} cryptos")

def test_providers():
    """Test rapide des providers"""
    print("\n🧪 TEST DES PROVIDERS")
    print("="*50)
    
    # Test CoinGecko
    try:
        cg = CoinGeckoProvider()
        print(f"🔧 Test {cg.name}...")
        data = cg.get_crypto_data()
        print(f"   Résultat: {len(data) if data else 0} cryptos")
        if data:
            print(f"   Exemple: {data[0]['name']} - ${data[0]['price']:.2f}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # Test CoinMarketCap
    api_key = os.getenv("COINMARKETCAP_API_KEY", "your-api-key-here")
    if api_key and api_key != "your-api-key-here":
        try:
            cmc = CoinMarketCapProvider()
            print(f"🔧 Test {cmc.name}...")
            data = cmc.get_crypto_data()
            print(f"   Résultat: {len(data) if data else 0} cryptos")
            if data:
                print(f"   Exemple: {data[0]['name']} - ${data[0]['price']:.2f}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    else:
        print("⚠️ CoinMarketCap: API Key manquante")
    
    print("="*50)

def main():
    """Boucle principale avec support multi-providers"""
    print("🚀 Scraper CryptoViz Multi-Provider démarré...", flush=True)
    print(f"🔄 Queue: {QUEUE_NAME}", flush=True)
    print(f"📡 Pub/Sub: {PUBSUB_CHANNEL}", flush=True)
    
    # Test Redis
    try:
        redis_client.ping()
        print("✅ Redis connecté", flush=True)
    except Exception as e:
        print(f"❌ Redis erreur: {e}", flush=True)
        return
    
    # Test rapide des providers
    test_providers()
    
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n{'='*60}", flush=True)
        print(f"🔄 CYCLE {cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"{'='*60}", flush=True)
        
        try:
            crypto_data = get_crypto_data_from_providers()
            
            if crypto_data:
                publish_dual(crypto_data)
                print(f"✅ CYCLE {cycle} RÉUSSI - {len(crypto_data)} cryptos traitées", flush=True)
            else:
                print("❌ CYCLE ÉCHOUÉ - Aucune donnée récupérée", flush=True)
                
        except Exception as e:
            print(f"❌ ERREUR CYCLE {cycle}: {e}", flush=True)
        
        # Attente entre cycles
        wait_time = 120  # 2 minutes
        next_time = time.strftime('%H:%M:%S', time.localtime(time.time() + wait_time))
        print(f"⏳ Pause {wait_time//60}min... (prochain: {next_time})", flush=True)
        time.sleep(wait_time)

if __name__ == "__main__":
    main()