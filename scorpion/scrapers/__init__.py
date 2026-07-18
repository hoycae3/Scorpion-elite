"""
Scorpion Elite - Módulo de Scrapers
===================================
Scraping multi-fuente para datos de fútbol:

- API-Football: Partidos del día (principal)
- Transfermarkt: Tablas de posiciones, valor de mercado
- Soccerway: Resultados históricos, forma actual
- WhoScored: Estadísticas avanzadas (corners, tarjetas, posesión)

Uso:
    from scorpion.scrapers import SimpleMatchScraper
    
    scraper = SimpleMatchScraper()
    partidos = scraper.scrape(dias=2)
"""

# Scraper principal de partidos (usa API-Football)
from .simple_scraper import SimpleMatchScraper

# Scraper de estadísticas
from .transfermarkt_scraper import TransfermarktScraper
from .soccerway_scraper import SoccerwayScraper
from .whoscored_scraper import WhoScoredScraper

# Scraper legacy (Flashscore con playwright)
from .flashscore_scraper import FlashscoreScraper

# Scraper unificado
from .scraper_unificado import ScraperUnificado

__all__ = [
    "SimpleMatchScraper",
    "FlashscoreScraper",
    "TransfermarktScraper", 
    "SoccerwayScraper",
    "WhoScoredScraper",
    "ScraperUnificado",
]

__version__ = "2.0.0"
