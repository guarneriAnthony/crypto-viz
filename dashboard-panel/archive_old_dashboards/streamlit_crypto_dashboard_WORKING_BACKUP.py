"""
Dashboard Principal CryptoViz - Version Définitive avec Architecture Hybride
Historique MinIO (filtré intelligemment) + Stream Kafka temps réel
Gère automatiquement 7000+ fichiers Parquet sans surcharge
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import time
from datetime import datetime, timedelta
import logging
import sys
import os

# Import du data manager hybride
try:
    from utils.hybrid_data_manager import HybridDataManager
    DATA_MANAGER_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Hybrid Data Manager non disponible: {e}")
    DATA_MANAGER_AVAILABLE = False

# Configuration Streamlit
st.set_page_config(
    page_title="🚀 CryptoViz Dashboard Hybride",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS pour interface moderne
st.markdown("""
<style>
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Status cards */
    .status-card {
        background: white;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .status-card h4 {
        color: #333;
        margin: 0 0 10px 0;
        font-size: 16px;
    }
    
    .status-card p {
        color: #666;
        margin: 5px 0;
        font-size: 14px;
    }
    
    /* Métriques */
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        color: #667eea;
        margin: 0;
    }
    
    .metric-label {
        font-size: 14px;
        color: #666;
        margin: 5px 0 0 0;
    }
    
    /* Performance badges */
    .perf-badge-good {
        background: #28a745;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .perf-badge-warning {
        background: #ffc107;
        color: black;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    .perf-badge-danger {
        background: #dc3545;
        color: white;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    
    /* Graphiques */
    .chart-container {
        background: white;
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Tables */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Variables globales pour cache
if 'data_manager' not in st.session_state:
    if DATA_MANAGER_AVAILABLE:
        st.session_state.data_manager = HybridDataManager()
    else:
        st.session_state.data_manager = None

# FORCE RESTART CONSUMER KAFKA si inactif pour données live
if st.session_state.data_manager:
    dm = st.session_state.data_manager
    if not dm._kafka_consumer_active or len(dm._live_buffer) == 0:
        dm._kafka_consumer_active = False
        dm.start_kafka_consumer()

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = None

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🚀 CryptoViz Dashboard Hybride V4.0</h1>
    <p>📊 Historique MinIO (Filtré) + ⚡ Stream Kafka Temps Réel</p>
    <p style="font-size: 14px; opacity: 0.9;">Gestion intelligente de 7000+ fichiers Parquet</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Contrôles
with st.sidebar:
    st.header("⚙️ Configuration Dashboard")
    
    if not DATA_MANAGER_AVAILABLE:
        st.error("❌ Data Manager non disponible")
        st.stop()
    
    # Status du data manager
    status = st.session_state.data_manager.get_status()
    
    st.subheader("📊 Status Système")
    
    # MinIO Status
    minio_status = "🟢 Connecté" if status['minio_connected'] else "🔴 Déconnecté"
    st.markdown(f"""
    <div class="status-card">
        <h4>🗄️ MinIO S3</h4>
        <p>{minio_status}</p>
        <p>Historique: {"✅ Chargé" if status['historical_loaded'] else "⏳ En attente"}</p>
        <p>Points: {status['historical_count']:,}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Kafka Status
    kafka_status = "🟢 Actif" if status['kafka_active'] else "🔴 Inactif"
    st.markdown(f"""
    <div class="status-card">
        <h4>📨 Kafka Stream</h4>
        <p>{kafka_status}</p>
        <p>Buffer: {status['live_buffer_count']} messages</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Contrôles historique
    st.subheader("🔧 Configuration Historique")
    
    hours_back = st.slider("🕐 Heures d'historique", 6, 72, 24, 
                          help="Plus de données = plus lent")
    max_files = st.slider("📁 Max fichiers Parquet", 20, 300, 100, 
                         help="Limite pour éviter surcharge")
    
    if st.button("🔄 Recharger Historique", width="stretch"):
        with st.spinner("🔍 Rechargement historique..."):
            success = st.session_state.data_manager.refresh_historical(hours_back, max_files)
            if success:
                st.success("✅ Historique rechargé")
                st.session_state.last_refresh = datetime.now()
            else:
                st.error("❌ Erreur rechargement")
    
    st.divider()
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (15s)", value=True)
    
    if st.button("📊 Force Refresh Data", width="stretch"):
        st.rerun()
    
    # Performance info
    if st.session_state.last_refresh:
        time_since = datetime.now() - st.session_state.last_refresh
        st.caption(f"⏱️ Dernier refresh: {int(time_since.total_seconds())}s")

# Main content
# Récupération des données
if st.session_state.data_manager:
    start_time = time.time()
    
    with st.spinner("🔍 Chargement données hybrides..."):
        combined_data = st.session_state.data_manager.get_combined_data()
    
    load_time = time.time() - start_time
    
    if not combined_data.empty:
        
        # Header métriques
        col1, col2, col3, col4 = st.columns(4)
        
        total_points = len(combined_data)
        cryptos_count = combined_data['symbol'].nunique() if 'symbol' in combined_data.columns else 0
        
        # Calcul répartition sources
        source_counts = combined_data['data_source'].value_counts() if 'data_source' in combined_data.columns else {}
        historical_count = source_counts.get('historical', 0)
        live_count = source_counts.get('live', 0)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_points:,}</div>
                <div class="metric-label">📊 Total Points</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{cryptos_count}</div>
                <div class="metric-label">💎 Cryptos Actives</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{historical_count:,}</div>
                <div class="metric-label">📚 Historique</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{live_count}</div>
                <div class="metric-label">⚡ Live</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance badge
        perf_class = "perf-badge-good" if load_time < 2 else "perf-badge-warning" if load_time < 5 else "perf-badge-danger"
        st.markdown(f"""
        <div style="text-align: center; margin: 20px 0;">
            <span class="{perf_class}">⚡ Chargé en {load_time:.2f}s</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Graphiques principaux
        if 'symbol' in combined_data.columns and 'price' in combined_data.columns:
            
            col_chart, col_table = st.columns([3, 1])
            
            with col_chart:
                st.markdown('<div class="chart-container">', unsafe_allow_html=True)
                st.subheader("📈 Évolution Prix - Vue Hybride")
                
                # Top cryptos par volume de données
                top_cryptos = combined_data['symbol'].value_counts().head(8)
                
                # Créer subplots
                fig = make_subplots(
                    rows=2, cols=4,
                    subplot_titles=[f"{symbol} ({count} pts)" for symbol, count in top_cryptos.items()],
                    specs=[[{"secondary_y": False}]*4]*2,
                    vertical_spacing=0.15,
                    horizontal_spacing=0.1
                )
                
                colors = {'historical': '#1f77b4', 'live': '#ff7f0e'}
                
                for i, (symbol, _) in enumerate(top_cryptos.items()):
                    row = (i // 4) + 1
                    col = (i % 4) + 1
                    
                    symbol_data = combined_data[combined_data['symbol'] == symbol].copy()
                    
                    if 'timestamp' in symbol_data.columns:
                        symbol_data = symbol_data.sort_values('timestamp')
                    
                    # Séparer par source
                    for source in ['historical', 'live']:
                        if 'data_source' in symbol_data.columns:
                            source_data = symbol_data[symbol_data['data_source'] == source]
                        else:
                            source_data = symbol_data if source == 'historical' else pd.DataFrame()
                        
                        if not source_data.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=source_data['timestamp'] if 'timestamp' in source_data.columns else source_data.index,
                                    y=source_data['price'],
                                    mode='lines' if source == 'historical' else 'lines+markers',
                                    name=f'{symbol} ({source})',
                                    line=dict(color=colors[source], width=2 if source == 'live' else 1),
                                    marker=dict(size=3) if source == 'live' else None,
                                    showlegend=False
                                ),
                                row=row, col=col
                            )
                
                fig.update_layout(
                    height=600,
                    title_text="🔄 Données Hybrides: Historique (Bleu) + Live (Orange)",
                    showlegend=False
                )
                
                st.plotly_chart(fig, width="stretch")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_table:
                st.subheader("🔥 Dernières Données")
                
                # Table des dernières données
                if 'timestamp' in combined_data.columns:
                    recent_data = combined_data.sort_values('timestamp').tail(20)
                    
                    display_cols = ['symbol', 'price']
                    if 'data_source' in recent_data.columns:
                        display_cols.append('data_source')
                    if 'timestamp' in recent_data.columns:
                        display_cols.append('timestamp')
                    
                    display_data = recent_data[display_cols].copy()
                    
                    # Formatage
                    if 'price' in display_data.columns:
                        display_data['price'] = display_data['price'].round(6)
                    if 'timestamp' in display_data.columns:
                        display_data['timestamp'] = display_data['timestamp'].dt.strftime('%H:%M:%S')
                    
                    st.dataframe(
                        display_data.iloc[::-1],  # Inverser pour plus récent en premier
                        width="stretch",
                        height=400,
                        hide_index=True
                    )
                
                # Statistiques par crypto
                st.subheader("💎 Stats par Crypto")
                if 'symbol' in combined_data.columns:
                    crypto_stats = combined_data.groupby('symbol').agg({
                        'price': ['count', 'mean', 'std']
                    }).round(2)
                    crypto_stats.columns = ['Count', 'Avg Price', 'Volatility']
                    
                    st.dataframe(
                        crypto_stats.head(10),
                        width="stretch",
                        height=300
                    )
        
        # Performance et architecture info
        st.markdown("---")
        
        col_perf1, col_perf2 = st.columns(2)
        
        with col_perf1:
            st.subheader("🏗️ Architecture Hybride")
            st.markdown(f"""
            **📊 Sources de Données:**
            - 📚 **Historique MinIO**: {historical_count:,} points (filtrés sur {hours_back}h)
            - ⚡ **Live Kafka**: {live_count} points (buffer temps réel)
            - 🔗 **Total Combiné**: {total_points:,} points
            
            **🚀 Optimisations:**
            - 📁 Max {max_files} fichiers Parquet (sur 7000+)
            - ⏱️ Filtrage temporel intelligent
            - 🎯 Échantillonnage par récence
            - 🔄 Fusion automatique + dédoublonnage
            """)
        
        with col_perf2:
            st.subheader("📈 Performances")
            
            # Calcul métriques performance
            data_efficiency = (historical_count / 7000) * 100 if historical_count > 0 else 0
            
            st.markdown(f"""
            **⚡ Métriques Temps Réel:**
            - 🔍 **Temps de chargement**: {load_time:.2f}s
            - 📊 **Efficacité données**: {data_efficiency:.1f}% des 7000 fichiers
            - 🎯 **Cryptos actives**: {cryptos_count}
            - 📡 **Stream Kafka**: {"✅ Actif" if status['kafka_active'] else "❌ Inactif"}
            
            **🔧 Status Technique:**
            - 🗄️ **MinIO**: {"✅ Connecté" if status['minio_connected'] else "❌ Déconnecté"}
            - 📅 **Dernière MAJ**: {status['last_historical_load'][:19] if status['last_historical_load'] else 'Jamais'}
            """)
    
    else:
        st.warning("⚠️ Aucune donnée disponible. Vérifiez les connexions MinIO et Kafka.")
        
        # Debug info
        st.subheader("🔍 Debug Info")
        st.json(status)

else:
    st.error("❌ Data Manager non initialisé")

# Auto-refresh
if auto_refresh and st.session_state.data_manager:
    time.sleep(1)
    st.rerun()
