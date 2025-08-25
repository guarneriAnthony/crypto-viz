"""
Page ML Predictions - Prédictions de prix basées sur machine learning
"""
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
st.set_page_config(page_title="ML Predictions - CryptoViz", layout="wide")

st.title("ML Predictions - Prédictions de Prix Crypto")
st.markdown("*Analyse prédictive basée sur machine learning*")

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
    st.error("Aucune donnée crypto disponible")
    st.stop()

crypto_list = available_cryptos['name'].tolist()

# ===== SIDEBAR =====
st.sidebar.header("📊 Configuration ML")

# Debug permanent
st.sidebar.markdown("### 🔍 État Actuel")
st.sidebar.write(f"**Session State:** `{st.session_state.selected_crypto}`")
st.sidebar.write(f"**Cryptos disponibles:** {len(crypto_list)}")

# ===== SÉLECTION CRYPTO =====
st.sidebar.markdown("### 🎯 Sélection Crypto")
st.sidebar.markdown("**Cliquez sur une crypto :**")

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
            
        if st.button(button_label, key=f"crypto_btn_{crypto}", type=button_type, use_container_width=True):
            st.session_state.selected_crypto = crypto
            st.session_state.analysis_results = None  # Reset analysis
            st.session_state.force_refresh = True
            st.rerun()

# Afficher la sélection actuelle
st.sidebar.success(f"🎯 **Sélectionné:** {st.session_state.selected_crypto}")

# ===== PARAMÈTRES DE CONFIGURATION =====
st.sidebar.markdown("### ⚙️ Paramètres")

# Utiliser des clés fixes pour éviter les conflicts
hours_history = st.sidebar.slider(
    "Historique (heures)", 
    6, 72, 24, 
    key="hours_history_slider"
)

hours_prediction = st.sidebar.slider(
    "Prédiction (heures)", 
    1, 24, 4,
    key="hours_prediction_slider"
)

source_selected = st.sidebar.selectbox(
    "Source données",
    ["Toutes", "coinmarketcap", "coingecko"],
    key="source_selectbox"
)

# Paramètres ML
st.sidebar.markdown("### 🤖 Modèles ML")
ma_short_window = st.sidebar.slider("MA Courte", 5, 30, 20, key="ma_short_slider")
ma_long_window = st.sidebar.slider("MA Longue", 20, 100, 50, key="ma_long_slider") 
momentum_window = st.sidebar.slider("Momentum", 5, 30, 14, key="momentum_slider")

# ===== MODE D'ANALYSE =====
st.sidebar.markdown("### 🔄 Mode d'Analyse")

mode_continu = st.sidebar.checkbox(
    "🔄 Mode Continu", 
    value=False,
    help="Analyse automatique à chaque changement de paramètre",
    key="mode_continu_checkbox"
)

if mode_continu:
    st.sidebar.success("✅ Mode continu activé")
    st.sidebar.caption("L'analyse se lance automatiquement")
else:
    # Bouton d'analyse manuel
    analyze_button = st.sidebar.button(
        "🚀 ANALYSER", 
        type="primary", 
        use_container_width=True,
        key="analyze_main_button"
    )
    st.sidebar.caption("Cliquez pour analyser")

# ===== DÉTECTION DES CHANGEMENTS POUR MODE CONTINU =====
current_params = {
    'crypto': st.session_state.selected_crypto,
    'hours_history': hours_history,
    'hours_prediction': hours_prediction,
    'source': source_selected,
    'ma_short': ma_short_window,
    'ma_long': ma_long_window,
    'momentum': momentum_window
}

# Vérifier si on doit lancer l'analyse
should_analyze = False

if mode_continu:
    # En mode continu, analyser si les paramètres ont changé
    if params_changed(current_params) or st.session_state.force_refresh:
        should_analyze = True
        st.session_state.last_params = current_params.copy()
else:
    # En mode manuel, analyser seulement sur clic du bouton
    if 'analyze_button' in locals() and analyze_button:
        should_analyze = True
    elif st.session_state.force_refresh:
        should_analyze = True

# ===== INTERFACE PRINCIPALE =====
current_crypto = st.session_state.selected_crypto

