import time
import redis
import requests
import json
import os

redis_client = redis.Redis(host="redis", port=6379, db=0)
QUEUE_NAME = "crypto_data"
PUBSUB_CHANNEL = "crypto_updates"
API_KEY = os.getenv("COINMARKETCAP_API_KEY", "your-api-key-here")
BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency"

def get_crypto_data():
    """
    Récupère les données crypto avec debug détaillé
    """
    try:
        url = f"{BASE_URL}/listings/latest"
        
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': API_KEY,
        }
        
        parameters = {
            'start': '1',
            'limit': '5',  # Réduire à 5 pour debug
            'convert': 'USD'
        }
        
        print(f"🔗 URL: {url}", flush=True)
        print(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-8:]}", flush=True)
        print(f"📋 Params: {parameters}", flush=True)
        
        response = requests.get(url, headers=headers, params=parameters)
        
        print(f"📊 Status HTTP: {response.status_code}", flush=True)
        print(f"📊 Headers: {dict(response.headers)}", flush=True)
        
        if response.status_code != 200:
            print(f"❌ Erreur HTTP: {response.text}", flush=True)
            return []
        
        data = response.json()
        print(f"📊 Réponse JSON clés: {list(data.keys())}", flush=True)
        
        if 'status' in data:
            status = data['status']
            print(f"📊 API Status: {status.get('error_code', 'unknown')}", flush=True)
            if status.get('error_message'):
                print(f"❌ API Error: {status['error_message']}", flush=True)
                return []
        
        if 'data' not in data:
            print(f"❌ Pas de 'data' dans la réponse: {data}", flush=True)
            return []
            
        crypto_data = data.get('data', [])
        print(f"📊 Nombre de cryptos reçues: {len(crypto_data)}", flush=True)
        
        if not crypto_data:
            print(f"❌ Liste vide reçue de l'API", flush=True)
            return []
        
        # Debug première crypto
        if crypto_data:
            first_crypto = crypto_data[0]
            print(f"🔍 Première crypto clés: {list(first_crypto.keys())}", flush=True)
            print(f"🔍 Name: {first_crypto.get('name')}", flush=True)
            print(f"🔍 Quote keys: {list(first_crypto.get('quote', {}).keys())}", flush=True)
        
        crypto_list = []
        for crypto in crypto_data:
            try:
                quote_usd = crypto.get('quote', {}).get('USD', {})
                crypto_item = {
                    'name': crypto.get('name', ''),
                    'symbol': crypto.get('symbol', ''),
                    'price': quote_usd.get('price', 0),
                    'percent_change_24h': quote_usd.get('percent_change_24h', 0),
                    'market_cap': quote_usd.get('market_cap', 0),
                    'source': 'coinmarketcap',
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                crypto_list.append(crypto_item)
                print(f"✅ Traité: {crypto_item['name']} - ${crypto_item['price']:.2f}", flush=True)
                
            except Exception as e:
                print(f"❌ Erreur traitement crypto: {e}", flush=True)
                continue

        print(f"✅ {len(crypto_list)} cryptos traitées avec succès", flush=True)
        return crypto_list

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur réseau: {e}", flush=True)
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Erreur JSON: {e}", flush=True)
        print(f"❌ Réponse brute: {response.text[:500]}", flush=True)
        return []
    except Exception as e:
        print(f"❌ Erreur générale: {e}", flush=True)
        return []

def publish_dual(crypto_data):
    """Publication duale avec debug"""
    if not crypto_data:
        print("⚠️ Aucune donnée à publier", flush=True)
        return
    
    print(f"📡 Publication de {len(crypto_data)} éléments...", flush=True)
    
    queue_success = 0
    pubsub_success = 0
    
    for item in crypto_data:
        json_data = json.dumps(item)
        
        try:
            # Queue
            redis_client.lpush(QUEUE_NAME, json_data)
            queue_success += 1
            
            # Pub/Sub
            subscribers = redis_client.publish(PUBSUB_CHANNEL, json_data)
            pubsub_success += 1
            
            print(f"📡 {item['name']}: Queue ✅ | Stream ✅ ({subscribers} abonnés)", flush=True)
            
        except Exception as e:
            print(f"❌ Erreur publication {item['name']}: {e}", flush=True)
    
    print(f"✅ Publication terminée: {queue_success} queue, {pubsub_success} streaming", flush=True)

def main():
    """Boucle principale avec debug"""
    print("🚀 Scraper CryptoViz (Version Debug) démarré...", flush=True)
    print(f"📊 API: {BASE_URL}", flush=True)
    print(f"🔑 API Key: {API_KEY[:8]}...{API_KEY[-8:]}", flush=True)
    print(f"🔄 Queue: {QUEUE_NAME}", flush=True)
    print(f"📡 Pub/Sub: {PUBSUB_CHANNEL}", flush=True)
    
    # Test Redis
    try:
        redis_client.ping()
        print("✅ Redis connecté", flush=True)
    except Exception as e:
        print(f"❌ Redis erreur: {e}", flush=True)
        return
    
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n{'='*60}", flush=True)
        print(f"🔄 CYCLE {cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"{'='*60}", flush=True)
        
        try:
            crypto_data = get_crypto_data()
            
            if crypto_data:
                publish_dual(crypto_data)
            else:
                print("❌ CYCLE ÉCHOUÉ - Aucune donnée récupérée", flush=True)
                
        except Exception as e:
            print(f"❌ ERREUR CYCLE {cycle}: {e}", flush=True)
        
        # Attente plus courte pour debug (2 minutes)
        wait_time = 120
        next_time = time.strftime('%H:%M:%S', time.localtime(time.time() + wait_time))
        print(f"⏳ Pause {wait_time//60}min... (prochain: {next_time})", flush=True)
        time.sleep(wait_time)

if __name__ == "__main__":
    main()