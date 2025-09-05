"""
CryptoViz V3.0 - Métriques temps réel Panel
KPIs et indicateurs de performance du pipeline
"""

import pandas as pd
import panel as pn
from datetime import datetime, timedelta
import param

class CryptoMetrics(param.Parameterized):
    """Métriques et KPIs crypto temps réel"""
    
    # Paramètres réactifs
    total_cryptos = param.Integer(default=0)
    total_records = param.Integer(default=0)
    last_update = param.String(default="N/A")
    pipeline_status = param.String(default="Initialisation...")
    
    def __init__(self, **params):
        super().__init__(**params)
        self.setup_layout()
    
    def setup_layout(self):
        """Configuration du layout des métriques"""
        # Styles CSS pour les métriques
        metric_style = """
        <style>
        .metric-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 5px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        .status-green { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
        .status-yellow { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
        .status-red { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); }
        </style>
        """
        
        self.style_pane = pn.pane.HTML(metric_style, height=0)
    
    def update_metrics(self, data: pd.DataFrame, partitions_info: dict):
        """Met à jour toutes les métriques depuis les données"""
        if not data.empty:
            self.total_cryptos = len(data['symbol'].unique())
            self.total_records = len(data)
            
            # Dernière mise à jour
            if 'timestamp' in data.columns:
                latest_timestamp = data['timestamp'].max()
                self.last_update = latest_timestamp.strftime("%H:%M:%S")
                
                # Status pipeline basé sur fraîcheur des données
                time_diff = datetime.now() - latest_timestamp.replace(tzinfo=None)
                if time_diff < timedelta(minutes=5):
                    self.pipeline_status = "🟢 Opérationnel"
                elif time_diff < timedelta(minutes=15):
                    self.pipeline_status = "🟡 Délai léger"
                else:
                    self.pipeline_status = "🔴 Délai important"
            
        else:
            self.total_cryptos = 0
            self.total_records = 0
            self.last_update = "N/A"
            self.pipeline_status = "⚪ Pas de données"
    
    def create_metrics_cards(self) -> pn.Row:
        """Crée les cartes de métriques"""
        
        # Carte cryptos
        crypto_card = pn.pane.HTML(f"""
        <div class="metric-card">
            <div class="metric-value">{self.total_cryptos}</div>
            <div class="metric-label">Cryptomonnaies</div>
        </div>
        """, height=120, sizing_mode='stretch_width')
        
        # Carte records
        records_card = pn.pane.HTML(f"""
        <div class="metric-card">
            <div class="metric-value">{self.total_records:,}</div>
            <div class="metric-label">Enregistrements</div>
        </div>
        """, height=120, sizing_mode='stretch_width')
        
        # Carte dernière mise à jour
        update_card = pn.pane.HTML(f"""
        <div class="metric-card">
            <div class="metric-value">{self.last_update}</div>
            <div class="metric-label">Dernière MAJ</div>
        </div>
        """, height=120, sizing_mode='stretch_width')
        
        # Carte status
        status_class = "status-green" if "🟢" in self.pipeline_status else \
                      "status-yellow" if "🟡" in self.pipeline_status else "status-red"
        
        status_card = pn.pane.HTML(f"""
        <div class="metric-card {status_class}">
            <div class="metric-value" style="font-size: 1.5em;">{self.pipeline_status}</div>
            <div class="metric-label">Pipeline</div>
        </div>
        """, height=120, sizing_mode='stretch_width')
        
        return pn.Row(self.style_pane, crypto_card, records_card, update_card, status_card)
    
    def create_data_summary(self, stats: dict) -> pn.Column:
        """Résumé détaillé des données"""
        if not stats:
            return pn.pane.HTML("<p>Aucune statistique disponible</p>")
        
        summary_html = f"""
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0;">
            <h4>📊 Résumé des Données Partitionnées</h4>
            <ul style="list-style-type: none; padding: 0;">
                <li><strong>Partitions totales:</strong> {stats.get('total_partitions', 0)}</li>
                <li><strong>Fichiers Parquet:</strong> {stats.get('total_files', 0)}</li>
                <li><strong>Période couverte:</strong> {stats.get('date_range', 'N/A')}</li>
                <li><strong>Dernière partition:</strong> {stats.get('latest_partition', 'N/A')}</li>
                <li><strong>Cryptos disponibles:</strong> {len(stats.get('available_cryptos', []))}</li>
            </ul>
        </div>
        """
        
        return pn.pane.HTML(summary_html)

class PerformanceMonitor:
    """Moniteur de performance du pipeline"""
    
    def __init__(self):
        self.metrics_history = []
    
    def log_metrics(self, data_count: int, processing_time: float, timestamp: datetime = None):
        """Enregistre une métrique de performance"""
        if timestamp is None:
            timestamp = datetime.now()
            
        self.metrics_history.append({
            'timestamp': timestamp,
            'data_count': data_count,
            'processing_time': processing_time,
            'throughput': data_count / processing_time if processing_time > 0 else 0
        })
        
        # Garder seulement les 100 dernières métriques
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
    
    def get_performance_chart(self) -> pn.pane.Bokeh:
        """Graphique de performance du pipeline"""
        if not self.metrics_history:
            return pn.pane.HTML("Pas encore de données de performance")
        
        df = pd.DataFrame(self.metrics_history)
        
        from bokeh.plotting import figure
        from bokeh.models import ColumnDataSource
        
        p = figure(title="Performance Pipeline", x_axis_type='datetime', 
                  height=200, sizing_mode='stretch_width')
        
        source = ColumnDataSource(df)
        p.line('timestamp', 'throughput', source=source, line_width=2, color='green')
        p.circle('timestamp', 'throughput', source=source, size=4, color='green')
        
        p.yaxis.axis_label = "Throughput (records/sec)"
        p.xaxis.axis_label = "Temps"
        
        return pn.pane.Bokeh(p)

def create_crypto_metrics():
    """Factory pour créer les métriques crypto"""
    return CryptoMetrics()

def create_performance_monitor():
    """Factory pour créer le moniteur de performance"""
    return PerformanceMonitor()
