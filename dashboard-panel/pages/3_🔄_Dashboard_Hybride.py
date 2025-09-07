"""
Page Dashboard Hybride - Architecture optimisée pour 7000+ fichiers Parquet
Historique MinIO (filtré intelligemment) + Stream Temps Réel Kafka
"""

import sys
import os

# Redirection vers le dashboard hybride optimisé
sys.path.append('/app')

# Import et exécution du dashboard hybride
exec(open('/app/streamlit_hybrid_dashboard.py').read())
