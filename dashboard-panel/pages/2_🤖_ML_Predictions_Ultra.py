"""
Page Streamlit ML Ultra - Version finale avec interface ultra-moderne
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

# Configuration de la page
st.set_page_config(
    page_title="ML Predictions Ultra",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Ultra-moderne identique à l'original
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;600&display=swap');

/* Variables CSS */
:root {
    --primary-glow: #00f5ff;
    --secondary-glow: #ff006e;
    --accent-glow: #8338ec;
    --success-glow: #00ff7f;
    --warning-glow: #ffd700;
    --bg-dark: #0a0a0a;
    --bg-card: rgba(255, 255, 255, 0.05);
    --text-glow: #ffffff;
}

/* Background animé */
.stApp {
    background: linear-gradient(-45deg, #0a0a0a, #1a1a2e, #16213e, #0f0f23);
    background-size: 400% 400%;
    animation: gradientShift 15s ease infinite;
}

@keyframes gradientShift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* Header principal */
.main-header {
    text-align: center;
    padding: 2rem 0;
    margin-bottom: 2rem;
    background: rgba(255, 255, 255, 0.03);
    border-radius: 20px;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(0, 245, 255, 0.2);
}

.main-title {
    font-family: 'Orbitron', monospace;
    font-size: 3.5rem;
    font-weight: 900;
    background: linear-gradient(45deg, #00f5ff, #ff006e, #8338ec);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
    animation: titlePulse 3s ease-in-out infinite alternate;
    margin-bottom: 0.5rem;
}

@keyframes titlePulse {
    0% { filter: brightness(1) drop-shadow(0 0 10px #00f5ff); }
    100% { filter: brightness(1.3) drop-shadow(0 0 20px #ff006e); }
}

.subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1.4rem;
    color: rgba(255, 255, 255, 0.8);
    font-weight: 300;
    letter-spacing: 2px;
}

/* Cartes métriques */
.metric-card {
    background: linear-gradient(145deg, rgba(0, 245, 255, 0.1), rgba(255, 0, 110, 0.1));
    border-radius: 15px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(15px);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    transition: left 0.5s;
}

.metric-card:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 0 15px 30px rgba(0, 245, 255, 0.3);
    border-color: var(--primary-glow);
}

.metric-card:hover::before {
    left: 100%;
}

.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary-glow);
    margin-bottom: 0.5rem;
    text-shadow: 0 0 10px currentColor;
}

.metric-label {
    font-family: 'Rajdhani', sans-serif;
    font-size: 1rem;
    color: rgba(255, 255, 255, 0.8);
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Graphiques Plotly */
.js-plotly-plot {
    border-radius: 15px;
    background: rgba(255, 255, 255, 0.02);
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Animations */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(30px); }
    to { opacity: 1; transform: translateY(0); }
}

.fadeInUp {
    animation: fadeInUp 0.6s ease-out;
}
</style>
""", unsafe_allow_html=True)

# Header principal identique à l'original
st.markdown("""
<div class="main-header fadeInUp">
    <div class="main-title">🚀 CRYPTO ML ULTRA</div>
    <div class="subtitle">Intelligence Artificielle • Prédictions Temps Réel • Analytics Avancées</div>
</div>
""", unsafe_allow_html=True)

# Connexion Redis
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
        return client
    except Exception as e:
        st.error(f"❌ Erreur connexion Redis: {e}")
        return None

redis_client = get_redis_connection()

# Fonctions utilitaires
def get_ml_predictions(symbol=None):
    """Récupère les prédictions ML depuis Redis"""
    if not redis_client:
        return {}
    
    try:
        if symbol:
            key = f"ml:ultra:predictions:{symbol}"
            data = redis_client.get(key)
            return json.loads(data) if data else {}
        else:
            cryptos = redis_client.smembers("ml:ultra:available_cryptos")
            predictions = {}
            for crypto in cryptos:
                key = f"ml:ultra:predictions:{crypto}"
                data = redis_client.get(key)
                if data:
                    predictions[crypto] = json.loads(data)
            return predictions
    except Exception as e:
        st.error(f"Erreur récupération données: {e}")
        return {}

