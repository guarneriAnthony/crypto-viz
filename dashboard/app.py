import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# Configuration de la page
st.set_page_config(page_title="CryptoViz Dashboard", layout="wide")

# Titre
st.title("📊 CryptoViz Dashboard - Analyse Temps Réel des Cryptomonnaies")

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

# Récupérer la liste des cryptomonnaies avec leurs prix moyens
@st.cache_data(ttl=60)
def get_cryptos_with_prices():
    try:
        conn = get_connection()
        result = conn.execute("""
            SELECT name, AVG(price) as avg_price 
            FROM crypto_prices 
            GROUP BY name 
            ORDER BY avg_price DESC
        """).fetchdf()
        conn.close()
        return result
    except:
        return pd.DataFrame(columns=['name', 'avg_price'])

cryptos_with_prices = get_cryptos_with_prices()
cryptos = cryptos_with_prices['name'].tolist()

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

# Sidebar avec filtres
st.sidebar.header("Filtres")

# Grouper les cryptos par gamme de prix
high_value = cryptos_with_prices[cryptos_with_prices['avg_price'] > 1000]['name'].tolist()
mid_value = cryptos_with_prices[(cryptos_with_prices['avg_price'] > 1) & (cryptos_with_prices['avg_price'] <= 1000)]['name'].tolist()
low_value = cryptos_with_prices[cryptos_with_prices['avg_price'] <= 1]['name'].tolist()

if high_value:
    st.sidebar.info("💰 **Cryptos haute valeur** (>$1000): " + ", ".join(high_value[:3]) + "...")
if mid_value:
    st.sidebar.info("💎 **Cryptos moyenne valeur** ($1-$1000): " + ", ".join(mid_value[:3]) + "...")
if low_value:
    st.sidebar.info("🪙 **Cryptos petite valeur** (<$1): " + ", ".join(low_value[:3]) + "...")

selected_cryptos = st.sidebar.multiselect(
    "Sélectionnez les cryptomonnaies:",
    options=cryptos if cryptos else [],
    default=cryptos[:3] if cryptos else []
)

# Type de graphique
chart_type = st.sidebar.selectbox(
    "Type d'affichage:",
    ["📊 Graphique unique (échelle partagée)", 
     "📈 Graphiques séparés (échelles individuelles)",
     "💹 Vue pourcentage (variations relatives)"]
)

# Période ajustée aux données disponibles
st.sidebar.info(f"📅 Données disponibles du {min_data_date} au {max_data_date}")
date_range = st.sidebar.date_input(
    "Période:",
    value=(min_data_date, max_data_date),
    min_value=min_data_date,
    max_value=max_data_date
)

# Indicateurs Clés
st.header("Indicateurs Clés")
col1, col2, col3 = st.columns(3)

@st.cache_data(ttl=30)
def get_metrics():
    try:
        conn = get_connection()
        total_records = conn.execute("SELECT COUNT(*) FROM crypto_prices").fetchone()[0]
        unique_cryptos = conn.execute("SELECT COUNT(DISTINCT name) FROM crypto_prices").fetchone()[0]
        latest_update = conn.execute("SELECT MAX(timestamp) FROM crypto_prices").fetchone()[0]
        conn.close()
        return total_records, unique_cryptos, latest_update
    except:
        return 0, 0, None

total_records, unique_cryptos, latest_update = get_metrics()

with col1:
    st.metric("Total d'enregistrements", f"{total_records:,}")

with col2:
    st.metric("Cryptomonnaies suivies", unique_cryptos)

with col3:
    if latest_update:
        age_seconds = (datetime.now() - latest_update).total_seconds()
        age_text = f"{latest_update.strftime('%H:%M:%S')} ({age_seconds:.0f}s)"
        st.metric("Dernière mise à jour", age_text)
    else:
        st.metric("Dernière mise à jour", "N/A")

