"""
Scorpion Elite - Live Scraper
Extrae partidos en VIVO de flashscore.co y guarda en Supabase
Usa Playwright para evadir protecciones
"""
import time
import random
import hashlib
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright


class LiveScraper:
    """Scraper de partidos en vivo"""
    
    # User-Agents rotativos
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0",
    ]
    
    def __init__(self):
        self.matches = []
        
    def random_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Delay aleatorio para parecer humano"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def scrape_live(self) -> List[Dict]:
        """Extrae partidos en vivo"""
        self.matches = []
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            context = browser.new_context(
                user_agent=random.choice(self.USER_AGENTS),
                locale='es-ES',
                timezone_id='America/Bogota',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = context.new_page()
            
            try:
                # Ir a flashscore
                page.goto("https://www.flashscore.co/", wait_until="domcontentloaded", timeout=60000)
                self.random_delay(2, 4)
                
                # Click en "En Vivo" si existe
                try:
                    live_btn = page.locator('text=En Vivo').first
                    if live_btn.is_visible():
                        live_btn.click()
                        self.random_delay(2, 3)
                except:
                    pass
                
                # Hacer scroll para cargar más partidos
                for _ in range(3):
                    page.evaluate("window.scrollBy(0, 500)")
                    self.random_delay(0.5, 1)
                
                # Extraer datos
                self.matches = self._extract_matches(page)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Encontrados: {len(self.matches)} partidos en vivo")
                
            except Exception as e:
                print(f"Error: {e}")
            finally:
                browser.close()
        
        return self.matches
    
    def _extract_matches(self, page) -> List[Dict]:
        """Extrae datos de partidos del DOM"""
        matches = []
        
        try:
            # Buscar todos los eventos/matches
            events = page.query_selector_all('[data-event-status="inprogress"], .event, .football-match')
            
            for event in events:
                try:
                    # Extraer minuto
                    minute_elem = event.query_selector('.minute, .time-box, [class*="minute"]')
                    minuto = minute_elem.inner_text() if minute_elem else "LIVE"
                    
                    # Extraer equipos
                    home_elem = event.query_selector('.home-name, .team-home, [class*="home"]')
                    away_elem = event.query_selector('.away-name, .team-away, [class*="away"]')
                    
                    home = home_elem.inner_text() if home_elem else ""
                    away = away_elem.inner_text() if away_elem else ""
                    
                    if not home or not away:
                        continue
                    
                    # Extraer marcador
                    score_elem = event.query_selector('.score, .result, [class*="score"]')
                    score_text = score_elem.inner_text() if score_elem else "0 - 0"
                    
                    # Parsear marcador
                    score_parts = score_text.replace(' ', '').split('-')
                    if len(score_parts) >= 2:
                        goles_local = score_parts[0].strip()
                        goles_visitante = score_parts[1].strip()
                    else:
                        goles_local, goles_visitante = "0", "0"
                    
                    # Extraer liga
                    league_elem = event.query_selector('.league-name, .tournament-name, [class*="league"]')
                    liga = league_elem.inner_text() if league_elem else "Various"
                    
                    # Generar ID único
                    fixture_id = hashlib.md5(f"{home}{away}".encode()).hexdigest()[:12]
                    fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                    
                    match_data = {
                        "fixture_id": fixture_id_int,
                        "fecha": datetime.now().strftime("%Y-%m-%d"),
                        "hora": datetime.now().strftime("%H:%M"),
                        "liga": liga,
                        "equipo_local": home,
                        "equipo_visitante": away,
                        "goles_local": goles_local,
                        "goles_visitante": goles_visitante,
                        "minuto": minuto,
                        "estado": "live"
                    }
                    
                    matches.append(match_data)
                    print(f"  ⚽ {home} {goles_local}-{goles_visitante} {away} ({minuto})")
                    
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error extrayendo matches: {e}")
        
        return matches


def save_to_supabase(matches: List[Dict]):
    """Guarda partidos en Supabase"""
    from supabase import create_client
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    
    if not url or not key:
        print("Error: Faltan credenciales de Supabase")
        return 0
    
    client = create_client(url, key)
    saved = 0
    
    for m in matches:
        try:
            data = {
                'fixture_id': m['fixture_id'],
                'fecha': m['fecha'],
                'hora': m['hora'],
                'liga': m['liga'],
                'equipo_local': m['equipo_local'],
                'equipo_visitante': m['equipo_visitante'],
                'goles_local': m.get('goles_local', '0'),
                'goles_visitante': m.get('goles_visitante', '0'),
                'minuto': m.get('minuto', 'LIVE'),
                'estado': m.get('estado', 'live')
            }
            
            client.table('partidos').upsert(data, on_conflict='fixture_id').execute()
            saved += 1
            
        except Exception as e:
            print(f"Error guardando: {e}")
    
    return saved


def run_live_loop(interval: int = 60):
    """
    Bucle principal que ejecuta el scraper cada X segundos
    """
    print("=" * 50)
    print("🦂 SCORPION ELITE - LIVE SCRAPER")
    print("=" * 50)
    print(f"Intervalo: {interval} segundos")
    print("Presiona Ctrl+C para detener")
    print("=" * 50)
    
    scraper = LiveScraper()
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Iniciando scraping...")
            
            matches = scraper.scrape_live()
            
            if matches:
                saved = save_to_supabase(matches)
                print(f"✅ Guardados: {saved}/{len(matches)} partidos")
            else:
                print("ℹ️ No hay partidos en vivo")
            
            print(f"⏳ Próximo scraping en {interval} segundos...")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Detenido por el usuario")
        return


# Agregar columnas a tabla si no existen
def setup_database():
    """Crea las columnas necesarias en Supabase"""
    from supabase import create_client
    
    url = os.environ.get('SUPABASE_URL')
    key = os.environ.get('SUPABASE_KEY')
    
    if not url or not key:
        print("Error: Faltan credenciales")
        return
    
    # SQL para agregar columnas
    sql = """
    ALTER TABLE partidos 
    ADD COLUMN IF NOT EXISTS goles_local TEXT DEFAULT '0',
    ADD COLUMN IF NOT EXISTS goles_visitante TEXT DEFAULT '0',
    ADD COLUMN IF NOT EXISTS minuto TEXT DEFAULT 'LIVE',
    ADD COLUMN IF NOT EXISTS estado TEXT DEFAULT 'live';
    """
    
    print("ℹ️ Ejecuta este SQL en Supabase Dashboard:")
    print(sql)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--setup":
            setup_database()
        elif sys.argv[1] == "--once":
            print("Ejecutando una vez...")
            scraper = LiveScraper()
            matches = scraper.scrape_live()
            if matches:
                saved = save_to_supabase(matches)
                print(f"✅ Guardados: {saved}/{len(matches)} partidos")
            else:
                print("ℹ️ No hay partidos en vivo")
    else:
        run_live_loop(interval=60)