def get_performance_metrics():
    """Récupère les métriques de performance"""
    if not redis_client:
        return {}
    
    try:
        key = "ml:ultra:performance"
        data = redis_client.get(key)
        return json.loads(data) if data else {}
    except:
        return {}

# Sidebar identique à l'original
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Status système
    st.markdown("### 📊 Status Système")
    if redis_client:
        st.markdown('<div style="color: #00ff7f;">🟢 Redis Connected</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="color: #ff006e;">🔴 Redis Disconnected</div>', unsafe_allow_html=True)
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (30s)", value=True)
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Métriques système
    st.markdown("### 📈 Métriques Système")
    perf_metrics = get_performance_metrics()
    
    if perf_metrics:
        st.metric("Messages traités", perf_metrics.get('total_messages', 0))
        st.metric("Prédictions", perf_metrics.get('total_predictions', 0))
        st.metric("Anomalies", perf_metrics.get('anomalies_detected', 0))
        
        uptime = perf_metrics.get('uptime_seconds', 0)
        uptime_str = f"{uptime//3600:.0f}h {(uptime%3600)//60:.0f}m"
        st.metric("Uptime", uptime_str)

# Corps principal
all_predictions = get_ml_predictions()
available_cryptos = list(all_predictions.keys())

# Filtre crypto dans sidebar
with st.sidebar:
    if available_cryptos:
        selected_crypto = st.selectbox(
            "💰 Sélectionner Crypto",
            ["Toutes"] + available_cryptos,
            index=0
        )
    else:
        st.warning("Aucune donnée ML disponible")
        selected_crypto = None

if not all_predictions:
    st.warning("⏳ En attente de données ML... Assurez-vous que le ML Processor Ultra tourne.")
    st.stop()

# Métriques en temps réel avec cartes ultra-modernes
col1, col2, col3, col4, col5 = st.columns(5)

total_cryptos = len(all_predictions)
total_signals_buy = sum(1 for p in all_predictions.values() 
                       if p.get('ensemble_prediction', {}).get('signal', '').startswith('BUY'))
total_anomalies = sum(1 for p in all_predictions.values() 
                     if p.get('anomalies', {}).get('price', {}).get('is_anomaly', False))
avg_confidence = np.mean([p.get('ensemble_prediction', {}).get('confidence', 0) 
                         for p in all_predictions.values()])
avg_volatility = np.mean([p.get('technical_indicators', {}).get('volatility', 0) 
                         for p in all_predictions.values()])

