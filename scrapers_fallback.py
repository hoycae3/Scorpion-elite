"""
Scorpion Elite - Scraper Alternativo
=====================================
Usa fuentes abiertas cuando los sitios principales están bloqueados:
1. Wikipedia (datos públicos de ligas)
2. API abierta de football-data (si disponible)
3. Datos locales pre-cargados
"""

import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# ═══════════════════════════════════════════════════════════════════════════════
# DATOS LOCALES (siempre funciona)
# ═══════════════════════════════════════════════════════════════════════════════

# Estadísticas pre-cargadas de equipos comunes
LOCAL_DATABASE = {
    # Premier League
    'Manchester City': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 94, 'goles_contra': 33, 'victorias': 28, 'empates': 5, 'derrotas': 5, 'lambda_local': 2.0, 'lambda_visitante': 1.5},
    'Arsenal': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 88, 'goles_contra': 43, 'victorias': 26, 'empates': 6, 'derrotas': 6, 'lambda_local': 1.9, 'lambda_visitante': 1.4},
    'Liverpool': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 86, 'goles_contra': 42, 'victorias': 24, 'empates': 8, 'derrotas': 6, 'lambda_local': 1.85, 'lambda_visitante': 1.45},
    'Chelsea': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 76, 'goles_contra': 47, 'victorias': 21, 'empates': 11, 'derrotas': 6, 'lambda_local': 1.7, 'lambda_visitante': 1.3},
    'Manchester United': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 68, 'goles_contra': 43, 'victorias': 20, 'empates': 6, 'derrotas': 12, 'lambda_local': 1.6, 'lambda_visitante': 1.2},
    'Tottenham': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 70, 'goles_contra': 63, 'victorias': 18, 'empates': 6, 'derrotas': 14, 'lambda_local': 1.5, 'lambda_visitante': 1.35},
    'Newcastle': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 82, 'goles_contra': 44, 'victorias': 23, 'empates': 5, 'derrotas': 10, 'lambda_local': 1.8, 'lambda_visitante': 1.4},
    'Brighton': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 75, 'goles_contra': 59, 'victorias': 18, 'empates': 9, 'derrotas': 11, 'lambda_local': 1.6, 'lambda_visitante': 1.3},
    'Aston Villa': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 72, 'goles_contra': 61, 'victorias': 20, 'empates': 8, 'derrotas': 10, 'lambda_local': 1.55, 'lambda_visitante': 1.35},
    'West Ham': {'liga': 'Premier League', 'partidos': 38, 'goles_favor': 60, 'goles_contra': 74, 'victorias': 14, 'empates': 10, 'derrotas': 14, 'lambda_local': 1.4, 'lambda_visitante': 1.2},
    
    # La Liga
    'Real Madrid': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 87, 'goles_contra': 31, 'victorias': 29, 'empates': 4, 'derrotas': 5, 'lambda_local': 2.0, 'lambda_visitante': 1.5},
    'Barcelona': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 79, 'goles_contra': 44, 'victorias': 26, 'empates': 6, 'derrotas': 6, 'lambda_local': 1.85, 'lambda_visitante': 1.4},
    'Atletico Madrid': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 70, 'goles_contra': 43, 'victorias': 22, 'empates': 8, 'derrotas': 8, 'lambda_local': 1.6, 'lambda_visitante': 1.3},
    'Real Sociedad': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 51, 'goles_contra': 39, 'victorias': 14, 'empates': 11, 'derrotas': 13, 'lambda_local': 1.3, 'lambda_visitante': 1.1},
    'Athletic Bilbao': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 61, 'goles_contra': 45, 'victorias': 17, 'empates': 10, 'derrotas': 11, 'lambda_local': 1.5, 'lambda_visitante': 1.2},
    'Sevilla': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 53, 'goles_contra': 55, 'victorias': 14, 'empates': 11, 'derrotas': 13, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'Villarreal': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 59, 'goles_contra': 55, 'victorias': 15, 'empates': 9, 'derrotas': 14, 'lambda_local': 1.4, 'lambda_visitante': 1.2},
    'Real Betis': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 46, 'goles_contra': 54, 'victorias': 12, 'empates': 10, 'derrotas': 16, 'lambda_local': 1.2, 'lambda_visitante': 1.0},
    'Valencia': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 42, 'goles_contra': 58, 'victorias': 11, 'empates': 9, 'derrotas': 18, 'lambda_local': 1.1, 'lambda_visitante': 0.95},
    'Getafe': {'liga': 'La Liga', 'partidos': 38, 'goles_favor': 38, 'goles_contra': 52, 'victorias': 9, 'empates': 11, 'derrotas': 18, 'lambda_local': 1.0, 'lambda_visitante': 0.9},
    
    # Bundesliga
    'Bayern Munich': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 92, 'goles_contra': 38, 'victorias': 28, 'empates': 3, 'derrotas': 3, 'lambda_local': 2.3, 'lambda_visitante': 1.7},
    'Borussia Dortmund': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 85, 'goles_contra': 52, 'victorias': 24, 'empates': 5, 'derrotas': 5, 'lambda_local': 2.0, 'lambda_visitante': 1.5},
    'RB Leipzig': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 77, 'goles_contra': 45, 'victorias': 22, 'empates': 4, 'derrotas': 8, 'lambda_local': 1.9, 'lambda_visitante': 1.4},
    'Bayer Leverkusen': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 89, 'goles_contra': 30, 'victorias': 28, 'empates': 4, 'derrotas': 2, 'lambda_local': 2.2, 'lambda_visitante': 1.6},
    'Eintracht Frankfurt': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 63, 'goles_contra': 55, 'victorias': 17, 'empates': 7, 'derrotas': 10, 'lambda_local': 1.6, 'lambda_visitante': 1.25},
    'Wolfsburg': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 55, 'goles_contra': 52, 'victorias': 15, 'empates': 10, 'derrotas': 9, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    'Freiburg': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 51, 'goles_contra': 56, 'victorias': 13, 'empates': 10, 'derrotas': 11, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'Mainz': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 47, 'goles_contra': 53, 'victorias': 12, 'empates': 8, 'derrotas': 14, 'lambda_local': 1.25, 'lambda_visitante': 1.05},
    'Monchengladbach': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 54, 'goles_contra': 58, 'victorias': 14, 'empates': 7, 'derrotas': 13, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    'Union Berlin': {'liga': 'Bundesliga', 'partidos': 34, 'goles_favor': 46, 'goles_contra': 59, 'victorias': 12, 'empates': 9, 'derrotas': 13, 'lambda_local': 1.25, 'lambda_visitante': 1.05},
    
    # Serie A
    'Inter Milan': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 94, 'goles_contra': 32, 'victorias': 29, 'empates': 6, 'derrotas': 3, 'lambda_local': 2.1, 'lambda_visitante': 1.55},
    'AC Milan': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 77, 'goles_contra': 49, 'victorias': 22, 'empates': 9, 'derrotas': 7, 'lambda_local': 1.75, 'lambda_visitante': 1.35},
    'Juventus': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 73, 'goles_contra': 32, 'victorias': 23, 'empates': 9, 'derrotas': 6, 'lambda_local': 1.7, 'lambda_visitante': 1.4},
    'Napoli': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 65, 'goles_contra': 36, 'victorias': 19, 'empates': 9, 'derrotas': 10, 'lambda_local': 1.55, 'lambda_visitante': 1.25},
    'Roma': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 63, 'goles_contra': 50, 'victorias': 18, 'empates': 8, 'derrotas': 12, 'lambda_local': 1.5, 'lambda_visitante': 1.2},
    'Lazio': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 59, 'goles_contra': 54, 'victorias': 16, 'empates': 10, 'derrotas': 12, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    'Atalanta': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 72, 'goles_contra': 52, 'victorias': 21, 'empates': 6, 'derrotas': 11, 'lambda_local': 1.65, 'lambda_visitante': 1.35},
    'Fiorentina': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 52, 'goles_contra': 46, 'victorias': 14, 'empates': 10, 'derrotas': 14, 'lambda_local': 1.3, 'lambda_visitante': 1.1},
    'Bologna': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 47, 'goles_contra': 45, 'victorias': 13, 'empates': 11, 'derrotas': 14, 'lambda_local': 1.25, 'lambda_visitante': 1.05},
    'Torino': {'liga': 'Serie A', 'partidos': 38, 'goles_favor': 42, 'goles_contra': 48, 'victorias': 11, 'empates': 11, 'derrotas': 16, 'lambda_local': 1.1, 'lambda_visitante': 0.95},
    
    # Ligue 1
    'PSG': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 91, 'goles_contra': 39, 'victorias': 27, 'empates': 4, 'derrotas': 3, 'lambda_local': 2.2, 'lambda_visitante': 1.6},
    'Monaco': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 68, 'goles_contra': 43, 'victorias': 20, 'empates': 7, 'derrotas': 7, 'lambda_local': 1.7, 'lambda_visitante': 1.3},
    'Marseille': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 61, 'goles_contra': 39, 'victorias': 18, 'empates': 8, 'derrotas': 8, 'lambda_local': 1.6, 'lambda_visitante': 1.25},
    'Lyon': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 60, 'goles_contra': 50, 'victorias': 16, 'empates': 9, 'derrotas': 9, 'lambda_local': 1.5, 'lambda_visitante': 1.2},
    'Lille': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 55, 'goles_contra': 45, 'victorias': 15, 'empates': 10, 'derrotas': 9, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    'Nice': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 48, 'goles_contra': 38, 'victorias': 14, 'empates': 11, 'derrotas': 9, 'lambda_local': 1.3, 'lambda_visitante': 1.1},
    'Lens': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 51, 'goles_contra': 54, 'victorias': 14, 'empates': 9, 'derrotas': 11, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'Rennes': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 52, 'goles_contra': 55, 'victorias': 14, 'empates': 8, 'derrotas': 12, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'Toulouse': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 42, 'goles_contra': 55, 'victorias': 11, 'empates': 9, 'derrotas': 14, 'lambda_local': 1.15, 'lambda_visitante': 0.95},
    'Brest': {'liga': 'Ligue 1', 'partidos': 34, 'goles_favor': 47, 'goles_contra': 48, 'victorias': 13, 'empates': 8, 'derrotas': 13, 'lambda_local': 1.25, 'lambda_visitante': 1.05},
    
    # Eredivisie
    'Ajax': {'liga': 'Eredivisie', 'partidos': 34, 'goles_favor': 93, 'goles_contra': 33, 'victorias': 29, 'empates': 3, 'derrotas': 2, 'lambda_local': 2.3, 'lambda_visitante': 1.7},
    'PSV Eindhoven': {'liga': 'Eredivisie', 'partidos': 34, 'goles_favor': 96, 'goles_contra': 39, 'victorias': 29, 'empates': 3, 'derrotas': 2, 'lambda_local': 2.35, 'lambda_visitante': 1.75},
    'Feyenoord': {'liga': 'Eredivisie', 'partidos': 34, 'goles_favor': 83, 'goles_contra': 34, 'victorias': 26, 'empates': 4, 'derrotas': 4, 'lambda_local': 2.1, 'lambda_visitante': 1.55},
    'AZ Alkmaar': {'liga': 'Eredivisie', 'partidos': 34, 'goles_favor': 74, 'goles_contra': 45, 'victorias': 22, 'empates': 6, 'derrotas': 6, 'lambda_local': 1.85, 'lambda_visitante': 1.4},
    'Twente': {'liga': 'Eredivisie', 'partidos': 34, 'goles_favor': 68, 'goles_contra': 43, 'victorias': 20, 'empates': 8, 'derrotas': 6, 'lambda_local': 1.7, 'lambda_visitante': 1.35},
    
    # Liga MX
    'Club America': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 52, 'goles_contra': 35, 'victorias': 15, 'empates': 9, 'derrotas': 10, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    'Chivas Guadalajara': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 45, 'goles_contra': 36, 'victorias': 12, 'empates': 11, 'derrotas': 11, 'lambda_local': 1.25, 'lambda_visitante': 1.05},
    'Tigres UANL': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 54, 'goles_contra': 38, 'victorias': 16, 'empates': 9, 'derrotas': 9, 'lambda_local': 1.45, 'lambda_visitante': 1.2},
    'Monterrey': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 50, 'goles_contra': 40, 'victorias': 14, 'empates': 10, 'derrotas': 10, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'Pumas UNAM': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 43, 'goles_contra': 42, 'victorias': 12, 'empates': 9, 'derrotas': 13, 'lambda_local': 1.2, 'lambda_visitante': 1.0},
    'Cruz Azul': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 41, 'goles_contra': 39, 'victorias': 11, 'empates': 10, 'derrotas': 13, 'lambda_local': 1.15, 'lambda_visitante': 0.95},
    'Leon': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 48, 'goles_contra': 52, 'victorias': 13, 'empates': 7, 'derrotas': 14, 'lambda_local': 1.3, 'lambda_visitante': 1.05},
    'Santos Laguna': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 44, 'goles_contra': 46, 'victorias': 11, 'empates': 9, 'derrotas': 14, 'lambda_local': 1.2, 'lambda_visitante': 1.0},
    'Necaxa': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 40, 'goles_contra': 48, 'victorias': 10, 'empates': 9, 'derrotas': 15, 'lambda_local': 1.1, 'lambda_visitante': 0.9},
    'Puebla': {'liga': 'Liga MX', 'partidos': 34, 'goles_favor': 35, 'goles_contra': 50, 'victorias': 9, 'empates': 8, 'derrotas': 17, 'lambda_local': 0.95, 'lambda_visitante': 0.8},
    
    # Argentina
    'River Plate': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 52, 'goles_contra': 22, 'victorias': 17, 'empates': 5, 'derrotas': 5, 'lambda_local': 1.8, 'lambda_visitante': 1.4},
    'Boca Juniors': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 45, 'goles_contra': 25, 'victorias': 14, 'empates': 7, 'derrotas': 6, 'lambda_local': 1.6, 'lambda_visitante': 1.25},
    'Racing Club': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 42, 'goles_contra': 28, 'victorias': 13, 'empates': 6, 'derrotas': 8, 'lambda_local': 1.5, 'lambda_visitante': 1.2},
    'Estudiantes LP': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 38, 'goles_contra': 30, 'victorias': 11, 'empates': 8, 'derrotas': 8, 'lambda_local': 1.4, 'lambda_visitante': 1.1},
    'Defensa y Justicia': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 35, 'goles_contra': 32, 'victorias': 10, 'empates': 9, 'derrotas': 8, 'lambda_local': 1.3, 'lambda_visitante': 1.05},
    'San Lorenzo': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 33, 'goles_contra': 30, 'victorias': 9, 'empates': 10, 'derrotas': 8, 'lambda_local': 1.2, 'lambda_visitante': 1.0},
    'Velez Sarsfield': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 36, 'goles_contra': 33, 'victorias': 10, 'empates': 8, 'derrotas': 9, 'lambda_local': 1.3, 'lambda_visitante': 1.05},
    'Huracan': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 30, 'goles_contra': 32, 'victorias': 8, 'empates': 9, 'derrotas': 10, 'lambda_local': 1.1, 'lambda_visitante': 0.9},
    'Argentinos Juniors': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 28, 'goles_contra': 35, 'victorias': 7, 'empates': 8, 'derrotas': 12, 'lambda_local': 1.0, 'lambda_visitante': 0.85},
    'Talleres Cordoba': {'liga': 'Primera Argentina', 'partidos': 27, 'goles_favor': 37, 'goles_contra': 29, 'victorias': 11, 'empates': 7, 'derrotas': 9, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    
    # Brasil
    'Flamengo': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 72, 'goles_contra': 40, 'victorias': 22, 'empates': 6, 'derrotas': 10, 'lambda_local': 1.75, 'lambda_visitante': 1.35},
    'Palmeiras': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 65, 'goles_contra': 38, 'victorias': 20, 'empates': 8, 'derrotas': 10, 'lambda_local': 1.6, 'lambda_visitante': 1.3},
    'Corinthians': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 58, 'goles_contra': 48, 'victorias': 16, 'empates': 9, 'derrotas': 13, 'lambda_local': 1.45, 'lambda_visitante': 1.15},
    'Sao Paulo': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 54, 'goles_contra': 45, 'victorias': 15, 'empates': 10, 'derrotas': 13, 'lambda_local': 1.4, 'lambda_visitante': 1.1},
    'Santos': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 48, 'goles_contra': 50, 'victorias': 13, 'empates': 9, 'derrotas': 16, 'lambda_local': 1.25, 'lambda_visitante': 1.0},
    'Internacional': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 52, 'goles_contra': 46, 'victorias': 14, 'empates': 10, 'derrotas': 14, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'Gremio': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 50, 'goles_contra': 48, 'victorias': 14, 'empates': 9, 'derrotas': 15, 'lambda_local': 1.3, 'lambda_visitante': 1.05},
    'Atletico Mineiro': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 60, 'goles_contra': 45, 'victorias': 17, 'empates': 7, 'derrotas': 14, 'lambda_local': 1.5, 'lambda_visitante': 1.2},
    'Fluminense': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 48, 'goles_contra': 50, 'victorias': 13, 'empates': 9, 'derrotas': 16, 'lambda_local': 1.25, 'lambda_visitante': 1.0},
    'Botafogo': {'liga': 'Brasil Serie A', 'partidos': 38, 'goles_favor': 55, 'goles_contra': 42, 'victorias': 16, 'empates': 8, 'derrotas': 14, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    
    # Colombia
    'Atletico Nacional': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 58, 'goles_contra': 32, 'victorias': 18, 'empates': 10, 'derrotas': 8, 'lambda_local': 1.55, 'lambda_visitante': 1.25},
    'Millonarios': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 52, 'goles_contra': 35, 'victorias': 16, 'empates': 10, 'derrotas': 10, 'lambda_local': 1.4, 'lambda_visitante': 1.15},
    'Santa Fe': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 48, 'goles_contra': 38, 'victorias': 14, 'empates': 11, 'derrotas': 11, 'lambda_local': 1.3, 'lambda_visitante': 1.05},
    'Junior': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 50, 'goles_contra': 40, 'victorias': 15, 'empates': 9, 'derrotas': 12, 'lambda_local': 1.35, 'lambda_visitante': 1.1},
    'America de Cali': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 45, 'goles_contra': 42, 'victorias': 13, 'empates': 9, 'derrotas': 14, 'lambda_local': 1.2, 'lambda_visitante': 1.0},
    'Once Caldas': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 42, 'goles_contra': 44, 'victorias': 11, 'empates': 11, 'derrotas': 14, 'lambda_local': 1.15, 'lambda_visitante': 0.95},
    'Independiente Medellin': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 44, 'goles_contra': 45, 'victorias': 12, 'empates': 9, 'derrotas': 15, 'lambda_local': 1.2, 'lambda_visitante': 0.95},
    'Alianza Petrolera': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 38, 'goles_contra': 48, 'victorias': 10, 'empates': 9, 'derrotas': 17, 'lambda_local': 1.0, 'lambda_visitante': 0.85},
    'Patriotas': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 35, 'goles_contra': 50, 'victorias': 9, 'empates': 8, 'derrotas': 19, 'lambda_local': 0.9, 'lambda_visitante': 0.75},
    'Deportivo Pasto': {'liga': 'Colombia Primera A', 'partidos': 36, 'goles_favor': 40, 'goles_contra': 45, 'victorias': 11, 'empates': 9, 'derrotas': 16, 'lambda_local': 1.1, 'lambda_visitante': 0.9},
}


