"""
Scraper para Soccerway
Fuente: https://www.soccerway.com/
Captura: Resultados históricos, alineaciones, goleadores, estadísticas detalladas de partidos
"""
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_scraper import BaseScraper


class SoccerwayScraper(BaseScraper):
    """Scraper específico para Soccerway"""
    
    def __init__(self):
        super().__init__(timeout=30, retry_count=3)
        self.base_url = "https://www.soccerway.com"
        
        # URLs de ligas principales
        self.ligas = {
            "premier league": "national/england/premier-league/20242025",
            "la liga": "national/spain/primera-division/20242025",
            "serie a": "national/italy/serie-a/20242025",
            "bundesliga": "national/germany/bundesliga/20242025",
            "ligue 1": "national/france/ligue-1/20242025",
            "brasileiro": "national/brazil/serie-a/2025",
            "mls": "national/usa/major-league-soccer/2024",
            "liga mx": "national/mexico/liga-mx/2024",
            "argentina": "national/argentina/primera-division/2024",
        }
    
    def get_league_results(self, league: str, limit: int = 50) -> List[Dict]:
        """
        Obtiene los resultados de una liga
        
        Args:
            league: Nombre de la liga
            limit: Número máximo de partidos a obtener
            
        Returns:
            Lista de partidos con resultados
        """
        if league.lower() not in self.ligas:
            return []
        
        url_path = self.ligas[league.lower()]
        url = f"{self.base_url}/{url_path}/results"
        
        soup = self._fetch_with_retry(url)
        if not soup:
            return []
        
        results = []
        matches = soup.find_all('tr', class_='match')
        
        for match in matches[:limit]:
            try:
                result = self._parse_match_result(match)
                if result:
                    result['liga'] = league
                    results.append(result)
            except Exception:
                continue
        
        return results
    
    def _parse_match_result(self, match_row) -> Optional[Dict]:
        """Parsea una fila de resultado de partido"""
        cells = match_row.find_all('td')
        if len(cells) < 5:
            return None
        
        # Fecha
        date_cell = cells[0]
        date_elem = date_cell.find('a') or date_cell.find('span')
        fecha = self._clean_text(date_elem.text) if date_elem else ""
        
        # Hora (si existe)
        time_elem = cells[1].find('span')
        hora = time_elem.text.strip() if time_elem else ""
        
        # Equipo local
        home_elem = cells[2].find('a')
        home_name = self._clean_text(home_elem.text) if home_elem else ""
        
        # Resultado
        score_cell = cells[3]
        score_elem = score_cell.find('a') or score_cell
        score_text = self._clean_text(score_elem.text)
        
        # Parsear score
        score_parts = score_text.split('-')
        if len(score_parts) == 2:
            home_goals = self._parse_number(score_parts[0])
            away_goals = self._parse_number(score_parts[1])
        else:
            home_goals, away_goals = None, None
        
        # Equipo visitante
        away_elem = cells[4].find('a')
        away_name = self._clean_text(away_elem.text) if away_elem else ""
        
        # Generar ID único
        import hashlib
        match_id = hashlib.md5(f"{home_name}{away_name}{fecha}".encode()).hexdigest()[:12]
        
        return {
            "match_id": match_id,
            "fecha": fecha,
            "hora": hora,
            "equipo_local": home_name,
            "equipo_visitante": away_name,
            "goles_local": int(home_goals) if home_goals else 0,
            "goles_visitante": int(away_goals) if away_goals else 0,
            "resultado_completo": score_text,
        }
    
    def get_team_matches(self, team_name: str, league: str = None, limit: int = 20) -> List[Dict]:
        """
        Obtiene los partidos de un equipo específico
        
        Args:
            team_name: Nombre del equipo
            league: Liga opcional para filtrar
            limit: Número máximo de partidos
            
        Returns:
            Lista de partidos del equipo
        """
        # Normalizar nombre para URL
        team_url = team_name.lower().replace(' ', '_').replace('/', '-')
        
        if league and league.lower() in self.ligas:
            url_path = self.ligas[league.lower()]
            url = f"{self.base_url}/{url_path}/teams/{team_url}"
        else:
            # Buscar en todas las ligas
            url = f"{self.base_url}/search/?q={team_name}"
            soup = self._fetch_with_retry(url)
            if soup:
                # Buscar enlace del equipo
                team_link = soup.find('a', href=re.compile(f'/teams/'))
                if team_link:
                    url = self.base_url + team_link.get('href')
                else:
                    return []
        
        soup = self._fetch_with_retry(url)
        if not soup:
            return []
        
        matches = []
        match_rows = soup.find_all('tr', class_='match')
        
        for row in match_rows[:limit]:
            try:
                match = self._parse_match_result(row)
                if match:
                    match['liga'] = league or "Unknown"
                    matches.append(match)
            except Exception:
                continue
        
        return matches
    
    def get_team_form(self, team_name: str, num_matches: int = 5) -> List[Dict]:
        """
        Obtiene los últimos resultados de un equipo para calcular forma actual
        
        Args:
            team_name: Nombre del equipo
            num_matches: Número de últimos partidos
            
        Returns:
            Lista con resultados recientes y forma
        """
        matches = self.get_team_matches(team_name, limit=num_matches * 2)
        
        if not matches:
            return []
        
        form = []
        for match in matches[:num_matches]:
            # Determinar si el equipo ganó, perdió o empató
            is_home = match['equipo_local'].lower() == team_name.lower()
            
            if is_home:
                if match['goles_local'] > match['goles_visitante']:
                    result = 'W'  # Win
                elif match['goles_local'] < match['goles_visitante']:
                    result = 'L'  # Loss
                else:
                    result = 'D'  # Draw
            else:
                if match['goles_visitante'] > match['goles_local']:
                    result = 'W'
                elif match['goles_visitante'] < match['goles_local']:
                    result = 'L'
                else:
                    result = 'D'
            
            form.append({
                'resultado': result,
                'fecha': match['fecha'],
                'rival': match['equipo_visitante'] if is_home else match['equipo_local'],
                'marcador': match['resultado_completo']
            })
        
        return form
    
    def calculate_team_form_score(self, team_name: str) -> Dict:
        """
        Calcula un score de forma basado en últimos partidos
        
        Args:
            team_name: Nombre del equipo
            
        Returns:
            Diccionario con score de forma
        """
        form = self.get_team_form(team_name, num_matches=5)
        
        if not form:
            return {'score': 0, 'form_string': '', 'wins': 0, 'draws': 0, 'losses': 0}
        
        wins = sum(1 for f in form if f['resultado'] == 'W')
        draws = sum(1 for f in form if f['resultado'] == 'D')
        losses = sum(1 for f in form if f['resultado'] == 'L')
        
        # Score de forma: 3 puntos por victoria, 1 por empate
        form_score = (wins * 3) + draws
        
        # Porcentaje de puntos posibles
        max_points = len(form) * 3
        form_percentage = round((form_score / max_points) * 100, 1) if max_points > 0 else 0
        
        form_string = ''.join([f['resultado'] for f in form])
        
        return {
            'score': form_score,
            'form_string': form_string,
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'percentage': form_percentage
        }
    
    def get_match_details(self, match_url: str) -> Dict:
        """
        Obtiene detalles de un partido específico
        
        Args:
            match_url: URL del partido
            
        Returns:
            Diccionario con detalles del partido
        """
        url = f"{self.base_url}/{match_url}"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return {}
        
        details = {}
        
        # Buscar goleadores
        scorers_section = soup.find('div', class_='scorers')
        if scorers_section:
            details['goleadores'] = self._clean_text(scorers_section.text)
        
        # Buscar裁判 (árbitro)
        referee_elem = soup.find('td', class_='referee')
        if referee_elem:
            details['arbitro'] = self._clean_text(referee_elem.text)
        
        # Estadio
        stadium_elem = soup.find('td', class_='stadium')
        if stadium_elem:
            details['estadio'] = self._clean_text(stadium_elem.text)
        
        return details
    
    def scrape(self, league: str = "premier league") -> Dict:
        """
        Método principal del scraper
        
        Args:
            league: Liga a scrapear
            
        Returns:
            Diccionario con resultados
        """
        results = self.get_league_results(league, limit=50)
        
        return {
            "liga": league,
            "resultados": results,
            "source": "soccerway"
        }


# Ejemplo de uso
if __name__ == "__main__":
    scraper = SoccerwayScraper()
    
    # Obtener resultados de Premier League
    resultado = scraper.scrape("premier league")
    print(f"Liga: {resultado['liga']}")
    print(f"Partidos: {len(resultado['resultados'])}")
    for match in resultado['resultados'][:5]:
        print(f"  {match['fecha']}: {match['equipo_local']} {match['resultado_completo']} {match['equipo_visitante']}")
