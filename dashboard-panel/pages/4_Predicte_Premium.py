"""
⚡ ML ULTRA DASHBOARD - Interface nouvelle génération
Architecture: Données historiques Redis → Analytics ultra-avancées → Visualisations modernes
Features: Multi-modèles, prédictions ensemble, détection anomalies, métriques temps réel
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

# Configuration de la page avec thème sombre futuriste
st.set_page_config(
    page_title="ML Ultra Dashboard",
    page_icon="💲",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Ultra-moderne avec animations et effets
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

/* Variables CSS pour cohérence */
:root {
    --primary-color: #00d4ff;
    --secondary-color: #ff6b35;
    --accent-color: #7b68ee;
    --success-color: #00ff88;
    --warning-color: #ffaa00;
    --danger-color: #ff3366;
    --dark-bg: #0a0a0a;
    --card-bg: #1a1a1a;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --glow-color: rgba(0, 212, 255, 0.3);
}

/* Reset et fond principal */
.main {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    color: var(--text-primary);
    font-family: 'Rajdhani', sans-serif;
}

/* Header ultra-futuriste */
.ultra-header {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(123, 104, 238, 0.1) 100%);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 15px;
    padding: 25px;
    margin-bottom: 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
}

.ultra-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    animation: rotate 6s linear infinite;
}

@keyframes rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.ultra-title {
    font-family: 'Orbitron', monospace;
    font-size: 3.2em;
    font-weight: 900;
    background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 50%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
    position: relative;
    z-index: 2;
}

.ultra-subtitle {
    font-size: 1.4em;
    color: var(--text-secondary);
    margin-top: 10px;
    font-weight: 300;
    position: relative;
    z-index: 2;
}

/* Métriques ultra avec animations */
.metric-ultra {
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.9) 0%, rgba(42, 42, 42, 0.7) 100%);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}

.metric-ultra:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(0, 212, 255, 0.3);
    border-color: var(--primary-color);
}

.metric-ultra::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    transition: left 0.5s;
}

.metric-ultra:hover::before {
    left: 100%;
}

.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 2.5em;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-size: 1.1em;
    color: var(--text-secondary);
    margin-top: 5px;
    font-weight: 500;
}

/* Cards avancées avec glow */
.ultra-card {
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(42, 42, 42, 0.8) 100%);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 15px;
    padding: 25px;
    margin: 15px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
}

.ultra-card:hover {
    border-color: var(--primary-color);
    box-shadow: 0 0 40px rgba(0, 212, 255, 0.2);
}

/* Alerts stylées */
.ultra-alert {
    padding: 15px 20px;
    border-radius: 10px;
    margin: 10px 0;
    font-weight: 500;
    border-left: 4px solid;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.alert-success {
    background: rgba(0, 255, 136, 0.1);
    border-left-color: var(--success-color);
    color: var(--success-color);
}

.alert-warning {
    background: rgba(255, 170, 0, 0.1);
    border-left-color: var(--warning-color);
    color: var(--warning-color);
}

.alert-danger {
    background: rgba(255, 51, 102, 0.1);
    border-left-color: var(--danger-color);
    color: var(--danger-color);
}

.alert-info {
    background: rgba(0, 212, 255, 0.1);
    border-left-color: var(--primary-color);
    color: var(--primary-color);
}

/* Sidebar ultra */
.css-1d391kg {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    border-right: 1px solid rgba(0, 212, 255, 0.3);
}

/* Boutons ultra */
.stSelectbox > div > div {
    background: rgba(26, 26, 26, 0.8) !important;
    border: 1px solid rgba(0, 212, 255, 0.3) !important;
    border-radius: 8px !important;
    color: white !important;
}

/* Animations de chargement */
.loading-pulse {
    display: inline-block;
    animation: pulse 1.5s ease-in-out infinite alternate;
}

@keyframes pulse {
    from { opacity: 0.5; }
    to { opacity: 1.0; }
}

/* Status indicators */
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    animation: blink 2s infinite;
}

.status-online { background: var(--success-color); }
.status-warning { background: var(--warning-color); }
.status-error { background: var(--danger-color); }

@keyframes blink {
    0%, 50% { opacity: 1; }
    51%, 100% { opacity: 0.5; }
}

/* Text effects */
.glow-text {
    text-shadow: 0 0 10px var(--glow-color);
}

.typing-effect {
    overflow: hidden;
    white-space: nowrap;
    animation: typing 2s steps(20, end);
}

@keyframes typing {
    from { width: 0; }
    to { width: 100%; }
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
}

::-webkit-scrollbar-track {
    background: rgba(26, 26, 26, 0.5);
}

::-webkit-scrollbar-thumb {
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(135deg, var(--accent-color), var(--secondary-color));
}
</style>
""", unsafe_allow_html=True)

