"""Base scraper con utilidades comunes para todos los scrapers"""
import requests
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import time
import logging

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Clase base para todos los scrapers"""
    
    def __init__(self, timeout: int = 30, retry_count: int = 3):
        self.timeout = timeout
        self.retry_count = retry_count
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
    
    def _fetch_with_retry(self, url: str, parser: str = "html.parser") -> Optional[BeautifulSoup]:
        """Hace fetch con reintentos en caso de error"""
        for attempt in range(self.retry_count):
            try:
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                return BeautifulSoup(response.text, parser)
            except requests.RequestException as e:
                logger.warning(f"Intento {attempt + 1}/{self.retry_count} fallido para {url}: {e}")
                if attempt < self.retry_count - 1:
                    time.sleep(2 ** attempt)  # Backoff exponencial
        return None
    
    def _clean_text(self, text: str) -> str:
        """Limpia texto eliminando espacios extra"""
        if not text:
            return ""
        return " ".join(text.split())
    
    def _parse_number(self, text: str) -> Optional[float]:
        """Convierte texto a número"""
        if not text:
            return None
        try:
            # Eliminar caracteres no numéricos excepto punto y coma
            cleaned = ''.join(c for c in text if c.isdigit() or c in '.,')
            # Normalizar separador decimal
            cleaned = cleaned.replace(',', '.')
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> Any:
        """Método principal que cada scraper debe implementar"""
        pass
