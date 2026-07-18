"""
Scraper de Partidos - Scorpion Elite
Usa Playwright para ejecutar JavaScript y obtener datos reales de Soccerway
"""
import subprocess
import sys
import re
import hashlib
from datetime import datetime
from typing import Dict, List

# Instalar playwright si no está
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Instalando Playwright...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright


class PlaywrightMatchesScraper:
    """Scraper de partidos usando Playwright"""
    
    LIGAS_PRIORIDAD = {
        "champions league": 15,
        "premier league": 14, "premier": 14,
        "la liga": 13, "laliga": 13, "primera division": 13,
        "serie a": 12,
        "bundesliga": 11,
        "ligue 1": 10,
        "brasileiro": 7, "brasileirao": 7,
        "eredivisie": 7,
        "primeira liga": 6,
        "liga mx": 6,
        "mls": 5, "major league soccer": 5,
        "usl championship": 4,
    }
    
    def _get_priority(self, league_name: str) -> int:
        league_lower = league_name.lower()
        for key, priority in self.LIGAS_PRIORIDAD.items():
            if key in league_lower:
                return priority
        return 1
    
    def scrape(self) -> List[Dict]:
        """Obtiene todos los partidos de Soccerway"""
        matches = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                url = "https://www.soccerway.com/"
                page.goto(url, wait_until="networkidle", timeout=90000)
                page.wait_for_timeout(5000)
                
                text = page.inner_text('body')
                matches = self._parse_text(text)
                print(f"Encontrados: {len(matches)} partidos")
                
            except Exception as e:
                print(f"Error: {e}")
            finally:
                browser.close()
        
        return matches
    
    def _parse_text(self, text: str) -> List[Dict]:
        """Parsea el texto de la página para extraer partidos"""
        matches = []
        lines = text.split('\n')
        
        current_liga = "Various"
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detectar nombre de liga (líneas antes de ":")
            if ':' in line and len(line) < 60:
                potential = line.replace(':', '').strip()
                if len(potential) > 3 and potential != potential.upper():
                    if not potential.isdigit() and potential not in ['LIVE', 'TODAY', 'MATCHES', 'ALL', 'Full-time', 'Half-time']:
                        current_liga = potential
            
            # Detectar secciones de país
            if line.isupper() and len(line) > 2 and len(line) < 40 and ':' not in line:
                if line not in ['WORLD CUP', 'PREMIER LEAGUE', 'LALIGA', 'MLS', 'LIGA MX', 'SERIE A', 'CHAMPIONS LEAGUE', 'LIVE SCORES', 'TODAY', 'ALL', 'SCHEDULED']:
                    current_liga = line
            
            # Detectar horas (formato HH:MM AM/PM)
            time_match = re.match(r'(\d{1,2}:\d{2})\s*(AM|PM)?', line, re.IGNORECASE)
            if time_match:
                hora = time_match.group(0)
                
                # Detectar liga
                detected_liga = self._detect_league_from_context(lines, i)
                if detected_liga:
                    current_liga = detected_liga
                
                # Buscar equipos después de la hora
                equipos = self._find_teams_after_time(lines, i)
                
                if len(equipos) >= 2:
                    home = equipos[0]
                    away = equipos[1]
                    
                    if home != away and self._is_meaningful_match(home, away):
                        resultado = self._find_score_after_time(lines, i)
                        
                        fixture_id = hashlib.md5(f"{home}{away}".encode()).hexdigest()[:12]
                        fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                        
                        matches.append({
                            "fixture_id": fixture_id_int,
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": hora,
                            "liga": current_liga,
                            "prioridad": self._get_priority(current_liga),
                            "equipo_local": home,
                            "equipo_visitante": away,
                            "resultado": resultado,
                            "source": "soccerway"
                        })
            
            # NUEVO: Buscar partidos internacionales en formato "fecha Equipo - Equipo"
            # Ejemplo: "7/18 France - England" o "7/19 Spain - Argentina"
            int_match = re.match(r'(\d{1,2}/\d{1,2})\s+([A-Za-z\s]+)\s*-\s*([A-Za-z\s]+)', line)
            if int_match:
                fecha_short = int_match.group(1)
                team1 = int_match.group(2).strip()
                team2 = int_match.group(3).strip()
                
                # Determinar si es partido internacional
                if self._is_national_team(team1) or self._is_national_team(team2):
                    # Buscar hora antes
                    hora = "00:00"
                    for j in range(max(0, i-10), i):
                        time_check = re.match(r'(\d{1,2}:\d{2})\s*(AM|PM)?', lines[j].strip(), re.IGNORECASE)
                        if time_check:
                            hora = time_check.group(0)
                            break
                    
                    # Determinar la liga (Nations League, World Cup, etc.)
                    liga = self._detect_international_league(lines, i)
                    
                    fixture_id = hashlib.md5(f"{team1}{team2}".encode()).hexdigest()[:12]
                    fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                    
                    matches.append({
                        "fixture_id": fixture_id_int,
                        "fecha": datetime.now().strftime("%Y-%m-%d"),
                        "hora": hora,
                        "liga": liga,
                        "prioridad": 15,  # Máxima prioridad para partidos internacionales
                        "equipo_local": team1,
                        "equipo_visitante": team2,
                        "resultado": "",
                        "source": "soccerway"
                    })
        
        return matches
    
    def _is_national_team(self, name: str) -> bool:
        """Verifica si es un equipo nacional"""
        national_teams = [
            'England', 'France', 'Spain', 'Germany', 'Italy', 'Portugal', 'Netherlands',
            'Belgium', 'Argentina', 'Brazil', 'Uruguay', 'Colombia', 'Mexico', 'USA',
            'Chile', 'Peru', 'Ecuador', 'Venezuela', 'Paraguay', 'Costa Rica',
            'Croatia', 'Denmark', 'Poland', 'Switzerland', 'Austria', 'Sweden', 'Norway',
            'Wales', 'Scotland', 'Ireland', 'Ukraine', 'Czech', 'Hungary', 'Romania',
            'Japan', 'South Korea', 'Australia', 'China', 'Iran', 'Saudi Arabia',
            'Egypt', 'Morocco', 'Nigeria', 'Ghana', 'Senegal', 'Cameroon', 'Algeria',
            'Tunisia', 'Ivory Coast', 'Greece', 'Turkey', 'Serbia', 'Russia', 'Israel'
        ]
        return name in national_teams
    
    def _detect_international_league(self, lines: list, idx: int) -> str:
        """Detecta si es Nations League, World Cup, etc."""
        # Buscar en las líneas anteriores
        for i in range(max(0, idx-10), idx):
            line = lines[i].strip().lower()
            if 'world cup' in line or 'mundial' in line:
                return 'World Cup 2026'
            if 'nations league' in line:
                return 'UEFA Nations League'
            if 'euro' in line and 'qualif' in line:
                return 'Euro Qualifiers'
            if 'copa america' in line:
                return 'Copa America'
            if 'friend' in line:
                return 'International Friendly'
        return 'International'
    
    def _find_teams_after_time(self, lines: list, start_idx: int) -> list:
        """Encuentra los equipos después de una hora"""
        equipos = []
        for j in range(start_idx+1, min(start_idx+15, len(lines))):
            l = lines[j].strip()
            if l and not re.match(r'^[\d\.\-\+]+$', l):
                if l not in ['Full-time', 'Half-time', 'Postponed', 'Cancelled', 'Extra Time', 'Penalties']:
                    if len(l) > 2 and len(l) < 50:
                        if self._is_valid_team(l):
                            equipos.append(l)
                            if len(equipos) >= 2:
                                break
        return equipos
    
    def _find_score_after_time(self, lines: list, start_idx: int) -> str:
        """Encuentra el marcador después de una hora"""
        for j in range(start_idx+1, min(start_idx+10, len(lines))):
            score_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', lines[j])
            if score_match:
                return f"{score_match.group(1)}-{score_match.group(2)}"
        return ""
    
    def _detect_league_from_context(self, lines: list, start_idx: int) -> str:
        """Detecta la liga mirando el contexto alrededor del partido"""
        # Buscar hacia arriba en las últimas 20 líneas
        for i in range(start_idx - 1, max(0, start_idx - 20), -1):
            line = lines[i].strip()
            
            # Detectar liga conocida
            known_ligas = [
                'UEFA Nations League', 'Nations League', 'International',
                'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1',
                'MLS', 'Liga MX', 'Brasileiro', 'Champions League', 'Europa League',
                'World Cup', 'Copa America', 'Euro'
            ]
            
            for liga in known_ligas:
                if liga.lower() in line.lower():
                    return liga
            
            # Detectar secciones de país (líneas cortas en mayúsculas)
            if line.isupper() and len(line) > 3 and len(line) < 30:
                if ':' not in line and line not in ['LIVE', 'TODAY', 'ALL', 'SCHEDULED']:
                    return line
        
        return "Various"
    
    def _is_meaningful_match(self, home: str, away: str) -> bool:
        """Verifica si es un partido significativo (no equipos menores)"""
        # Equipos menores/juveniles a excluir
        exclude_teams = ['U21', 'U20', 'U19', 'U18', 'U23', 'Youth', 'Reserves', 'II', 'B']
        
        for exclude in exclude_teams:
            if exclude in home or exclude in away:
                return False
        
        # Equipos menores de ligas menores
        minor_teams = ['FRO', 'Niva', 'Bar', 'Uni', 'Labs']  # Equipos cortos sospechosos
        
        return True
    
    def _is_valid_team(self, name: str) -> bool:
        """Verifica si es un nombre válido de equipo"""
        if not name or len(name) < 3:
            return False
        
        exclude = ['World', 'Cup', 'League', 'Standings', 'Bracket', 'Quarter', 'Semi', 'Final',
                   'Display', 'Matches', 'Wins', 'Draws', 'Losses', 'Goals', 'Points',
                   'Group', 'Round', 'Match', 'Playoffs', 'Play', 'Off', 'Advertisement',
                   'LIVE', 'TODAY', 'Full-time', 'Half-time', 'SCHEDULED']
        
        if name.strip() in exclude:
            return False
        
        return True


if __name__ == "__main__":
    scraper = PlaywrightMatchesScraper()
    matches = scraper.scrape()
    print(f"\nTotal: {len(matches)} partidos")
    for m in matches[:15]:
        print(f"  {m['liga']}: {m['equipo_local']} vs {m['equipo_visitante']} ({m['resultado']})")
