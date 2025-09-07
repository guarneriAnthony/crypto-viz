"""
Test simple de chargement MinIO optimisé - Version rapide sans refaire le container
"""

import streamlit as st
import pandas as pd
import s3fs
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="🔍 Test MinIO Optimisé", layout="wide")

st.title("🔍 Test Chargement MinIO Optimisé")

# Configuration MinIO
minio_endpoint = "http://minio:9000"
minio_access_key = "cryptoviz"
minio_secret_key = "cryptoviz2024"
bucket = "crypto-data-partitioned"

def get_recent_files_only(hours_back=24, max_files=50):
    """Récupère seulement les fichiers récents pour éviter 7000+ fichiers"""
    try:
        fs = s3fs.S3FileSystem(
            endpoint_url=minio_endpoint,
            key=minio_access_key,
            secret=minio_secret_key
        )
        
        # Calculer les dates récentes
        now = datetime.now()
        recent_files = []
        
        # Chercher dans les derniers jours
        for i in range(hours_back // 24 + 2):
            date = now - timedelta(days=i)
            partition_path = f"{bucket}/year={date.year}/month={date.month}/day={date.day}"
            
            try:
                files_in_partition = fs.find(partition_path)
                parquet_files = [f for f in files_in_partition if f.endswith('.parquet')]
                recent_files.extend(parquet_files)
                
                if parquet_files:
                    st.info(f"📁 {date.strftime('%Y-%m-%d')}: {len(parquet_files)} fichiers trouvés")
                    
            except Exception as e:
                st.debug(f"Partition {partition_path} non trouvée: {e}")
                continue
        
        # Limiter le nombre de fichiers
        if len(recent_files) > max_files:
            # Prendre les plus récents (tri par nom contient timestamp)
            sorted_files = sorted(recent_files, reverse=True)
            recent_files = sorted_files[:max_files]
            st.warning(f"⚠️ Limité à {max_files} fichiers les plus récents (sur {len(sorted_files)})")
        
        st.success(f"🎯 {len(recent_files)} fichiers sélectionnés (au lieu de 7000+)")
        return recent_files, fs
        
    except Exception as e:
        st.error(f"❌ Erreur connexion MinIO: {e}")
        return [], None

def load_sample_data(files, fs, max_files_to_read=10):
    """Charge un échantillon des données"""
    try:
        dfs = []
        
        # Prendre seulement les premiers fichiers pour le test
        files_to_read = files[:max_files_to_read]
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, file_path in enumerate(files_to_read):
            try:
                status_text.text(f"📊 Chargement {i+1}/{len(files_to_read)}: {file_path.split('/')[-1]}")
                
                df = pd.read_parquet(f"s3://{file_path}", filesystem=fs)
                
                if not df.empty:
                    dfs.append(df)
                
                progress_bar.progress((i + 1) / len(files_to_read))
                
            except Exception as e:
                st.warning(f"⚠️ Erreur lecture {file_path}: {e}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            
            # Conversion timestamp
            if 'timestamp' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp'])
            elif 'timestamp_dt' in combined_df.columns:
                combined_df['timestamp'] = pd.to_datetime(combined_df['timestamp_dt'])
            
            # Tri par timestamp
            if 'timestamp' in combined_df.columns:
                combined_df = combined_df.sort_values('timestamp')
            
            return combined_df
        
        return pd.DataFrame()
        
    except Exception as e:
        st.error(f"❌ Erreur chargement données: {e}")
        return pd.DataFrame()

# Interface utilisateur
col1, col2 = st.columns(2)

with col1:
    hours_back = st.slider("🕐 Heures d'historique", 1, 72, 24)
    max_files = st.slider("📁 Max fichiers à sélectionner", 10, 200, 50)

with col2:
    max_files_to_read = st.slider("📖 Max fichiers à lire (test)", 1, 20, 10)
    
if st.button("🔍 Tester Chargement Optimisé", use_container_width=True):
    
    start_time = time.time()
    
    with st.spinner("🔍 Récupération des fichiers récents..."):
        files, fs = get_recent_files_only(hours_back, max_files)
    
    if files and fs:
        st.success(f"✅ {len(files)} fichiers récents trouvés en {time.time() - start_time:.1f}s")
        
        with st.spinner(f"📊 Chargement échantillon de {max_files_to_read} fichiers..."):
            load_start = time.time()
            df = load_sample_data(files, fs, max_files_to_read)
            load_time = time.time() - load_start
        
        if not df.empty:
            st.success(f"✅ Données chargées: {len(df)} lignes en {load_time:.1f}s")
            
            # Statistiques
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Lignes", len(df))
            with col2:
                cryptos = df['symbol'].nunique() if 'symbol' in df.columns else 0
                st.metric("💎 Cryptos", cryptos)
            with col3:
                total_time = time.time() - start_time
                st.metric("⏱️ Temps total", f"{total_time:.1f}s")
            
            # Aperçu des données
            st.subheader("📋 Aperçu des Données")
            st.dataframe(df.head(20), use_container_width=True)
            
            # Graphique simple
            if 'symbol' in df.columns and 'price' in df.columns:
                st.subheader("📈 Graphique Simple")
                
                # Top 5 cryptos
                top_cryptos = df['symbol'].value_counts().head(5)
                
                for symbol in top_cryptos.index:
                    symbol_data = df[df['symbol'] == symbol].sort_values('timestamp') if 'timestamp' in df.columns else df[df['symbol'] == symbol]
                    
                    if not symbol_data.empty:
                        st.line_chart(
                            symbol_data.set_index('timestamp' if 'timestamp' in symbol_data.columns else symbol_data.index)['price'],
                            height=200
                        )
                        st.caption(f"💎 {symbol}: {len(symbol_data)} points")
        
        else:
            st.warning("⚠️ Aucune donnée chargée")
    
    else:
        st.error("❌ Impossible de récupérer les fichiers")

# Info de performance
st.markdown("---")
st.info("""
🚀 **Stratégie d'optimisation:**
- 📁 Sélection des fichiers récents seulement (évite 7000+ fichiers)  
- ⏱️ Limitation temporelle (24-72h au lieu de tout l'historique)
- 📊 Échantillonnage intelligent (10-200 fichiers max)
- 🎯 Chargement progressif avec barre de progression
""")
