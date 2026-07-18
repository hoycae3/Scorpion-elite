"""
Scraper Simple - Scorpion Elite
Usa API-Football para obtener partidos (ya configurada en el proyecto)
"""
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class SimpleMatchScraper:
    """Scraper simple usando API-Football que ya está configurada"""
    
    # API Keys de API-Football (del proyecto original)
    API_KEYS = [
        "e3926f829cd848f4b2b54d722ca29701",
        "124c9519df145caf883cd82f0b2a4671",
    ]
    
    # Mapeo de ligas a prioridades
    LIGAS_PRIORIDAD = {
        "champions league": 15, "champions": 15,
        "premier league": 14, "premier": 14,
        "la liga": 13, "liga": 13,
        "serie a": 12,
        "bundesliga": 11,
        "ligue 1": 10,
        "brasileiro": 7, "brasil": 7,
        "eredivisie": 7,
        "liga mx": 6,
        "major league soccer": 5, "mls": 5,
        "usl championship": 4,
        "primera nacional": 3, "copa argentina": 3,
    }
    
    def __init__(self):
        self.session = requests.Session()
    
    def _get_priority(self, league_name: str) -> int:
        """Calcula la prioridad de una liga"""
        league_lower = league_name.lower()
        for key, priority in self.LIGAS_PRIORIDAD.items():
            if key in league_lower:
                return priority
        return 1
    
    def get_matches(self, fecha_str: str) -> List[Dict]:
        """Obtiene partidos de una fecha específica"""
        all_matches = []
        
        for api_key in self.API_KEYS:
            try:
                url = f"https://v3.football.api-sports.io/fixtures"
                params = {"date": fecha_str}
                headers = {"x-apisports-key": api_key}
                
                response = requests.get(url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response"):
                        for fixture in data["response"]:
                            league = fixture.get("league", {})
                            teams = fixture.get("teams", {})
                            fixture_data = fixture.get("fixture", {})
                            
                            home_name = teams.get("home", {}).get("name", "Local")
                            away_name = teams.get("away", {}).get("name", "Visita")
                            league_name = league.get("name", "Liga")
                            
                            # Hora local (UTC-3 para Latinoamérica)
                            hora_utc = fixture_data.get("date", "")[11:16]
                            try:
                                dt = datetime.strptime(hora_utc, "%H:%M")
                                dt = dt + timedelta(hours=-3)
                                hora_local = dt.strftime("%H:%M")
                            except:
                                hora_local = hora_utc
                            
                            import hashlib
                            fixture_id = hashlib.md5(f"{home_name}{away_name}{fecha_str}".encode()).hexdigest()[:12]
                            fixture_id_int = int.from_bytes(fixture_id.encode()[:8], 'big') % (10**10)
                            
                            all_matches.append({
                                "fixture_id": fixture_id_int,
                                "fecha": fecha_str,
                                "hora": hora_local,
                                "liga": league_name,
                                "prioridad": self._get_priority(league_name),
                                "equipo_local": home_name,
                                "equipo_visitante": away_name,
                                "source": "api-football"
                            })
                        
                        print(f"API-Football: {len(data['response'])} partidos")
                        break  # Si funcionó, no intentar otra key
                        
            except Exception as e:
                print(f"Error API-Football: {e}")
                continue
        
        return all_matches
    
    def get_today_matches(self, dias: int = 2) -> List[Dict]:
        """Obtiene partidos de los próximos días"""
        all_matches = []
        
        for i in range(dias):
            fecha = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            matches = self.get_matches(fecha)
            all_matches.extend(matches)
            print(f"Fecha {fecha}: {len(matches)} partidos")
        
        # Eliminar duplicados
        seen = set()
        unique = []
        for m in all_matches:
            fid = m["fixture_id"]
            if fid not in seen:
                seen.add(fid)
                unique.append(m)
        
        return unique
    
    def scrape(self, dias: int = 2) -> List[Dict]:
        """Método principal"""
        return self.get_today_matches(dias=dias)


# Ejemplo de uso
if __name__ == "__main__":
    scraper = SimpleMatchScraper()
    partidos = scraper.scrape(dias=2)
    print(f"\nTotal partidos: {len(partidos)}")
    for p in partidos[:10]:
        print(f"  {p['fecha']} {p['hora']} - {p['liga']}: {p['equipo_local']} vs {p['equipo_visitante']}")
