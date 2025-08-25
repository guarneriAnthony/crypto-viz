"""
Provider pour l'API CoinGecko
"""
from typing import List, Dict
from .base import BaseProvider

class CoinGeckoProvider(BaseProvider):
    """
    Provider pour récupérer les données depuis CoinGecko API (gratuit)
    """
    
    def __init__(self):
        super().__init__(
            name="CoinGecko",
            base_url="https://api.coingecko.com/api/v3",
            api_key=None  # API gratuite, pas de clé nécessaire
        )
        # CoinGecko: 50 appels/minute gratuit = ~1.2s entre les appels
        self.min_request_interval = 1.5
    
    def get_crypto_data(self) -> List[Dict]:
        """
        Récupère le top 10 des cryptomonnaies depuis CoinGecko
        
        Returns:
            List[Dict]: Liste des cryptos avec format unifié
        """
        url = f"{self.base_url}/coins/markets"
        
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': 10,
            'page': 1,
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        
        print(f"🔄 Récupération depuis {self.name}...", flush=True)
        data = self._make_request(url, params=params)
        
        if not data or not isinstance(data, list):
            print(f"❌ Pas de données reçues de {self.name}", flush=True)
            return []
        
        crypto_list = []
        for crypto in data:
            try:
                # Mapping des champs CoinGecko vers notre format unifié
                crypto_item = {
                    'name': crypto.get('name', ''),
                    'symbol': crypto.get('symbol', '').upper(),  # CoinGecko retourne en minuscules
                    'price': crypto.get('current_price', 0),
                    'percent_change_24h': crypto.get('price_change_percentage_24h', 0),
                    'market_cap': crypto.get('market_cap', 0),
                    'source': self.get_source_name(),
                    'timestamp': self._format_timestamp()
                }
                crypto_list.append(crypto_item)
                print(f"✅ {self.name}: {crypto_item['name']} ({crypto_item['symbol']}) - ${crypto_item['price']:.2f}", flush=True)
                
            except Exception as e:
                print(f"⚠️ Erreur parsing {self.name} pour {crypto.get('name', 'unknown')}: {e}", flush=True)
                continue
        
        print(f"📊 {self.name}: {len(crypto_list)} cryptos récupérées", flush=True)
        return crypto_list
    
    def get_source_name(self) -> str:
        """
        Retourne l'identifiant de source
        
        Returns:
            str: 'coingecko'
        """
        return 'coingecko'
    
    def _make_request(self, url: str, params: Dict = None, headers: Dict = None, timeout: int = 10):
        """
        Override pour gestion spécifique des erreurs CoinGecko
        """
        # CoinGecko a parfois des rate limits plus stricts
        response_data = super()._make_request(url, params, headers, timeout)
        
        if response_data is None:
            return None
            
        # CoinGecko peut retourner des erreurs dans le JSON
        if isinstance(response_data, dict) and 'error' in response_data:
            print(f"❌ Erreur API {self.name}: {response_data['error']}", flush=True)
            return None
            
        return response_data