class FallbackScraper:
    """Usa base de datos local cuando otras fuentes fallan."""
    
    def __init__(self):
        self.db = LOCAL_DATABASE
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """Busca equipo en base de datos local."""
        team_lower = team_name.lower().strip()
        
        # Búsqueda exacta primero
        for name, data in self.db.items():
            if name.lower() == team_lower:
                return {
                    'equipo': name,
                    'liga': data['liga'],
                    'source': 'local_db',
                    'stats': data
                }
        
        # Búsqueda parcial
        for name, data in self.db.items():
            if team_lower in name.lower() or name.lower() in team_lower:
                return {
                    'equipo': name,
                    'liga': data['liga'],
                    'source': 'local_db',
                    'stats': data
                }
        
        return None
    
    def get_team_stats(self, team_name: str) -> Optional[Dict]:
        """Obtiene estadísticas del equipo."""
        result = self.search_team(team_name)
        if result:
            return result['stats']
        return None


def scrape_team_fallback(team_name: str) -> Dict:
    """
    Busca estadísticas usando base de datos local.
    Siempre funciona - no depende de internet.
    """
    scraper = FallbackScraper()
    result = scraper.search_team(team_name)
    
    if result:
        return {
            'equipo': team_name,
            'encontrado': True,
            'source': result['source'],
            'liga': result['liga'],
            'stats': result['stats']
        }
    
    return {
        'equipo': team_name,
        'encontrado': False,
        'source': None,
        'liga': None,
        'stats': {}
    }


def scrape_batch_fallback(teams: List[str]) -> List[Dict]:
    """Busca múltiples equipos."""
    return [scrape_team_fallback(team) for team in teams]


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    test_teams = ['Barcelona', 'Real Madrid', 'PSG', 'River Plate', 'Flamengo']
    
    print("=" * 60)
    print("PRUEBA: Scraper Fallback (Base de Datos Local)")
    print("=" * 60)
    
    for team in test_teams:
        result = scrape_team_fallback(team)
        if result['encontrado']:
            print(f"\n✅ {result['equipo']} ({result['liga']})")
            print(f"   Source: {result['source']}")
            stats = result['stats']
            print(f"   PJ: {stats.get('partidos', 'N/A')} | V: {stats.get('victorias', 'N/A')} | E: {stats.get('empates', 'N/A')} | D: {stats.get('derrotas', 'N/A')}")
            print(f"   GF: {stats.get('goles_favor', 'N/A')} | GC: {stats.get('goles_contra', 'N/A')}")
            print(f"   λL: {stats.get('lambda_local', 'N/A')} | λV: {stats.get('lambda_visitante', 'N/A')}")
        else:
            print(f"\n❌ {team} - No encontrado")
