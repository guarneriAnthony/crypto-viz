"""
CryptoViz V3.0 - Layout responsive Panel
Interface moderne adaptive avec WebSocket
"""

import panel as pn
import param
from datetime import datetime, timedelta

class ResponsiveLayout(param.Parameterized):
    """Layout responsive pour dashboard crypto"""
    
    # Paramètres de configuration
    auto_refresh = param.Boolean(default=True)
    refresh_interval = param.Integer(default=30)  # secondes
    selected_timeframe = param.Selector(default="1h", objects=["15m", "1h", "6h", "24h"])
    selected_cryptos = param.ListSelector(default=[], objects=[])
    
    def __init__(self, **params):
        super().__init__(**params)
        self.setup_styles()
    
    def setup_styles(self):
        """Configuration des styles CSS globaux"""
        self.custom_css = """
        <style>
        /* Styles globaux */
        .dashboard-container {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
            padding: 10px;
        }
        
        .header-title {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        
        .header-title h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        
        .header-subtitle {
            font-size: 1.1em;
            opacity: 0.9;
            margin-top: 5px;
        }
        
        .control-panel {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .chart-container {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .sidebar {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header-title h1 { font-size: 1.8em; }
            .dashboard-container { padding: 5px; }
        }
        
        /* Animations */
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """
    
    def create_header(self) -> pn.pane.HTML:
        """Crée l'en-tête du dashboard"""
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        header_html = f"""
        <div class="header-title fade-in">
            <h1>CryptoViz V3.0</h1>
            <div class="header-subtitle">
                Data Lakehouse Pipeline • Temps Réel • {current_time}
            </div>
        </div>
        """
        
        return pn.pane.HTML(header_html, sizing_mode='stretch_width')
    
    def create_control_panel(self) -> pn.Row:
        """Panneau de contrôles"""
        
        # Sélecteur de période
        timeframe_select = pn.widgets.Select(
            name="Période", 
            value=self.selected_timeframe,
            options=["15m", "1h", "6h", "24h"],
            width=120
        )
        
        # Toggle auto-refresh
        auto_refresh_toggle = pn.widgets.Toggle(
            name="Auto-refresh", 
            value=self.auto_refresh,
            width=120
        )
        
        # Intervalle de rafraîchissement
        refresh_slider = pn.widgets.IntSlider(
            name="Intervalle (s)",
            start=10, 
            end=300, 
            step=10,
            value=self.refresh_interval,
            width=200
        )
        
        # Bouton refresh manuel
        refresh_button = pn.widgets.Button(
            name="🔄 Actualiser",
            button_type="primary",
            width=120
        )
        
        # Status indicator
        status_indicator = pn.pane.HTML(
            '<div style="background: #28a745; color: white; padding: 8px 12px; border-radius: 20px; text-align: center;">🟢 En ligne</div>',
            width=100
        )
        
        control_html = """
        <div class="control-panel">
            <h4 style="margin-top: 0;">⚙️ Contrôles</h4>
        </div>
        """
        
        controls_header = pn.pane.HTML(control_html, width=200)
        
        return pn.Row(
            controls_header,
            timeframe_select,
            auto_refresh_toggle, 
            refresh_slider,
            refresh_button,
            status_indicator,
            sizing_mode='stretch_width'
        )
    
    def create_simple_layout(self, metrics_row, charts_column, sidebar_content) -> pn.Column:
        """Layout simple sans MaterialTemplate pour éviter les erreurs"""
        
        # CSS embarqué
        css_pane = pn.pane.HTML(self.custom_css, height=0)
        
        # Layout principal en colonnes
        main_layout = pn.Column(
            css_pane,
            self.create_header(),
            self.create_control_panel(),
            pn.Row(
                pn.Column(
                    metrics_row,
                    charts_column,
                    sizing_mode='stretch_width',
                    width=800
                ),
                pn.Column(
                    sidebar_content,
                    sizing_mode='stretch_width',
                    width=300
                ),
                sizing_mode='stretch_width'
            ),
            sizing_mode='stretch_width'
        )
        
        return main_layout

def create_responsive_layout():
    """Factory pour créer le layout responsive"""
    return ResponsiveLayout()

class ThemeManager:
    """Gestionnaire de thèmes pour le dashboard"""
    
    def __init__(self):
        self.themes = {
            'light': {
                'background': 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
                'card_bg': 'white',
                'text_color': '#333',
                'accent': '#667eea'
            },
            'dark': {
                'background': 'linear-gradient(135deg, #2c3e50 0%, #34495e 100%)',
                'card_bg': '#34495e',
                'text_color': 'white',
                'accent': '#3498db'
            }
        }
        self.current_theme = 'light'

def create_theme_manager():
    """Factory pour créer le gestionnaire de thèmes"""
    return ThemeManager()
