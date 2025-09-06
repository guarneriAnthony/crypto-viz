#!/usr/bin/env python3
import panel as pn
import pandas as pd
import sys
import os
from datetime import datetime

# Configuration Panel
pn.extension('bokeh')

# Import reader
sys.path.append('/app')

def create_simple_dashboard():
    """Dashboard simple et stable"""
    try:
        from utils.parquet_reader_partitioned import get_partitioned_reader
        reader = get_partitioned_reader()
        df = reader.read_all_data()
        
        # Info sur les données
        if not df.empty:
            data_info = f"""
            📊 **CryptoViz Dashboard Simple**
            - **{len(df)} lignes** de données
            - **{df['symbol'].nunique()} cryptos** différentes  
            - **Dernière mise à jour**: {datetime.now().strftime('%H:%M:%S')}
            """
        else:
            data_info = "❌ Aucune donnée disponible"
        
        # Derniers prix par crypto
        if not df.empty:
            latest_prices = df.groupby('symbol').last()[['price']].round(2)
            price_table = pn.pane.DataFrame(latest_prices, width=400)
        else:
            price_table = pn.pane.HTML("<p>Pas de données prix</p>")
        
        # Layout simple
        dashboard = pn.template.MaterialTemplate(
            title="CryptoViz - Simple Dashboard",
            sidebar=[data_info],
            main=[
                pn.pane.HTML("<h2>💰 Prix Actuels</h2>"),
                price_table
            ]
        )
        
        return dashboard
        
    except Exception as e:
        error_html = f"""
        <div style="padding: 20px; background: #f8d7da; color: #721c24; border-radius: 5px;">
            <h3>❌ Erreur Dashboard</h3>
            <p>Erreur: {str(e)}</p>
        </div>
        """
        return pn.pane.HTML(error_html)

# Servir l'application
if __name__ == "__main__":
    print("🚀 Démarrage Dashboard Simple CryptoViz...")
    
    pn.config.allow_websocket_origin = ["*"]
    app = create_simple_dashboard()
    app.servable()
    
    print("✅ Dashboard simple prêt!")
