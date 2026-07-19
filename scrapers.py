"""
Scorpion Elite - Scraper Multi-Fuente
=====================================
Scrapers para:
1. Flashscore
2. Sofascore
3. Soccerway
4. FBref

Orden de búsqueda: Soccerway → Flashscore → Sofascore → FBref
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from typing import Dict, List, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# ═══════════════════════════════════════════════════════════════════════════════
# FLASHSCORE SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class FlashscoreScraper:
    """Scraper para Flashscore.com"""
    
    BASE_URL = "https://www.flashscore.com"
    
    # URLs de ligas por país
    LEAGUE_URLS = {
        'Premier League': '/football/england/premier-league/',
        'La Liga': '/football/spain/laliga/',
        'Bundesliga': '/football/germany/bundesliga/',
        'Serie A': '/football/italy/serie-a/',
        'Ligue 1': '/football/france/ligue-1/',
        'Eredivisie': '/football/netherlands/eredivisie/',
        'Primeira Liga': '/football/portugal/primeira-liga/',
        'Championship': '/football/england/championship/',
        'Copa Libertadores': '/football/south-america/copa-libertadores/',
        # Latinoamérica
        'Liga MX': '/football/mexico/liga-mx/',
        'Primera Argentina': '/football/argentina/primera-nacional/',
        'Brasil Serie A': '/football/brazil/serie-a/',
        'Colombia Primera A': '/football/colombia/liga-aguila/',
        'Chile Primera': '/football/chile/primera-division/',
        'Peru Liga 1': '/football/peru/liga-1/',
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """Busca un equipo en Flashscore."""
        try:
            # Intentar buscar directamente
            search_url = f"{self.BASE_URL}/search/"
            params = {'query': team_name}
            
            response = self.session.get(search_url, params=params, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar enlace de equipo
            team_links = soup.find_all('a', href=re.compile(r'/team/football/'))
            
            for link in team_links:
                link_text = link.get_text(strip=True).lower()
                if team_name.lower() in link_text or link_text in team_name.lower():
                    return {
                        'name': link.get_text(strip=True),
                        'url': self.BASE_URL + link.get('href'),
                        'source': 'flashscore'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando en Flashscore: {e}")
            return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas del equipo."""
        try:
            response = self.session.get(team_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stats = {}
            
            # Buscar estadísticas en la página
            # Formato común: número seguido de label
            stat_blocks = soup.find_all(['div', 'td'], class_=re.compile(r'stat|value|number'))
            
            for block in stat_blocks:
                text = block.get_text(strip=True)
                # Intentar extraer números
                numbers = re.findall(r'\d+\.?\d*', text)
                if numbers:
                    if 'goals' in text.lower():
                        stats['goles'] = float(numbers[0])
                    elif 'match' in text.lower() or 'game' in text.lower():
                        stats['partidos'] = int(numbers[0])
            
            time.sleep(1)
            return stats if stats else None
            
        except Exception as e:
            logger.error(f"Error obteniendo stats de Flashscore: {e}")
            return None
    
    def get_league_standings(self, league: str) -> List[Dict]:
        """Obtiene la tabla de posiciones de una liga."""
        standings = []
        
        try:
            url = self.LEAGUE_URLS.get(league)
            if not url:
                return standings
            
            # Ir a la sección de standings
            standings_url = f"{self.BASE_URL}{url}standings/"
            response = self.session.get(standings_url, timeout=10)
            
            if response.status_code != 200:
                return standings
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar tabla de posiciones
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 8:
                        team_data = {
                            'posicion': cells[0].get_text(strip=True),
                            'equipo': cells[1].get_text(strip=True),
                            'partidos': cells[2].get_text(strip=True),
                            'victorias': cells[3].get_text(strip=True),
                            'empates': cells[4].get_text(strip=True),
                            'derrotas': cells[5].get_text(strip=True),
                            'goles_favor': cells[6].get_text(strip=True),
                            'goles_contra': cells[7].get_text(strip=True),
                        }
                        standings.append(team_data)
            
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error obteniendo standings de {league}: {e}")
        
        return standings


# ═══════════════════════════════════════════════════════════════════════════════
# SOFASCORE SCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

class SofascoreScraper:
    """Scraper para Sofascore.com"""
    
    BASE_URL = "https://www.sofascore.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self._cache = {}
    
    def search_team(self, team_name: str) -> Optional[Dict]:
        """Busca un equipo en Sofascore."""
        try:
            search_url = f"{self.BASE_URL}/search/{team_name.replace(' ', '-')}"
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar enlaces de equipos
            team_links = soup.find_all('a', href=re.compile(r'/team/'))
            
            for link in team_links:
                link_text = link.get_text(strip=True).lower()
                if team_name.lower() in link_text or link_text in team_name.lower():
                    return {
                        'name': link.get_text(strip=True),
                        'url': self.BASE_URL + link.get('href'),
                        'source': 'sofascore'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando en Sofascore: {e}")
            return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas del equipo."""
        try:
            response = self.session.get(team_url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            stats = {}
            
            # Sofascore tiene stats en formato JSON en la página
            scripts = soup.find_all('script')
            for script in scripts:
                text = script.string or ''
                if 'averageGoals' in text or 'corners' in text:
                    # Intentar extraer datos del JSON
                    corners_match = re.search(r'"corners":\s*(\d+\.?\d*)', text)
                    if corners_match:
                        stats['corners_avg'] = float(corners_match.group(1))
                    
                    goals_match = re.search(r'"goals":\s*(\d+\.?\d*)', text)
                    if goals_match:
                        stats['goles_promedio'] = float(goals_match.group(1))
            
            time.sleep(1)
            return stats if stats else None
            
        except Exception as e:
            logger.error(f"Error obteniendo stats de Sofascore: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER PRINCIPAL - COMBINADO
# ═══════════════════════════════════════════════════════════════════════════════

class MultiSourceScraper:
    """Scraper que combina múltiples fuentes."""
    
    def __init__(self):
        self.flashscore = FlashscoreScraper()
        self.sofascore = SofascoreScraper()
    
    def scrape_team(self, team_name: str, league: str = None) -> Dict:
        """
        Busca estadísticas de un equipo en múltiples fuentes.
        Retorna el primer resultado encontrado.
        """
        result = {
            'equipo': team_name,
            'liga': league,
            'source': None,
            'encontrado': False,
            'stats': {}
        }
        
        # 1. Intentar Flashscore
        logger.info(f"Buscando {team_name} en Flashscore...")
        fs_result = self.flashscore.search_team(team_name)
        if fs_result:
            fs_stats = self.flashscore.get_team_stats(fs_result['url'])
            if fs_stats:
                result['encontrado'] = True
                result['source'] = 'flashscore'
                result['stats'] = fs_stats
                return result
        
        # 2. Intentar Sofascore
        logger.info(f"Buscando {team_name} en Sofascore...")
        sf_result = self.sofascore.search_team(team_name)
        if sf_result:
            sf_stats = self.sofascore.get_team_stats(sf_result['url'])
            if sf_stats:
                result['encontrado'] = True
                result['source'] = 'sofascore'
                result['stats'] = sf_stats
                return result
        
        return result
    
    def scrape_league_standings(self, league: str) -> List[Dict]:
        """Obtiene tabla de posiciones de una liga."""
        return self.flashscore.get_league_standings(league)


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def scrape_team_all_sources(team_name: str, league: str = None) -> Dict:
    """
    Busca un equipo en todas las fuentes disponibles.
    Retorna estadísticas encontradas.
    """
    scraper = MultiSourceScraper()
    return scraper.scrape_team(team_name, league)


def scrape_batch(teams: List[str], leagues: List[str] = None) -> List[Dict]:
    """Busca múltiples equipos."""
    results = []
    
    for i, team in enumerate(teams):
        league = leagues[i] if leagues and i < len(leagues) else None
        result = scrape_team_all_sources(team, league)
        results.append(result)
        time.sleep(1)  # Rate limiting
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Probar con algunos equipos
    test_teams = ['Manchester City', 'Barcelona', 'Bayern Munich']
    
    for team in test_teams:
        print(f"\n🔍 Buscando: {team}")
        result = scrape_team_all_sources(team)
        
        if result['encontrado']:
            print(f"   ✅ Encontrado en: {result['source']}")
            print(f"   📊 Stats: {result['stats']}")
        else:
            print(f"   ❌ No encontrado")
