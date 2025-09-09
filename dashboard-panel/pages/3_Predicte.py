"""
  ML Ultra Simple - Version garantie fonctionnelle
"""

import streamlit as st
import redis
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import time
import os

# Configuration
st.set_page_config(
    page_title="ML Ultra Simple",
    page_icon="💲",
    layout="wide"
)

# CSS Moderne simplifié
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Rajdhani:wght@300;400;600&display=swap');

.main {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    color: white;
    font-family: 'Rajdhani', sans-serif;
}

.ultra-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.5em;
    font-weight: 700;
    background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 50%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    margin-bottom: 30px;
}

.metric-card {
    background: rgba(26, 26, 26, 0.8);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 10px;
    padding: 20px;
    margin: 10px 0;
    text-align: center;
    backdrop-filter: blur(10px);
}

.signal-buy { color: #00ff88; }
.signal-sell { color: #ff3366; }
.signal-hold { color: #ffaa00; }
</style>
""", unsafe_allow_html=True)

# Interface
st.markdown('<h1 class="ultra-title">  ML ULTRA SIMPLE</h1>', unsafe_allow_html=True)

# Redis Client
@st.cache_resource
def get_redis_client():
    try:
        client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=0,
            decode_responses=True,
            socket_connect_timeout=3
        )
        client.ping()
        return client
    except Exception as e:
        st.error(f"❌ Connexion Redis échouée: {e}")
        return None

redis_client = get_redis_client()

if redis_client is None:
    st.stop()

# Récupération données
@st.cache_data(ttl=10)  # Cache de 10 secondes
def get_ml_data():
    try:
        # Cryptos disponibles 
        cryptos = redis_client.smembers('ml:ultra:available_cryptos')
        if not cryptos:
            return {}
            
        data = {}
        for crypto in cryptos:
            key = f'ml:ultra:predictions:{crypto}'
            raw_data = redis_client.get(key)
            if raw_data:
                data[crypto] = json.loads(raw_data)
        
        return data
    except Exception as e:
        st.error(f"Erreur récupération données: {e}")
        return {}

# Interface principale
col1, col2 = st.columns([1, 3])

with col1:
    st.subheader("🎛️ Contrôles")
    
    # Auto-refresh
    auto_refresh = st.checkbox("  Auto-refresh", value=True)
    if auto_refresh:
        refresh_rate = st.slider("Secondes", 5, 60, 15)

with col2:
    st.subheader("  Données ML Ultra")

# Données
predictions_data = get_ml_data()

if not predictions_data:
    st.warning("  En attente de données ML Ultra...")
    if auto_refresh:
        time.sleep(2)
        st.rerun()
    st.stop()

st.success(f"✅ {len(predictions_data)} cryptos avec prédictions ML")

# Métriques globales
col1, col2, col3, col4 = st.columns(4)

buy_signals = sum(1 for data in predictions_data.values() 
                 if data.get('ensemble_prediction', {}).get('signal', '') in ['BUY', 'STRONG_BUY'])
sell_signals = sum(1 for data in predictions_data.values() 
                  if data.get('ensemble_prediction', {}).get('signal', '') in ['SELL', 'STRONG_SELL'])
avg_confidence = sum(data.get('ensemble_prediction', {}).get('confidence', 0) 
                    for data in predictions_data.values()) / len(predictions_data)

with col1:
    st.metric("   Signaux BUY", buy_signals)
with col2:
    st.metric("📉 Signaux SELL", sell_signals)
with col3:
    st.metric("⚖️ Signaux HOLD", len(predictions_data) - buy_signals - sell_signals)
with col4:
    st.metric("  Confiance Moy.", f"{avg_confidence:.1%}")

# Table des cryptos
st.subheader("💰 Cryptomonnaies")

crypto_table_data = []
for symbol, data in predictions_data.items():
    prediction = data.get('ensemble_prediction', {})
    current_price = data.get('current_price', 0)
    pred_value = prediction.get('value', current_price)
    change_pct = prediction.get('change_pct', 0)
    signal = prediction.get('signal', 'HOLD')
    confidence = prediction.get('confidence', 0)
    
    crypto_table_data.append({
        'Crypto': symbol,
        'Prix Actuel': f"${current_price:.4f}",
        'Prédiction': f"${pred_value:.4f}",
        'Change %': f"{change_pct:+.2f}%",
        'Signal': signal,
        'Confiance': f"{confidence:.1%}"
    })

df = pd.DataFrame(crypto_table_data)
st.dataframe(df, use_container_width=True, height=300)

# Graphique principal - Version simple mais garantie
st.subheader("📈 Graphique Prédictions")

# Préparation données pour graphique
crypto_names = []
current_prices = []
predicted_prices = []
changes = []
signals = []

for symbol, data in predictions_data.items():
    prediction = data.get('ensemble_prediction', {})
    crypto_names.append(symbol)
    current_prices.append(data.get('current_price', 0))
    predicted_prices.append(prediction.get('value', 0))
    changes.append(prediction.get('change_pct', 0))
    signals.append(prediction.get('signal', 'HOLD'))

# Graphique en barres simple mais efficace
fig = go.Figure()

# Barres prix actuels
fig.add_trace(go.Bar(
    name='Prix Actuel',
    x=crypto_names,
    y=current_prices,
    marker_color='rgba(0, 212, 255, 0.8)',
    text=[f"${p:.4f}" for p in current_prices],
    textposition='auto'
))

# Barres prédictions
fig.add_trace(go.Bar(
    name='Prédiction',
    x=crypto_names,
    y=predicted_prices,
    marker_color='rgba(123, 104, 238, 0.8)',
    text=[f"${p:.4f}" for p in predicted_prices],
    textposition='auto'
))

fig.update_layout(
    title='Prix Actuels vs Prédictions ML',
    xaxis_title='Cryptomonnaies',
    yaxis_title='Prix ($)',
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Rajdhani", color="white"),
    barmode='group',
    height=500
)

st.plotly_chart(fig, use_container_width=True)

# Graphique changements en %
st.subheader("  Changements Prédits (%)")

colors = ['#00ff88' if c > 0 else '#ff3366' if c < 0 else '#ffaa00' for c in changes]

fig2 = go.Figure(data=go.Bar(
    x=crypto_names,
    y=changes,
    marker_color=colors,
    text=[f"{c:+.2f}%" for c in changes],
    textposition='auto'
))

fig2.update_layout(
    title='Changements Prédits par Crypto (%)',
    xaxis_title='Cryptomonnaies',
    yaxis_title='Changement (%)',
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Rajdhani", color="white"),
    height=400
)

fig2.add_hline(y=0, line_dash="dash", line_color="gray")

st.plotly_chart(fig2, use_container_width=True)

# Graphique distribution des signaux
st.subheader("  Distribution des Signaux")

signal_counts = pd.Series(signals).value_counts()

fig3 = go.Figure(data=go.Pie(
    labels=signal_counts.index,
    values=signal_counts.values,
    hole=0.4,
    marker_colors=['#00ff88', '#00d4ff', '#ffaa00', '#ff6b35', '#ff3366'][:len(signal_counts)]
))

fig3.update_layout(
    title='Répartition des Signaux de Trading',
    template='plotly_dark',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(family="Rajdhani", color="white"),
    height=400
)

st.plotly_chart(fig3, use_container_width=True)

# Auto-refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("  **ML Ultra Simple** - Prédictions en temps réel avec garantie d'affichage")