st.header(f"🎯 Analyse ML : {current_crypto}")

# Métriques de configuration
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Crypto Active", current_crypto)
with col2:
    st.metric("Historique", f"{hours_history}h")
with col3:
    st.metric("Prédiction", f"{hours_prediction}h") 
with col4:
    mode_display = "🔄 Continu" if mode_continu else "🔘 Manuel"
    st.metric("Mode", mode_display)

# ===== LOGIQUE D'ANALYSE =====
if should_analyze:
    # Reset du flag de refresh
    if st.session_state.force_refresh:
        st.session_state.force_refresh = False
    
    if mode_continu:
        st.info(f"🔄 Analyse continue pour **{current_crypto}**...")
    else:
        st.info(f"🚀 Analyse ML en cours pour **{current_crypto}**...")
    
    # Récupération des données
    source_filter = None if source_selected == "Toutes" else source_selected
    
    try:
        with st.spinner("Récupération des données..."):
            data = get_crypto_data(current_crypto, hours_history, source_filter)
            
        if data.empty:
            st.error(f"❌ Pas de données pour **{current_crypto}** sur {hours_history}h")
            st.info("💡 Essayez une autre crypto ou réduisez la période d'historique")
            
        else:
            # Traitement des données
            data = data.sort_values('timestamp').reset_index(drop=True)
            
            with st.spinner("Calculs ML..."):
                # Calculs ML
                data_with_ma = calculate_moving_averages(data, ma_short_window, ma_long_window)
                data_with_trend, trend_slope = calculate_trend(data_with_ma)
                data_final = calculate_momentum(data_with_trend, momentum_window)
                
                # Prédictions
                predictions = predict_price(data_final, hours_prediction)
                confidence_metrics = calculate_confidence_metrics(data_final, predictions)
                
                # Stocker les résultats
                st.session_state.analysis_results = {
                    'data': data_final,
                    'predictions': predictions,
                    'confidence': confidence_metrics,
                    'trend_slope': trend_slope,
                    'crypto': current_crypto,
                    'params': current_params.copy(),
                    'timestamp': datetime.now()
                }
            
            if mode_continu:
                st.success(f"🔄 Analyse continue mise à jour pour **{current_crypto}**")
            else:
                st.success(f"✅ Analyse terminée pour **{current_crypto}**")
            
    except Exception as e:
        st.error(f"❌ Erreur lors de l'analyse: {str(e)}")
        st.session_state.analysis_results = None

