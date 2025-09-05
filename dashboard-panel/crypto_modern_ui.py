#!/usr/bin/env python3
"""
CryptoViz Dashboard - Design exact de l'image fournie
Interface moderne avec thème sombre, sidebar, cartes crypto et layout professionnel
"""

import panel as pn
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import sys
import os
from datetime import datetime
import random

# Configuration Panel
pn.extension('bokeh', 'tabulator')

# Import reader
sys.path.append('/app')
from utils.parquet_reader_partitioned import get_partitioned_reader

class ModernCryptoDashboard:
    """Dashboard avec le design exact de l'image"""
    
    def __init__(self):
        self.reader = get_partitioned_reader()
        self.df = self.reader.read_all_data()
        
        # Couleurs crypto comme dans l'image
        self.crypto_colors = {
            'BTC': '#F7931A',
            'ETH': '#627EEA', 
            'LTC': '#BFBBBB',
            'SOL': '#9945FF',
            'BNB': '#F3BA2F',
            'ADA': '#0033AD',
            'XRP': '#23292F',
            'DOGE': '#C2A633',
            'TRX': '#FF060A',
            'USDT': '#26A17B'
        }
    
    def create_dark_theme_css(self):
        """CSS exact du design de l'image"""
        return """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body, html {
            background: #0F0F23 !important;
            color: #FFFFFF !important;
            overflow-x: hidden;
        }
        
        .dashboard-container {
            display: flex;
            min-height: 100vh;
            background: #0F0F23;
        }
        
        /* SIDEBAR - Exact comme l'image */
        .sidebar {
            width: 280px;
            background: linear-gradient(180deg, #1A1B3A 0%, #161632 100%);
            padding: 0;
            position: fixed;
            height: 100vh;
            left: 0;
            top: 0;
            z-index: 1000;
            border-right: 1px solid #2A2D5A;
        }
        
        .logo-section {
            padding: 30px 25px;
            border-bottom: 1px solid #2A2D5A;
            text-align: left;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .logo-icon {
            width: 32px;
            height: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
        }
        
        .logo-text {
            font-size: 22px;
            font-weight: 700;
            color: white;
        }
        
        .nav-menu {
            padding: 20px 0;
        }
        
        .nav-item {
            display: flex;
            align-items: center;
            padding: 15px 25px;
            color: #8B92B0;
            text-decoration: none;
            transition: all 0.3s ease;
            border-radius: 0;
            font-size: 15px;
            font-weight: 500;
        }
        
        .nav-item.active {
            background: linear-gradient(90deg, rgba(102, 126, 234, 0.15) 0%, transparent 100%);
            color: #667eea;
            border-right: 3px solid #667eea;
        }
        
        .nav-item:hover {
            background: rgba(102, 126, 234, 0.08);
            color: #667eea;
        }
        
        .nav-icon {
            width: 20px;
            margin-right: 15px;
            font-size: 16px;
        }
        
        /* MAIN CONTENT */
        .main-content {
            margin-left: 280px;
            width: calc(100% - 280px);
            background: #0F0F23;
            min-height: 100vh;
        }
        
        /* HEADER - Exact comme l'image */
        .top-header {
            background: #161632;
            padding: 20px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #2A2D5A;
        }
        
        .page-title {
            font-size: 28px;
            font-weight: 600;
            color: white;
        }
        
        .header-right {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .search-box {
            position: relative;
        }
        
        .search-input {
            background: #2A2D5A;
            border: 1px solid #3A3D6A;
            border-radius: 8px;
            padding: 10px 15px 10px 40px;
            color: white;
            width: 250px;
            font-size: 14px;
        }
        
        .search-icon {
            position: absolute;
            left: 12px;
            top: 50%;
            transform: translateY(-50%);
            color: #8B92B0;
        }
        
        .notification-btn {
            width: 40px;
            height: 40px;
            background: #2A2D5A;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .notification-btn:hover {
            background: #3A3D6A;
        }
        
        .user-profile {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .avatar {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
        }
        
        .user-info {
            text-align: left;
        }
        
        .user-name {
            font-size: 14px;
            font-weight: 600;
            color: white;
            line-height: 1.2;
        }
        
        .user-time {
            font-size: 12px;
            color: #8B92B0;
            line-height: 1.2;
        }
        
        /* CRYPTO CARDS - Exact comme l'image */
        .crypto-cards-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            padding: 30px;
        }
        
        .crypto-card {
            background: linear-gradient(135deg, #1A1B3A 0%, #161632 100%);
            border: 1px solid #2A2D5A;
            border-radius: 16px;
            padding: 20px;
            position: relative;
            transition: all 0.3s ease;
        }
        
        .crypto-card:hover {
            transform: translateY(-2px);
            border-color: #667eea;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .crypto-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .crypto-logo {
            width: 32px;
            height: 32px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 14px;
            color: white;
        }
        
        .crypto-details h4 {
            font-size: 16px;
            font-weight: 600;
            color: white;
            margin-bottom: 2px;
        }
        
        .crypto-details span {
            font-size: 12px;
            color: #8B92B0;
        }
        
        .trend-icon {
            font-size: 18px;
        }
        
        .trend-up { color: #22c55e; }
        .trend-down { color: #ef4444; }
        
        .crypto-price {
            font-size: 24px;
            font-weight: 700;
            color: white;
            margin: 10px 0 8px 0;
        }
        
        .crypto-change {
            font-size: 13px;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 6px;
        }
        
        .change-positive {
            background: rgba(34, 197, 94, 0.1);
            color: #22c55e;
        }
        
        .change-negative {
            background: rgba(239, 68, 68, 0.1);
            color: #ef4444;
        }
        
        /* MINI CHART dans les cartes */
        .mini-chart {
            position: absolute;
            bottom: 15px;
            right: 15px;
            width: 60px;
            height: 30px;
            opacity: 0.7;
        }
        
        /* MAIN CHART AREA */
        .chart-section {
            padding: 0 30px 30px 30px;
        }
        
        .chart-container {
            background: linear-gradient(135deg, #1A1B3A 0%, #161632 100%);
            border: 1px solid #2A2D5A;
            border-radius: 16px;
            padding: 25px;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .chart-title {
            font-size: 20px;
            font-weight: 600;
            color: white;
        }
        
        .chart-controls {
            display: flex;
            gap: 8px;
        }
        
        .time-btn {
            padding: 8px 16px;
            background: transparent;
            border: 1px solid #2A2D5A;
            border-radius: 6px;
            color: #8B92B0;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .time-btn.active, .time-btn:hover {
            background: #667eea;
            border-color: #667eea;
            color: white;
        }
        
        /* RESPONSIVE */
        @media (max-width: 1400px) {
            .crypto-cards-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        @media (max-width: 768px) {
            .sidebar {
                width: 60px;
            }
            .main-content {
                margin-left: 60px;
                width: calc(100% - 60px);
            }
            .nav-item span {
                display: none;
            }
            .crypto-cards-grid {
                grid-template-columns: 1fr;
                padding: 20px;
            }
        }
        </style>
        """

    def create_sidebar(self):
        """Sidebar exactement comme dans l'image"""
        sidebar_html = """
        <div class="sidebar">
            <div class="logo-section">
                <div class="logo">
                    <div class="logo-icon">₿</div>
                    <div class="logo-text">CryptoViz</div>
                </div>
            </div>
            
            <nav class="nav-menu">
                <a href="#" class="nav-item active">
                    <div class="nav-icon">📊</div>
                    <span>Dashboard</span>
                </a>
                <a href="#" class="nav-item">
                    <div class="nav-icon">💰</div>
                    <span>Portfolio</span>
                </a>
                <a href="#" class="nav-item">
                    <div class="nav-icon">📈</div>
                    <span>Markets</span>
                </a>
                <a href="#" class="nav-item">
                    <div class="nav-icon">🔄</div>
                    <span>Trading</span>
                </a>
                <a href="#" class="nav-item">
                    <div class="nav-icon">📰</div>
                    <span>News</span>
                </a>
                <a href="#" class="nav-item">
                    <div class="nav-icon">⚙️</div>
                    <span>Settings</span>
                </a>
            </nav>
        </div>
        """
        return pn.pane.HTML(sidebar_html, margin=0, sizing_mode='stretch_width')

    def create_header(self):
        """Header avec recherche et profil comme dans l'image"""
        current_time = datetime.now().strftime("%H:%M")
        header_html = f"""
        <div class="top-header">
            <div class="page-title">Dashboard</div>
            <div class="header-right">
                <div class="search-box">
                    <div class="search-icon">🔍</div>
                    <input type="text" class="search-input" placeholder="Search cryptocurrencies...">
                </div>
                <div class="notification-btn">🔔</div>
                <div class="user-profile">
                    <div class="user-info">
                        <div class="user-name">John Doe</div>
                        <div class="user-time">{current_time}</div>
                    </div>
                    <div class="avatar">JD</div>
                </div>
            </div>
        </div>
        """
        return pn.pane.HTML(header_html, margin=0, sizing_mode='stretch_width')

    def create_crypto_card(self, crypto, price, change_24h):
        """Carte crypto individuelle avec mini-chart comme dans l'image"""
        color = self.crypto_colors.get(crypto, '#667eea')
        trend = "↗" if change_24h > 0 else "↘"
        trend_class = "trend-up" if change_24h > 0 else "trend-down"
        change_class = "change-positive" if change_24h > 0 else "change-negative"
        
        # Génère des données pour mini-chart sparkline
        mini_data = [random.uniform(0.8, 1.2) for _ in range(20)]
        
        card_html = f"""
        <div class="crypto-card">
            <div class="card-header">
                <div class="crypto-info">
                    <div class="crypto-logo" style="background-color: {color}">
                        {crypto[:2]}
                    </div>
                    <div class="crypto-details">
                        <h4>{crypto}</h4>
                        <span>{crypto}USDT</span>
                    </div>
                </div>
                <div class="trend-icon {trend_class}">{trend}</div>
            </div>
            
            <div class="crypto-price">${price:,.2f}</div>
            <div class="crypto-change {change_class}">
                {change_24h:+.2f}%
            </div>
            
            <div class="mini-chart">
                <svg width="60" height="30" viewBox="0 0 60 30">
                    <polyline points="{','.join([f'{i*3},{30-v*10}' for i, v in enumerate(mini_data)])}"
                              fill="none" stroke="{color}" stroke-width="1.5" opacity="0.8"/>
                </svg>
            </div>
        </div>
        """
        return pn.pane.HTML(card_html, margin=0, sizing_mode='stretch_width')

    def create_crypto_cards_grid(self):
        """Grille de cartes crypto comme dans l'image"""
        if self.df.empty:
            return pn.pane.HTML("<div>No crypto data available</div>")
        
        # Prendre les dernières données par crypto
        latest_data = self.df.groupby('symbol').last().reset_index()
        
        cards = []
        for _, row in latest_data.head(8).iterrows():  # 8 cartes max
            crypto = row['symbol']
            price = float(row['price'])
            # Calcul changement 24h simulé
            change_24h = random.uniform(-5, 10)
            cards.append(self.create_crypto_card(crypto, price, change_24h))
        
        # Organise en grille de 4 colonnes
        grid_html = '<div class="crypto-cards-grid">' + ''.join([card.object for card in cards]) + '</div>'
        return pn.pane.HTML(grid_html, margin=0, sizing_mode='stretch_width')

    def create_main_chart(self):
        """Graphique principal stylé comme dans l'image"""
        if self.df.empty:
            return pn.pane.HTML("<div>No data for chart</div>")
        
        # Prépare données BTC pour le graphique principal
        btc_data = self.df[self.df['symbol'] == 'BTC'].copy()
        if btc_data.empty:
            # Fallback avec première crypto disponible
            btc_data = self.df[self.df['symbol'] == self.df['symbol'].iloc[0]].copy()
        
        btc_data = btc_data.sort_values('timestamp')
        
        # Créer figure Bokeh avec style dark
        p = figure(
            width=800, height=400,
            x_axis_type='datetime',
            title="Bitcoin Price Chart",
            toolbar_location=None,
            background_fill_color='#161632',
            border_fill_color='#161632'
        )
        
        # Style du graphique
        p.title.text_color = "white"
        p.title.text_font_size = "16px"
        p.xgrid.grid_line_color = "#2A2D5A"
        p.ygrid.grid_line_color = "#2A2D5A"
        p.xaxis.axis_line_color = "#2A2D5A"
        p.yaxis.axis_line_color = "#2A2D5A"
        p.xaxis.major_tick_line_color = "#2A2D5A"
        p.yaxis.major_tick_line_color = "#2A2D5A"
        p.xaxis.axis_label_text_color = "#8B92B0"
        p.yaxis.axis_label_text_color = "#8B92B0"
        p.xaxis.major_label_text_color = "#8B92B0"
        p.yaxis.major_label_text_color = "#8B92B0"
        
        # Ligne de prix avec gradient
        p.line(
            btc_data['timestamp'], btc_data['price'],
            line_width=3, color='#667eea',
            alpha=0.9
        )
        
        # Points sur la ligne
        p.circle(
            btc_data['timestamp'], btc_data['price'],
            size=4, color='#667eea', alpha=0.7
        )
        
        # Header du graphique avec contrôles
        chart_header = """
        <div class="chart-header">
            <div class="chart-title">Price Overview</div>
            <div class="chart-controls">
                <button class="time-btn active">1D</button>
                <button class="time-btn">7D</button>
                <button class="time-btn">1M</button>
                <button class="time-btn">3M</button>
                <button class="time-btn">1Y</button>
            </div>
        </div>
        """
        
        chart_container = pn.Column(
            pn.pane.HTML(chart_header, margin=0),
            p,
            margin=0
        )
        
        return pn.pane.HTML(f'<div class="chart-container">{chart_container._repr_html_()}</div>')

    def create_dashboard_layout(self):
        """Layout complet du dashboard comme dans l'image"""
        # CSS globaux
        css = pn.pane.HTML(self.create_dark_theme_css(), margin=0)
        
        # Composants principaux
        sidebar = self.create_sidebar()
        header = self.create_header()
        crypto_cards = self.create_crypto_cards_grid()
        main_chart = self.create_main_chart()
        
        # Structure principale
        main_content = pn.Column(
            header,
            crypto_cards,
            pn.pane.HTML('<div class="chart-section">', margin=0),
            main_chart,
            pn.pane.HTML('</div>', margin=0),
            margin=0,
            css_classes=['main-content']
        )
        
        # Container global
        dashboard = pn.Column(
            css,
            pn.pane.HTML('<div class="dashboard-container">', margin=0),
            pn.Row(
                sidebar,
                main_content,
                margin=0
            ),
            pn.pane.HTML('</div>', margin=0),
            margin=0
        )
        
        return dashboard

# FONCTION PRINCIPALE
def create_modern_dashboard():
    """Créer et servir le dashboard moderne"""
    try:
        dashboard = ModernCryptoDashboard()
        layout = dashboard.create_dashboard_layout()
        return layout
    except Exception as e:
        error_html = f"""
        <div style="background: #1A1B3A; color: white; padding: 40px; text-align: center; font-family: 'Inter', sans-serif;">
            <h2>🚨 Erreur Dashboard</h2>
            <p>Erreur: {str(e)}</p>
            <p style="color: #8B92B0; margin-top: 20px;">Vérifiez les données et la configuration.</p>
        </div>
        """
        return pn.pane.HTML(error_html)

# SERVEUR
if __name__ == "__main__":
    print("🚀 Démarrage du Dashboard Moderne CryptoViz...")
    
    # Configuration serveur
    pn.config.allow_websocket_origin = ["*"]
    
    # Créer l'application
    app = create_modern_dashboard()
    
    # Servir l'application
    app.servable()
    
    print("✅ Dashboard moderne prêt sur le port 5006!")
    print("🌐 URL: http://192.168.1.76:5006")
