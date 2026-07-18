"""
Scraper para Flashscore
Fuente: https://www.flashscore.com/
Captura: Partidos del día, cuotas, probabilidades, liga, equipos
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_scraper import BaseScraper


class FlashscoreScraper(BaseScraper):
    """Scraper específico para Flashscore"""
    
    # Mapeo de ligas a prioridades
    LIGAS_PRIORIDAD = {
        "champions league": 15,
        "champions": 15,
        "premier league": 14,
        "premier": 14,
        "la liga": 13,
        "liga": 13,
        "serie a": 12,
        "bundesliga": 11,
        "ligue 1": 10,
        "ligue": 10,
        "europa league": 9,
        "europa": 9,
        "libertadores": 8,
        "copa libertadores": 8,
        "brasileiro": 7,
        "brasil": 7,
        "serie a brasil": 7,
        "eredivisie": 7,
        "primeira liga": 6,
        "liga mx": 6,
        "liga mx": 6,
        "major league soccer": 5,
        "mls": 5,
        "usl": 4,
        "usl championship": 4,
        "primera nacional": 3,
        "copa argentina": 3,
        "canadian premier league": 3,
        "cpl": 3,
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
        return 1  # Prioridad mínima por defecto
    
    def get_today_matches(self, dias: int = 2) -> List[Dict]:
        """
        Obtiene los partidos de los próximos días
        
        Args:
            dias: Número de días hacia adelante a buscar (default: 2)
            
        Returns:
            Lista de diccionarios con datos de partidos
        """
        all_matches = []
        
        for day_offset in range(dias):
            fecha = datetime.now() + timedelta(days=day_offset)
            fecha_str = fecha.strftime("%Y-%m-%d")
            
            # Flashscore usa formato de fecha en la URL: 2024-01-15
            url = f"{self.base_url}/partidos/{fecha_str}/"
            
            soup = self._fetch_with_retry(url)
            if not soup:
                continue
            
            # Buscar todos los eventos de partidos
            eventos = soup.find_all('div', class_=re.compile(r'event^'))
            
            for evento in eventos:
                try:
                    partido = self._parse_match_event(evento, fecha_str)
                    if partido:
                        all_matches.append(partido)
                except Exception as e:
                    continue
        
        return all_matches
    
    def _parse_match_event(self, evento, fecha_str: str) -> Optional[Dict]:
        """Parsea un evento individual de partido"""
        # Obtener ID del partido
        event_id = evento.get('id', '')
        if not event_id or not event_id.startswith('g_'):
            return None
        
        fixture_id = event_id.replace('g_', '')
        
        # Obtener hora
        time_elem = evento.find('div', class_=re.compile(r'event__time'))
        hora = time_elem.text.strip() if time_elem else "00:00"
        
        # Obtener liga
        league_elem = evento.find('div', class_=re.compile(r'event__league'))
        liga = self._clean_text(league_elem.text) if league_elem else "Liga"
        
        # Obtener equipos
        home_elem = evento.find('div', class_=re.compile(r'event__home'))
        away_elem = evento.find('div', class_=re.compile(r'event__away'))
        
        home_name = self._clean_text(home_elem.text) if home_elem else "Local"
        away_name = self._clean_text(away_elem.text) if away_elem else "Visita"
        
        # Calcular prioridad
        prioridad = self._get_priority(liga)
        
        return {
            "fixture_id": self._generate_fixture_id(home_name, away_name, fecha_str),
            "fecha": fecha_str,
            "hora": hora,
            "liga": liga,
            "prioridad": prioridad,
            "equipo_local": home_name,
            "equipo_visitante": away_name,
            "source": "flashscore"
        }
    
    def _generate_fixture_id(self, home: str, away: str, fecha: str) -> int:
        """Genera un ID único para el partido"""
        import hashlib
        key = f"{home}{away}{fecha}".encode()
        return int(hashlib.md5(key).hexdigest()[:8], 16) % (10 ** 10)
    
    def get_league_matches(self, league_url: str) -> List[Dict]:
        """
        Obtiene todos los partidos de una liga específica
        
        Args:
            league_url: URL relativa de la liga en Flashscore
            
        Returns:
            Lista de partidos
        """
        url = f"{self.base_url}/{league_url}"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return []
        
        matches = []
        eventos = soup.find_all('div', class_=re.compile(r'event^'))
        
        for evento in eventos:
            partido = self._parse_match_event_simple(evento)
            if partido:
                matches.append(partido)
        
        return matches
    
    def _parse_match_event_simple(self, evento) -> Optional[Dict]:
        """Parse simplificado para eventos de liga"""
        # Similar al anterior pero sin fecha
        return None
    
    def scrape(self, dias: int = 2) -> List[Dict]:
        """
        Método principal del scraper
        
        Args:
            dias: Número de días hacia adelante
            
        Returns:
            Lista de partidos
        """
        return self.get_today_matches(dias=dias)


# Ejemplo de uso
if __name__ == "__main__":
    scraper = FlashscoreScraper()
    partidos = scraper.scrape(dias=2)
    print(f"Total partidos encontrados: {len(partidos)}")
    for p in partidos[:5]:
        print(f"  {p['fecha']} {p['hora']} - {p['liga']}: {p['equipo_local']} vs {p['equipo_visitante']}")
