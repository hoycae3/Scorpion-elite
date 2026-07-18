"""
Scorpion Elite - Módulo de Scrapers
===================================
Scraping de sitios web de fútbol:

- Flashscore.co: Partidos en vivo (principal - Latinoamérica)
- Transfermarkt: Tablas de posiciones
- Soccerway: Resultados históricos
- WhoScored: Estadísticas avanzadas

Uso:
    from scorpion.scrapers import FlashscoreCoScraper
    
    scraper = FlashscoreCoScraper()
    partidos = scraper.scrape()
"""

# Scraper de partidos (Flashscore.co - Latinoamericano)
from .flashscore_co_scraper import FlashscoreCoScraper

# Scraper legacy
from .playwright_matches_scraper import PlaywrightMatchesScraper

# Scraper de estadísticas
from .transfermarkt_scraper import TransfermarktScraper
from .soccerway_scraper import SoccerwayScraper
from .whoscored_scraper import WhoScoredScraper

# Scraper unificado
from .scraper_unificado import ScraperUnificado

__all__ = [
    "FlashscoreCoScraper",
    "PlaywrightMatchesScraper",
    "SoccerwayScraper",
    "TransfermarktScraper", 
    "WhoScoredScraper",
    "ScraperUnificado",
]

__version__ = "2.0.0"
