"""
Scraper para WhoScored
Fuente: https://www.whoscored.com/
Captura: Estadísticas avanzadas - posesión, disparos, corners, tarjetas, duelos, passes
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from .base_scraper import BaseScraper


class WhoScoredScraper(BaseScraper):
    """Scraper específico para WhoScored"""
    
    # Mapeo de regiones/ligas
    REGIONS = {
        "england": "England",
        "spain": "Spain",
        "italy": "Italy",
        "germany": "Germany",
        "france": "France",
        "brazil": "Brazil",
        "usa": "USA",
        "argentina": "Argentina",
        "mexico": "Mexico",
    }
    
    def __init__(self):
        super().__init__(timeout=30, retry_count=3)
        self.base_url = "https://www.whoscored.com"
        
        # Agentes de usuario rotativos para evitar bloqueos
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        ]
    
    def _rotate_user_agent(self):
        """Rota el user agent para evitar bloqueos"""
        import random
        self.session.headers.update({
            "User-Agent": random.choice(self.user_agents)
        })
    
    def get_region_tournaments(self, region: str) -> List[Dict]:
        """
        Obtiene los torneos disponibles en una región
        
        Args:
            region: Nombre de la región/país
            
        Returns:
            Lista de torneos disponibles
        """
        region_key = region.lower()
        if region_key not in self.REGIONS:
            return []
        
        url = f"{self.base_url}/Regions/{self.REGIONS[region_key]}"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return []
        
        tournaments = []
        
        # Buscar enlaces de torneos
        links = soup.find_all('a', href=re.compile(r'/Tournaments/'))
        for link in links:
            href = link.get('href', '')
            name = self._clean_text(link.text)
            
            if name and '/Live' not in href:
                tournaments.append({
                    'name': name,
                    'url': href
                })
        
        return tournaments
    
    def get_tournament_matches(self, tournament_id: int, days: int = 7) -> List[Dict]:
        """
        Obtiene los partidos de un torneo específico
        
        Args:
            tournament_id: ID del torneo
            days: Número de días hacia adelante/atrás
            
        Returns:
            Lista de partidos
        """
        # WhoScored usa fechas en formato timestamp
        date_to = datetime.now() + timedelta(days=days)
        date_from = datetime.now() - timedelta(days=1)
        
        # Formato: /Tournaments/Show/{tournament_id}?category=categoryId&subcategory=subCategoryId&tournamentOptions=tournamentOptions
        url = f"{self.base_url}/Tournaments/Show/{tournament_id}"
        
        # Parámetros para obtener partidos
        params = {
            "category": "1",  # General
            "subcategory": "0",  # All
        }
        
        soup = self._fetch_with_retry(url, params=params)
        if not soup:
            return []
        
        matches = []
        
        # Buscar datos de partidos en scripts JSON
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'matchList' in script.string:
                try:
                    # Extraer JSON de los datos
                    match_data = self._extract_match_data(script.string)
                    if match_data:
                        matches.extend(match_data)
                except Exception:
                    continue
        
        return matches
    
    def _extract_match_data(self, script_text: str) -> List[Dict]:
        """Extrae datos de partidos del script JSON"""
        matches = []
        
        # Buscar patrón de datos de partidos
        patterns = [
            r'"matches":\[(.*?)\]',
            r'data-match-id="(\d+)"',
        ]
        
        for pattern in patterns:
            matches_found = re.findall(pattern, script_text, re.DOTALL)
            for match_str in matches_found[:10]:
                try:
                    # Intentar parsear como JSON
                    if match_str.startswith('{') or match_str.startswith('['):
                        data = json.loads(match_str)
                        if isinstance(data, list):
                            for item in data:
                                if 'homeTeam' in item:
                                    matches.append(self._parse_whoscored_match(item))
                except json.JSONDecodeError:
                    continue
        
        return matches
    
    def _parse_whoscored_match(self, data: Dict) -> Dict:
        """Parsea un partido de WhoScored"""
        home = data.get('homeTeam', {})
        away = data.get('awayTeam', {})
        
        return {
            'match_id': data.get('id'),
            'fecha': data.get('startDateTime', ''),
            'equipo_local': home.get('name', ''),
            'equipo_visitante': away.get('name', ''),
            'home_id': home.get('id'),
            'away_id': away.get('id'),
        }
    
    def get_match_stats(self, match_id: int) -> Dict:
        """
        Obtiene estadísticas detalladas de un partido
        
        Args:
            match_id: ID del partido
            
        Returns:
            Diccionario con estadísticas
        """
        self._rotate_user_agent()  # Rotar user agent para evitar bloqueos
        
        url = f"{self.base_url}/MatchDetails/Match/{match_id}"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return {}
        
        stats = {
            'match_id': match_id,
            'stats': {},
            'history': []
        }
        
        # Buscar estadísticas del partido
        stats_div = soup.find('div', id='match-centre-stats')
        if stats_div:
            stats['stats'] = self._parse_match_stats(stats_div)
        
        # Buscar historial de cara a cara
        h2h_div = soup.find('div', id='h2h-form')
        if h2h_div:
            stats['history'] = self._parse_head_to_head(h2h_div)
        
        return stats
    
    def _parse_match_stats(self, stats_div) -> Dict:
        """Parsea las estadísticas del partido"""
        stats_data = {}
        
        # Buscar filas de estadísticas
        rows = stats_div.find_all('div', class_=re.compile(r'stats-row'))
        
        for row in rows:
            # Nombre de la estadística
            stat_name_elem = row.find('div', class_='stat-label')
            stat_name = self._clean_text(stat_name_elem.text) if stat_name_elem else ""
            
            # Valores de los equipos
            stat_values = row.find_all('span', class_=re.compile(r'stat-value'))
            
            if len(stat_values) >= 2:
                home_value = self._clean_text(stat_values[0].text)
                away_value = self._clean_text(stat_values[1].text)
                
                # Mapear nombres de estadísticas
                stat_key = self._map_stat_name(stat_name)
                if stat_key:
                    stats_data[stat_key] = {
                        'home': home_value,
                        'away': away_value,
                        'home_num': self._parse_number(home_value),
                        'away_num': self._parse_number(away_value)
                    }
        
        return stats_data
    
    def _map_stat_name(self, name: str) -> Optional[str]:
        """Mapea nombres de estadísticas a claves normalizadas"""
        mappings = {
            'Possession %': 'possession',
            'Goals': 'goals',
            'Goal Attempts': 'shots_total',
            'Shots on Target': 'shots_on_target',
            'Shots off Target': 'shots_off_target',
            'Blocked Shots': 'shots_blocked',
            'Corner Kicks': 'corners',
            'Fouls': 'fouls',
            'Offsides': 'offsides',
            'Yellow Cards': 'yellow_cards',
            'Red Cards': 'red_cards',
            'Saves': 'saves',
            'Passes': 'passes',
            'Passes %': 'pass_accuracy',
            'Tackles': 'tackles',
            'Interceptions': 'interceptions',
            'Clearances': 'clearances',
            'Awards': 'awards',
        }
        
        name_lower = name.lower().strip()
        for key, mapped in mappings.items():
            if key.lower() in name_lower:
                return mapped
        
        return None
    
    def _parse_head_to_head(self, h2h_div) -> List[Dict]:
        """Parsea el historial de cara a cara"""
        history = []
        matches = h2h_div.find_all('div', class_='h2h-match')
        
        for match in matches[:10]:
            try:
                teams = match.find_all('span', class_='h2h-team')
                scores = match.find_all('span', class_='h2h-score')
                
                if len(teams) >= 2 and len(scores) >= 1:
                    score_text = scores[0].text.strip()
                    score_parts = score_text.split('-')
                    
                    if len(score_parts) == 2:
                        history.append({
                            'home_team': self._clean_text(teams[0].text),
                            'away_team': self._clean_text(teams[1].text),
                            'home_goals': self._parse_number(score_parts[0]),
                            'away_goals': self._parse_number(score_parts[1]),
                        })
            except Exception:
                continue
        
        return history
    
    def get_team_stats(self, team_id: int) -> Dict:
        """
        Obtiene estadísticas generales de un equipo
        
        Args:
            team_id: ID del equipo
            
        Returns:
            Diccionario con estadísticas del equipo
        """
        self._rotate_user_agent()
        
        url = f"{self.base_url}/Teams/{team_id}"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return {}
        
        stats = {}
        
        # Buscar estadísticas del equipo
        stats_section = soup.find('div', class_='team-field-total')
        if stats_section:
            stats['totals'] = self._parse_team_stats(stats_section)
        
        return stats
    
    def _parse_team_stats(self, stats_section) -> Dict:
        """Parsea las estadísticas del equipo"""
        stats = {}
        
        items = stats_section.find_all('div', class_='category-data-item')
        for item in items:
            label = item.find('div', class_='category-data-label')
            value = item.find('div', class_='category-data-value')
            
            if label and value:
                key = self._clean_text(label.text).lower().replace(' ', '_')
                stats[key] = self._clean_text(value.text)
        
        return stats
    
    def get_upcoming_matches(self, region: str = "England") -> List[Dict]:
        """
        Obtiene los próximos partidos de una región
        
        Args:
            region: Región para filtrar
            
        Returns:
            Lista de próximos partidos
        """
        self._rotate_user_agent()
        
        # WhoScored muestra partidos en vivo en la página principal
        url = f"{self.base_url}/"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return []
        
        matches = []
        
        # Buscar sección de partidos
        match_sections = soup.find_all('div', class_=re.compile(r' match-'))
        
        for section in match_sections[:20]:
            try:
                match = self._parse_upcoming_match(section)
                if match:
                    matches.append(match)
            except Exception:
                continue
        
        return matches
    
    def _parse_upcoming_match(self, section) -> Optional[Dict]:
        """Parsea un próximo partido"""
        # Buscar equipos
        teams = section.find_all('span', class_=re.compile(r'team-name'))
        
        if len(teams) < 2:
            return None
        
        home_name = self._clean_text(teams[0].text)
        away_name = self._clean_text(teams[1].text)
        
        # Buscar hora o estado
        time_elem = section.find('span', class_=re.compile(r'time'))
        time_text = time_elem.text.strip() if time_elem else "Por confirmar"
        
        # Generar ID
        import hashlib
        match_id = hashlib.md5(f"{home_name}{away_name}".encode()).hexdigest()[:10]
        
        return {
            'match_id': match_id,
            'equipo_local': home_name,
            'equipo_visitante': away_name,
            'hora': time_text,
            'source': 'whoscored'
        }
    
    def scrape(self, region: str = "England") -> Dict:
        """
        Método principal del scraper
        
        Args:
            region: Región a scrapear
            
        Returns:
            Diccionario con datos
        """
        upcoming = self.get_upcoming_matches(region)
        
        return {
            "region": region,
            "proximos_partidos": upcoming,
            "source": "whoscored"
        }


# Ejemplo de uso
if __name__ == "__main__":
    scraper = WhoScoredScraper()
    
    # Obtener próximos partidos de Inglaterra
    resultado = scraper.scrape("England")
    print(f"Región: {resultado['region']}")
    print(f"Próximos partidos: {len(resultado['proximos_partidos'])}")
    for match in resultado['proximos_partidos'][:5]:
        print(f"  {match['equipo_local']} vs {match['equipo_visitante']} - {match['hora']}")
