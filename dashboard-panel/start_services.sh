#!/bin/bash

# Start ML Processor Ultra Historical in background
echo "🚀 Démarrage ML Processor Ultra Historical..."
cd /app/utils
python3 -u ml_processor_ultra_historical.py &
ML_PID=$!
echo "✅ ML Processor Ultra Historical démarré (PID: $ML_PID)"

# Attendre quelques secondes pour que le processeur génère des données
sleep 5

# Start Streamlit
echo "🎮 Démarrage Streamlit Dashboard..."
cd /app
streamlit run streamlit_crypto_home.py --server.port=5008 --server.address=0.0.0.0 &
STREAMLIT_PID=$!

# Trap to handle graceful shutdown
trap "echo 'Arrêt des services...'; kill $ML_PID $STREAMLIT_PID; exit" SIGTERM SIGINT

# Wait for processes
wait $ML_PID $STREAMLIT_PID
