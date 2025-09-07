"""
CryptoViz V3.0 - Page d'Accueil Multi-Pages
Navigation entre Dashboard Principal et ML Predictions
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="CryptoViz V3.0 - Accueil", 
    page_icon="🚀",
    layout="wide"
)

# CSS personnalisé avec contraste amélioré
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 1rem 0;
        color: #333333;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .feature-card h4 {
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .feature-card p {
        color: #666666;
    }
    .feature-card ul {
        color: #555555;
    }
    .feature-card li {
        color: #666666;
        margin-bottom: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# En-tête principal
st.markdown("""
<div class="main-header">
    <h1>🚀 CryptoViz V3.0</h1>
    <h3>Dashboard Multi-Pages avec ML Predictions</h3>
    <p>Analyse temps réel des cryptomonnaies avec prédictions IA</p>
</div>
""", unsafe_allow_html=True)

# Test de connexion Redis ML
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from utils.redis_ml_client import test_ml_connection
    connection_status = test_ml_connection()
except Exception as e:
    connection_status = False

# Statut du système
st.subheader("📊 Statut du Système")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "🔗 Connexion ML", 
        "✅ OK" if connection_status else "❌ Erreur",
        help="Statut de la connexion au système ML Redis"
    )

with col2:
    st.metric(
        "🕐 Dernière MAJ", 
        datetime.now().strftime("%H:%M:%S"),
        help="Dernière vérification du statut"
    )

with col3:
    st.metric(
        "🏗️ Version", 
        "V3.0",
        help="Version actuelle de CryptoViz"
    )

if not connection_status:
    st.warning("⚠️ **Système ML indisponible** - Les prédictions ML peuvent ne pas fonctionner")

# Navigation des pages
st.subheader("📱 Navigation")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="feature-card">
        <h4>📊 Dashboard Principal</h4>
        <p>Vue d'ensemble temps réel des cryptomonnaies</p>
        <ul>
            <li>Métriques en temps réel</li>
            <li>Graphiques interactifs</li>
            <li>Top cryptos et tendances</li>
            <li>Données live depuis Kafka</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Ouvrir Dashboard Principal", width="stretch", type="primary"):
        st.switch_page("pages/1_📊_Dashboard_Principal.py")

with col2:
    st.markdown("""
    <div class="feature-card">
        <h4>🤖 ML Predictions</h4>
        <p>Prédictions de prix par intelligence artificielle</p>
        <ul>
            <li>Architecture Redis ultra-rapide</li>
            <li>7+ cryptos avec prédictions</li>
            <li>4 modèles ML temps réel</li>
            <li>Signaux de trading automatiques</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔮 Ouvrir ML Predictions", width="stretch", type="secondary"):
        st.switch_page("pages/2_🤖_ML_Predictions.py")

# Architecture et informations
st.subheader("🏗️ Architecture")

st.markdown("""
### Stack Technique
- **Frontend:** Streamlit Multi-Pages
- **ML Temps Réel:** Kafka → ML Processor → Redis  
- **Données Archives:** MinIO Data Lake (Parquet)
- **Streaming:** RedPanda (Kafka)
- **Processing:** Apache Spark

### Fonctionnalités V3.0
- 📊 **Dashboard temps réel** avec métriques live depuis Kafka
- 🤖 **ML Predictions ultra-rapides** via Redis (millisecondes)
- 🔄 **Pipeline continu** de données en streaming
- 💾 **Architecture standard** de l'industrie ML
- 🚀 **Interface moderne** et responsive
""")

# Informations de debugging
with st.expander("🐛 Informations Debug"):
    st.write(f"**Timestamp:** {datetime.now()}")
    st.write(f"**Connexion ML:** {'✅ OK' if connection_status else '❌ KO'}")
    st.write(f"**Working Directory:** {os.getcwd()}")
    
    # Structure des pages
    pages_dir = "pages"
    if os.path.exists(pages_dir):
        pages = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
        st.write(f"**Pages disponibles:** {pages}")
    else:
        st.write("**Pages:** Dossier pages non trouvé")

st.markdown("---")
st.markdown("*CryptoViz V3.0 - Analytics & ML Predictions avec Architecture Standard*")
