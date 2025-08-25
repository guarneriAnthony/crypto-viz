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

# Titre avec icône multi-sources
st.title(" CryptoViz Dashboard - Analyse Multi-Sources Temps Réel")
st.markdown("*Données agrégées de CoinMarketCap & CoinGecko*")

def get_connection():
    """Retourne une connexion DuckDB courte (non cachée)"""
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
    st.warning("⏳ En attente des données... Le système est en cours d'initialisation.")
    st.info("Cette opération peut prendre quelques minutes. Le dashboard se rafraîchira automatiquement.")
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

# Récupérer la liste des cryptomonnaies avec leurs prix moyens
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

# Récupérer la période des données disponibles
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

# Sidebar avec filtres multi-sources
st.sidebar.header("Filtres Multi-Sources")

# Récupérer les sources disponibles
sources_data = get_available_sources()

if not sources_data.empty:
    # Affichage du statut des sources
    st.sidebar.subheader("📡 Statut des Sources")
    for _, row in sources_data.iterrows():
        source = row['source']
        records = row['records']
        latest = row['latest_update']
        
        # Calculer l'âge des données
        if latest:
            age_minutes = (datetime.now() - latest).total_seconds() / 60
            if age_minutes < 10:
                status_icon = "🟢"
                status_text = f"{age_minutes:.0f}min"
            elif age_minutes < 60:
                status_icon = "🟡" 
                status_text = f"{age_minutes:.0f}min"
            else:
                status_icon = "🔴"
                status_text = f"{age_minutes/60:.1f}h"
        else:
            status_icon = "❓"
            status_text = "N/A"
        
        st.sidebar.metric(
            f"{status_icon} {source.title()}", 
            f"{records:,} records",
            f"MAJ: {status_text}"
        )

    # Sélecteur de sources
    available_sources = sources_data['source'].tolist()
    sources_options = ["Toutes sources"] + available_sources
    
    selected_sources = st.sidebar.multiselect(
        "🎯 Choisir les sources:",
        options=sources_options,
        default=["Toutes sources"]
    )
    
    if not selected_sources:
        selected_sources = ["Toutes sources"]
        
else:
    st.sidebar.warning("Aucune source de données détectée")
    selected_sources = ["Toutes sources"]

# Récupérer les cryptos en fonction des sources sélectionnées
cryptos_with_prices = get_cryptos_with_prices(selected_sources)
cryptos = cryptos_with_prices['name'].tolist()

selected_cryptos = st.sidebar.multiselect(
    " Sélectionnez les cryptomonnaies:",
    options=cryptos if cryptos else [],
    default=cryptos[:3] if cryptos else []
)

# Type de graphique avec nouvelles options multi-sources
chart_options = [
    " Graphique unifié (toutes sources)",
    " Comparaison par source", 
    " Graphiques séparés par crypto",
    " Variations relatives (%)",
    " Écarts entre sources"
]

chart_type = st.sidebar.selectbox(" Type d'affichage:", chart_options)

# Période
st.sidebar.info(f" Données disponibles du {min_data_date} au {max_data_date}")
date_range = st.sidebar.date_input(
    " Période:",
    value=(min_data_date, max_data_date),
    min_value=min_data_date,
    max_value=max_data_date
)

# Indicateurs Clés Multi-Sources
st.header("Indicateurs Clés Multi-Sources")

@st.cache_data(ttl=30)
def get_multi_source_metrics():
    try:
        conn = get_connection()
        
        # Métriques globales
        total_records = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        unique_cryptos = conn.execute("SELECT COUNT(DISTINCT name) FROM crypto_prices").fetchone()[0]
        latest_update = conn.execute("SELECT MAX(timestamp) FROM crypto_prices").fetchone()[0]
        
        # Métriques par source
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

# Affichage des métriques par source
if not source_metrics.empty:
    st.subheader("Répartition par Source")
    
    cols = st.columns(len(source_metrics))
    for i, (_, row) in enumerate(source_metrics.iterrows()):
        with cols[i]:
            source_name = row['source'].title()
            records = row['records']
            cryptos = row['cryptos']
            st.metric(
                f"{source_name}", 
                f"{records:,} records",
                f"{cryptos} cryptos"
            )

# Graphiques Multi-Sources
st.header("Analyse Multi-Sources")

