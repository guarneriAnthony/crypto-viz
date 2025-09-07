"""
Page Dashboard Principal - Vue d'ensemble des cryptomonnaies
Adapté depuis streamlit_crypto_dashboard.py pour le multipage
"""
# Import du dashboard principal existant
import sys
import os

# Redirection vers le dashboard principal (chemin correct dans le container)
sys.path.append('/app')

# Import des composants du dashboard principal
exec(open('/app/streamlit_crypto_dashboard.py').read())
