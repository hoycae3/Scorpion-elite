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


# ═══════════════════════════════════════════════════════════════════════════════
# SCRAPER DE FLASHSCORE (FALLBACK PARA CUANDO API-FOOTBALL NO FUNCIONA)
# ═══════════════════════════════════════════════════════════════════════════════

# URLs de Flashscore para las 5 ligas
FLASHSCORE_LIGAS = {
    "Champions League": "https://www.flashscore.com/football/europe/champions-league/",
    "Copa Sudamericana": "https://www.flashscore.com/football/south-america/copa-sudamericana/",
    "La Liga": "https://www.flashscore.com/football/spain/laliga/",
    "Bundesliga": "https://www.flashscore.com/football/germany/bundesliga/",
    "Brasileirão": "https://www.flashscore.com/football/brazil/serie-a/",
}


def scrape_flashscore_partidos(fecha: str = None) -> List[Dict]:
    """
    Scraper de Flashscore para obtener partidos de las 5 ligas configuradas.
    
    Args:
        fecha: Fecha en formato YYYY-MM-DD. Si es None, usa la fecha de hoy.
    
    Returns:
        Lista de partidos con estructura:
        {
            'fixture_id': str (generado),
            'fecha': str,
            'hora': str,
            'liga': str,
            'liga_id': int,
            'equipo_local': str,
            'equipo_local_id': None,
            'equipo_visitante': str,
            'equipo_visitante_id': None,
            'source': 'flashscore'
        }
    """
    try:
        import cloudscraper
        import re
    except ImportError as e:
        logger.warning(f"No se pudo importar cloudscraper: {e}")
        return []
    
    if fecha is None:
        fecha = date.today().strftime('%Y-%m-%d')
    
    # Mapear IDs de liga (para API-Football compatibility)
    LIGA_IDS = {
        "Champions League": 2,
        "Copa Sudamericana": 87,
        "La Liga": 71,
        "Bundesliga": 78,
        "Brasileirão": 24,
    }
    
    partidos = []
    
    # Crear scraper
    try:
        scraper = cloudscraper.CloudScraper()
    except:
        scraper = cloudscraper.create_scraper()
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    
    for liga_name, url in FLASHSCORE_LIGAS.items():
        try:
            response = scraper.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"Flashscore {liga_name}: status {response.status_code}")
                continue
            
            html_content = response.text
            
            # Patrones para encontrar partidos en Flashscore
            # Flashscore usa clases como event__match, event__homeParticipant, etc.
            
            # Buscar todos los bloques de partidos
            event_blocks = re.findall(
                r'<div[^>]*class="event__match[^"]*"[^>]*>(.*?)</div>',
                html_content, re.DOTALL
            )
            
            if not event_blocks:
                # Intentar otro patrón
                event_blocks = re.findall(
                    r'<div[^>]*data-id="(\d+)"[^>]*>.*?<span[^>]*class="event__homeParticipant[^"]*"[^>]*>([^<]+)</span>.*?<span[^>]*class="event__awayParticipant[^"]*"[^>]*>([^<]+)</span>',
                    html_content, re.DOTALL
                )
            
            count = 0
            for block in event_blocks:
                if isinstance(block, tuple):
                    match_id, home, away = block
                else:
                    # Extraer datos del bloque
                    match_id_match = re.search(r'data-id="(\d+)"', block)
                    home_match = re.search(r'class="event__homeParticipant[^"]*"[^>]*>([^<]+)</span>', block)
                    away_match = re.search(r'class="event__awayParticipant[^"]*"[^>]*>([^<]+)</span>', block)
                    time_match = re.search(r'class="event__time[^"]*"[^>]*>([^<]+)</span>', block)
                    
                    if not (home_match and away_match):
                        continue
                    
                    match_id = match_id_match.group(1) if match_id_match else str(count)
                    home = home_match.group(1).strip()
                    away = away_match.group(1).strip()
                    hora = time_match.group(1).strip() if time_match else "00:00"
                    
                    if home and away and len(home) > 1 and len(away) > 1:
                        fixture_id = f"fs_{match_id}"
                        
                        partido = {
                            'fixture_id': fixture_id,
                            'fecha': fecha,
                            'hora': hora,
                            'liga': liga_name,
                            'liga_id': LIGA_IDS.get(liga_name, 0),
                            'equipo_local': home,
                            'equipo_local_id': None,
                            'equipo_visitante': away,
                            'equipo_visitante_id': None,
                            'source': 'flashscore'
                        }
                        partidos.append(partido)
                        logger.info(f"✅ {liga_name}: {home} vs {away}")
                        count += 1
            
            if count > 0:
                logger.info(f"Flashscore {liga_name}: {count} partidos encontrados")
            
        except Exception as e:
            logger.error(f"Error scraping {liga_name}: {e}")
            continue
    
    return partidos


def get_partidos_from_flashscore(fecha: str = None) -> List[Dict]:
    """Wrapper para obtener partidos de Flashscore."""
    return scrape_flashscore_partidos(fecha)
