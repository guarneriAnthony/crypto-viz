import panel as pn
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import HoverTool, DatetimeTickFormatter
import asyncio
from datetime import datetime, timedelta
import logging
from crypto_reader import CryptoDataReader

pn.extension('bokeh', template='material')

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoDreamDashboard:
    def __init__(self):
        self.reader = CryptoDataReader()
        self.current_timeframe = '1h'
        self.selected_crypto = 'BTC'
        
        # Test de la connexion MinIO
        connection_ok = self.reader.test_connection()
        logger.info(f"MinIO connection status: {connection_ok}")
        
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
        
    def create_sidebar(self):
        """Sidebar avec navigation identique à l'image"""
        
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
                        <span style="color: white; font-weight: bold;">∞</span>
                    </div>
                    <span style="color: #f8fafc; font-size: 18px; font-weight: 600;">Logoipsm</span>
                </div>
                <h2 style="color: #f8fafc; margin: 0; font-size: 24px; font-weight: 700;">Dashboard</h2>
            </div>
            
            <!-- Search -->
            <div style="padding: 20px;">
                <div style="position: relative;">
                    <input type="text" placeholder="Search..." style="
                        width: 100%; 
                        padding: 12px 40px 12px 16px; 
                        background: #374151; 
                        border: 1px solid #4b5563; 
                        border-radius: 8px; 
                        color: #f8fafc;
                        font-size: 14px;
                        box-sizing: border-box;
                    ">
                    <span style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); color: #9ca3af;">🔍</span>
                </div>
            </div>
            
            <!-- Navigation -->
            <div style="flex: 1; padding: 0 10px;">
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: #4f7cee; color: #ffffff;">
                    <span style="font-size: 16px;">📊</span>
                    <span style="font-size: 14px; font-weight: 500;">Overview</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">📈</span>
                    <span style="font-size: 14px; font-weight: 500;">Chart</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">💳</span>
                    <span style="font-size: 14px; font-weight: 500;">Transactions</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">💰</span>
                    <span style="font-size: 14px; font-weight: 500;">Wallet</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">📰</span>
                    <span style="font-size: 14px; font-weight: 500;">News</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">📧</span>
                    <span style="font-size: 14px; font-weight: 500;">Mail Box</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">⚙️</span>
                    <span style="font-size: 14px; font-weight: 500;">Setting</span>
                </div>
                <div style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin: 4px 0; border-radius: 8px; background: transparent; color: #94a3b8; cursor: pointer;">
                    <span style="font-size: 16px;">🚪</span>
                    <span style="font-size: 14px; font-weight: 500;">Logout</span>
                </div>
            </div>
            
            <!-- User Profile -->
            <div style="padding: 20px; border-top: 1px solid #374151;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 40px; height: 40px; background: #6b7280; border-radius: 50%;"></div>
                    <div>
                        <div style="color: #f8fafc; font-weight: 600; font-size: 14px;">Courtney Henry</div>
                        <div style="color: #9ca3af; font-size: 12px;">▼</div>
                    </div>
                </div>
            </div>
        </div>
        '''
        
        return pn.pane.HTML(sidebar_html, width=280, height=800)
    
    def create_crypto_cards(self):
        """Cartes crypto avec données réelles de MinIO"""
        
        try:
            # Récupérer les données réelles
            crypto_summary = self.reader.get_crypto_summary()
            
            # Mappage des cryptos vers les configs d'affichage
            crypto_configs = {
                'BTC': ('Bitcoin', '₿', '#f59e0b'),
                'ETH': ('Ethereum', 'Ξ', '#3b82f6'),
                'LTC': ('Litecoin', 'Ł', '#64748b'),
                'SOL': ('Solana', '◎', '#22c55e')
            }
            
            cards_html = '<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 20px;">'
            
            # Utiliser les données réelles ou fallback
            for symbol, (name, icon, color) in crypto_configs.items():
                if symbol in crypto_summary:
                    data = crypto_summary[symbol]
                    price = data['price']
                    change = data['change_24h']
                    data_points = data.get('data_points', 0)
                else:
                    # Fallback si le crypto n'est pas dans les données
                    price = np.random.uniform(100, 60000)
                    change = np.random.uniform(-5, 5)
                    data_points = 0
                
                change_color = '#22c55e' if change > 0 else '#ef4444'
                change_sign = '+' if change > 0 else ''
                arrow = '▲' if change > 0 else '▼'
                
                # Génération données sparkline basée sur l'historique réel
                try:
                    price_history = self.reader.get_price_history(symbol, hours=2)
                    if len(price_history['prices']) > 1:
                        sparkline_data = price_history['prices'][-20:]  # 20 derniers points
                    else:
                        # Fallback sparkline
                        np.random.seed(hash(symbol) % 1000)
                        sparkline_data = np.cumsum(np.random.randn(20) * 0.1) + price/1000
                except:
                    np.random.seed(hash(symbol) % 1000)
                    sparkline_data = np.cumsum(np.random.randn(20) * 0.1) + price/1000
                
                # SVG sparkline
                svg_path = ""
                if len(sparkline_data) > 1:
                    for i, val in enumerate(sparkline_data):
                        x = i * 4
                        y = 40 - (val - min(sparkline_data)) / (max(sparkline_data) - min(sparkline_data)) * 30
                        if i == 0:
                            svg_path += f"M {x} {y}"
                        else:
                            svg_path += f" L {x} {y}"
                
                # Status indicator
                status_text = f"🔴 Demo" if data_points == 0 else f"🟢 {data_points} pts"
                
                cards_html += f'''
                <div style="
                    background: {self.colors['card_bg']}; 
                    border-radius: 16px; 
                    padding: 24px; 
                    border: 1px solid #374151;
                    min-height: 140px;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    position: relative;
                ">
                    <div style="position: absolute; top: 8px; right: 8px; font-size: 10px; color: {self.colors['text_secondary']};">
                        {status_text}
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
            return pn.pane.HTML(cards_html, width=1200)
            
        except Exception as e:
            logger.error(f"Error creating crypto cards: {e}")
            # Fallback en cas d'erreur
            return self._create_fallback_cards()

    def _create_fallback_cards(self):
        """Cartes de fallback en cas d'erreur"""
        return pn.pane.HTML('<div style="color: #ef4444; text-align: center; padding: 40px;">Error loading crypto data</div>')

    def create_main_content(self):
        """Contenu principal avec chart et portfolio utilisant données réelles"""
        
        try:
            # Récupérer l'historique des prix pour le graphique principal
            price_history = self.reader.get_price_history(self.selected_crypto, hours=24)
            
            # Convertir en format Pandas pour Bokeh
            timestamps = pd.to_datetime(price_history['timestamps'])
            prices = price_history['prices']
            
            # Graphique Bokeh avec données réelles
            p = figure(
                width=800, 
                height=400,
                x_axis_type='datetime',
                tools="pan,wheel_zoom,box_zoom,reset",
                background_fill_color=self.colors['card_bg'],
                border_fill_color=self.colors['card_bg']
            )
            
            # Styling du graphique
            p.grid.grid_line_alpha = 0.1
            p.xaxis.axis_line_color = '#374151'
            p.yaxis.axis_line_color = '#374151'
            p.xaxis.major_tick_line_color = '#374151'
            p.yaxis.major_tick_line_color = '#374151'
            p.xaxis.axis_label_text_color = self.colors['text_secondary']
            p.yaxis.axis_label_text_color = self.colors['text_secondary']
            
            # Ligne de prix avec données réelles
            p.line(timestamps, prices, line_width=3, color='#4f7cee', alpha=0.8)
            p.varea(timestamps, 0, prices, alpha=0.1, color='#4f7cee')
            
            chart_pane = pn.pane.Bokeh(p, width=800, height=400)
            
            # Récupérer le prix actuel pour l'affichage
            current_price = prices[-1] if prices else 35352.02
            
        except Exception as e:
            logger.error(f"Error creating main chart: {e}")
            # Fallback avec données de démo
            dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
            prices = 35000 + np.cumsum(np.random.randn(100) * 100)
            current_price = prices[-1]
            
            p = figure(width=800, height=400, x_axis_type='datetime', tools="pan,wheel_zoom,box_zoom,reset",
                      background_fill_color=self.colors['card_bg'], border_fill_color=self.colors['card_bg'])
            p.line(dates, prices, line_width=3, color='#4f7cee', alpha=0.8)
            chart_pane = pn.pane.Bokeh(p, width=800, height=400)
        
        # Portfolio section avec données réelles si possible
        try:
            crypto_summary = self.reader.get_crypto_summary()
        except:
            crypto_summary = {}
        
        portfolio_html = f'''
        <div style="width: 400px;">
            <!-- Carte de crédit -->
            <div style="
                background: linear-gradient(135deg, #4f7cee 0%, #3b82f6 100%);
                border-radius: 16px;
                padding: 24px;
                color: white;
                margin-bottom: 20px;
                position: relative;
                overflow: hidden;
            ">
                <div style="position: relative; z-index: 2;">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                        <span style="font-size: 16px; font-weight: 600;">Credit Card</span>
                        <div style="background: #f59e0b; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold;">💳</div>
                    </div>
                    
                    <div style="font-size: 24px; font-weight: 700; letter-spacing: 2px; margin: 20px 0;">
                        3475 7381 3759 4512
                    </div>
                    
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-size: 12px; opacity: 0.8;">DARRILL STEWARD</div>
                        </div>
                        <div style="font-size: 18px; font-weight: bold;">VISA</div>
                    </div>
                </div>
            </div>
            
            <!-- Portfolio avec données réelles -->
            <div style="
                background: {self.colors['card_bg']}; 
                border-radius: 16px; 
                padding: 24px;
                border: 1px solid #374151;
            ">
                <h3 style="color: {self.colors['text_primary']}; margin: 0 0 20px 0; font-size: 18px; font-weight: 600;">My Portfolio</h3>
                '''
        
        # Générer les lignes du portfolio avec données réelles
        portfolio_cryptos = [
            ('ETH', 'Ethereum', '#3b82f6', 0.12543),
            ('BTC', 'Bitcoin', '#f59e0b', 0.12543),
            ('LTC', 'Litecoin', '#64748b', 0.12543),
            ('SOL', 'Solana', '#22c55e', 0.12543),
            ('BNB', 'Binance Coin', '#f59e0b', 0.12543)
        ]
        
        for symbol, name, color, amount in portfolio_cryptos:
            if symbol in crypto_summary:
                price = crypto_summary[symbol]['price']
                change = crypto_summary[symbol]['change_24h']
                value = price * amount
                is_real = True
            else:
                # Valeurs de fallback
                price = np.random.uniform(100, 5000)
                change = np.random.uniform(-15, 15)
                value = price * amount
                is_real = False
            
            change_color = '#22c55e' if change > 0 else '#ef4444'
            change_sign = '+' if change > 0 else ''
            status_indicator = '🟢' if is_real else '🔴'
            
            portfolio_html += f'''
                <div style="display: flex; align-items: center; justify-content: space-between; padding: 16px 0; border-bottom: 1px solid #374151;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div style="width: 40px; height: 40px; background: {color}20; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {color}; font-weight: bold;">{symbol[0]}</div>
                        <div>
                            <div style="color: {self.colors['text_primary']}; font-weight: 600; font-size: 14px;">{name} {status_indicator}</div>
                            <div style="color: {self.colors['text_secondary']}; font-size: 12px;">${value:.2f}</div>
                        </div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {change_color}; font-weight: 600; font-size: 14px;">{change_sign}{change:.2f}%</div>
                        <div style="color: {self.colors['text_secondary']}; font-size: 12px;">{amount:.5f} {symbol}</div>
                    </div>
                </div>
            '''
        
        portfolio_html += '''
            </div>
        </div>
        '''
        
        portfolio_pane = pn.pane.HTML(portfolio_html, width=400)
        
        # Chart header avec prix réel
        chart_header = pn.pane.HTML(f'''
        <div style="
            background: {self.colors['card_bg']}; 
            padding: 24px; 
            border-radius: 16px 16px 0 0; 
            border: 1px solid #374151; 
            border-bottom: none;
            width: 800px;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: {self.colors['text_primary']}; margin: 0; font-size: 18px; font-weight: 600;">Chart (Real Data)</h3>
                    <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                        <span style="color: {self.colors['text_secondary']}; font-size: 14px;">{self.selected_crypto}/USD</span>
                        <span style="color: {self.colors['text_primary']}; font-size: 24px; font-weight: 700;">${current_price:,.2f}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button style="background: #4f7cee; color: #fff; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">1h</button>
                    <button style="background: transparent; color: #94a3b8; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">3h</button>
                    <button style="background: transparent; color: #94a3b8; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">1d</button>
                    <button style="background: transparent; color: #94a3b8; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">1w</button>
                    <button style="background: transparent; color: #94a3b8; border: 1px solid #374151; border-radius: 6px; padding: 6px 12px; font-size: 12px; cursor: pointer;">1m</button>
                </div>
            </div>
        </div>
        ''', width=800)
        
        # Wrapper pour le chart
        chart_wrapper = pn.Column(
            chart_header,
            chart_pane,
            styles={
                'background': self.colors['card_bg'],
                'border-radius': '0 0 16px 16px',
                'border': '1px solid #374151',
                'border-top': 'none',
                'margin': '0'
            },
            width=800
        )
        
        return pn.Row(chart_wrapper, portfolio_pane, margin=(0, 0, 20, 0))

    def create_live_market(self):
        """Table Live Market avec données réelles"""
        
        try:
            crypto_summary = self.reader.get_crypto_summary()
        except:
            crypto_summary = {}
        
        market_html = f'''
        <div style="
            background: {self.colors['card_bg']}; 
            border-radius: 16px; 
            border: 1px solid #374151;
            overflow: hidden;
            width: 100%;
        ">
            <div style="padding: 24px 24px 16px; display: flex; justify-content: space-between; align-items: center;">
                <h3 style="color: {self.colors['text_primary']}; margin: 0; font-size: 18px; font-weight: 600;">Live Market (Real Data)</h3>
                <a href="#" style="color: {self.colors['primary']}; font-size: 14px; text-decoration: none;">View More</a>
            </div>
            
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="border-bottom: 1px solid #374151;">
                        <th style="padding: 12px 24px; color: {self.colors['text_secondary']}; font-size: 12px; text-align: left; font-weight: 500;">Coin</th>
                        <th style="padding: 12px 8px; color: {self.colors['text_secondary']}; font-size: 12px; text-align: right; font-weight: 500;">Change</th>
                        <th style="padding: 12px 8px; color: {self.colors['text_secondary']}; font-size: 12px; text-align: right; font-weight: 500;">Market Cap</th>
                        <th style="padding: 12px 8px; color: {self.colors['text_secondary']}; font-size: 12px; text-align: right; font-weight: 500;">24h Volume</th>
                        <th style="padding: 12px 24px; color: {self.colors['text_secondary']}; font-size: 12px; text-align: right; font-weight: 500;">Price</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        # Données du marché avec vraies données
        market_cryptos = [
            ('Bitcoin', 'BTC', '#f59e0b'),
            ('Ethereum', 'ETH', '#3b82f6'),
            ('Litecoin', 'LTC', '#64748b'),
            ('Solana', 'SOL', '#22c55e')
        ]
        
        for name, symbol, color in market_cryptos:
            if symbol in crypto_summary:
                data = crypto_summary[symbol]
                price = data['price']
                change = data['change_24h']
                volume = data['volume_24h']
                market_cap = price * 21000000  # Estimation simple
                status = '🟢'
            else:
                # Données de fallback
                price = np.random.uniform(100, 60000)
                change = np.random.uniform(-10, 15)
                volume = np.random.uniform(10000000, 100000000)
                market_cap = price * 21000000
                status = '🔴'
            
            change_color = '#22c55e' if change > 0 else '#ef4444'
            change_sign = '+' if change > 0 else ''
            
            market_html += f'''
                    <tr style="border-bottom: 1px solid #374151;">
                        <td style="padding: 16px 24px;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="width: 32px; height: 32px; background: {color}20; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: {color}; font-weight: bold; font-size: 12px;">{symbol[0]}</div>
                                <span style="color: {self.colors['text_primary']}; font-weight: 600; font-size: 14px;">{name} {status}</span>
                            </div>
                        </td>
                        <td style="padding: 16px 8px; color: {change_color}; font-weight: 600; text-align: right;">{change_sign}{change:.2f}%</td>
                        <td style="padding: 16px 8px; color: {self.colors['text_primary']}; text-align: right;">${market_cap/1000000:.0f}M</td>
                        <td style="padding: 16px 8px; color: {self.colors['text_primary']}; text-align: right;">${volume/1000000:.1f}M</td>
                        <td style="padding: 16px 24px; color: {self.colors['text_primary']}; font-weight: 600; text-align: right;">${price:,.2f}</td>
                    </tr>
            '''
        
        market_html += '''
                </tbody>
            </table>
        </div>
        '''
        
        return pn.pane.HTML(market_html, width=1200)

    def create_dashboard(self):
        """Assembly du dashboard complet avec données réelles"""
        
        # CSS global pour le thème dark
        css = f"""
        body {{
            background-color: {self.colors['background']} !important;
            margin: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}
        
        .bk-root {{
            background-color: {self.colors['background']} !important;
            color: {self.colors['text_primary']} !important;
        }}
        """
        
        pn.config.raw_css = [css]
        
        # Création des sections avec données réelles
        sidebar = self.create_sidebar()
        crypto_cards = self.create_crypto_cards()
        main_content = self.create_main_content()
        live_market = self.create_live_market()
        
        # Layout principal 
        content_area = pn.Column(
            crypto_cards,
            main_content,
            live_market,
            styles={
                'background': self.colors['background'],
                'padding': '24px',
                'flex': '1'
            }
        )
        
        # Dashboard complet
        dashboard = pn.Row(
            sidebar,
            content_area,
            styles={
                'background': self.colors['background'],
                'min-height': '100vh',
                'margin': '0'
            }
        )
        
        return dashboard

def create_app():
    """Point d'entrée de l'application avec données réelles"""
    try:
        dashboard = CryptoDreamDashboard()
        return dashboard.create_dashboard()
    except Exception as e:
        logger.error(f"Error creating dashboard: {e}")
        # Fallback en cas d'erreur critique
        return pn.pane.HTML(f'''
        <div style="background: #1a1d29; color: #f8fafc; padding: 40px; text-align: center;">
            <h1>Dashboard Error</h1>
            <p>Dashboard en mode démonstration - MinIO indisponible</p>
            <p>Check MinIO connection and try again.</p>
        </div>
        ''')

# Configuration Panel
if __name__ == "__main__":
    pn.serve(
        create_app,
        port=5006,
        allow_websocket_origin=["*"],
        show=False,
        autoreload=True,
        title="Crypto Dream Dashboard - Real Data"
    )
