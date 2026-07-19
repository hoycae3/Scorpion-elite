"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Usa football-data.co.uk para extraer estadisticas de equipos
"""

import requests
from io import StringIO
import csv
from supabase import create_client
from typing import Dict, List


SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

LEAGUE_URLS = {
    'premier': 'https://www.football-data.co.uk/england.csv',
    'la liga': 'https://www.football-data.co.uk/spain.csv',
    'bundesliga': 'https://www.football-data.co.uk/germany.csv',
    'serie a': 'https://www.football-data.co.uk/italy.csv',
    'ligue 1': 'https://www.football-data.co.uk/france.csv',
    'brasileirao': 'https://www.football-data.co.uk/brazil.csv',
}


def get_league_stats(league_key: str) -> Dict:
    url = LEAGUE_URLS.get(league_key.lower())
    if not url:
        return {}
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            return {}
        
        reader = csv.DictReader(StringIO(response.text))
        stats = {}
        
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
            
            if home not in stats:
                stats[home] = {'gf': 0, 'ga': 0, 'home_games': 0, 'away_games': 0}
            if away not in stats:
                stats[away] = {'gf': 0, 'ga': 0, 'home_games': 0, 'away_games': 0}
            
            stats[home]['gf'] += goals_home
            stats[home]['ga'] += goals_away
            stats[home]['home_games'] += 1
            
            stats[away]['gf'] += goals_away
            stats[away]['ga'] += goals_home
            stats[away]['away_games'] += 1
        
        return stats
    except Exception as e:
        print(f"Error: {e}")
        return {}


def calculate_lambda(gf: int, games: int, is_home: bool = True) -> float:
    if games == 0:
        return None
    avg = gf / games
    if is_home:
        return round(avg * 1.1, 2)
    else:
        return round(avg * 0.85, 2)


def run_robot_for_league(league_name: str) -> List[Dict]:
    print(f"Procesando: {league_name}")
    results = []
    league_stats = get_league_stats(league_name)
    
    if not league_stats:
        print(f"  Sin datos")
        return results
    
    print(f"  {len(league_stats)} equipos")
    
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    for team, data in league_stats.items():
        total_games = data['home_games'] + data['away_games']
        if total_games < 5:
            continue
        
        lambda_local = calculate_lambda(data['gf'], data['home_games'], True)
        lambda_visitante = calculate_lambda(data['gf'], data['away_games'], False)
        
        if lambda_local is None:
            continue
        
        team_data = {
            'equipo': team,
            'liga': league_name,
            'partidos_jugados': total_games,
            'goles_favor': data['gf'],
            'goles_contra': data['ga'],
            'lambda_local': lambda_local,
            'lambda_visitante': lambda_visitante,
        }
        
        try:
            client.table('estadisticas_equipos').upsert(team_data, on_conflict='equipo').execute()
            results.append({'equipo': team, 'exito': True})
            print(f"  OK: {team}")
        except Exception as e:
            print(f"  Error: {team} - {e}")
    
    return results


def run_robot_batch(league_names: List[str]) -> List[Dict]:
    all_results = []
    for league in league_names:
        results = run_robot_for_league(league)
        all_results.extend(results)
    return all_results


if __name__ == "__main__":
    result = run_robot_for_league('premier')
    print(f"Total: {len(result)}")
