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
            
            # Detectar nombre de liga
            if ':' in line and len(line) < 60:
                potential = line.replace(':', '').strip()
                if len(potential) > 3 and potential != potential.upper():
                    current_liga = potential
            
            # Detectar horas (formato HH:MM AM/PM)
            time_match = re.match(r'(\d{1,2}:\d{2})\s*(AM|PM)?', line, re.IGNORECASE)
            if time_match:
                hora = time_match.group(0)
                
                # Buscar equipos después de la hora
                equipos = []
                for j in range(i+1, min(i+12, len(lines))):
                    l = lines[j].strip()
                    # Ignorar líneas de apuestas
                    if l and not re.match(r'^[\d\.\-\+]+$', l):
                        if l not in ['Full-time', 'Half-time', 'Postponed', 'Cancelled', 'Extra Time', 'Penalties']:
                            if len(l) > 2 and len(l) < 50:
                                if self._is_valid_team(l):
                                    equipos.append(l)
                                    if len(equipos) >= 2:
                                        break
                
                if len(equipos) >= 2:
                    home = equipos[0]
                    away = equipos[1]
                    
                    # Buscar resultado
                    resultado = ""
                    for j in range(i+1, min(i+8, len(lines))):
                        score_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', lines[j])
                        if score_match:
                            resultado = f"{score_match.group(1)}-{score_match.group(2)}"
                            break
                    
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
        
        return matches
    
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
