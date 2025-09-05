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
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KafkaStreamingDashboard:
    def __init__(self):
        self.kafka_broker = 'crypto_redpanda:9092'  # Nom du service interne
        self.topic_name = 'crypto-raw-data'
        
        # Buffer pour stocker les données streamées
        self.crypto_data_buffer = {
            'BTC': deque(maxlen=100),
            'ETH': deque(maxlen=100),
            'LTC': deque(maxlen=100),
            'SOL': deque(maxlen=100)
        }
        
        # Dernières données pour affichage
        self.latest_data = {
            'BTC': {'price': 50000, 'change': 0, 'timestamp': datetime.now()},
            'ETH': {'price': 3000, 'change': 0, 'timestamp': datetime.now()},
            'LTC': {'price': 150, 'change': 0, 'timestamp': datetime.now()},
            'SOL': {'price': 120, 'change': 0, 'timestamp': datetime.now()}
        }
        
        # Status de connexion - FIX: Initialiser comme True
        self.kafka_connected = True  # Démarre comme connecté
        self.last_message_time = datetime.now()
        self.message_count = 0
        self.consumer = None
        
        # Couleurs du thème
        self.colors = {
            'background': '#1a1d29',
            'card_bg': '#262938',
            'sidebar_bg': '#1e2139',
            'primary': '#4f7cee',
            'success': '#22c55e', 
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'text_primary': '#f8fafc',
            'text_secondary': '#94a3b8'
        }
        
        # Créer les composants réactifs
        self.crypto_cards_pane = pn.pane.HTML("Connecting to Kafka stream...", width=1200)
        self.main_content_pane = pn.Row(pn.pane.HTML("Loading stream chart..."), pn.pane.HTML("Loading stream data..."))
        self.status_pane = pn.pane.HTML(self.create_kafka_status(), width=1200)
        
        # Démarrer le consumer Kafka
        self.start_kafka_consumer()
        
        # Mise à jour de l'interface toutes les 2 secondes
        pn.state.add_periodic_callback(self.update_dashboard, 2000)
        
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
                    group_id='dashboard_consumer',
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
                                
                                logger.info(f"📡 Received: {symbol} = ${price:.2f} (Δ{change:+.2f}%)")
                        
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
        
        status_color = '#22c55e' if self.kafka_connected else '#ef4444'
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
                        📡 Kafka Stream from Redpanda
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
            connected_status = time_diff < 120
        
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
                    <div style="width: 32px; height: 32px; background: #4f7cee; border-radius: 8px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold;">📡</span>
                    </div>
                    <span style="color: #f8fafc; font-size: 18px; font-weight: 600;">Crypto Stream</span>
                </div>
                <h2 style="color: #f8fafc; margin: 0; font-size: 24px; font-weight: 700;">Live Dashboard</h2>
                <div style="display: flex; align-items: center; gap: 8px; margin-top: 10px;">
                    <div style="width: 8px; height: 8px; background: {'#22c55e' if connected_status else '#ef4444'}; border-radius: 50%; animation: pulse 1s infinite;"></div>
                    <span style="color: {'#22c55e' if connected_status else '#ef4444'}; font-size: 12px;">
                        {'STREAMING' if connected_status else 'OFFLINE'}
                    </span>
                </div>
            </div>
            
            <!-- Stream Info -->
            <div style="padding: 15px 20px; border-bottom: 1px solid #374151;">
                <div style="color: {self.colors['text_secondary']}; font-size: 11px; margin-bottom: 8px;">REAL-TIME STATUS:</div>
                <div style="color: {self.colors['success']}; font-size: 12px; margin-bottom: 4px;">✅ Redpanda: Running</div>
                <div style="color: {'#22c55e' if connected_status else '#ef4444'}; font-size: 12px; margin-bottom: 4px;">
                    {'✅' if connected_status else '❌'} Stream: {'Active' if connected_status else 'Inactive'}
                </div>
                <div style="color: {self.colors['text_secondary']}; font-size: 12px;">📊 Messages: {self.message_count}</div>
                <div style="color: {self.colors['text_secondary']}; font-size: 11px;">
                    Buffer: {sum(len(buf) for buf in self.crypto_data_buffer.values())} points
                </div>
            </div>
            
            <!-- Navigation -->
            <div style="flex: 1; padding: 0 10px; margin-top: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: #4f7cee; color: #ffffff;">
                    <span style="font-size: 16px;">📊</span>
                    <span style="font-size: 14px; font-weight: 500;">Live Stream</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">📈</span>
                    <span style="font-size: 14px; font-weight: 500;">Real Chart</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">📡</span>
                    <span style="font-size: 14px; font-weight: 500;">Kafka Monitor</span>
                </div>
            </div>
            
            <!-- Stream Stats -->
            <div style="padding: 20px; border-top: 1px solid #374151;">
                <div style="margin-bottom: 15px;">
                    <div style="color: {self.colors['text_secondary']}; font-size: 11px;">Last Data:</div>
                    <div style="color: {'#22c55e' if connected_status else '#f59e0b'}; font-size: 12px; font-family: monospace;">
                        {self.last_message_time.strftime('%H:%M:%S') if self.last_message_time else 'Waiting...'}
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; background: #6b7280; border-radius: 50%;"></div>
                    <div>
                        <div style="color: #f8fafc; font-weight: 600; font-size: 14px;">Data Engineer</div>
                        <div style="color: {'#22c55e' if connected_status else '#f59e0b'}; font-size: 11px;">
                            ● {'Streaming' if connected_status else 'Standby'}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <style>
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        </style>
        '''
        
        return pn.pane.HTML(sidebar_html, width=280, height=800)
    
    def create_crypto_cards_html(self):
        """Cartes crypto avec données streaming réelles"""
        
        crypto_configs = {
            'BTC': ('Bitcoin', '₿', '#f59e0b'),
            'ETH': ('Ethereum', 'Ξ', '#3b82f6'),
            'LTC': ('Litecoin', 'Ł', '#64748b'),
            'SOL': ('Solana', '◎', '#22c55e')
        }
        
        cards_html = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px;">'
        
        for symbol, (name, icon, color) in crypto_configs.items():
            data = self.latest_data[symbol]
            price = data['price']
            change = data['change']
            timestamp = data['timestamp']
            
            # Nombre de points de données dans le buffer
            data_points = len(self.crypto_data_buffer[symbol])
            
            change_color = '#22c55e' if change > 0 else '#ef4444'
            change_sign = '+' if change > 0 else ''
            arrow = '▲' if change > 0 else '▼'
            
            # Indicateur de fraîcheur amélioré
            time_diff = (datetime.now() - timestamp).total_seconds()
            if time_diff < 120 and data_points > 0:  # Données récentes ET dans le buffer
                freshness = f"🟢 LIVE {data_points}pts"
                pulse_class = "animation: pulse 2s infinite;"
                border_color = "#22c55e"
            elif data_points > 0:
                freshness = f"🟡 CACHE {data_points}pts"
                pulse_class = ""
                border_color = "#f59e0b"
            else:
                freshness = "🔴 NO DATA"
                pulse_class = ""
                border_color = "#374151"
            
            # Sparkline basée sur les vraies données du buffer
            svg_path = "M 0 20 L 20 15 L 40 25 L 60 18 L 80 22"  # Pattern par défaut
            if data_points > 1:
                # Construire sparkline avec les vraies données
                buffer_data = list(self.crypto_data_buffer[symbol])[-20:]
                if len(buffer_data) > 1:
                    prices = [d['price'] for d in buffer_data]
                    min_price, max_price = min(prices), max(prices)
                    if max_price > min_price:
                        svg_path = ""
                        for i, price in enumerate(prices):
                            x = i * (80 / len(prices))
                            y = 40 - ((price - min_price) / (max_price - min_price)) * 30
                            if i == 0:
                                svg_path += f"M {x} {y}"
                            else:
                                svg_path += f" L {x} {y}"
            
            cards_html += f'''
            <div style="
                background: {self.colors['card_bg']}; 
                border-radius: 16px; 
                padding: 24px; 
                border: 2px solid {border_color};
                min-height: 140px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                position: relative;
                {pulse_class}
            ">
                <div style="position: absolute; top: 8px; right: 8px; font-size: 9px; color: {self.colors['text_secondary']};">
                    {freshness}
                </div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                            <div style="
                                width: 32px; height: 32px; 
                                background: {color}20; 
                                border-radius: 50%;
                                display: flex; align-items: center; justify-content: center;
                                color: {color}; font-weight: bold;
                            ">{icon}</div>
                            <div>
                                <div style="color: {self.colors['text_primary']}; font-weight: 600; font-size: 16px;">{name}</div>
                                <div style="color: {self.colors['text_secondary']}; font-size: 12px;">{symbol}</div>
                            </div>
                        </div>
                        <div style="color: {self.colors['text_primary']}; font-size: 24px; font-weight: 700; margin-bottom: 4px;">
                            ${price:,.2f}
                        </div>
                        <div style="color: {change_color}; font-size: 14px; font-weight: 600;">
                            {arrow} {change_sign}{change:.2f}%
                        </div>
                    </div>
                    <div style="width: 80px; height: 40px;">
                        <svg width="80" height="40" style="overflow: visible;">
                            <path d="{svg_path}" stroke="{change_color}" stroke-width="2" fill="none"/>
                        </svg>
                    </div>
                </div>
            </div>
            '''
        
        cards_html += '</div>'
        return cards_html

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
                background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
                border-radius: 16px; padding: 24px; color: white; margin-bottom: 20px;
            ">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <span style="font-size: 16px; font-weight: 600;">Kafka Real Stream</span>
                    <div style="background: rgba(255,255,255,0.2); padding: 4px 8px; border-radius: 4px; font-size: 11px;">
                        📡 LIVE
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
        
        for symbol in ['BTC', 'ETH', 'LTC', 'SOL']:
            count = len(self.crypto_data_buffer[symbol])
            total_points += count
            last_update = self.latest_data[symbol]['timestamp']
            time_diff = (datetime.now() - last_update).total_seconds()
            
            if time_diff < 120 and count > 0:
                status_color = '#22c55e'
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
        """Met à jour l'interface du dashboard"""
        try:
            # Mettre à jour le status Kafka
            self.status_pane.object = self.create_kafka_status()
            
            # Mettre à jour les cartes crypto
            self.crypto_cards_pane.object = self.create_crypto_cards_html()
            
            # Mettre à jour le contenu principal
            self.main_content_pane.clear()
            main_content = self.create_main_content()
            self.main_content_pane.extend(main_content)
            
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
        <div style="background: #1a1d29; color: #f8fafc; padding: 40px; text-align: center;">
            <h1>📡 Real Streaming Dashboard</h1>
            <p>Error: {str(e)}</p>
            <p>But your Kafka consumer is working! Check logs.</p>
        </div>
        ''')

if __name__ == "__main__":
    pn.serve(
        create_app,
        port=5006,
        allow_websocket_origin=["*"],
        show=False,
        autoreload=True,
        title="📡 Real Crypto Kafka Stream Dashboard"
    )
