#!/usr/bin/env python3
"""
CryptoViz V3.0 - Modern Crypto Dashboard
Interface moderne inspirée de CoinMarketCap avec thème sombre
"""

import panel as pn
import pandas as pd
import numpy as np
import asyncio
import logging
from datetime import datetime, timedelta
import os
import sys
import time
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.palettes import Viridis3, RdYlGn11

# Configuration Panel avec thème sombre moderne
pn.extension('bokeh', 'tabulator', template='material', sizing_mode='stretch_width')
pn.config.throttled = True

# Ajout du chemin des modules
sys.path.append('/app')

# Imports des utils
from utils.parquet_reader_partitioned import get_partitioned_reader

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModernCryptoDashboard:
    """Dashboard moderne de style CoinMarketCap pour cryptomonnaies"""
    
    def __init__(self):
        logger.info("Initialisation Modern Crypto Dashboard")
        
        # Composants de données
        self.data_reader = get_partitioned_reader()
        
        # État de l'application
        self.current_data = pd.DataFrame()
        self.last_update = datetime.now()
        self.update_interval = 30  # secondes
        
        # Configuration du style CSS moderne
        self.setup_modern_styling()
        
        # Interface réactive
        self.setup_reactive_interface()
        
        logger.info("Modern Dashboard initialisé avec succès")
    
    def setup_modern_styling(self):
        """Configuration du style CSS moderne et sombre"""
        
        self.css_styles = """
        <style>
        .crypto-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #ffffff;
            padding: 15px 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        
        .nav-tabs {
            display: flex;
            gap: 25px;
            margin: 15px 0;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        
        .nav-tab {
            color: #8892b0;
            font-weight: 500;
            cursor: pointer;
            padding: 8px 12px;
            border-radius: 6px;
            transition: all 0.3s ease;
        }
        
        .nav-tab.active {
            color: #64ffda;
            background-color: rgba(100, 255, 218, 0.1);
        }
        
        .nav-tab:hover {
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.05);
        }
        
        .network-filters {
            display: flex;
            gap: 15px;
            align-items: center;
            margin: 10px 0;
        }
        
        .network-badge {
            background: #1e1e1e;
            color: #ffffff;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            border: 1px solid #333;
        }
        
        .crypto-table {
            background: #0f1419;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }
        
        .price-positive {
            color: #26a69a !important;
            font-weight: 600;
        }
        
        .price-negative {
            color: #ef5350 !important;
            font-weight: 600;
        }
        
        .market-cap-column {
            font-family: 'Roboto Mono', monospace;
            font-size: 13px;
        }
        
        .crypto-icon {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            margin-right: 10px;
        }
        
        .crypto-name {
            font-weight: 600;
            color: #ffffff;
        }
        
        .crypto-symbol {
            color: #8892b0;
            font-size: 12px;
            text-transform: uppercase;
        }
        
        .status-indicator {
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
        }
        
        .status-online {
            background-color: rgba(76, 175, 80, 0.2);
            color: #4caf50;
            border: 1px solid #4caf50;
        }
        
        .status-updating {
            background-color: rgba(255, 193, 7, 0.2);
            color: #ffc107;
            border: 1px solid #ffc107;
        }
        
        .sparkline-container {
            width: 100px;
            height: 40px;
        }
        </style>
        """
    
    def setup_reactive_interface(self):
        """Configuration de l'interface réactive moderne"""
        
        # Header avec status
        self.header_pane = pn.pane.HTML(
            self.css_styles + """
            <div class="crypto-header">
                <h2 style="margin: 0; font-size: 28px; font-weight: 700;">
                    🚀 CryptoViz - Données Temps Réel
                </h2>
                <div class="nav-tabs">
                    <div class="nav-tab active">Principaux</div>
                    <div class="nav-tab">Tendances</div>
                    <div class="nav-tab">Les plus visités</div>
                    <div class="nav-tab">Nouveau</div>
                    <div class="nav-tab">En hausse</div>
                    <div class="nav-tab">Actifs Monde Réel</div>
                    <div class="nav-tab">Plus ▾</div>
                </div>
                <div class="network-filters">
                    <span style="color: #8892b0; font-size: 14px;">🔗 Réseaux:</span>
                    <span class="network-badge">🟢 All Networks</span>
                    <span class="network-badge">🔶 BSC</span>
                    <span class="network-badge">🟣 Solana</span>
                    <span class="network-badge">🔵 Base</span>
                    <span class="network-badge">⚫ Ethereum</span>
                </div>
            </div>
            """, 
            height=180
        )
        
        # Indicateur de status
        self.status_pane = pn.pane.HTML(
            '<div class="status-indicator status-updating">🔄 Chargement des données...</div>',
            height=50
        )
        
        # Tableau principal des cryptos (Tabulator avec style moderne)
        self.crypto_table = pn.widgets.Tabulator(
            value=pd.DataFrame(),
            layout='fit_columns',
            height=600,
            theme='midnight',
            stylesheets=["""
            .tabulator {
                background-color: #0f1419 !important;
                border: none !important;
                border-radius: 12px !important;
                overflow: hidden !important;
            }
            .tabulator-header {
                background-color: #1a1a2e !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                border-bottom: 2px solid #333 !important;
            }
            .tabulator-row {
                background-color: #0f1419 !important;
                border-bottom: 1px solid #1e1e1e !important;
            }
            .tabulator-row:hover {
                background-color: #1a1a2e !important;
            }
            .tabulator-cell {
                color: #ffffff !important;
                border-right: 1px solid #1e1e1e !important;
            }
            """],
            pagination='remote',
            page_size=50,
            sizing_mode='stretch_width'
        )
        
        # Graphiques sparkline container
        self.sparklines_container = pn.Row(sizing_mode='stretch_width')
    
    def create_sparkline(self, price_history):
        """Crée un mini-graphique sparkline pour l'historique des prix"""
        if len(price_history) < 2:
            return None
            
        try:
            x = list(range(len(price_history)))
            y = price_history
            
            # Déterminer la couleur (vert si hausse, rouge si baisse)
            color = '#26a69a' if y[-1] > y[0] else '#ef5350'
            
            p = figure(
                width=100, height=40,
                toolbar_location=None,
                x_axis_type=None,
                y_axis_type=None,
                background_fill_color='transparent',
                border_fill_color='transparent'
            )
            
            # Configuration des axes invisibles
            p.grid.visible = False
            p.outline_line_color = None
            p.xaxis.visible = False
            p.yaxis.visible = False
            
            # Ligne sparkline
            p.line(x, y, line_width=2, color=color, alpha=0.8)
            
            # Zone sous la courbe
            p.varea(x, [min(y)] * len(y), y, color=color, alpha=0.1)
            
            return p
            
        except Exception as e:
            logger.error(f"Erreur création sparkline: {e}")
            return None
    
    async def update_data(self):
        """Mise à jour des données crypto depuis le pipeline"""
        try:
            start_time = time.time()
            logger.info("Début mise à jour des données crypto...")
            
            # Lecture des données récentes
            raw_data = self.data_reader.read_recent_data(hours=24)
            
            if raw_data.empty:
                logger.warning("Aucune donnée récupérée")
                self.status_pane.object = '<div class="status-indicator status-updating">❌ Aucune donnée disponible</div>'
                return
            
            # Traitement et formatage des données pour le tableau
            self.current_data = self.format_crypto_data(raw_data)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Données mises à jour: {len(self.current_data)} cryptos en {processing_time:.2f}s")
            
            self.status_pane.object = f'''
            <div class="status-indicator status-online">
                ✅ Mis à jour: {datetime.now().strftime('%H:%M:%S')} 
                ({len(self.current_data)} cryptos)
            </div>
            '''
            
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour données: {e}")
            self.status_pane.object = f'<div class="status-indicator status-updating">❌ Erreur: {str(e)[:50]}...</div>'
    
    def format_crypto_data(self, raw_data):
        """Formate les données crypto pour l'affichage dans le tableau"""
        try:
            # Grouper par symbole et prendre les données les plus récentes
            latest_data = raw_data.sort_values('timestamp').groupby('symbol').tail(1).reset_index(drop=True)
            
            # Calculer les variations (simulation pour l'exemple)
            latest_data['change_1h'] = np.random.uniform(-5, 5, len(latest_data))
            latest_data['change_24h'] = np.random.uniform(-15, 15, len(latest_data))
            latest_data['change_7d'] = np.random.uniform(-30, 30, len(latest_data))
            
            # Formater les données pour le tableau
            formatted_data = []
            
            for idx, row in latest_data.iterrows():
                # Formatage des valeurs monétaires
                price = f"${row['price']:,.2f}" if row['price'] < 1 else f"${row['price']:,.0f}"
                market_cap = self.format_large_number(row.get('market_cap', row['price'] * 1000000))
                volume = self.format_large_number(row.get('volume_24h', row['price'] * 50000))
                
                # Formatage des pourcentages avec couleurs
                change_1h = f"{row['change_1h']:+.2f}%"
                change_24h = f"{row['change_24h']:+.2f}%"
                change_7d = f"{row['change_7d']:+.2f}%"
                
                formatted_data.append({
                    '#': idx + 1,
                    'Nom': f"🪙 {row['name']} ({row['symbol'].upper()})",
                    'Prix': price,
                    '1h %': change_1h,
                    '24h %': change_24h,
                    '7j %': change_7d,
                    'Cap. Boursière': market_cap,
                    'Volume (24h)': volume,
                    'Offre en Circulation': f"{self.format_large_number(row.get('circulating_supply', 21000000))} {row['symbol'].upper()}",
                    '7 Derniers Jours': '📊'  # Placeholder pour sparkline
                })
            
            return pd.DataFrame(formatted_data)
            
        except Exception as e:
            logger.error(f"Erreur formatage données: {e}")
            return pd.DataFrame()
    
    def format_large_number(self, num):
        """Formate les grands nombres avec suffixes (K, M, B, T)"""
        try:
            num = float(num)
            if num >= 1e12:
                return f"€{num/1e12:.2f}T"
            elif num >= 1e9:
                return f"€{num/1e9:.2f}B"
            elif num >= 1e6:
                return f"€{num/1e6:.2f}M"
            elif num >= 1e3:
                return f"€{num/1e3:.2f}K"
            else:
                return f"€{num:.2f}"
        except:
            return "€0.00"
    
    def update_table(self):
        """Met à jour le tableau principal avec les nouvelles données"""
        try:
            if not self.current_data.empty:
                # Configuration des colonnes avec style conditionnel
                formatters = {
                    '1h %': {'type': 'progress', 'max': 100},
                    '24h %': {'type': 'progress', 'max': 100},
                    '7j %': {'type': 'progress', 'max': 100}
                }
                
                # Mise à jour du tableau
                self.crypto_table.value = self.current_data
                
                logger.info(f"Tableau mis à jour avec {len(self.current_data)} entrées")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour tableau: {e}")
    
    async def refresh_dashboard(self):
        """Cycle complet de rafraîchissement du dashboard"""
        await self.update_data()
        self.update_table()
    
    def create_dashboard_layout(self):
        """Crée le layout complet du dashboard moderne"""
        
        # Layout principal
        main_layout = pn.Column(
            self.header_pane,
            pn.Row(
                self.status_pane,
                pn.Spacer(),
                pn.pane.HTML(
                    '<div style="color: #8892b0; font-size: 13px; align-self: center;">🔄 Cap. Boursière: €€€ ▾  📊 Volume (24h): €€€€€ 🔺 Filtres 🗂️ Colonnes</div>',
                    height=50
                ),
                sizing_mode='stretch_width'
            ),
            self.crypto_table,
            pn.pane.HTML(
                '<div style="text-align: center; padding: 20px; color: #8892b0; font-size: 12px;">Données mises à jour en temps réel - CryptoViz V3.0</div>',
                height=60
            ),
            sizing_mode='stretch_width',
            margin=(20, 20)
        )
        
        return main_layout
    
    def setup_periodic_update(self, template):
        """Configuration des mises à jour périodiques"""
        
        async def periodic_refresh():
            while True:
                try:
                    await self.refresh_dashboard()
                    await asyncio.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Erreur refresh périodique: {e}")
                    await asyncio.sleep(5)
        
        # Lancer la tâche de mise à jour
        pn.state.add_periodic_callback(periodic_refresh, period=self.update_interval * 1000)
        
        return template

def create_modern_dashboard():
    """Factory pour créer le dashboard moderne"""
    dashboard = ModernCryptoDashboard()
    
    # Chargement initial des données
    pn.state.add_periodic_callback(dashboard.refresh_dashboard, period=1000, count=1)
    
    # Création du layout
    template = dashboard.create_dashboard_layout()
    
    # Configuration des mises à jour périodiques
    template = dashboard.setup_periodic_update(template)
    
    logger.info("Modern Crypto Dashboard prêt à servir")
    return template

# Point d'entrée pour Panel serve
def main():
    return create_modern_dashboard()

if __name__ == "__main__":
    # Pour développement local
    dashboard = create_modern_dashboard()
    dashboard.show(port=5007, threaded=True)
else:
    # Pour Panel serve
    pn.serve(main, port=5007, allow_websocket_origin=["*"], threaded=True, show=False)
