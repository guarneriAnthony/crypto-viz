"""
CryptoViz V4.0 - Page d'Accueil Ultra-Moderne
Style visuel aligné sur ML Ultra Dashboard
Navigation entre Dashboard Principal et ML Predictions
"""
import streamlit as st
import sys
import os
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="CryptoViz V4.0 - Accueil", 
    page_icon="💲",
    layout="wide"
)

# CSS Ultra-moderne avec animations et effets (identique au ML Dashboard)
st.markdown("""
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;400;500;600;700&display=swap');

/* Variables CSS pour cohérence */
:root {
    --primary-color: #00d4ff;
    --secondary-color: #ff6b35;
    --accent-color: #7b68ee;
    --success-color: #00ff88;
    --warning-color: #ffaa00;
    --danger-color: #ff3366;
    --dark-bg: #0a0a0a;
    --card-bg: #1a1a1a;
    --text-primary: #ffffff;
    --text-secondary: #b0b0b0;
    --glow-color: rgba(0, 212, 255, 0.3);
}

/* Reset et fond principal */
.main {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    color: var(--text-primary);
    font-family: 'Rajdhani', sans-serif;
}

/* Header ultra-futuriste */
.ultra-header {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(123, 104, 238, 0.1) 100%);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 15px;
    padding: 40px;
    margin-bottom: 30px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 30px rgba(0, 212, 255, 0.2);
}

.ultra-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(45deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    animation: rotate 6s linear infinite;
}

@keyframes rotate {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.ultra-title {
    font-family: 'Orbitron', monospace;
    font-size: 4em;
    font-weight: 900;
    background: linear-gradient(135deg, #00d4ff 0%, #7b68ee 50%, #ff6b35 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    text-shadow: 0 0 30px rgba(0, 212, 255, 0.5);
    position: relative;
    z-index: 2;
}

.ultra-subtitle {
    font-size: 1.6em;
    color: var(--text-secondary);
    margin-top: 15px;
    font-weight: 400;
    position: relative;
    z-index: 2;
}

.ultra-description {
    font-size: 1.2em;
    color: var(--text-secondary);
    margin-top: 10px;
    font-weight: 300;
    position: relative;
    z-index: 2;
}

/* Section title */
.section-title {
    font-family: 'Orbitron', monospace;
    font-size: 2.2em;
    font-weight: 700;
    color: var(--primary-color);
    margin: 30px 0 20px 0;
    text-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    display: flex;
    align-items: center;
    gap: 15px;
}

.section-title::before,
.section-title::after {
    content: '';
    flex: 1;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
}

/* Métriques ultra avec animations */
.metric-ultra {
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.9) 0%, rgba(42, 42, 42, 0.7) 100%);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 12px;
    padding: 20px;
    margin: 10px 0;
    text-align: center;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    height: 120px;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.metric-ultra:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(0, 212, 255, 0.3);
    border-color: var(--primary-color);
}

.metric-ultra::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.1), transparent);
    transition: left 0.5s;
}

.metric-ultra:hover::before {
    left: 100%;
}

.metric-value {
    font-family: 'Orbitron', monospace;
    font-size: 2.2em;
    font-weight: 700;
    margin: 0;
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.metric-label {
    font-size: 1em;
    color: var(--text-secondary);
    margin-top: 8px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Cards ultra-modernes */
.ultra-card {
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.95) 0%, rgba(42, 42, 42, 0.8) 100%);
    border: 1px solid rgba(0, 212, 255, 0.2);
    border-radius: 15px;
    padding: 30px;
    margin: 15px 0;
    backdrop-filter: blur(15px);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    height: auto;
    min-height: 300px;
}

.ultra-card:hover {
    border-color: var(--primary-color);
    box-shadow: 0 0 40px rgba(0, 212, 255, 0.2);
    transform: translateY(-5px);
}

.ultra-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.05), transparent);
    transition: left 0.6s;
}

.ultra-card:hover::before {
    left: 100%;
}

.card-title {
    font-family: 'Orbitron', monospace;
    font-size: 1.6em;
    font-weight: 700;
    color: var(--primary-color);
    margin-bottom: 15px;
    position: relative;
    z-index: 2;
}

.card-description {
    color: var(--text-secondary);
    font-size: 1.1em;
    line-height: 1.6;
    margin-bottom: 20px;
    position: relative;
    z-index: 2;
}

.feature-list {
    list-style: none;
    padding: 0;
    margin: 0;
    position: relative;
    z-index: 2;
}

.feature-list li {
    color: var(--text-secondary);
    font-size: 0.95em;
    line-height: 1.8;
    padding: 5px 0;
    padding-left: 25px;
    position: relative;
}

.feature-list li::before {
    content: '▶';
    color: var(--accent-color);
    font-weight: bold;
    position: absolute;
    left: 0;
    top: 5px;
}

/* Alerts stylées */
.ultra-alert {
    padding: 20px;
    border-radius: 12px;
    margin: 15px 0;
    font-weight: 500;
    border-left: 4px solid;
    animation: slideIn 0.3s ease;
    backdrop-filter: blur(10px);
}

@keyframes slideIn {
    from { transform: translateX(-20px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

.alert-success {
    background: rgba(0, 255, 136, 0.1);
    border-left-color: var(--success-color);
    color: var(--success-color);
}

.alert-warning {
    background: rgba(255, 170, 0, 0.1);
    border-left-color: var(--warning-color);
    color: var(--warning-color);
}

/* Status indicators */
.status-indicator {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 8px;
    animation: pulse 2s infinite;
}

.status-online { background: var(--success-color); }
.status-error { background: var(--danger-color); }

@keyframes pulse {
    0% { opacity: 1; box-shadow: 0 0 0 0 currentColor; }
    70% { opacity: 0.7; box-shadow: 0 0 0 10px rgba(0, 0, 0, 0); }
    100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0, 0, 0, 0); }
}

/* Architecture section */
.architecture-section {
    background: linear-gradient(135deg, rgba(26, 26, 26, 0.6) 0%, rgba(42, 42, 42, 0.4) 100%);
    border: 1px solid rgba(123, 104, 238, 0.3);
    border-radius: 15px;
    padding: 30px;
    margin: 30px 0;
    backdrop-filter: blur(10px);
}

.tech-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 15px;
    margin: 20px 0;
}

.tech-item {
    background: rgba(0, 212, 255, 0.1);
    border: 1px solid rgba(0, 212, 255, 0.3);
    border-radius: 10px;
    padding: 20px;
    text-align: center;
    transition: all 0.3s ease;
}

.tech-item:hover {
    background: rgba(0, 212, 255, 0.2);
    transform: scale(1.05);
    box-shadow: 0 5px 20px rgba(0, 212, 255, 0.2);
}

.tech-item strong {
    font-family: 'Orbitron', monospace;
    font-size: 1.1em;
    display: block;
    margin-bottom: 8px;
}

/* Animations */
.fade-in {
    animation: fadeIn 0.8s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.typing-effect {
    overflow: hidden;
    white-space: nowrap;
    animation: typing 3s steps(20, end);
}

@keyframes typing {
    from { width: 0; }
    to { width: 100%; }
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--accent-color) 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 15px 30px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 600 !important;
    font-size: 1.1em !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
    margin-top: 15px !important;
    box-shadow: 0 5px 15px rgba(0, 212, 255, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 25px rgba(0, 212, 255, 0.4) !important;
}

/* Footer */
.ultra-footer {
    text-align: center;
    padding: 20px 0;
    border-top: 1px solid rgba(0, 212, 255, 0.2);
    margin-top: 40px;
    color: var(--text-secondary);
    font-style: italic;
}

/* Responsive */
@media (max-width: 768px) {
    .ultra-title {
        font-size: 2.5em;
    }
    
    .section-title {
        font-size: 1.8em;
    }
    
    .ultra-card {
        padding: 20px;
        min-height: auto;
    }
}
</style>
""", unsafe_allow_html=True)