# Graphique des prix
st.header("Évolution des Prix")
if selected_cryptos and len(date_range) == 2:
    start_date, end_date = date_range
    
    # Construction de la requête avec des paramètres sécurisés
    crypto_list = "', '".join(selected_cryptos)
    query = f"""
        SELECT name, price, timestamp 
        FROM crypto_prices 
        WHERE name IN ('{crypto_list}')
        AND timestamp >= '{start_date}' 
        AND timestamp <= '{end_date} 23:59:59'
        ORDER BY timestamp
    """
    
    try:
        conn = get_connection()
        price_data = conn.execute(query).fetchdf()
        conn.close()
        
        if not price_data.empty:
            # Debug info
            st.sidebar.success(f"📊 Données chargées: {len(price_data)} lignes")
            
            if chart_type == "📊 Graphique unique (échelle partagée)":
                fig = px.line(
                    price_data, 
                    x='timestamp', 
                    y='price', 
                    color='name', 
                    title=f'Évolution des Prix ({start_date} au {end_date})',
                    labels={'price': 'Prix (USD)', 'timestamp': 'Temps'}
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
                
                if len(selected_cryptos) > 1:
                    st.info("💡 **Astuce**: Si certaines courbes semblent plates, essayez 'Graphiques séparés' pour mieux voir les variations de chaque crypto.")
                
            elif chart_type == "📈 Graphiques séparés (échelles individuelles)":
                fig = make_subplots(
                    rows=len(selected_cryptos), 
                    cols=1,
                    subplot_titles=selected_cryptos,
                    shared_xaxes=True,
                    vertical_spacing=0.1
                )
                
                colors = px.colors.qualitative.Set1
                for i, crypto in enumerate(selected_cryptos):
                    crypto_data = price_data[price_data['name'] == crypto]
                    fig.add_trace(
                        go.Scatter(
                            x=crypto_data['timestamp'], 
                            y=crypto_data['price'],
                            name=crypto,
                            line=dict(color=colors[i % len(colors)]),
                            mode='lines'
                        ), 
                        row=i+1, col=1
                    )
                    fig.update_yaxes(title_text=f"Prix USD", row=i+1, col=1)
                
                fig.update_layout(
                    height=300 * len(selected_cryptos),
                    title_text=f"Évolutions Individuelles ({start_date} au {end_date})",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            elif chart_type == "💹 Vue pourcentage (variations relatives)":
                price_data_pct = price_data.copy()
                price_data_pct['price_pct'] = price_data_pct.groupby('name')['price'].transform(
                    lambda x: (x / x.iloc[0] - 1) * 100
                )
                
                fig = px.line(
                    price_data_pct, 
                    x='timestamp', 
                    y='price_pct', 
                    color='name', 
                    title=f'Variations Relatives en % ({start_date} au {end_date})',
                    labels={'price_pct': 'Variation (%)', 'timestamp': 'Temps'}
                )
                fig.update_layout(height=600)
                fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                st.plotly_chart(fig, use_container_width=True)
            
            # Prix actuels
            st.subheader("Prix Actuels")
            try:
                conn = get_connection()
                current_prices = conn.execute(f"""
                    SELECT name, price, percent_change_24h 
                    FROM crypto_prices 
                    WHERE name IN ('{crypto_list}')
                    AND timestamp = (SELECT MAX(timestamp) FROM crypto_prices)
                    ORDER BY price DESC
                """).fetchdf()
                conn.close()
                
                if not current_prices.empty:
                    fig2 = px.bar(
                        current_prices, 
                        x='name', 
                        y='price',
                        title='Prix Actuels par Cryptomonnaie',
                        labels={'price': 'Prix (USD)', 'name': 'Cryptomonnaie'},
                        text='price'
                    )
                    fig2.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
                    fig2.update_layout(height=400)
                    st.plotly_chart(fig2, use_container_width=True)
            except Exception as e:
                st.error(f"Erreur prix actuels: {e}")
                
        else:
            st.warning("Aucune donnée disponible pour la sélection actuelle.")
            st.info(f"Période sélectionnée: {start_date} à {end_date}")
            st.info(f"Cryptos sélectionnées: {', '.join(selected_cryptos)}")
            
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données: {e}")
        st.code(query)
else:
    st.info("Veuillez sélectionner au moins une cryptomonnaie et une période valide.")

# Tableau des données récentes
st.header("Données Récentes")
try:
    conn = get_connection()
    recent_data = conn.execute("""
        SELECT name, symbol, price, percent_change_24h, market_cap, timestamp
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
        
    st.dataframe(recent_data, use_container_width=True)
except Exception as e:
    st.error(f"Erreur lors du chargement des données récentes: {e}")

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
            st.success(f"🟢 Streaming actif (dernière donnée: {age_seconds:.0f}s)")
        else:
            st.warning(f"🟡 Données anciennes ({age_seconds/60:.0f} min)")
    else:
        st.error("🔴 Aucune donnée")
