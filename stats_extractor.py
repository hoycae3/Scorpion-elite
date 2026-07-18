"""
Scorpion Elite - Extractor de Estadísticas de Equipos
====================================================
Extrae estadísticas de equipos desde Soccerway para construir
una base de datos histórica de la temporada.
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional


def get_team_stats_from_soccerway(team_url: str) -> Optional[Dict]:
    """
    Extrae estadísticas de un equipo desde Soccerway.
    
    Args:
        team_url: URL del equipo en Soccerway (ej: /teams/brazil/criciuma/1234/)
    
    Returns:
        Dict con estadísticas o None si falla
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        base_url = "https://pt.soccerway.com"
        url = base_url + team_url if team_url.startswith('/') else team_url
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        stats = {}
        
        # Buscar tabla de estadísticas generales
        tables = soup.find_all('table', class_='grid')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if 'jogos' in label or 'matches' in label:
                        stats['partidos_jugados'] = int(value) if value.isdigit() else 0
                    elif 'vitó' in label or 'wins' in label:
                        stats['victorias'] = int(value) if value.isdigit() else 0
                    elif 'empates' in label or 'draws' in label:
                        stats['empates'] = int(value) if value.isdigit() else 0
                    elif 'derrotas' in label or 'losses' in label:
                        stats['derrotas'] = int(value) if value.isdigit() else 0
                    elif 'golos marcados' in label or 'goals for' in label:
                        stats['goles_favor'] = int(value) if value.isdigit() else 0
                    elif 'golos sofridos' in label or 'goals against' in label:
                        stats['goles_contra'] = int(value) if value.isdigit() else 0
        
        # Buscar estadísticas de la temporada actual
        summary = soup.find('div', class_='season-summary')
        if summary:
            summary_text = summary.get_text()
            
            # Extraer promedios usando regex
            if match := re.search(r'(\d+[\d,\.]*)\s*(?:goles/go\s*)', summary_text):
                stats['promedio_goles'] = float(match.group(1).replace(',', '.'))
        
        return stats if stats else None
        
    except Exception as e:
        print(f"Error extrayendo estadísticas: {e}")
        return None


def get_league_teams_from_soccerway(league_url: str) -> List[Dict]:
    """
    Extrae la lista de equipos de una liga desde Soccerway.
    
    Args:
        league_url: URL de la liga (ej: /national/brazil/brasileirao-serie-a/2024/)
    
    Returns:
        Lista de dicts con nombre y URL de cada equipo
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        base_url = "https://pt.soccerway.com"
        url = base_url + league_url if league_url.startswith('/') else league_url
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        teams = []
        
        # Buscar tabla de equipos
        table = soup.find('table', class_='teams')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                link = row.find('a')
                if link and '/teams/' in str(link.get('href', '')):
                    team_name = link.get_text(strip=True)
                    team_url = link.get('href')
                    if team_name and team_url:
                        teams.append({
                            'nombre': team_name,
                            'url': team_url
                        })
        
        return teams
        
    except Exception as e:
        print(f"Error extrayendo equipos: {e}")
        return []


def calculate_team_lambda(
    goals_for: int, 
    goals_against: int, 
    matches: int,
    is_home: bool = True
) -> float:
    """
    Calcula el lambda (goles esperados) para un equipo.
    
    Args:
        goals_for: Goles marcados en la temporada
        goals_against: Goles recibidos en la temporada
        matches: Partidos jugados
        is_home: True si juega como local
    
    Returns:
        Lambda (promedio de goles esperados)
    """
    if matches <= 0:
        return 1.3  # Valor por defecto
    
    # Promedio de goles por partido
    avg_goals_for = goals_for / matches
    avg_goals_against = goals_against / matches
    
    # Ajustar por local/visitante
    if is_home:
        return round(avg_goals_for * 1.1, 2)  # +10% ventaja local
    else:
        return round(avg_goals_for * 0.85, 2)  # -15% desventaja visitante


def calculate_lambda_from_season_stats(stats: Dict, is_home: bool = True) -> float:
    """
    Calcula lambda directamente desde estadísticas de temporada.
    
    Args:
        stats: Dict con 'goles_favor', 'partidos_jugados'
        is_home: True si juega como local
    
    Returns:
        Lambda calculado
    """
    goals = stats.get('goles_favor', 0)
    matches = stats.get('partidos_jugados', 0)
    
    return calculate_team_lambda(goals, 0, matches, is_home)


def manual_team_stats(equipo: str) -> Dict:
    """
    Retorna estructura vacía para estadísticas manuales.
    El usuario ingresará los datos manualmente en la interfaz.
    """
    return {
        'equipo': equipo,
        'partidos_jugados': 0,
        'victorias': 0,
        'empates': 0,
        'derrotas': 0,
        'goles_favor': 0,
        'goles_contra': 0,
        'lambda_local': 0,
        'lambda_visitante': 0,
        'datos_disponibles': False
    }


def merge_team_stats(stats_local: Dict, stats_away: Dict) -> Dict:
    """
    Combina estadísticas de local y visitante para análisis.
    
    Args:
        stats_local: Estadísticas del equipo local
        stats_away: Estadísticas del equipo visitante
    
    Returns:
        Dict combinado para el análisis
    """
    return {
        'local': {
            'lambda': stats_local.get('lambda_local', 1.3),
            'goles_favor': stats_local.get('goles_favor', 0),
            'partidos': stats_local.get('partidos_jugados', 0),
            'disponible': stats_local.get('datos_disponibles', False)
        },
        'visitante': {
            'lambda': stats_away.get('lambda_visitante', 1.1),
            'goles_favor': stats_away.get('goles_favor', 0),
            'partidos': stats_away.get('partidos_jugados', 0),
            'disponible': stats_away.get('datos_disponibles', False)
        }
    }
