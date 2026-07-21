"""
Scorpion Elite - Robot Extractor Anti-Bloqueo
============================================
Scraper robusto con técnicas antibloqueo para FBref.

Características:
- cloudscraper para evadir Cloudflare
- Headers realistas de Chrome
- Throttling inteligente
- Fallback a API proxy
"""

import time
import random
import logging
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE HEADERS
# ═══════════════════════════════════════════════════════════════════════════════

CHROME_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.football-data.co.uk/',
}

# Headers específicos para football-data.co.uk
FD_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/csv,text/plain,*/*',
    'Accept-Language': 'en-GB,en;q=0.9',
    'Referer': 'https://www.football-data.co.uk/',
}

# ═══════════════════════════════════════════════════════════════════════════════
# API-FOOTBALL.COM
# ═══════════════════════════════════════════════════════════════════════════════

API_FOOTBALL_KEY = "e3926f829cd848f4b2b54d722ca29701"
API_FOOTBALL_URL = "https://v3.football.api-sports.io"

def search_team_api_football(team_name: str) -> Optional[Dict]:
    """
    Busca un equipo en api-football.com usando la API.
    Retorna estadísticas del equipo o None si no lo encuentra.
    """
    try:
        headers = {
            'x-apisports-key': API_FOOTBALL_KEY
        }
        
        # Buscar equipo
        response = requests.get(
            f"{API_FOOTBALL_URL}/teams",
            headers=headers,
            params={'search': team_name},
            timeout=15
        )
        
        if response.status_code != 200:
            logger.warning(f"   ⚠️ API-Football error: status {response.status_code}")
            return None
        
        data = response.json()
        
        if data.get('results', 0) == 0:
            return None
        
        # Obtener el primer equipo encontrado
        teams = data.get('response', [])
        if not teams:
            return None
        
        team_info = teams[0].get('team', {})
        team_id = team_info.get('id')
        team_league = teams[0].get('league', {}).get('name', 'Desconocida')
        
        if not team_id:
            return None
        
        logger.info(f"   📡 Encontrado: {team_info.get('name')} (ID: {team_id})")
        
        # Obtener fixtures del equipo para calcular estadísticas
        fixtures_response = requests.get(
            f"{API_FOOTBALL_URL}/fixtures",
            headers=headers,
            params={
                'team': team_id,
                'season': 2024,
                'status': 'FT'  # Solo partidos completados
            },
            timeout=15
        )
        
        fixtures_data = fixtures_response.json() if fixtures_response.status_code == 200 else {}
        fixtures = fixtures_data.get('response', [])
        
        # Calcular estadísticas de los fixtures
        partidos = 0
        victorias = 0
        empates = 0
        derrotas = 0
        goles_favor = 0
        goles_contra = 0
        corners_total = 0
        tarjetas_amarillas = 0
        tarjetas_rojas = 0
        tiros_total = 0
        tiros_arco = 0
        partidos_local = 0
        partidos_visitante = 0
        goles_local = 0
        goles_visitante = 0
        
        for fixture in fixtures[:38]:  # Máximo 38 partidos
            fix = fixture.get('fixture', {})
            teams = fixture.get('teams', {})
            goals = fixture.get('goals', {})
            score = fixture.get('score', {})
            
            # Solo partidos completados
            if fix.get('status', {}).get('short') != 'FT':
                continue
            
            home_team = teams.get('home', {})
            away_team = teams.get('away', {})
            
            is_home = home_team.get('id') == team_id
            
            partidos += 1
            
            # Resultado
            home_goals = goals.get('home') or 0
            away_goals = goals.get('away') or 0
            
            if is_home:
                partidos_local += 1
                goles_local += home_goals
                goles_favor += home_goals
                goles_contra += away_goals
                
                if home_goals > away_goals:
                    victorias += 1
                elif home_goals == away_goals:
                    empates += 1
                else:
                    derrotas += 1
            else:
                partidos_visitante += 1
                goles_visitante += away_goals
                goles_favor += away_goals
                goles_contra += home_goals
                
                if away_goals > home_goals:
                    victorias += 1
                elif away_goals == home_goals:
                    empates += 1
                else:
                    derrotas += 1
        
        # Calcular lambdas
        lambda_local = 0
        lambda_visitante = 0
        
        if partidos_local > 0:
            lambda_local = round(goles_local / partidos_local, 2)
        
        if partidos_visitante > 0:
            lambda_visitante = round(goles_visitante / partidos_visitante, 2)
        
        result = {
            'equipo': team_info.get('name', team_name),
            'liga': team_league,
            'pais': team_info.get('country', ''),
            'partidos': partidos,
            'partidos_local': partidos_local,
            'partidos_visitante': partidos_visitante,
            'victorias': victorias,
            'empates': empates,
            'derrotas': derrotas,
            'goles_favor': goles_favor,
            'goles_contra': goles_contra,
            'lambda_local': lambda_local,
            'lambda_visitante': lambda_visitante,
            'goles_local': goles_local,
            'goles_visitante': goles_visitante,
            'source': 'api-football.com'
        }
        
        logger.info(f"   ✅ API-Football: {result['equipo']} - {partidos} partidos, λL={lambda_local}, λV={lambda_visitante}")
        return result
        
    except Exception as e:
        logger.warning(f"   ⚠️ API-Football error: {e}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# football-data.co.uk (SIN CLOUDFLARE - Acceso directo)
# ═══════════════════════════════════════════════════════════════════════════════

# Formato: https://www.football-data.co.uk/mmz4281/2324/E0.csv
# mmz4281 = directorio, 2324 = temporada 23/24, E0 = código de liga

FD_LEAGUE_URLS = {
    # Inglaterra
    'Premier League': 'https://www.football-data.co.uk/mmz4281/2324/E0.csv',
    'Championship': 'https://www.football-data.co.uk/mmz4281/2324/E1.csv',
    'League One': 'https://www.football-data.co.uk/mmz4281/2324/E2.csv',
    'League Two': 'https://www.football-data.co.uk/mmz4281/2324/E3.csv',
    # España
    'La Liga': 'https://www.football-data.co.uk/mmz4281/2324/SP1.csv',
    'Segunda Division': 'https://www.football-data.co.uk/mmz4281/2324/SP2.csv',
    # Italia
    'Serie A': 'https://www.football-data.co.uk/mmz4281/2324/I1.csv',
    'Serie B': 'https://www.football-data.co.uk/mmz4281/2324/I2.csv',
    # Alemania
    'Bundesliga': 'https://www.football-data.co.uk/mmz4281/2324/D1.csv',
    '2 Bundesliga': 'https://www.football-data.co.uk/mmz4281/2324/D2.csv',
    # Francia
    'Ligue 1': 'https://www.football-data.co.uk/mmz4281/2324/F1.csv',
    'Ligue 2': 'https://www.football-data.co.uk/mmz4281/2324/F2.csv',
    # Portugal
    'Primeira Liga': 'https://www.football-data.co.uk/mmz4281/2324/P1.csv',
    # Holanda
    'Eredivisie': 'https://www.football-data.co.uk/mmz4281/2324/N1.csv',
    # Belgica
    'Jupiler Pro League': 'https://www.football-data.co.uk/mmz4281/2324/B1.csv',
    # Grecia
    'Super League Greece': 'https://www.football-data.co.uk/mmz4281/2324/G1.csv',
    # Escoci
    'Scottish Premier League': 'https://www.football-data.co.uk/mmz4281/2324/SC0.csv',
    'Scottish League One': 'https://www.football-data.co.uk/mmz4281/2324/SC1.csv',
    # Turqua
    'Super Lig': 'https://www.football-data.co.uk/mmz4281/2324/T1.csv',
    # Rusia
    'Premier League Russia': 'https://www.football-data.co.uk/mmz4281/2324/R1.csv',
    # Polonia
    'Ekstraklasa': 'https://www.football-data.co.uk/mmz4281/2324/PO1.csv',
    # Austria
    'Bundesliga Austria': 'https://www.football-data.co.uk/mmz4281/2324/A1.csv',
    # Suiza
    'Super League Switzerland': 'https://www.football-data.co.uk/mmz4281/2324/S1.csv',
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTE CLOUDSCRAPER
# ═══════════════════════════════════════════════════════════════════════════════

def get_scraper():
    """Obtiene cliente cloudscraper configurado."""
    try:
        import cloudscraper
        scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        scraper.headers = CHROME_HEADERS.copy()
        return scraper
    except ImportError:
        logger.warning("cloudscraper no instalado, usando requests básico")
        import requests
        return requests.Session()

# ═══════════════════════════════════════════════════════════════════════════════
# URLs DE EQUIPOS FBBREF
# ═══════════════════════════════════════════════════════════════════════════════

FBREF_SQUADS = {
    # Premier League
    'Manchester City': '361ca564/Manchester-City-Stats',
    'Arsenal': 'b8b03df0/Arsenal-Stats',
    'Liverpool': '822bd0ba/Liverpool-Stats',
    'Chelsea': 'cff44d04/Chelsea-Stats',
    'Manchester United': '19538871/Manchester-United-Stats',
    'Tottenham': '361ca564/Tottenham-Hotspur-Stats',
    'Newcastle': 'b2b47a98/Newcastle-United-Stats',
    'Brighton': '0335a503/Brighton-and-Hove-Albion-Stats',
    'Aston Villa': '9600892f/Aston-Villa-Stats',
    'West Ham': '8eccca6e/West-Ham-United-Stats',
    'Crystal Palace': 'a2da8f83/Crystal-Palace-Stats',
    'Fulham': 'fd7b415d/Fulham-Stats',
    'Wolves': 'f7c6d7b0/Wolverhampton-Wanderers-Stats',
    'Brentford': 'cd05481d/Brentford-Stats',
    'Bournemouth': '4ba9d3a3/Bournemouth-Stats',
    'Nottingham Forest': 'e3a1d1fb/Nottingham-Forest-Stats',
    'Everton': 'd3fd31cc/Everton-Stats',
    'Leicester': 'a2d74b07/Leicester-City-Stats',
    
    # La Liga
    'Real Madrid': '53a2f82b/Real-Madrid-Stats',
    'Barcelona': '361ca564/FC-Barcelona-Stats',
    'Atletico Madrid': 'f7fab33c/Atletico-Madrid-Stats',
    'Real Sociedad': 'ee2d5bce/Real-Sociedad-Stats',
    'Athletic Bilbao': 'fbf6a8ae/Athletic-Club-Stats',
    'Sevilla': 'ad0bae88/Sevilla-Stats',
    'Villarreal': 'f8d357d5/Villarreal-Stats',
    'Real Betis': 'cd3fb8ef/Real-Betis-Stats',
    'Valencia': 'dcc91a7b/Valencia-Stats',
    'Getafe': '5e42e779/CE-Getafe-Stats',
    'Osasuna': 'd1fa625c/CA-Osasuna-Stats',
    'Celta Vigo': 'f9d8c7e1/Celta-Vigo-Stats',
    'Mallorca': 'c4e92e9c/RCD-Mallorca-Stats',
    'Las Palmas': 'e67a39d7/UD-Las-Palmas-Stats',
    'Rayo Vallecano': 'c6a3c0e5/Rayo-Vallecano-Stats',
    
    # Bundesliga
    'Bayern Munich': 'fc65c9f2/FC-Bayern-Munich-Stats',
    'Borussia Dortmund': 'addf9828/Borussia-Dortmund-Stats',
    'RB Leipzig': 'c18905e9/RB-Leipzig-Stats',
    'Bayer Leverkusen': 'b6967de9/Bayer-04-Leverkusen-Stats',
    'Eintracht Frankfurt': 'b5f85301/Eintracht-Frankfurt-Stats',
    'Wolfsburg': 'cd89f64e/VfL-Wolfsburg-Stats',
    'Freiburg': '2a6c2ca2/SC-Freiburg-Stats',
    'Dortmund': 'addf9828/Borussia-Dortmund-Stats',
    
    # Serie A
    'Inter Milan': 'd6f4e60c/Inter-Milan-Stats',
    'AC Milan': 'c8e86ee2/AC-Milan-Stats',
    'Juventus': '907a5e38/Juventus-Stats',
    'Napoli': 'a4f5a882/SSC-Napoli-Stats',
    'Roma': 'cf5a4e36/AS-Roma-Stats',
    'Lazio': 'a54f3f3d/Lazio-Stats',
    'Atalanta': 'bf5a23a5/Atalanta-Stats',
    'Fiorentina': '3e74e5c6/Fiorentina-Stats',
    'Bologna': '8c65c9e2/Bologna-Stats',
    
    # Ligue 1
    'PSG': 'e2d889f8/Paris-Saint-Germain-Stats',
    'Monaco': 'c1a2c7c5/AS-Monaco-Stats',
    'Marseille': '2abb4c5e/Olympique-Marseille-Stats',
    'Lyon': '8d70d3f8/Olympique-Lyon-Stats',
    'Lille': '176f3dc5/LOSC-Lille-Stats',
    'Nice': 'f98e0d8b/OGC-Nice-Stats',
    'Lens': 'a427c8b0/RC-Lens-Stats',
    'Rennes': 'a25b6e2c/Stade-Rennais-Stats',
    
    # Eredivisie
    'Ajax': '0a26a56a/Amsterdam-Ajax-Stats',
    'PSV': '5e42e779/PSV-Eindhoven-Stats',
    'PSV Eindhoven': '5e42e779/PSV-Eindhoven-Stats',
    'Feyenoord': 'e67a39d7/Feyenoord-Stats',
    'AZ': 'c7f10f1d/AZ-Alkmaar-Stats',
    'AZ Alkmaar': 'c7f10f1d/AZ-Alkmaar-Stats',
    'Twente': '9d1a7790/FC-Twente-Stats',
    
    # Liga MX
    'Club America': 'ce3c7e4d/Club-America-Stats',
    'Chivas': 'a1f1c6b2/Guadalajara-Stats',
    'Chivas Guadalajara': 'a1f1c6b2/Guadalajara-Stats',
    'Tigres': '2f22dc85/Tigres-Stats',
    'Tigres UANL': '2f22dc85/Tigres-Stats',
    'Monterrey': '1c7053a0/Monterrey-Stats',
    'Pumas': 'f1fda0b5/Pumas-Stats',
    'Pumas UNAM': 'f1fda0b5/Pumas-Stats',
    'Cruz Azul': '7ab4c0e3/Cruz-Azul-Stats',
    'Leon': '1e71c7c8/Leon-Stats',
    'Santos': '7c7a9c0e/Santos-Laguna-Stats',
    'Santos Laguna': '7c7a9c0e/Santos-Laguna-Stats',
    
    # Argentina
    'River Plate': 'a4f5a882/River-Plate-Stats',
    'Boca Juniors': 'c3b5a7d2/Boca-Juniors-Stats',
    'Racing Club': '7c7a9c0e/Racing-Club-Stats',
    'Estudiantes': '5e42e779/Estudiantes-Stats',
    'Defensa y Justicia': '3f60ea0a/Defensa-y-Justicia-Stats',
    'San Lorenzo': '1c7053a0/San-Lorenzo-Stats',
    'Velez Sarsfield': '8e74aee6/Velez-Sarsfield-Stats',
    'Huracan': '5c5c8a8e/Huracan-Stats',
    'Talleres': 'c1b5a7d2/Talleres-Stats',
    
    # Brasil
    'Flamengo': 'c11e6d8e/Flamengo-Stats',
    'Palmeiras': 'b4ba92a2/Palmeiras-Stats',
    'Corinthians': 'f39b7b2d/Corinthians-Stats',
    'Sao Paulo': 'c8e86ee2/Sao-Paulo-Stats',
    'Santos': '7c7a9c0e/Santos-Stats',
    'Internacional': '1c7053a0/Internacional-Stats',
    'Gremio': '5e42e779/Gremio-Stats',
    'Atletico Mineiro': 'c1a2c7c5/Atletico-Mineiro-Stats',
    'Fluminense': '7ab4c0e3/Fluminense-Stats',
    'Botafogo': '8e74aee6/Botafogo-Stats',
    
    # Colombia
    'Atletico Nacional': 'c1a2c7c5/Atletico-Nacional-Stats',
    'Millonarios': '7ab4c0e3/Millonarios-Stats',
    'Santa Fe': '1e71c7c8/Santa-Fe-Stats',
    'Junior': '5e42e779/Junior-Stats',
    'America de Cali': 'c1b5a7d2/America-de-Cali-Stats',
    'Once Caldas': '7c7a9c0e/Once-Caldas-Stats',
    'Independiente Medellin': '8e74aee6/Independiente-Medellin-Stats',
    
    # Chile
    'Colo Colo': 'c1a2c7c5/Colo-Colo-Stats',
    'Universidad de Chile': '7ab4c0e3/Universidad-de-Chile-Stats',
    'U de Chile': '7ab4c0e3/Universidad-de-Chile-Stats',
    'Catolica': '1e71c7c8/Catolica-Stats',
    'Union Española': '5e42e779/Union-Espanola-Stats',
    
    # Peru
    'Universitario': '7ab4c0e3/Universitario-Stats',
    'Alianza Lima': '1e71c7c8/Alianza-Lima-Stats',
    'Sporting Cristal': '5e42e779/Sporting-Cristal-Stats',
    'Melgar': '7c7a9c0e/Melgar-Stats',
    
    # Ecuador
    'LDU Quito': '7ab4c0e3/LDU-Quito-Stats',
    'Barcelona SC': 'c1a2c7c5/Barcelona-SC-Stats',
    'Emelec': '1e71c7c8/Emelec-Stats',
    'Independiente del Valle': '5e42e779/Independiente-del-Valle-Stats',
}

BASE_URL = "https://fbref.com/en/squads"


# ═══════════════════════════════════════════════════════════════════════════════
# ROBOT EXTRACTOR ANTI-BLOQUEO
# ═══════════════════════════════════════════════════════════════════════════════

class RobotExtractor:
    """
    Robot extractor con técnicas antibloqueo.
    """
    
    def __init__(self, use_proxy: bool = False, proxy_api_key: str = None):
        self.use_proxy = use_proxy
        self.proxy_api_key = proxy_api_key
        self.scraper = None
        self.request_count = 0
        
    def _get_scraper(self):
        """Obtiene o reutiliza el scraper."""
        if self.scraper is None:
            self.scraper = get_scraper()
        return self.scraper
    
    def _throttle(self):
        """Aplica retraso aleatorio entre requests (5-10 segundos)."""
        delay = random.randint(5, 10)
        logger.info(f"⏳ Esperando {delay} segundos...")
        time.sleep(delay)
    
    def _get_proxy_url(self, url: str) -> str:
        """Usa API proxy para obtener el HTML."""
        if not self.proxy_api_key:
            return None
        
        # ScrapingAnt API
        api_url = f"https://api.scrapingant.com/v2/general?url={url}&x-api-key={self.proxy_api_key}"
        return api_url
    
    def get_team_url(self, team_name: str) -> Optional[str]:
        """Busca la URL del equipo en el diccionario."""
        team_lower = team_name.lower().strip()
        
        # Búsqueda exacta
        for name, path in FBREF_SQUADS.items():
            if name.lower() == team_lower:
                return f"{BASE_URL}/{path}"
        
        # Búsqueda parcial
        for name, path in FBREF_SQUADS.items():
            if team_lower in name.lower() or name.lower() in team_lower:
                return f"{BASE_URL}/{path}"
        
        return None
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Obtiene el HTML de una página con técnicas antibloqueo.
        """
        try:
            # Si usa proxy
            if self.use_proxy and self.proxy_api_key:
                proxy_url = self._get_proxy_url(url)
                if proxy_url:
                    response = self.scraper.get(proxy_url, timeout=30)
                    if response.status_code == 200:
                        self.request_count += 1
                        return response.text
                    else:
                        logger.warning(f"Proxy error: {response.status_code}")
                        return None
            
            # Solicitud normal con cloudscraper
            scraper = self._get_scraper()
            response = scraper.get(url, timeout=30)
            
            if response.status_code == 200:
                self.request_count += 1
                logger.info(f"✅ Request #{self.request_count} exitoso")
                return response.text
            
            logger.warning(f"❌ Status: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetch_page: {e}")
            return None
    
    def extract_last_matches(self, team_url: str, num_matches: int = 5) -> List[Dict]:
        """
        Extrae los últimos N partidos del equipo.
        """
        html = self.fetch_page(team_url)
        if not html:
            return []
        
        matches = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Buscar tabla de partidos recientes
            tables = soup.find_all('table')
            
            for table in tables:
                table_id = table.get('id', '') or ''
                # FBref usa IDs como "matchlogs_control_...shooting"
                if 'matchlogs' in table_id.lower():
                    rows = table.find_all('tr')
                    
                    count = 0
                    for row in rows:
                        if count >= num_matches:
                            break
                        
                        cells = row.find_all(['td', 'th'])
                        if len(cells) < 5:
                            continue
                        
                        # Saltar headers
                        if cells[0].get('data-stat') == 'date':
                            continue
                        
                        match = {}
                        
                        # Extraer datos
                        for cell in cells:
                            stat = cell.get('data-stat', '')
                            value = cell.get_text(strip=True)
                            
                            if stat == 'date':
                                match['fecha'] = value
                            elif stat == 'comp':
                                match['competencia'] = value
                            elif stat == 'opponent':
                                match['rival'] = value
                            elif stat == 'result':
                                match['resultado'] = value
                                # Extraer score
                                score = re.search(r'(\d+)\s*[-–]\s*(\d+)', value)
                                if score:
                                    match['goles_nuestros'] = int(score.group(1))
                                    match['goles_rival'] = int(score.group(2))
                            elif stat == 'shots':
                                match['remates'] = int(value) if value.isdigit() else 0
                            elif stat == 'shots_on_target':
                                match['remates_arco'] = int(value) if value.isdigit() else 0
                            elif stat == 'yellow_cards':
                                match['amarillas'] = int(value) if value.isdigit() else 0
                            elif stat == 'red_cards':
                                match['rojas'] = int(value) if value.isdigit() else 0
                            elif stat == 'corners':
                                match['corners'] = int(value) if value.isdigit() else 0
                            elif stat == 'possession':
                                match['posesion'] = value
                            elif stat == 'venue':
                                match['local'] = value.lower() == 'home'
                        
                        if match.get('fecha'):
                            matches.append(match)
                            count += 1
            
            return matches[:num_matches]
            
        except Exception as e:
            logger.error(f"Error extract_last_matches: {e}")
            return []
    
    def calculate_stats(self, matches: List[Dict]) -> Dict:
        """
        Calcula estadísticas promediadas de los partidos.
        """
        if not matches:
            return {}
        
        n = len(matches)
        
        total_remates = sum(m.get('remates', 0) for m in matches)
        total_arco = sum(m.get('remates_arco', 0) for m in matches)
        total_amarillas = sum(m.get('amarillas', 0) for m in matches)
        total_rojas = sum(m.get('rojas', 0) for m in matches)
        total_corners = sum(m.get('corners', 0) for m in matches)
        total_gf = sum(m.get('goles_nuestros', 0) for m in matches)
        total_gc = sum(m.get('goles_rival', 0) for m in matches)
        
        # Posesión promedio
        posesiones = []
        for m in matches:
            p = m.get('posesion', '')
            if '%' in p:
                try:
                    posesiones.append(float(p.replace('%', '')))
                except:
                    pass
        
        return {
            'partidos': n,
            'partidos_local': sum(1 for m in matches if m.get('local', True)),
            'partidos_visitante': sum(1 for m in matches if not m.get('local', True)),
            'victorias': sum(1 for m in matches if m.get('goles_nuestros', 0) > m.get('goles_rival', 0)),
            'empates': sum(1 for m in matches if m.get('goles_nuestros', 0) == m.get('goles_rival', 0)),
            'derrotas': sum(1 for m in matches if m.get('goles_nuestros', 0) < m.get('goles_rival', 0)),
            'goles_favor': total_gf,
            'goles_contra': total_gc,
            'promedio_remates': round(total_remates / n, 1),
            'promedio_remates_arco': round(total_arco / n, 1),
            'promedio_amarillas': round(total_amarillas / n, 1),
            'promedio_rojas': round(total_rojas / n, 2),
            'promedio_corners': round(total_corners / n, 1),
            'promedio_posesion': round(sum(posesiones) / len(posesiones), 1) if posesiones else 50,
            'lambda_local': round((total_gf / n) * 1.1, 2),
            'lambda_visitante': round((total_gf / n) * 0.85, 2),
        }
    
    def extract_team(self, team_name: str, num_matches: int = 5) -> Dict:
        """
        Función principal: Extrae estadísticas de un equipo.
        """
        logger.info(f"🔍 Extrayendo: {team_name}")
        
        # Obtener URL
        url = self.get_team_url(team_name)
        if not url:
            logger.warning(f"❌ URL no encontrada para: {team_name}")
            return {
                'equipo': team_name,
                'encontrado': False,
                'source': 'fbref',
                'matches': [],
                'stats': {}
            }
        
        # Aplicar throttling
        self._throttle()
        
        # Extraer partidos
        matches = self.extract_last_matches(url, num_matches)
        
        # Calcular estadísticas
        stats = self.calculate_stats(matches)
        
        return {
            'equipo': team_name,
            'encontrado': len(matches) > 0,
            'source': 'fbref',
            'url': url,
            'matches': matches,
            'stats': stats
        }
    
    def extract_batch(self, teams: List[str], num_matches: int = 5) -> List[Dict]:
        """
        Extrae estadísticas de múltiples equipos.
        Con throttling automático entre cada uno.
        """
        results = []
        
        for i, team in enumerate(teams):
            logger.info(f"📊 Progreso: {i+1}/{len(teams)}")
            result = self.extract_team(team, num_matches)
            results.append(result)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def run_robot_fbref(teams: List[str], use_proxy: bool = False, proxy_api_key: str = None) -> List[Dict]:
    """
    Ejecuta el robot extractor de FBref.
    
    Args:
        teams: Lista de nombres de equipos
        use_proxy: Usar API proxy si está bloqueado
        proxy_api_key: API key de ScrapingAnt/Crawlbase
    
    Returns:
        Lista de resultados con estadísticas
    """
    robot = RobotExtractor(use_proxy=use_proxy, proxy_api_key=proxy_api_key)
    return robot.extract_batch(teams)


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# football-data.co.uk - DESCARGAR DATOS
# ═══════════════════════════════════════════════════════════════════════════════

_fd_cache = {}

def get_football_data_stats() -> Dict:
    """Descarga estadísticas de football-data.co.uk (acceso directo, sin Cloudflare)."""
    global _fd_cache
    if _fd_cache:
        return _fd_cache
    
    import csv
    from io import StringIO
    import requests
    
    all_stats = {}
    
    logger.info(f"📥 Descargando datos de football-data.co.uk ({len(FD_LEAGUE_URLS)} ligas)...")
    
    for league, url in FD_LEAGUE_URLS.items():
        try:
            # Delay menor - 0.5 segundos entre descargas
            delay = random.uniform(0.3, 0.8)
            time.sleep(delay)
            
            session = requests.Session()
            # Usar headers específicos para football-data
            r = session.get(url, timeout=15, headers=FD_HEADERS)
            
            if r.status_code != 200 or not r.content:
                logger.warning(f"   ⚠️ {league}: Sin datos (status {r.status_code})")
                continue
            
            # Detectar si es CSV o HTML (si hay redirect a página HTML)
            content = r.content
            if b'<html' in content.lower() or b'<!doctype' in content.lower():
                logger.warning(f"   ⚠️ {league}: Redirigió a HTML, no CSV")
                continue
            
            reader = csv.DictReader(StringIO(content.decode('utf-8', errors='ignore')))
            row_count = 0
            
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
                
                # Guardar stats del equipo local
                if home not in all_stats:
                    all_stats[home] = {
                        'equipo': home,
                        'liga': league,
                        'partidos': 0,
                        'goles_favor': 0,
                        'goles_contra': 0,
                        'victorias': 0,
                        'empates': 0,
                        'derrotas': 0,
                        'source': 'football-data.co.uk'
                    }
                all_stats[home]['partidos'] += 1
                all_stats[home]['goles_favor'] += gh
                all_stats[home]['goles_contra'] += ga
                if gh > ga:
                    all_stats[home]['victorias'] += 1
                elif gh == ga:
                    all_stats[home]['empates'] += 1
                else:
                    all_stats[home]['derrotas'] += 1
                
                # Guardar stats del equipo visitante
                if away not in all_stats:
                    all_stats[away] = {
                        'equipo': away,
                        'liga': league,
                        'partidos': 0,
                        'goles_favor': 0,
                        'goles_contra': 0,
                        'victorias': 0,
                        'empates': 0,
                        'derrotas': 0,
                        'source': 'football-data.co.uk'
                    }
                all_stats[away]['partidos'] += 1
                all_stats[away]['goles_favor'] += ga
                all_stats[away]['goles_contra'] += gh
                if ga > gh:
                    all_stats[away]['victorias'] += 1
                elif ga == gh:
                    all_stats[away]['empates'] += 1
                else:
                    all_stats[away]['derrotas'] += 1
                    
                row_count += 1
            
            if row_count > 0:
                logger.info(f"   ✅ {league}: {row_count} partidos")
            
        except Exception as e:
            logger.error(f"   ❌ Error en {league}: {e}")
    
    _fd_cache = all_stats
    logger.info(f"📊 Total equipos cargados: {len(all_stats)}")
    return all_stats


def get_team_stats_from_football_data(team_name: str) -> Optional[Dict]:
    """Busca estadísticas de un equipo específico."""
    stats = get_football_data_stats()
    
    # Busqueda exacta primero
    if team_name in stats:
        return stats[team_name]
    
    # Busqueda parcial (ignorar acentos y mayusculas)
    team_lower = team_name.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
    for equipo, data in stats.items():
        eq_lower = equipo.lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u')
        if team_lower in eq_lower or eq_lower in team_lower:
            return data
    
    return None


def run_football_data_batch(team_names: List[str]) -> List[Dict]:
    """Procesa una lista de equipos y retorna sus estadísticas."""
    results = []
    
    for team in team_names:
        stats = get_team_stats_from_football_data(team)
        if stats:
            results.append({
                'equipo': team,
                'encontrado': True,
                'stats': stats,
                'source': 'football-data.co.uk'
            })
        else:
            results.append({
                'equipo': team,
                'encontrado': False,
                'source': 'football-data.co.uk'
            })
    
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# WhoScored - Corners, Tarjetas, Posesión
# ═══════════════════════════════════════════════════════════════════════════════

class WhoScoredScraper:
    """Scraper para WhoScored.com - Stats avanzadas (corners, tarjetas, posesión)"""
    
    BASE_URL = "https://www.whoscored.com"
    
    def __init__(self):
        # Usar cloudscraper para evadir Cloudflare
        self.scraper = get_scraper()
    
    def search_team(self, team_name: str) -> Optional[str]:
        """Busca un equipo y devuelve su URL."""
        try:
            url = f"{self.BASE_URL}/Search/?keyword={team_name.replace(' ', '+')}"
            response = self.scraper.get(url, timeout=15)
            
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
        """Obtiene estadísticas avanzadas del equipo."""
        try:
            delay = random.randint(5, 10)
            time.sleep(delay)
            
            response = self.scraper.get(team_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = {
                'source': 'whoscored',
                'promedio_corners': 0,
                'promedio_tarjetas': 0,
                'promedio_posesion': 50.0,
                'promedio_remates': 0,
                'promedio_rematesPuerta': 0,
                'faltas': 0,
                'tarjetas_amarillas': 0,
                'tarjetas_rojas': 0,
                'posesion_local': 0,
                'posesion_visitante': 0,
                'corners_local': 0,
                'corners_visitante': 0,
                'ultimos_partidos': []
            }
            
            # Buscar estadísticas en la página
            # WhoScored muestra stats en tablas con clase "matchStats"
            stats_table = soup.find('div', {'id': 'team-match-stats'})
            if stats_table:
                rows = stats_table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        label = cells[0].get_text(strip=True).lower()
                        local_val = cells[1].get_text(strip=True)
                        away_val = cells[2].get_text(strip=True)
                        
                        try:
                            if 'corner' in label:
                                stats['corners_local'] = float(local_val) if local_val else 0
                                stats['corners_visitante'] = float(away_val) if away_val else 0
                                stats['promedio_corners'] = (stats['corners_local'] + stats['corners_visitante']) / 2
                            elif 'yellow card' in label:
                                stats['tarjetas_amarillas'] = int(local_val) if local_val else 0
                            elif 'red card' in label:
                                stats['tarjetas_rojas'] = int(local_val) if local_val else 0
                            elif 'foul' in label:
                                stats['faltas'] = int(local_val) if local_val else 0
                            elif 'shot' in label and 'on target' not in label:
                                stats['promedio_remates'] = float(local_val) if local_val else 0
                        except:
                            pass
            
            # Buscar posesión
            possession_div = soup.find('div', {'id': 'team-possession'})
            if possession_div:
                spans = possession_div.find_all('span')
                for span in spans:
                    text = span.get_text(strip=True)
                    if '%' in text:
                        try:
                            val = float(text.replace('%', ''))
                            if stats['promedio_posesion'] == 50.0:
                                stats['promedio_posesion'] = val
                            else:
                                stats['promedio_posesion'] = (stats['promedio_posesion'] + val) / 2
                        except:
                            pass
            
            # Extraer últimos partidos del equipo
            recent_matches = soup.find_all('div', {'class': 'match'})
            for match in recent_matches[:5]:
                score = match.find('div', {'class': 'scoreboard'})
                if score:
                    stats['ultimos_partidos'].append(score.get_text(strip=True))
            
            return stats
        except Exception as e:
            logger.debug(f"Error en WhoScored get_team_stats: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# FBref - Estadísticas Detalladas
# ═══════════════════════════════════════════════════════════════════════════════

class FBrefAdvancedScraper:
    """Scraper para FBref.com - Stats detalladas de equipos"""
    
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
        self.session.headers.update(CHROME_HEADERS)
        self._squads_cache = {}
    
    def _get_squads(self, league: str) -> Dict[str, str]:
        """Obtiene equipos de una liga."""
        if league in self._squads_cache:
            return self._squads_cache[league]
        
        try:
            url = self.SQUAD_URLS.get(league)
            if not url:
                return {}
            
            delay = random.randint(5, 10)
            time.sleep(delay)
            
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
            return squads
        except Exception as e:
            logger.debug(f"Error en FBref _get_squads: {e}")
            return {}
    
    def find_team(self, team_name: str, league: str = None) -> Optional[Dict]:
        """Busca un equipo y devuelve su URL y nombre."""
        leagues_to_search = [league] if league else list(self.SQUAD_URLS.keys())
        
        for lg in leagues_to_search:
            squads = self._get_squads(lg)
            team_lower = team_name.lower()
            
            # Busqueda exacta
            for name, url in squads.items():
                if team_lower == name.lower():
                    return {'name': name, 'url': url, 'league': lg}
            
            # Busqueda parcial
            for name, url in squads.items():
                if team_lower in name.lower() or name.lower() in team_lower:
                    return {'name': name, 'url': url, 'league': lg}
        
        return None
    
    def get_team_stats(self, team_url: str) -> Optional[Dict]:
        """Obtiene estadísticas detalladas del equipo."""
        try:
            delay = random.randint(5, 10)
            time.sleep(delay)
            
            response = self.session.get(team_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            stats = {
                'source': 'fbref',
                'partidos': 0,
                'goles_favor': 0,
                'goles_contra': 0,
                'victorias': 0,
                'empates': 0,
                'derrotas': 0,
                'promedio_goles': 0,
                'promedio_posesion': 50.0,
                'promedio_remates': 0,
                'promedio_rematesPuerta': 0,
                'promedio_faltas': 0,
                'promedio_corners': 0,
                'promedio_tarjetas': 0,
            }
            
            # FBref tiene tablas con estadísticas de equipo
            # Buscar la tabla principal de estadísticas
            tables = soup.find_all('table')
            
            for table in tables:
                # Buscar la tabla de "Stats" del equipo
                thead = table.find('thead')
                if thead:
                    headers = [th.get_text(strip=True).lower() for th in thead.find_all('th')]
                    
                    # Si es una tabla de estadísticas de equipo
                    if 'mp' in headers or 'matches' in headers or 'games' in headers:
                        tbody = table.find('tbody')
                        if tbody:
                            rows = tbody.find_all('tr')
                            for row in rows:
                                cells = row.find_all('td')
                                if cells and len(cells) >= len(headers):
                                    try:
                                        # Parsear según los headers
                                        cell_dict = dict(zip(headers, [c.get_text(strip=True) for c in cells]))
                                        
                                        # Extraer datos relevantes
                                        if 'mp' in cell_dict:
                                            stats['partidos'] = int(cell_dict['mp'].replace(',', ''))
                                        if 'gf' in cell_dict:
                                            stats['goles_favor'] = int(cell_dict['gf'].replace(',', ''))
                                        if 'ga' in cell_dict:
                                            stats['goles_contra'] = int(cell_dict['ga'].replace(',', ''))
                                        if 'w' in cell_dict:
                                            stats['victorias'] = int(cell_dict['w'].replace(',', ''))
                                        if 'd' in cell_dict:
                                            stats['empates'] = int(cell_dict['d'].replace(',', ''))
                                        if 'l' in cell_dict:
                                            stats['derrotas'] = int(cell_dict['l'].replace(',', ''))
                                            
                                        # Calcular promedios
                                        if stats['partidos'] > 0:
                                            stats['promedio_goles'] = round(stats['goles_favor'] / stats['partidos'], 2)
                                            
                                    except Exception as e:
                                        continue
            
            # Buscar estadísticas avanzadas en divs específicos
            stat_groups = soup.find_all('div', {'class': 'stat_group'})
            for group in stat_groups:
                group_text = group.get_text(strip=True).lower()
                if 'possession' in group_text:
                    # Extraer posesión
                    numbers = re.findall(r'(\d+(?:\.\d+)?)\s*%', group_text)
                    if numbers:
                        stats['promedio_posesion'] = float(numbers[0])
            
            return stats
        except Exception as e:
            logger.debug(f"Error en FBref get_team_stats: {e}")
            return None


# ═══════════════════════════════════════════════════════════════════════════════
# Soccerway - Resultados Históricos
# ═══════════════════════════════════════════════════════════════════════════════

class SoccerwayScraper:
    """Scraper para Soccerway.com - Resultados históricos de equipos"""
    
    BASE_URL = "https://int.soccerway.com"
    
    def __init__(self):
        # Usar cloudscraper para evadir posibles bloqueos
        self.scraper = get_scraper()
    
    def search_team(self, team_name: str) -> Optional[str]:
        """Busca un equipo y devuelve su URL."""
        try:
            url = f"{self.BASE_URL}/search/?q={team_name.replace(' ', '+')}"
            response = self.scraper.get(url, timeout=15)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=re.compile(r'/teams/[a-z-]+/\d+'))
            
            for link in links:
                if team_name.lower() in link.get_text().lower():
                    href = link.get('href')
                    if href:
                        return self.BASE_URL + href if href.startswith('/') else href
            return None
        except Exception as e:
            logger.debug(f"Error en Soccerway search: {e}")
            return None
    
    def get_team_results(self, team_url: str, num_matches: int = 10) -> List[Dict]:
        """Obtiene los últimos resultados del equipo."""
        results = []
        try:
            delay = random.randint(5, 10)
            time.sleep(delay)
            
            response = self.scraper.get(team_url, timeout=15)
            if response.status_code != 200:
                return results
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Soccerway tiene tablas con resultados
            # Buscar la tabla de resultados recientes
            match_rows = soup.find_all('tr', {'class': 'match'})
            
            for row in match_rows[:num_matches]:
                try:
                    # Extraer fecha
                    date_cell = row.find('td', {'class': 'date'})
                    date = date_cell.get_text(strip=True) if date_cell else ''
                    
                    # Extraer equipo local
                    home_cell = row.find('td', {'class': 'team-a'})
                    home_link = home_cell.find('a') if home_cell else None
                    home_team = home_link.get_text(strip=True) if home_link else ''
                    home_href = home_link.get('href') if home_link else ''
                    
                    # Extraer equipo visitante
                    away_cell = row.find('td', {'class': 'team-b'})
                    away_link = away_cell.find('a') if away_cell else None
                    away_team = away_link.get_text(strip=True) if away_link else ''
                    
                    # Extraer marcador
                    score_cell = row.find('td', {'class': 'score'})
                    if score_cell:
                        score_text = score_cell.get_text(strip=True)
                        # Parsear "2 - 1" o "2-1"
                        parts = re.split(r'[-\s]+', score_text)
                        if len(parts) >= 2:
                            try:
                                home_score = int(parts[0])
                                away_score = int(parts[1])
                            except:
                                home_score, away_score = 0, 0
                        else:
                            home_score, away_score = 0, 0
                    else:
                        home_score, away_score = 0, 0
                    
                    # Extraer liga/competencia
                    competition_cell = row.find('td', {'class': 'competition'})
                    competition = competition_cell.get_text(strip=True) if competition_cell else ''
                    
                    result = {
                        'fecha': date,
                        'liga': competition,
                        'local': home_team,
                        'visitante': away_team,
                        'goles_local': home_score,
                        'goles_visitante': away_score,
                        'marcador': f"{home_score}-{away_score}",
                        'resultado': 'victoria' if home_score > away_score else ('derrota' if home_score < away_score else 'empate')
                    }
                    results.append(result)
                    
                except Exception as e:
                    logger.debug(f"Error parseando partido: {e}")
                    continue
            
            return results
        except Exception as e:
            logger.debug(f"Error en Soccerway get_team_results: {e}")
            return results
    
    def get_team_stats_summary(self, team_url: str) -> Dict:
        """Obtiene resumen de estadísticas del equipo."""
        results = self.get_team_results(team_url, num_matches=20)
        
        if not results:
            return {}
        
        stats = {
            'partidos': len(results),
            'victorias': 0,
            'empates': 0,
            'derrotas': 0,
            'goles_favor': 0,
            'goles_contra': 0,
            'promedio_goles': 0,
            'victorias_local': 0,
            'victorias_visitante': 0,
            'source': 'soccerway'
        }
        
        for r in results:
            stats['goles_favor'] += r['goles_local']
            stats['goles_contra'] += r['goles_visitante']
            
            if r['resultado'] == 'victoria':
                stats['victorias'] += 1
            elif r['resultado'] == 'empate':
                stats['empates'] += 1
            else:
                stats['derrotas'] += 1
        
        stats['promedio_goles'] = round((stats['goles_favor'] + stats['goles_contra']) / stats['partidos'], 2) if stats['partidos'] > 0 else 0
        
        return stats


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER UNIFICADO - Combina todas las fuentes
# ═══════════════════════════════════════════════════════════════════════════════

class SuperRobot:
    """
    Robot unificado que combina todas las fuentes:
    - football-data.co.uk (principal, sin bloqueo)
    - FBref (stats detalladas, con cloudscraper)
    - WhoScored (corners, tarjetas, posesión)
    - Soccerway (resultados históricos)
    """
    
    def __init__(self):
        self.fd_stats = None
        self.whoscored = WhoScoredScraper()
        self.fbref = FBrefAdvancedScraper()
        self.soccerway = SoccerwayScraper()
        self.scraper = get_scraper()
    
    def get_team_complete_stats(self, team_name: str, league: str = None) -> Dict:
        """
        Obtiene estadísticas completas de un equipo desde todas las fuentes.
        """
        result = {
            'equipo': team_name,
            'fuentes': [],
            'stats': {}
        }
        
        # 1. football-data.co.uk (siempre disponible)
        if not self.fd_stats:
            self.fd_stats = get_football_data_stats()
        
        fd_data = get_team_stats_from_football_data(team_name)
        if fd_data:
            result['stats']['football_data'] = fd_data
            result['fuentes'].append('football-data.co.uk')
        
        # 2. FBref
        try:
            fbref_team = self.fbref.find_team(team_name, league)
            if fbref_team:
                fbref_stats = self.fbref.get_team_stats(fbref_team['url'])
                if fbref_stats:
                    result['stats']['fbref'] = fbref_stats
                    result['fuentes'].append('fbref')
        except Exception as e:
            logger.debug(f"FBref error: {e}")
        
        # 3. WhoScored
        try:
            ws_url = self.whoscored.search_team(team_name)
            if ws_url:
                ws_stats = self.whoscored.get_team_stats(ws_url)
                if ws_stats:
                    result['stats']['whoscored'] = ws_stats
                    result['fuentes'].append('whoscored')
        except Exception as e:
            logger.debug(f"WhoScored error: {e}")
        
        # 4. Soccerway
        try:
            sw_url = self.soccerway.search_team(team_name)
            if sw_url:
                sw_results = self.soccerway.get_team_results(sw_url)
                if sw_results:
                    result['stats']['soccerway'] = sw_results
                    result['fuentes'].append('soccerway')
        except Exception as e:
            logger.debug(f"Soccerway error: {e}")
        
        return result
    
    def run_batch(self, teams: List[str], leagues: List[str] = None) -> List[Dict]:
        """Procesa una lista de equipos y retorna estadísticas completas."""
        results = []
        
        for i, team in enumerate(teams):
            print(f"[{i+1}/{len(teams)}] 🔍 {team}...")
            
            league = leagues[i] if leagues and i < len(leagues) else None
            stats = self.get_team_complete_stats(team, league)
            results.append(stats)
            
            # Delay entre equipos
            delay = random.randint(5, 10)
            print(f"   ⏳ Esperando {delay}s...")
            time.sleep(delay)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES DE COMPATIBILIDAD PARA elite.py
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_team_lambda(goles_favor: int, goles_contra: int, partidos: int, is_home: bool = True) -> float:
    """
    Calcula el lambda (promedio de goles esperados) para un equipo.
    is_home=True: Lambda para cuando juega de local
    is_home=False: Lambda para cuando juega de visitante
    """
    if partidos == 0:
        return 1.5 if is_home else 1.2
    
    # Promedio de goles por partido
    promedio_goles = (goles_favor + goles_contra) / partidos
    
    # Ajuste por local/visitante
    # Equipos locales marcan ~0.3 goles más que visitantes
    if is_home:
        return round(promedio_goles * 1.15, 2)  # Un poco más de gol como local
    else:
        return round(promedio_goles * 0.85, 2)  # Un poco menos como visitante


def run_robot_batch(team_names: List[str]) -> List[Dict]:
    """
    Función de compatibilidad para stats_robot.run_robot_batch
    Procesa una lista de equipos y retorna estadísticas en formato compatible con elite.py.
    
    FLUJO:
    1. football-data.co.uk → Busca TODOS los equipos (sin límite)
    2. API-Football → Busca SOLO equipos sin datos (máximo 88)
    
    En cuanto una fuente encuentra datos → USA ESOS y PARA.
    """
    MAX_API_FOOTBALL = 88  # Límite de API-Football
    
    results = []
    logger.info(f"🔍 Procesando {len(team_names)} equipos...")
    
    # Preparar football-data (cargar en cache)
    logger.info("📥 Preparando football-data.co.uk...")
    fd_stats = get_football_data_stats()
    logger.info(f"   ✅ {len(fd_stats)} equipos en cache")
    
    # PASO 1: Buscar TODOS los equipos en football-data (sin límite)
    logger.info("="*50)
    logger.info("📊 PASO 1: Buscando en football-data.co.uk (TODOS los equipos)")
    logger.info("="*50)
    
    for i, team_name in enumerate(team_names):
        logger.info(f"[{i+1}/{len(team_names)}] 🔍 {team_name}...")
        
        try:
            fd_data = get_team_stats_from_football_data(team_name)
            if fd_data:
                gf = fd_data.get('goles_favor', 0)
                gc = fd_data.get('goles_contra', 0)
                p = fd_data.get('partidos', 0)
                lambda_local = calculate_team_lambda(gf, gc, p, is_home=True)
                lambda_visitante = calculate_team_lambda(gf, gc, p, is_home=False)
                
                result = {
                    'equipo': team_name,
                    'encontrado': True,
                    'exito': True,
                    'sin_estadisticas': False,
                    'equipo_real': fd_data.get('equipo', team_name),
                    'liga': fd_data.get('liga', 'Desconocida'),
                    'lambda_local': round(lambda_local, 2),
                    'lambda_visitante': round(lambda_visitante, 2),
                    'goles_favor': gf,
                    'goles_contra': gc,
                    'partidos_jugados': p,
                    'victorias': fd_data.get('victorias', 0),
                    'empates': fd_data.get('empates', 0),
                    'derrotas': fd_data.get('derrotas', 0),
                    'fuentes_probadas': ['football-data.co.uk'],
                }
                logger.info(f"   ✅ ENCONTRADO: λL={result['lambda_local']}, λV={result['lambda_visitante']}")
                results.append(result)
            else:
                # NO encontrado en football-data → marcar para buscar en API
                results.append({
                    'equipo': team_name,
                    'encontrado': False,
                    'exito': True,
                    'sin_estadisticas': True,
                    'equipo_real': team_name,
                    'liga': 'PENDIENTE',
                    'lambda_local': 0,
                    'lambda_visitante': 0,
                    'goles_favor': 0,
                    'goles_contra': 0,
                    'partidos_jugados': 0,
                    'victorias': 0,
                    'empates': 0,
                    'derrotas': 0,
                    'fuentes_probadas': ['NINGUNA'],
                })
                logger.info(f"   ❌ NO encontrado → Pendiente para API")
        except Exception as e:
            logger.warning(f"   ⚠️ Error: {e}")
            results.append({
                'equipo': team_name,
                'encontrado': False,
                'exito': True,
                'sin_estadisticas': True,
                'equipo_real': team_name,
                'liga': 'ERROR',
                'lambda_local': 0,
                'lambda_visitante': 0,
                'goles_favor': 0,
                'goles_contra': 0,
                'partidos_jugados': 0,
                'victorias': 0,
                'empates': 0,
                'derrotas': 0,
                'fuentes_probadas': ['ERROR'],
            })
    
    # PASO 2: Buscar equipos NO encontrados en API-Football
    pendientes = [r for r in results if r.get('encontrado') == False]
    
    if pendientes:
        # Limitar a 88 equipos máximo para API-Football
        if len(pendientes) > MAX_API_FOOTBALL:
            logger.warning(f"⚠️ Limitando a {MAX_API_FOOTBALL} equipos para API-Football (hay {len(pendientes)} pendientes)")
            pendientes = pendientes[:MAX_API_FOOTBALL]
        
        logger.info("="*50)
        logger.info(f"📊 PASO 2: Buscando {len(pendientes)} equipos en API-Football (máx. {MAX_API_FOOTBALL})")
        logger.info("⚠️ Rate limit: 10 solicitudes/minuto - Delay de 7s entre equipos")
        logger.info("="*50)
        
        for i, result in enumerate(results):
            if result.get('encontrado') == True:
                continue
            
            team_name = result['equipo']
            logger.info(f"[{i+1}/{len(results)}] 🔍 {team_name}...")
            
            try:
                api_data = search_team_api_football(team_name)
                
                if api_data:
                    result['encontrado'] = True
                    result['exito'] = True
                    result['sin_estadisticas'] = False
                    result['equipo_real'] = api_data.get('equipo', team_name)
                    result['liga'] = api_data.get('liga', 'Desconocida')
                    result['lambda_local'] = api_data.get('lambda_local', 0)
                    result['lambda_visitante'] = api_data.get('lambda_visitante', 0)
                    result['goles_favor'] = api_data.get('goles_favor', 0)
                    result['goles_contra'] = api_data.get('goles_contra', 0)
                    result['partidos_jugados'] = api_data.get('partidos', 0)
                    result['victorias'] = api_data.get('victorias', 0)
                    result['empates'] = api_data.get('empates', 0)
                    result['derrotas'] = api_data.get('derrotas', 0)
                    result['fuentes_probadas'] = ['api-football.com']
                    
                    logger.info(f"   ✅ ENCONTRADO: λL={result['lambda_local']}, λV={result['lambda_visitante']}")
                else:
                    result['liga'] = 'NO ENCONTRADO'
                    logger.info(f"   ❌ NO encontrado")
            except Exception as e:
                logger.warning(f"   ⚠️ API Error: {e}")
                result['liga'] = 'ERROR'
            
            # Delay para evitar rate limit (7 segundos entre equipos)
            if i < len(results) - 1:
                logger.info("   ⏳ Esperando 7s para evitar rate limit...")
                time.sleep(7)
    
    # Resumen
    encontrados = sum(1 for r in results if r.get('encontrado') == True)
    no_encontrados = sum(1 for r in results if r.get('encontrado') == False)
    
    logger.info("="*50)
    logger.info(f"✅ SUPERROBOT COMPLETADO")
    logger.info(f"   Encontrados: {encontrados}")
    logger.info(f"   No encontrados: {no_encontrados}")
    logger.info("="*50)
    
    return results


def scrape_team_fallback(team_name: str) -> Dict:
    """
    Función de compatibilidad para scrapers_fallback.scrape_team_fallback
    Busca un equipo en football-data.co.uk
    """
    fd_data = get_team_stats_from_football_data(team_name)
    
    if fd_data:
        # Calcular lambdas
        gf = fd_data.get('goles_favor', 0)
        gc = fd_data.get('goles_contra', 0)
        p = fd_data.get('partidos', 0)
        
        return {
            'equipo': team_name,
            'encontrado': True,
            'stats': {
                'equipo': fd_data.get('equipo', team_name),
                'liga': fd_data.get('liga', ''),
                'partidos': p,
                'goles_favor': gf,
                'goles_contra': gc,
                'lambda_local': calculate_team_lambda(gf, gc, p, is_home=True),
                'lambda_visitante': calculate_team_lambda(gf, gc, p, is_home=False),
            },
            'source': 'football-data.co.uk'
        }
    
    return {
        'equipo': team_name,
        'encontrado': False,
        'stats': {},
        'source': 'fallback'
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PRUEBA
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    # Prueba con algunos equipos
    test_teams = ['Barcelona', 'Real Madrid', 'PSG']
    
    print("=" * 60)
    print("PRUEBA: SuperRobot - Todas las fuentes")
    print("=" * 60)
    
    robot = SuperRobot()
    
    for team in test_teams:
        print(f"\n🔍 {team}...")
        result = robot.get_team_complete_stats(team)
        
        print(f"   📡 Fuentes: {result['fuentes']}")
        if 'football_data' in result['stats']:
            fd = result['stats']['football_data']
            print(f"   ⚽ Partidos: {fd.get('partidos', 0)}, GF: {fd.get('goles_favor', 0)}, GC: {fd.get('goles_contra', 0)}")
