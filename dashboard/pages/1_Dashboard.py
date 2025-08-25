import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Configuration de la page
st.set_page_config(page_title="CryptoViz Multi-Sources Dashboard", layout="wide")

st.title("CryptoViz Dashboard - Analyse Multi-Sources")
st.markdown("*Données agrégées de CoinMarketCap & CoinGecko*")

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
    st.warning("En attente des données... Le système est en cours d'initialisation.")
    st.info("Cette opération peut prendre quelques minutes.")
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
st.sidebar.header("Filtres")

# Récupérer les sources disponibles
sources_data = get_available_sources()

if not sources_data.empty:
    st.sidebar.subheader("Statut des Sources")
    for _, row in sources_data.iterrows():
        source = row['source']
        records = row['records']
        latest = row['latest_update']
        
        # Calculer l'âge des données
        if latest:
            age_minutes = (datetime.now() - latest).total_seconds() / 60
            if age_minutes < 10:
                status = "🟢"
                status_text = f"{age_minutes:.0f}min"
            elif age_minutes < 60:
                status = "🟡" 
                status_text = f"{age_minutes:.0f}min"
            else:
                status = "🔴"
                status_text = f"{age_minutes/60:.1f}h"
        else:
            status = "🔴"
            status_text = "N/A"
        
        st.sidebar.metric(
            f"{status} {source.title()}", 
            f"{records:,} records",
            f"MAJ: {status_text}"
        )

    # Sélecteur de sources
    available_sources = sources_data['source'].tolist()
    sources_options = ["Toutes sources"] + available_sources
    
    selected_sources = st.sidebar.multiselect(
        "Choisir les sources:",
        options=sources_options,
        default=["Toutes sources"]
    )
    
    if not selected_sources:
        selected_sources = ["Toutes sources"]
        
else:
    st.sidebar.warning("Aucune source de données détectée")
    selected_sources = ["Toutes sources"]

# Récupérer les cryptos
cryptos_with_prices = get_cryptos_with_prices(selected_sources)
cryptos = cryptos_with_prices['name'].tolist()

selected_cryptos = st.sidebar.multiselect(
    "Sélectionnez les cryptomonnaies:",
    options=cryptos if cryptos else [],
    default=cryptos[:3] if cryptos else []
)

# Type de graphique
chart_type = st.sidebar.selectbox(
    "Type d'affichage:",
    [
        "Graphique unifié (toutes sources)",
        "Comparaison par source", 
        "Graphiques séparés par crypto",
        "Variations relatives (%)"
    ]
)

# Période
st.sidebar.info(f"Données disponibles: {min_data_date} au {max_data_date}")
date_range = st.sidebar.date_input(
    "Période:",
    value=(min_data_date, max_data_date),
    min_value=min_data_date,
    max_value=max_data_date
)

# Indicateurs Clés
st.header("Indicateurs Clés")

@st.cache_data(ttl=30)
def get_multi_source_metrics():
    try:
        conn = get_connection()
        
        total_records = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        unique_cryptos = conn.execute("SELECT COUNT(DISTINCT name) FROM crypto_prices").fetchone()[0]
        latest_update = conn.execute("SELECT MAX(timestamp) FROM crypto_prices").fetchone()[0]
        
        source_metrics = conn.execute("""
            SELECT source, COUNT(*) as records, COUNT(DISTINCT name) as cryptos
            FROM crypto_prices 
            GROUP BY source
            ORDER BY source
        """).fetchdf()
        
        conn.close()
        return total_records, unique_cryptos, latest_update, source_metrics
        
    except:
        return 0, 0, None, pd.DataFrame()

total_records, unique_cryptos, latest_update, source_metrics = get_multi_source_metrics()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Records", f"{total_records:,}")

with col2:
    st.metric("Cryptos Suivies", unique_cryptos)

with col3:
    if latest_update:
        age_seconds = (datetime.now() - latest_update).total_seconds()
        age_text = f"{latest_update.strftime('%H:%M:%S')} ({age_seconds:.0f}s)"
        st.metric("Dernière MAJ", age_text)
    else:
        st.metric("Dernière MAJ", "N/A")

with col4:
    if not source_metrics.empty:
        active_sources = len(source_metrics)
        st.metric("Sources Actives", active_sources)
    else:
        st.metric("Sources Actives", 0)

# Répartition par source
if not source_metrics.empty:
    st.subheader("Répartition par Source")
    
    cols = st.columns(len(source_metrics))
    for i, (_, row) in enumerate(source_metrics.iterrows()):
        with cols[i]:
            source_name = row['source'].title()
            records = row['records']
            cryptos_count = row['cryptos']
            st.metric(
                source_name, 
                f"{records:,} records",
                f"{cryptos_count} cryptos"
            )

# Graphiques
st.header("Évolution des Prix")

