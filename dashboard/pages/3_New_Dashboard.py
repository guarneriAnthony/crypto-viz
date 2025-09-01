import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json

# Configuration de la page
st.set_page_config(
    page_title="CryptoViz Streaming Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# JavaScript pour le streaming temps réel
def inject_streaming_javascript():
    """Injection du JavaScript pour le streaming SSE"""
    js_code = """
    <script>
    console.log("🚀 Initialisation streaming CryptoViz...");
    
    let eventSource = null;
    let reconnectAttempts = 0;
    let maxReconnectAttempts = 5;
    let isConnected = false;
    let latestData = [];
    
    function connectToStream() {
        try {
            eventSource = new EventSource('http://localhost:5000/stream');
            
            eventSource.onopen = function(event) {
                console.log("✅ Connexion streaming établie");
                isConnected = true;
                reconnectAttempts = 0;
                updateStreamingStatus("🟢 Streaming actif", "success");
            };
            
            eventSource.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    console.log("📡 Message reçu:", data.type);
                    
                    if (data.type === 'welcome') {
                        console.log("👋 Bienvenue:", data.message);
                        updateStreamingStatus(`🟢 Connecté - ${data.client_id}`, "success");
                        
                    } else if (data.type === 'crypto_update') {
                        console.log("💰 Nouvelle crypto:", data.data.name, "$" + data.data.price.toFixed(2));
                        
                        // Stocker la donnée
                        latestData.push({
                            name: data.data.name,
                            price: data.data.price,
                            timestamp: data.timestamp,
                            change: data.data.percent_change_24h
                        });
                        
                        // Garder seulement les 50 dernières
                        if (latestData.length > 50) {
                            latestData = latestData.slice(-50);
                        }
                        
                        // Afficher notification
                        showCryptoNotification(data.data);
                        
                        // Déclencher refresh Streamlit après quelques données
                        if (latestData.length % 5 === 0) {
                            console.log("🔄 Déclenchement refresh dashboard...");
                            setTimeout(() => {
                                // Poster un message à Streamlit
                                window.parent.postMessage({
                                    type: 'streamlit:setQueryParams',
                                    data: {refresh: Date.now()}
                                }, '*');
                            }, 1000);
                        }
                        
                    } else if (data.type === 'heartbeat') {
                        const stats = data.stats || {};
                        updateStreamingStatus(
                            `🟢 Actif - ${stats.connected_clients} clients - ${stats.messages_sent} msg`, 
                            "success"
                        );
                    }
                    
                } catch (e) {
                    console.error("❌ Erreur parsing:", e);
                }
            };
            
            eventSource.onerror = function(event) {
                console.error("❌ Erreur streaming:", event);
                isConnected = false;
                updateStreamingStatus("🔴 Connexion perdue", "error");
                
                eventSource.close();
                
                if (reconnectAttempts < maxReconnectAttempts) {
                    reconnectAttempts++;
                    const delay = 3000 * reconnectAttempts;
                    console.log(`🔄 Reconnexion dans ${delay}ms (${reconnectAttempts}/${maxReconnectAttempts})`);
                    updateStreamingStatus(`🟡 Reconnexion ${reconnectAttempts}/${maxReconnectAttempts}...`, "warning");
                    setTimeout(connectToStream, delay);
                } else {
                    updateStreamingStatus("🔴 Streaming déconnecté", "error");
                }
            };
            
        } catch (e) {
            console.error("❌ Erreur init streaming:", e);
            updateStreamingStatus("🔴 Erreur connexion", "error");
        }
    }
    
    function updateStreamingStatus(message, type) {
        const statusElement = document.getElementById('streaming-status');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `streaming-status ${type}`;
        }
        
        // Mettre à jour aussi dans la sidebar
        const sidebarStatus = document.getElementById('sidebar-streaming-status');
        if (sidebarStatus) {
            sidebarStatus.textContent = message;
            sidebarStatus.className = `sidebar-status ${type}`;
        }
    }
    
    function showCryptoNotification(cryptoData) {
        // Créer une notification discrète
        const notification = document.createElement('div');
        notification.className = 'crypto-notification';
        notification.innerHTML = `
            <strong>${cryptoData.name}</strong>: $${cryptoData.price.toFixed(2)}
            <span class="${cryptoData.percent_change_24h >= 0 ? 'positive' : 'negative'}">
                ${cryptoData.percent_change_24h >= 0 ? '+' : ''}${cryptoData.percent_change_24h.toFixed(2)}%
            </span>
        `;
        
        document.body.appendChild(notification);
        
        // Supprimer après 3 secondes
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    // Auto-refresh périodique comme fallback
    function startPeriodicRefresh() {
        setInterval(() => {
            if (!isConnected) {
                console.log("📡 Pas de streaming - refresh périodique");
                window.location.reload();
            }
        }, 30000); // Toutes les 30 secondes si pas de streaming
    }
    
    // Démarrer au chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            connectToStream();
            startPeriodicRefresh();
        });
    } else {
        connectToStream();
        startPeriodicRefresh();
    }
    
    // Exposer les données pour debug
    window.cryptoVizStreaming = {
        latestData: latestData,
        isConnected: () => isConnected,
        reconnect: connectToStream
    };
    
    </script>
    
    <style>
    .streaming-status {
        padding: 8px 12px;
        border-radius: 6px;
        font-weight: 600;
        margin: 8px 0;
        display: inline-block;
        min-width: 200px;
        text-align: center;
    }
    
    .streaming-status.success {
        background-color: #d4edda;
        color: #155724;
        border: 1px solid #c3e6cb;
    }
    
    .streaming-status.warning {
        background-color: #fff3cd;
        color: #856404;
        border: 1px solid #ffeaa7;
    }
    
    .streaming-status.error {
        background-color: #f8d7da;
        color: #721c24;
        border: 1px solid #f5c6cb;
    }
    
    .sidebar-status {
        font-size: 0.8em;
        padding: 4px 8px;
        border-radius: 4px;
        margin: 4px 0;
    }
    
    .crypto-notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        z-index: 1000;
        font-size: 14px;
        max-width: 300px;
        animation: slideInRight 0.3s ease-out;
    }
    
    .crypto-notification .positive {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .crypto-notification .negative {
        color: #f44336;
        font-weight: bold;
    }
    
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    /* Style pour les métriques */
    .metric-streaming {
        border-left: 4px solid #1f77b4;
        padding-left: 10px;
        margin: 5px 0;
    }
    
    /* Animation pour les données qui changent */
    .data-updated {
        animation: pulse 0.5s ease-in-out;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    </style>
    """
    
    st.components.v1.html(js_code, height=0)

# Injecter le JavaScript
inject_streaming_javascript()

# Titre avec statut streaming
col_title, col_status = st.columns([3, 1])

with col_title:
    st.title("📊 CryptoViz - Dashboard Streaming Temps Réel")

with col_status:
    st.markdown('<div id="streaming-status" class="streaming-status">🔄 Connexion...</div>', unsafe_allow_html=True)

def get_connection():
    """Connexion DuckDB"""
    return duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=True)