with col1:
    st.markdown(f"""
    <div class="metric-card fadeInUp">
        <div class="metric-value">{total_cryptos}</div>
        <div class="metric-label">🔮 Cryptos Actives</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card fadeInUp">
        <div class="metric-value">{total_signals_buy}</div>
        <div class="metric-label">📈 Signaux Buy</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card fadeInUp">
        <div class="metric-value">{avg_confidence:.1%}</div>
        <div class="metric-label">🎯 Confiance Moy.</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card fadeInUp">
        <div class="metric-value">{total_anomalies}</div>
        <div class="metric-label">⚠️ Anomalies</div>
    </div>
    """, unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card fadeInUp">
        <div class="metric-value">{avg_volatility:.1f}%</div>
        <div class="metric-label">📊 Volatilité Moy.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Graphiques principaux
if selected_crypto == "Toutes" or selected_crypto is None:
    # Vue d'ensemble avec graphique ultra-moderne
    st.markdown("### 🌟 Vue d'Ensemble - Toutes les Cryptos")
    
    # Graphique ensemble des prédictions
    fig_overview = go.Figure()
    
    colors = px.colors.qualitative.Set1
    for i, (symbol, data) in enumerate(all_predictions.items()):
        ensemble = data.get('ensemble_prediction', {})
        current_price = data.get('current_price', 0)
        predicted_value = ensemble.get('value', current_price)
        confidence = ensemble.get('confidence', 0)
        
        fig_overview.add_trace(go.Scatter(
            x=[current_price],
            y=[predicted_value],
            mode='markers',
            name=symbol,
            marker=dict(
                size=20 + confidence * 30,
                color=colors[i % len(colors)],
                line=dict(width=2, color='white'),
                opacity=0.8
            ),
            text=f"{symbol}<br>Confiance: {confidence:.1%}<br>Change: {ensemble.get('change_pct', 0):.2f}%",
            hovertemplate='<b>%{text}</b><br>Prix actuel: $%{x:.2f}<br>Prédiction: $%{y:.2f}<extra></extra>'
        ))
    
    # Ligne de prédiction parfaite
    min_price = min(data.get('current_price', 0) for data in all_predictions.values())
    max_price = max(data.get('current_price', 0) for data in all_predictions.values())
    
    fig_overview.add_trace(go.Scatter(
        x=[min_price * 0.9, max_price * 1.1],
        y=[min_price * 0.9, max_price * 1.1],
        mode='lines',
        name='Prédiction Parfaite',
        line=dict(color='rgba(255, 255, 255, 0.5)', width=2, dash='dash'),
        showlegend=True
    ))
    
    fig_overview.update_layout(
        title="🎯 Précision des Prédictions Ensemble",
        xaxis_title="Prix Actuel ($)",
        yaxis_title="Prix Prédit ($)",
        template="plotly_dark",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=500,
        hovermode='closest'
    )
    
    st.plotly_chart(fig_overview, use_container_width=True)
    
    # Distribution des signaux et volatilité
    col1, col2 = st.columns(2)
    
    with col1:
        signals_data = {}
        for data in all_predictions.values():
            signal = data.get('ensemble_prediction', {}).get('signal', 'HOLD')
            signals_data[signal] = signals_data.get(signal, 0) + 1
        
        fig_signals = go.Figure(data=go.Pie(
            labels=list(signals_data.keys()),
            values=list(signals_data.values()),
            hole=0.4,
            marker=dict(colors=['#00ff7f', '#32cd32', '#ffd700', '#ff6347', '#ff006e'])
        ))
        
        fig_signals.update_layout(
            title="📊 Distribution des Signaux",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig_signals, use_container_width=True)
    
    with col2:
        # Heatmap de volatilité
        symbols = list(all_predictions.keys())
        volatilities = [data.get('technical_indicators', {}).get('volatility', 0) 
                       for data in all_predictions.values()]
        
        fig_vol = go.Figure(data=go.Bar(
            x=symbols,
            y=volatilities,
            marker=dict(
                color=volatilities,
                colorscale='plasma',
                showscale=True,
                colorbar=dict(title="Volatilité %")
            )
        ))
        
        fig_vol.update_layout(
            title="⚡ Volatilité par Crypto",
            xaxis_title="Crypto",
            yaxis_title="Volatilité (%)",
            template="plotly_dark",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=400
        )
        
        st.plotly_chart(fig_vol, use_container_width=True)

else:
    # Vue détaillée pour une crypto spécifique
    if selected_crypto in all_predictions:
        data = all_predictions[selected_crypto]
        st.markdown(f"### 💰 Analyse Détaillée - {selected_crypto}")
        
        ensemble = data.get('ensemble_prediction', {})
        technical = data.get('technical_indicators', {})
        
        # Métriques crypto spécifique
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            current_price = data.get('current_price', 0)
            st.metric("Prix Actuel", f"${current_price:.4f}")
        
        with col2:
            predicted_price = ensemble.get('value', 0)
            change = predicted_price - current_price
            st.metric("Prédiction 1h", f"${predicted_price:.4f}", f"${change:+.4f}")
        
        with col3:
            confidence = ensemble.get('confidence', 0)
            st.metric("Confiance", f"{confidence:.1%}")
        
        with col4:
            rsi = technical.get('rsi', 50)
            st.metric("RSI", f"{rsi:.1f}")

# Footer ultra-moderne
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.6);">
    <p>⚡ <strong>Crypto ML Ultra</strong> - Powered by Advanced ML Ensemble Models</p>
    <p>🚀 Temps réel • 🧠 IA Avancée • 📊 Prédictions Multi-Horizon</p>
</div>
""", unsafe_allow_html=True)

# Auto-refresh en bas
if auto_refresh:
    st.markdown('<div style="position: fixed; bottom: 20px; right: 20px; background: rgba(0,245,255,0.2); padding: 10px; border-radius: 10px; color: #00f5ff;">🔄 Auto-refresh actif</div>', unsafe_allow_html=True)
