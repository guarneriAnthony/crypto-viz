"""
Page ML Predictions Redis - Architecture standard temps réel
Ultra-rapide: Redis → Dashboard (millisecondes vs minutes MinIO)
"""
import streamlit as st
import sys
import os
import plotly.graph_objects as go
from datetime import datetime
import time

# Ajouter le dossier parent au path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.redis_ml_client import RedisMLClient, get_crypto_predictions, get_available_ml_cryptos, test_ml_connection, normalize_crypto_name
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Configuration de la page
st.set_page_config(page_title="ML Predictions - CryptoViz", layout="wide")

st.title("🤖 ML Predictions - Temps Réel")
st.markdown("*Prédictions ultra-rapides via architecture standard Kafka→ML→Redis→Dashboard*")

# Vérification des dépendances
if not REDIS_AVAILABLE:
    st.error("❌ Module Redis non disponible. Vérifiez l'installation de redis-py.")
    st.stop()

# Test de connexion Redis
if not test_ml_connection():
    st.error("❌ **Connexion Redis ML indisponible**")
    st.info("📋 **Solutions:**")
    st.markdown("""
    1. Vérifiez que Redis est démarré: `docker-compose up -d redis`
    2. Démarrez le ML Processor: `docker-compose up -d ml-processor`  
    3. Attendez quelques minutes pour l'accumulation des données
    """)
    st.stop()

# Client Redis
client = RedisMLClient()

# ===== SIDEBAR =====
with st.sidebar:
    st.header("⚡ ML Temps Réel")
    
    # Statistiques système
    stats = client.get_ml_stats()
    st.metric("📊 Cryptos ML", stats.get('available_cryptos', 0))
    st.metric("🔗 Source", stats.get('data_source', 'N/A'))
    
    if stats.get('last_update'):
        st.metric("🕐 Dernière MAJ", datetime.fromisoformat(stats['last_update']).strftime('%H:%M:%S'))
    
    # Liste des cryptos disponibles
    st.subheader("💎 Cryptos Disponibles")
    available_cryptos = get_available_ml_cryptos()
    
    if not available_cryptos:
        st.warning("Aucune crypto ML disponible. Le ML Processor accumule les données...")
        st.stop()
    
    # Mapping symbol → nom pour affichage
    symbol_to_name = {
        'BTC': 'Bitcoin', 'ETH': 'Ethereum', 'BNB': 'Binance Coin',
        'ADA': 'Cardano', 'SOL': 'Solana', 'XRP': 'XRP',
        'DOT': 'Polkadot', 'DOGE': 'Dogecoin', 'AVAX': 'Avalanche',
        'SHIB': 'Shiba Inu', 'MATIC': 'Polygon', 'LTC': 'Litecoin'
    }
    
    # Affichage des cryptos avec boutons
    selected_crypto = None
    for symbol in sorted(available_cryptos):
        name = symbol_to_name.get(symbol, symbol)
        
        if st.button(f"📊 {name} ({symbol})", width="stretch"):
            selected_crypto = symbol
    
    # Auto-refresh
    if st.checkbox("🔄 Auto-refresh (10s)", value=True):
        time.sleep(0.1)  # Petit délai pour éviter les refreshs trop rapides
        st.rerun()

# ===== CONTENU PRINCIPAL =====

if not selected_crypto:
    # Vue d'ensemble de toutes les cryptos
    st.subheader("🌍 Vue d'Ensemble ML")
    
    start_time = time.time()
    all_predictions = client.get_all_predictions()
    load_time = time.time() - start_time
    
    st.info(f"⚡ Données chargées en **{load_time*1000:.1f}ms** depuis Redis")
    
    if all_predictions:
        # Tableau de synthèse
        summary_data = []
        for symbol, pred in all_predictions.items():
            name = symbol_to_name.get(symbol, symbol)
            current = pred['current_price']
            ma_pred = pred['predictions']['moving_average_1h']
            trend_pred = pred['predictions']['linear_trend_1h'] 
            signal = pred['signals']['trading']
            change = pred['signals']['change_pct']
            
            summary_data.append({
                'Crypto': f"{name} ({symbol})",
                'Prix Actuel': f"${current:,.2f}",
                'MA Pred (+1h)': f"${ma_pred:,.2f}",
                'Trend Pred (+1h)': f"${trend_pred:,.2f}",
                'Signal': signal,
                'Variation': f"{change:+.1f}%"
            })
        
        st.dataframe(summary_data, width="stretch")
        
        # Signaux de trading
        buy_signals = [d for d in summary_data if 'BUY' in d['Signal']]
        sell_signals = [d for d in summary_data if 'SELL' in d['Signal']]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🟢 Signaux ACHAT", len(buy_signals))
        with col2:
            st.metric("🔴 Signaux VENTE", len(sell_signals))
        with col3:
            st.metric("🟡 Signaux HOLD", len(summary_data) - len(buy_signals) - len(sell_signals))
    
    else:
        st.warning("Aucune prédiction disponible. Le ML Processor accumule les données...")

