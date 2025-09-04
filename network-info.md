# 🌐 Configuration Réseau CryptoViz avec Redpanda

## 📍 Adresses IP de la machine
- **IP locale**: 192.168.1.76
- **Localhost**: 127.0.0.1

## 🚀 Services Accessibles

### 📊 Dashboard Principal
- **URL**: http://192.168.1.76:8501
- **Local**: http://localhost:8501
- **Description**: Interface Streamlit avec visualisations

### 📡 Streaming Server
- **URL**: http://192.168.1.76:5000
- **Endpoints**:
  - `/stream` - SSE streaming
  - `/health` - Health check
  - `/stats` - Statistiques
  - `/test` - Test manuel

### 🔧 Console Redpanda (Admin)
- **URL**: http://192.168.1.76:8080
- **Description**: Interface web pour administrer Redpanda

### 📈 API Redpanda
- **URL**: http://192.168.1.76:9644
- **Description**: API REST pour monitoring Redpanda

## 🛡️ Firewall (si nécessaire)

Si les services ne sont pas accessibles depuis d'autres machines :

```bash
# Ouvrir les ports sur Ubuntu/Debian
sudo ufw allow 8501 comment 'CryptoViz Dashboard'
sudo ufw allow 5000 comment 'CryptoViz Streaming'
sudo ufw allow 8080 comment 'Redpanda Console'
sudo ufw allow 9644 comment 'Redpanda API'

# Vérifier les règles
sudo ufw status
```

## 🧪 Tests depuis une autre machine

```bash
# Test dashboard (doit retourner du HTML)
curl http://192.168.1.76:8501

# Test streaming server
curl http://192.168.1.76:5000/health | jq '.'

# Test streaming live
curl -N http://192.168.1.76:5000/stream

# Test manual du streaming
curl http://192.168.1.76:5000/test
```

## 📱 Accès Mobile/Tablet

Les services sont accessibles depuis n'importe quel appareil sur le réseau local :
- **Dashboard mobile**: http://192.168.1.76:8501
- **Console admin**: http://192.168.1.76:8080

## 🔄 Docker Network

Les containers communiquent via le réseau `crypto-net`:
- redpanda:9092 (interne)
- 192.168.1.76:19092 (externe)

## 🎯 Avantages de l'IP fixe

✅ **Accès multi-device**: Depuis téléphone, tablet, autre PC
✅ **Demo facile**: Partage de l'URL directement  
✅ **Production-ready**: Configuration prête pour déploiement
✅ **Debug réseau**: Plus facile de tester la connectivité
