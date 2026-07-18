"""
Scraper para Flashscore.co (Latinoamérica)
Captura partidos en tiempo real
"""
import subprocess
import sys
import re
import hashlib
from datetime import datetime
from typing import Dict, List

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright


class FlashscoreCoScraper:
    """Scraper de flashscore.co"""
    
    LIGAS_PRIORIDAD = {
        "copa del mundo": 15, "mundial": 15,
        "champions league": 15, "champions": 15,
        "nations league": 15, "uefa nations": 15,
        "premier league": 14, "premier": 14,
        "la liga": 13, "liga": 13,
        "serie a": 12,
        "bundesliga": 11,
        "ligue 1": 10,
        "brasileiro": 8, "brasil": 8, "serie a brasil": 8,
        "liga mx": 8,
        "liga argentina": 7,
        "primera division chile": 7, "chile": 7,
        "liga colombia": 7,
        "liga peruana": 7,
        "copa argentina": 6, "copa america": 6,
        "mls": 5, "major league soccer": 5,
        "eredivisie": 5,
        "primera nacional": 3,
    }
    
    def _get_priority(self, league_name: str) -> int:
        league_lower = league_name.lower()
        for key, priority in self.LIGAS_PRIORIDAD.items():
            if key in league_lower:
                return priority
        return 1
    
    def scrape(self) -> List[Dict]:
        """Obtiene todos los partidos de flashscore.co"""
        matches = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # Ir a flashscore.co
                url = "https://www.flashscore.co/"
                page.goto(url, wait_until="networkidle", timeout=90000)
                page.wait_for_timeout(5000)
                
                # Extraer texto de la página
                text = page.inner_text('body')
                matches = self._parse_text(text)
                print(f"Encontrados: {len(matches)} partidos")
                
            except Exception as e:
                print(f"Error: {e}")
            finally:
                browser.close()
        
        return matches
    
    def _parse_text(self, text: str) -> List[Dict]:
        """Parsea el texto de flashscore"""
        matches = []
        lines = text.split('\n')
        
        current_liga = "Various"
        current_country = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detectar país/sección (líneas cortas en mayúsculas)
            if len(line) > 2 and len(line) < 40 and line.isupper():
                if line not in ['MUNDIAL', 'LIGA', 'CUADRO', 'PARTIDOS', 'TODAY', 'LIVE', 'FULL TIME', 'SCHEDULED']:
                    current_country = line
            
            # Detectar nombre de liga (líneas con dos puntos)
            if ':' in line and len(line) < 60:
                potential = line.replace(':', '').strip()
                if len(potential) > 3 and potential != potential.upper():
                    if not potential.replace(' ', '').isdigit():
                        current_liga = potential
            
            # Detectar horas (formato HH:MM)
            time_match = re.match(r'^(\d{1,2}:\d{2})$', line)
            if time_match:
                hora = time_match.group(1)
                
                # Buscar equipos después de la hora
                equipos = self._find_teams(lines, i)
                
                if len(equipos) >= 2:
                    home = equipos[0]
                    away = equipos[1]
                    
                    if home != away:
                        # Buscar resultado después
                        resultado = ""
                        for j in range(i+1, min(i+5, len(lines))):
                            score_match = re.search(r'^(\d+)\s*[-–]\s*(\d+)$', lines[j].strip())
                            if score_match:
                                resultado = f"{score_match.group(1)}-{score_match.group(2)}"
                                break
                        
                        fixture_id = hashlib.md5(f"{home}{away}".encode()).hexdigest()[:12]
                        fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                        
                        # Determinar liga correcta
                        liga = self._determine_league(current_liga, current_country, home, away)
                        
                        matches.append({
                            "fixture_id": fixture_id_int,
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": hora,
                            "liga": liga,
                            "prioridad": self._get_priority(liga),
                            "equipo_local": home,
                            "equipo_visitante": away,
                            "resultado": resultado,
                            "source": "flashscore.co"
                        })
            
            # Buscar formato "Equipo 1 - Equipo 2" con fecha
            # Ejemplo: "7/18 Francia - Inglaterra" o "16:00 Francia - Inglaterra"
            special_match = re.match(r'^(\d{1,2}:\d{2}|[A-Za-z]{3}\s*\d{1,2}[/-]\d{1,2})\s+(.+?)\s*[-–]\s*(.+)$', line)
            if special_match:
                hora_partido = special_match.group(1)
                team1 = special_match.group(2).strip()
                team2 = special_match.group(3).strip()
                
                # Verificar que sean equipos válidos
                if self._is_valid_team_name(team1) and self._is_valid_team_name(team2):
                    if team1 != team2:
                        fixture_id = hashlib.md5(f"{team1}{team2}".encode()).hexdigest()[:12]
                        fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                        
                        # Determinar liga
                        liga = self._determine_league(current_liga, current_country, team1, team2)
                        
                        matches.append({
                            "fixture_id": fixture_id_int,
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": hora_partido if ':' in hora_partido else "00:00",
                            "liga": liga,
                            "prioridad": self._get_priority(liga),
                            "equipo_local": team1,
                            "equipo_visitante": team2,
                            "resultado": "",
                            "source": "flashscore.co"
                        })
        
        return matches
    
    def _determine_league(self, current_liga: str, country: str, home: str, away: str) -> str:
        """Determina la liga correcta basándose en los equipos"""
        combined = f"{current_liga} {country}".lower()
        home_lower = home.lower()
        away_lower = away.lower()
        
        # Equipos de selecciones (PRIMERO para máxima prioridad)
        national_teams = ['francia', 'inglaterra', 'españa', 'alemania', 'italia', 'portugal',
                         'brasil', 'argentina', 'méxico', 'uruguay', 'colombia', 'chile',
                         'perú', 'ecuador', 'venezuela', 'paraguay', 'holanda', 'bélgica',
                         'croacia', 'dinamarca', 'polonia', 'suiza', 'austria', 'suecia',
                         'noruega', 'galés', 'escocia', 'irlanda', 'ucrania', 'rusia',
                         'japón', 'corea del sur', 'australia', 'china', 'irán', 'arábia']
        
        for team in national_teams:
            if team in home_lower or team in away_lower:
                if 'mundial' in combined or 'world' in combined:
                    return "Copa del Mundo 2026"
                if 'nations' in combined or 'nación' in combined:
                    return "UEFA Nations League"
                if 'copa america' in combined:
                    return "Copa America"
                if 'eliminatorias' in combined or 'qualif' in combined:
                    return "Eliminatorias"
                return "Internacional"
        
        # Equipos colombianos (ANTES de Chile porque Millonarios tiene "Millo")
        colombia_teams = ['millonarios', 'america de cali', 'nacional', 'atletico nacional', 
                         'junior', 'santa fe', 'tolima', 'cali', 'once caldas', 'medellin',
                         'pasto', 'huila', 'quindio', 'barranquilla']
        
        for team in colombia_teams:
            if team in home_lower or team in away_lower:
                return "Liga Colombia"
        
        # Equipos peruanos
        peru_teams = ['universitario', 'universidad san martin', 'cristal', 'alianza lima',
                      'sport huancayo', 'deportivo municipal', 'binacional', 'carlos a. manucci',
                      'sporting cristal', 'universidad technique']
        
        for team in peru_teams:
            if team in home_lower or team in away_lower:
                return "Liga Peruana"
        
        # Equipos chilenos específicos
        chile_teams = ['coquimbo', 'ohiggins', 'universidad chile', 'colo colo', 'catolica', 
                       'huachipato', 'audax italiano', 'san felipe', 'santa cruz', 'palestino',
                       'everton de viña', 'antofagasta', 'magallanes', 'copiapo', 'lautaro bueno',
                       'santa maria', 'concepcion']
        
        for team in chile_teams:
            if team in home_lower or team in away_lower:
                return "Primera Division Chile"
        
        # Equipos de Liga MX
        liga_mx_teams = ['pumas unam', 'pachuca', 'cruz azul', 'america', 'chivas', 'guadalajara',
                         'tigres', 'monterrey', 'leon', 'juarez', 'necaxa', 'santos laguna',
                         'puebla', 'toluca', 'queretaro', 'atlas', 'tijuana']
        
        for team in liga_mx_teams:
            if team in home_lower or team in away_lower:
                return "Liga MX"
        
        # Equipos argentinos
        argentina_teams = ['river plate', 'boca juniors', 'independiente', 'racing club', 
                         'san lorenzo', 'huracan', 'velez sarsfield', 'estudiantes', 
                         'gimnasia lp', 'newells old boys', 'rosario central', 'argentinos juniors',
                         'talleres cordoba', ' Belgrano', 'defensa y justicia']
        
        for team in argentina_teams:
            if team in home_lower or team in away_lower:
                if 'copa argentina' in combined:
                    return "Copa Argentina"
                return "Liga Argentina"
        
        # Equipos brasileños
        brasil_teams = ['gremio', 'flamengo', 'corinthians', 'palmeiras', 'sao paulo', 'botafogo',
                        'internacional', 'fluminense', 'athletico paranaense', 'coritiba', 
                        'bahia', 'ceara', 'fortaleza', 'sport recife', 'vitoria', 'cruzeiro',
                        'vasco da gama', 'atlético-go', 'goias', 'ponte preta', 'criciuma',
                        'bragantino', 'atletico mineiro', 'sao bernardo']
        
        for team in brasil_teams:
            if team in home_lower or team in away_lower:
                return "Serie A Brasil"
        
        # Usar la liga detectada si es buena
        if current_liga != "Various" and len(current_liga) > 3:
            return current_liga
        
        return "Various"
    
    def _find_teams(self, lines: list, start_idx: int) -> list:
        """Encuentra los equipos después de la hora"""
        equipos = []
        for j in range(start_idx+1, min(start_idx+10, len(lines))):
            l = lines[j].strip()
            if l and len(l) > 2 and len(l) < 40:
                # Ignorar líneas de UI
                if l not in ['Full-time', 'Half-time', 'Postponed', 'Live', 'Finished', 'Cancelled']:
                    if not re.match(r'^[\d\.\-\+]+$', l):
                        if self._is_valid_team_name(l):
                            equipos.append(l)
                            if len(equipos) >= 2:
                                break
        return equipos
    
    def _is_valid_team_name(self, name: str) -> bool:
        """Verifica si es un nombre válido de equipo"""
        if not name or len(name) < 3:
            return False
        
        # Excluir textos de UI
        exclude = ['MUNDIAL', 'LIGA', 'CUADRO', 'PARTIDOS', 'TODAY', 'LIVE', 'FULL TIME', 
                   'SCHEDULED', 'Half', 'Extra', 'Penalties', 'Pen', 'ET', 'FT', 'HT',
                   'Argentina', 'Brasil', 'Chile', 'Mexico', 'Colombia', 'Uruguay', 'Paraguay']
        
        if name.strip() in exclude:
            return False
        
        # Debe tener letras
        if not any(c.isalpha() for c in name):
            return False
        
        return True


if __name__ == "__main__":
    scraper = FlashscoreCoScraper()
    matches = scraper.scrape()
    print(f"\nTotal: {len(matches)} partidos")
    
    # Mostrar partidos prioritarios
    print("\n=== PARTIDOS PRIORITARIOS ===")
    for m in sorted(matches, key=lambda x: -x['prioridad'])[:20]:
        print(f"  [{m['prioridad']}] {m['liga']}: {m['equipo_local']} vs {m['equipo_visitante']} ({m['hora']}) {m['resultado']}")
