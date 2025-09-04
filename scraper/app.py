import time
import json
import os
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError
from providers.coinmarketcap import CoinMarketCapProvider
from providers.coingecko import CoinGeckoProvider

class RedpandaCryptoProducer:
    """Producer Redpanda pour données crypto avec dual topics"""
    
    def __init__(self):
        brokers = os.getenv("REDPANDA_BROKERS", "redpanda:9092")
        
        # Configuration Redpanda/Kafka Producer
        self.producer = KafkaProducer(
            bootstrap_servers=[brokers],
            value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
            key_serializer=lambda x: x.encode('utf-8') if x else None,
            acks='all',  # Attendre confirmation de toutes les répliques
            retries=5,   # Retry automatique
            batch_size=16384,
            linger_ms=10,  # Attendre 10ms pour grouper les messages
            compression_type=None
        )
        
        # Topics configuration
        self.topics = {
            'raw_data': 'crypto-raw-data',      # Pour batch processing
            'streaming': 'crypto-streaming'     # Pour streaming temps réel
        }
        
        print("✅ Redpanda Producer initialisé", flush=True)
        print(f"📡 Brokers: {brokers}", flush=True)
        print(f"📊 Topics: {list(self.topics.values())}", flush=True)

    def create_topics_if_needed(self):
        """Crée les topics s'ils n'existent pas"""
        try:
            from kafka.admin import KafkaAdminClient, NewTopic
            
            admin_client = KafkaAdminClient(
                bootstrap_servers=[os.getenv("REDPANDA_BROKERS", "redpanda:9092")]
            )
            
            # Définir les topics à créer
            topics_to_create = [
                NewTopic(name=self.topics['raw_data'], num_partitions=3, replication_factor=1),
                NewTopic(name=self.topics['streaming'], num_partitions=3, replication_factor=1)
            ]
            
            # Créer les topics
            admin_client.create_topics(topics_to_create, validate_only=False)
            print("✅ Topics créés avec succès", flush=True)
            
        except Exception as e:
            print(f"⚠️ Topics déjà existants ou erreur création: {e}", flush=True)

    def publish_crypto_data(self, crypto_data):
        """Publication dual vers Redpanda topics"""
        if not crypto_data:
            print("⚠️ Aucune donnée à publier", flush=True)
            return

        print(f"📡 Publication de {len(crypto_data)} éléments vers Redpanda...", flush=True)
        
        # Statistiques
        sent_count = {'raw': 0, 'streaming': 0}
        source_counts = {}
        
        for item in crypto_data:
            try:
                # Enrichir les données
                enhanced_item = {
                    **item,
                    'ingestion_timestamp': datetime.now().isoformat(),
                    'producer_id': 'crypto-scraper-v2',
                    'schema_version': '2.0'
                }
                
                # Clé de partitioning : crypto_symbol pour distribuer équitablement
                partition_key = f"{item['symbol']}_{item['source']}"
                
                # 1. Topic RAW DATA (pour batch processing)
                future_raw = self.producer.send(
                    self.topics['raw_data'],
                    key=partition_key,
                    value=enhanced_item
                )
                
                # 2. Topic STREAMING (pour temps réel)
                future_streaming = self.producer.send(
                    self.topics['streaming'], 
                    key=partition_key,
                    value=enhanced_item
                )
                
                # Attendre confirmation (blocking)
                future_raw.get(timeout=10)
                future_streaming.get(timeout=10)
                
                sent_count['raw'] += 1
                sent_count['streaming'] += 1
                
                # Stats par source
                source = item.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
                
                print(f"📡 {item['name']} ({source}): Raw ✅ | Streaming ✅", flush=True)
                
            except KafkaError as e:
                print(f"❌ Erreur Kafka pour {item['name']}: {e}", flush=True)
            except Exception as e:
                print(f"❌ Erreur publication {item['name']}: {e}", flush=True)
        
        # Forcer l'envoi des messages en buffer
        self.producer.flush()
        
        # Afficher les statistiques finales
        print(f"\n✅ Publication Redpanda terminée:")
        print(f"   📊 Topic raw-data: {sent_count['raw']} messages")
        print(f"   📡 Topic streaming: {sent_count['streaming']} messages")
        print(f"   📈 Par source:")
        for source, count in source_counts.items():
            print(f"      • {source}: {count} cryptos")
        print()

def get_crypto_data_from_providers():
    """Récupère les données depuis tous les providers configurés"""
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
                    print(f"   • {crypto['name']} ({crypto['symbol']}) - ${crypto['price']:.2f}", flush=True)
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

def main():
    """Boucle principale avec Redpanda Producer"""
    print("🚀 Scraper CryptoViz Multi-Provider avec Redpanda démarré...", flush=True)
    
    # Initialiser le producer Redpanda
    producer = RedpandaCryptoProducer()
    
    # Créer les topics si nécessaire
    producer.create_topics_if_needed()
    
    # Attendre que Redpanda soit prêt
    print("⏳ Attente de la disponibilité Redpanda...", flush=True)
    time.sleep(10)
    
    cycle = 0
    
    while True:
        cycle += 1
        print(f"\n{'='*70}", flush=True)
        print(f"🔄 CYCLE {cycle} - {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
        print(f"{'='*70}", flush=True)
        
        try:
            # Récupérer les données crypto
            crypto_data = get_crypto_data_from_providers()
            
            if crypto_data:
                # Publier vers Redpanda
                producer.publish_crypto_data(crypto_data)
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
