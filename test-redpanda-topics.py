#!/usr/bin/env python3

from kafka import KafkaConsumer
import json
import sys
import signal
import time

def test_consume_topic(topic_name):
    print(f"🔍 Test consommation topic: {topic_name}")
    
    try:
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=['localhost:19092'],  # Port externe Redpanda
            group_id=f'test-{topic_name}-consumer',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='latest',
            consumer_timeout_ms=10000  # 10 secondes timeout
        )
        
        print(f"✅ Consumer connecté pour {topic_name}")
        print("⏳ En attente des messages (10s max)...")
        
        message_count = 0
        for message in consumer:
            message_count += 1
            data = message.value
            print(f"📡 Message {message_count}: {data.get('name', 'Unknown')} - ${data.get('price', 0):.2f} ({data.get('source', 'unknown')})")
            
            if message_count >= 5:  # Afficher max 5 messages
                print(f"✅ {message_count} messages reçus, test réussi!")
                break
                
        consumer.close()
        
        if message_count == 0:
            print(f"⚠️ Aucun message reçu sur {topic_name}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test {topic_name}: {e}")
        return False

def main():
    print("🚀 Test des topics Redpanda")
    print("=" * 50)
    
    # Test des deux topics
    topics = ['crypto-raw-data', 'crypto-streaming']
    
    for topic in topics:
        print(f"\n📊 Topic: {topic}")
        print("-" * 30)
        success = test_consume_topic(topic)
        
        if not success:
            print(f"❌ Échec test {topic}")
        else:
            print(f"✅ Succès test {topic}")
    
    print("\n🎯 Test terminé")

if __name__ == "__main__":
    # Gérer Ctrl+C proprement
    def signal_handler(sig, frame):
        print("\n🛑 Arrêt demandé")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    main()
