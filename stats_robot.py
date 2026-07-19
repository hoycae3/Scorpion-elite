"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Busca equipos en MULTIPLES fuentes:
1. football-data.co.uk
2. Soccerway
3. TheSportsDB
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

SOCCERWAY_LEAGUES = {
    'Colombia Primera A': 'https://pt.soccerway.com/national/colombia/categoria-primera-a/2024/regular-season/r76545/',
    'Colombia Primera B': 'https://pt.soccerway.com/national/colombia/categoria-primera-b/2024/regular-season/',
    'Ecuador': 'https://pt.soccerway.com/national/ecuador/serie-a/2024/regular-season/',
    'Peru': 'https://pt.soccerway.com/national/peru/liga-1/2024/regular-season/',
    'Chile': 'https://pt.soccerway.com/national/chile/primera-division/2024/regular-season/',
    'Uruguay': 'https://pt.soccerway.com/national/uruguay/primera-division/2024/regular-season/',
    'Paraguay': 'https://pt.soccerway.com/national/paraguay/primera-division/2024/regular-season/',
    'Bolivia': 'https://pt.soccerway.com/national/bolivia/liga-de-futbol-profesional/2024/regular-season/',
    'Venezuela': 'https://pt.soccerway.com/national/venezuela/primera-division/2024/regular-season/',
    'Costa Rica': 'https://pt.soccerway.com/national/costa-rica/primera-division/2024/regular-season/',
    'Guatemala': 'https://pt.soccerway.com/national/guatemala/liga-nacional/2024/regular-season/',
    'Honduras': 'https://pt.soccerway.com/national/honduras/liguilla/2024/regular-season/',
    'El Salvador': 'https://pt.soccerway.com/national/el-salvador/primera-division/2024/regular-season/',
    'Panama': 'https://pt.soccerway.com/national/panama/lpf/2024/regular-season/',
    'Copa Libertadores': 'https://pt.soccerway.com/international-tournaments/south-america/copa-libertadores/2024/group-stage/',
    'Copa Sudamericana': 'https://pt.soccerway.com/international-tournaments/south-america/copa-sudamericana/2024/group-stage/',
}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
_fd_cache = None
_sw_cache = None


def get_football_data_stats() -> Dict:
    global _fd_cache
    if _fd_cache is not None:
        return _fd_cache
    all_stats = {}
    for league, url in FD_LEAGUE_URLS.items():
        try:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                continue
            reader = csv.DictReader(StringIO(r.text))
            for row in reader:
                home = row.get('HomeTeam', '').strip()
                away = row.get('AwayTeam', '').strip()
                fthg, ftag = row.get('FTHG'), row.get('FTAG')
                if not home or not fthg or not ftag:
                    continue
                try:
                    gh, ga = int(fthg), int(ftag)
                except:
                    continue
                for team, gf, ga_team, is_home in [(home, gh, ga, True), (away, ga, gh, False)]:
                    if team not in all_stats:
                        all_stats[team] = {'gf': 0, 'ga': 0, 'home': 0, 'away': 0, 'source': 'FD', 'league': league}
                    all_stats[team]['gf'] += gf
                    all_stats[team]['ga'] += ga_team
                    if is_home:
                        all_stats[team]['home'] += 1
                    else:
                        all_stats[team]['away'] += 1
        except:
            continue
    _fd_cache = all_stats
    return all_stats


def scrape_soccerway(url: str) -> Dict:
    stats = {}
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return stats
        soup = BeautifulSoup(r.text, 'html.parser')
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    text = ' '.join([c.get_text(strip=True) for c in cells])
                    match = re.search(r'(\w[\w\s]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+(\w[\w\s]+)', text)
                    if match:
                        t1, s1, s2, t2 = match.group(1).strip(), int(match.group(2)), int(match.group(3)), match.group(4).strip()
                        for team, gf, ga, is_home in [(t1, s1, s2, True), (t2, s2, s1, False)]:
                            if team and len(team) > 2:
                                if team not in stats:
                                    stats[team] = {'gf': 0, 'ga': 0, 'home': 0, 'away': 0}
                                stats[team]['gf'] += gf
                                stats[team]['ga'] += ga
                                if is_home:
                                    stats[team]['home'] += 1
                                else:
                                    stats[team]['away'] += 1
    except:
        pass
    return stats


