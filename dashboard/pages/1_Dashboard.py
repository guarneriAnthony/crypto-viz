import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Configuration de la page
st.set_page_config(page_title="🏠 Pipeline Monitoring - CryptoViz", layout="wide")

st.title(" Pipeline Monitoring - CryptoViz")
st.markdown("* Surveillance temps réel du pipeline dual batch + streaming*")

def get_connection():
    """Retourne une connexion DuckDB courte"""
    return duckdb.connect(database='/data/crypto_analytics.duckdb', read_only=True)

def check_table_exists():
    """Vérifier si la table existe"""
    try:
        conn = get_connection()
        result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'crypto_prices'").fetchone()
        conn.close()
        return result[0] > 0
    except:
        return False

# Attendre que la table soit créée
if not check_table_exists():
    st.warning(" En attente des données... Le système est en cours d'initialisation.")
    st.info(" Cette opération peut prendre quelques minutes.")
    time.sleep(5)
    st.rerun()
    st.stop()

# Récupérer les sources disponibles
@st.cache_data(ttl=60)
def get_available_sources():
    try:
        conn = get_connection()
        result = conn.execute("""
            SELECT source, COUNT(*) as records, MAX(timestamp) as latest_update
            FROM crypto_prices 
            GROUP BY source 
            ORDER BY source
        """).fetchdf()
        conn.close()
        return result
    except:
        return pd.DataFrame(columns=['source', 'records', 'latest_update'])

# Récupérer la liste des cryptomonnaies
@st.cache_data(ttl=60)
def get_cryptos_with_prices(selected_sources):
    try:
        conn = get_connection()
        if "Toutes sources" in selected_sources:
            source_filter = ""
        else:
            sources_str = "', '".join(selected_sources)
            source_filter = f"WHERE source IN ('{sources_str}')"
        
        query = f"""
            SELECT name, AVG(price) as avg_price 
            FROM crypto_prices 
            {source_filter}
            GROUP BY name 
            ORDER BY avg_price DESC
        """
        result = conn.execute(query).fetchdf()
        conn.close()
        return result
    except:
        return pd.DataFrame(columns=['name', 'avg_price'])

@st.cache_data(ttl=30)
def get_data_period():
    try:
        conn = get_connection()
        result = conn.execute("SELECT MIN(timestamp) as min_date, MAX(timestamp) as max_date FROM crypto_prices").fetchone()
        conn.close()
        return result[0].date(), result[1].date()
    except:
        return datetime.now().date(), datetime.now().date()

min_data_date, max_data_date = get_data_period()

# Sidebar avec filtres
st.sidebar.header(" Contrôles Pipeline")

# Récupérer les sources disponibles
sources_data = get_available_sources()

if not sources_data.empty:
    st.sidebar.subheader(" Statut des Sources")
    for _, row in sources_data.iterrows():
        source = row['source']
        records = row['records']
        latest_update = pd.to_datetime(row['latest_update'])
        
        # Calculer le délai depuis la dernière mise à jour
        time_since_update = datetime.now() - latest_update
        minutes_since = time_since_update.total_seconds() / 60
        
        # Icône status basée sur fraîcheur des données
        if minutes_since < 10:
            status_icon = "🟢"
            status_text = "Actif"
        elif minutes_since < 30:
            status_icon = "🟡" 
            status_text = "Ralenti"
        else:
            status_icon = "🔴"
            status_text = "Inactif"
        
        st.sidebar.metric(
            f"{status_icon} {source.title()}", 
            f"{records:,} records",
            f"{status_text} - {latest_update.strftime('%H:%M:%S')}"
        )

# Sélection sources
available_sources = sources_data['source'].tolist() if not sources_data.empty else []
source_options = ["Toutes sources"] + available_sources

selected_sources = st.sidebar.multiselect(
    " Sources à analyser",
    source_options,
    default=["Toutes sources"]
)

if not selected_sources:
    selected_sources = ["Toutes sources"]

