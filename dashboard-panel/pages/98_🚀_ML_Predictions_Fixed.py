"""
Page ML Predictions FIXÉE avec debug
"""
import streamlit as st
import redis
import json
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import os
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(
    page_title="ML Predictions Ultra FIXED",
    page_icon="🚀", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 CRYPTO ML ULTRA (FIXED)")

# Connexion Redis AVEC DEBUG
@st.cache_resource
def get_redis_connection():
    try:
        client = redis.Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=0,
            decode_responses=True,
            socket_connect_timeout=5
        )
        client.ping()
        st.success("✅ Redis connecté")
        return client
    except Exception as e:
        st.error(f"❌ Erreur connexion Redis: {e}")
        return None

redis_client = get_redis_connection()

def get_ml_predictions_debug():
    """Récupère les prédictions ML avec debug"""
    if not redis_client:
        st.error("❌ Pas de client Redis")
        return {}
    
    try:
        # Debug: liste les clés
        ultra_keys = redis_client.keys("ml:ultra:*")
        st.write(f"🔍 Debug: {len(ultra_keys)} clés ultra trouvées")
        
        # Récupère les cryptos disponibles
        cryptos = redis_client.smembers("ml:ultra:available_cryptos")
        st.write(f"🔍 Debug: {len(cryptos)} cryptos disponibles: {list(cryptos)}")
        
        predictions = {}
        for crypto in cryptos:
            key = f"ml:ultra:predictions:{crypto}"
            data = redis_client.get(key)
            if data:
                predictions[crypto] = json.loads(data)
                
        st.write(f"🔍 Debug: {len(predictions)} prédictions récupérées")
        return predictions
        
    except Exception as e:
        st.error(f"❌ Erreur récupération données: {e}")
        return {}

# Récupère les données AVEC DEBUG
st.subheader("🔍 Debug des données")
all_predictions = get_ml_predictions_debug()

if not all_predictions:
    st.warning("⏳ Aucune donnée ML trouvée")
    st.stop()
else:
    st.success(f"✅ {len(all_predictions)} cryptos avec données ML trouvées !")

# Affichage des métriques
st.subheader("📊 Métriques")
col1, col2, col3, col4 = st.columns(4)

total_cryptos = len(all_predictions)
total_signals_buy = sum(1 for p in all_predictions.values() 
                       if p.get('ensemble_prediction', {}).get('signal', '').startswith('BUY'))
avg_confidence = np.mean([p.get('ensemble_prediction', {}).get('confidence', 0) 
                         for p in all_predictions.values()])
total_anomalies = sum(1 for p in all_predictions.values() 
                     if p.get('anomalies', {}).get('price', {}).get('is_anomaly', False))

with col1:
    st.metric("Cryptos Actives", total_cryptos)
with col2:
    st.metric("Signaux Buy", total_signals_buy)
with col3:
    st.metric("Confiance Moy.", f"{avg_confidence:.1%}")
with col4:
    st.metric("Anomalies", total_anomalies)

# Graphique simple pour tester
st.subheader("📈 Test Graphique Simple")

if all_predictions:
    # Données pour le graphique
    symbols = list(all_predictions.keys())[:6]  # Limite à 6 pour test
    prices = [all_predictions[s].get('current_price', 0) for s in symbols]
    predictions = [all_predictions[s].get('ensemble_prediction', {}).get('value', 0) for s in symbols]
    
    st.write(f"🔍 Debug graphique: {len(symbols)} symboles, {len(prices)} prix")
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=symbols,
        y=prices,
        name='Prix Actuel',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        x=symbols,
        y=predictions, 
        name='Prédiction',
        marker_color='orange'
    ))
    
    fig.update_layout(
        title="Prix Actuels vs Prédictions",
        xaxis_title="Cryptos",
        yaxis_title="Prix ($)",
        template="plotly_dark"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Tableau des données
st.subheader("📋 Données Détaillées") 

data_table = []
for symbol, data in all_predictions.items():
    ensemble = data.get('ensemble_prediction', {})
    data_table.append({
        'Crypto': symbol,
        'Prix Actuel': f"${data.get('current_price', 0):,.2f}",
        'Prédiction': f"${ensemble.get('value', 0):,.2f}",
        'Signal': ensemble.get('signal', 'N/A'),
        'Change %': f"{ensemble.get('change_pct', 0):+.2f}%",
        'Confiance': f"{ensemble.get('confidence', 0):.1%}"
    })

df = pd.DataFrame(data_table)
st.dataframe(df, use_container_width=True)

st.success("🎉 Page ML Ultra FIXÉE fonctionne !")
