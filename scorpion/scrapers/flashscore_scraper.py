"""
Scraper para Flashscore
Fuente: https://www.flashscore.com/
Captura: Partidos del día, cuotas, probabilidades, liga, equipos
Usa Playwright para cargar contenido dinámico
"""
import re
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Playwright se instala en runtime
PLAYWRIGHT_AVAILABLE = False

def _ensure_playwright():
    global PLAYWRIGHT_AVAILABLE
    if not PLAYWRIGHT_AVAILABLE:
        try:
            from playwright.sync_api import sync_playwright
            PLAYWRIGHT_AVAILABLE = True
        except ImportError:
            import subprocess
            subprocess.run(["pip", "install", "playwright"], capture_output=True)
            subprocess.run(["playwright", "install", "chromium"], capture_output=True)
            try:
                from playwright.sync_api import sync_playwright
                PLAYWRIGHT_AVAILABLE = True
            except:
                PLAYWRIGHT_AVAILABLE = False

from .base_scraper import BaseScraper


class FlashscoreScraper(BaseScraper):
    """Scraper específico para Flashscore usando Playwright"""
    
    # Mapeo de ligas a prioridades
    LIGAS_PRIORIDAD = {
        "champions league": 15, "champions": 15,
        "premier league": 14, "premier": 14,
        "la liga": 13, "liga": 13,
        "serie a": 12,
        "bundesliga": 11,
        "ligue 1": 10, "ligue": 10,
        "europa league": 9, "europa": 9,
        "libertadores": 8, "copa libertadores": 8,
        "brasileiro": 7, "brasil": 7, "serie a brasil": 7,
        "eredivisie": 7,
        "primeira liga": 6, "liga mx": 6,
        "major league soccer": 5, "mls": 5,
        "usl championship": 4, "usl": 4,
        "primera nacional": 3, "copa argentina": 3,
        "canadian premier league": 3, "cpl": 3,
    }
    
    def __init__(self):
        super().__init__(timeout=30, retry_count=3)
        self.base_url = "https://www.flashscore.com"
    
    def _get_priority(self, league_name: str) -> int:
        """Calcula la prioridad de una liga"""
        league_lower = league_name.lower()
        for key, priority in self.LIGAS_PRIORIDAD.items():
            if key in league_lower:
                return priority
        return 1
    
    def _scrape_with_playwright(self, url: str, dias: int = 2) -> List[Dict]:
        """Usa Playwright para scraping de contenido dinámico"""
        all_matches = []
        
        _ensure_playwright()
        
        if not PLAYWRIGHT_AVAILABLE:
            return []
        
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            for day_offset in range(dias):
                fecha = datetime.now() + timedelta(days=day_offset)
                fecha_str = fecha.strftime("%Y-%m-%d")
                
                # URL de partidos por fecha
                page_url = f"https://www.flashscore.com/football/{fecha_str}/"
                
                try:
                    page.goto(page_url, wait_until="networkidle", timeout=30000)
                    page.wait_for_timeout(2000)  # Esperar que carguen datos
                    
                    # Buscar eventos
                    eventos = page.query_selector_all('[id^="g_"]')
                    
                    for evento in eventos:
                        try:
                            # Extraer datos del evento
                            evento_html = evento.inner_html()
                            
                            # Parsear hora
                            hora_elem = evento.query_selector('.event__time')
                            hora = hora_elem.inner_text() if hora_elem else "00:00"
                            
                            # Parsear equipos
                            home_elem = evento.query_selector('.event__home')
                            away_elem = evento.query_selector('.event__away')
                            
                            home_name = home_elem.inner_text() if home_elem else "Local"
                            away_name = away_elem.inner_text() if away_elem else "Visita"
                            
                            # Parsear liga
                            league_elem = evento.query_selector('.event__league')
                            liga = league_elem.inner_text() if league_elem else "Liga"
                            
                            if home_name and away_name:
                                all_matches.append({
                                    "fixture_id": self._generate_fixture_id(home_name, away_name, fecha_str),
                                    "fecha": fecha_str,
                                    "hora": hora,
                                    "liga": liga,
                                    "prioridad": self._get_priority(liga),
                                    "equipo_local": home_name,
                                    "equipo_visitante": away_name,
                                    "source": "flashscore"
                                })
                        except Exception as e:
                            continue
                            
                except Exception as e:
                    print(f"Error en {page_url}: {e}")
                    continue
            
            browser.close()
        
        return all_matches
    
    def _scrape_fallback(self) -> List[Dict]:
        """Método fallback que intenta encontrar datos en scripts JSON"""
        all_matches = []
        fecha_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code == 200:
                # Buscar datos JSON en scripts
                scripts = re.findall(r'<script[^>]*>(.*?)</script>', response.text, re.DOTALL)
                
                for script in scripts:
                    # Buscar patrones de datos de partidos
                    matches = re.findall(r'"homeTeam"\s*:\s*"([^"]+)".*?"awayTeam"\s*:\s*"([^"]+)".*?"time"\s*:\s*"([^"]+)"', script, re.DOTALL)
                    for match in matches:
                        home, away, time = match
                        all_matches.append({
                            "fixture_id": self._generate_fixture_id(home, away, fecha_str),
                            "fecha": fecha_str,
                            "hora": time,
                            "liga": "Various",
                            "prioridad": 1,
                            "equipo_local": home,
                            "equipo_visitante": away,
                            "source": "flashscore"
                        })
        except Exception as e:
            print(f"Error en fallback: {e}")
        
        return all_matches
    
    def get_today_matches(self, dias: int = 2) -> List[Dict]:
        """Obtiene los partidos de los próximos días"""
        # Intentar con Playwright primero
        if PLAYWRIGHT_AVAILABLE:
            try:
                matches = self._scrape_with_playwright(self.base_url, dias)
                if matches:
                    return matches
            except Exception as e:
                print(f"Playwright falló: {e}")
        
        # Fallback al método simple
        return self._scrape_fallback()
    
    def _generate_fixture_id(self, home: str, away: str, fecha: str) -> int:
        """Genera un ID único para el partido"""
        import hashlib
        key = f"{home}{away}{fecha}".encode()
        return int(hashlib.md5(key).hexdigest()[:8], 16) % (10 ** 10)
    
    def scrape(self, dias: int = 2) -> List[Dict]:
        """Método principal del scraper"""
        return self.get_today_matches(dias=dias)


# Ejemplo de uso
if __name__ == "__main__":
    scraper = FlashscoreScraper()
    partidos = scraper.scrape(dias=2)
    print(f"Total partidos encontrados: {len(partidos)}")
    for p in partidos[:5]:
        print(f"  {p['fecha']} {p['hora']} - {p['liga']}: {p['equipo_local']} vs {p['equipo_visitante']}")
