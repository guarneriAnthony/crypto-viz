import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Ajouter le dossier parent au path pour importer utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.database import get_crypto_data, get_available_cryptos

# Configuration de la page
st.set_page_config(page_title=" ML Predictions - CryptoViz", layout="wide")

st.title(" ML Predictions - Prédictions de Prix Crypto")
st.markdown("*🔮 Analyse prédictive basée sur machine learning temps réel*")

# ===== SESSION STATE =====
if 'selected_crypto' not in st.session_state:
    st.session_state.selected_crypto = 'Bitcoin'
    
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None
    
if 'force_refresh' not in st.session_state:
    st.session_state.force_refresh = False

if 'last_params' not in st.session_state:
    st.session_state.last_params = {}

def calculate_moving_averages(df, window_short=20, window_long=50):
    """Calcule les moyennes mobiles"""
    df = df.copy()
    df['ma_short'] = df['price'].rolling(window=window_short, min_periods=1).mean()
    df['ma_long'] = df['price'].rolling(window=window_long, min_periods=1).mean()
    return df

def calculate_trend(df):
    """Calcule la tendance linéaire"""
    df = df.copy()
    x = np.arange(len(df))
    coeffs = np.polyfit(x, df['price'], 1)
    df['trend'] = coeffs[0] * x + coeffs[1]
    return df, coeffs[0]

def calculate_momentum(df, window=14):
    """Calcule le momentum"""
    df = df.copy()
    df['momentum'] = df['price'].diff(window)
    return df

def predict_price(df, hours_ahead=1):
    """Prédit le prix basé sur différents modèles"""
    predictions = {}
    
    last_ma_short = df['ma_short'].iloc[-1]
    predictions['ma_short'] = last_ma_short
    
    last_ma_long = df['ma_long'].iloc[-1]
    predictions['ma_long'] = last_ma_long
    
    slope = (df['trend'].iloc[-1] - df['trend'].iloc[-2])
    predictions['trend'] = df['trend'].iloc[-1] + slope * hours_ahead
    
    last_price = df['price'].iloc[-1]
    avg_momentum = df['momentum'].dropna().tail(10).mean()
    predictions['momentum'] = last_price + (avg_momentum * hours_ahead / 14)
    
    weights = {'ma_short': 0.3, 'ma_long': 0.2, 'trend': 0.3, 'momentum': 0.2}
    consensus = sum(predictions[model] * weight for model, weight in weights.items())
    predictions['consensus'] = consensus
    
    return predictions

def calculate_confidence_metrics(df, predictions):
    """Calcule les métriques de confiance"""
    last_price = df['price'].iloc[-1]
    price_std = df['price'].tail(20).std()
    
    metrics = {}
    for model, predicted_price in predictions.items():
        deviation = abs(predicted_price - last_price)
        confidence = max(0, 100 - (deviation / last_price) * 100)
        volatility_factor = min(100, price_std / last_price * 100)
        adjusted_confidence = confidence * (1 - volatility_factor / 200)
        metrics[model] = max(0, min(100, adjusted_confidence))
    
    return metrics

def params_changed(current_params):
    """Vérifie si les paramètres ont changé"""
    if not st.session_state.last_params:
        return True
    return current_params != st.session_state.last_params

# Récupérer les cryptos disponibles AVEC CACHE
@st.cache_data(ttl=300)  # Cache 5 minutes
def get_available_cryptos_cached():
    return get_available_cryptos()

available_cryptos = get_available_cryptos_cached()
if available_cryptos.empty:
    st.error("❌ Aucune donnée crypto disponible")
    st.stop()

crypto_list = available_cryptos['name'].tolist()

# ===== SIDEBAR =====
st.sidebar.header(" Configuration ML")

# Debug permanent
st.sidebar.markdown("### 🔍 État Actuel")
st.sidebar.write(f"** Sélection:** `{st.session_state.selected_crypto}`")
st.sidebar.write(f"**💰 Cryptos disponibles:** {len(crypto_list)}")

# ===== SÉLECTION CRYPTO =====
st.sidebar.markdown("### 💰 Sélection Crypto")
st.sidebar.markdown("** Cliquez sur une crypto :**")

# Créer des colonnes pour organiser les boutons
crypto_cols = st.sidebar.columns(2)

for i, crypto in enumerate(crypto_list[:10]):  # Limiter à 10 pour l'affichage
    col_idx = i % 2
    
    with crypto_cols[col_idx]:
        # Bouton spécial pour la crypto sélectionnée
        if crypto == st.session_state.selected_crypto:
            button_label = f"✅ {crypto}"
            button_type = "primary"
        else:
            button_label = crypto
            button_type = "secondary"
            
        if st.button(button_label, key=f"crypto_btn_{crypto}", type=button_type, width="stretch"):
            st.session_state.selected_crypto = crypto
            st.session_state.analysis_results = None  # Reset analysis
            st.session_state.force_refresh = True
            st.rerun()

