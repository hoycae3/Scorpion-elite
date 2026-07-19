"""
Scorpion Elite - Soccerway Scraper
==================================
Scraping de Soccerway para ligas sudamericanas
"""

import requests
from bs4 import BeautifulSoup
import re
from typing import Dict, List, Optional


# URLs de Soccerway por liga
SOCCERWAY_LEAGUES = {
    # Colombia
    'Categoria Primera A': 'https://pt.soccerway.com/national/colombia/categoria-primera-a/2024/regular-season/r76545/',
    'Categoria Primera B': 'https://pt.soccerway.com/national/colombia/categoria-primera-b/2024/regular-season/',
    
    # Sudamerica
    'Ecuador Serie A': 'https://pt.soccerway.com/national/ecuador/serie-a/2024/regular-season/',
    'Peru Liga 1': 'https://pt.soccerway.com/national/peru/liga-1/2024/regular-season/',
    'Chile Primera Division': 'https://pt.soccerway.com/national/chile/primera-division/2024/regular-season/',
    'Uruguay Primera': 'https://pt.soccerway.com/national/uruguay/primera-division/2024/regular-season/',
    'Paraguay Primera': 'https://pt.soccerway.com/national/paraguay/primera-division/2024/regular-season/',
    'Bolivia Liga': 'https://pt.soccerway.com/national/bolivia/liga-de-futbol-profesional/2024/regular-season/',
    'Venezuela Primera': 'https://pt.soccerway.com/national/venezuela/primera-division/2024/regular-season/',
    
    # Centroamerica
    'Costa Rica Primera': 'https://pt.soccerway.com/national/costa-rica/primera-division/2024/regular-season/',
    'Guatemala Liga': 'https://pt.soccerway.com/national/guatemala/liga-nacional/2024/regular-season/',
    'Honduras Liga': 'https://pt.soccerway.com/national/honduras/liguilla/2024/regular-season/',
    'El Salvador Primera': 'https://pt.soccerway.com/national/el-salvador/primera-division/2024/regular-season/',
    'Panama LPF': 'https://pt.soccerway.com/national/panama/lpf/2024/regular-season/',
    
    # Libertadores/Sudamericana
    'Copa Libertadores': 'https://pt.soccerway.com/international-tournaments/south-america/copa-libertadores/2024/group-stage/',
    'Copa Sudamericana': 'https://pt.soccerway.com/international-tournaments/south-america/copa-sudamericana/2024/group-stage/',
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def scrape_league(url: str) -> Dict:
    """Extrae equipos y estadisticas de una liga."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.content, 'html.parser')
        stats = {}
        
        # Buscar tabla de equipos/resultados
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    # Buscar celdas con datos de partido
                    cell_texts = [c.get_text(strip=True) for c in cells]
                    
                    # Patrones para extraer equipos y marcador
                    # Formato comun: Equipo1 2 - 1 Equipo2
                    text = ' '.join(cell_texts)
                    match = re.search(r'(\w[\w\s]+?)\s+(\d+)\s*[-–]\s*(\d+)\s+(\w[\w\s]+)', text)
                    
                    if match:
                        team1 = match.group(1).strip()
                        score1 = int(match.group(2))
                        score2 = int(match.group(3))
                        team2 = match.group(4).strip()
                        
                        # Agregar a estadisticas
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
        
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {}


def get_all_soccerway_stats() -> Dict:
    """Obtiene estadisticas de TODAS las ligas de Soccerway."""
    all_stats = {}
    
    for league_name, url in SOCCERWAY_LEAGUES.items():
        print(f"Scraping: {league_name}")
        stats = scrape_league(url)
        
        for team, data in stats.items():
            if team not in all_stats:
                all_stats[team] = {'gf': 0, 'ga': 0, 'home': 0, 'away': 0, 'league': league_name}
            
            all_stats[team]['gf'] += data['gf']
            all_stats[team]['ga'] += data['ga']
            all_stats[team]['home'] += data['home']
            all_stats[team]['away'] += data['away']
    
    return all_stats


def search_team_soccerway(team_name: str, all_stats: Dict) -> Optional[Dict]:
    """Busca un equipo en las estadisticas."""
    team_lower = team_name.lower()
    
    for team, data in all_stats.items():
        if team_lower in team.lower() or team.lower() in team_lower:
            return {
                'equipo': team,
                'liga': data['league'],
                'partidos_local': data['home'],
                'partidos_visitante': data['away'],
                'goles_favor': data['gf'],
                'goles_contra': data['ga'],
            }
    
    return None


# Cache
_cached_stats = None


def get_all_stats() -> Dict:
    """Obtiene todas las estadisticas (con cache)."""
    global _cached_stats
    if _cached_stats is None:
        _cached_stats = get_all_soccerway_stats()
    return _cached_stats


def clear_cache():
    global _cached_stats
    _cached_stats = None