# Filtre période
st.sidebar.subheader(" Période d'Analyse")
date_range = st.sidebar.date_input(
    "Sélectionner la période",
    value=[max_data_date - timedelta(days=1), max_data_date],
    min_value=min_data_date,
    max_value=max_data_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = max_data_date

# Sélection crypto
cryptos_data = get_cryptos_with_prices(selected_sources)
if not cryptos_data.empty:
    crypto_options = cryptos_data['name'].tolist()
    selected_cryptos = st.sidebar.multiselect(
        "💰 Cryptomonnaies",
        crypto_options,
        default=crypto_options[:5] if len(crypto_options) >= 5 else crypto_options
    )
else:
    selected_cryptos = []
    st.sidebar.warning("⚠️ Aucune crypto disponible avec les filtres actuels")

# Fonction pour récupérer les données avec filtres
@st.cache_data(ttl=30)
def get_filtered_data(sources, cryptos, start_date, end_date):
    if not cryptos:
        return pd.DataFrame()
    
    try:
        conn = get_connection()
        
        # Construire les filtres
        if "Toutes sources" in sources:
            source_filter = ""
        else:
            sources_str = "', '".join(sources)
            source_filter = f" AND source IN ('{sources_str}')"
        
        cryptos_str = "', '".join(cryptos)
        
        query = f"""
            SELECT *
            FROM crypto_prices
            WHERE name IN ('{cryptos_str}')
            AND DATE(timestamp) BETWEEN '{start_date}' AND '{end_date}'
            {source_filter}
            ORDER BY timestamp DESC
        """
        
        result = conn.execute(query).fetchdf()
        conn.close()
        return result
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des données: {e}")
        return pd.DataFrame()

# Récupérer les données filtrées
data = get_filtered_data(selected_sources, selected_cryptos, start_date, end_date)

if data.empty:
    st.warning("⚠️ Aucune donnée trouvée avec les filtres actuels")
    st.stop()

# Métriques principales
st.header(" Métriques Pipeline")
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_records = len(data)
    st.metric("📈 Total Records", f"{total_records:,}")

with col2:
    unique_cryptos = data['name'].nunique()
    st.metric("💰 Cryptos Uniques", unique_cryptos)

with col3:
    unique_sources = data['source'].nunique()
    st.metric("🌐 Sources Actives", unique_sources)

with col4:
    latest_price = data.iloc[0]['price'] if not data.empty else 0
    st.metric("💎 Dernier Prix", f"${latest_price:,.2f}")

# Status temps réel
st.header(" Status Temps Réel")
col1, col2 = st.columns(2)

with col1:
    st.subheader(" Pipeline Batch")
    
    # Calculer dernière activité
    if not data.empty:
        last_update = pd.to_datetime(data['timestamp'].max())
        time_since = datetime.now() - last_update
        minutes_ago = int(time_since.total_seconds() / 60)
        
        if minutes_ago < 10:
            batch_status = "🟢 Actif"
            batch_color = "normal"
        elif minutes_ago < 30:
            batch_status = "🟡 Ralenti" 
            batch_color = "normal"
        else:
            batch_status = "🔴 Problème"
            batch_color = "inverse"
            
        st.success(f"{batch_status} - Dernière donnée: {minutes_ago}min")
    else:
        st.error("🔴 Aucune donnée disponible")

with col2:
    st.subheader(" Pipeline Streaming")
    
    # Test basique streaming server
    try:
        import requests
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            health_data = response.json()
            if health_data.get('status') == 'healthy':
                st.success("🟢 Streaming Server Actif")
            else:
                st.warning("🟡 Streaming Server Limité")
        else:
            st.error("🔴 Streaming Server Inaccessible")
    except:
        st.error("🔴 Streaming Server Hors Ligne")

# Graphique principal - Prix dans le temps
st.header(" Analyse Multi-Sources")

if len(selected_cryptos) > 0:
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3
    
    for i, crypto in enumerate(selected_cryptos[:10]):  # Limiter à 10 cryptos
        crypto_data = data[data['name'] == crypto].sort_values('timestamp')
        
        if not crypto_data.empty:
            # Grouper par source pour différencier
            for source in crypto_data['source'].unique():
                source_data = crypto_data[crypto_data['source'] == source]
                
                fig.add_trace(go.Scatter(
                    x=source_data['timestamp'],
                    y=source_data['price'],
                    mode='lines+markers',
                    name=f"{crypto} ({source})",
                    line=dict(color=colors[i % len(colors)]),
                    marker=dict(size=4)
                ))
    
    fig.update_layout(
        title="💹 Évolution des Prix par Source",
        xaxis_title="📅 Temps",
        yaxis_title="💰 Prix ($)",
        height=600,
        hovermode='x unified',
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Comparaison par source
if len(available_sources) > 1:
    st.header(" Comparaison Multi-Sources")
    
    comparison_data = []
    for crypto in selected_cryptos[:5]:  # Top 5 cryptos
        crypto_data = data[data['name'] == crypto]
        for source in available_sources:
            source_data = crypto_data[crypto_data['source'] == source]
            if not source_data.empty:
                avg_price = source_data['price'].mean()
                latest_price = source_data['price'].iloc[0]
                comparison_data.append({
                    'Crypto': crypto,
                    'Source': source,
                    'Prix Moyen': avg_price,
                    'Prix Actuel': latest_price,
                    'Records': len(source_data)
                })
    
    if comparison_data:
        comparison_df = pd.DataFrame(comparison_data)
        
        fig = px.bar(
            comparison_df, 
            x='Crypto', 
            y='Prix Actuel', 
            color='Source',
            title="📊 Prix Actuel par Source",
            text='Prix Actuel'
        )
        fig.update_traces(texttemplate='$%{text:,.2f}', textposition='outside')
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

# Statistiques détaillées
st.header(" Statistiques Pipeline")

col1, col2 = st.columns(2)

with col1:
    st.subheader(" Par Crypto")
    crypto_stats = data.groupby('name').agg({
        'price': ['mean', 'min', 'max', 'std'],
        'timestamp': 'count'
    }).round(2)
    crypto_stats.columns = ['Prix Moyen', 'Prix Min', 'Prix Max', 'Volatilité', 'Records']
    crypto_stats = crypto_stats.sort_values('Prix Moyen', ascending=False)
    st.dataframe(crypto_stats, use_container_width=True)

with col2:
    st.subheader(" Par Source")
    if not sources_data.empty:
        # Enrichir avec stats temps réel
        for idx, row in sources_data.iterrows():
            source = row['source']
            source_data = data[data['source'] == source]
            if not source_data.empty:
                avg_price = source_data['price'].mean()
                sources_data.loc[idx, 'Prix Moyen'] = avg_price
                
                # Status icône
                latest_update = pd.to_datetime(row['latest_update'])
                time_since = datetime.now() - latest_update
                minutes_since = time_since.total_seconds() / 60
                
                if minutes_since < 10:
                    sources_data.loc[idx, 'Status'] = "🟢 Actif"
                elif minutes_since < 30:
                    sources_data.loc[idx, 'Status'] = "🟡 Ralenti"
                else:
                    sources_data.loc[idx, 'Status'] = "🔴 Problème"
        
        display_sources = sources_data[['source', 'records', 'Status']].copy()
        display_sources.columns = ['Source', 'Records', 'Status']
        st.dataframe(display_sources, use_container_width=True)

# Auto-refresh
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Actualiser les Données"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("*🔄 Actualisation automatique toutes les 30s*")