else:
    # Détail d'une crypto sélectionnée  
    crypto_name = symbol_to_name.get(selected_crypto, selected_crypto)
    st.subheader(f"🔍 Analyse ML Détaillée - {crypto_name} ({selected_crypto})")
    
    start_time = time.time()
    predictions = get_crypto_predictions(selected_crypto)
    load_time = time.time() - start_time
    
    st.info(f"⚡ Prédictions chargées en **{load_time*1000:.1f}ms** depuis Redis")
    
    if predictions:
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "💰 Prix Actuel", 
                f"${predictions['current_price']:,.2f}",
                help="Prix en temps réel depuis Kafka"
            )
        
        with col2:
            ma_pred = predictions['predictions']['moving_average_1h']
            current = predictions['current_price']
            change = ((ma_pred - current) / current) * 100
            st.metric(
                "📈 Moyenne Mobile (+1h)", 
                f"${ma_pred:,.2f}",
                f"{change:+.1f}%"
            )
        
        with col3:
            trend_pred = predictions['predictions']['linear_trend_1h']
            trend_change = ((trend_pred - current) / current) * 100
            st.metric(
                "📊 Tendance Linéaire (+1h)", 
                f"${trend_pred:,.2f}",
                f"{trend_change:+.1f}%"
            )
        
        # Signal de trading
        signal = predictions['signals']['trading']
        strength = predictions['signals']['strength']
        change_pct = predictions['signals']['change_pct']
        
        if signal == 'BUY':
            st.success(f"🟢 **SIGNAL ACHAT** ({strength}) - Variation prévue: {change_pct:+.1f}%")
        elif signal == 'SELL':
            st.error(f"🔴 **SIGNAL VENTE** ({strength}) - Variation prévue: {change_pct:+.1f}%")
        else:
            st.info(f"🟡 **SIGNAL HOLD** ({strength}) - Variation prévue: {change_pct:+.1f}%")
        
        # Graphique des prédictions 6h
        st.subheader("📈 Prédictions 6 Heures")
        
        fig = go.Figure()
        
        # Prix actuel (point de référence)
        fig.add_trace(go.Scatter(
            x=[0],
            y=[current],
            mode='markers',
            name='Prix Actuel',
            marker=dict(size=12, color='blue')
        ))
        
        # Prédictions différents modèles
        hours = list(range(1, 7))
        
        fig.add_trace(go.Scatter(
            x=hours,
            y=predictions['predictions']['moving_average_6h'],
            mode='lines+markers',
            name=f"Moyenne Mobile (conf: {predictions['confidence']['moving_average']:.0%})",
            line=dict(color='orange', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=hours,
            y=predictions['predictions']['linear_trend_6h'],
            mode='lines+markers', 
            name=f"Tendance Linéaire (conf: {predictions['confidence']['linear_trend']:.0%})",
            line=dict(color='green', dash='dash')
        ))
        
        fig.add_trace(go.Scatter(
            x=hours,
            y=predictions['predictions']['momentum_6h'],
            mode='lines+markers',
            name=f"Momentum (conf: {predictions['confidence']['momentum']:.0%})",
            line=dict(color='red', dash='dash')
        ))
        
        fig.update_layout(
            title=f"Prédictions ML - {crypto_name} ({selected_crypto})",
            xaxis_title="Heures (+)",
            yaxis_title="Prix USD",
            hovermode='x unified',
            height=500
        )
        
        st.plotly_chart(fig, width="stretch")
        
        # Détails techniques
        with st.expander("🔧 Détails Techniques"):
            st.write(f"**Symbol:** {selected_crypto}")
            st.write(f"**Dernière mise à jour:** {predictions['last_update']}")
            st.write(f"**Prix actuel:** ${predictions['current_price']:,.2f}")
            
            st.subheader("Niveaux de Confiance")
            for model, conf in predictions['confidence'].items():
                st.progress(conf, text=f"{model.replace('_', ' ').title()}: {conf:.0%}")
        
    else:
        st.error(f"❌ Aucune prédiction disponible pour {crypto_name} ({selected_crypto})")

# Footer
st.markdown("---")
st.markdown("*CryptoViz V3.0 - Architecture ML Temps Réel: Kafka → ML Processor → Redis → Dashboard*")

# Debug info
with st.expander("🐛 Informations Debug"):
    st.write(f"**Cryptos ML disponibles:** {len(available_cryptos)}")
    st.write(f"**Cryptos:** {', '.join(available_cryptos)}")
    st.write(f"**Redis connexion:** {'✅ OK' if test_ml_connection() else '❌ KO'}")
    st.write(f"**Timestamp:** {datetime.now().strftime('%H:%M:%S')}")