# ===== AFFICHAGE DES RÉSULTATS =====
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    data_final = results['data']
    predictions = results['predictions']
    confidence_metrics = results['confidence']
    trend_slope = results['trend_slope']
    
    # Afficher l'horodatage de l'analyse
    if 'timestamp' in results:
        analysis_time = results['timestamp'].strftime("%H:%M:%S")
        st.caption(f"📊 Dernière analyse: {analysis_time}")
    
    # Métriques actuelles
    st.subheader("📊 Métriques de Prix")
    col1, col2, col3, col4 = st.columns(4)
    
    current_price = data_final['price'].iloc[-1]
    price_change = ((current_price - data_final['price'].iloc[0]) / data_final['price'].iloc[0]) * 100
    volatility = (data_final['price'].std() / data_final['price'].mean()) * 100
    
    with col1:
        st.metric("Prix Actuel", f"${current_price:.4f}")
    with col2:
        st.metric("Variation", f"{price_change:+.2f}%")
    with col3:
        st.metric("Volatilité", f"{volatility:.2f}%")
    with col4:
        st.metric("Points", len(data_final))
    
    # Graphique et prédictions
    st.subheader("📈 Graphique & Prédictions")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Graphique
        fig = go.Figure()
        
        # Prix réel
        fig.add_trace(go.Scatter(
            x=data_final['timestamp'],
            y=data_final['price'],
            mode='lines',
            name='Prix réel',
            line=dict(color='blue', width=2)
        ))
        
        # Moyennes mobiles
        fig.add_trace(go.Scatter(
            x=data_final['timestamp'],
            y=data_final['ma_short'],
            mode='lines',
            name=f'MA {ma_short_window}',
            line=dict(color='orange', width=1)
        ))
        
        fig.add_trace(go.Scatter(
            x=data_final['timestamp'],
            y=data_final['ma_long'],
            mode='lines',
            name=f'MA {ma_long_window}',
            line=dict(color='red', width=1)
        ))
        
        # Tendance
        fig.add_trace(go.Scatter(
            x=data_final['timestamp'],
            y=data_final['trend'],
            mode='lines',
            name='Tendance',
            line=dict(color='green', width=1, dash='dash')
        ))
        
        # Prédictions
        future_time = data_final['timestamp'].iloc[-1] + timedelta(hours=hours_prediction)
        
        # Points de prédiction
        for model, pred_price in predictions.items():
            if model != 'consensus':
                fig.add_trace(go.Scatter(
                    x=[future_time],
                    y=[pred_price],
                    mode='markers',
                    name=f'Pred {model}',
                    marker=dict(size=8)
                ))
        
        # Consensus
        fig.add_trace(go.Scatter(
            x=[future_time],
            y=[predictions['consensus']],
            mode='markers',
            name='CONSENSUS',
            marker=dict(size=12, color='black', symbol='star')
        ))
        
        fig.update_layout(
            title=f'Analyse ML - {current_crypto} {"(Mode Continu)" if mode_continu else ""}',
            xaxis_title='Temps',
            yaxis_title='Prix ($)',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Tableau des résultats
        st.markdown("#### 📋 Prédictions")
        
        results_data = []
        for model, pred_price in predictions.items():
            change_pct = ((pred_price - current_price) / current_price) * 100
            confidence = confidence_metrics[model]
            
            model_names = {
                'ma_short': f'MA {ma_short_window}',
                'ma_long': f'MA {ma_long_window}', 
                'trend': 'Tendance',
                'momentum': 'Momentum',
                'consensus': '⭐ CONSENSUS'
            }
            
            results_data.append({
                'Modèle': model_names.get(model, model),
                'Prix': f"${pred_price:.4f}",
                'Var.': f"{change_pct:+.2f}%",
                'Conf.': f"{confidence:.0f}%"
            })
        
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, hide_index=True, use_container_width=True)
        
        # Indicateur de mode
        if mode_continu:
            st.info("🔄 **Mode Continu**\nMise à jour automatique")
    
    # Signal de trading
    st.subheader("🎯 Signal de Trading")
    
    consensus_change = ((predictions['consensus'] - current_price) / current_price) * 100
    avg_confidence = np.mean(list(confidence_metrics.values()))
    
    if consensus_change > 2 and avg_confidence > 60:
        signal = "🟢 ACHAT"
    elif consensus_change < -2 and avg_confidence > 60:
        signal = "🔴 VENTE"
    else:
        signal = "🟡 HOLD"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Recommandation", signal)
    with col2:
        st.metric("Variation Consensus", f"{consensus_change:+.2f}%")
    with col3:
        st.metric("Confiance", f"{avg_confidence:.1f}%")

else:
    # Pas d'analyse
    if mode_continu:
        st.info(f"""
        **Mode Continu Activé pour {current_crypto}**
        
        🔄 **L'analyse se met à jour automatiquement** quand vous :
        - Changez de cryptomonnaie
        - Modifiez les paramètres (historique, prédiction, etc.)
        - Ajustez les modèles ML
        
        💡 **{len(crypto_list)} cryptomonnaies disponibles dans la sidebar**
        """)
    else:
        st.info(f"""
        **Prêt pour l'analyse de {current_crypto}**
        
        📝 **Étapes:**
        1. Sélectionnez une crypto avec les boutons dans la sidebar ⬅️
        2. Ajustez les paramètres si nécessaire
        3. Cliquez sur **"🚀 ANALYSER"**
        
        💡 **Astuce:** Activez le **"Mode Continu"** pour une mise à jour automatique !
        """)

# Avertissement
st.warning("⚠️ **Disclaimer:** Prédictions à des fins éducatives uniquement. Ne pas utiliser pour des décisions d'investissement.")

