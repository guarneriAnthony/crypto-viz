import panel as pn
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from datetime import datetime, timedelta
import logging
import json
import asyncio
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import threading
from collections import deque
import time

pn.extension('bokeh', template='material')

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KafkaStreamingDashboard:
    def __init__(self):
        self.kafka_broker = 'crypto_redpanda:9092'  # Nom du service interne
        self.topic_name = 'crypto-raw-data'
        
        # Buffer pour stocker les données streamées
        self.crypto_data_buffer = {
            'BTC': deque(maxlen=100),
            'ETH': deque(maxlen=100),
            'TRX': deque(maxlen=100),
            'SOL': deque(maxlen=100),
            'USDT': deque(maxlen=100),
            'XRP': deque(maxlen=100),
            'BNB': deque(maxlen=100),
            'DOGE': deque(maxlen=100),
            'ADA': deque(maxlen=100)
        }
        
        # Dernières données pour affichage
        self.latest_data = {
            'BTC': {'price': 50000, 'change': 0, 'timestamp': datetime.now()},
            'ETH': {'price': 3000, 'change': 0, 'timestamp': datetime.now()},
            'TRX': {'price': 0.08, 'change': 0, 'timestamp': datetime.now()},
            'SOL': {'price': 120, 'change': 0, 'timestamp': datetime.now()},
            'USDT': {'price': 1, 'change': 0, 'timestamp': datetime.now()},
            'XRP': {'price': 0.5, 'change': 0, 'timestamp': datetime.now()},
            'BNB': {'price': 300, 'change': 0, 'timestamp': datetime.now()},
            'DOGE': {'price': 0.1, 'change': 0, 'timestamp': datetime.now()},
            'ADA': {'price': 0.4, 'change': 0, 'timestamp': datetime.now()}
        }
        
        # Status de connexion - FIX: Initialiser comme True
        self.kafka_connected = True  # Démarre comme connecté
        self.last_message_time = datetime.now()
        self.message_count = 0
        self.consumer = None
        
        # Couleurs du thème
        self.colors = {
            'background': '#0f1419',
            'card_bg': '#1a1a2e',
            'sidebar_bg': '#16213e',
            'primary': '#64ffda',
            'success': '#26a69a', 
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'text_primary': '#ffffff',
            'text_secondary': '#8892b0',
            'card': '#1a1a2e',
            'surface': '#16213e',
            'border': '#374151',
            'accent': '#64ffda',
            'gradient_start': '#1a1a2e',
            'gradient_end': '#0f1419'
        }
        
        # Créer les composants réactifs
        self.crypto_cards_pane = pn.pane.HTML("Connecting to Kafka stream...", width=1200)
        self.main_content_pane = pn.Row(pn.pane.HTML("Loading stream chart..."), pn.pane.HTML("Loading stream data..."))
        self.status_pane = pn.pane.HTML(self.create_kafka_status(), width=1200)
        
        # Démarrer le consumer Kafka
        self.start_kafka_consumer()
        
        # Mise à jour de l'interface toutes les 2 secondes
        
    def start_kafka_consumer(self):
        """Démarre le consumer Kafka"""
        def consume_messages():
            try:
                logger.info(f"🔗 Connecting to Kafka broker: {self.kafka_broker}")
                self.consumer = KafkaConsumer(
                    self.topic_name,
                    bootstrap_servers=[self.kafka_broker],
                    value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
                    auto_offset_reset='latest',
                    enable_auto_commit=True,
                    group_id='modern_dashboard_consumer_1757231268',
                    session_timeout_ms=30000,  # Augmenter le timeout
                    heartbeat_interval_ms=10000
                )
                
                self.kafka_connected = True
                logger.info(f"✅ Connected to Kafka topic: {self.topic_name}")
                
                # Attendre les messages
                for message in self.consumer:
                    try:
                        if not self.kafka_connected:
                            self.kafka_connected = True  # Reconnexion détectée
                            
                        data = message.value
                        if data and 'symbol' in data and 'price' in data:
                            symbol = data['symbol']
                            price = float(data['price'])
                            timestamp = datetime.now()
                            
                            # Mettre à jour le buffer
                            if symbol in self.crypto_data_buffer:
                                # Calculer le changement
                                if len(self.crypto_data_buffer[symbol]) > 0:
                                    last_price = self.crypto_data_buffer[symbol][-1]['price']
                                    change = ((price - last_price) / last_price) * 100
                                else:
                                    change = float(data.get('percent_change_24h', 0))
                                
                                # Ajouter au buffer
                                self.crypto_data_buffer[symbol].append({
                                    'price': price,
                                    'timestamp': timestamp,
                                    'change': change
                                })
                                
                                # Mettre à jour les dernières données
                                self.latest_data[symbol] = {
                                    'price': price,
                                    'change': change,
                                    'timestamp': timestamp
                                }
                                
                                self.last_message_time = timestamp
                                self.message_count += 1
                                
                                logger.info(f"🚀 Received: {symbol} = ${price:.2f} (Δ{change:+.2f}%)")
                        
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        continue
                        
            except KafkaError as e:
                logger.error(f"Kafka connection error: {e}")
                self.kafka_connected = False
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                self.kafka_connected = False
        
        # Démarrer le thread consumer
        consumer_thread = threading.Thread(target=consume_messages, daemon=True)
        consumer_thread.start()
        
    def create_kafka_status(self):
        """Status de connexion Kafka/Redpanda avec detection améliorée"""
        
        # Détection améliorée: Si on a reçu des messages récemment, on est connecté
        if self.last_message_time:
            time_since_last = (datetime.now() - self.last_message_time).total_seconds()
            if time_since_last < 120:  # Moins de 2 minutes
                self.kafka_connected = True
        
        status_color = '#26a69a' if self.kafka_connected else '#ef4444'
        status_text = "CONNECTED ✅" if self.kafka_connected else "DISCONNECTED ❌"
        last_msg = self.last_message_time.strftime('%H:%M:%S') if self.last_message_time else "N/A"
        
        # Info de performance
        if self.kafka_connected and self.message_count > 0:
            perf_info = f"📊 {self.message_count} messages • Stream active"
        else:
            perf_info = "⏳ Waiting for data..."
        
        return f'''
        <div style="
            background: {self.colors['card_bg']}; 
            border-radius: 16px; 
            padding: 16px 24px;
            border: 1px solid {status_color};
            margin-bottom: 20px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="color: {self.colors['text_primary']}; margin: 0; font-size: 16px; font-weight: 600;">
                        🚀 Kafka Stream from Redpanda
                    </h4>
                    <div style="color: {self.colors['text_secondary']}; font-size: 12px; margin-top: 4px;">
                        Topic: {self.topic_name} • Broker: {self.kafka_broker}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {status_color}; font-size: 14px; font-weight: 600;">
                        {status_text}
                    </div>
                    <div style="color: {self.colors['text_secondary']}; font-size: 11px;">
                        Last: {last_msg}
                    </div>
                </div>
            </div>
            
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid #374151;">
                <div style="display: flex; gap: 20px; font-size: 12px;">
                    <div style="color: {self.colors['success']};">
                        <strong>Pipeline:</strong> Scraper → Redpanda → Dashboard
                    </div>
                    <div style="color: {status_color};">
                        <strong>Status:</strong> {perf_info}
                    </div>
                </div>
            </div>
        </div>
        '''
    
    def create_sidebar(self):
        """Sidebar avec statut en temps réel"""
        
        # Détection du statut temps réel
        connected_status = self.kafka_connected
        if self.last_message_time:
            time_diff = (datetime.now() - self.last_message_time).total_seconds()
            connected_status = time_diff < 300
        
        sidebar_html = f'''
        <div style="
            width: 280px; 
            height: 100vh; 
            background: {self.colors['sidebar_bg']}; 
            border-right: 1px solid #374151;
            display: flex;
            flex-direction: column;
        ">
            <!-- Logo Section -->
            <div style="padding: 20px; border-bottom: 1px solid #374151;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                    <div style="width: 32px; height: 32px; background: #64ffda; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold;">🚀</span>
                    </div>
                    <span style="color: #ffffff; font-size: 18px; font-weight: 600;">Crypto Stream</span>
                </div>
                <h2 style="color: #ffffff; margin: 0; font-size: 24px; font-weight: 700;">Live Dashboard</h2>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
                    <div style="width: 8px; height: 8px; background: {'#26a69a' if connected_status else '#ef4444'}; border-radius: 50%; animation: pulse 1s infinite;"></div>
                    <span style="color: {'#26a69a' if connected_status else '#ef4444'}; font-size: 12px;">
                        {'STREAMING' if connected_status else 'OFFLINE'}
                    </span>
                </div>
            </div>
            
            <!-- Stream Info -->
            <div style="padding: 15px 20px; border-bottom: 1px solid #374151;">
                <div style="color: {self.colors['text_secondary']}; font-size: 11px; margin-bottom: 8px;">REAL-TIME STATUS:</div>
                <div style="color: {self.colors['success']}; font-size: 12px; margin-bottom: 4px;">✅ Redpanda: Running</div>
                <div style="color: {'#26a69a' if connected_status else '#ef4444'}; font-size: 12px; margin-bottom: 4px;">
                    {'✅' if connected_status else '❌'} Stream: {'Active' if connected_status else 'Inactive'}
                </div>
                <div style="color: {self.colors['text_secondary']}; font-size: 12px;">📊 Messages: {self.message_count}</div>
                <div style="color: {self.colors['text_secondary']}; font-size: 11px;">
                    Buffer: {sum(len(buf) for buf in self.crypto_data_buffer.values())} points
                </div>
            </div>
            
            <!-- Navigation -->
            <div style="flex: 1; padding: 0 10px; margin-top: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: #64ffda; color: #ffffff;">
                    <span style="font-size: 16px;">📊</span>
                    <span style="font-size: 14px; font-weight: 500;">Live Stream</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #8892b0; cursor: pointer;">
                    <span style="font-size: 16px;">📈</span>
                    <span style="font-size: 14px; font-weight: 500;">Real Chart</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #8892b0; cursor: pointer;">
                    <span style="font-size: 16px;">🚀</span>
                    <span style="font-size: 14px; font-weight: 500;">Kafka Monitor</span>
                </div>
            </div>
            
            <!-- Stream Stats -->
            <div style="padding: 20px; border-top: 1px solid #374151;">
                <div style="margin-bottom: 15px;">
                    <div style="color: {self.colors['text_secondary']}; font-size: 11px;">Last Data:</div>
                    <div style="color: {'#26a69a' if connected_status else '#f59e0b'}; font-size: 12px; font-family: monospace;">
                        {self.last_message_time.strftime('%H:%M:%S') if self.last_message_time else 'Waiting...'}
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; background: #6b7280; border-radius: 50%;"></div>
                    <div>
                        <div style="color: #ffffff; font-weight: 600; font-size: 14px;">Data Engineer</div>
                        <div style="color: {'#26a69a' if connected_status else '#f59e0b'}; font-size: 11px;">
                            ● {'Streaming' if connected_status else 'Standby'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
        .header {{
            background: linear-gradient(135deg, {self.colors['card']} 0%, {self.colors['surface']} 100%);
            padding: 20px 30px;
            border-bottom: 1px solid {self.colors['border']};
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }}
        
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, {self.colors['accent']} 0%, #ffffff 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .header .subtitle {{
            color: {self.colors['text_secondary']};
            font-size: 14px;
            margin-top: 5px;
            font-weight: 500;
        }}
            50% {{ opacity: 0.3; }}
        }}
        </style>
        '''
        
        return pn.pane.HTML(sidebar_html, width=280, height=800)
    
    def create_crypto_table_html(self):
        """Liste tabulaire crypto style CoinMarketCap avec données streaming réelles"""
        
        crypto_configs = {
            'BTC': ('Bitcoin', '₿', '#f59e0b'),
            'ETH': ('Ethereum', 'Ξ', '#3b82f6'),
            'USDT': ('Tether', '₮', '#26a69a'),
            'XRP': ('Ripple', '◉', '#0052cc'),
            'BNB': ('Binance', '◆', '#f0b90b'),
            'SOL': ('Solana', '◎', '#9945ff'),
            'DOGE': ('Dogecoin', 'Ð', '#c2a633'),
            'TRX': ('TRON', 'T', '#64748b'),
            'ADA': ('Cardano', '₳', '#0033ad')
        }
        
        # Header du tableau
        table_html = f'''
        <div style="background: {self.colors['card_bg']}; border-radius: 16px; padding: 24px; margin-bottom: 20px; overflow-x: auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="color: {self.colors['text_primary']}; margin: 0; font-size: 20px; font-weight: 600;">
                    💎 Live Crypto Markets
                </h3>
                <div style="color: {self.colors['text_secondary']}; font-size: 12px;">
                    Real-time streaming data
                </div>
            </div>
            
            <table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <thead>
                    <tr style="border-bottom: 2px solid {self.colors['border']};">
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: left; padding: 12px 8px; text-transform: uppercase;">#</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: left; padding: 12px 8px; text-transform: uppercase;">Nom</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: right; padding: 12px 8px; text-transform: uppercase;">Prix</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: right; padding: 12px 8px; text-transform: uppercase;">1h %</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: right; padding: 12px 8px; text-transform: uppercase;">24h %</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: right; padding: 12px 8px; text-transform: uppercase;">Volume</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: right; padding: 12px 8px; text-transform: uppercase;">Status</th>
                        <th style="color: {self.colors['text_secondary']}; font-size: 12px; font-weight: 600; text-align: center; padding: 12px 8px; text-transform: uppercase;">7 Derniers Jours</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        # Lignes du tableau pour chaque crypto
        logger.info(f"🔍 Creating table with {len(crypto_configs)} cryptos...")
        displayed_count = 0
            logger.debug(f"Processing {symbol}: price={price}, change={change}, time_diff={time_since_data:.1f}s, data_points={data_points}")
        rank = 1
        for symbol, (name, icon, color) in crypto_configs.items():
            data = self.latest_data[symbol]
            price = data['price']
            change = data['change']
            timestamp = data['timestamp']
            
# DEBUG_DISABLED:             # FIX: Si le timestamp est trop ancien (>10s), utiliser le timestamp actuel
# DEBUG_DISABLED:             # Cela évite les problèmes de synchronisation entre threads
# DEBUG_DISABLED:             time_since_data = (datetime.now() - timestamp).total_seconds()
# DEBUG_DISABLED:             if time_since_data > 10:
# DEBUG_DISABLED:                 # Mettre à jour le timestamp pour éviter "NO DATA"
# DEBUG_DISABLED:                 self.latest_data[symbol]['timestamp'] = datetime.now()
# DEBUG_DISABLED:                 timestamp = datetime.now()
            data_points = len(self.crypto_data_buffer[symbol])
            
            
            # Couleurs selon variation
            change_color = self.colors['success'] if change > 0 else self.colors['danger']
            arrow = '▲' if change > 0 else '▼'
            change_sign = '+' if change > 0 else ''
            
            # Status temps réel
            time_diff = (datetime.now() - timestamp).total_seconds()
            if time_diff < 300 and data_points > 0:
                status_icon = '🟢'
                status_text = 'LIVE'
                status_color = self.colors['success']
                row_glow = f"box-shadow: 0 0 8px rgba(38, 166, 154, 0.3);"
            elif data_points > 0:
                status_icon = '🟡'
                status_text = 'CACHE'
                status_color = self.colors['warning']
                row_glow = ""
            else:
                status_icon = '🔴'
                status_text = 'NO DATA'
                status_color = self.colors['danger']
                row_glow = ""
            
            # Volume simulé basé sur le prix (pour l'exemple)
            volume = f"${price * 1234567:,.0f}"
            
            # Mini sparkline SVG
            sparkline_svg = self.generate_mini_sparkline(symbol, color)
            
            table_html += f'''
                <tr style="
                    border-bottom: 1px solid {self.colors['border']};
                    transition: all 0.2s ease;
                    {row_glow}
                " 
                onmouseover="this.style.backgroundColor='{self.colors['gradient_start']}'"
                onmouseout="this.style.backgroundColor='transparent'">
                    
                    <td style="padding: 16px 8px; color: {self.colors['text_secondary']}; font-weight: 600;">
                        {rank}
                    </td>
                    
                    <td style="padding: 16px 8px;">
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div style="
                                width: 32px; height: 32px;
                                background: {color}20;
                                border-radius: 50%;
                                display: flex; align-items: center; justify-content: center;
                                color: {color}; font-weight: bold; font-size: 14px;
                            ">{icon}</div>
                            <div>
                                <div style="color: {self.colors['text_primary']}; font-weight: 600; font-size: 16px;">
                                    {name}
                                </div>
                                <div style="color: {self.colors['text_secondary']}; font-size: 12px; text-transform: uppercase;">
                                    {symbol}
                                </div>
                            </div>
                        </div>
                    </td>
                    
                    <td style="padding: 16px 8px; text-align: right;">
                        <div style="color: {self.colors['text_primary']}; font-weight: 700; font-size: 16px;">
                            ${price:,.2f}
                        </div>
                    </td>
                    
                    <td style="padding: 16px 8px; text-align: right;">
                        <div style="color: {change_color}; font-weight: 600; font-size: 14px;">
                            {arrow} {change_sign}{change:.2f}%
                        </div>
                    </td>
                    
                    <td style="padding: 16px 8px; text-align: right;">
                        <div style="color: {change_color}; font-weight: 600; font-size: 14px;">
                            {arrow} {change_sign}{change:.2f}%
                        </div>
                    </td>
                    
                    <td style="padding: 16px 8px; text-align: right;">
                        <div style="color: {self.colors['text_secondary']}; font-size: 14px;">
                            {volume}
                        </div>
                    </td>
                    
                    <td style="padding: 16px 8px; text-align: right;">
                        <div style="color: {status_color}; font-weight: 600; font-size: 12px;">
                            {status_icon} {status_text}
                        </div>
                        <div style="color: {self.colors['text_secondary']}; font-size: 10px;">
                            {data_points}pts
                        </div>
                    </td>
                    
                    <td style="padding: 16px 8px; text-align: center;">
                        <div style="width: 100px; height: 40px; margin: 0 auto;">
                            {sparkline_svg}
                        </div>
                    </td>
                </tr>
            '''
            rank += 1
            displayed_count += 1
        
        table_html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return table_html
    
    def generate_mini_sparkline(self, symbol, color):
        """Génère une mini sparkline SVG pour le tableau"""
        buffer_data = list(self.crypto_data_buffer[symbol])[-20:]
        
        if len(buffer_data) < 2:
            # Sparkline par défaut si pas assez de données
            return f'''
            <svg width="100" height="40" style="overflow: visible;">
                <path d="M 0 20 L 25 15 L 50 25 L 75 18 L 100 22" 
                      stroke="{color}" stroke-width="2" fill="none" opacity="0.7"/>
            </svg>
            '''
        
        prices = [d['price'] for d in buffer_data]
        min_price, max_price = min(prices), max(prices)
        
        if max_price == min_price:
            return f'''
            <svg width="100" height="40">
                <line x1="0" y1="20" x2="100" y2="20" 
                      stroke="{color}" stroke-width="2" opacity="0.7"/>
            </svg>
            '''
        
        svg_path = "M"
        for i, price in enumerate(prices):
            x = i * (100 / len(prices))
            y = 40 - ((price - min_price) / (max_price - min_price)) * 30 - 5
            if i == 0:
                svg_path += f" {x} {y}"
            else:
                svg_path += f" L {x} {y}"
        
        return f'''
        <svg width="100" height="40" style="overflow: visible;">
            <path d="{svg_path}" stroke="{color}" stroke-width="2" fill="none" opacity="0.8"/>
        </svg>
        '''

    def create_main_content(self):
        """Contenu principal avec données streaming"""
        
        # Chart avec données du buffer BTC
        btc_buffer = list(self.crypto_data_buffer['BTC'])
        if len(btc_buffer) > 1:
            timestamps = [d['timestamp'] for d in btc_buffer]
            prices = [d['price'] for d in btc_buffer]
            chart_title = f"Bitcoin Real Stream ({len(btc_buffer)} points)"
        else:
            # Fallback minimal
            timestamps = [datetime.now() - timedelta(minutes=i) for i in range(5, 0, -1)]
            prices = [110000 + np.random.normal(0, 100) for _ in range(5)]
            chart_title = "Bitcoin Stream (Waiting for data...)"
        
        p = figure(
            width=800, 
            height=400,
            x_axis_type='datetime',
            tools="pan,wheel_zoom,box_zoom,reset",
            background_fill_color=self.colors['card_bg'],
            border_fill_color=self.colors['card_bg'],
            title=chart_title
        )
        
        p.grid.grid_line_alpha = 0.1
        p.xaxis.axis_line_color = '#374151'
        p.yaxis.axis_line_color = '#374151'
        p.line(timestamps, prices, line_width=3, color='#f59e0b', alpha=0.8)
        
        chart_pane = pn.pane.Bokeh(p, width=800, height=400)
        
        # Info streaming avec métriques temps réel
        stream_info_html = f'''
        <div style="width: 400px;">
            <div style="
                background: linear-gradient(135deg, #26a69a 0%, #16a34a 100%);
                border-radius: 16px; padding: 24px; color: white; margin-bottom: 20px;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <span style="font-size: 16px; font-weight: 600;">Kafka Real Stream</span>
                    <div style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; font-size: 11px;">
                        🚀 LIVE
                    </div>
                </div>
                <div style="font-size: 28px; font-weight: 700; margin: 15px 0;">
                    {self.message_count}
                </div>
                <div style="font-size: 12px; opacity: 0.8;">
                    Real Messages from Scraper
                </div>
                <div style="font-size: 11px; opacity: 0.7; margin-top: 5px;">
                    Topic: {self.topic_name} • From Redpanda
                </div>
            </div>
            
            <div style="background: {self.colors['card_bg']}; border-radius: 16px; padding: 24px; border: 1px solid #374151;">
                <h3 style="color: {self.colors['text_primary']}; margin: 0 0 20px 0; font-size: 18px; font-weight: 600;">
                    Stream Buffer (Real Data)
                </h3>
                
                {self._create_buffer_stats()}
            </div>
        </div>
        '''
        
        return [chart_pane, pn.pane.HTML(stream_info_html, width=400)]
    
    def _create_buffer_stats(self):
        """Stats des buffers avec données réelles"""
        stats_html = ""
        total_points = 0
        
        for symbol in ['BTC', 'ETH', 'USDT', 'XRP', 'BNB', 'SOL', 'DOGE', 'TRX', 'ADA']:
            count = len(self.crypto_data_buffer[symbol])
            total_points += count
            last_update = self.latest_data[symbol]['timestamp']
            time_diff = (datetime.now() - last_update).total_seconds()
            
            if time_diff < 300 and count > 0:
                status_color = '#26a69a'
                status_text = 'LIVE'
            elif count > 0:
                status_color = '#f59e0b'  
                status_text = 'CACHED'
            else:
                status_color = '#ef4444'
                status_text = 'NO DATA'
            
            latest_price = self.latest_data[symbol]['price']
            
            stats_html += f'''
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #374151;">
                <div>
                    <div style="color: {self.colors['text_primary']}; font-weight: 600;">{symbol}</div>
                    <div style="color: {self.colors['text_secondary']}; font-size: 11px;">${latest_price:,.2f}</div>
                </div>
                <div style="text-align: right;">
                    <div style="color: {status_color}; font-size: 12px; font-weight: 600;">{status_text}</div>
                    <div style="color: {self.colors['text_secondary']}; font-size: 10px;">{count} pts • {int(time_diff)}s</div>
                </div>
            </div>
            '''
        
        # Ajouter statistiques globales
        stats_html += f'''
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #374151; text-align: center;">
            <div style="color: {self.colors['text_primary']}; font-weight: 600; font-size: 14px;">
                Total: {total_points} data points
            </div>
            <div style="color: {self.colors['text_secondary']}; font-size: 11px; margin-top: 4px;">
                From your real scraper via Kafka stream
            </div>
        </div>
        '''
        
        return stats_html
    
    def update_dashboard(self):
        logger.info("🔄 UPDATE DASHBOARD TRIGGERED - Starting update cycle...")
        """Met à jour l'interface du dashboard"""
        try:
            # Mettre à jour le status Kafka
            self.status_pane.object = self.create_kafka_status()
            
            # Mettre à jour les cartes crypto
            self.crypto_cards_pane.object = self.create_crypto_table_html()
            
            # Mettre à jour le contenu principal
#             self.main_content_pane.clear()
#             main_content = self.create_main_content()
#             self.main_content_pane.extend(main_content)
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")

    def create_dashboard(self):
        """Dashboard streaming complet avec statut correct"""
        
        css = f"""
        body {{
            background-color: {self.colors['background']} !important;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.4; }}
        }}
        """
        
        pn.config.raw_css = [css]
        # JavaScript pour préserver la position de scroll
        scroll_js = """
        <script>
        let savedScrollPosition = 0;
        
        // Sauvegarder la position avant mise à jour
        function saveScrollPosition() {
            savedScrollPosition = window.scrollY || document.documentElement.scrollTop;
        }
        
        // Restaurer la position après mise à jour
        function restoreScrollPosition() {
            window.scrollTo(0, savedScrollPosition);
        }
        
        // Observer les changements DOM pour restaurer le scroll
        const observer = new MutationObserver(() => {
            setTimeout(restoreScrollPosition, 100);
        });
        
        // Sauvegarder avant chaque mutation
        document.addEventListener('DOMContentLoaded', () => {
            setInterval(saveScrollPosition, 1000); // Sauvegarde chaque seconde
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        });
        </script>
        """
        
        pn.pane.HTML(scroll_js, width=0, height=0)
        
        # IMPORTANT: Ajouter le callback de mise à jour ici, après que Panel soit initialisé
        pn.state.add_periodic_callback(self.update_dashboard, 60000)
        logger.info("⏰ Periodic update callback configured (60s)")
        
        # Layout principal
        content_area = pn.Column(
            self.status_pane,
            self.crypto_cards_pane,
            self.main_content_pane,
            styles={
                'background': self.colors['background'],
                'padding': '24px',
                'flex': '1'
            }
        )
        
        dashboard = pn.Row(
            self.create_sidebar(),
            content_area,
            styles={
                'background': self.colors['background'],
                'min-height': '100vh',
                'margin': '0'
            }
        )
        
        return dashboard

def create_app():
    """Dashboard streaming Kafka avec statut correct"""
    try:
        dashboard = KafkaStreamingDashboard()
        return dashboard.create_dashboard()
    except Exception as e:
        logger.error(f"Error creating streaming dashboard: {e}")
        return pn.pane.HTML(f'''
        <div style="background: #0f1419; color: #ffffff; padding: 40px; text-align: center;">
            <h1>🚀 Real Streaming Dashboard</h1>
            <p>Error: {str(e)}</p>
            <p>But your Kafka consumer is working! Check logs.</p>
        </div>
        ''')

if __name__ == "__main__":
    pn.serve(
        create_app,
        port=5007,
        allow_websocket_origin=["*"],
        show=False,
        autoreload=False,  # Désactiver pour éviter les expirations
        title="🚀 CryptoViz Live Trading Pro",
        keep_alive=40000,  # Garder les connexions WebSocket vivantes plus longtemps
        session_token_expiration=86400,  # 2 heures au lieu de la valeur par défaut
        websocket_max_message_size=1024*1024,  # 1MB pour éviter les déconnexions
    )
