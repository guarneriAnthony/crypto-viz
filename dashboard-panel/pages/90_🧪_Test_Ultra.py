"""
🧪 Test Ultra - Page de diagnostic simple
"""

import streamlit as st
import redis
import json
import os

st.set_page_config(page_title="Test Ultra", page_icon="🧪", layout="wide")

st.title("🧪 Test Ultra - Diagnostic Simple")

# Test Redis
st.subheader("1. Connexion Redis")
try:
    client = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)
    client.ping()
    st.success("✅ Redis connecté avec succès")
except Exception as e:
    st.error(f"❌ Redis non connecté: {e}")
    st.stop()

# Test données ultra
st.subheader("2. Données ML Ultra")
try:
    cryptos = client.smembers('ml:ultra:available_cryptos')
    st.info(f"Cryptos ultra disponibles: {list(cryptos)}")
    
    if cryptos:
        ultra_keys = client.keys('ml:ultra:predictions:*')
        st.info(f"Nombre de clés ultra: {len(ultra_keys)}")
        
        # Test une crypto
        test_crypto = list(cryptos)[0]
        key = f'ml:ultra:predictions:{test_crypto}'
        data = client.get(key)
        
        if data:
            parsed_data = json.loads(data)
            st.success(f"✅ Données trouvées pour {test_crypto}")
            
            # Affichage des données principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                current_price = parsed_data.get('current_price', 0)
                st.metric("Prix Actuel", f"${current_price:.4f}")
            
            with col2:
                prediction = parsed_data.get('ensemble_prediction', {})
                pred_value = prediction.get('value', 0)
                st.metric("Prédiction", f"${pred_value:.4f}")
            
            with col3:
                signal = prediction.get('signal', 'N/A')
                confidence = prediction.get('confidence', 0)
                st.metric("Signal", f"{signal} ({confidence:.1%})")
                
            # Test graphique simple
            st.subheader("3. Test Graphique Simple")
            
            historical_prices = parsed_data.get('advanced_analytics', {}).get('historical_prices', [])
            
            if historical_prices:
                st.success(f"✅ Prix historiques trouvés: {len(historical_prices)} points")
                
                # Test graphique Streamlit natif
                import pandas as pd
                df = pd.DataFrame({
                    'Index': range(len(historical_prices)),
                    'Prix': historical_prices
                })
                st.line_chart(df.set_index('Index'))
                
                # Test graphique Plotly
                st.subheader("4. Test Plotly")
                try:
                    import plotly.graph_objects as go
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=list(range(len(historical_prices))),
                        y=historical_prices,
                        mode='lines',
                        name='Prix Historiques',
                        line=dict(color='cyan', width=2)
                    ))
                    
                    fig.update_layout(
                        title=f"Prix Historiques {test_crypto}",
                        xaxis_title="Temps",
                        yaxis_title="Prix ($)",
                        template="plotly_dark",
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    st.success("✅ Graphique Plotly affiché avec succès!")
                    
                except Exception as e:
                    st.error(f"❌ Erreur Plotly: {e}")
                    
            else:
                st.error("❌ Pas de prix historiques dans les données")
                
        else:
            st.error(f"❌ Pas de données pour {test_crypto}")
    else:
        st.error("❌ Aucune crypto ultra disponible")
        
except Exception as e:
    st.error(f"❌ Erreur lors du test des données: {e}")

# Debug complet des données
st.subheader("5. Debug Données Complètes")
if st.button("Afficher données brutes"):
    try:
        test_crypto = list(client.smembers('ml:ultra:available_cryptos'))[0]
        key = f'ml:ultra:predictions:{test_crypto}'
        raw_data = client.get(key)
        if raw_data:
            parsed = json.loads(raw_data)
            st.json(parsed)
    except Exception as e:
        st.error(f"Erreur debug: {e}")
