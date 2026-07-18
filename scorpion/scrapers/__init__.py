"""
Scorpion Elite - Módulo de Scrapers
===================================
Scraping multi-fuente para datos de fútbol:

- Flashscore: Partidos del día, cuotas
- Transfermarkt: Tablas de posiciones, valor de mercado
- Soccerway: Resultados históricos, forma actual
- WhoScored: Estadísticas avanzadas (corners, tarjetas, posesión)

Uso:
    from scorpion.scrapers import ScraperUnificado
    
    scraper = ScraperUnificado()
    partidos = scraper.scrape_partidos()
    equipos = scraper.scrape_all_leagues_transfermarkt()
"""

# Scraper principal unificado
from .scraper_unificado import ScraperUnificado

# Scraper individuales (para uso avanzado)
from .flashscore_scraper import FlashscoreScraper
from .transfermarkt_scraper import TransfermarktScraper
from .soccerway_scraper import SoccerwayScraper
from .whoscored_scraper import WhoScoredScraper
from .base_scraper import BaseScraper

__all__ = [
    "ScraperUnificado",
    "FlashscoreScraper",
    "TransfermarktScraper", 
    "SoccerwayScraper",
    "WhoScoredScraper",
    "BaseScraper",
]

__version__ = "2.0.0"
