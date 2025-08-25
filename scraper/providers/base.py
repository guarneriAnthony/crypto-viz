"""
Classe de base abstraite pour tous les providers crypto
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import time
import requests

class BaseProvider(ABC):
    """
    Interface commune pour tous les providers de données crypto
    """
    
    def __init__(self, name: str, base_url: str, api_key: Optional[str] = None):
        self.name = name
        self.base_url = base_url
        self.api_key = api_key
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum 1 seconde entre les requêtes
    
    @abstractmethod
    def get_crypto_data(self) -> List[Dict]:
        """
        Récupère les données crypto depuis l'API
        
        Returns:
            List[Dict]: Liste des cryptomonnaies avec format unifié:
                {
                    'name': str,
                    'symbol': str, 
                    'price': float,
                    'percent_change_24h': float,
                    'market_cap': float,
                    'source': str,
                    'timestamp': str
                }
        """
        pass
    
    @abstractmethod
    def get_source_name(self) -> str:
        """
        Retourne le nom de la source pour identification
        
        Returns:
            str: Nom de la source (ex: 'coinmarketcap', 'coingecko')
        """
        pass
    
    def _rate_limit_wait(self):
        """
        Applique un rate limiting basique entre les requêtes
        """
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            print(f"⏳ Rate limiting: attente {sleep_time:.1f}s pour {self.name}", flush=True)
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict = None, headers: Dict = None, timeout: int = 10) -> Optional[Dict]:
        """
        Effectue une requête HTTP avec gestion d'erreurs commune
        
        Args:
            url: URL de l'API
            params: Paramètres de la requête
            headers: Headers HTTP
            timeout: Timeout en secondes
            
        Returns:
            Dict: Réponse JSON ou None en cas d'erreur
        """
        self._rate_limit_wait()
        
        try:
            response = requests.get(url, params=params or {}, headers=headers or {}, timeout=timeout)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout pour {self.name} après {timeout}s", flush=True)
            return None
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print(f"🚦 Rate limit atteint pour {self.name}, retry dans 60s", flush=True)
                time.sleep(60)
                return None
            else:
                print(f"❌ Erreur HTTP {response.status_code} pour {self.name}: {e}", flush=True)
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"🌐 Erreur réseau pour {self.name}: {e}", flush=True)
            return None
            
        except Exception as e:
            print(f"💥 Erreur inattendue pour {self.name}: {e}", flush=True)
            return None
    
    def _format_timestamp(self) -> str:
        """
        Génère un timestamp unifié
        
        Returns:
            str: Timestamp au format ISO
        """
        return time.strftime('%Y-%m-%d %H:%M:%S')
