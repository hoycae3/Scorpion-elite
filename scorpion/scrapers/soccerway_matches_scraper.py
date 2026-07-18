"""
Scraper de Partidos - Scorpion Elite
Usa Soccerway para obtener partidos del día
Soccerway es más amigable con scraping que Flashscore
"""
import requests
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import Dict, List, Optional


class SoccerwayMatchesScraper:
    """Scraper de partidos usando Soccerway"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        })
        self.base_url = "https://www.soccerway.com"
        
        # URLs de partidos por fecha
        self.ligas_urls = {
            "premier-league": "https://www.soccerway.com/national/england/premier-league/20242025/",
            "la-liga": "https://www.soccerway.com/national/spain/primera-division/20242025/",
            "serie-a": "https://www.soccerway.com/national/italy/serie-a/20242025/",
            "bundesliga": "https://www.soccerway.com/national/germany/bundesliga/20242025/",
            "ligue-1": "https://www.soccerway.com/national/france/ligue-1/20242025/",
            "brasileiro": "https://www.soccerway.com/national/brazil/serie-a/2025/",
            "mls": "https://www.soccerway.com/national/usa/major-league-soccer/2024/",
            "liga-mx": "https://www.soccerway.com/national/mexico/liga-mx/2024/",
        }
    
    # Mapeo de ligas a prioridades
    LIGAS_PRIORIDAD = {
        "premier league": 14, "premier": 14,
        "la liga": 13, "primera division": 13,
        "serie a": 12,
        "bundesliga": 11,
        "ligue 1": 10,
        "brasileiro": 7, "brasileirao": 7, "serie a": 7,
        "mls": 5, "major league soccer": 5,
        "liga mx": 6, "liga mx": 6,
    }
    
    def _get_priority(self, league_name: str) -> int:
        """Calcula la prioridad de una liga"""
        league_lower = league_name.lower()
        for key, priority in self.LIGAS_PRIORIDAD.items():
            if key in league_lower:
                return priority
        return 1
    
    def get_league_matches(self, league_name: str, limit: int = 20) -> List[Dict]:
        """Obtiene los partidos de una liga"""
        url_key = league_name.lower().replace(' ', '-')
        
        if url_key not in self.ligas_urls:
            # Buscar coincidencias parciales
            for key, url in self.ligas_urls.items():
                if url_key in key or key in url_key:
                    url_key = key
                    break
            else:
                print(f"Liga no encontrada: {league_name}")
                return []
        
        url = self.ligas_urls.get(url_key, "")
        if not url:
            return []
        
        try:
            response = self.session.get(url, timeout=30)
            if response.status_code != 200:
                print(f"Error {response.status_code} para {league_name}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            matches = self._parse_page(soup, league_name)
            print(f"{league_name}: {len(matches)} partidos")
            return matches[:limit]
            
        except Exception as e:
            print(f"Error scraping {league_name}: {e}")
            return []
    
    def _parse_page(self, soup: BeautifulSoup, league_name: str) -> List[Dict]:
        """Parsea la página para extraer partidos"""
        matches = []
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        
        # Buscar filas de partidos
        rows = soup.find_all('tr', class_='match')
        
        for row in rows:
            try:
                # Buscar fecha
                date_cell = row.find('td', class_='date')
                date_elem = date_cell.find('a') if date_cell else None
                fecha = date_elem.text.strip() if date_elem else fecha_hoy
                
                # Normalizar fecha
                if '/' in fecha:
                    parts = fecha.split('/')
                    if len(parts) == 3:
                        fecha = f"20{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                
                # Buscar hora
                time_cell = row.find('td', class_='time')
                time_elem = time_cell.find('span') if time_cell else None
                hora = time_elem.text.strip() if time_elem else "00:00"
                
                # Buscar equipos
                team_cells = row.find_all('td', class_='team')
                if len(team_cells) >= 2:
                    home_link = team_cells[0].find('a')
                    away_link = team_cells[1].find('a')
                    
                    home_name = home_link.text.strip() if home_link else "Local"
                    away_name = away_link.text.strip() if away_link else "Visita"
                    
                    # Buscar resultado
                    score_cell = row.find('td', class_='score')
                    score_link = score_cell.find('a') if score_cell else None
                    score_text = score_link.text.strip() if score_link else ""
                    
                    if home_name and away_name:
                        import hashlib
                        fixture_id = hashlib.md5(f"{home_name}{away_name}{fecha}".encode()).hexdigest()[:12]
                        fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                        
                        matches.append({
                            "fixture_id": fixture_id_int,
                            "fecha": fecha,
                            "hora": hora,
                            "liga": league_name,
                            "prioridad": self._get_priority(league_name),
                            "equipo_local": home_name,
                            "equipo_visitante": away_name,
                            "resultado": score_text,
                            "source": "soccerway"
                        })
                        
            except Exception as e:
                continue
        
        return matches
    
    def get_all_matches(self) -> List[Dict]:
        """Obtiene partidos de todas las ligas configuradas"""
        all_matches = []
        
        ligas = [
            "Premier League",
            "La Liga",
            "Serie A",
            "Bundesliga",
            "Ligue 1",
            "Brasileiro",
            "MLS",
            "Liga MX"
        ]
        
        for liga in ligas:
            matches = self.get_league_matches(liga, limit=30)
            all_matches.extend(matches)
        
        # Eliminar duplicados
        seen = set()
        unique = []
        for m in all_matches:
            fid = m["fixture_id"]
            if fid not in seen:
                seen.add(fid)
                unique.append(m)
        
        return unique
    
    def scrape(self) -> List[Dict]:
        """Método principal"""
        return self.get_all_matches()


# Ejemplo de uso
if __name__ == "__main__":
    scraper = SoccerwayMatchesScraper()
    matches = scraper.scrape()
    print(f"\nTotal partidos: {len(matches)}")
    for m in matches[:10]:
        print(f"  {m['fecha']} {m['hora']} - {m['liga']}: {m['equipo_local']} vs {m['equipo_visitante']} {m.get('resultado', '')}")
