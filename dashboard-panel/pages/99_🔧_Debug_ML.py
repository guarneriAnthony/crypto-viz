"""
Debug ML Ultra - Page de test simple
"""
import streamlit as st
import redis
import json
import os

st.set_page_config(page_title="Debug ML", layout="wide")

st.title("🔧 Debug ML Ultra")

# Test connexion Redis
try:
    redis_client = redis.Redis(
        host=os.getenv('REDIS_HOST', 'redis'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=0,
        decode_responses=True
    )
    redis_client.ping()
    st.success("✅ Redis connecté")
except Exception as e:
    st.error(f"❌ Redis erreur: {e}")
    st.stop()

# Test clés Ultra
ultra_keys = redis_client.keys("ml:ultra:*")
st.write(f"**Clés Ultra trouvées:** {len(ultra_keys)}")
st.write(ultra_keys[:10])

# Test cryptos disponibles  
available_cryptos = redis_client.smembers("ml:ultra:available_cryptos")
st.write(f"**Cryptos Ultra:** {available_cryptos}")

# Test données BTC
if available_cryptos:
    btc_key = "ml:ultra:predictions:BTC"
    btc_data = redis_client.get(btc_key)
    
    if btc_data:
        st.success("✅ Données BTC trouvées")
        btc_json = json.loads(btc_data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Prix actuel", f"${btc_json.get('current_price', 0):,.2f}")
        with col2:
            ensemble = btc_json.get('ensemble_prediction', {})
            st.metric("Prédiction", f"${ensemble.get('value', 0):,.2f}")
        with col3:
            st.metric("Signal", ensemble.get('signal', 'N/A'))
            
        # Afficher structure complète
        st.subheader("Structure des données BTC:")
        st.json(btc_json)
    else:
        st.error("❌ Pas de données BTC")
else:
    st.warning("⚠️ Aucune crypto Ultra disponible")
    
# Test performance
perf_data = redis_client.get("ml:ultra:performance")
if perf_data:
    perf_json = json.loads(perf_data)
    st.subheader("Performance ML Ultra:")
    st.json(perf_json)