# En-tête ultra-futuriste
st.markdown("""
<div class="ultra-header fade-in">
    <h1 class="ultra-title typing-effect">CryptoViz  V4.0</h1>
    <h3 class="ultra-subtitle">Dashboard Multi-Pages avec ML Predictions</h3>
    <p class="ultra-description">Analyse temps réel des cryptomonnaies avec prédictions IA</p>
</div>
""", unsafe_allow_html=True)

# Test de connexion Redis ML
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from utils.redis_ml_client import test_ml_connection
    connection_status = test_ml_connection()
except Exception as e:
    connection_status = False

# Statut du système avec style ultra
st.markdown('<div class="section-title">Statut du Système</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    status_icon = "✅" if connection_status else "❌"
    status_text = "OK" if connection_status else "Erreur"
    status_color = "var(--success-color)" if connection_status else "var(--danger-color)"
    
    st.markdown(f"""
    <div class="metric-ultra">
        <div class="metric-value" style="color: {status_color};">{status_icon}</div>
        <div class="metric-label">Connexion ML</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.markdown(f"""
    <div class="metric-ultra">
        <div class="metric-value">{current_time}</div>
        <div class="metric-label">Dernière MAJ</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-ultra">
        <div class="metric-value"> V4.0</div>
        <div class="metric-label">Version</div>
    </div>
    """, unsafe_allow_html=True)

# Alert de statut
if not connection_status:
    st.markdown("""
    <div class="ultra-alert alert-warning">
        <strong>⚠️ Système ML indisponible</strong><br>
        Les prédictions ML peuvent ne pas fonctionner correctement.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="ultra-alert alert-success">
        <span class="status-indicator status-online"></span>
        <strong>Système opérationnel</strong><br>
        Tous les services sont en ligne et fonctionnent correctement.
    </div>
    """, unsafe_allow_html=True)

# Navigation des pages avec style ultra
st.markdown('<div class="section-title">Navigation</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="ultra-card fade-in">
        <h4 class="card-title">Dashboard Principal</h4>
        <p class="card-description">Vue d'ensemble temps réel des cryptomonnaies</p>
        <ul class="feature-list">
            <li>Métriques en temps réel</li>
            <li>Graphiques interactifs</li>
            <li>Top cryptos et tendances</li>
            <li>Données live depuis Kafka</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Ouvrir hybrideViz", key="dashboard"):
        st.switch_page("pages/2_hybrideViz.py")

with col2:
    st.markdown("""
    <div class="ultra-card fade-in">
        <h4 class="card-title">ML Predictions</h4>
        <p class="card-description">Prédictions de prix par intelligence artificielle</p>
        <ul class="feature-list">
            <li>Architecture Redis ultra-rapide</li>
            <li>7+ cryptos avec prédictions</li>
            <li>4 modèles ML temps réel</li>
            <li>Signaux de trading automatiques</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("Ouvrir ML Predictions", key="ml"):
        st.switch_page("pages/3_Predicte.py")

# Architecture avec style ultra
st.markdown('<div class="section-title">Architecture</div>', unsafe_allow_html=True)

st.markdown("""
""", unsafe_allow_html=True)

# Informations de debugging avec style
with st.expander("Informations Debug"):
    debug_time = datetime.now()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Timestamp:** {debug_time.strftime('%Y-%m-%d %H:%M:%S')}  
        **Connexion ML:** {'✅ OK' if connection_status else '❌ KO'}  
        **Working Directory:** {os.getcwd()}
        """)
    
    with col2:
        # Structure des pages
        pages_dir = "pages"
        if os.path.exists(pages_dir):
            pages = [f for f in os.listdir(pages_dir) if f.endswith('.py')]
            st.write(f"**Pages disponibles:** {pages}")
        else:
            st.write("**Pages:** Dossier pages non trouvé")

# Footer ultra-moderne
st.markdown("""
<div class="ultra-footer fade-in">
    <em>CryptoViz V4.0 - Analytics & ML Predictions avec Architecture Standard</em>
</div>
""", unsafe_allow_html=True)