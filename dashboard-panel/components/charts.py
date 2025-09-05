"""
CryptoViz V3.0 - Composants graphiques Bokeh pour Panel
Graphiques interactifs temps réel avec WebSocket
"""

import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, HoverTool, DatetimeTickFormatter
from bokeh.layouts import column, row
from bokeh.palettes import Category20, Spectral6
import panel as pn
from datetime import datetime, timedelta

class CryptoCharts:
    """Gestionnaire des graphiques crypto avec Bokeh"""
    
    def __init__(self):
        self.color_palette = Category20[20]
        self.default_tools = "pan,wheel_zoom,box_zoom,reset,save"
    
    def create_price_chart(self, data: pd.DataFrame, height: int = 400) -> figure:
        """Graphique des prix avec courbes par crypto"""
        p = figure(
            title="Prix des Cryptomonnaies (Temps Réel)",
            x_axis_type='datetime',
            height=height,
            sizing_mode='stretch_width',
            tools=self.default_tools
        )
        
        if data.empty:
            p.text(0.5, 0.5, text=["Aucune donnée disponible"], 
                  text_align="center", text_baseline="middle")
            return p
        
        # Grouper par crypto
        cryptos = data['symbol'].unique()
        
        for i, crypto in enumerate(cryptos):
            crypto_data = data[data['symbol'] == crypto].sort_values('timestamp')
            
            if not crypto_data.empty:
                source = ColumnDataSource(crypto_data)
                color = self.color_palette[i % len(self.color_palette)]
                
                # Ligne principale
                p.line('timestamp', 'price', source=source, 
                      line_color=color, line_width=2, legend_label=crypto)
                
                # Points pour interactivité
                p.circle('timestamp', 'price', source=source,
                        color=color, size=4, alpha=0.6)
        
        # Hover tool
        hover = HoverTool(tooltips=[
            ("Crypto", "@symbol"),
            ("Prix", "@price{$0,0.00}"),
            ("Timestamp", "@timestamp{%F %T}"),
            ("Volume 24h", "@volume_24h{$0,0}")
        ], formatters={'@timestamp': 'datetime'})
        
        p.add_tools(hover)
        
        # Formatage
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.xaxis.formatter = DatetimeTickFormatter(hours="%H:%M", days="%d/%m")
        p.yaxis.formatter.use_scientific = False
        
        return p
    
    def create_volume_chart(self, data: pd.DataFrame, height: int = 300) -> figure:
        """Graphique des volumes 24h"""
        p = figure(
            title="Volumes 24h par Crypto",
            height=height,
            sizing_mode='stretch_width',
            tools=self.default_tools
        )
        
        if data.empty:
            return p
        
        # Prendre les dernières données par crypto
        latest_data = data.groupby('symbol').tail(1).sort_values('volume_24h', ascending=False)
        
        source = ColumnDataSource(latest_data)
        
        # Graphique en barres
        p.vbar(x='symbol', top='volume_24h', source=source, width=0.6,
               color='navy', alpha=0.8)
        
        # Hover
        hover = HoverTool(tooltips=[
            ("Crypto", "@symbol"),
            ("Volume 24h", "@volume_24h{$0,0}"),
            ("Prix actuel", "@price{$0,0.00}")
        ])
        p.add_tools(hover)
        
        p.xgrid.grid_line_color = None
        p.xaxis.major_label_orientation = 45
        
        return p
    
    def create_change_heatmap(self, data: pd.DataFrame, height: int = 200) -> figure:
        """Heatmap des variations de prix"""
        p = figure(
            title="Variations de Prix (%)",
            height=height,
            sizing_mode='stretch_width',
            tools=self.default_tools
        )
        
        if data.empty:
            return p
        
        # Dernières données par crypto
        latest_data = data.groupby('symbol').tail(1)
        
        # Créer des rectangles colorés selon la variation
        from bokeh.transform import linear_cmap
        from bokeh.models import ColorBar
        
        mapper = linear_cmap('change_24h', 'RdYlGn', 
                           low=latest_data['change_24h'].min(), 
                           high=latest_data['change_24h'].max())
        
        source = ColumnDataSource(latest_data.reset_index())
        
        p.rect(x='index', y=0, width=0.8, height=0.8, source=source,
               fill_color=mapper, line_color='white')
        
        # Ajouter les labels
        from bokeh.models import LabelSet
        labels = LabelSet(x='index', y=0, text='symbol', source=source,
                         text_align='center', text_baseline='middle')
        p.add_layout(labels)
        
        # Color bar
        color_bar = ColorBar(color_mapper=mapper['transform'], location=(0,0))
        p.add_layout(color_bar, 'right')
        
        p.xaxis.visible = False
        p.yaxis.visible = False
        p.grid.visible = False
        
        return p
    
    def create_market_cap_pie(self, data: pd.DataFrame, height: int = 350) -> figure:
        """Graphique camembert des market caps"""
        from bokeh.transform import cumsum
        from math import pi
        
        p = figure(
            title="Répartition Market Cap",
            height=height,
            toolbar_location=None,
            tools="hover",
            tooltips="@symbol: @market_cap{$0,0}",
            x_range=(-0.5, 1.0),
            sizing_mode='stretch_width'
        )
        
        if data.empty:
            return p
        
        # Top 10 des market caps
        latest_data = data.groupby('symbol').tail(1).nlargest(10, 'market_cap')
        
        # Calculer les angles
        latest_data['angle'] = latest_data['market_cap'] / latest_data['market_cap'].sum() * 2 * pi
        latest_data['angle'] = latest_data['angle'].cumsum()
        
        # Couleurs
        latest_data['color'] = Category20[len(latest_data)]
        
        source = ColumnDataSource(latest_data)
        
        p.wedge(x=0, y=1, radius=0.4, start_angle=cumsum('angle', include_zero=True), 
                end_angle=cumsum('angle'), color='color', legend_field='symbol',
                source=source)
        
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None
        
        return p

def create_crypto_charts():
    """Factory pour créer les composants graphiques"""
    return CryptoCharts()
