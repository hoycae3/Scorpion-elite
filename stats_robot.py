"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Usa football-data.co.uk + Soccerway para extraer estadisticas de equipos
"""

import requests
from io import StringIO
import csv
from bs4 import BeautifulSoup
import re
from supabase import create_client
from typing import Dict, List, Optional


SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

# ===== FOOTBALL-DATA.CO.UK =====
FD_LEAGUE_URLS = {
    'Premier League': 'https://www.football-data.co.uk/england.csv',
    'La Liga': 'https://www.football-data.co.uk/spain.csv',
    'Serie A': 'https://www.football-data.co.uk/italy.csv',
    'Bundesliga': 'https://www.football-data.co.uk/germany.csv',
    'Ligue 1': 'https://www.football-data.co.uk/france.csv',
    'Eredivisie': 'https://www.football-data.co.uk/netherlands.csv',
    'Brasileirao': 'https://www.football-data.co.uk/brazil.csv',
    'Liga Argentina': 'https://www.football-data.co.uk/argentina.csv',
    'MLS': 'https://www.football-data.co.uk/usa.csv',
    'Liga MX': 'https://www.football-data.co.uk/mexico.csv',
}

# ===== SOCCERWAY =====
SOCCERWAY_LEAGUES = {
    'Categoria Primera A (Colombia)': 'https://pt.soccerway.com/national/colombia/categoria-primera-a/2024/regular-season/r76545/',
    'Ecuador Serie A': 'https://pt.soccerway.com/national/ecuador/serie-a/2024/regular-season/',
    'Peru Liga 1': 'https://pt.soccerway.com/national/peru/liga-1/2024/regular-season/',
    'Chile Primera': 'https://pt.soccerway.com/national/chile/primera-division/2024/regular-season/',
    'Uruguay Primera': 'https://pt.soccerway.com/national/uruguay/primera-division/2024/regular-season/',
    'Paraguay Primera': 'https://pt.soccerway.com/national/paraguay/primera-division/2024/regular-season/',
    'Bolivia Liga': 'https://pt.soccerway.com/national/bolivia/liga-de-futbol-profesional/2024/regular-season/',
    'Venezuela Primera': 'https://pt.soccerway.com/national/venezuela/primera-division/2024/regular-season/',
    'Costa Rica': 'https://pt.soccerway.com/national/costa-rica/primera-division/2024/regular-season/',
    'Copa Libertadores': 'https://pt.soccerway.com/international-tournaments/south-america/copa-libertadores/2024/group-stage/',
    'Copa Sudamericana': 'https://pt.soccerway.com/international-tournaments/south-america/copa-sudamericana/2024/group-stage/',
}

SOCCERWAY_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Cache
_cached_stats = None


def scrape_soccerway(url: str) -> Dict:
    """Extrae equipos de Soccerway."""
    try:
        response = requests.get(url, headers=SOCCERWAY_HEADERS, timeout=15)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        stats = {}
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    text = ' '.join(cell_texts)
                    
                    match = re.search(r'(\w[\w\s]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+(\w[\w\s]+)', text)
                    if match:
                        team1 = match.group(1).strip()
                        score1 = int(match.group(2))
                        score2 = int(match.group(3))
                        team2 = match.group(4).strip()
                        
                        for team, gf, ga, is_home in [(team1, score1, score2, True), (team2, score2, score1, False)]:
                            if team and len(team) > 2:
                                if team not in stats:
                                    stats[team] = {'gf': 0, 'ga': 0, 'home': 0, 'away': 0}
                                stats[team]['gf'] += gf
                                stats[team]['ga'] += ga
                                if is_home:
                                    stats[team]['home'] += 1
                                else:
                                    stats[team]['away'] += 1
        return stats
    except:
        return {}


def get_all_stats() -> Dict:
    """Obtiene estadisticas de TODAS las ligas (cache)."""
    global _cached_stats
    
    if _cached_stats is not None:
        return _cached_stats
    
    all_stats = {}
    
    # 1. Football-data.co.uk
    for league, url in FD_LEAGUE_URLS.items():
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
                
                for team, gf, ga, is_home in [(home, goals_home, goals_away, True), (away, goals_away, goals_home, False)]:
                    if team not in all_stats:
                        all_stats[team] = {'gf': 0, 'ga': 0, 'home_games': 0, 'away_games': 0, 'league': league}
                    all_stats[team]['gf'] += gf
                    all_stats[team]['ga'] += ga
                    if is_home:
                        all_stats[team]['home_games'] += 1
                    else:
                        all_stats[team]['away_games'] += 1
        except:
            continue
    
    # 2. Soccerway (Latinoamerica)
    for league, url in SOCCERWAY_LEAGUES.items():
        stats = scrape_soccerway(url)
        for team, data in stats.items():
            if team not in all_stats:
                all_stats[team] = {'gf': 0, 'ga': 0, 'home_games': 0, 'away_games': 0, 'league': league}
            all_stats[team]['gf'] += data['gf']
            all_stats[team]['ga'] += data['ga']
            all_stats[team]['home_games'] += data['home']
            all_stats[team]['away_games'] += data['away']
    
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