# Afficher la sélection actuelle
st.sidebar.success(f" **Analysé:** {st.session_state.selected_crypto}")

# ===== PARAMÈTRES DE CONFIGURATION =====
st.sidebar.markdown("### ⚙️ Paramètres ML")

# Utiliser des clés fixes pour éviter les conflicts
hours_back = st.sidebar.slider(
    " Historique (heures)", 
    min_value=6, 
    max_value=168, 
    value=24, 
    step=6,
    key="hours_back_slider"
)

hours_ahead = st.sidebar.slider(
    " Horizon prédiction (heures)", 
    min_value=1, 
    max_value=48, 
    value=4, 
    step=1,
    key="hours_ahead_slider"
)

st.sidebar.markdown("###  Paramètres Avancés")

window_short = st.sidebar.number_input(
    " MA Court Terme", 
    min_value=5, 
    max_value=50, 
    value=20, 
    step=5,
    key="window_short_input"
)

window_long = st.sidebar.number_input(
    " MA Long Terme", 
    min_value=20, 
    max_value=200, 
    value=50, 
    step=10,
    key="window_long_input"
)

momentum_window = st.sidebar.number_input(
    " Fenêtre Momentum", 
    min_value=7, 
    max_value=30, 
    value=14, 
    step=1,
    key="momentum_window_input"
)

# Paramètres actuels pour tracking
current_params = {
    'crypto': st.session_state.selected_crypto,
    'hours_back': hours_back,
    'hours_ahead': hours_ahead,
    'window_short': window_short,
    'window_long': window_long,
    'momentum_window': momentum_window
}

# ===== BOUTONS DE CONTRÔLE =====
st.sidebar.markdown("---")
st.sidebar.markdown("###  Actions")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button(" Actualiser", type="secondary", width="stretch"):
        st.session_state.force_refresh = True
        st.cache_data.clear()
        st.rerun()

with col2:
    if st.button(" Analyser", type="primary", width="stretch"):
        st.session_state.force_refresh = True
        st.session_state.analysis_results = None
        st.rerun()

# Vérifier si on doit recalculer
if (st.session_state.analysis_results is None or 
    params_changed(current_params) or 
    st.session_state.force_refresh):
    
    with st.spinner(' Calcul des prédictions ML...'):
        # Récupérer les données
        data = get_crypto_data(st.session_state.selected_crypto, hours_back)
        
        if data.empty:
            st.error(f"❌ Aucune donnée disponible pour {st.session_state.selected_crypto}")
            st.stop()
        # Configurer timestamp comme index pour les calculs temporels
        data = data.set_index(pd.to_datetime(data['timestamp']))
        data = data.drop(columns=['timestamp'], errors='ignore')

        
        # Calculs ML
        data = calculate_moving_averages(data, window_short, window_long)
        data, trend_slope = calculate_trend(data)
        data = calculate_momentum(data, momentum_window)
        
        # Prédictions
        predictions = predict_price(data, hours_ahead)
        confidence_metrics = calculate_confidence_metrics(data, predictions)
        
        # Stocker les résultats
        st.session_state.analysis_results = {
            'data': data,
            'predictions': predictions,
            'confidence': confidence_metrics,
            'trend_slope': trend_slope
        }
        st.session_state.last_params = current_params.copy()
        st.session_state.force_refresh = False

# Récupérer les résultats
results = st.session_state.analysis_results
if not results:
    st.error("❌ Erreur de calcul ML")
    st.stop()

data = results['data']
predictions = results['predictions']
confidence_metrics = results['confidence']
trend_slope = results['trend_slope']

# ===== AFFICHAGE PRINCIPAL =====

# Métriques principales
st.header(" Métriques ML Temps Réel")
col1, col2, col3, col4 = st.columns(4)

current_price = data['price'].iloc[-1]
consensus_prediction = predictions['consensus']
price_change = ((consensus_prediction - current_price) / current_price) * 100
consensus_confidence = confidence_metrics['consensus']

with col1:
    st.metric("💰 Prix Actuel", f"${current_price:,.2f}")

with col2:
    st.metric("🔮 Prédiction Consensus", f"${consensus_prediction:,.2f}", f"{price_change:+.2f}%")

with col3:
    confidence_icon = "🟢" if consensus_confidence > 70 else "🟡" if consensus_confidence > 50 else "🔴"
    st.metric(f"{confidence_icon} Confiance", f"{consensus_confidence:.1f}%")

