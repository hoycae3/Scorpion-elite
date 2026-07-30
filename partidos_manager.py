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
# PARTIDOS VACÍOS (PRODUCCIÓN)
# ═══════════════════════════════════════════════════════════════════════════════

PARTIDOS_DEMO = []


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
