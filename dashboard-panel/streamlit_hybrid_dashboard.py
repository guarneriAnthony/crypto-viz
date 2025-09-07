"""
Dashboard Hybride Optimisé - Historique MinIO (filtré) + Stream Temps Réel Kafka
Architecture: Historique récent (24h, max 100 fichiers) + Updates live
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
import json
from kafka import KafkaConsumer
from datetime import datetime, timedelta
import threading
from collections import deque, defaultdict
import logging
import sys
import os

# Ajouter le path pour imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.smart_historical_reader import get_smart_reader
    HISTORICAL_READER_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Smart Historical Reader non disponible: {e}")
    HISTORICAL_READER_AVAILABLE = False

# Configuration Streamlit
st.set_page_config(
    page_title="🔄 CryptoViz Hybride - Historique + Live",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS optimisé pour lisibilité
st.markdown("""
<style>
    .hybrid-header {
        background: linear-gradient(90deg, #1f4037 0%, #99f2c8 100%);
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        color: white;
        text-align: center;
    }
    
    .data-source-card {
        background-color: white;
        color: black;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .historical-badge {
        background-color: #28a745;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .live-badge {
        background-color: #dc3545;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .crypto-metric {
        background-color: white;
        color: black;
        padding: 10px;
        border-radius: 6px;
        text-align: center;
        margin: 5px 0;
    }
    
    .performance-info {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 6px;
        padding: 10px;
        margin: 10px 0;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# Variables globales pour les données
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = pd.DataFrame()
if 'live_data_buffer' not in st.session_state:
    st.session_state.live_data_buffer = deque(maxlen=1000)  # Buffer circulaire
if 'combined_data' not in st.session_state:
    st.session_state.combined_data = pd.DataFrame()
if 'last_historical_load' not in st.session_state:
    st.session_state.last_historical_load = None
if 'kafka_consumer_active' not in st.session_state:
    st.session_state.kafka_consumer_active = False

# Header hybride
st.markdown("""
<div class="hybrid-header">
    <h1>🔄 Dashboard Hybride CryptoViz</h1>
    <p>📊 Données Historiques MinIO (filtrées) + ⚡ Stream Temps Réel Kafka</p>
</div>
""", unsafe_allow_html=True)

def load_historical_data_smart(hours_back=24, max_files=100):
    """Charge les données historiques de manière optimisée"""
    if not HISTORICAL_READER_AVAILABLE:
        st.warning("⚠️ Reader historique non disponible")
        return pd.DataFrame()
    
    try:
        with st.spinner(f"🔍 Chargement historique optimisé: {hours_back}h, max {max_files} fichiers..."):
            reader = get_smart_reader()
            
            start_time = time.time()
            historical_df = reader.load_recent_historical_data(
                hours_back=hours_back, 
                max_files=max_files
            )
            load_time = time.time() - start_time
            
            if not historical_df.empty:
                st.success(f"✅ Historique chargé: {len(historical_df)} lignes en {load_time:.1f}s")
                logger.info(f"📊 Données historiques: {len(historical_df)} lignes, {historical_df['symbol'].nunique() if 'symbol' in historical_df.columns else 0} cryptos")
            else:
                st.warning("⚠️ Aucune donnée historique trouvée")
            
            return historical_df
            
    except Exception as e:
        st.error(f"❌ Erreur chargement historique: {e}")
        logger.error(f"Erreur historique: {e}")
        return pd.DataFrame()

def start_kafka_consumer_thread():
    """Démarre le consumer Kafka en arrière-plan"""
    if st.session_state.kafka_consumer_active:
        return
    
    def kafka_consumer_worker():
        try:
            consumer = KafkaConsumer(
                'crypto-streaming',
                bootstrap_servers=['redpanda:9092'],
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                consumer_timeout_ms=5000,
                auto_offset_reset='latest'
            )
            
            st.session_state.kafka_consumer_active = True
            logger.info("🎯 Kafka consumer démarré")
            
            for message in consumer:
                try:
                    crypto_data = message.value
                    crypto_data['source'] = 'live'
                    crypto_data['received_at'] = datetime.now().isoformat()
                    
                    # Ajouter au buffer circulaire
                    st.session_state.live_data_buffer.append(crypto_data)
                    
                    logger.debug(f"📨 Live data: {crypto_data.get('symbol', 'Unknown')} = ${crypto_data.get('price', 0)}")
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur processing message Kafka: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"❌ Erreur Kafka consumer: {e}")
            st.session_state.kafka_consumer_active = False
    
    # Démarrer le thread
    kafka_thread = threading.Thread(target=kafka_consumer_worker, daemon=True)
    kafka_thread.start()

def combine_historical_and_live_data():
    """Combine les données historiques avec les données live"""
    try:
        historical_df = st.session_state.historical_data.copy()
        
        # Convertir le buffer live en DataFrame
        if st.session_state.live_data_buffer:
            live_data_list = list(st.session_state.live_data_buffer)
            live_df = pd.DataFrame(live_data_list)
            
            # Normaliser les colonnes live
            if 'timestamp' not in live_df.columns and 'received_at' in live_df.columns:
                live_df['timestamp'] = pd.to_datetime(live_df['received_at'])
            
            # Marquer la source
            if not historical_df.empty:
                historical_df['data_source'] = 'historical'
            if not live_df.empty:
                live_df['data_source'] = 'live'
            
            # Combiner
            if not historical_df.empty and not live_df.empty:
                # S'assurer que les colonnes sont compatibles
                common_cols = set(historical_df.columns) & set(live_df.columns)
                
                if common_cols:
                    historical_subset = historical_df[list(common_cols)]
                    live_subset = live_df[list(common_cols)]
                    
                    combined = pd.concat([historical_subset, live_subset], ignore_index=True)
                    
                    if 'timestamp' in combined.columns:
                        combined = combined.sort_values('timestamp')
                        # Dédoublonnage (garder live en priorité)
                        if 'symbol' in combined.columns:
                            combined = combined.drop_duplicates(subset=['symbol', 'timestamp'], keep='last')
                    
                    return combined
            
            elif not live_df.empty:
                return live_df
            elif not historical_df.empty:
                return historical_df
        
        return historical_df
        
    except Exception as e:
        logger.error(f"❌ Erreur combinaison données: {e}")
        return st.session_state.historical_data

# Sidebar - Contrôles
with st.sidebar:
    st.header("⚙️ Configuration Hybride")
    
    # Contrôles historique
    st.subheader("📊 Données Historiques")
    
    hours_back = st.slider("🕐 Heures d'historique", 1, 72, 24, help="Plus = plus de données, mais plus lent")
    max_files = st.slider("📁 Max fichiers Parquet", 10, 200, 100, help="Limite pour éviter de surcharger")
    
    if st.button("🔄 Recharger Historique", use_container_width=True):
        st.session_state.historical_data = load_historical_data_smart(hours_back, max_files)
        st.session_state.last_historical_load = datetime.now()
    
    # Status historique
    if not st.session_state.historical_data.empty:
        hist_cryptos = st.session_state.historical_data['symbol'].nunique() if 'symbol' in st.session_state.historical_data.columns else 0
        st.markdown(f"""
        <div class="data-source-card">
            <span class="historical-badge">HISTORIQUE</span><br>
            📊 <strong>{len(st.session_state.historical_data)} lignes</strong><br>
            💎 <strong>{hist_cryptos} cryptos</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Contrôles live
    st.subheader("⚡ Stream Temps Réel")
    
    if st.button("🎯 Démarrer Stream Kafka", use_container_width=True):
        start_kafka_consumer_thread()
        time.sleep(1)  # Laisser le temps au thread de démarrer
    
    # Status live
    if st.session_state.kafka_consumer_active:
        live_count = len(st.session_state.live_data_buffer)
        st.markdown(f"""
        <div class="data-source-card">
            <span class="live-badge">LIVE</span><br>
            📡 <strong>{live_count} messages</strong><br>
            🔄 <strong>En cours...</strong>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (10s)", value=True)
    
    if auto_refresh:
        time.sleep(0.1)
        st.rerun()

# Chargement initial des données historiques
if st.session_state.historical_data.empty and st.session_state.last_historical_load is None:
    st.session_state.historical_data = load_historical_data_smart(hours_back=hours_back, max_files=max_files)
    st.session_state.last_historical_load = datetime.now()

# Démarrer Kafka automatiquement
if not st.session_state.kafka_consumer_active:
    start_kafka_consumer_thread()

# Combiner les données
st.session_state.combined_data = combine_historical_and_live_data()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📈 Graphiques Hybrides")
    
    if not st.session_state.combined_data.empty:
        # Vérifier les sources de données
        data_sources = st.session_state.combined_data['data_source'].value_counts() if 'data_source' in st.session_state.combined_data.columns else {}
        
        st.markdown(f"""
        <div class="performance-info">
            <strong>📊 Sources de données actives:</strong><br>
            📚 Historique: {data_sources.get('historical', 0)} points<br>
            ⚡ Live: {data_sources.get('live', 0)} points<br>
            🔗 Total combiné: {len(st.session_state.combined_data)} points
        </div>
        """, unsafe_allow_html=True)
        
        # Graphique principal
        if 'symbol' in st.session_state.combined_data.columns and 'price' in st.session_state.combined_data.columns:
            
            # Top cryptos par activité
            top_cryptos = st.session_state.combined_data['symbol'].value_counts().head(6)
            
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=[f"{symbol} ({count} pts)" for symbol, count in top_cryptos.items()],
                specs=[[{"secondary_y": False}]*3]*2
            )
            
            for i, (symbol, _) in enumerate(top_cryptos.items()):
                row = (i // 3) + 1
                col = (i % 3) + 1
                
                symbol_data = st.session_state.combined_data[
                    st.session_state.combined_data['symbol'] == symbol
                ].sort_values('timestamp') if 'timestamp' in st.session_state.combined_data.columns else st.session_state.combined_data[
                    st.session_state.combined_data['symbol'] == symbol
                ]
                
                if not symbol_data.empty:
                    # Données historiques
                    hist_data = symbol_data[symbol_data['data_source'] == 'historical'] if 'data_source' in symbol_data.columns else symbol_data
                    if not hist_data.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=hist_data['timestamp'] if 'timestamp' in hist_data.columns else hist_data.index,
                                y=hist_data['price'],
                                mode='lines',
                                name=f'{symbol} (Hist)',
                                line=dict(color='blue', width=1),
                                showlegend=False
                            ),
                            row=row, col=col
                        )
                    
                    # Données live
                    live_data = symbol_data[symbol_data['data_source'] == 'live'] if 'data_source' in symbol_data.columns else pd.DataFrame()
                    if not live_data.empty:
                        fig.add_trace(
                            go.Scatter(
                                x=live_data['timestamp'] if 'timestamp' in live_data.columns else live_data.index,
                                y=live_data['price'],
                                mode='markers+lines',
                                name=f'{symbol} (Live)',
                                line=dict(color='red', width=2),
                                marker=dict(size=4, color='red'),
                                showlegend=False
                            ),
                            row=row, col=col
                        )
            
            fig.update_layout(
                height=600,
                title_text="🔄 Vue Hybride: Historique (Bleu) + Live (Rouge)",
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        else:
            st.warning("⚠️ Colonnes 'symbol' ou 'price' manquantes dans les données")
    
    else:
        st.info("📊 En attente de données... Chargement historique + stream live en cours...")

with col2:
    st.subheader("📊 Métriques Hybrides")
    
    if not st.session_state.combined_data.empty:
        
        # Métriques globales
        total_cryptos = st.session_state.combined_data['symbol'].nunique() if 'symbol' in st.session_state.combined_data.columns else 0
        total_points = len(st.session_state.combined_data)
        
        st.markdown(f"""
        <div class="crypto-metric">
            <h3>💎 {total_cryptos}</h3>
            <p>Cryptos Actives</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="crypto-metric">
            <h3>📊 {total_points:,}</h3>
            <p>Points de Données</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Performance système
        if st.session_state.last_historical_load:
            time_since_load = datetime.now() - st.session_state.last_historical_load
            st.markdown(f"""
            <div class="crypto-metric">
                <h3>⏱️ {int(time_since_load.total_seconds())}s</h3>
                <p>Depuis Dernier Chargement</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Buffer live
        live_buffer_size = len(st.session_state.live_data_buffer)
        st.markdown(f"""
        <div class="crypto-metric">
            <h3>📡 {live_buffer_size}</h3>
            <p>Messages Live Buffer</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Tableau récent
        if 'symbol' in st.session_state.combined_data.columns:
            st.subheader("🔥 Dernières Données")
            
            recent_data = st.session_state.combined_data.tail(10)[
                ['symbol', 'price', 'data_source', 'timestamp']
            ] if set(['symbol', 'price', 'data_source', 'timestamp']).issubset(st.session_state.combined_data.columns) else st.session_state.combined_data.tail(10)
            
            st.dataframe(recent_data, use_container_width=True, height=300)

# Footer informatif
st.markdown("---")
st.markdown("""
<div class="performance-info">
    <strong>🏗️ Architecture Hybride:</strong><br>
    📊 <strong>Historique</strong>: MinIO S3 (filtrées sur 24h, max 100 fichiers)<br>
    ⚡ <strong>Live</strong>: Stream Kafka temps réel<br>
    🔄 <strong>Combiné</strong>: Fusion intelligente avec dédoublonnage<br>
    🚀 <strong>Performance</strong>: Équilibre entre complétude et rapidité
</div>
""", unsafe_allow_html=True)
