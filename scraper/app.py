"""
Scraper unifié multi-sources pour données crypto
Supporte CoinMarketCap et CoinGecko
"""
import time
import redis
import json
import os
from typing import List
from providers import CoinMarketCapProvider, CoinGeckoProvider

class UnifiedCryptoScraper:
    """
    Orchestrateur principal qui gère plusieurs sources de données crypto
    """
    
    def __init__(self):
        self.redis_client = redis.Redis(host="redis", port=6379, db=0)
        self.queue_name = "crypto_data"
        self.scraping_interval = 300  # 5 minutes
        
        # Initialiser les providers
        self.providers = []
        
        # Toujours activer CoinMarketCap si API key disponible
        cmc_api_key = os.getenv("COINMARKETCAP_API_KEY", "")
        if cmc_api_key and cmc_api_key != "your-api-key-here":
            self.providers.append(CoinMarketCapProvider())
            print("✅ CoinMarketCap provider activé", flush=True)
        else:
            print("⚠️ CoinMarketCap désactivé (pas d'API key)", flush=True)
        
        # Toujours activer CoinGecko (API gratuite)
        self.providers.append(CoinGeckoProvider())
        print("✅ CoinGecko provider activé", flush=True)
        
        if not self.providers:
            raise Exception("❌ Aucun provider configuré !")
            
        print(f"🚀 {len(self.providers)} provider(s) configuré(s)", flush=True)
    
    def scrape_from_provider(self, provider) -> int:
        """
        Scrape les données d'un provider spécifique
        
        Args:
            provider: Instance du provider à utiliser
            
        Returns:
            int: Nombre d'enregistrements traités
        """
        try:
            crypto_data = provider.get_crypto_data()
            
            if not crypto_data:
                print(f"⚠️ Aucune donnée reçue de {provider.name}", flush=True)
                return 0
            
            # Envoyer chaque crypto dans Redis
            for crypto_item in crypto_data:
                self.redis_client.lpush(self.queue_name, json.dumps(crypto_item))
            
            print(f"📤 {provider.name}: {len(crypto_data)} enregistrements envoyés à Redis", flush=True)
            return len(crypto_data)
            
        except Exception as e:
            print(f"❌ Erreur avec {provider.name}: {e}", flush=True)
            return 0
    
    def scrape_all_sources(self) -> dict:
        """
        Scrape toutes les sources configurées
        
        Returns:
            dict: Statistiques du scraping {provider_name: count}
        """
        start_time = time.time()
        stats = {}
        
        print(f"\n🔄 === DÉBUT CYCLE DE SCRAPING ({time.strftime('%H:%M:%S')}) ===", flush=True)
        
        for provider in self.providers:
            try:
                count = self.scrape_from_provider(provider)
                stats[provider.name] = count
                
                # Petit délai entre providers pour éviter la surcharge
                if len(self.providers) > 1:
                    print("⏳ Délai entre providers...", flush=True)
                    time.sleep(2)
                    
            except Exception as e:
                print(f"💥 Erreur critique avec {provider.name}: {e}", flush=True)
                stats[provider.name] = 0
        
        duration = time.time() - start_time
        total_records = sum(stats.values())
        
        print(f"\n📊 === RÉSULTATS CYCLE ({duration:.1f}s) ===", flush=True)
        for provider_name, count in stats.items():
            print(f"  {provider_name}: {count} enregistrements", flush=True)
        print(f"  TOTAL: {total_records} enregistrements", flush=True)
        print(f"🔄 === FIN CYCLE ===\n", flush=True)
        
        return stats
    
    def test_providers(self):
        """
        Teste tous les providers sans envoyer à Redis (mode debug)
        """
        print("🧪 === MODE TEST PROVIDERS ===", flush=True)
        
        for provider in self.providers:
            print(f"\n🔍 Test {provider.name}:", flush=True)
            try:
                data = provider.get_crypto_data()
                if data:
                    print(f"✅ {provider.name}: {len(data)} cryptos récupérées", flush=True)
                    # Afficher les 3 premiers pour vérification
                    for crypto in data[:3]:
                        print(f"   📈 {crypto['symbol']}: ${crypto['price']:.2f}", flush=True)
                else:
                    print(f"❌ {provider.name}: Aucune donnée", flush=True)
            except Exception as e:
                print(f"💥 {provider.name}: Erreur - {e}", flush=True)
        
        print("\n🧪 === FIN TESTS ===", flush=True)
    
    def main_loop(self):
        """
        Boucle principale du scraper
        """
        print("🚀 Scraper CryptoViz Multi-Sources démarré !", flush=True)
        print(f"📅 Intervalle: {self.scraping_interval}s ({self.scraping_interval//60}min)", flush=True)
        
        # Test initial
        if os.getenv("TEST_MODE", "").lower() in ['true', '1', 'yes']:
            self.test_providers()
            return
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                print(f"🔥 Cycle #{cycle_count}", flush=True)
                
                stats = self.scrape_all_sources()
                
                # Vérification de santé
                if sum(stats.values()) == 0:
                    print("⚠️ ALERTE: Aucune donnée récupérée ce cycle !", flush=True)
                
                print(f"💤 Attente {self.scraping_interval}s avant prochain cycle...", flush=True)
                time.sleep(self.scraping_interval)
                
            except KeyboardInterrupt:
                print("\n👋 Arrêt du scraper demandé", flush=True)
                break
            except Exception as e:
                print(f"💥 Erreur dans la boucle principale: {e}", flush=True)
                print("⏳ Retry dans 30s...", flush=True)
                time.sleep(30)

def main():
    """Point d'entrée principal"""
    try:
        scraper = UnifiedCryptoScraper()
        scraper.main_loop()
    except Exception as e:
        print(f"🔥 Erreur fatale: {e}", flush=True)
        exit(1)

if __name__ == "__main__":
    main()