def check_table_exists():
    """Vérifier si la table existe"""
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'crypto_prices'").fetchone()
        conn.close()
        return result[0] > 0
    except:
        return False

# Vérification table
if not check_table_exists():
    st.warning("⏳ En attente des données... Le système streaming se met en place.")
    st.info("📡 Le streaming est actif - les données arrivent en temps réel !")
    time.sleep(3)
    st.rerun()
    st.stop()

# Cache très court pour données temps réel
@st.cache_data(ttl=5)  # Cache de seulement 5 secondes
def get_cryptos_with_prices():
    try:
        conn = get_connection()
        result = conn.execute("""
            SELECT name, AVG(price) as avg_price, COUNT(*) as data_points,
                   MAX(timestamp) as last_update
            FROM crypto_prices 
            GROUP BY name 
            ORDER BY avg_price DESC
        """).fetchdf()
        conn.close()
        return result
    except:
        return pd.DataFrame()

@st.cache_data(ttl=3)  # Cache ultra-court
def get_latest_data():
    try:
        conn = get_connection()
        result = conn.execute("""
            SELECT name, symbol, price, percent_change_24h, market_cap, source, timestamp
            FROM crypto_prices 
            WHERE timestamp >= datetime('now', '-10 minutes')
            ORDER BY timestamp DESC 
            LIMIT 20
        """).fetchdf()
        conn.close()
        return result
    except:
        return pd.DataFrame()

@st.cache_data(ttl=2)  # Métriques temps réel
def get_streaming_metrics():
    try:
        conn = get_connection()
        
        # Métriques générales
        total_records = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        unique_cryptos = conn.execute("SELECT COUNT(DISTINCT name) FROM crypto_prices").fetchone()[0]
        latest_update = conn.execute("SELECT MAX(timestamp) FROM crypto_prices").fetchone()[0]
        
        # Données récentes (dernières 10 minutes)
        recent_count = conn.execute("""
            SELECT COUNT(*) FROM crypto_prices 
            WHERE timestamp >= datetime('now', '-10 minutes')
        """).fetchone()[0]
        
        # Données par source
        sources = conn.execute("""
            SELECT source, COUNT(*) as count 
            FROM crypto_prices 
            GROUP BY source
        """).fetchall()
        
        conn.close()
        
        return {
            'total_records': total_records,
            'unique_cryptos': unique_cryptos,
            'latest_update': latest_update,
            'recent_count': recent_count,
            'sources': dict(sources)
        }
    except Exception as e:
        st.error(f"Erreur métriques: {e}")
        return {}

# Sidebar avec contrôles streaming
st.sidebar.header("🎛️ Contrôles Streaming")

# Status streaming dans sidebar
st.sidebar.markdown('<div id="sidebar-streaming-status" class="sidebar-status">Connexion...</div>', unsafe_allow_html=True)

