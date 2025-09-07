#!/usr/bin/env python3
"""
Composant pour les mini-graphiques sparkline
Graphiques de tendance compacts pour l'affichage dans le tableau
"""

import pandas as pd
import numpy as np
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.io import curdoc
from bokeh.layouts import row, column
import logging

logger = logging.getLogger(__name__)

class SparklineGenerator:
    """Générateur de mini-graphiques sparkline pour les données crypto"""
    
    def __init__(self, width=120, height=50):
        self.width = width
        self.height = height
        
    def create_price_sparkline(self, price_history, symbol="", positive_color="#26a69a", negative_color="#ef5350"):
        """
        Crée un sparkline pour l'évolution des prix
        
        Args:
            price_history: Liste ou array des prix historiques
            symbol: Symbole de la crypto (pour debug)
            positive_color: Couleur pour tendance positive
            negative_color: Couleur pour tendance négative
        
        Returns:
            Bokeh figure ou None
        """
        
        if not price_history or len(price_history) < 2:
            return self._create_empty_sparkline()
        
        try:
            # Préparation des données
            prices = list(price_history)
            x_values = list(range(len(prices)))
            
            # Déterminer la couleur selon la tendance
            trend_color = positive_color if prices[-1] >= prices[0] else negative_color
            
            # Créer la figure
            p = figure(
                width=self.width,
                height=self.height,
                toolbar_location=None,
                x_axis_type=None,
                y_axis_type=None,
                background_fill_color='transparent',
                border_fill_color='transparent',
                margin=(2, 2, 2, 2)
            )
            
            # Masquer tous les éléments de l'interface
            p.grid.visible = False
            p.outline_line_color = None
            p.xaxis.visible = False
            p.yaxis.visible = False
            p.min_border = 0
            p.toolbar.logo = None
            
            # Ligne principale du sparkline
            p.line(
                x_values, 
                prices, 
                line_width=2.5, 
                color=trend_color, 
                alpha=0.9,
                line_cap='round'
            )
            
            # Zone remplie sous la courbe (subtle)
            if len(prices) > 2:
                min_price = min(prices)
                p.varea(
                    x_values, 
                    [min_price] * len(prices), 
                    prices, 
                    color=trend_color, 
                    alpha=0.15
                )
            
            # Point final (indicateur de valeur actuelle)
            p.circle(
                x_values[-1], 
                prices[-1], 
                size=4, 
                color=trend_color, 
                alpha=0.8
            )
            
            return p
            
        except Exception as e:
            logger.error(f"Erreur création sparkline pour {symbol}: {e}")
            return self._create_empty_sparkline()
    
    def create_volume_sparkline(self, volume_history, symbol=""):
        """
        Crée un sparkline pour l'évolution du volume
        Utilise une couleur bleue pour le volume
        """
        
        if not volume_history or len(volume_history) < 2:
            return self._create_empty_sparkline()
        
        try:
            volumes = list(volume_history)
            x_values = list(range(len(volumes)))
            
            p = figure(
                width=self.width,
                height=self.height,
                toolbar_location=None,
                x_axis_type=None,
                y_axis_type=None,
                background_fill_color='transparent',
                border_fill_color='transparent'
            )
            
            # Configuration similaire
            p.grid.visible = False
            p.outline_line_color = None
            p.xaxis.visible = False
            p.yaxis.visible = False
            p.min_border = 0
            
            # Graphique en barres pour le volume
            p.vbar(
                x=x_values,
                top=volumes,
                width=0.8,
                color='#2196f3',
                alpha=0.7
            )
            
            return p
            
        except Exception as e:
            logger.error(f"Erreur création sparkline volume pour {symbol}: {e}")
            return self._create_empty_sparkline()
    
    def _create_empty_sparkline(self):
        """Crée un sparkline vide en cas d'erreur ou données insuffisantes"""
        
        p = figure(
            width=self.width,
            height=self.height,
            toolbar_location=None,
            x_axis_type=None,
            y_axis_type=None,
            background_fill_color='transparent',
            border_fill_color='transparent'
        )
        
        p.grid.visible = False
        p.outline_line_color = None
        p.xaxis.visible = False
        p.yaxis.visible = False
        p.min_border = 0
        
        # Ligne plate grise pour indiquer "pas de données"
        p.line([0, 10], [0, 0], line_width=1, color='#666666', alpha=0.5)
        
        return p
    
    def create_change_indicator_sparkline(self, change_percentage):
        """
        Crée un mini-indicateur visuel pour le pourcentage de changement
        Plus simple qu'un graphique complet
        """
        
        try:
            # Couleur basée sur le changement
            color = '#26a69a' if change_percentage >= 0 else '#ef5350'
            
            p = figure(
                width=60,
                height=30,
                toolbar_location=None,
                x_axis_type=None,
                y_axis_type=None,
                background_fill_color='transparent',
                border_fill_color='transparent'
            )
            
            p.grid.visible = False
            p.outline_line_color = None
            p.xaxis.visible = False
            p.yaxis.visible = False
            p.min_border = 0
            
            # Flèche simple basée sur le signe
            if change_percentage > 0:
                # Flèche vers le haut
                p.triangle([0], [0], size=15, color=color, alpha=0.8, angle=0)
            elif change_percentage < 0:
                # Flèche vers le bas
                p.inverted_triangle([0], [0], size=15, color=color, alpha=0.8, angle=0)
            else:
                # Ligne plate
                p.line([-1, 1], [0, 0], line_width=3, color='#666666')
            
            return p
            
        except Exception as e:
            logger.error(f"Erreur création indicateur changement: {e}")
            return None

def generate_sample_price_history(base_price, days=7, volatility=0.1):
    """
    Génère un historique de prix échantillon pour les tests
    
    Args:
        base_price: Prix de base
        days: Nombre de jours d'historique
        volatility: Volatilité des prix (0.1 = 10%)
    
    Returns:
        Liste des prix
    """
    
    prices = [base_price]
    
    for i in range(1, days):
        # Simulation d'une marche aléatoire avec tendance
        change = np.random.normal(0, volatility)
        new_price = prices[-1] * (1 + change)
        prices.append(max(new_price, base_price * 0.5))  # Prix minimum
    
    return prices

# Test de fonctionnement
if __name__ == "__main__":
    sparkline_gen = SparklineGenerator()
    
    # Test avec données échantillon
    sample_prices = generate_sample_price_history(50000, 7, 0.05)
    sparkline = sparkline_gen.create_price_sparkline(sample_prices, "BTC")
    
    if sparkline:
        print("Sparkline créé avec succès")
        # sparkline.show()  # Décommentez pour voir le résultat
    else:
        print("Erreur lors de la création du sparkline")
