#!/usr/bin/env python3
"""
CryptoViz V3.0 - Dashboard Panel/Bokeh avec WebSocket temps réel
Application principale avec interface moderne et données partitionnées
"""

import panel as pn
import pandas as pd
import asyncio
import logging
from datetime import datetime, timedelta
import os
import sys
import time

# Configuration Panel
pn.extension('bokeh', 'tabulator', template='material')
pn.config.throttled = True

# Ajout du chemin des modules
sys.path.append('/app')

# Imports des composants
from utils.parquet_reader_partitioned import get_partitioned_reader
from components.charts import create_crypto_charts
from components.metrics import create_crypto_metrics, create_performance_monitor
from components.layout import create_responsive_layout, create_theme_manager

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CryptoVizDashboard:
    """Dashboard principal CryptoViz avec Panel/Bokeh"""
    
    def __init__(self):
        logger.info("Initialisation CryptoViz Dashboard Panel/Bokeh")
        
        # Composants
        self.data_reader = get_partitioned_reader()
        self.charts = create_crypto_charts()
        self.metrics = create_crypto_metrics()
        self.performance = create_performance_monitor()
        self.layout_manager = create_responsive_layout()
        self.theme_manager = create_theme_manager()
        
        # État de l'application
        self.current_data = pd.DataFrame()
        self.last_update = datetime.now()
        self.update_interval = 30  # secondes
        
        # Interface réactive
        self.setup_reactive_interface()
        
        logger.info("Dashboard initialisé avec succès")
    
    def setup_reactive_interface(self):
        """Configuration de l'interface réactive"""
        
        # Indicateurs de status
        self.status_pane = pn.pane.HTML("🔄 Chargement...", height=50)
        
        # Conteneurs pour les graphiques
        self.price_chart_pane = pn.pane.Bokeh(height=400, sizing_mode='stretch_width')
        self.volume_chart_pane = pn.pane.Bokeh(height=300, sizing_mode='stretch_width')
        self.heatmap_pane = pn.pane.Bokeh(height=200, sizing_mode='stretch_width')
        self.pie_chart_pane = pn.pane.Bokeh(height=350, sizing_mode='stretch_width')
        
        # Métriques réactives
        self.metrics_row = pn.Row(sizing_mode='stretch_width')
        self.data_summary_pane = pn.Column(sizing_mode='stretch_width')
        
        # Performance monitoring
        self.performance_pane = pn.pane.Bokeh(height=200, sizing_mode='stretch_width')
    
    async def update_data(self):
        """Mise à jour asynchrone des données"""
        try:
            start_time = time.time()
            logger.info("Début mise à jour des données...")
            
            # Lecture des données récentes
            self.current_data = self.data_reader.read_recent_data(hours=24)
            
            # Statistiques
            stats = self.data_reader.get_summary_stats()
            
            processing_time = time.time() - start_time
            
            if not self.current_data.empty:
                logger.info(f"Données mises à jour: {len(self.current_data)} enregistrements, "
                          f"{len(self.current_data['symbol'].unique())} cryptos")
                
                # Mettre à jour les métriques
                self.metrics.update_metrics(self.current_data, stats)
                
                # Log performance
                self.performance.log_metrics(len(self.current_data), processing_time)
                
                self.status_pane.object = f"🟢 Mis à jour: {datetime.now().strftime('%H:%M:%S')}"
            else:
                logger.warning("Aucune donnée récupérée")
                self.status_pane.object = "🔴 Aucune donnée disponible"
            
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Erreur mise à jour données: {e}")
            self.status_pane.object = f"❌ Erreur: {str(e)[:50]}..."
    
    def update_charts(self):
        """Mise à jour de tous les graphiques"""
        try:
            if self.current_data.empty:
                return
            
            # Graphique des prix
            price_fig = self.charts.create_price_chart(self.current_data)
            self.price_chart_pane.object = price_fig
            
            # Graphique des volumes
            volume_fig = self.charts.create_volume_chart(self.current_data)
            self.volume_chart_pane.object = volume_fig
            
            # Heatmap des variations
            heatmap_fig = self.charts.create_change_heatmap(self.current_data)
            self.heatmap_pane.object = heatmap_fig
            
            # Graphique camembert
            pie_fig = self.charts.create_market_cap_pie(self.current_data)
            self.pie_chart_pane.object = pie_fig
            
            logger.info("Graphiques mis à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour graphiques: {e}")
    
    def update_metrics_ui(self):
        """Mise à jour de l'interface des métriques"""
        try:
            # Cartes de métriques
            self.metrics_row.clear()
            metrics_cards = self.metrics.create_metrics_cards()
            self.metrics_row.extend(metrics_cards)
            
            # Résumé des données
            stats = self.data_reader.get_summary_stats()
            self.data_summary_pane.clear()
            data_summary = self.metrics.create_data_summary(stats)
            self.data_summary_pane.append(data_summary)
            
            # Performance
            perf_chart = self.performance.get_performance_chart()
            self.performance_pane.object = perf_chart
            
        except Exception as e:
            logger.error(f"Erreur mise à jour métriques UI: {e}")
    
    async def refresh_dashboard(self):
        """Cycle complet de rafraîchissement du dashboard"""
        await self.update_data()
        self.update_charts()
        self.update_metrics_ui()
    
    def create_dashboard_layout(self):
        """Crée le layout complet du dashboard"""
        
        # Sidebar content
        sidebar_content = pn.Column(
            pn.pane.HTML("<h3>📊 Statistiques</h3>"),
            self.data_summary_pane,
            pn.pane.HTML("<h3>⚡ Performance</h3>"),
            self.performance_pane,
            pn.Spacer(height=20),
            self.status_pane,
            sizing_mode='stretch_width'
        )
        
        # Charts column
        charts_column = pn.Column(
            pn.Row(
                pn.Column("## 💰 Prix Temps Réel", self.price_chart_pane),
                sizing_mode='stretch_width'
            ),
            pn.Row(
                pn.Column("## 📊 Volumes 24h", self.volume_chart_pane, width=600),
                pn.Column("## 🥧 Market Cap", self.pie_chart_pane, width=400),
                sizing_mode='stretch_width'
            ),
            pn.Row(
                pn.Column("## 🌡️ Variations", self.heatmap_pane),
                sizing_mode='stretch_width'
            ),
            sizing_mode='stretch_width'
        )
        
        # Layout principal avec template
        template = self.layout_manager.create_simple_layout(
            self.metrics_row, 
            charts_column, 
            sidebar_content
        )
        
        return template
    
    def setup_periodic_update(self, template):
        """Configuration des mises à jour périodiques"""
        
        async def periodic_refresh():
            while True:
                try:
                    await self.refresh_dashboard()
                    await asyncio.sleep(self.update_interval)
                except Exception as e:
                    logger.error(f"Erreur refresh périodique: {e}")
                    await asyncio.sleep(5)  # Attendre 5s en cas d'erreur
        
        # Lancer la tâche de mise à jour
        pn.state.add_periodic_callback(periodic_refresh, period=self.update_interval * 1000)
        
        return template

def create_dashboard():
    """Factory principale pour créer le dashboard"""
    dashboard = CryptoVizDashboard()
    
    # Chargement initial des données
    pn.state.add_periodic_callback(dashboard.refresh_dashboard, period=1000, count=1)
    
    # Création du layout
    template = dashboard.create_dashboard_layout()
    
    # Configuration des mises à jour périodiques
    template = dashboard.setup_periodic_update(template)
    
    logger.info("Dashboard Panel/Bokeh prêt à servir")
    return template

# Point d'entrée pour Panel serve
def main():
    return create_dashboard()

if __name__ == "__main__":
    # Pour développement local
    dashboard = create_dashboard()
    dashboard.show(port=5006, threaded=True)
else:
    # Pour Panel serve
    pn.serve(main, port=5006, allow_websocket_origin=["*"], threaded=True, show=False)