# Contrôles
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh", value=True)
refresh_interval = st.sidebar.selectbox("Intervalle:", [2, 5, 10, 15], index=0)

if st.sidebar.button("🔄 Refresh Manuel"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("🔗 Reconnecter Stream"):
    st.markdown('<script>window.cryptoVizStreaming.reconnect();</script>', unsafe_allow_html=True)

# Métriques temps réel
st.header("📊 Métriques Temps Réel")

metrics = get_streaming_metrics()

if metrics:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "📈 Total Records", 
            f"{metrics['total_records']:,}",
            delta=f"+{metrics.get('recent_count', 0)} (10min)",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "💰 Cryptos Suivies", 
            metrics['unique_cryptos']
        )
    
    with col3:
        if metrics['latest_update']:
            age_seconds = (datetime.now() - metrics['latest_update']).total_seconds()
            st.metric(
                "🕐 Dernière Donnée", 
                f"{age_seconds:.0f}s",
                delta="Streaming actif" if age_seconds < 300 else "Données anciennes",
                delta_color="normal" if age_seconds < 300 else "inverse"
            )
    
    with col4:
        sources_text = ", ".join([f"{k}({v})" for k, v in metrics.get('sources', {}).items()])
        st.metric("📡 Sources", sources_text[:20] + "...")

# Données temps réel
st.header("⚡ Données Temps Réel (Dernières 10 min)")

latest_data = get_latest_data()

if not latest_data.empty:
    # Formatage pour affichage
    display_data = latest_data.copy()
    display_data['price'] = display_data['price'].apply(lambda x: f"${x:,.2f}")
    display_data['percent_change_24h'] = display_data['percent_change_24h'].apply(
        lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A"
    )
    display_data['market_cap'] = display_data['market_cap'].apply(
        lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A"
    )
    
    # Colorier les variations
    def color_change(val):
        if val.startswith('+'):
            return 'background-color: #d4edda'
        elif val.startswith('-'):
            return 'background-color: #f8d7da'
        return ''
    
    styled_data = display_data.style.applymap(color_change, subset=['percent_change_24h'])
    st.dataframe(styled_data, use_container_width=True, height=300)
    
    # Graphique temps réel
    if len(latest_data) > 1:
        st.subheader("📈 Évolution Temps Réel")
        
        fig = px.scatter(
            latest_data, 
            x='timestamp', 
            y='price', 
            color='name',
            size='market_cap',
            hover_data=['percent_change_24h'],
            title="Prix en Temps Réel (10 dernières minutes)"
        )
        
        fig.update_layout(
            height=500,
            showlegend=True,
            xaxis_title="Temps",
            yaxis_title="Prix (USD)"
        )
        
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("📡 En attente des premières données streaming...")
    st.markdown("Le système collecte les données toutes les 2 minutes. Patientez quelques instants.")

# Graphiques historiques (cache plus long)
cryptos_data = get_cryptos_with_prices()

if not cryptos_data.empty:
    st.header("📊 Vue d'Ensemble")
    
    # Sélection des cryptos
    selected_cryptos = st.multiselect(
        "Cryptomonnaies à analyser:",
        options=cryptos_data['name'].tolist(),
        default=cryptos_data['name'].head(3).tolist()
    )
    
    if selected_cryptos:
        # Récupérer données historiques
        crypto_list_str = "', '".join(selected_cryptos)
        
        @st.cache_data(ttl=30)  # Cache de 30s pour historique
        def get_historical_data(crypto_names):
            conn = get_connection()
            query = f"""
                SELECT name, price, timestamp, percent_change_24h
                FROM crypto_prices 
                WHERE name IN ('{crypto_names}')
                AND timestamp >= datetime('now', '-24 hours')
                ORDER BY timestamp
            """
            result = conn.execute(query).fetchdf()
            conn.close()
            return result
        
        historical = get_historical_data(crypto_list_str)
        
        if not historical.empty:
            fig = px.line(
                historical,
                x='timestamp',
                y='price',
                color='name',
                title=f"Évolution 24h - {', '.join(selected_cryptos)}",
                labels={'price': 'Prix (USD)', 'timestamp': 'Temps'}
            )
            
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

# Auto-refresh JavaScript
if auto_refresh:
    st.markdown(f"""
    <script>
    setTimeout(function() {{
        if (!window.cryptoVizStreaming.isConnected()) {{
            location.reload();
        }}
    }}, {refresh_interval * 1000});
    </script>
    """, unsafe_allow_html=True)

# Debug info
with st.expander("🔧 Debug Streaming"):
    st.markdown("""
    **Status Streaming:**
    - Les données arrivent toutes les 2 minutes
    - Les graphiques se rafraîchissent automatiquement  
    - Le cache est de 2-5 secondes seulement
    
    **Console JavaScript:** Ouvrez F12 > Console pour voir les logs streaming
    """)
    
    if st.button("Clear Cache"):
        st.cache_data.clear()
        st.success("Cache effacé !")
        
    st.markdown("**Données JavaScript:** `window.cryptoVizStreaming.latestData`")