"""
Scorpion Elite - Compatibilidad para scrapers_fallback
======================================================
Este archivo mantiene la compatibilidad para imports de elite.py
La lógica real está en robot_extractor.py
"""

from robot_extractor import scrape_team_fallback

__all__ = ['scrape_team_fallback']