with col4:
    trend_icon = "📈" if trend_slope > 0 else "📉"
    trend_text = "Haussière" if trend_slope > 0 else "Baissière"
    st.metric(f"{trend_icon} Tendance", trend_text)

# Signal Trading
st.header(" Signal Trading")
col1, col2, col3 = st.columns(3)

# Déterminer le signal
if price_change > 2 and consensus_confidence > 60:
    signal = "🟢 ACHAT"
    signal_color = "success"
elif price_change < -2 and consensus_confidence > 60:
    signal = "🔴 VENTE"
    signal_color = "error"
else:
    signal = "🟡 HOLD"
    signal_color = "warning"

with col2:
    if signal_color == "success":
        st.success(f"### {signal}")
    elif signal_color == "error":
        st.error(f"### {signal}")
    else:
        st.warning(f"### {signal}")

# Tableau des prédictions détaillées
st.header(" Prédictions par Modèle")

models_data = []
model_names = {
    'ma_short': f'⚡ MA Court ({window_short})',
    'ma_long': f' MA Long ({window_long})',
    'trend': ' Tendance Linéaire',
    'momentum': f' Momentum ({momentum_window})',
    'consensus': ' Consensus Pondéré'
}

for model, prediction in predictions.items():
    change = ((prediction - current_price) / current_price) * 100
    confidence = confidence_metrics[model]
    
    # Icône basée sur la confiance
    if confidence > 70:
        conf_icon = "🟢"
    elif confidence > 50:
        conf_icon = "🟡"
    else:
        conf_icon = "🔴"
    
    # Icône direction
    direction_icon = "📈" if change > 0 else "📉"
    
    models_data.append({
        'Modèle': model_names.get(model, model),
        'Prix Prédit': f"${prediction:,.2f}",
        'Variation': f"{direction_icon} {change:+.2f}%",
        'Confiance': f"{conf_icon} {confidence:.1f}%"
    })

models_df = pd.DataFrame(models_data)
st.dataframe(models_df, width="stretch", hide_index=True)

# Graphique principal
st.header(" Analyse Technique + Prédictions")

fig = go.Figure()

# Prix historique
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['price'],
    mode='lines',
    name='💰 Prix Historique',
    line=dict(color='blue', width=2)
))

# Moyennes mobiles
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['ma_short'],
    mode='lines',
    name=f'⚡ MA {window_short}',
    line=dict(color='orange', width=1)
))

fig.add_trace(go.Scatter(
    x=data.index,
    y=data['ma_long'],
    mode='lines',
    name=f'📈 MA {window_long}',
    line=dict(color='red', width=1)
))

# Tendance
fig.add_trace(go.Scatter(
    x=data.index,
    y=data['trend'],
    mode='lines',
    name=' Tendance',
    line=dict(color='green', width=1, dash='dash')
))

# Point de prédiction consensus
future_time = data.index[-1] + pd.Timedelta(hours=hours_ahead)
fig.add_trace(go.Scatter(
    x=[future_time],
    y=[consensus_prediction],
    mode='markers',
    name=' Prédiction Consensus',
    marker=dict(color='red', size=15, symbol='star')
))

fig.update_layout(
    title=f" Analyse ML - {st.session_state.selected_crypto}",
    xaxis_title=" Temps",
    yaxis_title="💰 Prix ($)",
    height=600,
    hovermode='x unified'
)

st.plotly_chart(fig, width="stretch")

# Métriques de performance
st.header(" Métriques Performance")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📈 Volatilité")
    volatility = data['price'].tail(20).std()
    vol_pct = (volatility / current_price) * 100
    vol_icon = "🟢" if vol_pct < 5 else "🟡" if vol_pct < 10 else "🔴"
    st.metric(f"{vol_icon} Volatilité 20P", f"{vol_pct:.2f}%")

with col2:
    st.subheader(" Momentum")
    last_momentum = data['momentum'].dropna().iloc[-1] if not data['momentum'].dropna().empty else 0
    momentum_pct = (last_momentum / current_price) * 100
    mom_icon = "📈" if momentum_pct > 0 else "📉"
    st.metric(f"{mom_icon} Momentum {momentum_window}P", f"{momentum_pct:+.2f}%")

with col3:
    st.subheader(" Points de Données")
    data_quality_icon = "🟢" if len(data) > 50 else "🟡" if len(data) > 20 else "🔴"
    st.metric(f"{data_quality_icon} Qualité Données", f"{len(data)} points")

# Auto-refresh
st.sidebar.markdown("---")
st.sidebar.markdown("###  Actualisation")
if st.sidebar.button(" Actualiser ML", width="stretch"):
    st.cache_data.clear()
    st.session_state.force_refresh = True
    st.rerun()

st.sidebar.info(" *ML recalculé automatiquement sur nouvelles données streaming*")
