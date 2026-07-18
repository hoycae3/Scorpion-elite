"""
Scorpion Elite - Módulo de Scrapers
===================================
Scraping con Playwright (JavaScript real):

- Soccerway: Partidos del día (Playwright)
- Transfermarkt: Tablas de posiciones
- Soccerway Stats: Resultados históricos
- WhoScored: Estadísticas avanzadas

Uso:
    from scorpion.scrapers import PlaywrightMatchesScraper
    
    scraper = PlaywrightMatchesScraper()
    partidos = scraper.scrape()
"""

# Scraper de partidos (usa Playwright)
from .playwright_matches_scraper import PlaywrightMatchesScraper

# Scraper de estadísticas
from .transfermarkt_scraper import TransfermarktScraper
from .soccerway_scraper import SoccerwayScraper
from .whoscored_scraper import WhoScoredScraper

# Scraper unificado
from .scraper_unificado import ScraperUnificado

__all__ = [
    "PlaywrightMatchesScraper",
    "SoccerwayScraper",
    "TransfermarktScraper", 
    "WhoScoredScraper",
    "ScraperUnificado",
]

__version__ = "2.0.0"
