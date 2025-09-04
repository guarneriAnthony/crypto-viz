#!/usr/bin/env python3
"""
Script de débogage pour forcer l'affichage des graphiques
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Désactiver tout cache
st.cache_data.clear()
st.cache_resource.clear()

# Import forcé
sys.path.append('/app/utils')
from parquet_reader_s3fs import ParquetDataReader

st.title("🔧 Debug Dashboard - Graphiques Forcés")

st.markdown("### Test direct des conditions graphiques")

# Instance reader
reader = ParquetDataReader()

# Chargement données
data = reader.read_latest_data(limit=100)

st.write(f"📊 **Données chargées**: {data.shape}")

if data.empty:
    st.error("❌ Aucune donnée!")
    st.stop()

st.write(f"**Colonnes**: {list(data.columns)}")

# Test conditions exactes
has_name = 'name' in data.columns
has_price = 'price' in data.columns
has_timestamp = 'timestamp' in data.columns

st.write(f"- **Has 'name'**: {has_name}")  
st.write(f"- **Has 'price'**: {has_price}")
st.write(f"- **Has 'timestamp'**: {has_timestamp}")

conditions_ok = not data.empty and has_name and has_price
st.write(f"🎯 **Conditions graphiques**: {conditions_ok}")

if conditions_ok:
    st.success("✅ Conditions remplies - Génération graphiques...")
    
    # Graphique 1: Top Cryptos (code exact dashboard)
    st.subheader("📈 Top 10 Cryptos par Prix")
    top_cryptos = data.groupby('name')['price'].last().sort_values(ascending=False).head(10)
    
    fig = px.bar(
        x=top_cryptos.values, 
        y=top_cryptos.index,
        orientation='h',
        title="Top 10 Cryptos par Prix (Debug)",
        labels={'x': 'Prix (USD)', 'y': 'Crypto'}
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)
    
    # Graphique 2: Évolution temporelle
    if has_timestamp:
        st.subheader("📊 Évolution Temporelle")
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        
        crypto_list = sorted(data['name'].unique())
        selected_crypto = st.selectbox("Crypto à analyser", crypto_list)
        
        if selected_crypto:
            crypto_data = data[data['name'] == selected_crypto].sort_values('timestamp')
            
            fig = px.line(
                crypto_data, 
                x='timestamp', 
                y='price',
                title=f"Évolution {selected_crypto} (Debug)",
                color='source' if 'source' in crypto_data.columns else None
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Tableau des données
    st.subheader("🔍 Aperçu Données")
    st.dataframe(data.head(20))

else:
    st.error("❌ Conditions non remplies!")
    st.write("**Détails debug:**")
    st.write(f"- Empty: {data.empty}")
    st.write(f"- Shape: {data.shape}")
    if not data.empty:
        st.dataframe(data.head())