if selected_cryptos and len(date_range) == 2:
    start_date, end_date = date_range
    
    # Construction de la requête avec filtrage par sources
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
        AND timestamp >= '{start_date}' 
        AND timestamp <= '{end_date} 23:59:59'
        {source_filter}
        ORDER BY timestamp
    """
    
    try:
        conn = get_connection()
        price_data = conn.execute(query).fetchdf()
        conn.close()
        
        if not price_data.empty:
            # Info sur les données chargées
            st.sidebar.success(f"Données: {len(price_data)} lignes")
            
            # Couleurs personnalisées par source
            source_colors = {
                'coinmarketcap': '#1f77b4',  # Bleu
                'coingecko': '#ff7f0e',      # Orange  
            }
            
            if chart_type == "Graphique unifié (toutes sources)":
                # Créer une colonne combinée crypto+source pour la légende
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
                    title=f'Comparaison Sources par Crypto ({start_date} au {end_date})',
                    labels={'price': 'Prix (USD)', 'timestamp': 'Temps'},
                    color_discrete_map=source_colors
                )
                fig.update_layout(height=400 * ((len(selected_cryptos) + 1) // 2))
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Graphiques séparés par crypto":
                fig = make_subplots(
                    rows=len(selected_cryptos), 
                    cols=1,
                    subplot_titles=[f"{crypto} - Comparaison Sources" for crypto in selected_cryptos],
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
                        
                    fig.update_yaxes(title_text=f"Prix USD", row=i+1, col=1)
                
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
                    title=f'Variations Relatives Multi-Sources ({start_date} au {end_date})',
                    labels={'price_pct': 'Variation (%)', 'timestamp': 'Temps'}
                )
                fig.update_layout(height=600)
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "Écarts entre sources":
                if len(price_data['source'].unique()) >= 2:
                    # Calculer les écarts de prix entre sources pour chaque crypto
                    st.subheader("🔍 Analyse des Écarts entre Sources")
                    
                    for crypto in selected_cryptos:
                        crypto_data = price_data[price_data['name'] == crypto]
                        
                        if len(crypto_data['source'].unique()) >= 2:
                            # Pivot pour avoir les sources en colonnes
                            pivot_data = crypto_data.pivot_table(
                                values='price', 
                                index='timestamp', 
                                columns='source', 
                                aggfunc='mean'
                            ).reset_index()
                            
                            if len(pivot_data.columns) > 2:  # Au moins 2 sources + timestamp
                                sources_list = [col for col in pivot_data.columns if col != 'timestamp']
                                if len(sources_list) >= 2:
                                    # Calculer l'écart entre la première et la deuxième source
                                    source1, source2 = sources_list[0], sources_list[1]
                                    pivot_data['ecart_abs'] = pivot_data[source1] - pivot_data[source2]
                                    pivot_data['ecart_pct'] = (pivot_data['ecart_abs'] / pivot_data[source1]) * 100
                                    
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        fig_abs = px.line(
                                            pivot_data, 
                                            x='timestamp', 
                                            y='ecart_abs',
                                            title=f'{crypto} - Écart Absolu ({source1} - {source2})',
                                            labels={'ecart_abs': 'Écart (USD)', 'timestamp': 'Temps'}
                                        )
                                        fig_abs.add_hline(y=0, line_dash="dash", line_color="gray")
                                        st.plotly_chart(fig_abs, use_container_width=True)
                                    
                                    with col2:
                                        fig_pct = px.line(
                                            pivot_data, 
                                            x='timestamp', 
                                            y='ecart_pct',
                                            title=f'{crypto} - Écart Relatif (%)',
                                            labels={'ecart_pct': 'Écart (%)', 'timestamp': 'Temps'}
                                        )
                                        fig_pct.add_hline(y=0, line_dash="dash", line_color="gray")
                                        st.plotly_chart(fig_pct, use_container_width=True)
                                    
                                    # Statistiques des écarts
                                    avg_ecart = pivot_data['ecart_abs'].mean()
                                    max_ecart = pivot_data['ecart_abs'].abs().max()
                                    st.metric(f"{crypto} - Écart moyen", f"${avg_ecart:.2f}", f"Max: ${max_ecart:.2f}")
                        else:
                            st.info(f"{crypto}: Une seule source disponible, pas d'écart calculable")
                else:
                    st.warning("Au moins 2 sources nécessaires pour calculer les écarts")
            
        else:
            st.warning("Aucune donnée disponible pour la sélection actuelle.")
            st.info(f"Période: {start_date} à {end_date}")
            st.info(f"Cryptos: {', '.join(selected_cryptos)}")
            st.info(f"Sources: {', '.join(selected_sources)}")
            
    except Exception as e:
        st.error(f"💥 Erreur lors de la récupération des données: {e}")
        with st.expander("Détails de la requête"):
            st.code(query)
else:
    st.info("Veuillez sélectionner au moins une cryptomonnaie et une période valide.")

# Tableau des données récentes multi-sources
st.header("Données Récentes Multi-Sources")
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
        # Formatage des colonnes
        recent_data['price'] = recent_data['price'].apply(lambda x: f"${x:,.2f}")
        recent_data['market_cap'] = recent_data['market_cap'].apply(lambda x: f"${x:,.0f}" if pd.notnull(x) else "N/A")
        recent_data['percent_change_24h'] = recent_data['percent_change_24h'].apply(lambda x: f"{x:+.2f}%" if pd.notnull(x) else "N/A")
        recent_data['source'] = recent_data['source'].apply(lambda x: f"📊 {x.title()}")
        
    st.dataframe(
        recent_data, 
        use_container_width=True,
        column_config={
            "source": st.column_config.TextColumn("Source", help="Source des données"),
            "price": st.column_config.TextColumn("Prix", help="Prix actuel en USD"),
            "percent_change_24h": st.column_config.TextColumn("Δ 24h", help="Variation sur 24h"),
            "market_cap": st.column_config.TextColumn("Market Cap", help="Capitalisation boursière")
        }
    )
except Exception as e:
    st.error(f"💥 Erreur lors du chargement des données récentes: {e}")

# Auto-refresh et statut
col_refresh, col_status = st.columns([1, 2])
with col_refresh:
    if st.button("🔄 Actualiser"):
        st.cache_data.clear()
        st.rerun()

with col_status:
    if latest_update:
        age_seconds = (datetime.now() - latest_update).total_seconds()
        if age_seconds < 300:  # Moins de 5 minutes
            st.success(f"🟢 Multi-Sources Actifs (dernière donnée: {age_seconds:.0f}s)")
        else:
            st.warning(f"🟡 Données anciennes ({age_seconds/60:.0f} min)")
    else:
        st.error("🔴 Aucune donnée multi-sources")

# Footer avec infos techniques
st.markdown("---")
st.markdown("*🔧 Dashboard Multi-Sources - CoinMarketCap & CoinGecko - Mise à jour temps réel*")
