"""
Scorpion Elite - Scraper Avanzado
=================================
Busca estadísticas avanzadas en:
1. WhoScored - Stats de partidos (corners, tarjetas, posesión)
2. FBref - Estadísticas avanzadas de equipos

Orden de búsqueda:
1. WhoScored (preferido)
2. FBref (backup)
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# ═══════════════════════════════════════════════════════════════════════════════
# WHOSCORED SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class WhoScoredScraper:
    """Scraper para WhoScored.com"""
    
    BASE_URL = "https://www.whoscored.com"
    
    # Regiones y torneos
    REGIONS = {
        'england': {'id': 1, 'tournaments': ['Premier League']},
        'spain': {'id': 4, 'tournaments': ['La Liga']},
        'germany': {'id': 3, 'tournaments': ['Bundesliga']},
        'italy': {'id': 2, 'tournaments': ['Serie A']},
        'france': {'id': 5, 'tournaments': ['Ligue 1']},
        'portugal': {'id': 17, 'tournaments': ['Primeira Liga']},
        'netherlands': {'id': 10, 'tournaments': ['Eredivisie']},
    }
    
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
            
            # Buscar enlace de equipo
            links = soup.find_all('a', href=re.compile(r'/Teams/\d+/'))
            for link in links:
                if team_name.lower() in link.get_text().lower():
                    return self.BASE_URL + link.get('href')
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando equipo en WhoScored: {e}")
            return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas de un equipo desde su página."""
        try:
            response = self.session.get(team_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stats = {}
            
            # Intentar extraer estadísticas básicas
            # (La estructura puede variar)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo stats de WhoScored: {e}")
            return None
    
    def get_team_matches(self, team_url: str, limit: int = 10) -> List[Dict]:
        """Obtiene los últimos partidos de un equipo."""
        matches = []
        try:
            # Añadir /Results al URL del equipo
            results_url = team_url.rstrip('/') + '/Results'
            response = self.session.get(results_url, timeout=10)
            
            if response.status_code != 200:
                return matches
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Buscar tabla de partidos
            match_rows = soup.find_all('tr', class_='match')
            
            for row in match_rows[:limit]:
                try:
                    # Extraer datos del partido
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        match_data = {
                            'fecha': cells[0].get_text(strip=True),
                            'competencia': cells[1].get_text(strip=True),
                            'equipo_local': cells[2].get_text(strip=True),
                            'resultado': cells[3].get_text(strip=True),
                            'equipo_visitante': cells[4].get_text(strip=True),
                        }
                        matches.append(match_data)
                except:
                    continue
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            logger.error(f"Error obteniendo partidos: {e}")
        
        return matches


# ═══════════════════════════════════════════════════════════════════════════════
# FBREF SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class FBrefScraper:
    """Scraper para FBref.com (Football Reference)"""
    
    BASE_URL = "https://fbref.com"
    
    # URLs de squads por liga
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
        self._squads_cache = None
    
    def _get_squads(self, league: str) -> Dict[str, str]:
        """Obtiene diccionario de equipos para una liga."""
        if self._squads_cache and league in self._squads_cache:
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
            
            # Buscar tabla de equipos
            table = soup.find('table', {'id': 'stats_squads_season'})
            if not table:
                # Alternativa
                table = soup.find('table')
            
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    link = row.find('a', href=re.compile(r'/en/squads/'))
                    if link:
                        team_name = link.get_text(strip=True)
                        team_url = self.BASE_URL + link.get('href')
                        squads[team_name] = team_url
            
            if not self._squads_cache:
                self._squads_cache = {}
            self._squads_cache[league] = squads
            
            time.sleep(1)
            return squads
            
        except Exception as e:
            logger.error(f"Error obteniendo squads de {league}: {e}")
            return {}
    
    def find_team(self, team_name: str, league: str = None) -> Optional[str]:
        """Busca un equipo y devuelve su URL de FBref."""
        try:
            # Si我们知道 la liga, buscar solo ahí
            if league:
                squads = self._get_squads(league)
                team_lower = team_name.lower()
                
                for name, url in squads.items():
                    if team_lower in name.lower() or name.lower() in team_lower:
                        return url
            else:
                # Buscar en todas las ligas
                for lg, url in self.SQUAD_URLS.items():
                    squads = self._get_squads(lg)
                    team_lower = team_name.lower()
                    
                    for name, squad_url in squads.items():
                        if team_lower in name.lower() or name.lower() in team_lower:
                            return squad_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando equipo en FBref: {e}")
            return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas avanzadas de un equipo."""
        try:
            response = self.session.get(team_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            stats = {}
            
            # Buscar tabla de estadísticas generales
            all_stats = {}
            
            # Intentar encontrar la tabla de stats
            tables = soup.find_all('table')
            for table in tables:
                # Buscar filas con estadísticas
                rows = table.find_all('tr')
                for row in rows:
                    # Skip header rows
                    if row.get('class') and 'thead' in row.get('class'):
                        continue
                    
                    cells = row.find_all('td')
                    if len(cells) >= 20:
                        try:
                            # Intentar extraer estadísticas
                            # Los índices varían, buscar los correctos
                            stat_data = {
                                'partidos': int(cells[3].get_text(strip=True)) if cells[3].get_text(strip=True).isdigit() else 0,
                                'goles': int(cells[6].get_text(strip=True)) if cells[6].get_text(strip=True).isdigit() else 0,
                                'asistencias': int(cells[7].get_text(strip=True)) if cells[7].get_text(strip=True).isdigit() else 0,
                                'tarjetas_amarillas': int(cells[9].get_text(strip=True)) if cells[9].get_text(strip=True).isdigit() else 0,
                                'tarjetas_rojas': int(cells[10].get_text(strip=True)) if cells[10].get_text(strip=True).isdigit() else 0,
                            }
                            all_stats.update(stat_data)
                        except:
                            continue
            
            # Buscar estadísticas de posesión
            possession_elem = soup.find('div', {'data-stat': 'poss'})
            if possession_elem:
                all_stats['posesion'] = possession_elem.get_text(strip=True)
            
            # Buscar平均 corners
            corners_elem = soup.find('div', {'data-stat': 'crs'})
            if corners_elem:
                all_stats['corners'] = corners_elem.get_text(strip=True)
            
            stats = all_stats
            time.sleep(1)
            
            return stats if stats else None
            
        except Exception as e:
            logger.error(f"Error obteniendo stats de FBref: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

class AdvancedStatsScraper:
    """Scraper que combina WhoScored y FBref."""
    
    def __init__(self):
        self.whoscored = WhoScoredScraper()
        self.fbref = FBrefScraper()
    
    def scrape_team(self, team_name: str, league: str = None) -> Dict:
        """
        Busca estadísticas de un equipo en múltiples fuentes.
        Orden: WhoScored → FBref → football-data
        """
        result = {
            'equipo': team_name,
            'liga': league,
            'encontrado': False,
            'source': None,
            'stats': {}
        }
        
        # 1. Intentar WhoScored
        logger.info(f"Buscando {team_name} en WhoScored...")
        ws_url = self.whoscored.search_team(team_name)
        if ws_url:
            ws_stats = self.whoscored.get_team_stats(ws_url)
            if ws_stats:
                result['encontrado'] = True
                result['source'] = 'whoscored'
                result['stats'] = ws_stats
                return result
        
        # 2. Intentar FBref
        logger.info(f"Buscando {team_name} en FBref...")
        fb_url = self.fbref.find_team(team_name, league)
        if fb_url:
            fb_stats = self.fbref.get_team_stats(fb_url)
            if fb_stats:
                result['encontrado'] = True
                result['source'] = 'fbref'
                result['stats'] = fb_stats
                return result
        
        return result
    
    def scrape_batch(self, teams: List[Tuple[str, str]]) -> List[Dict]:
        """Busca estadísticas para múltiples equipos."""
        results = []
        
        for team_name, league in teams:
            result = self.scrape_team(team_name, league)
            results.append(result)
            time.sleep(1)  # Rate limiting
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE UTILIDAD
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_averages(stats_list: List[Dict], team_name: str) -> Dict:
    """
    Calcula promedios de estadísticas de múltiples partidos.
    Útil para calcular promedios de corners, tarjetas, etc.
    """
    if not stats_list:
        return {}
    
    totals = {
        'goles_favor': 0,
        'goles_contra': 0,
        'corners_total': 0,
        'amarillas': 0,
        'rojas': 0,
        'tiros': 0,
        'tiros_arco': 0,
        'partidos': len(stats_list)
    }
    
    for stats in stats_list:
        totals['goles_favor'] += stats.get('goles_favor', 0)
        totals['goles_contra'] += stats.get('goles_contra', 0)
        totals['corners_total'] += stats.get('corners_total', 0)
        totals['amarillas'] += stats.get('amarillas', 0)
        totals['rojas'] += stats.get('rojas', 0)
        totals['tiros'] += stats.get('tiros', 0)
        totals['tiros_arco'] += stats.get('tiros_arco', 0)
    
    n = totals['partidos']
    averages = {
        'equipo': team_name,
        'promedio_goles_favor': round(totals['goles_favor'] / n, 2) if n > 0 else 0,
        'promedio_goles_contra': round(totals['goles_contra'] / n, 2) if n > 0 else 0,
        'promedio_corners': round(totals['corners_total'] / n, 2) if n > 0 else 0,
        'promedio_amarillas': round(totals['amarillas'] / n, 2) if n > 0 else 0,
        'promedio_rojas': round(totals['rojas'] / n, 2) if n > 0 else 0,
        'promedio_tiros': round(totals['tiros'] / n, 2) if n > 0 else 0,
        'promedio_tiros_arco': round(totals['tiros_arco'] / n, 2) if n > 0 else 0,
        'partidos': n
    }
    
    return averages


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    scraper = AdvancedStatsScraper()
    
    # Probar con un equipo
    test_teams = [
        ('Manchester City', 'Premier League'),
        ('Barcelona', 'La Liga'),
        ('Bayern Munich', 'Bundesliga'),
    ]
    
    for team, league in test_teams:
        print(f"\n🔍 Buscando {team} ({league})...")
        result = scraper.scrape_team(team, league)
        
        if result['encontrado']:
            print(f"   ✅ Encontrado en: {result['source']}")
            print(f"   📊 Stats: {result['stats']}")
        else:
            print(f"   ❌ No encontrado")
