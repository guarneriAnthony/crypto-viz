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
    initial_sidebar_state="expanded"
)

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            'BTC': 110000, 'ETH': 4300, 'USDT': 1.0, 'XRP': 2.83,
            'BNB': 870, 'SOL': 203, 'DOGE': 0.22, 'TRX': 0.33, 'ADA': 0.83
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
                            st.session_state.kafka_connected = True
                            st.session_state.last_update = self.last_update
                            st.session_state.message_count = self.message_count
                            
                            if self.message_count % 10 == 0:
                                logger.info(f"📈 Received {self.message_count} crypto updates")
                            
            except Exception as e:
                logger.error(f"Error in Kafka consumer: {e}")
                self.kafka_connected = False
                st.session_state.kafka_connected = False
        
        # Démarrer le thread
        threading.Thread(target=consume_kafka_data, daemon=True).start()
    
    def get_connection_status(self):
        """Récupère le statut de connexion depuis session_state"""
        connected = getattr(st.session_state, 'kafka_connected', False)
        last_update = getattr(st.session_state, 'last_update', None)
        message_count = getattr(st.session_state, 'message_count', 0)
        
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
            volume = hist_data[-1]['volume'] if hist_data else 0
            market_cap = hist_data[-1]['market_cap'] if hist_data else 0
            change_24h = hist_data[-1]['change_24h'] if hist_data else change_pct
            
            metrics.append({
                'symbol': symbol,
                'name': self.get_crypto_name(symbol),
                'price': price,
                'change_pct': change_24h,  # Utiliser le change_24h du message
                'volume': volume,
                'market_cap': market_cap,
                'data_points': len(hist_data)
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
    
    def create_price_chart(self, symbol, hours=24):
        """Crée un graphique des prix pour une crypto"""
        if symbol not in self.crypto_data or len(self.crypto_data[symbol]) < 2:
            return None
            
        data = list(self.crypto_data[symbol])[-hours:]
        if not data:
            return None
            
        df = pd.DataFrame(data)
        
        fig = go.Figure()
        
        # Ligne de prix
        fig.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['price'],
            mode='lines+markers',
            name=f'{symbol} Price',
            line=dict(color='#00D4AA', width=3),
            marker=dict(size=4, color='#00D4AA')
        ))
        
        fig.update_layout(
            title=f'📈 {symbol} • {self.get_crypto_name(symbol)} Price Chart',
            xaxis_title='Time',
            yaxis_title='Price (USD)',
            height=400,
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(17,17,17,0.8)',
            font=dict(color='white'),
            xaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            ),
            yaxis=dict(
                gridcolor='rgba(128,128,128,0.2)',
                showgrid=True
            )
        )
        
        return fig

# Initialiser le dashboard dans session_state
if 'dashboard' not in st.session_state:
    st.session_state.dashboard = StreamlitCryptoDashboard()

dashboard = st.session_state.dashboard

# Interface utilisateur
def main():
    st.title("🚀 CryptoViz Live Dashboard")
    st.markdown("*Real-time cryptocurrency data from Kafka streaming*")
    
    # Récupérer le statut depuis session_state
    kafka_connected, last_update, message_count = dashboard.get_connection_status()
    
    # Status bar
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        if kafka_connected and last_update:
            time_diff = (datetime.now() - last_update).seconds
            if time_diff < 60:
                st.success(f"🟢 Live • Last update: {last_update.strftime('%H:%M:%S')}")
            elif time_diff < 300:
                st.warning(f"🟡 Stale • Last update: {time_diff//60}min ago")
            else:
                st.error(f"🔴 Stale • Last update: {time_diff//60}min ago")
        else:
            st.error("🔴 Connecting to Kafka...")
    
    with col2:
        st.metric("🏛️ Cryptos", "9")
    
    with col3:
        st.metric("📊 Messages", message_count)
    
    with col4:
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()
    
    st.divider()
    
    # Métriques en temps réel
    st.header("💰 Live Market Data")
    
    metrics = dashboard.get_crypto_metrics()
    
    # Affichage en grille 3x3
    for row in range(3):
        cols = st.columns(3)
        for col_idx, col in enumerate(cols):
            crypto_idx = row * 3 + col_idx
            if crypto_idx < len(metrics):
                crypto = metrics[crypto_idx]
                
                with col:
                    st.metric(
                        label=f"**{crypto['symbol']}** • {crypto['name']}",
                        value=f"${crypto['price']:,.2f}",
                        delta=f"{crypto['change_pct']:+.2f}%",
                        help=f"Volume: ${crypto['volume']:,.0f} | Cap: ${crypto['market_cap']:,.0f}"
                    )
                    
                    # Indicateur de données
                    if crypto['data_points'] > 0:
                        st.caption(f"📊 {crypto['data_points']} data points")
                    else:
                        st.caption("⏳ Loading data...")
    
    st.divider()
    
    # Section graphiques
    st.header("📊 Price Charts")
    
    # Sélecteurs
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        cryptos_with_data = [m['symbol'] for m in metrics if m['data_points'] > 0]
        if cryptos_with_data:
            selected_crypto = st.selectbox(
                "📈 Select Cryptocurrency:",
                options=cryptos_with_data,
                format_func=lambda x: f"{x} • {dashboard.get_crypto_name(x)}"
            )
        else:
            st.info("📊 Waiting for crypto data...")
            selected_crypto = None
    
    with col2:
        selected_hours = st.selectbox(
            "⏰ Time Period:",
            options=[1, 6, 12, 24],
            index=3,
            format_func=lambda x: f"{x} Hour{'s' if x > 1 else ''}"
        )
    
    with col3:
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
    
    # Affichage du graphique
    if selected_crypto:
        chart = dashboard.create_price_chart(selected_crypto, selected_hours)
        if chart:
            st.plotly_chart(chart, use_container_width=True)
        else:
            st.info(f"📊 Collecting {selected_crypto} chart data...")
    
    st.divider()
    
    # Tableau style CoinMarketCap
    st.header("📈 Market Overview")
    
    # Préparer les données du tableau
    table_data = []
    for idx, crypto in enumerate(metrics):
        status = "🟢 LIVE" if crypto['data_points'] > 0 else "⏳ LOADING"
        
        table_data.append({
            'Rank': f"#{idx + 1}",
            'Name': f"**{crypto['symbol']}** {crypto['name']}",
            'Price': f"${crypto['price']:,.2f}",
            'Change (24h)': f"{crypto['change_pct']:+.2f}%",
            'Volume': f"${crypto['volume']:,.0f}" if crypto['volume'] > 0 else "N/A",
            'Market Cap': f"${crypto['market_cap']:,.0f}" if crypto['market_cap'] > 0 else "N/A",
            'Status': status
        })
    
    df_display = pd.DataFrame(table_data)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # Footer avec informations techniques
    st.divider()
    with st.expander("🔧 Technical Info"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Kafka Topics:**")
            st.write(f"- Raw Data: `{dashboard.raw_topic}`")
            st.write(f"- Broker: `{dashboard.kafka_broker}`")
        
        with col2:
            st.write("**Connection Status:**")
            st.write(f"- Connected: {'✅' if kafka_connected else '❌'}")
            st.write(f"- Messages: {message_count}")
            if last_update:
                st.write(f"- Last Update: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
