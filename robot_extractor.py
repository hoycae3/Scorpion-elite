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
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE HEADERS (Chrome de escritorio real)
# ═══════════════════════════════════════════════════════════════════════════════

CHROME_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9,es;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Cache-Control': 'max-age=0',
}

# ═══════════════════════════════════════════════════════════════════════════════
# football-data.co.uk (SIN CLOUDFLARE - Acceso directo)
# ═══════════════════════════════════════════════════════════════════════════════

FD_LEAGUE_URLS = {
    # Inglaterra
    'Premier League': 'https://www.football-data.co.uk/england.csv',
    'Championship': 'https://www.football-data.co.uk/england.csv',
    'League One': 'https://www.football-data.co.uk/england.csv',
    # España
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
    # Portugal
    'Primeira Liga': 'https://www.football-data.co.uk/portugal.csv',
    # Holanda
    'Eredivisie': 'https://www.football-data.co.uk/netherlands.csv',
    # Belgica
    'Jupiler Pro League': 'https://www.football-data.co.uk/belgium.csv',
    # Grecia
    'Super League Greece': 'https://www.football-data.co.uk/greece.csv',
    # Escoci
    'Scottish Premier League': 'https://www.football-data.co.uk/scotland.csv',
    'Scottish League One': 'https://www.football-data.co.uk/scotland.csv',
    # Turqua
    'Super Lig': 'https://www.football-data.co.uk/turkey.csv',
    # Rusia
    'Premier League Russia': 'https://www.football-data.co.uk/russia.csv',
    # Ukrania
    'Premier League Ukraine': 'https://www.football-data.co.uk/ukraine.csv',
    # Polonia
    'Ekstraklasa': 'https://www.football-data.co.uk/poland.csv',
    # Austria
    'Bundesliga Austria': 'https://www.football-data.co.uk/austria.csv',
    # Suiza
    'Super League Switzerland': 'https://www.football-data.co.uk/switzerland.csv',
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
            # football-data no tiene Cloudflare, delay pequeño
            delay = random.uniform(1, 3)
            time.sleep(delay)
            
            r = requests.get(url, timeout=15, headers=CHROME_HEADERS)
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
                    
            logger.info(f"   ✅ {league}: {len(reader)} partidos")
            
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


if __name__ == '__main__':
    # Prueba con algunos equipos
    test_teams = ['Barcelona', 'Real Madrid', 'PSG']
    
    print("=" * 60)
    print("PRUEBA: Robot Extractor FBref Anti-Bloqueo")
    print("=" * 60)
    
    robot = RobotExtractor()
    
    for team in test_teams:
        print(f"\n🔍 {team}...")
        result = robot.extract_team(team, num_matches=5)
        
        if result['encontrado']:
            print(f"   ✅ {result['stats']['partidos']} partidos encontrados")
            print(f"   ⚽ GF: {result['stats']['goles_favor']} | GC: {result['stats']['goles_contra']}")
            print(f"   📊 Remates: {result['stats']['promedio_remates']} | Corners: {result['stats']['promedio_corners']}")
        else:
            print(f"   ❌ No encontrado")
