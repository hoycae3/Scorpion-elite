"""
Scorpion Elite - Robot Extractor de Estadisticas
================================================
Busca equipos en:
1. football-data.co.uk (goles, resultados)
2. Soccerway (Latinoamérica)
3. WhoScored (stats avanzadas: corners, tarjetas)
4. FBref (stats avanzadas: posesión, duelos)

Orden de búsqueda: football-data → Soccerway → WhoScored → FBref
"""

import requests
from io import StringIO
import csv
from bs4 import BeautifulSoup
import re
import time
from supabase import create_client
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# TODAS las ligas de football-data.co.uk
FD_LEAGUE_URLS = {
    # Inglaterra
    'Premier League': 'https://www.football-data.co.uk/england.csv',
    'Championship': 'https://www.football-data.co.uk/england.csv',
    'League One': 'https://www.football-data.co.uk/england.csv',
    'League Two': 'https://www.football-data.co.uk/england.csv',
    
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
    'Super League Greece': 'https://www.football-data.co.uk/greece.csv',
    
    # TurquÃ­a
    'Super Lig': 'https://www.football-data.co.uk/turkey.csv',
    
    # Rusia
    'Premier League Russia': 'https://www.football-data.co.uk/russia.csv',
    
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
    'Superliga Denmark': 'https://www.football-data.co.uk/denmark.csv',
    
    # Finlandia
    'Veikkausliiga': 'https://www.football-data.co.uk/finland.csv',
    
    # Hungria
    'NB I': 'https://www.football-data.co.uk/hungary.csv',
    
    # Irlanda
    'Premier Division Ireland': 'https://www.football-data.co.uk/ireland.csv',
    
    # Noruega
    'Eliteserien': 'https://www.football-data.co.uk/norway.csv',
    
    # Polonia
    'Ekstraklasa': 'https://www.football-data.co.uk/poland.csv',
    
    # Romania
    'Liga I Romania': 'https://www.football-data.co.uk/romania.csv',
    
    # EscoCia
    'Premiership': 'https://www.football-data.co.uk/scotland.csv',
    
    # Suecia
    'Allsvenskan': 'https://www.football-data.co.uk/sweden.csv',
    
    # Suiza
    'Super League Switzerland': 'https://www.football-data.co.uk/switzerland.csv',
    
    # Ukrania
    'Premier League Ukraine': 'https://www.football-data.co.uk/ukraine.csv',
}

