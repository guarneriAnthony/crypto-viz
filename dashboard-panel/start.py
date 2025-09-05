#!/usr/bin/env python3
"""
Script de lancement Dashboard Panel/Bokeh
Utilise IP machine: 192.168.1.76
"""

import panel as pn
import os
import sys

# Configuration avec IP machine
IP_MACHINE = "192.168.1.76"

# Ajout du chemin des modules
sys.path.append('/app')

# Import de l'application
from app import create_dashboard

if __name__ == "__main__":
    print(f"🚀 Démarrage Dashboard Panel sur {IP_MACHINE}:5006")
    
    # Configuration Panel avec IP machine
    pn.config.global_css = []
    
    # Création du dashboard
    dashboard_app = create_dashboard()
    
    # Servir l'application sur IP machine
    pn.serve(
        dashboard_app, 
        port=5006, 
        address="0.0.0.0",  # Écouter sur toutes interfaces
        allow_websocket_origin=[f"{IP_MACHINE}:5006", "*"],
        show=False,
        autoreload=False,
        threaded=True
    )
