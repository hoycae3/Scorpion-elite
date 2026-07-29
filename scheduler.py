"""
Scorpion Elite - Scheduler
==========================
Script que se ejecuta automáticamente para:
1. Consultar partidos de los próximos 7 días
2. Guardar en Supabase
3. Consultar estadísticas de equipos que juegan en 2-3 días
4. Guardar en Supabase

Se ejecuta via CRON JOB a las 00:00 todos los días
"""

import os
import sys
from datetime import date, timedelta
from supabase import create_client
import requests
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://jjtifureeygvygxtpuku.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA')
API_FOOTBALL_KEY = "e3926f829cd848f4b2b54d722ca29701"

# Todas las ligas que sigue el usuario
LIGAS_SELECCIONADAS = [
    {"id": 2, "name": "UEFA Champions League"},
    {"id": 87, "name": "Copa Sudamericana"},
    {"id": 71, "name": "La Liga"},
    {"id": 71, "name": "Serie A"},  # Italia
    {"id": 78, "name": "Bundesliga"},  # Alemania
    {"id": 24, "name": "Brasileirão"},  # Brasil
]


def get_supabase_client():
    """Obtiene cliente de Supabase."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_partidos_from_api(league_id: int, fecha: str) -> list:
    """
    Consulta partidos de una liga para una fecha específica.
    """
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {
        'league': league_id,
        'season': 2024,
        'date': fecha,
        'status': 'NS'  # Not Started
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', [])
        else:
            logger.warning(f"Error API: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Error consultando partidos: {e}")
        return []


def get_stats_from_api(team_id: int) -> dict:
    """
    Consulta estadísticas de un equipo.
    """
    url = "https://v3.football.api-sports.io/teams/statistics"
    headers = {'x-apisports-key': API_FOOTBALL_KEY}
    params = {
        'team': team_id,
        'season': 2024,
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return data.get('response', {})
        else:
            return {}
    except Exception as e:
        logger.error(f"Error consultando stats: {e}")
        return {}


def guardar_partidos_en_supabase(partidos: list, client):
    """
    Guarda partidos en Supabase.
    """
    guardados = 0
    for match in partidos:
        try:
            fixture = match.get('fixture', {})
            teams = match.get('teams', {})
            league = match.get('league', {})
            
            data = {
                'fixture_id': fixture.get('id'),
                'fecha': fixture.get('date', '')[:10],  # Solo fecha
                'hora': fixture.get('date', '')[11:16],  # Solo hora
                'liga': league.get('name', ''),
                'liga_id': league.get('id'),
                'equipo_local': teams.get('home', {}).get('name', ''),
                'equipo_local_id': teams.get('home', {}).get('id'),
                'equipo_visitante': teams.get('away', {}).get('name', ''),
                'equipo_visitante_id': teams.get('away', {}).get('id'),
                'ultima_actualizacion': str(date.today())
            }
            
            client.table('partidos').upsert(data, on_conflict='fixture_id').execute()
            guardados += 1
            
        except Exception as e:
            logger.error(f"Error guardando partido: {e}")
    
    return guardados


def guardar_stats_equipo_en_supabase(team_id: int, team_name: str, league: str, client):
    """
    Guarda estadísticas de un equipo en Supabase.
    """
    stats = get_stats_from_api(team_id)
    if not stats:
        return False
    
    # Extraer datos relevantes
    lineups = stats.get('lineups', [])
    estadisticas = stats.get('statistics', [])
    
    # Calcular lambdas
    partidos = stats.get('fixtures', {}).get('played', {}).get('total', 0) or 1
    goles_favor = stats.get('goals', {}).get('for', {}).get('total', {}).get('total', 0) or 0
    goles_contra = stats.get('goals', {}).get('against', {}).get('total', {}).get('total', 0) or 0
    
    lambda_local = round((goles_favor / partidos) * 1.15, 2)
    lambda_visitante = round((goles_favor / partidos) * 0.85, 2)
    
    # Buscar stats específicas
    corners_total = 0
    tarjetas_total = 0
    tiros_total = 0
    
    for stat in estadisticas:
        if stat.get('type') == 'Corners':
            corners_total = int(stat.get('value', 0) or 0)
        elif stat.get('type') == 'Yellow Cards':
            tarjetas_total = int(stat.get('value', 0) or 0)
        elif stat.get('type') == 'Shots':
            tiros_total = int(stat.get('value', 0) or 0)
    
    data = {
        'equipo': team_name,
        'liga': league,
        'temporada': '2024',
        'partidos_jugados': partidos,
        'goles_favor': goles_favor,
        'goles_contra': goles_contra,
        'lambda_local': lambda_local,
        'lambda_visitante': lambda_visitante,
        'promedio_corners_total': round(corners_total / max(partidos, 1), 1),
        'promedio_tarjetas': round(tarjetas_total / max(partidos, 1), 1),
        'promedio_tiros': round(tiros_total / max(partidos, 1), 1),
        'ultima_actualizacion': str(date.today())
    }
    
    try:
        client.table('equipos_stats').upsert(data, on_conflict='equipo').execute()
        return True
    except Exception as e:
        logger.error(f"Error guardando stats de {team_name}: {e}")
        return False


def run_scheduler():
    """
    Función principal que se ejecuta via cron.
    """
    logger.info("="*60)
    logger.info("🦂 INICIANDO SCHEDULER - Partidos Scorpion Elite")
    logger.info(f"📅 Fecha: {date.today()}")
    logger.info("="*60)
    
    # Conectar a Supabase
    client = get_supabase_client()
    
    # ═══════════════════════════════════════════════════════════
    # PASO 1: Consultar partidos de los próximos 7 días
    # ═══════════════════════════════════════════════════════════
    logger.info("\n📅 PASO 1: Consultando partidos de los próximos 7 días...")
    
    hoy = date.today()
    fechas = [(hoy + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)]
    
    total_partidos = 0
    total_requests = 0
    
    for liga in LIGAS_SELECCIONADAS:
        liga_id = liga['id']
        liga_nombre = liga['name']
        
        # Verificar si YA tenemos partidos para esta fecha (en Supabase)
        # Si ya existen, no consultar
        
        for fecha in fechas:
            # Consultar API
            logger.info(f"  📡 {liga_nombre} - {fecha}")
            partidos = get_partidos_from_api(liga_id, fecha)
            total_requests += 1
            
            if partidos:
                guardados = guardar_partidos_en_supabase(partidos, client)
                total_partidos += guardados
                logger.info(f"    ✅ {guardados} partidos guardados")
            
            # Delay para evitar rate limit
            import time
            time.sleep(1)
    
    logger.info(f"\n📊 Resumen partidos: {total_partidos} guardados, {total_requests} requests usados")
    
    # ═══════════════════════════════════════════════════════════
    # PASO 2: Consultar estadísticas de equipos que juegan en 2-3 días
    # ═══════════════════════════════════════════════════════════
    logger.info("\n📊 PASO 2: Consultando estadísticas de equipos próximos...")
    
    # Obtener partidos de mañana y pasado mañana
    manana = (hoy + timedelta(days=1)).strftime('%Y-%m-%d')
    pasado_manana = (hoy + timedelta(days=2)).strftime('%Y-%m-%d')
    
    # Obtener partidos de Supabase
    try:
        response = client.table('partidos').select('*').gte('fecha', manana).lte('fecha', pasado_manana).execute()
        proximos_partidos = response.data
    except Exception as e:
        logger.error(f"Error obteniendo partidos: {e}")
        proximos_partidos = []
    
    # Extraer equipos únicos
    equipos = set()
    for p in proximos_partidos:
        if p.get('equipo_local_id'):
            equipos.add((p['equipo_local_id'], p['equipo_local'], p['liga']))
        if p.get('equipo_visitante_id'):
            equipos.add((p['equipo_visitante_id'], p['equipo_visitante'], p['liga']))
    
    logger.info(f"  📊 {len(equipos)} equipos a consultar...")
    
    stats_guardadas = 0
    for team_id, team_name, league in equipos:
        logger.info(f"  📡 {team_name}...")
        if guardar_stats_equipo_en_supabase(team_id, team_name, league, client):
            stats_guardadas += 1
            total_requests += 1
        
        # Delay para evitar rate limit
        import time
        time.sleep(1)
    
    # ═══════════════════════════════════════════════════════════
    # RESUMEN FINAL
    # ═══════════════════════════════════════════════════════════
    logger.info("\n" + "="*60)
    logger.info("✅ SCHEDULER COMPLETADO")
    logger.info(f"📊 Requests usados hoy: {total_requests}")
    logger.info(f"📅 Partidos guardados: {total_partidos}")
    logger.info(f"📊 Stats guardadas: {stats_guardadas}")
    logger.info("="*60)
    
    return {
        'requests': total_requests,
        'partidos': total_partidos,
        'stats': stats_guardadas
    }


if __name__ == "__main__":
    # Ejecutar scheduler
    result = run_scheduler()
    
    # Exit code 0 = éxito
    sys.exit(0)
