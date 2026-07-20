"""Módulo de APIs."""
from scorpion.api.football import FootballAPI
from scorpion.api.scraper import (
    obtener_partidos_hoy,
    obtener_partidos_liga,
    obtener_estadisticas_equipo,
    obtener_top_goleadores_liga,
    calcular_confianza_partido,
    PartidoScraped,
    GoleadorScraped,
)

__all__ = [
    "FootballAPI",
    "obtener_partidos_hoy",
    "obtener_partidos_liga",
    "obtener_estadisticas_equipo",
    "obtener_top_goleadores_liga",
    "calcular_confianza_partido",
    "PartidoScraped",
    "GoleadorScraped",
]