if selected_cryptos and len(date_range) == 2:
    start_date, end_date = date_range
    
    crypto_list = "', '".join(selected_cryptos)
    
    if "Toutes sources" in selected_sources:
        source_filter = ""
    else:
        sources_str = "', '".join(selected_sources)
        source_filter = f"AND source IN ('{sources_str}')"
    
    query = f"""
        SELECT name, price, timestamp, source
        FROM crypto_prices 
        WHERE name IN ('{crypto_list}')
        AND date(timestamp) >= '{start_date}' 
        AND date(timestamp) <= '{end_date}'
        {source_filter}
        ORDER BY timestamp
    """
    
    try:
        conn = get_connection()
        price_data = conn.execute(query).fetchdf()
        conn.close()
        
        if not price_data.empty:
            st.sidebar.success(f"Données chargées: {len(price_data)} lignes")
            
            # Couleurs par source
            source_colors = {
                'coinmarketcap': '#1f77b4',
                'coingecko': '#ff7f0e'
            }
            
            if chart_type == "Graphique unifié (toutes sources)":
                price_data['crypto_source'] = price_data['name'] + ' (' + price_data['source'] + ')'
                
                fig = px.line(
                    price_data, 
                    x='timestamp', 
                    y='price', 
                    color='crypto_source',
                    title=f'Évolution Multi-Sources ({start_date} au {end_date})',
                    labels={'price': 'Prix (USD)', 'timestamp': 'Temps'}
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Comparaison par source":
                fig = px.line(
                    price_data, 
                    x='timestamp', 
                    y='price', 
                    color='source',
                    facet_col='name',
                    facet_col_wrap=2,
                    title=f'Comparaison Sources ({start_date} au {end_date})',
                    labels={'price': 'Prix (USD)', 'timestamp': 'Temps'},
                    color_discrete_map=source_colors
                )
                fig.update_layout(height=400 * ((len(selected_cryptos) + 1) // 2))
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Graphiques séparés par crypto":
                fig = make_subplots(
                    rows=len(selected_cryptos), 
                    cols=1,
                    subplot_titles=selected_cryptos,
                    shared_xaxes=True,
                    vertical_spacing=0.1
                )
                
                for i, crypto in enumerate(selected_cryptos):
                    crypto_data = price_data[price_data['name'] == crypto]
                    
                    for source in crypto_data['source'].unique():
                        source_data = crypto_data[crypto_data['source'] == source]
                        fig.add_trace(
                            go.Scatter(
                                x=source_data['timestamp'], 
                                y=source_data['price'],
                                name=f"{crypto} ({source})",
                                line=dict(color=source_colors.get(source, '#000000')),
                                mode='lines'
                            ), 
                            row=i+1, col=1
                        )
                        
                    fig.update_yaxes(title_text="Prix USD", row=i+1, col=1)
                
                fig.update_layout(
                    height=300 * len(selected_cryptos),
                    title_text=f"Évolutions par Source ({start_date} au {end_date})"
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Variations relatives (%)":
                price_data_pct = price_data.copy()
                price_data_pct['price_pct'] = price_data_pct.groupby(['name', 'source'])['price'].transform(
                    lambda x: (x / x.iloc[0] - 1) * 100 if len(x) > 0 else 0
                )
                
                price_data_pct['crypto_source'] = price_data_pct['name'] + ' (' + price_data_pct['source'] + ')'
                
                fig = px.line(
                    price_data_pct, 
                    x='timestamp', 
                    y='price_pct', 
                    color='crypto_source',
                    title=f'Variations Relatives ({start_date} au {end_date})',
                    labels={'price_pct': 'Variation (%)', 'timestamp': 'Temps'}
                )
                fig.update_layout(height=600)
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                st.plotly_chart(fig, use_container_width=True)
                
        else:
            st.warning("Aucune donnée disponible pour la sélection actuelle.")
            st.info(f"Période: {start_date} à {end_date}")
            st.info(f"Cryptos: {', '.join(selected_cryptos)}")
            st.info(f"Sources: {', '.join(selected_sources)}")
            
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données: {e}")
        with st.expander("Détails de la requête"):
            st.code(query)
else:
    st.info("Veuillez sélectionner au moins une cryptomonnaie et une période valide.")

# Tableau des données récentes
st.header("Données Récentes")
try:
    conn = get_connection()
    recent_data = conn.execute("""
        SELECT name, symbol, price, percent_change_24h, market_cap, source, timestamp
        FROM crypto_prices 
        ORDER BY timestamp DESC 
        LIMIT 20
    """).fetchdf()
    conn.close()
    
    if not recent_data.empty:
        recent_data['price'] = recent_data['price'].apply(lambda x: f"${x:,.2f}")
        recent_data['market_cap'] = recent_data['market_cap'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
        recent_data['percent_change_24h'] = recent_data['percent_change_24h'].apply(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A")
        
    st.dataframe(recent_data, use_container_width=True)
except Exception as e:
    st.error(f"Erreur lors du chargement des données récentes: {e}")

# Contrôles
col_refresh, col_status = st.columns([1, 2])
with col_refresh:
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()

with col_status:
    if latest_update:
        age_seconds = (datetime.now() - latest_update).total_seconds()
        if age_seconds < 300:
            st.success(f"🟢 Multi-Sources Actifs (dernière donnée: {age_seconds:.0f}s)")
        else:
            st.warning(f"🟡 Données anciennes ({age_seconds/60:.0f} min)")
    else:
        st.error("🔴 Aucune donnée")

st.markdown("---")
st.markdown("*Dashboard Multi-Sources - CoinMarketCap & CoinGecko*")
