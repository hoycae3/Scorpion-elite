"""
Scorpion Elite - Scraper de Partidos
Extrae partidos de flashscore.co y los guarda en Supabase
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


class FlashscoreScraper:
    """Scraper de flashscore.co"""
    
    LIGAS_PRIORIDAD = {
        "copa del mundo": 15, "mundial": 15,
        "champions league": 15, "nations league": 15,
        "premier league": 14, "la liga": 13, "serie a": 12,
        "bundesliga": 11, "ligue 1": 10, "brasil": 8,
        "liga mx": 8, "liga argentina": 7, "chile": 7,
        "liga colombia": 7, "liga peruana": 7,
    }
    
    def scrape(self) -> List[Dict]:
        """Obtiene todos los partidos"""
        matches = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                page.goto("https://www.flashscore.co/", wait_until="networkidle", timeout=90000)
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
        """Parsea el texto"""
        matches = []
        lines = text.split('\n')
        current_liga = "Various"
        current_country = ""
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Detectar país/sección
            if len(line) > 2 and len(line) < 40 and line.isupper():
                if line not in ['MUNDIAL', 'LIGA', 'CUADRO', 'PARTIDOS', 'TODAY', 'LIVE']:
                    current_country = line
            
            # Detectar nombre de liga
            if ':' in line and len(line) < 60:
                potential = line.replace(':', '').strip()
                if len(potential) > 3 and potential != potential.upper():
                    if not potential.replace(' ', '').isdigit():
                        current_liga = potential
            
            # Detectar horas
            time_match = re.match(r'^(\d{1,2}:\d{2})$', line)
            if time_match:
                hora = time_match.group(1)
                equipos = self._find_teams(lines, i)
                
                if len(equipos) >= 2:
                    home, away = equipos[0], equipos[1]
                    if home != away:
                        fixture_id = hashlib.md5(f"{home}{away}".encode()).hexdigest()[:12]
                        fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                        
                        matches.append({
                            "fixture_id": fixture_id_int,
                            "fecha": datetime.now().strftime("%Y-%m-%d"),
                            "hora": hora,
                            "liga": self._determine_league(current_liga, current_country, home, away),
                            "equipo_local": home,
                            "equipo_visitante": away,
                        })
        
        return matches
    
    def _determine_league(self, current_liga: str, country: str, home: str, away: str) -> str:
        """Determina la liga"""
        combined = f"{current_liga} {country}".lower()
        home_lower, away_lower = home.lower(), away.lower()
        
        # Selecciones
        national = ['francia', 'inglaterra', 'españa', 'alemania', 'italia', 'brasil', 'argentina']
        for t in national:
            if t in home_lower or t in away_lower:
                if 'mundial' in combined:
                    return "Copa del Mundo 2026"
                return "Internacional"
        
        # Equipos específicos
        teams = {
            'pumas': 'Liga MX', 'pachuca': 'Liga MX', 'cruz azul': 'Liga MX',
            'millonarios': 'Liga Colombia', 'colo colo': 'Primera Division Chile',
            'sport recife': 'Serie A Brasil', 'river plate': 'Liga Argentina',
            'universitario': 'Liga Peruana',
        }
        
        for key, league in teams.items():
            if key in home_lower or key in away_lower:
                return league
        
        return current_liga if current_liga != "Various" else "Various"
    
    def _find_teams(self, lines: list, start_idx: int) -> list:
        """Encuentra equipos"""
        equipos = []
        for j in range(start_idx+1, min(start_idx+10, len(lines))):
            l = lines[j].strip()
            if l and len(l) > 2 and len(l) < 40:
                if l not in ['Full-time', 'Half-time', 'Postponed', 'Live']:
                    if not re.match(r'^[\d\.\-\+]+$', l):
                        equipos.append(l)
                        if len(equipos) >= 2:
                            break
        return equipos


def guardar_en_supabase(partidos: List[Dict]):
    """Guarda partidos en Supabase"""
    from supabase import create_client
    import os
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    
    if not url or not key:
        print("Error: Faltan credenciales de Supabase")
        return
    
    client = create_client(url, key)
    
    for p in partidos[:30]:
        try:
            data = {
                'fixture_id': p['fixture_id'],
                'fecha': p['fecha'],
                'hora': p['hora'],
                'liga': p['liga'],
                'equipo_local': p['equipo_local'],
                'equipo_visitante': p['equipo_visitante'],
            }
            client.table('partidos').upsert(data, on_conflict='fixture_id').execute()
            print(f"OK: {p['liga']} - {p['equipo_local']} vs {p['equipo_visitante']}")
        except Exception as e:
            print(f"Error: {str(e)[:50]}")


if __name__ == "__main__":
    scraper = FlashscoreScraper()
    partidos = scraper.scrape()
    guardar_en_supabase(partidos)
