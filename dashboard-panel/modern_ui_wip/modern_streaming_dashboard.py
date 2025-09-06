#!/usr/bin/env python3
"""
CryptoViz V3.0 - Modern Streaming Dashboard
Dashboard moderne avec streaming temps réel optimisé et sparklines
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
import json
from concurrent.futures import ThreadPoolExecutor

# Configuration Panel avec thème sombre moderne
pn.extension('bokeh', 'tabulator', template='material', sizing_mode='stretch_width')
pn.config.throttled = True

# Ajout du chemin des modules
sys.path.append('/app')

# Imports des utils et composants
from utils.parquet_reader_partitioned import get_partitioned_reader
from components.sparklines import SparklineGenerator, generate_sample_price_history

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModernStreamingDashboard:
    """Dashboard moderne avec streaming temps réel optimisé"""
    
    def __init__(self):
        logger.info("Initialisation Modern Streaming Dashboard")
        
        # Composants de données
        self.data_reader = get_partitioned_reader()
        self.sparkline_gen = SparklineGenerator(width=100, height=40)
        
        # État de l'application
        self.current_data = pd.DataFrame()
        self.historical_data = {}  # Cache pour historiques par crypto
        self.last_update = datetime.now()
        self.update_interval = 15  # secondes (plus fréquent)
        self.streaming_active = True
        
        # Executor pour les tâches async
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Configuration du style CSS moderne
        self.setup_modern_styling()
        
        # Interface réactive
        self.setup_reactive_interface()
        
        logger.info("Modern Streaming Dashboard initialisé avec succès")
    
    def setup_modern_styling(self):
        """Configuration du style CSS moderne et sombre"""
        
        self.css_styles = """
        <style>
        * {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }
        
        .crypto-header {
            background: linear-gradient(135deg, #0f1419 0%, #1a1a2e 50%, #16213e 100%);
            color: #ffffff;
            padding: 20px 25px;
            border-radius: 15px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .nav-tabs {
            display: flex;
            gap: 30px;
            margin: 20px 0;
            border-bottom: 2px solid #333;
            padding-bottom: 15px;
        }
        
        .nav-tab {
            color: #8892b0;
            font-weight: 500;
            cursor: pointer;
            padding: 10px 15px;
            border-radius: 8px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 14px;
        }
        
        .nav-tab.active {
            color: #64ffda;
            background: linear-gradient(135deg, rgba(100, 255, 218, 0.15), rgba(100, 255, 218, 0.05));
            border: 1px solid rgba(100, 255, 218, 0.3);
            box-shadow: 0 4px 12px rgba(100, 255, 218, 0.2);
        }
        
        .nav-tab:hover:not(.active) {
            color: #ffffff;
            background-color: rgba(255, 255, 255, 0.08);
            transform: translateY(-1px);
        }
        
        .network-filters {
            display: flex;
            gap: 12px;
            align-items: center;
            margin: 15px 0;
            flex-wrap: wrap;
        }
        
        .network-badge {
            background: linear-gradient(135deg, #1e1e1e, #2a2a2a);
            color: #ffffff;
            padding: 8px 14px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 500;
            border: 1px solid #404040;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .network-badge:hover {
            border-color: #64ffda;
            box-shadow: 0 0 10px rgba(100, 255, 218, 0.3);
        }
        
        .status-indicator {
            padding: 10px 18px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-online {
            background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.1));
            color: #4caf50;
            border: 1px solid #4caf50;
            animation: pulse-green 2s infinite;
        }
        
        .status-updating {
            background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
            color: #ffc107;
            border: 1px solid #ffc107;
            animation: pulse-yellow 1.5s infinite;
        }
        
        .status-error {
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.2), rgba(244, 67, 54, 0.1));
            color: #f44336;
            border: 1px solid #f44336;
        }
        
        @keyframes pulse-green {
            0%, 100% { box-shadow: 0 0 10px rgba(76, 175, 80, 0.3); }
            50% { box-shadow: 0 0 20px rgba(76, 175, 80, 0.6); }
        }
        
        @keyframes pulse-yellow {
            0%, 100% { box-shadow: 0 0 10px rgba(255, 193, 7, 0.3); }
            50% { box-shadow: 0 0 20px rgba(255, 193, 7, 0.6); }
        }
        
        .crypto-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px 0;
            border-bottom: 1px solid #333;
            margin-bottom: 20px;
        }
        
        .controls-left {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .controls-right {
            display: flex;
            gap: 10px;
            align-items: center;
            color: #8892b0;
            font-size: 13px;
        }
        
        .streaming-indicator {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: rgba(100, 255, 218, 0.1);
            border-radius: 20px;
            color: #64ffda;
            font-size: 11px;
            font-weight: 600;
        }
        
        .streaming-dot {
            width: 8px;
            height: 8px;
            background: #64ffda;
            border-radius: 50%;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 50% { opacity: 1; }
            51%, 100% { opacity: 0.3; }
        }
        
        .footer-info {
            text-align: center;
            padding: 25px;
            color: #8892b0;
            font-size: 12px;
            border-top: 1px solid #333;
            margin-top: 30px;
            background: linear-gradient(135deg, #0f1419, #1a1a1a);
        }
        </style>
        """
    
    def setup_reactive_interface(self):
        """Configuration de l'interface réactive moderne"""
        
        # Header avec navigation
        self.header_pane = pn.pane.HTML(
            self.css_styles + """
            <div class="crypto-header">
                <h2 style="margin: 0 0 10px 0; font-size: 32px; font-weight: 700; background: linear-gradient(45deg, #64ffda, #ffffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                    🚀 CryptoViz Live Dashboard
                </h2>
                <p style="margin: 0 0 15px 0; color: #8892b0; font-size: 14px;">Données crypto en temps réel avec analyse technique</p>
                
                <div class="nav-tabs">
                    <div class="nav-tab active">📊 Principaux</div>
                    <div class="nav-tab">📈 Tendances</div>
                    <div class="nav-tab">👁️ Les plus visités</div>
                    <div class="nav-tab">🆕 Nouveau</div>
                    <div class="nav-tab">🚀 En hausse</div>
                    <div class="nav-tab">🏛️ Actifs Monde Réel</div>
                    <div class="nav-tab">⚙️ Plus ▾</div>
                </div>
                
                <div class="network-filters">
                    <span style="color: #8892b0; font-size: 14px; font-weight: 600;">🔗 Réseaux:</span>
                    <span class="network-badge">🌐 All Networks</span>
                    <span class="network-badge">🔶 BSC</span>
                    <span class="network-badge">🟣 Solana</span>
                    <span class="network-badge">🔵 Base</span>
                    <span class="network-badge">⚫ Ethereum</span>
                    <span class="network-badge">➕ Plus</span>
                </div>
            </div>
            """, 
            height=220
        )
        
        # Zone de contrôles avec indicateur streaming
        self.controls_pane = pn.pane.HTML(
            """
            <div class="crypto-controls">
                <div class="controls-left">
                    <div class="streaming-indicator">
                        <div class="streaming-dot"></div>
                        LIVE STREAMING
                    </div>
                </div>
                <div class="controls-right">
                    <span>🔄 Cap. Boursière: €2.45T ▾</span>
                    <span>📊 Volume (24h): €89.2B</span>
                    <span>🔺 Filtres</span>
                    <span>🗂️ Colonnes</span>
                </div>
            </div>
            """,
            height=60
        )
        
        # Indicateur de status
        self.status_pane = pn.pane.HTML(
            '<div class="status-indicator status-updating">🔄 Initialisation du streaming...</div>',
            height=50
        )
        
        # Configuration avancée du tableau avec style moderne
        self.crypto_table = pn.widgets.Tabulator(
            value=pd.DataFrame(),
            layout='fit_columns',
            height=700,
            theme='midnight',
            stylesheets=["""
            .tabulator {
                background-color: #0f1419 !important;
                border: none !important;
                border-radius: 15px !important;
                overflow: hidden !important;
                box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
            }
            .tabulator-header {
                background: linear-gradient(135deg, #1a1a2e, #16213e) !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                border-bottom: 2px solid #64ffda !important;
                font-size: 13px !important;
            }
            .tabulator-row {
                background-color: #0f1419 !important;
                border-bottom: 1px solid rgba(255,255,255,0.05) !important;
                transition: all 0.2s ease !important;
            }
            .tabulator-row:hover {
                background: linear-gradient(135deg, #1a1a2e, #0f1419) !important;
                transform: translateY(-1px) !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            }
            .tabulator-cell {
                color: #ffffff !important;
                border-right: 1px solid rgba(255,255,255,0.08) !important;
                padding: 12px 10px !important;
                font-size: 13px !important;
            }
            .positive-change {
                color: #26a69a !important;
                font-weight: 600 !important;
            }
            .negative-change {
                color: #ef5350 !important;
                font-weight: 600 !important;
            }
            """],
            pagination='local',
            page_size=50,
            sizing_mode='stretch_width',
            text_align={'#': 'center', 'Prix': 'right', '1h %': 'center', '24h %': 'center', '7j %': 'center'}
        )
        
        # Footer informatif
        self.footer_pane = pn.pane.HTML(
            """
            <div class="footer-info">
                <p><strong>CryptoViz V3.0</strong> - Pipeline de données crypto temps réel</p>
                <p>Powered by Apache Spark • MinIO Lakehouse • Panel/Bokeh • Streaming mis à jour toutes les 15 secondes</p>
            </div>
            """,
            height=100
        )
    
    async def fetch_historical_data(self, symbol, days=7):
        """Récupère l'historique des prix pour un symbole donné"""
        try:
            # Lecture des données historiques depuis le data reader
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            historical = self.data_reader.read_data_range(
                start_date=start_date,
                end_date=end_date,
                symbols=[symbol]
            )
            
            if not historical.empty:
                # Extraire les prix et créer une série temporelle
                prices = historical.sort_values('timestamp')['price'].tolist()
                return prices
            else:
                # Données de simulation si pas d'historique
                current_price = self.get_current_price(symbol)
                return generate_sample_price_history(current_price, days, 0.05)
                
        except Exception as e:
            logger.error(f"Erreur récupération historique pour {symbol}: {e}")
            # Fallback avec données simulées
            return generate_sample_price_history(50000, days, 0.05)
    
    def get_current_price(self, symbol):
        """Récupère le prix actuel d'un symbole"""
        try:
            current_row = self.current_data[self.current_data['symbol'].str.upper() == symbol.upper()]
            if not current_row.empty:
                return current_row.iloc[0]['price']
            else:
                return 50000  # Prix par défaut
        except:
            return 50000
    
    async def update_data_streaming(self):
        """Mise à jour streaming optimisée des données"""
        try:
            start_time = time.time()
            logger.info("🔄 Streaming - Mise à jour des données crypto...")
            
            # Lecture des données les plus récentes
            raw_data = await asyncio.get_event_loop().run_in_executor(
                self.executor, 
                self.data_reader.read_recent_data, 
                2  # Dernières 2 heures pour optimiser
            )
            
            if raw_data.empty:
                logger.warning("❌ Streaming - Aucune donnée récupérée")
                self.status_pane.object = '<div class="status-indicator status-error">❌ Aucune donnée disponible</div>'
                return False
            
            # Traitement et formatage des données
            formatted_data = await self.format_crypto_data_streaming(raw_data)
            
            if formatted_data.empty:
                return False
            
            self.current_data = formatted_data
            processing_time = time.time() - start_time
            
            logger.info(f"✅ Streaming - {len(formatted_data)} cryptos mis à jour en {processing_time:.2f}s")
            
            self.status_pane.object = f'''
            <div class="status-indicator status-online">
                ✅ Live: {datetime.now().strftime('%H:%M:%S')} 
                ({len(formatted_data)} cryptos • {processing_time:.1f}s)
            </div>
            '''
            
            self.last_update = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur streaming: {e}")
            self.status_pane.object = f'<div class="status-indicator status-error">❌ Erreur: {str(e)[:40]}...</div>'
            return False
    
    async def format_crypto_data_streaming(self, raw_data):
        """Formatage streaming optimisé des données crypto"""
        try:
            # Grouper par symbole et prendre les données les plus récentes
            latest_data = raw_data.sort_values('timestamp').groupby('symbol').tail(1).reset_index(drop=True)
            
            # Générer des variations réalistes (simulation améliorée)
            latest_data['change_1h'] = np.random.normal(0, 2, len(latest_data))
            latest_data['change_24h'] = np.random.normal(0, 8, len(latest_data))
            latest_data['change_7d'] = np.random.normal(0, 25, len(latest_data))
            
            # Formater les données pour le tableau avec sparklines
            formatted_data = []
            
            for idx, row in latest_data.iterrows():
                try:
                    # Formatage des valeurs monétaires
                    price = f"${row['price']:,.2f}" if row['price'] < 1000 else f"${row['price']:,.0f}"
                    market_cap = self.format_large_number(row.get('market_cap', row['price'] * 1000000))
                    volume = self.format_large_number(row.get('volume_24h', row['price'] * 50000))
                    
                    # Formatage des pourcentages avec couleurs
                    change_1h_val = row['change_1h']
                    change_24h_val = row['change_24h']
                    change_7d_val = row['change_7d']
                    
                    change_1h = f"{change_1h_val:+.2f}%"
                    change_24h = f"{change_24h_val:+.2f}%"
                    change_7d = f"{change_7d_val:+.2f}%"
                    
                    # Récupération de l'historique pour sparkline (en arrière-plan)
                    price_history = await self.fetch_historical_data(row['symbol'])
                    
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
                        '7 Derniers Jours': self.create_sparkline_html(price_history, change_7d_val),
                        # Colonnes cachées pour le tri/filtrage
                        '_change_1h_val': change_1h_val,
                        '_change_24h_val': change_24h_val,
                        '_change_7d_val': change_7d_val,
                        '_price_val': row['price']
                    })
                    
                except Exception as e:
                    logger.error(f"Erreur formatage ligne {idx}: {e}")
                    continue
            
            return pd.DataFrame(formatted_data)
            
        except Exception as e:
            logger.error(f"Erreur formatage données streaming: {e}")
            return pd.DataFrame()
    
    def create_sparkline_html(self, price_history, change_7d):
        """Crée une représentation HTML du sparkline pour le tableau"""
        try:
            if not price_history or len(price_history) < 2:
                return "📊 ─"
            
            # Couleur basée sur la tendance
            color = "#26a69a" if change_7d >= 0 else "#ef5350"
            direction = "↗️" if change_7d >= 0 else "↘️"
            
            # Simple représentation textuelle du trend
            trend_chars = self.create_ascii_sparkline(price_history)
            
            return f'<span style="color: {color}; font-family: monospace; font-size: 12px;">{direction} {trend_chars}</span>'
            
        except:
            return "📊 ─"
    
    def create_ascii_sparkline(self, values, length=8):
        """Crée un sparkline ASCII simple"""
        if len(values) < 2:
            return "────────"
        
        # Normaliser les valeurs
        min_val, max_val = min(values), max(values)
        if max_val == min_val:
            return "────────"
        
        # Créer les caractères de tendance
        chars = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
        
        # Échantillonner les valeurs pour obtenir la longueur désirée
        if len(values) > length:
            step = len(values) / length
            sampled = [values[int(i * step)] for i in range(length)]
        else:
            sampled = values
        
        # Convertir en caractères ASCII
        sparkline = ""
        for val in sampled:
            normalized = (val - min_val) / (max_val - min_val)
            char_idx = min(int(normalized * len(chars)), len(chars) - 1)
            sparkline += chars[char_idx]
        
        return sparkline[:length].ljust(length, "─")
    
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
    
    def update_table_streaming(self):
        """Met à jour le tableau avec formatage conditionnel"""
        try:
            if not self.current_data.empty:
                # Mise à jour du tableau
                self.crypto_table.value = self.current_data
                
                logger.info(f"📊 Tableau streaming mis à jour avec {len(self.current_data)} entrées")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour tableau streaming: {e}")
    
    async def refresh_dashboard_streaming(self):
        """Cycle complet de rafraîchissement streaming"""
        if self.streaming_active:
            success = await self.update_data_streaming()
            if success:
                self.update_table_streaming()
    
    def create_dashboard_layout(self):
        """Crée le layout complet du dashboard moderne"""
        
        # Layout principal avec espacement optimisé
        main_layout = pn.Column(
            self.header_pane,
            self.controls_pane,
            pn.Row(
                self.status_pane,
                pn.Spacer(),
                sizing_mode='stretch_width',
                margin=(0, 0, 15, 0)
            ),
            self.crypto_table,
            self.footer_pane,
            sizing_mode='stretch_width',
            margin=(25, 25),
            background='#0a0a0a'
        )
        
        return main_layout
    
    def setup_streaming_updates(self, template):
        """Configuration du streaming temps réel avec gestion d'erreurs"""
        
        async def streaming_loop():
            """Boucle principale de streaming avec reconnexion automatique"""
            while self.streaming_active:
                try:
                    await self.refresh_dashboard_streaming()
                    await asyncio.sleep(self.update_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Erreur boucle streaming: {e}")
                    self.status_pane.object = f'<div class="status-indicator status-error">❌ Reconnexion... {str(e)[:30]}</div>'
                    await asyncio.sleep(5)  # Pause avant reconnexion
        
        # Démarrer la boucle de streaming
        pn.state.add_periodic_callback(streaming_loop, period=self.update_interval * 1000)
        
        return template
    
    def stop_streaming(self):
        """Arrête le streaming (pour nettoyage)"""
        self.streaming_active = False
        logger.info("🛑 Streaming arrêté")

def create_modern_streaming_dashboard():
    """Factory pour créer le dashboard streaming moderne"""
    dashboard = ModernStreamingDashboard()
    
    # Chargement initial des données
    pn.state.add_periodic_callback(dashboard.refresh_dashboard_streaming, period=1000, count=1)
    
    # Création du layout
    template = dashboard.create_dashboard_layout()
    
    # Configuration du streaming temps réel
    template = dashboard.setup_streaming_updates(template)
    
    logger.info("🚀 Modern Streaming Dashboard prêt à servir")
    return template

# Point d'entrée pour Panel serve
def main():
    return create_modern_streaming_dashboard()

if __name__ == "__main__":
    # Pour développement local
    dashboard = create_modern_streaming_dashboard()
    dashboard.show(port=5008, threaded=True)
else:
    # Pour Panel serve
    pass  # Panel serve utilisera la fonction main() directement