# Classe utilitaire pour Redis
class RedisMLClient:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3
            )
            # Test de connexion
            self.client.ping()
            self.connected = True
        except Exception as e:
            st.error(f"❌ Connexion Redis échouée: {e}")
            self.connected = False
            self.client = None
    
    def get_ultra_predictions(self, symbol: str = None):
        """Récupère les prédictions ultra depuis Redis"""
        if not self.connected:
            return {}
        
        try:
            if symbol:
                key = f"ml:ultra:predictions:{symbol}"
                data = self.client.get(key)
                if data:
                    return {symbol: json.loads(data)}
                return {}
            else:
                # Récupère toutes les cryptos ultra
                cryptos = self.client.smembers("ml:ultra:available_cryptos")
                predictions = {}
                for crypto in cryptos:
                    key = f"ml:ultra:predictions:{crypto}"
                    data = self.client.get(key)
                    if data:
                        predictions[crypto] = json.loads(data)
                return predictions
        except Exception as e:
            st.error(f"❌ Erreur récupération prédictions: {e}")
            return {}
    
    def get_ultra_performance(self):
        """Récupère les métriques de performance ultra"""
        if not self.connected:
            return {}
        
        try:
            data = self.client.get("ml:ultra:performance")
            return json.loads(data) if data else {}
        except:
            return {}
    
    def get_available_cryptos(self):
        """Récupère la liste des cryptos disponibles"""
        if not self.connected:
            return []
        
        try:
            cryptos = self.client.smembers("ml:ultra:available_cryptos")
            return list(cryptos) if cryptos else []
        except:
            return []

