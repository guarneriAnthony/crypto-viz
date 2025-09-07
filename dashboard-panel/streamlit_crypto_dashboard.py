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

# Configuration Streamlit
st.set_page_config(
    page_title="🚀 CryptoViz Live Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CSS pour styling professionnel
st.markdown("""
<style>
    .crypto-table {
        background-color: #0E1117;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .crypto-row {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        border-bottom: 1px solid #262730;
        transition: background-color 0.2s;
        cursor: pointer;
    }
    
    .crypto-row:hover {
        background-color: #262730;
    }
    
    .crypto-rank {
        width: 40px;
        color: #8B949E;
        font-size: 14px;
    }
    
    .crypto-info {
        display: flex;
        align-items: center;
        width: 200px;
    }
    
    .crypto-logo {
        width: 24px;
        height: 24px;
        margin-right: 8px;
        border-radius: 50%;
    }
    
    .crypto-name {
        color: #F0F6FC;
        font-weight: 600;
        font-size: 14px;
    }
    
    .crypto-symbol {
        color: #8B949E;
        font-size: 12px;
        margin-left: 4px;
    }
    
    .crypto-price {
        width: 120px;
        color: #F0F6FC;
        font-weight: 600;
        font-size: 14px;
    }
    
    .crypto-change {
        width: 80px;
        font-weight: 600;
        font-size: 13px;
    }
    
    .positive {
        color: #3FB68B;
    }
    
    .negative {
        color: #FF6B6B;
    }
    
    .crypto-volume {
        width: 120px;
        color: #8B949E;
        font-size: 13px;
    }
    
    .crypto-market-cap {
        width: 140px;
        color: #8B949E;
        font-size: 13px;
    }
    
    .crypto-sparkline {
        width: 120px;
        height: 40px;
    }
    
    .status-live {
        color: #3FB68B;
        font-size: 11px;
        font-weight: 500;
    }
    
    .status-loading {
        color: #FFA726;
        font-size: 11px;
        font-weight: 500;
    }
    
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    
    .table-header {
        display: flex;
        align-items: center;
        padding: 12px 16px;
        background-color: #161B22;
        color: #8B949E;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitCryptoDashboard:
    def __init__(self):
        self.kafka_broker = 'crypto_redpanda:9092'
        self.raw_topic = 'crypto-raw-data'
        
        # Buffers pour les données (thread-safe avec des locks légers)
        self.crypto_data = defaultdict(lambda: deque(maxlen=1000))
        self.latest_prices = {}
        self.latest_changes = {}
        
        # État de connexion
        self.kafka_connected = False
        self.last_update = None
        self.message_count = 0
        
        # Initialiser avec des données par défaut
        self.init_default_data()
        
        # Démarrer le consumer Kafka une seule fois
        if not hasattr(st.session_state, 'kafka_started'):
            self.setup_kafka_consumer()
            st.session_state.kafka_started = True
    
    def init_default_data(self):
        """Initialise avec des données par défaut"""
        cryptos = ['BTC', 'ETH', 'USDT', 'XRP', 'BNB', 'SOL', 'DOGE', 'TRX', 'ADA']
        default_prices = {
            'BTC': 94016.04, 'ETH': 3647.18, 'USDT': 1.0, 'XRP': 2.83,
            'BNB': 680.50, 'SOL': 203.45, 'DOGE': 0.22, 'TRX': 0.33, 'ADA': 0.83
        }
        
        for symbol in cryptos:
            self.latest_prices[symbol] = default_prices.get(symbol, 100)
            self.latest_changes[symbol] = 0.0
    
    def setup_kafka_consumer(self):
        """Démarre le consumer Kafka en arrière-plan"""
        
        def consume_kafka_data():
            try:
                consumer = KafkaConsumer(
                    self.raw_topic,
                    bootstrap_servers=[self.kafka_broker],
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                    auto_offset_reset='latest',
                    group_id=f'streamlit_crypto_{int(time.time())}'
                )
                
                logger.info(f"📊 Connected to Kafka topic: {self.raw_topic}")
                
                for message in consumer:
                    if message.value:
                        symbol = message.value.get('symbol')
                        price = float(message.value.get('price', 0))
                        
                        if symbol and price > 0:
                            # Calculer le changement
                            old_price = self.latest_prices.get(symbol, price)
                            change_pct = ((price - old_price) / old_price * 100) if old_price > 0 else 0
                            
                            # Mettre à jour les données
                            self.latest_prices[symbol] = price
                            self.latest_changes[symbol] = change_pct
                            
                            # Ajouter aux données historiques
                            self.crypto_data[symbol].append({
                                'timestamp': datetime.now(),
                                'price': price,
                                'volume': float(message.value.get('volume', 0)),
                                'market_cap': float(message.value.get('market_cap', 0)),
                                'change_24h': float(message.value.get('percent_change_24h', 0))
                            })
                            
                            # IMPORTANT: Mettre à jour l'état de connexion 
                            self.last_update = datetime.now()
                            self.kafka_connected = True
                            self.message_count += 1
                            
                            # Stocker l'état dans session_state pour que Streamlit le voit
                            self.kafka_connected = True
                            
                            
                            
                            if self.message_count % 10 == 0:
                                logger.info(f"📈 Received {self.message_count} crypto updates")
                            
            except Exception as e:
                logger.error(f"Error in Kafka consumer: {e}")
                self.kafka_connected = False
                self.kafka_connected = False
        
        # Démarrer le thread
        threading.Thread(target=consume_kafka_data, daemon=True).start()
    
    def get_connection_status(self):
        """Récupère le statut de connexion depuis session_state"""
        connected = self.kafka_connected
        last_update = self.last_update
        message_count = self.message_count
        
        return connected, last_update, message_count
    
    def get_crypto_metrics(self):
        """Récupère les métriques actuelles des cryptos"""
        cryptos = ['BTC', 'ETH', 'USDT', 'XRP', 'BNB', 'SOL', 'DOGE', 'TRX', 'ADA']
        metrics = []
        
        for symbol in cryptos:
            price = self.latest_prices.get(symbol, 0)
            change_pct = self.latest_changes.get(symbol, 0)
            
            # Données historiques récentes
            hist_data = list(self.crypto_data[symbol])[-50:] if symbol in self.crypto_data else []
            
            # Volume et market cap depuis les dernières données
            volume = hist_data[-1]['volume'] if hist_data else np.random.randint(10000000, 50000000000)
            market_cap = hist_data[-1]['market_cap'] if hist_data else volume * price * 100
            change_24h = hist_data[-1]['change_24h'] if hist_data else change_pct
            
            # Générer des changements aléatoires réalistes pour 1h et 7j
            change_1h = np.random.uniform(-0.5, 0.5)
            change_7d = np.random.uniform(-8, 12)
            
            metrics.append({
                'symbol': symbol,
                'name': self.get_crypto_name(symbol),
                'price': price,
                'change_1h': change_1h,
                'change_24h': change_24h,
                'change_7d': change_7d,
                'volume': volume,
                'market_cap': market_cap,
                'data_points': len(hist_data),
                'sparkline_data': [d['price'] for d in hist_data[-20:]] if hist_data else []
            })
        
        return metrics
    
    def get_crypto_name(self, symbol):
        names = {
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum', 
            'USDT': 'Tether',
            'XRP': 'Ripple',
            'BNB': 'Binance Coin',
            'SOL': 'Solana',
            'DOGE': 'Dogecoin',
            'TRX': 'TRON',
            'ADA': 'Cardano'
        }
        return names.get(symbol, symbol)
    
    def get_crypto_logo_url(self, symbol):
        """Retourne l'URL du logo pour chaque crypto"""
        logos = {
            'BTC': 'https://assets.coingecko.com/coins/images/1/small/bitcoin.png',
            'ETH': 'https://assets.coingecko.com/coins/images/279/small/ethereum.png',
            'USDT': 'https://assets.coingecko.com/coins/images/325/small/Tether.png',
            'XRP': 'https://assets.coingecko.com/coins/images/44/small/xrp-symbol-white-128.png',
            'BNB': 'https://assets.coingecko.com/coins/images/825/small/bnb-icon2_2x.png',
            'SOL': 'https://assets.coingecko.com/coins/images/4128/small/solana.png',
            'DOGE': 'https://assets.coingecko.com/coins/images/5/small/dogecoin.png',
            'TRX': 'https://assets.coingecko.com/coins/images/1094/small/tron-logo.png',
            'ADA': 'https://assets.coingecko.com/coins/images/975/small/cardano.png'
        }
        return logos.get(symbol, '')
    
    def create_sparkline(self, data, positive_trend=True):
        """Crée un mini-graphique sparkline"""
        if not data or len(data) < 2:
            # Données simulées pour la démo
            data = [100 + i + np.random.uniform(-2, 2) for i in range(20)]
        
        fig = go.Figure()
        
        color = '#3FB68B' if positive_trend else '#FF6B6B'
        
        fig.add_trace(go.Scatter(
            y=data,
            mode='lines',
            line=dict(color=color, width=1.5),
            fill='tonexty' if positive_trend else None,
            fillcolor=f'rgba({59 if positive_trend else 255}, {182 if positive_trend else 107}, {139 if positive_trend else 107}, 0.1)',
            showlegend=False,
            hoverinfo='skip'
        ))
        
        fig.update_layout(
            showlegend=False,
            height=40,
            width=120,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        
        return fig
    
    def format_number(self, num, is_currency=True, is_volume=False):
        """Formate les nombres avec les bonnes unités"""
        if num == 0:
            return "N/A"
            
        if is_volume or num > 1e9:
            if num >= 1e12:
                return f"{'€' if is_currency else ''}{num/1e12:.1f}T"
            elif num >= 1e9:
                return f"{'€' if is_currency else ''}{num/1e9:.1f}B"
            elif num >= 1e6:
                return f"{'€' if is_currency else ''}{num/1e6:.1f}M"
            else:
                return f"{'€' if is_currency else ''}{num:,.0f}"
        else:
            if is_currency:
                return f"€{num:,.2f}"
            else:
                return f"{num:,.2f}"

# Initialiser le dashboard dans session_state
if 'dashboard' not in st.session_state:
    st.session_state.dashboard = StreamlitCryptoDashboard()
    
if 'selected_crypto' not in st.session_state:
    st.session_state.selected_crypto = None
    
dashboard = st.session_state.dashboard

# Pages du dashboard
def main_page():
    """Page principale avec le tableau des cryptos"""
    
    # Header principal
    st.markdown('<div class="main-header">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("🚀 CryptoViz Live Dashboard")
        st.markdown("*Données de cryptomonnaies en temps réel depuis Kafka*")
    
    with col2:
        # Status en temps réel
        kafka_connected, last_update, message_count = dashboard.get_connection_status()
        
        if kafka_connected and last_update:
            time_diff = (datetime.now() - last_update).seconds
            if time_diff < 60:
                st.success(f"🟢 LIVE • {message_count} msgs")
            else:
                st.warning(f"🟡 Stale • {time_diff//60}min")
        else:
            st.error("🔴 Connexion...")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Récupérer les données crypto
    metrics = dashboard.get_crypto_metrics()
    
    # En-tête du tableau
    st.markdown("""
        <div class="table-header">
            <div style="width: 40px;">#</div>
            <div style="width: 200px;">Nom</div>
            <div style="width: 120px;">Prix</div>
            <div style="width: 80px;">1h %</div>
            <div style="width: 80px;">24h %</div>
            <div style="width: 80px;">7j %</div>
            <div style="width: 140px;">Cap. Boursière</div>
            <div style="width: 120px;">Volume (24h)</div>
            <div style="width: 120px;">7 Derniers Jours</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Conteneur du tableau
    st.markdown('<div class="crypto-table">', unsafe_allow_html=True)
    
    # Générer les lignes du tableau
    for idx, crypto in enumerate(metrics):
        # Déterminer les couleurs des changements
        color_1h = 'positive' if crypto['change_1h'] >= 0 else 'negative'
        color_24h = 'positive' if crypto['change_24h'] >= 0 else 'negative'
        color_7d = 'positive' if crypto['change_7d'] >= 0 else 'negative'
        
        # Status
        status = "LIVE" if crypto['data_points'] > 0 else "CHARGEMENT"
        status_class = "status-live" if crypto['data_points'] > 0 else "status-loading"
        
        # Créer la ligne cliquable
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([0.5, 2.5, 1.5, 1, 1, 1, 1.8, 1.5, 1.5])
        
        with col1:
            st.markdown(f"<div class='crypto-rank'>{idx + 1}</div>", unsafe_allow_html=True)
            
        with col2:
            # Bouton crypto avec logo et nom
            if st.button(f"{crypto['symbol']} {crypto['name']}", 
                        key=f"crypto_{crypto['symbol']}",
                        help=f"Cliquez pour voir les détails de {crypto['name']}"):
                st.session_state.selected_crypto = crypto['symbol']
                st.rerun()
            
        with col3:
            st.markdown(f"<div class='crypto-price'>{dashboard.format_number(crypto['price'])}</div>", 
                       unsafe_allow_html=True)
            
        with col4:
            st.markdown(f"<div class='crypto-change {color_1h}'>{crypto['change_1h']:+.2f}%</div>", 
                       unsafe_allow_html=True)
            
        with col5:
            st.markdown(f"<div class='crypto-change {color_24h}'>{crypto['change_24h']:+.2f}%</div>", 
                       unsafe_allow_html=True)
            
        with col6:
            st.markdown(f"<div class='crypto-change {color_7d}'>{crypto['change_7d']:+.2f}%</div>", 
                       unsafe_allow_html=True)
            
        with col7:
            st.markdown(f"<div class='crypto-market-cap'>{dashboard.format_number(crypto['market_cap'], is_volume=True)}</div>", 
                       unsafe_allow_html=True)
            
        with col8:
            st.markdown(f"<div class='crypto-volume'>{dashboard.format_number(crypto['volume'], is_volume=True)}</div>", 
                       unsafe_allow_html=True)
            
        with col9:
            # Mini sparkline
            if crypto['sparkline_data']:
                sparkline = dashboard.create_sparkline(crypto['sparkline_data'], crypto['change_7d'] >= 0)
                st.plotly_chart(sparkline, use_container_width=True, config={'displayModeBar': False})
            else:
                st.markdown("<div style='height:40px;display:flex;align-items:center;color:#8B949E;font-size:11px;'>Chargement...</div>", unsafe_allow_html=True)
        
        # Ligne de séparation
        if idx < len(metrics) - 1:
            st.markdown("<hr style='margin: 0; border: 0; border-top: 1px solid #262730;'>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-refresh
    if st.sidebar.checkbox("🔄 Actualisation auto", value=False):
        time.sleep(5)
        st.rerun()

def crypto_detail_page(symbol):
    """Page détaillée pour une crypto spécifique"""
    
    crypto_name = dashboard.get_crypto_name(symbol)
    
    # Header avec bouton retour
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("← Retour", key="back_button"):
            st.session_state.selected_crypto = None
            st.rerun()
    
    with col2:
        st.title(f"📊 {symbol} • {crypto_name}")
    
    st.divider()
    
    # Métriques principales
    metrics = dashboard.get_crypto_metrics()
    crypto_data = next((c for c in metrics if c['symbol'] == symbol), None)
    
    if crypto_data:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Prix Actuel", dashboard.format_number(crypto_data['price']), 
                     f"{crypto_data['change_24h']:+.2f}%")
        
        with col2:
            st.metric("Market Cap", dashboard.format_number(crypto_data['market_cap'], is_volume=True))
        
        with col3:
            st.metric("Volume 24h", dashboard.format_number(crypto_data['volume'], is_volume=True))
        
        with col4:
            st.metric("Change 7j", f"{crypto_data['change_7d']:+.2f}%")
    
    st.divider()
    
    # Graphique de prix détaillé
    if symbol in dashboard.crypto_data and len(dashboard.crypto_data[symbol]) > 0:
        st.header("📈 Graphique des Prix")
        
        # Options de timeframe
        timeframe = st.selectbox("Période", ["1H", "6H", "24H", "7J"], index=2)
        hours_map = {"1H": 1, "6H": 6, "24H": 24, "7J": 168}
        selected_hours = hours_map[timeframe]
        
        # Données historiques
        hist_data = list(dashboard.crypto_data[symbol])[-selected_hours*12:]  # 12 points par heure
        
        if hist_data:
            df = pd.DataFrame(hist_data)
            
            fig = go.Figure()
            
            # Graphique en chandelier ou ligne
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['price'],
                mode='lines+markers',
                name=f'{symbol} Prix',
                line=dict(color='#00D4AA', width=2),
                marker=dict(size=3, color='#00D4AA'),
                hovertemplate='<b>%{y:,.2f}€</b><br>%{x}<extra></extra>'
            ))
            
            fig.update_layout(
                title=f'{crypto_name} ({symbol}) - {timeframe}',
                xaxis_title='Temps',
                yaxis_title='Prix (EUR)',
                height=500,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(17,17,17,0.8)',
                font=dict(color='white'),
                xaxis=dict(gridcolor='rgba(128,128,128,0.2)'),
                yaxis=dict(gridcolor='rgba(128,128,128,0.2)')
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📊 Collecte des données en cours...")
    else:
        st.info("📊 Aucune donnée historique disponible pour le moment.")
    
    # Tableau des dernières transactions (simulé)
    st.header("💱 Dernières Transactions")
    
    # Générer des données de demo pour les transactions
    transactions_data = []
    for i in range(10):
        transactions_data.append({
            'Heure': (datetime.now() - timedelta(minutes=i*2)).strftime('%H:%M:%S'),
            'Type': np.random.choice(['Achat', 'Vente']),
            'Prix': f"{crypto_data['price'] + np.random.uniform(-50, 50):,.2f}€",
            'Quantité': f"{np.random.uniform(0.1, 5):.4f} {symbol}",
            'Total': f"{np.random.uniform(100, 5000):,.2f}€"
        })
    
    st.dataframe(pd.DataFrame(transactions_data), use_container_width=True, hide_index=True)

# Interface utilisateur principale
def main():
    # Vérifier si une crypto est sélectionnée
    if st.session_state.selected_crypto:
        crypto_detail_page(st.session_state.selected_crypto)
    else:
        main_page()

if __name__ == "__main__":
    main()
