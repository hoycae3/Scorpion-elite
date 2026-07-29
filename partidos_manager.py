"""
Scorpion Elite - Gestor de Partidos
====================================
Sistema para consultar y guardar partidos automáticamente.

FLUJO:
1. Al iniciar → Verificar fechas guardadas en Supabase
2. Solo consultar fechas NUEVAS que no están guardadas
3. Guardar partidos en Supabase
4. Consultar estadísticas de equipos que juegan en 2-3 días
5. Guardar estadísticas en Supabase

PARTIDOS INVENTADOS (para pruebas sin usar API):
"""

from datetime import date, timedelta
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# PARTIDOS DE DEMOSTRACIÓN (SIN CONSUMIR API)
# ═══════════════════════════════════════════════════════════════════════════════

PARTIDOS_DEMO = [
    {
        "id": "demo_001",
        "fecha": "2026-07-29",
        "hora": "21:00",
        "liga": "Champions League",
        "equipo_local": "Real Madrid",
        "equipo_visitante": "Manchester City",
        "pais": "Europa",
        "stats_local": {
            "partidos_jugados": 38,
            "victorias": 24,
            "empates": 8,
            "derrotas": 6,
            "goles_favor": 75,
            "goles_contra": 32,
            "lambda_local": 1.95,
            "lambda_visitante": 1.10,
            "corners_promedio": 6.5,
            "tarjetas_promedio": 2.1,
            "tiros_promedio": 15.2,
            "forma": ["G", "G", "E", "W", "W"]
        },
        "stats_visitante": {
            "partidos_jugados": 38,
            "victorias": 28,
            "empates": 7,
            "derrotas": 3,
            "goles_favor": 94,
            "goles_contra": 33,
            "lambda_local": 2.10,
            "lambda_visitante": 1.25,
            "corners_promedio": 7.2,
            "tarjetas_promedio": 1.8,
            "tiros_promedio": 17.5,
            "forma": ["W", "W", "G", "W", "D"]
        }
    },
    {
        "id": "demo_002",
        "fecha": "2026-07-30",
        "hora": "20:00",
        "liga": "Champions League",
        "equipo_local": "Bayern Munich",
        "equipo_visitante": "Barcelona",
        "pais": "Europa",
        "stats_local": {
            "partidos_jugados": 34,
            "victorias": 26,
            "empates": 5,
            "derrotas": 3,
            "goles_favor": 102,
            "goles_contra": 32,
            "lambda_local": 2.50,
            "lambda_visitante": 1.15,
            "corners_promedio": 8.1,
            "tarjetas_promedio": 1.9,
            "tiros_promedio": 19.3,
            "forma": ["W", "W", "W", "G", "W"]
        },
        "stats_visitante": {
            "partidos_jugados": 38,
            "victorias": 22,
            "empates": 10,
            "derrotas": 6,
            "goles_favor": 68,
            "goles_contra": 43,
            "lambda_local": 1.75,
            "lambda_visitante": 1.00,
            "corners_promedio": 5.8,
            "tarjetas_promedio": 2.4,
            "tiros_promedio": 13.1,
            "forma": ["D", "G", "W", "E", "W"]
        }
    },
    {
        "id": "demo_003",
        "fecha": "2026-07-30",
        "hora": "22:00",
        "liga": "La Liga",
        "equipo_local": "Atletico Madrid",
        "equipo_visitante": "Sevilla",
        "pais": "España",
        "stats_local": {
            "partidos_jugados": 38,
            "victorias": 21,
            "empates": 9,
            "derrotas": 8,
            "goles_favor": 62,
            "goles_contra": 35,
            "lambda_local": 1.65,
            "lambda_visitante": 0.95,
            "corners_promedio": 5.2,
            "tarjetas_promedio": 3.1,
            "tiros_promedio": 12.8,
            "forma": ["W", "D", "W", "G", "L"]
        },
        "stats_visitante": {
            "partidos_jugados": 38,
            "victorias": 13,
            "empates": 11,
            "derrotas": 14,
            "goles_favor": 48,
            "goles_contra": 55,
            "lambda_local": 1.10,
            "lambda_visitante": 0.85,
            "corners_promedio": 4.5,
            "tarjetas_promedio": 3.5,
            "tiros_promedio": 10.2,
            "forma": ["L", "D", "L", "W", "D"]
        }
    },
    {
        "id": "demo_004",
        "fecha": "2026-07-31",
        "hora": "21:30",
        "liga": "Brasileirão",
        "equipo_local": "Flamengo",
        "equipo_visitante": "Palmeiras",
        "pais": "Brasil",
        "stats_local": {
            "partidos_jugados": 38,
            "victorias": 22,
            "empates": 8,
            "derrotas": 8,
            "goles_favor": 68,
            "goles_contra": 38,
            "lambda_local": 1.80,
            "lambda_visitante": 1.05,
            "corners_promedio": 6.8,
            "tarjetas_promedio": 2.3,
            "tiros_promedio": 14.5,
            "forma": ["G", "W", "E", "W", "W"]
        },
        "stats_visitante": {
            "partidos_jugados": 38,
            "victorias": 20,
            "empates": 12,
            "derrotas": 6,
            "goles_favor": 64,
            "goles_contra": 32,
            "lambda_local": 1.70,
            "lambda_visitante": 0.95,
            "corners_promedio": 6.2,
            "tarjetas_promedio": 2.0,
            "tiros_promedio": 13.8,
            "forma": ["W", "D", "W", "E", "G"]
        }
    },
    {
        "id": "demo_005",
        "fecha": "2026-08-01",
        "hora": "20:00",
        "liga": "Copa Sudamericana",
        "equipo_local": "Independiente Medellin",
        "equipo_visitante": "LDU Quito",
        "pais": "Colombia",
        "stats_local": {
            "partidos_jugados": 20,
            "victorias": 11,
            "empates": 5,
            "derrotas": 4,
            "goles_favor": 32,
            "goles_contra": 18,
            "lambda_local": 1.55,
            "lambda_visitante": 0.90,
            "corners_promedio": 5.5,
            "tarjetas_promedio": 2.8,
            "tiros_promedio": 11.2,
            "forma": ["W", "W", "D", "L", "W"]
        },
        "stats_visitante": {
            "partidos_jugados": 18,
            "victorias": 9,
            "empates": 6,
            "derrotas": 3,
            "goles_favor": 28,
            "goles_contra": 15,
            "lambda_local": 1.45,
            "lambda_visitante": 0.85,
            "corners_promedio": 5.1,
            "tarjetas_promedio": 2.5,
            "tiros_promedio": 10.8,
            "forma": ["D", "W", "W", "W", "D"]
        }
    },
    {
        "id": "demo_006",
        "fecha": "2026-08-02",
        "hora": "18:30",
        "liga": "Bundesliga",
        "equipo_local": "Borussia Dortmund",
        "equipo_visitante": "RB Leipzig",
        "pais": "Alemania",
        "stats_local": {
            "partidos_jugados": 34,
            "victorias": 18,
            "empates": 8,
            "derrotas": 8,
            "goles_favor": 85,
            "goles_contra": 52,
            "lambda_local": 2.10,
            "lambda_visitante": 1.20,
            "corners_promedio": 7.5,
            "tarjetas_promedio": 2.2,
            "tiros_promedio": 16.8,
            "forma": ["W", "L", "W", "W", "D"]
        },
        "stats_visitante": {
            "partidos_jugados": 34,
            "victorias": 20,
            "empates": 6,
            "derrotas": 8,
            "goles_favor": 72,
            "goles_contra": 40,
            "lambda_local": 1.95,
            "lambda_visitante": 1.10,
            "corners_promedio": 7.0,
            "tarjetas_promedio": 2.0,
            "tiros_promedio": 15.5,
            "forma": ["W", "W", "L", "W", "W"]
        }
    }
]


def get_partidos_demo() -> List[Dict]:
    """Retorna los partidos de demostración."""
    return PARTIDOS_DEMO


def get_partidos_para_fechas(fechas: List[str]) -> List[Dict]:
    """Filtra partidos demo por fechas."""
    partidos = []
    for p in PARTIDOS_DEMO:
        if p["fecha"] in fechas:
            partidos.append(p)
    return partidos


def get_equipos_que_juegan_en_fecha(fecha: str) -> List[str]:
    """Retorna lista de equipos que juegan en una fecha específica."""
    equipos = []
    for p in PARTIDOS_DEMO:
        if p["fecha"] == fecha:
            if p["equipo_local"] not in equipos:
                equipos.append(p["equipo_local"])
            if p["equipo_visitante"] not in equipos:
                equipos.append(p["equipo_visitante"])
    return equipos


def get_stats_equipo(nombre_equipo: str) -> Optional[Dict]:
    """Busca estadísticas de un equipo en los partidos demo."""
    for p in PARTIDOS_DEMO:
        if p["equipo_local"] == nombre_equipo:
            return p["stats_local"]
        if p["equipo_visitante"] == nombre_equipo:
            return p["stats_visitante"]
    return None
