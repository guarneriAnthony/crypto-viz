"""
Modèles de prédiction ML simples pour les prix crypto
  CONCEPT : Chaque modèle est une classe avec fit() et predict()
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class MovingAveragePredictor:
    """
    Modèle basé sur les moyennes mobiles
      PRINCIPE : Le prix futur = moyenne des N derniers prix
    """
    
    def __init__(self, window=20):
        self.window = window  # Nombre de points pour la moyenne
        self.last_prices = []
        self.name = f"Moyenne Mobile ({window} points)"
    
    def fit(self, data):
        """
        Entraîner le modèle (ici juste stocker les derniers prix)
          CONCEPT : fit() prépare le modèle avec les données historiques
        """
        if len(data) < self.window:
            raise ValueError(f"Pas assez de données. Besoin de {self.window}, reçu {len(data)}")
        
        # Garder seulement les derniers prix pour prédire
        self.last_prices = data['price'].tail(self.window).tolist()
        return self
    
    def predict(self, steps=1):
        """
        Prédire les prochains prix
          CONCEPT : predict() génère des prédictions futures
        """
        predictions = []
        current_prices = self.last_prices.copy()
        
        for _ in range(steps):
            # Prédiction = moyenne des derniers prix
            next_price = np.mean(current_prices[-self.window:])
            predictions.append(next_price)
            
            # Mettre à jour pour la prochaine prédiction
            current_prices.append(next_price)
        
        return predictions

class LinearTrendPredictor:
    """
    Modèle basé sur une tendance linéaire
      PRINCIPE : Trace une droite sur les derniers prix et l'extraple
    """
    
    def __init__(self, window=50):
        self.window = window
        self.slope = 0
        self.intercept = 0
        self.last_time = 0
        self.name = f"Tendance Linéaire ({window} points)"
    
    def fit(self, data):
        """
        Calcule la tendance (pente) des derniers prix
          CONCEPT : Régression linéaire simple y = ax + b
        """
        if len(data) < self.window:
            raise ValueError(f"Pas assez de données. Besoin de {self.window}, reçu {len(data)}")
        
        recent_data = data.tail(self.window)
        
        # Créer des indices temporels (0, 1, 2, ...)
        x = np.arange(len(recent_data))
        y = recent_data['price'].values
        
        # Calculer la pente (slope) et l'ordonnée à l'origine (intercept)
        self.slope = np.polyfit(x, y, 1)[0]
        self.intercept = y[-1]  # Dernier prix connu
        self.last_time = len(recent_data) - 1
        
        return self
    
    def predict(self, steps=1):
        """
        Extrapoler la tendance dans le futur
          CONCEPT : Continuer la droite : prix_futur = prix_actuel + pente * temps
        """
        predictions = []
        
        for i in range(1, steps + 1):
            # Prédiction = dernier prix + pente * nombre de pas dans le futur
            future_price = self.intercept + (self.slope * i)
            predictions.append(max(0, future_price))  # Prix ne peut pas être négatif
        
        return predictions

class MomentumPredictor:
    """
    Modèle basé sur le momentum (vitesse de changement)
      PRINCIPE : Si ça monte vite, ça va continuer à monter (un peu)
    """
    
    def __init__(self, window=10):
        self.window = window
        self.momentum = 0
        self.last_price = 0
        self.name = f"Momentum ({window} points)"
    
    def fit(self, data):
        """
        Calcule le momentum récent
          CONCEPT : momentum = (prix_actuel - prix_ancien) / temps
        """
        if len(data) < self.window:
            raise ValueError(f"Pas assez de données. Besoin de {self.window}, reçu {len(data)}")
        
        recent_data = data.tail(self.window)
        
        # Momentum = changement moyen par période
        price_changes = recent_data['price'].diff().dropna()
        self.momentum = price_changes.mean()
        self.last_price = recent_data['price'].iloc[-1]
        
        return self
    
    def predict(self, steps=1):
        """
        Applique le momentum aux prédictions futures
          CONCEPT : prix_futur = prix_actuel + momentum * pas_de_temps
        """
        predictions = []
        current_price = self.last_price
        
        for i in range(steps):
            # Appliquer le momentum, mais avec décroissance (momentum s'affaiblit)
            momentum_effect = self.momentum * (0.8 ** i)  # Décroissance exponentielle
            current_price += momentum_effect
            predictions.append(max(0, current_price))
        
        return predictions

def get_all_models():
    """
    Retourne tous les modèles disponibles
      CONCEPT : Factory pattern pour créer facilement différents modèles
    """
    return [
        MovingAveragePredictor(window=20),
        MovingAveragePredictor(window=50),
        LinearTrendPredictor(window=50),
        MomentumPredictor(window=10)
    ]