# Fonctions utilitaires pour les graphiques
def create_prediction_chart(predictions_data):
    """Crée un graphique ultra-moderne des prédictions"""
    if not predictions_data:
        return None
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Prix & Prédictions", "Indicateurs Techniques", "Signaux Trading", "Performance"),
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"type": "indicator"}, {"type": "bar"}]]
    )
    
    colors = {
        'primary': '#00d4ff',
        'secondary': '#ff6b35', 
        'accent': '#7b68ee',
        'success': '#00ff88',
        'warning': '#ffaa00',
        'danger': '#ff3366'
    }
    
    for symbol, data in predictions_data.items():
        current_price = data.get('current_price', 0)
        prediction = data.get('ensemble_prediction', {})
        pred_value = prediction.get('value', current_price)
        
        # Historique des prix (si disponible)
        historical_prices = data.get('advanced_analytics', {}).get('historical_prices', [])
        
        if historical_prices:
            # Graphique principal : Prix historiques et prédiction
            x_hist = list(range(len(historical_prices)))
            fig.add_trace(
                go.Scatter(
                    x=x_hist, 
                    y=historical_prices,
                    name=f"{symbol} - Historique",
                    line=dict(color=colors['primary'], width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
            
            # Prédiction
            fig.add_trace(
                go.Scatter(
                    x=[len(historical_prices)-1, len(historical_prices)],
                    y=[historical_prices[-1], pred_value],
                    name=f"{symbol} - Prédiction",
                    line=dict(color=colors['accent'], width=3, dash='dash'),
                    mode='lines+markers'
                ),
                row=1, col=1
            )
        
        # Indicateurs techniques
        tech_indicators = data.get('technical_indicators', {})
        if tech_indicators:
            rsi = tech_indicators.get('rsi', 50)
            volatility = tech_indicators.get('volatility', 0)
            
            fig.add_trace(
                go.Scatter(
                    x=[symbol], 
                    y=[rsi],
                    name="RSI",
                    mode='markers',
                    marker=dict(size=15, color=colors['secondary'])
                ),
                row=1, col=2
            )
        
        # Gauge pour la confiance
        confidence = prediction.get('confidence', 0.5) * 100
        fig.add_trace(
            go.Indicator(
                mode="gauge+number+delta",
                value=confidence,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"{symbol} - Confiance %"},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': colors['success']},
                    'steps': [
                        {'range': [0, 50], 'color': colors['danger']},
                        {'range': [50, 75], 'color': colors['warning']},
                        {'range': [75, 100], 'color': colors['success']}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ),
            row=2, col=1
        )
        
        # Performance par signal
        signal = prediction.get('signal', 'HOLD')
        signal_strength = prediction.get('strength', 'MEDIUM')
        
        signal_colors = {
            'STRONG_BUY': colors['success'],
            'BUY': colors['primary'],
            'HOLD': colors['warning'],
            'SELL': colors['secondary'],
            'STRONG_SELL': colors['danger']
        }
        
        fig.add_trace(
            go.Bar(
                x=[symbol],
                y=[abs(prediction.get('change_pct', 0))],
                name="Change %",
                marker_color=signal_colors.get(signal, colors['primary'])
            ),
            row=2, col=2
        )
    
    # Layout ultra-moderne
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Rajdhani", size=12, color="white"),
        title=dict(
            text="   ML Ultra Analytics Dashboard",
            font=dict(size=24, family="Orbitron"),
            x=0.5
        ),
        showlegend=True,
        height=800
    )
    
    return fig

def create_market_overview(predictions_data):
    """Crée une vue d'ensemble du marché"""
    if not predictions_data:
        return None
    
    # Données pour le sunburst
    symbols = []
    signals = []
    confidences = []
    changes = []
    
    for symbol, data in predictions_data.items():
        prediction = data.get('ensemble_prediction', {})
        symbols.append(symbol)
        signals.append(prediction.get('signal', 'HOLD'))
        confidences.append(prediction.get('confidence', 0.5))
        changes.append(prediction.get('change_pct', 0))
    
    # Sunburst chart des signaux
    fig = go.Figure(go.Sunburst(
        labels=symbols + list(set(signals)),
        parents=signals + [''] * len(set(signals)),
        values=confidences + [1] * len(set(signals)),
        branchvalues="total",
        hovertemplate='<b>%{label}</b><br>Confiance: %{value:.1%}<extra></extra>',
        maxdepth=2,
        textfont_size=12
    ))
    
    signal_colors = {
        'STRONG_BUY': '#00ff88',
        'BUY': '#00d4ff',
        'HOLD': '#ffaa00',
        'SELL': '#ff6b35',
        'STRONG_SELL': '#ff3366'
    }
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Rajdhani", size=12, color="white"),
        title=dict(
            text=" Market Signal Distribution",
            font=dict(size=20, family="Orbitron"),
            x=0.5
        ),
        height=500
    )
    
    return fig

def display_crypto_metrics(symbol, data):
    """Affiche les métriques d'une crypto"""
    prediction = data.get('ensemble_prediction', {})
    current_price = data.get('current_price', 0)
    pred_value = prediction.get('value', current_price)
    change_pct = prediction.get('change_pct', 0)
    signal = prediction.get('signal', 'HOLD')
    confidence = prediction.get('confidence', 0.5)
    
    # Couleur selon le signal
    if signal in ['STRONG_BUY', 'BUY']:
        color = 'success'
    elif signal in ['STRONG_SELL', 'SELL']:
        color = 'danger'
    else:
        color = 'warning'

    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-ultra">
            <div class="metric-value">${current_price:.4f}</div>
            <div class="metric-label">Prix Actuel</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-ultra">
            <div class="metric-value" style="color: {'#00ff88' if change_pct > 0 else '#ff3366'}">{change_pct:+.2f}%</div>
            <div class="metric-label">Prédiction</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-ultra">
            <div class="metric-value">{signal}</div>
            <div class="metric-label">Signal</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        confidence_color = '#00ff88' if confidence > 0.7 else '#ffaa00' if confidence > 0.5 else '#ff3366'
        st.markdown(f"""
        <div class="metric-ultra">
            <div class="metric-value" style="color: {confidence_color}">{confidence:.1%}</div>
            <div class="metric-label">Confiance</div>
        </div>
        """, unsafe_allow_html=True)

def display_technical_analysis(data):
    """Affiche l'analyse technique avancée"""
    tech_indicators = data.get('technical_indicators', {})
    advanced_analytics = data.get('advanced_analytics', {})
    anomalies = data.get('anomalies', {})
    
    st.markdown("###   Analyse Technique Ultra")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**  Indicateurs Techniques**")
        
        rsi = tech_indicators.get('rsi', 50)
        volatility = tech_indicators.get('volatility', 0)
        market_phase = advanced_analytics.get('market_phase', 'unknown')
        risk_level = advanced_analytics.get('risk_level', 'medium')
        
        # RSI
        rsi_color = '#ff3366' if rsi > 70 else '#00ff88' if rsi < 30 else '#ffaa00'
        st.markdown(f"""
        <div class="ultra-alert alert-info">
            <strong>RSI:</strong> <span style="color: {rsi_color}">{rsi:.1f}</span>
            {'(Survente)' if rsi < 30 else '(Surachat)' if rsi > 70 else '(Neutre)'}
        </div>
        """, unsafe_allow_html=True)
        
        # Volatilité
        vol_color = '#ff3366' if volatility > 5 else '#ffaa00' if volatility > 2 else '#00ff88'
        st.markdown(f"""
        <div class="ultra-alert alert-info">
            <strong>Volatilité:</strong> <span style="color: {vol_color}">{volatility:.2f}%</span>
            (Risque: {risk_level.title()})
        </div>
        """, unsafe_allow_html=True)
        
        # Phase de marché
        phase_colors = {'bull_market': '#00ff88', 'bear_market': '#ff3366', 'sideways': '#ffaa00'}
        phase_icons = {'bull_market': '🐂', 'bear_market': '🐻', 'sideways': '↔️'}
        st.markdown(f"""
        <div class="ultra-alert alert-info">
            <strong>Phase Marché:</strong> {phase_icons.get(market_phase, '❓')} 
            <span style="color: {phase_colors.get(market_phase, '#ffaa00')}">{market_phase.replace('_', ' ').title()}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**  Détection d'Anomalies**")
        
        price_anomaly = anomalies.get('price', {})
        volume_anomaly = anomalies.get('volume', {})
        
        if price_anomaly.get('is_anomaly'):
            anomaly_type = price_anomaly.get('type', 'unknown')
            severity = price_anomaly.get('severity', 'medium')
            score = price_anomaly.get('score', 0)
            
            alert_class = 'alert-danger' if severity == 'critical' else 'alert-warning'
            st.markdown(f"""
            <div class="ultra-alert {alert_class}">
                <strong>  Anomalie Prix:</strong> {anomaly_type.replace('_', ' ').title()}<br>
                <strong>Score:</strong> {score:.2f} | <strong>Sévérité:</strong> {severity.title()}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ultra-alert alert-success">
                <strong>✅ Prix Normal:</strong> Aucune anomalie détectée
            </div>
            """, unsafe_allow_html=True)
        
        if volume_anomaly.get('is_anomaly'):
            vol_type = volume_anomaly.get('type', 'unknown')
            ratio = volume_anomaly.get('ratio', 1.0)
            
            st.markdown(f"""
            <div class="ultra-alert alert-warning">
                <strong>  Anomalie Volume:</strong> {vol_type.replace('_', ' ').title()}<br>
                <strong>Ratio:</strong> {ratio:.1f}x la normale
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="ultra-alert alert-success">
                <strong>✅ Volume Normal:</strong> Aucune anomalie détectée
            </div>
            """, unsafe_allow_html=True)

def display_multi_horizon_predictions(data):
    """Affiche les prédictions multi-horizon"""
    multi_horizon = data.get('multi_horizon', {})
    
    if not multi_horizon:
        return
    
    st.markdown("###   Prédictions Multi-Horizon")
    
    current_price = data.get('current_price', 0)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        short_pred = multi_horizon.get('short_term_1h', current_price)
        short_change = ((short_pred - current_price) / current_price * 100) if current_price > 0 else 0
        color = '#00ff88' if short_change > 0 else '#ff3366' if short_change < 0 else '#ffaa00'
        
        st.markdown(f"""
        <div class="ultra-card">
            <h4 style="color: var(--primary-color); margin-top: 0;">🕐 Court Terme (1h)</h4>
            <div style="font-size: 1.8em; font-weight: bold; color: {color};">
                ${short_pred:.4f}
            </div>
            <div style="color: {color}; font-weight: 500;">
                {short_change:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        medium_pred = multi_horizon.get('medium_term_6h', [current_price])
        if isinstance(medium_pred, list) and medium_pred:
            medium_pred = medium_pred[-1]  # Dernière prédiction
        medium_change = ((medium_pred - current_price) / current_price * 100) if current_price > 0 else 0
        color = '#00ff88' if medium_change > 0 else '#ff3366' if medium_change < 0 else '#ffaa00'
        
        st.markdown(f"""
        <div class="ultra-card">
            <h4 style="color: var(--accent-color); margin-top: 0;">🕕 Moyen Terme (6h)</h4>
            <div style="font-size: 1.8em; font-weight: bold; color: {color};">
                ${medium_pred:.4f}
            </div>
            <div style="color: {color}; font-weight: 500;">
                {medium_change:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        long_pred = multi_horizon.get('long_term_24h', [current_price])
        if isinstance(long_pred, list) and long_pred:
            long_pred = long_pred[-1]  # Dernière prédiction
        long_change = ((long_pred - current_price) / current_price * 100) if current_price > 0 else 0
        color = '#00ff88' if long_change > 0 else '#ff3366' if long_change < 0 else '#ffaa00'
        
        st.markdown(f"""
        <div class="ultra-card">
            <h4 style="color: var(--secondary-color); margin-top: 0;">🕛 Long Terme (24h)</h4>
            <div style="font-size: 1.8em; font-weight: bold; color: {color};">
                ${long_pred:.4f}
            </div>
            <div style="color: {color}; font-weight: 500;">
                {long_change:+.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

# Interface principale
def main():
    # Header ultra-futuriste
    st.markdown("""
    <div class="ultra-header">
        <h1 class="ultra-title typing-effect"> ML ULTRA DASHBOARD</h1>
        <p class="ultra-subtitle">Intelligence Artificielle Avancée • Prédictions • Analytics Temps Réel</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialisation Redis
    redis_client = RedisMLClient()
    
    if not redis_client.connected:
        st.markdown("""
        <div class="ultra-alert alert-danger">
            <strong>❌ Connexion Redis Échouée</strong><br>
            Vérifiez que le service Redis est en cours d'exécution et que les variables d'environnement sont correctement configurées.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Récupération des cryptos disponibles
    available_cryptos = redis_client.get_available_cryptos()
    
    if not available_cryptos:
        st.markdown("""
        <div class="ultra-alert alert-warning">
            <strong>⚠️ Aucune Crypto Disponible</strong><br>
            Le ML Processor Ultra n'a pas encore généré de données. Veuillez patienter ou vérifier le processeur.
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Sélecteur de crypto
    crypto_options = ["Toutes les cryptos"] + sorted(available_cryptos)
    selected_crypto = st.sidebar.selectbox(
        "  Sélectionner une Crypto",
        crypto_options,
        help="Choisissez une crypto spécifique ou affichez toutes les cryptos"
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("  Rafraîchissement Auto", value=True)
    if auto_refresh:
        refresh_interval = st.sidebar.slider("Intervalle (secondes)", 10, 120, 30)
    
    # Status de connexion
    st.sidebar.markdown(f"""
    <div class="ultra-alert alert-success">
        <span class="status-indicator status-online"></span>
        <strong>Redis Connecté</strong><br>
        <small>Données en temps réel disponibles</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Récupération des données
    if selected_crypto == "Toutes les cryptos":
        predictions_data = redis_client.get_ultra_predictions()
    else:
        predictions_data = redis_client.get_ultra_predictions(selected_crypto)
    
    if not predictions_data:
        st.markdown("""
        <div class="ultra-alert alert-warning">
            <strong>  En attente de données...</strong><br>
            Les prédictions ML Ultra sont en cours de génération.
        </div>
        """, unsafe_allow_html=True)
        if auto_refresh:
            time.sleep(2)
            st.rerun()
        return
    
    # Performance globale
    performance = redis_client.get_ultra_performance()
    if performance:
        st.markdown("###   Performance ML Ultra")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="metric-ultra">
                <div class="metric-value">{performance.get('total_predictions', 0)}</div>
                <div class="metric-label">Prédictions Générées</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-ultra">
                <div class="metric-value">{performance.get('total_cryptos', 0)}</div>
                <div class="metric-label">Cryptos Analysées</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            accuracy = performance.get('avg_accuracy', 0)
            accuracy_color = '#00ff88' if accuracy > 0.8 else '#ffaa00' if accuracy > 0.6 else '#ff3366'
            st.markdown(f"""
            <div class="metric-ultra">
                <div class="metric-value" style="color: {accuracy_color}">{accuracy:.1%}</div>
                <div class="metric-label">Précision Moyenne</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            uptime_hours = performance.get('uptime_seconds', 0) / 3600
            st.markdown(f"""
            <div class="metric-ultra">
                <div class="metric-value">{uptime_hours:.1f}h</div>
                <div class="metric-label">Uptime Processeur</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Vue d'ensemble du marché (pour toutes les cryptos)
    if selected_crypto == "Toutes les cryptos" and len(predictions_data) > 1:
        st.markdown("###   Vue d'Ensemble du Marché")
        market_fig = create_market_overview(predictions_data)
        if market_fig:
            st.plotly_chart(market_fig, use_container_width=True)
    
    # Analyse détaillée par crypto
    for symbol, data in predictions_data.items():
        st.markdown(f"##    {symbol} - Analyse Ultra")
        
        # Métriques principales
        display_crypto_metrics(symbol, data)
        
        # Prédictions multi-horizon
        display_multi_horizon_predictions(data)
        
        # Graphiques avancés
        single_crypto_data = {symbol: data}
        chart = create_prediction_chart(single_crypto_data)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        
        # Analyse technique
        display_technical_analysis(data)
        
        # Modèles individuels
        individual_models = data.get('individual_models', {})
        if individual_models:
            st.markdown("###   Prédictions par Modèle")
            
            model_cols = st.columns(len(individual_models))
            current_price = data.get('current_price', 0)
            
            for i, (model_name, pred_value) in enumerate(individual_models.items()):
                if current_price > 0:
                    change = ((pred_value - current_price) / current_price * 100)
                    color = '#00ff88' if change > 0 else '#ff3366' if change < 0 else '#ffaa00'
                    
                    with model_cols[i]:
                        st.markdown(f"""
                        <div class="ultra-card" style="text-align: center;">
                            <h5 style="margin-top: 0; color: var(--accent-color);">{model_name.replace('_', ' ').title()}</h5>
                            <div style="font-size: 1.4em; font-weight: bold;">
                                ${pred_value:.4f}
                            </div>
                            <div style="color: {color}; font-weight: 500;">
                                {change:+.2f}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        
        st.markdown("---")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()
