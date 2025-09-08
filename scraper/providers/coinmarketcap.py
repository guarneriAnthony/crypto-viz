"""
Provider pour l'API CoinMarketCap
"""
import os
from typing import List, Dict
from .base import BaseProvider

class CoinMarketCapProvider(BaseProvider):    
    def __init__(self):
        api_key = os.getenv("COINMARKETCAP_API_KEY", "your-api-key-here")
        super().__init__(
            name="CoinMarketCap",
            base_url="https://pro-api.coinmarketcap.com/v1",
            api_key=api_key
        )
        self.min_request_interval = 2.0  
    
    def get_crypto_data(self) -> List[Dict]:
        """
        Récupère le top 10 des cryptomonnaies depuis CoinMarketCap
        
        Returns:
            List[Dict]: Liste des cryptos avec format unifié
        """
        url = f"{self.base_url}/cryptocurrency/listings/latest"
        
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.api_key,
        }
        
        params = {
            'start': '1',
            'limit': '10',
            'convert': 'USD'
        }
        
        print(f" Récupération depuis {self.name}...", flush=True)
        data = self._make_request(url, params=params, headers=headers)
        
        if not data or 'data' not in data:
            print(f"❌ Pas de données reçues de {self.name}", flush=True)
            return []
        
        crypto_list = []
        for crypto in data.get('data', []):
            try:
                crypto_item = {
                    'name': crypto.get('name', ''),
                    'symbol': crypto.get('symbol', ''),
                    'price': crypto.get('quote', {}).get('USD', {}).get('price', 0),
                    'percent_change_24h': crypto.get('quote', {}).get('USD', {}).get('percent_change_24h', 0),
                    'market_cap': crypto.get('quote', {}).get('USD', {}).get('market_cap', 0),
                    'source': self.get_source_name(),
                    'timestamp': self._format_timestamp()
                }
                crypto_list.append(crypto_item)
                print(f"✅ {self.name}: {crypto_item['name']} - ${crypto_item['price']:.2f}", flush=True)
                
            except Exception as e:
                print(f"⚠️ Erreur parsing {self.name} pour {crypto.get('name', 'unknown')}: {e}", flush=True)
                continue
        
        print(f" {self.name}: {len(crypto_list)} cryptos récupérées", flush=True)
        return crypto_list
    
    def get_source_name(self) -> str:
        """
        Retourne l'identifiant de source
        
        Returns:
            str: 'coinmarketcap'
        """
        return 'coinmarketcap'
