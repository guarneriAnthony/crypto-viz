#!/usr/bin/env python3
"""
Dashboard moderne simplifié pour test
"""

import panel as pn
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration Panel
pn.extension('tabulator', template='material', sizing_mode='stretch_width')

def create_test_dashboard():
    """Crée un dashboard de test avec données simulées"""
    
    # Style CSS moderne
    css_styles = """
    <style>
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
        transition: all 0.3s ease;
        font-size: 14px;
    }
    
    .nav-tab.active {
        color: #64ffda;
        background: linear-gradient(135deg, rgba(100, 255, 218, 0.15), rgba(100, 255, 218, 0.05));
        border: 1px solid rgba(100, 255, 218, 0.3);
        box-shadow: 0 4px 12px rgba(100, 255, 218, 0.2);
    }
    </style>
    """
    
    # Header
    header = pn.pane.HTML(css_styles + """
    <div class="crypto-header">
        <h2 style="margin: 0 0 10px 0; font-size: 32px; font-weight: 700; background: linear-gradient(45deg, #64ffda, #ffffff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            🚀 CryptoViz Live Dashboard - TEST
        </h2>
        <p style="margin: 0 0 15px 0; color: #8892b0; font-size: 14px;">Interface moderne avec données de test</p>
        
        <div class="nav-tabs">
            <div class="nav-tab active">📊 Principaux</div>
            <div class="nav-tab">📈 Tendances</div>
            <div class="nav-tab">👁️ Les plus visités</div>
            <div class="nav-tab">🆕 Nouveau</div>
        </div>
    </div>
    """, height=200)
    
    # Créer des données de test
    test_data = pd.DataFrame({
        '#': range(1, 11),
        'Nom': [
            '🪙 Bitcoin (BTC)',
            '🪙 Ethereum (ETH)', 
            '🪙 Tether (USDT)',
            '🪙 XRP (XRP)',
            '🪙 Solana (SOL)',
            '🪙 BNB (BNB)',
            '🪙 Dogecoin (DOGE)',
            '🪙 USDC (USDC)',
            '🪙 Cardano (ADA)',
            '🪙 Polygon (MATIC)'
        ],
        'Prix': [
            '$94,115.23',
            '$3,653.63',
            '$0.8536',
            '$2.39',
            '$145.67',
            '$598.12',
            '$0.1234',
            '$1.00',
            '$0.4567',
            '$0.8901'
        ],
        '1h %': [
            '+0.08%',
            '+0.15%',
            '+0.00%',
            '+0.05%',
            '-0.23%',
            '+0.12%',
            '+0.45%',
            '+0.00%',
            '-0.34%',
            '+0.67%'
        ],
        '24h %': [
            '-0.86%',
            '-0.69%',
            '+0.03%',
            '+1.23%',
            '+2.45%',
            '-1.23%',
            '+5.67%',
            '+0.01%',
            '-2.34%',
            '+3.45%'
        ],
        '7j %': [
            '+1.09%',
            '-1.98%',
            '-0.23%',
            '-0.40%',
            '+8.90%',
            '+2.34%',
            '+12.34%',
            '+0.05%',
            '-5.67%',
            '+7.89%'
        ],
        'Cap. Boursière': [
            '€1,874,495,987,522',
            '€441,012,834,281',
            '€144,157,218,770',
            '€142,575,539,390',
            '€65,123,456,789',
            '€89,234,567,890',
            '€17,890,123,456',
            '€32,123,456,789',
            '€15,678,901,234',
            '€8,901,234,567'
        ],
        'Volume (24h)': [
            '€24,043,470,104',
            '€18,001,119,657',
            '€60,986,834,840',
            '€2,538,288,331',
            '€1,234,567,890',
            '€987,654,321',
            '€567,890,123',
            '€1,111,111,111',
            '€444,555,666',
            '€222,333,444'
        ],
        'Offre en Circulation': [
            '19.91M BTC',
            '120.7M ETH',
            '168.87B USDT',
            '59.61B XRP',
            '467.89M SOL',
            '150.12M BNB',
            '146.78B DOGE',
            '24.56B USDC',
            '35.67B ADA',
            '10.12B MATIC'
        ],
        '7 Derniers Jours': [
            '↗️ ▃▅▆▇█▆▅',
            '↘️ █▇▆▅▄▃▂',
            '↘️ ▅▅▅▅▄▄▄',
            '↘️ ▆▅▄▃▄▅▆',
            '↗️ ▂▃▄▅▆▇█',
            '↗️ ▄▅▆▅▄▅▆',
            '↗️ ▂▃▅▇██▇',
            '↗️ ▅▅▅▅▅▅▅',
            '↘️ ▇▆▅▄▃▂▁',
            '↗️ ▃▄▅▆▇▆▅'
        ]
    })
    
    # Status pane
    status = pn.pane.HTML(
        '''<div style="padding: 10px 18px; border-radius: 8px; font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 8px; background: linear-gradient(135deg, rgba(76, 175, 80, 0.2), rgba(76, 175, 80, 0.1)); color: #4caf50; border: 1px solid #4caf50;">
        ✅ Test Mode: ''' + datetime.now().strftime('%H:%M:%S') + ''' (10 cryptos de test)
        </div>''',
        height=50
    )
    
    # Tableau avec style moderne
    table = pn.widgets.Tabulator(
        value=test_data,
        layout='fit_columns',
        height=500,
        theme='midnight',
        stylesheets=["""
        .tabulator {
            background-color: #0f1419 !important;
            border: none !important;
            border-radius: 15px !important;
            overflow: hidden !important;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4) !important;
        }
        .tabulator-header {
            background: linear-gradient(135deg, #1a1a2e, #16213e) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-bottom: 2px solid #64ffda !important;
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
        }
        """],
        pagination='local',
        page_size=20,
        sizing_mode='stretch_width'
    )
    
    # Footer
    footer = pn.pane.HTML("""
    <div style="text-align: center; padding: 25px; color: #8892b0; font-size: 12px; border-top: 1px solid #333; margin-top: 30px; background: linear-gradient(135deg, #0f1419, #1a1a1a);">
        <p><strong>CryptoViz V3.0 - TEST MODE</strong> - Interface moderne fonctionnelle</p>
        <p>🚀 Dashboard moderne style CoinMarketCap • Interface responsive • Données de test</p>
    </div>
    """, height=100)
    
    # Layout final
    layout = pn.Column(
        header,
        pn.Row(status, pn.Spacer(), sizing_mode='stretch_width'),
        table,
        footer,
        sizing_mode='stretch_width',
        margin=(25, 25),
        background='#0a0a0a'
    )
    
    return layout

# Point d'entrée pour Panel serve
def main():
    return create_test_dashboard()

if __name__ == "__main__":
    dashboard = create_test_dashboard()
    dashboard.show(port=5009, threaded=True)
