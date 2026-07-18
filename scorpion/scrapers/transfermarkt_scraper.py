"""
Scraper para Transfermarkt
Fuente: https://www.transfermarkt.com/
Captura: Estadísticas de equipos, valor de mercado, plantilla, lesiones, sanciones
"""
import re
from typing import Dict, List, Optional
from .base_scraper import BaseScraper


class TransfermarktScraper(BaseScraper):
    """Scraper específico para Transfermarkt"""
    
    def __init__(self):
        super().__init__(timeout=30, retry_count=3)
        self.base_url = "https://www.transfermarkt.com"
        
        # URLs de ligas principales
        self.ligas = {
            "premier league": "premier-league/startseite/wettbewerb/GB1",
            "la liga": "laliga/startseite/wettbewerb/ES1",
            "serie a": "serie-a/startseite/wettbewerb/IT1",
            "bundesliga": "1-bundesliga/startseite/wettbewerb/L1",
            "ligue 1": "ligue-1/startseite/wettbewerb/FR1",
            "brasileiro": "campeonato-brasileiro-serie-a/startseite/wettbewerb/BRA1",
            "mls": "major-league-soccer/startseite/wettbewerb/US1",
            "liga mx": "liga-mx/startseite/wettbewerb/MEX1",
        }
    
    def get_league_standings(self, league: str) -> List[Dict]:
        """
        Obtiene la tabla de posiciones de una liga
        
        Args:
            league: Nombre de la liga (ej: "premier league", "la liga")
            
        Returns:
            Lista de equipos con estadísticas
        """
        if league.lower() not in self.ligas:
            return []
        
        url_path = self.ligas[league.lower()]
        url = f"{self.base_url}/{url_path}"
        
        soup = self._fetch_with_retry(url)
        if not soup:
            return []
        
        standings = []
        
        # Buscar tabla de posiciones
        table = soup.find('table', class_='items')
        if not table:
            return []
        
        rows = table.find_all('tr')
        for row in rows:
            try:
                team_data = self._parse_standings_row(row)
                if team_data:
                    team_data['liga'] = league
                    standings.append(team_data)
            except Exception:
                continue
        
        return standings
    
    def _parse_standings_row(self, row) -> Optional[Dict]:
        """Parsea una fila de la tabla de posiciones"""
        cells = row.find_all('td')
        if len(cells) < 8:
            return None
        
        # Número de plaza
        posicion = cells[0].text.strip()
        if not posicion.isdigit():
            return None
        
        # Nombre del equipo
        team_link = cells[1].find('a')
        team_name = self._clean_text(team_link.text) if team_link else ""
        
        # Partidos jugados
        played = self._parse_number(cells[2].text)
        
        # Victorias
        wins = self._parse_number(cells[3].text)
        
        # Empates
        draws = self._parse_number(cells[4].text)
        
        # Derrotas
        losses = self._parse_number(cells[5].text)
        
        # Goles a favor
        goals_for = self._parse_number(cells[6].text)
        
        # Goles en contra
        goals_against = self._parse_number(cells[7].text)
        
        # Diferencia de goles
        diff_cell = cells[8].text.strip()
        goal_diff = self._parse_number(diff_cell)
        
        # Puntos
        points = self._parse_number(cells[9].text)
        
        return {
            "posicion": int(posicion) if posicion.isdigit() else 0,
            "equipo": team_name,
            "partidos_jugados": int(played) if played else 0,
            "victorias": int(wins) if wins else 0,
            "empates": int(draws) if draws else 0,
            "derrotas": int(losses) if losses else 0,
            "goles_favor": int(goals_for) if goals_for else 0,
            "goles_contra": int(goals_against) if goals_against else 0,
            "diferencia_goles": int(goal_diff) if goal_diff else 0,
            "puntos": int(points) if points else 0,
        }
    
    def get_team_stats(self, team_url: str) -> Dict:
        """
        Obtiene estadísticas detalladas de un equipo
        
        Args:
            team_url: URL relativa del equipo
            
        Returns:
            Diccionario con estadísticas del equipo
        """
        url = f"{self.base_url}/{team_url}"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return {}
        
        stats = {}
        
        # Valor de mercado del equipo
        value_elem = soup.find('a', class_='data-header__market-value')
        if value_elem:
            stats['valor_mercado'] = self._clean_text(value_elem.text)
        
        # Nombre completo
        title_elem = soup.find('h1', class_='data-header__headline-container')
        if title_elem:
            stats['nombre_completo'] = self._clean_text(title_elem.text)
        
        # Información del estadio
        stadium_elem = soup.find('span', class_='data-header__stadium')
        if stadium_elem:
            stats['estadio'] = self._clean_text(stadium_elem.text)
        
        # Estadio capacidad
        capacity_elem = soup.find('span', class_='data-header__stadium-capacity')
        if capacity_elem:
            stats['capacidad_estadio'] = self._parse_number(capacity_elem.text)
        
        return stats
    
    def get_team_squad(self, team_url: str) -> List[Dict]:
        """
        Obtiene la plantilla de un equipo
        
        Args:
            team_url: URL relativa del equipo
            
        Returns:
            Lista de jugadores con información
        """
        url = f"{self.base_url}/{team_url}/kader/1"
        soup = self._fetch_with_retry(url)
        
        if not soup:
            return []
        
        squad = []
        table = soup.find('table', class_='items')
        if not table:
            return []
        
        rows = table.find_all('tr')
        for row in rows:
            try:
                player = self._parse_player_row(row)
                if player:
                    squad.append(player)
            except Exception:
                continue
        
        return squad
    
    def _parse_player_row(self, row) -> Optional[Dict]:
        """Parsea una fila de la plantilla"""
        cells = row.find_all('td')
        if len(cells) < 6:
            return None
        
        # Número
        number = self._parse_number(cells[0].text)
        
        # Nombre
        name_link = cells[1].find('a')
        name = self._clean_text(name_link.text) if name_link else ""
        
        # Posición
        position = cells[2].text.strip()
        
        # Fecha de nacimiento
        birth_date = cells[3].text.strip()
        
        # Nacionalidad
        nationality_elem = cells[4].find('img')
        nationality = nationality_elem.get('title', '') if nationality_elem else ""
        
        # Valor de mercado del jugador
        market_value = self._clean_text(cells[5].text)
        
        return {
            "numero": int(number) if number else None,
            "nombre": name,
            "posicion": position,
            "fecha_nacimiento": birth_date,
            "nacionalidad": nationality,
            "valor_mercado": market_value,
        }
    
    def get_league_stats(self, league: str) -> Dict:
        """
        Obtiene estadísticas generales de una liga
        
        Args:
            league: Nombre de la liga
            
        Returns:
            Diccionario con estadísticas de la liga
        """
        if league.lower() not in self.ligas:
            return {}
        
        url_path = self.ligas[league.lower()]
        url = f"{self.base_url}/{url_path}"
        
        soup = self._fetch_with_retry(url)
        if not soup:
            return {}
        
        stats = {}
        
        # Buscar secciones de estadísticas
        sections = soup.find_all('div', class_='quick-facts__value')
        
        if len(sections) > 0:
            stats['total_valor'] = self._clean_text(sections[0].text) if sections else ""
        
        return stats
    
    def scrape(self, league: str = "premier league") -> Dict:
        """
        Método principal del scraper
        
        Args:
            league: Liga a scrapear
            
        Returns:
            Diccionario con tabla de posiciones y estadísticas
        """
        standings = self.get_league_standings(league)
        stats = self.get_league_stats(league)
        
        return {
            "liga": league,
            "tabla_posiciones": standings,
            "estadisticas_liga": stats,
            "source": "transfermarkt"
        }


# Ejemplo de uso
if __name__ == "__main__":
    scraper = TransfermarktScraper()
    
    # Obtener tabla de Premier League
    resultado = scraper.scrape("premier league")
    print(f"Liga: {resultado['liga']}")
    print(f"Equipos: {len(resultado['tabla_posiciones'])}")
    for equipo in resultado['tabla_posiciones'][:5]:
        print(f"  {equipo['posicion']}. {equipo['equipo']} - {equipo['puntos']} pts")
