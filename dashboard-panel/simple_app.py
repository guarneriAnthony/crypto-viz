#!/usr/bin/env python3
"""
Dashboard Simple qui FONCTIONNE - sans threading complexe
"""

import panel as pn
import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
import sys
import os
from datetime import datetime

# Configuration Panel simple
pn.extension('bokeh', template='bootstrap')

# Import reader
sys.path.append('/app')
from utils.parquet_reader_partitioned import get_partitioned_reader

def create_simple_dashboard():
    """Dashboard simple qui affiche les données"""
    
    # Lecture des données
    try:
        reader = get_partitioned_reader()
        df = reader.read_all_data()
        
        if df.empty:
            return pn.pane.HTML("<h2>Aucune donnée disponible</h2>")
        
        # Statistiques
        stats = reader.get_summary_stats()
        
        # Header
        header = pn.pane.HTML(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 20px; border-radius: 10px; text-align: center; margin: 10px;">
            <h1>CryptoViz Dashboard</h1>
            <p>{len(df)} enregistrements | {len(df['symbol'].unique()) if 'symbol' in df.columns else 0} cryptos</p>
            <p>Dernière mise à jour: {datetime.now().strftime('%H:%M:%S')}</p>
        </div>
        """)
        
        # Métriques
        metrics_html = f"""
        <div style="display: flex; gap: 20px; margin: 20px;">
            <div style="background: #28a745; color: white; padding: 15px; border-radius: 8px; text-align: center; flex: 1;">
                <h3>{stats.get('total_files', 0)}</h3>
                <p>Fichiers Parquet</p>
            </div>
            <div style="background: #007bff; color: white; padding: 15px; border-radius: 8px; text-align: center; flex: 1;">
                <h3>{stats.get('total_records', 0)}</h3>
                <p>Enregistrements</p>
            </div>
            <div style="background: #ffc107; color: black; padding: 15px; border-radius: 8px; text-align: center; flex: 1;">
                <h3>{stats.get('cryptos_count', 0)}</h3>
                <p>Cryptomonnaies</p>
            </div>
        </div>
        """
        
        # Graphique des prix
        if 'symbol' in df.columns and 'price' in df.columns:
            # Derniers prix par crypto
            latest_prices = df.groupby('symbol')['price'].last().sort_values(ascending=False)
            
            p = figure(
                title="Prix des Cryptomonnaies (USD)",
                x_range=list(latest_prices.index),
                height=400,
                sizing_mode='stretch_width'
            )
            
            p.vbar(x=list(latest_prices.index), top=list(latest_prices.values), 
                   width=0.8, color='navy', alpha=0.8)
            
            p.xaxis.major_label_orientation = 45
            p.yaxis.formatter.use_scientific = False
            
            chart_pane = pn.pane.Bokeh(p)
        else:
            chart_pane = pn.pane.HTML("<p>Graphique non disponible</p>")
        
        # Tableau des données récentes
        if len(df) > 0:
            recent_df = df.tail(50)
            if 'timestamp' in recent_df.columns:
                recent_df = recent_df[['symbol', 'price', 'change_24h', 'volume_24h', 'timestamp']].copy()
                recent_df['timestamp'] = recent_df['timestamp'].dt.strftime('%H:%M:%S')
            else:
                recent_df = recent_df[['symbol', 'price', 'change_24h', 'volume_24h']].copy()
            
            table = pn.widgets.Tabulator(recent_df, pagination='remote', page_size=10)
        else:
            table = pn.pane.HTML("<p>Pas de données pour le tableau</p>")
        
        # Layout final
        dashboard = pn.Column(
            header,
            pn.pane.HTML(metrics_html),
            chart_pane,
            pn.pane.HTML("<h3>Données récentes:</h3>"),
            table,
            sizing_mode='stretch_width'
        )
        
        return dashboard
        
    except Exception as e:
        error_html = f"""
        <div style="background: #f8d7da; color: #721c24; padding: 20px; border-radius: 8px; margin: 20px;">
            <h3>Erreur Dashboard</h3>
            <p>{str(e)}</p>
        </div>
        """
        return pn.pane.HTML(error_html)

# Application principale
def main():
    return create_simple_dashboard()

if __name__ == "__main__":
    # Servir sur port 5006
    pn.serve(main, port=5006, address="0.0.0.0", 
             allow_websocket_origin=["*"], show=False, threaded=False)
