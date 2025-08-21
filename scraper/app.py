import time
import redis
import requests
import json
import os

redis_client = redis.Redis(host="redis", port=6379, db=0)
QUEUE_NAME = "crypto_data"
API_KEY = os.getenv("COINMARKETCAP_API_KEY", "your-api-key-here")  # Ton API key
BASE_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency"

def get_crypto_data():
    """
    Récupère les données crypto via l'API CoinMarketCap
    """
    try:
        url = f"{BASE_URL}/listings/latest"
        
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': API_KEY,
        }
        
        parameters = {
            'start': '1',
            'limit': '10',  
            'convert': 'USD'
        }
        
        response = requests.get(url, headers=headers, params=parameters)
        data = response.json()
        
        crypto_list = []
        for crypto in data.get('data', []):
            crypto_item = {
                'name': crypto.get('name', ''),
                'symbol': crypto.get('symbol', ''),
                'price': crypto.get('quote', {}).get('USD', {}).get('price', 0),
                'percent_change_24h': crypto.get('quote', {}).get('USD', {}).get('percent_change_24h', 0),
                'market_cap': crypto.get('quote', {}).get('USD', {}).get('market_cap', 0),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            crypto_list.append(crypto_item)
            print(f"Récupéré: {crypto_item['name']} - ${crypto_item['price']}", flush=True)

        return crypto_list

    except Exception as e:
        print(f"Erreur lors de l'appel API: {e}", flush=True)
        return []

def main():
    """Boucle principale"""
    print("Le scraper CryptoViz (CoinMarketCap API) est démarré...", flush=True)
    while True:
        crypto_data = get_crypto_data()
        for item in crypto_data:
            redis_client.lpush(QUEUE_NAME, json.dumps(item))
        time.sleep(300)  

if __name__ == "__main__":
    main()