# Soccerway - Latinoamerica
SOCCERWAY_LEAGUES = {
    'Colombia Primera A': 'https://pt.soccerway.com/national/colombia/categoria-primera-a/2024/regular-season/r76545/',
    'Colombia Primera B': 'https://pt.soccerway.com/national/colombia/categoria-primera-b/2024/regular-season/',
    'Ecuador Serie A': 'https://pt.soccerway.com/national/ecuador/serie-a/2024/regular-season/',
    'Peru Liga 1': 'https://pt.soccerway.com/national/peru/liga-1/2024/regular-season/',
    'Chile Primera Division': 'https://pt.soccerway.com/national/chile/primera-division/2024/regular-season/',
    'Uruguay Primera': 'https://pt.soccerway.com/national/uruguay/primera-division/2024/regular-season/',
    'Paraguay Primera': 'https://pt.soccerway.com/national/paraguay/primera-division/2024/regular-season/',
    'Bolivia Liga': 'https://pt.soccerway.com/national/bolivia/liga-de-futbol-profesional/2024/regular-season/',
    'Venezuela Primera': 'https://pt.soccerway.com/national/venezuela/primera-division/2024/regular-season/',
    'Costa Rica Primera': 'https://pt.soccerway.com/national/costa-rica/primera-division/2024/regular-season/',
    'Guatemala Liga': 'https://pt.soccerway.com/national/guatemala/liga-nacional/2024/regular-season/',
    'Honduras Liga': 'https://pt.soccerway.com/national/honduras/liguilla/2024/regular-season/',
    'El Salvador Primera': 'https://pt.soccerway.com/national/el-salvador/primera-division/2024/regular-season/',
    'Panama LPF': 'https://pt.soccerway.com/national/panama/lpf/2024/regular-season/',
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


def search_all_sources(team_name: str) -> Optional[Dict]:
    team_lower = team_name.lower()
    
    # Fuente 1: football-data (40+ ligas)
    fd_stats = get_football_data_stats()
    for team, data in fd_stats.items():
        if team_lower in team.lower() or team.lower() in team_lower:
            return {'equipo': team, **data}
    
    # Fuente 2: Soccerway (Latinoamerica)
    sw_stats = get_soccerway_stats()
    for team, data in sw_stats.items():
        if team_lower in team.lower() or team.lower() in team_lower:
            return {'equipo': team, **data}
    
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
            'lambda_visitante': None
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
                
                result['lambda_local'] = lambda_local
                result['lambda_visitante'] = lambda_visitante
                
                try:
                    supa_data = {
                        'equipo': data.get('equipo', team),
                        'liga': data.get('league', 'N/A'),
                        'partidos_jugados': total,
                        'goles_favor': gf,
                        'goles_contra': data.get('ga', 0),
                        'lambda_local': lambda_local,
                        'lambda_visitante': lambda_visitante,
                    }
                    client.table('estadisticas_equipos').upsert(supa_data, on_conflict='equipo').execute()
                    result['exito'] = True
                    result['equipo_real'] = data.get('equipo', team)
                except Exception as e:
                    result['error'] = str(e)[:50]
            else:
                result['liga'] = 'SIN ESTADISTICAS'
        else:
            result['liga'] = 'NO ENCONTRADO'
        
        results.append(result)
        status = "OK" if result['exito'] else "X"
        print(f"[{status}] {team} -> {result.get('liga', 'NO')}")
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPERS AVANZADOS: WHOSCORED Y FBREF
# ═══════════════════════════════════════════════════════════════════════════════

class WhoScoredScraper:
    """Scraper para WhoScored.com - Stats avanzadas (corners, tarjetas)"""
    
    BASE_URL = "https://www.whoscored.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def search_team(self, team_name: str) -> Optional[str]:
        """Busca un equipo y devuelve su URL."""
        try:
            url = f"{self.BASE_URL}/Search/?keyword={team_name.replace(' ', '+')}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/Teams/\d+/'))
            
            for link in links:
                if team_name.lower() in link.get_text().lower():
                    return self.BASE_URL + link.get('href')
            
            return None
        except Exception as e:
            logger.debug(f"Error en WhoScored search: {e}")
            return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas del equipo."""
        try:
            response = self.session.get(team_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stats = {}
            
            # Buscar estadísticas en la página
            # La estructura puede variar, buscar patrones comunes
            stat_divs = soup.find_all('div', class_=re.compile(r'stat'))
            
            for div in stat_divs:
                text = div.get_text(strip=True)
                # Intentar extraer números
                if 'Corner' in text or 'corner' in text.lower():
                    match = re.search(r'(\d+\.?\d*)', text)
                    if match:
                        stats['corners_avg'] = float(match.group(1))
                elif 'Yellow' in text or 'Card' in text:
                    match = re.search(r'(\d+\.?\d*)', text)
                    if match:
                        stats['yellows_avg'] = float(match.group(1))
            
            time.sleep(1)
            return stats if stats else None
            
        except Exception as e:
            logger.debug(f"Error en WhoScored get_team_stats: {e}")
            return None


class FBrefScraper:
    """Scraper para FBref.com - Stats avanzadas de equipos"""
    
    BASE_URL = "https://fbref.com"
    
    SQUAD_URLS = {
        'Premier League': 'https://fbref.com/en/comps/9/Premier-League-Stats',
        'La Liga': 'https://fbref.com/en/comps/12/La-Liga-Stats',
        'Bundesliga': 'https://fbref.com/en/comps/20/Bundesliga-Stats',
        'Serie A': 'https://fbref.com/en/comps/11/Serie-A-Stats',
        'Ligue 1': 'https://fbref.com/en/comps/13/Ligue-1-Stats',
        'Primeira Liga': 'https://fbref.com/en/comps/32/Primeira-Liga-Stats',
        'Eredivisie': 'https://fbref.com/en/comps/23/Eredivisie-Stats',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._squads_cache = {}
    
    def _get_squads(self, league: str) -> Dict[str, str]:
        """Obtiene equipos de una liga."""
        if league in self._squads_cache:
            return self._squads_cache[league]
        
        try:
            url = self.SQUAD_URLS.get(league)
            if not url:
                return {}
            
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            squads = {}
            
            links = soup.find_all('a', href=re.compile(r'/en/squads/'))
            for link in links:
                name = link.get_text(strip=True)
                if name and len(name) > 2:
                    squads[name] = self.BASE_URL + link.get('href')
            
            self._squads_cache[league] = squads
            time.sleep(1)
            return squads
            
        except Exception as e:
            logger.debug(f"Error en FBref _get_squads: {e}")
            return {}
    
    def find_team(self, team_name: str, league: str = None) -> Optional[Dict]:
        """Busca un equipo y devuelve stats."""
        try:
            if league:
                squads = self._get_squads(league)
                team_lower = team_name.lower()
                
                for name, url in squads.items():
                    if team_lower in name.lower() or name.lower() in team_lower:
                        return {'name': name, 'url': url, 'league': league}
            else:
                # Buscar en todas las ligas
                for lg in self.SQUAD_URLS.keys():
                    squads = self._get_squads(lg)
                    team_lower = team_name.lower()
                    
                    for name, url in squads.items():
                        if team_lower in name.lower() or name.lower() in team_lower:
                            return {'name': name, 'url': url, 'league': lg}
            
            return None
            
        except Exception as e:
            logger.debug(f"Error en FBref find_team: {e}")
            return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas del equipo."""
        try:
            response = self.session.get(team_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stats = {}
            
            # FBref tiene muchas estadísticas, buscar las importantes
            stat_cells = soup.find_all('td', {'data-stat': True})
            
            for cell in stat_cells:
                stat_type = cell.get('data-stat')
                value = cell.get_text(strip=True)
                
                # Mapear estadísticas importantes
                if stat_type == 'poss':
                    try:
                        stats['posesion'] = float(value.replace('%', ''))
                    except:
                        pass
                elif stat_type == 'crs':
                    try:
                        stats['corners_avg'] = float(value)
                    except:
                        pass
                elif stat_type == 'cards_yellow':
                    try:
                        stats['amarillas_avg'] = float(value)
                    except:
                        pass
                elif stat_type == 'shots':
                    try:
                        stats['tiros_avg'] = float(value)
                    except:
                        pass
                elif stat_type == 'shots_on_target':
                    try:
                        stats['tiros_arco_avg'] = float(value)
                    except:
                        pass
            
            time.sleep(1)
            return stats if stats else None
            
        except Exception as e:
            logger.debug(f"Error en FBref get_team_stats: {e}")
            return None


def scrape_team_advanced(team_name: str, league: str = None) -> Dict:
    """
    Busca estadísticas avanzadas de un equipo en WhoScored y FBref.
    """
    result = {
        'equipo': team_name,
        'liga': league,
        'source': None,
        'corners_avg': None,
        'amarillas_avg': None,
        'tiros_avg': None,
        'tiros_arco_avg': None,
        'posesion': None,
    }
    
    # 1. Intentar WhoScored
    ws = WhoScoredScraper()
    ws_url = ws.search_team(team_name)
    
    if ws_url:
        ws_stats = ws.get_team_stats(ws_url)
        if ws_stats:
            result['source'] = 'whoscored'
            if 'corners_avg' in ws_stats:
                result['corners_avg'] = ws_stats['corners_avg']
            if 'yellows_avg' in ws_stats:
                result['amarillas_avg'] = ws_stats['yellows_avg']
    
    # 2. Intentar FBref
    fb = FBrefScraper()
    fb_team = fb.find_team(team_name, league)
    
    if fb_team:
        fb_stats = fb.get_team_stats(fb_team['url'])
        if fb_stats:
            result['source'] = 'fbref' if not result['source'] else result['source']
            for key in ['corners_avg', 'amarillas_avg', 'tiros_avg', 'tiros_arco_avg', 'posesion']:
                if key in fb_stats:
                    result[key] = fb_stats[key]
    
    return result


def run_robot_batch_v2(team_names: List[str], leagues: List[str] = None) -> List[Dict]:
    """
    Versión mejorada del robot que usa todas las fuentes.
    Incluye: football-data, Soccerway, WhoScored, FBref
    """
    results = []
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Cache de football-data y Soccerway
    fd_cache = get_football_data_stats()
    sw_cache = get_soccerway_stats()
    
    for team in team_names:
        result = {
            'equipo': team,
            'encontrado': False,
            'exito': False,
            'fuentes': [],
            'liga': None,
            'lambda_local': None,
            'lambda_visitante': None,
            # Stats avanzadas
            'corners_avg': None,
            'amarillas_avg': None,
            'tiros_avg': None,
        }
        
        team_lower = team.lower()
        
        # 1. football-data
        for name, data in fd_cache.items():
            if team_lower in name.lower() or name.lower() in team_lower:
                result['encontrado'] = True
                result['fuentes'].append('FD')
                result['liga'] = data.get('league', 'N/A')
                
                home = data.get('home', 0)
                away = data.get('away', 0)
                total = home + away
                gf = data.get('gf', 0)
                
                if total > 0 and gf > 0:
                    result['lambda_local'] = round((gf / total) * 1.1, 2)
                    result['lambda_visitante'] = round((gf / total) * 0.85, 2)
                    result['exito'] = True
                break
        
        # 2. Soccerway (si no encontrado)
        if not result['encontrado']:
            for name, data in sw_cache.items():
                if team_lower in name.lower() or name.lower() in team_lower:
                    result['encontrado'] = True
                    result['fuentes'].append('SW')
                    result['liga'] = data.get('league', 'N/A')
                    
                    home = data.get('home', 0)
                    away = data.get('away', 0)
                    total = home + away
                    gf = data.get('gf', 0)
                    
                    if total > 0 and gf > 0:
                        result['lambda_local'] = round((gf / total) * 1.1, 2)
                        result['lambda_visitante'] = round((gf / total) * 0.85, 2)
                        result['exito'] = True
                    break
        
        # 3. WhoScored y FBref para stats avanzadas
        league = result.get('liga')
        advanced = scrape_team_advanced(team, league)
        
        if advanced['source']:
            result['fuentes'].append(advanced['source'])
            result['corners_avg'] = advanced.get('corners_avg')
            result['amarillas_avg'] = advanced.get('amarillas_avg')
            result['tiros_avg'] = advanced.get('tiros_avg')
        
        # Guardar en Supabase
        if result['exito']:
            try:
                supa_data = {
                    'equipo': team,
                    'liga': result.get('liga', 'N/A'),
                    'partidos_jugados': total if result['exito'] else 0,
                    'goles_favor': gf if result['exito'] else 0,
                    'lambda_local': result.get('lambda_local', 1.3),
                    'lambda_visitante': result.get('lambda_visitante', 1.1),
                    'source_fbdata': 'FD' in result['fuentes'],
                    'source_whoscored': 'whoscored' in result['fuentes'],
                    'source_fbref': 'fbref' in result['fuentes'],
                    'promedio_corners_total': result.get('corners_avg'),
                    'promedio_amarillas': result.get('amarillas_avg'),
                    'promedio_tiros': result.get('tiros_avg'),
                }
                client.table('equipos_stas').upsert(supa_data, on_conflict='equipo,temporada').execute()
            except Exception as e:
                logger.error(f"Error guardando {team}: {e}")
        
        results.append(result)
        status = "✅" if result['exito'] else "❌"
        print(f"[{status}] {team} ({', '.join(result['fuentes'])})")
    
    return results
