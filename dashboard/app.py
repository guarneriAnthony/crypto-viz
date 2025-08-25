"""
Page d'accueil CryptoViz - Point d'entrée de l'application multi-pages
"""
import streamlit as st
import sys
import os

# Ajouter le dossier courant au path pour importer utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.database import get_connection

# Configuration de la page
st.set_page_config(page_title="CryptoViz - Multi-Sources & ML", layout="wide")

st.title("CryptoViz - Dashboard Multi-Sources & ML Predictions")
st.markdown("*Plateforme d'analyse crypto avec prédictions ML temps réel*")

# Vérifier la connexion à la base de données
@st.cache_data(ttl=60)
def get_system_status():
    try:
        conn = get_connection()
        result = conn.execute("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT name) as unique_cryptos,
                COUNT(DISTINCT source) as sources,
                MAX(timestamp) as latest_update
            FROM crypto_prices
        """).fetchone()
        conn.close()
        return result
    except:
        return None

# Affichage du statut du système
st.header("État du Système")

status = get_system_status()
if status:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Records", f"{status[0]:,}")
    
    with col2:
        st.metric("Cryptos", status[1])
    
    with col3:
        st.metric("Sources", status[2])
    
    with col4:
        from datetime import datetime
        if status[3]:
            age_minutes = (datetime.now() - status[3]).total_seconds() / 60
            status_color = "🟢" if age_minutes < 10 else "🟡" if age_minutes < 60 else "🔴"
            st.metric("Dernière MAJ", f"{status_color} {age_minutes:.0f}min")
        else:
            st.metric("Dernière MAJ", "🔴 N/A")
else:
    st.error("🔴 Impossible de se connecter à la base de données")

# Guide des fonctionnalités
st.header("Fonctionnalités Disponibles")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Dashboard Multi-Sources")
    st.markdown("""
    **Analyse temps réel des prix crypto**
    
    **Sources multiples :**
    - CoinMarketCap (API premium)
    - CoinGecko (API gratuite)
    
    **Visualisations :**
    - Graphiques comparatifs
    - Évolutions par source
    - Métriques temps réel
    - Variations relatives
    
    **Filtres avancés :**
    - Par source de données
    - Par période personnalisée
    - Par cryptomonnaie
    """)

with col2:
    st.subheader("ML Predictions")
    st.markdown("""
    **Prédictions de prix basées sur ML**
    
    **Modèles disponibles :**
    - Moyennes mobiles (20 & 50 points)
    - Tendance linéaire
    - Momentum
    
    **Analyses :**
    - Prédictions court terme (1-24h)
    - Consensus des modèles
    - Métriques de confiance
    - Visualisations interactives
    
    **Configuration :**
    - Horizon de prédiction
    - Historique d'analyse
    - Source des données
    """)

# Instructions d'utilisation
st.header("Comment utiliser CryptoViz")

with st.expander("Guide rapide", expanded=False):
    st.markdown("""
    ### 1. Navigation
    - Utilisez la **sidebar gauche** pour naviguer entre les pages
    - **Dashboard** : Analyse des données temps réel
    - **ML Predictions** : Prédictions et analyse ML
    
    ### 2. Dashboard Multi-Sources
    - Sélectionnez les **sources** de données (CoinMarketCap/CoinGecko)
    - Choisissez les **cryptomonnaies** à analyser
    - Configurez la **période** d'analyse
    - Explorez les différents **types de graphiques**
    
    ### 3. ML Predictions
    - Sélectionnez une **cryptomonnaie** à analyser
    - Définissez l'**horizon de prédiction** (1-24h)
    - Configurez l'**historique** à analyser (6-72h)
    - Cliquez sur **"Lancer l'Analyse ML"**
    - Analysez les **résultats** et le **consensus**
    
    ### 4. Bonnes Pratiques
    - Comparez toujours **plusieurs sources**
    - Utilisez différents **horizons temporels**
    - Les prédictions ML sont des **indications**, pas des garanties
    - Toujours faire ses **propres recherches** (DYOR)
    """)

# Avertissements
st.warning("""
**Avertissements Importants :**
- Les données crypto sont très volatiles et imprévisibles
- Les prédictions ML ne garantissent pas les performances futures
- Ne jamais investir plus que ce que vous pouvez vous permettre de perdre
- Toujours diversifier vos sources d'information
- DYOR (Do Your Own Research) !
""")

# Footer technique
st.markdown("---")
st.markdown("""
*Architecture Technique :  
Multi-sources (CoinMarketCap + CoinGecko) • DuckDB Analytics • ML Predictions • Streamlit UI*
""")
