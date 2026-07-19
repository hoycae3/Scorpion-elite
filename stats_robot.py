"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Usa football-data.co.uk para extraer estadisticas de equipos
"""

import requests
from io import StringIO
import csv
from supabase import create_client
from typing import Dict, List, Optional


SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

# TODAS las ligas disponibles en football-data.co.uk
LEAGUE_URLS = {
    # Inglaterra
    'Premier League': 'https://www.football-data.co.uk/england.csv',
    'Championship': 'https://www.football-data.co.uk/england.csv',
    'League One': 'https://www.football-data.co.uk/england.csv',
    
    # Espana
    'La Liga': 'https://www.football-data.co.uk/spain.csv',
    'Segunda Division': 'https://www.football-data.co.uk/spain.csv',
    
    # Italia
    'Serie A': 'https://www.football-data.co.uk/italy.csv',
    'Serie B': 'https://www.football-data.co.uk/italy.csv',
    
    # Alemania
    'Bundesliga': 'https://www.football-data.co.uk/germany.csv',
    '2 Bundesliga': 'https://www.football-data.co.uk/germany.csv',
    
    # Francia
    'Ligue 1': 'https://www.football-data.co.uk/france.csv',
    'Ligue 2': 'https://www.football-data.co.uk/france.csv',
    
    # Paises Bajos
    'Eredivisie': 'https://www.football-data.co.uk/netherlands.csv',
    'Eerste Divisie': 'https://www.football-data.co.uk/netherlands.csv',
    
    # Belgica
    'Jupiler Pro League': 'https://www.football-data.co.uk/belgium.csv',
    
    # Portugal
    'Primeira Liga': 'https://www.football-data.co.uk/portugal.csv',
    
    # Grecia
    'Super League': 'https://www.football-data.co.uk/greece.csv',
    
    # TurquÃ­a
    'Super Lig': 'https://www.football-data.co.uk/turkey.csv',
    
    # Rusia
    'Premier League Rusia': 'https://www.football-data.co.uk/russia.csv',
    
    # Brasil
    'Brasileirao': 'https://www.football-data.co.uk/brazil.csv',
    
    # Argentina
    'Liga Argentina': 'https://www.football-data.co.uk/argentina.csv',
    
    # Mexico
    'Liga MX': 'https://www.football-data.co.uk/mexico.csv',
    
    # USA
    'MLS': 'https://www.football-data.co.uk/usa.csv',
    
    # Austria
    'Bundesliga Austria': 'https://www.football-data.co.uk/austria.csv',
    
    # Republica Checa
    'Czech Liga': 'https://www.football-data.co.uk/czech.csv',
    
    # Dinamarca
    'Superliga': 'https://www.football-data.co.uk/denmark.csv',
    
    # Finlandia
    'Veikkausliiga': 'https://www.football-data.co.uk/finland.csv',
    
    # Hungria
    'NB I': 'https://www.football-data.co.uk/hungary.csv',
    
    # Irlanda
    'Premier Division': 'https://www.football-data.co.uk/ireland.csv',
    
    # Noruega
    'Eliteserien': 'https://www.football-data.co.uk/norway.csv',
    
    # Polonia
    'Ekstraklasa': 'https://www.football-data.co.uk/poland.csv',
    
    # Romania
    'Liga I': 'https://www.football-data.co.uk/romania.csv',
    
    # EscoCia
    'Premiership': 'https://www.football-data.co.uk/scotland.csv',
    
    # Suecia
    'Allsvenskan': 'https://www.football-data.co.uk/sweden.csv',
    
    # Suiza
    'Super League': 'https://www.football-data.co.uk/switzerland.csv',
    
    # Ukrania
    'Premier League Ukrania': 'https://www.football-data.co.uk/ukraine.csv',
}

# Equipos en cache
_cached_stats = None


def get_all_stats() -> Dict:
    """Obtiene estadisticas de TODAS las ligas (cache)."""
    global _cached_stats
    
    if _cached_stats is not None:
        return _cached_stats
    
    all_stats = {}
    
    for league, url in LEAGUE_URLS.items():
        try:
            response = requests.get(url, timeout=15)
            if response.status_code != 200:
                continue
            
            reader = csv.DictReader(StringIO(response.text))
            
            for row in reader:
                home = row.get('HomeTeam', '').strip()
                away = row.get('AwayTeam', '').strip()
                fthg = row.get('FTHG')
                ftag = row.get('FTAG')
                
                if not home or not fthg or not ftag:
                    continue
                
                try:
                    goals_home = int(fthg)
                    goals_away = int(ftag)
                except:
                    continue
                
                # Acumular para cada equipo
                for team, gf, ga, is_home in [(home, goals_home, goals_away, True), (away, goals_away, goals_home, False)]:
                    if team not in all_stats:
                        all_stats[team] = {'gf': 0, 'ga': 0, 'home_games': 0, 'away_games': 0, 'league': league}
                    
                    all_stats[team]['gf'] += gf
                    all_stats[team]['ga'] += ga
                    if is_home:
                        all_stats[team]['home_games'] += 1
                    else:
                        all_stats[team]['away_games'] += 1
                        
        except Exception as e:
            print(f"Error {league}: {e}")
            continue
    
    _cached_stats = all_stats
    return all_stats


def clear_cache():
    """Limpia el cache de estadisticas."""
    global _cached_stats
    _cached_stats = None


def search_team(team_name: str) -> Optional[Dict]:
    """Busca un equipo por nombre y retorna sus estadisticas."""
    
    all_stats = get_all_stats()
    team_name_lower = team_name.lower()
    
    # Buscar coincidencia parcial
    for team, data in all_stats.items():
        if team_name_lower in team.lower() or team.lower() in team_name_lower:
            return {
                'equipo': team,
                'liga': data['league'],
                'partidos_local': data['home_games'],
                'partidos_visitante': data['away_games'],
                'goles_favor': data['gf'],
                'goles_contra': data['ga'],
            }
    
    return None


def calculate_lambda(gf: int, games: int, is_home: bool = True) -> float:
    if games == 0:
        return 0.0
    avg = gf / games
    if is_home:
        return round(avg * 1.1, 2)
    else:
        return round(avg * 0.85, 2)


def run_robot_for_team(team_name: str) -> Dict:
    """Busca un equipo y guarda sus estadisticas."""
    
    print(f"Buscando: {team_name}")
    
    team_data = search_team(team_name)
    
    if not team_data:
        return {'equipo': team_name, 'encontrado': False, 'exito': False}
    
    print(f"Encontrado: {team_data['equipo']} ({team_data['liga']})")
    
    lambda_local = calculate_lambda(
        team_data['goles_favor'], 
        team_data['partidos_local'], 
        True
    )
    lambda_visitante = calculate_lambda(
        team_data['goles_favor'], 
        team_data['partidos_visitante'], 
        False
    )
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    data = {
        'equipo': team_data['equipo'],
        'liga': team_data['liga'],
        'partidos_jugados': team_data['partidos_local'] + team_data['partidos_visitante'],
        'goles_favor': team_data['goles_favor'],
        'goles_contra': team_data['goles_contra'],
        'lambda_local': lambda_local,
        'lambda_visitante': lambda_visitante,
    }
    
    try:
        client.table('estadisticas_equipos').upsert(data, on_conflict='equipo').execute()
        return {
            'equipo': team_data['equipo'],
            'liga': team_data['liga'],
            'lambda_local': lambda_local,
            'lambda_visitante': lambda_visitante,
            'partidos': data['partidos_jugados'],
            'encontrado': True,
            'exito': True
        }
    except Exception as e:
        return {'equipo': team_name, 'encontrado': True, 'exito': False, 'error': str(e)}


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """Busca multiples equipos."""
    results = []
    for team in team_names:
        result = run_robot_for_team(team)
        results.append(result)
    return results
