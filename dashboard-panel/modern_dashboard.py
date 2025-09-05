#!/usr/bin/env python3
"""
CryptoViz Dashboard Moderne - Style Dark Theme
Interface élégante inspirée des meilleurs dashboards crypto
"""

import panel as pn
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, DatetimeTickFormatter
from bokeh.palettes import Category20
import sys
import os
from datetime import datetime, timedelta
import random

# Configuration Panel avec thème moderne
pn.extension('bokeh', 'tabulator', template='bootstrap')

# Import reader
sys.path.append('/app')
from utils.parquet_reader_partitioned import get_partitioned_reader

def create_modern_dashboard():
    """Création dashboard moderne simplifié mais élégant"""
    
    try:
        # Lecture des données
        reader = get_partitioned_reader()
        df = reader.read_all_data()
        
        if df.empty:
            return pn.pane.HTML("""
            <div style="background: #0a0b0d; color: white; padding: 40px; text-align: center; min-height: 100vh; font-family: 'Inter', sans-serif;">
                <h2>Dashboard en cours de chargement...</h2>
                <p style="color: #a0aec0;">Aucune donnée disponible pour le moment</p>
            </div>
            """)
        
        # CSS moderne
        modern_css = """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif !important; }
        
        body, .bk-root { 
            background: #0a0b0d !important; 
            color: #ffffff !important; 
        }
        
        .modern-card {
            background: linear-gradient(135deg, #1a1d29 0%, #16192b 100%);
            border: 1px solid #2d3748;
            border-radius: 16px;
            padding: 25px;
            margin: 15px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            transition: all 0.3s ease;
        }
        
        .modern-card:hover {
            transform: translateY(-2px);
            border-color: #667eea;
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .crypto-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .crypto-item {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border: 1px solid #4a5568;
            border-radius: 12px;
            padding: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease;
        }
        
        .crypto-item:hover {
            transform: scale(1.02);
            border-color: #667eea;
        }
        
        .crypto-info h3 {
            color: white;
            margin: 0 0 5px 0;
            font-size: 18px;
            font-weight: 600;
        }
        
        .crypto-info p {
            color: #a0aec0;
            margin: 0;
            font-size: 14px;
        }
        
        .crypto-price {
            text-align: right;
        }
        
        .price-value {
            color: white;
            font-size: 20px;
            font-weight: 700;
            margin: 0;
        }
        
        .price-change {
            font-size: 14px;
            font-weight: 500;
            padding: 4px 8px;
            border-radius: 6px;
            margin: 5px 0 0 0;
        }
        
        .positive { 
            color: #48bb78; 
            background: rgba(72, 187, 120, 0.1); 
        }
        
        .negative { 
            color: #f56565; 
            background: rgba(245, 101, 101, 0.1); 
        }
        
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 16px;
            margin: 20px;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        
        .main-header h1 {
            margin: 0 0 10px 0;
            font-size: 36px;
            font-weight: 700;
        }
        
        .main-header p {
            margin: 0;
            opacity: 0.9;
            font-size: 16px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #2d3748 0%, #1a202c 100%);
            border: 1px solid #4a5568;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 28px;
            font-weight: 700;
            color: white;
            margin: 0 0 5px 0;
        }
        
        .stat-label {
            color: #a0aec0;
            font-size: 14px;
            margin: 0;
        }
        </style>
        """
        
        # Header principal
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        stats = reader.get_summary_stats()
        
        header = f"""
        <div class="main-header">
            <h1>CryptoViz Dashboard</h1>
            <p>Pipeline Data Lakehouse • Temps Réel • {current_time}</p>
        </div>
        """
        
        # Statistiques
        stats_html = f"""
        <div class="stats-grid">
            <div class="stat-card">
                <p class="stat-value">{stats.get('total_files', 0)}</p>
                <p class="stat-label">Fichiers Parquet</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">{stats.get('total_records', 0)}</p>
                <p class="stat-label">Enregistrements</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">{stats.get('cryptos_count', 0)}</p>
                <p class="stat-label">Cryptomonnaies</p>
            </div>
            <div class="stat-card">
                <p class="stat-value">📈</p>
                <p class="stat-label">Live Data</p>
            </div>
        </div>
        """
        
        # Grille crypto moderne
        crypto_items = []
        latest_data = df.groupby('symbol').tail(1).sort_values('price', ascending=False)
        
        for _, crypto in latest_data.iterrows():
            symbol = crypto['symbol']
            name = crypto.get('name', symbol)
            price = crypto['price']
            change = crypto.get('change_24h', 0)
            
            price_formatted = f"${price:,.2f}" if price > 1 else f"${price:.4f}"
            change_class = "positive" if change > 0 else "negative"
            change_formatted = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
            
            crypto_items.append(f"""
            <div class="crypto-item">
                <div class="crypto-info">
                    <h3>{name}</h3>
                    <p>{symbol}</p>
                </div>
                <div class="crypto-price">
                    <p class="price-value">{price_formatted}</p>
                    <p class="price-change {change_class}">{change_formatted}</p>
                </div>
            </div>
            """)
        
        crypto_grid = f"""
        <div class="modern-card">
            <h2 style="color: white; margin: 0 0 20px 0;">Cryptomonnaies Live</h2>
            <div class="crypto-grid">
                {''.join(crypto_items)}
            </div>
        </div>
        """
        
        # Graphique principal simple
        p = figure(
            title="Prix des Cryptomonnaies",
            height=400,
            sizing_mode='stretch_width',
            background_fill_color="#1a202c",
            border_fill_color="#1a202c"
        )
        
        # Configuration thème sombre
        p.title.text_color = "white"
        p.grid.grid_line_color = "#2d3748"
        p.grid.grid_line_alpha = 0.3
        p.axis.axis_line_color = "#4a5568"
        p.axis.major_tick_line_color = "#4a5568"
        p.axis.axis_label_text_color = "#a0aec0"
        p.axis.major_label_text_color = "#a0aec0"
        
        # Données graphique
        if not df.empty and 'symbol' in df.columns:
            btc_data = df[df['symbol'] == 'BTC']
            if not btc_data.empty:
                btc_data = btc_data.sort_values('timestamp')
                p.line('timestamp', 'price', source=ColumnDataSource(btc_data),
                       line_width=3, color='#f7931a', alpha=0.8)
        
        chart_container = """
        <div class="modern-card">
            <h2 style="color: white; margin: 0 0 20px 0;">Graphique Principal</h2>
        </div>
        """
        
        # Assembly final
        dashboard = pn.Column(
            pn.pane.HTML(modern_css, height=0),
            pn.pane.HTML(header),
            pn.pane.HTML(stats_html),
            pn.pane.HTML(crypto_grid),
            pn.pane.HTML(chart_container),
            pn.pane.Bokeh(p),
            sizing_mode='stretch_width'
        )
        
        return dashboard
        
    except Exception as e:
        return pn.pane.HTML(f"""
        <div style="background: #0a0b0d; color: white; padding: 40px; text-align: center; min-height: 100vh;">
            <h2>Erreur Dashboard</h2>
            <p style="color: #f56565;">{str(e)}</p>
            <p style="color: #a0aec0;">Le dashboard sera rechargé automatiquement...</p>
        </div>
        """)

def main():
    return create_modern_dashboard()

if __name__ == "__main__":
    pn.serve(main, port=5006, address="0.0.0.0", 
             allow_websocket_origin=["*"], show=False, threaded=False)