def get_soccerway_stats() -> Dict:
    global _sw_cache
    if _sw_cache is not None:
        return _sw_cache
    all_stats = {}
    for league, url in SOCCERWAY_LEAGUES.items():
        stats = scrape_soccerway(url)
        for team, data in stats.items():
            if team not in all_stats:
                all_stats[team] = {'gf': 0, 'ga': 0, 'home': 0, 'away': 0, 'source': 'SW', 'league': league}
            all_stats[team]['gf'] += data['gf']
            all_stats[team]['ga'] += data['ga']
            all_stats[team]['home'] += data['home']
            all_stats[team]['away'] += data['away']
    _sw_cache = all_stats
    return all_stats


def search_thesportsdb(team_name: str) -> Optional[Dict]:
    try:
        url = f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={team_name.replace(' ', '+')}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get('teams'):
                team_data = data['teams'][0]
                return {
                    'equipo': team_data.get('strTeam'),
                    'liga': team_data.get('strLeague', 'N/A'),
                    'source': 'TSDB'
                }
    except:
        pass
    return None


def search_all_sources(team_name: str) -> Optional[Dict]:
    team_lower = team_name.lower()
    fd_stats = get_football_data_stats()
    for team, data in fd_stats.items():
        if team_lower in team.lower() or team.lower() in team_lower:
            return {'equipo': team, **data}
    sw_stats = get_soccerway_stats()
    for team, data in sw_stats.items():
        if team_lower in team.lower() or team.lower() in team_lower:
            return {'equipo': team, **data}
    tsdb = search_thesportsdb(team_name)
    if tsdb:
        return {
            'equipo': tsdb['equipo'],
            'gf': 0, 'ga': 0, 'home': 0, 'away': 0,
            'source': 'TSDB',
            'league': tsdb.get('liga', 'N/A')
        }
    return None


def clear_cache():
    global _fd_cache, _sw_cache
    _fd_cache = None
    _sw_cache = None


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    results = []
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for team in team_names:
        result = {
            'equipo': team,
            'encontrado': False,
            'exito': False,
            'fuentes_probadas': [],
            'lambda_local': None,
            'lambda_visitante': None,
            'sin_estadisticas': False
        }
        
        data = search_all_sources(team)
        
        if data:
            result['encontrado'] = True
            result['fuentes_probadas'].append(data.get('source', '?'))
            result['liga'] = data.get('league', 'N/A')
            
            home_games = data.get('home', 0)
            away_games = data.get('away', 0)
            total = home_games + away_games
            gf = data.get('gf', 0)
            
            if total > 0 and gf > 0:
                lambda_local = round((gf / total) * 1.1, 2)
                lambda_visitante = round((gf / total) * 0.85, 2)
            else:
                result['sin_estadisticas'] = True
                lambda_local = 1.5
                lambda_visitante = 1.2
            
            result['lambda_local'] = lambda_local
            result['lambda_visitante'] = lambda_visitante
            
            try:
                supa_data = {
                    'equipo': data.get('equipo', team),
                    'liga': data.get('league', 'N/A'),
                    'partidos_jugados': total if total > 0 else 0,
                    'goles_favor': gf if gf > 0 else 0,
                    'goles_contra': data.get('ga', 0) if data.get('ga', 0) else 0,
                    'lambda_local': lambda_local,
                    'lambda_visitante': lambda_visitante,
                }
                client.table('estadisticas_equipos').upsert(supa_data, on_conflict='equipo').execute()
                result['exito'] = True
                result['equipo_real'] = data.get('equipo', team)
            except Exception as e:
                result['error'] = str(e)[:50]
        else:
            result['liga'] = 'NO ENCONTRADO'
        
        results.append(result)
        status = "OK" if result['exito'] else "X"
        source = result['fuentes_probadas'][-1] if result['fuentes_probadas'] else "NO"
        sin_stats = " (sin datos)" if result.get('sin_estadisticas') else ""
        print(f"[{status}] {team} -> {source} ({result.get('liga', 'NO')}){sin_stats}")
    
    return results
