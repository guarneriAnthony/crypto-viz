from typing import List, Dict
from .base import BaseProvider

class CoinGeckoProvider(BaseProvider):
    """
    Provider pour récupérer les données depuis CoinGecko API 
    """
    
    def __init__(self):
        super().__init__(
            name="CoinGecko",
            base_url="https://api.coingecko.com/api/v3",
            api_key=None
        )
        self.min_request_interval = 1.5
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_crypto_data(self) -> List[Dict]:
        """
        Récupère les cryptomonnaies depuis CoinGecko avec format unifié
        
        Returns:
            List[Dict]: Liste des cryptos avec format unifié
        """
        url = f"{self.base_url}/coins/markets"
        
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': '10',
            'page': '1',
            'sparkline': 'false',
            'price_change_percentage': '24h'
        }
        self.timeout = 20
        
        print(f" Récupération depuis {self.name}...", flush=True)
        data = self._make_request(url, params=params)
        
        if not data or not isinstance(data, list):
            print(f"❌ Pas de données reçues de {self.name}", flush=True)
            return []
        
        # SOLUTION 1: Mapping basé sur les IDs CoinGecko (plus fiable)
        crypto_id_mapping = {
            'bitcoin': 'Bitcoin',
            'ethereum': 'Ethereum',
            'binancecoin': 'Binance Coin',
            'solana': 'Solana',
            'ripple': 'Ripple',
            'cardano': 'Cardano',
            'dogecoin': 'Dogecoin',
            'polygon': 'Polygon',
            'litecoin': 'Litecoin',
            'avalanche-2': 'Avalanche'
        }
        
        # SOLUTION 2: Mapping basé sur les symbols (alternative)
        crypto_symbol_mapping = {
            'btc': 'Bitcoin',
            'eth': 'Ethereum', 
            'bnb': 'Binance Coin',
            'sol': 'Solana',
            'xrp': 'Ripple',
            'ada': 'Cardano',
            'doge': 'Dogecoin',
            'matic': 'Polygon',
            'ltc': 'Litecoin',
            'avax': 'Avalanche'
        }
        
        crypto_list = []
        for crypto in data:
            try:
                # Utilisation de l'ID pour plus de fiabilité
                crypto_id = crypto.get('id', '').lower()
                symbol = crypto.get('symbol', '').upper()
                
                # Vérifier d'abord par ID (plus fiable)
                if crypto_id in crypto_id_mapping:
                    crypto_name = crypto_id_mapping[crypto_id]
                # Sinon essayer par symbol en backup
                elif symbol.lower() in crypto_symbol_mapping:
                    crypto_name = crypto_symbol_mapping[symbol.lower()]
                else:
                    # Si aucun mapping, prendre les 5 premiers du top 10 par défaut
                    if len(crypto_list) < 5:
                        crypto_name = crypto.get('name', 'Unknown')
                    else:
                        continue
                
                crypto_item = {
                    'name': crypto_name,
                    'symbol': symbol,
                    'price': crypto.get('current_price', 0),
                    'percent_change_24h': crypto.get('price_change_percentage_24h', 0),
                    'market_cap': crypto.get('market_cap', 0),
                    'source': self.get_source_name(),
                    'timestamp': self._format_timestamp()
                }
                
                crypto_list.append(crypto_item)
                print(f"✅ {self.name}: {crypto_item['name']} ({crypto_item['symbol']}) - ${crypto_item['price']:.2f}", flush=True)
                
            except Exception as e:
                print(f"⚠️ Erreur parsing {self.name} pour {crypto.get('id', 'unknown')}: {e}", flush=True)
                continue
        
        print(f" {self.name}: {len(crypto_list)} cryptos récupérées", flush=True)
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