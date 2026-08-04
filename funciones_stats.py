"""
Funciones para obtener y procesar estadísticas de partidos
- Últimos 5 partidos jugados por equipo
- Estadísticas: corners, tiros, tarjetas, posesión
"""

import requests
import time


def obtener_stats_partido(fixture_id, team_id, team_name, headers, API_URL):
    """
    Obtiene las estadísticas de un partido específico para un equipo.
    Retorna diccionario con los datos o None si falla.
    """
    try:
        resp = requests.get(
            f"{API_URL}/fixtures/statistics",
            headers=headers,
            params={'fixture': fixture_id},
            timeout=10
        )
        
        if resp.status_code != 200:
            return None
        
        data = resp.json().get('response', [])
        
        # Buscar las estadísticas del equipo específico
        for team_stats in data:
            if team_stats.get('team', {}).get('id') == team_id:
                stats = team_stats.get('statistics', [])
                
                # Extraer valores
                def get_val(stat_list, stat_type):
                    for s in stat_list:
                        if s.get('type') == stat_type:
                            val = s.get('value')
                            if val is None:
                                return 0
                            if isinstance(val, str):
                                val = val.replace('%', '')
                            try:
                                return int(float(val))
                            except:
                                return 0
                    return 0
                
                return {
                    'tiros_totales': get_val(stats, 'Total Shots'),
                    'tiros_arco': get_val(stats, 'Shots on Goal'),
                    'tiros_fuera': get_val(stats, 'Shots off Goal'),
                    'corners': get_val(stats, 'Corner Kicks'),
                    'amarillas': get_val(stats, 'Yellow Cards'),
                    'rojas': get_val(stats, 'Red Cards'),
                    'posesion': get_val(stats, 'Ball Possession'),
                    'faltas': get_val(stats, 'Fouls'),
                    'ahorradas': get_val(stats, 'Goalkeeper Saves'),
                }
        
        return None
    
    except Exception as e:
        return None


def obtener_ultimos_partidos_equipo(team_id, team_name, league_id, season, headers, API_URL, max_partidos=50):
    """
    Obtiene los últimos N partidos jugados de un equipo con sus estadísticas.
    """
    partidos_stats = []
    
    try:
        # Obtener fixtures terminados
        resp = requests.get(
            f"{API_URL}/fixtures",
            headers=headers,
            params={
                'team': team_id,
                'season': season,
                'status': 'FT',
                'from': f'{season}-01-01',
                'to': f'{season+1}-12-31'
            },
            timeout=15
        )
        
        if resp.status_code != 200:
            return []
        
        fixtures = resp.json().get('response', [])
        
        if not fixtures:
            return []
        
        # Tomar solo los últimos N partidos
        fixtures = fixtures[:max_partidos]
        
        for f in fixtures:
            fix = f.get('fixture', {})
            teams = f.get('teams', {})
            league = f.get('league', {})
            
            fix_id = fix.get('id')
            fecha = fix.get('date', '')[:10]
            
            # Determinar si es local o visitante
            home_team = teams.get('home', {})
            away_team = teams.get('away', {})
            
            goals = teams.get('goals', {})
            gf_home = goals.get('home') or 0
            gf_away = goals.get('away') or 0

            if home_team.get('id') == team_id:
                es_local = True
                resultado_str = home_team.get('winner') or False
                gf = gf_home
                gv = gf_away
            else:
                es_local = False
                resultado_str = away_team.get('winner') or False
                gf = gf_away
                gv = gf_home
            
            # Determinar resultado W/D/L
            if resultado_str == True:
                resultado = 'W'
            elif resultado_str == False and (gf != gv):
                resultado = 'L'
            else:
                resultado = 'D'
            
            # Obtener estadísticas del partido
            stats = obtener_stats_partido(fix_id, team_id, team_name, headers, API_URL)
            
            if stats:
                partido_data = {
                    'fixture_id': fix_id,
                    'fecha': fecha,
                    'liga': league.get('name', ''),
                    'es_local': es_local,
                    'resultado': resultado,
                    'goles_favor': gf,
                    'goles_contra': gv,
                    **stats
                }
                partidos_stats.append(partido_data)
            
            # Rate limit suave
            time.sleep(0.2)
        
        return partidos_stats
    
    except Exception as e:
        return []


def guardar_stats_equipo(client, team_id, equipo, partidos_stats):
    """
    Guarda las estadísticas de partidos de un equipo en Supabase.
    ★ NO borra partidos - acumula TODOS los partidos históricos.
    La función calcular_promedios_equipo se encarga de ponderar.
    
    Returns:
        tuple: (success: bool, message: str, count: int)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not partidos_stats:
        return True, "Sin partidos para guardar", 0
    
    try:
        partidos_guardados = 0
        errores = []
        primer_error = None
        
        # Guardar cada partido (upsert no duplica gracias a UNIQUE constraint)
        for ps in partidos_stats:
            try:
                data = {
                    'team_id': int(team_id) if team_id else 0,
                    'equipo': str(equipo) if equipo else '',
                    'fixture_id': int(ps['fixture_id']) if ps.get('fixture_id') else 0,
                    'fecha': str(ps['fecha']) if ps.get('fecha') else None,
                    'liga': str(ps['liga']) if ps.get('liga') else '',
                    'es_local': bool(ps['es_local']) if ps.get('es_local') is not None else False,
                    'resultado': str(ps['resultado']) if ps.get('resultado') else '-',
                    'goles_favor': int(ps.get('goles_favor', 0)) if ps.get('goles_favor') is not None else 0,
                    'goles_contra': int(ps.get('goles_contra', 0)) if ps.get('goles_contra') is not None else 0,
                    'tiros_totales': int(ps.get('tiros_totales', 0)) if ps.get('tiros_totales') is not None else 0,
                    'tiros_arco': int(ps.get('tiros_arco', 0)) if ps.get('tiros_arco') is not None else 0,
                    'tiros_fuera': int(ps.get('tiros_fuera', 0)) if ps.get('tiros_fuera') is not None else 0,
                    'corners': int(ps.get('corners', 0)) if ps.get('corners') is not None else 0,
                    'amarillas': int(ps.get('amarillas', 0)) if ps.get('amarillas') is not None else 0,
                    'rojas': int(ps.get('rojas', 0)) if ps.get('rojas') is not None else 0,
                    'posesion': int(ps.get('posesion', 0)) if ps.get('posesion') is not None else 0,
                    'faltas': int(ps.get('faltas', 0)) if ps.get('faltas') is not None else 0,
                }
                
                # ★ Usar upsert con constraint única - no duplica, solo actualiza si existe
                # La constraint se llama 'equipo_partidos_stats_unique'
                result = client.table('equipo_partidos_stats').upsert(
                    data, 
                    on_conflict='equipo_partidos_stats_unique'
                ).execute()
                
                partidos_guardados += 1
                
            except Exception as e:
                error_msg = str(e)
                # Registrar error individual pero continuar con otros partidos
                if primer_error is None:
                    primer_error = error_msg
                errores.append(f"fixture {ps.get('fixture_id', '?')}: {error_msg[:100]}")
                logger.warning(f"Error al guardar partido {ps.get('fixture_id')} para {equipo}: {e}")
                continue
        
        # ★ NO BORRAMOS NADA - Acumulamos todos los partidos
        if errores:
            logger.warning(f"{equipo}: {len(errores)} errores, {partidos_guardados} guardados. Primer error: {primer_error}")
            return True, f"{len(errores)} errores. Detalle: {primer_error[:80] if primer_error else 'Unknown'}", partidos_guardados
        
        return True, "OK", partidos_guardados
    
    except Exception as e:
        logger.error(f"Error grave en guardar_stats_equipo({equipo}): {e}")
        return False, str(e)[:100], 0


def calcular_promedios_equipo(client, team_id, max_partidos=None):
    """
    Calcula promedios PONDERADOS de TODOS los partidos de un equipo.
    
    ★ USA TODOS LOS PARTIDOS DISPONIBLES
    ★ Aplica decaimiento exponencial: partidos más recientes pesan más
    ★ max_partidos limita a los N más recientes (None = todos)
    
    La ponderación exponencial: peso = decay^(posicion)
    donde posición 0 = más reciente (peso = 1.0)
          posición 1 = siguiente (peso = decay)
          ...
    """
    import math
    
    try:
        # Obtener TODOS los partidos del equipo (sin límite)
        query = client.table('equipo_partidos_stats').select('*').eq('team_id', team_id).order('fecha', desc=True)
        
        if max_partidos:
            query = query.limit(max_partidos)
        
        resp = query.execute()
        
        if not resp.data:
            return None
        
        partidos = resp.data
        n = len(partidos)
        
        if n == 0:
            return None
        
        # Factor de decaimiento: partidos recientes pesan más
        # decay = 0.9 significa que el partido N pesa 0.9^N vs el más reciente
        # Ajustable: decay más bajo = más peso a lo reciente
        decay = 0.92  # ~50% de peso al último tercio
        
        def weighted_avg(values, decay=0.92):
            """Calcula promedio ponderado exponencialmente."""
            if not values:
                return 0
            
            n = len(values)
            weights = [math.pow(decay, i) for i in range(n)]  # weights[0]=1.0 para más reciente
            total_weight = sum(weights)
            
            if total_weight == 0:
                return 0
            
            weighted_sum = sum(v * w for v, w in zip(values, weights))
            return weighted_sum / total_weight
        
        # Calcular promedios ponderados
        corners_vals = [p.get('corners', 0) for p in partidos]
        tiros_vals = [p.get('tiros_totales', 0) for p in partidos]
        tiros_arco_vals = [p.get('tiros_arco', 0) for p in partidos]
        amarillas_vals = [p.get('amarillas', 0) for p in partidos]
        rojas_vals = [p.get('rojas', 0) for p in partidos]
        posesion_vals = [p.get('posesion', 0) for p in partidos]
        faltas_vals = [p.get('faltas', 0) for p in partidos]
        
        # También calcular lambda con ponderación
        gf_vals = [p.get('goles_favor', 0) for p in partidos]
        gc_vals = [p.get('goles_contra', 0) for p in partidos]
        
        lambda_goles = weighted_avg([gf + gc for gf, gc in zip(gf_vals, gc_vals)], decay)
        
        # Forma: últimos 5 partidos (para display)
        forma = ''.join(p.get('resultado', '-') for p in reversed(partidos[:5]))
        
        # Promedios de goles
        promedio_gf = round(weighted_avg(gf_vals), 2) if gf_vals else 0
        promedio_gc = round(weighted_avg(gc_vals), 2) if gc_vals else 0
        
        return {
            'partidos_total': n,  # Total de partidos acumulados
            'partidos_usados': n,  # Partidos usados en el cálculo
            'promedio_goles_favor': promedio_gf,
            'promedio_goles_contra': promedio_gc,
            'promedio_corners': round(weighted_avg(corners_vals), 1),
            'promedio_tiros': round(weighted_avg(tiros_vals), 1),
            'promedio_tiros_arco': round(weighted_avg(tiros_arco_vals), 1),
            'promedio_amarillas': round(weighted_avg(amarillas_vals), 1),
            'promedio_rojas': round(weighted_avg(rojas_vals), 1),
            'promedio_posesion': round(weighted_avg(posesion_vals), 1),
            'promedio_faltas': round(weighted_avg(faltas_vals), 1),
            # Lambda dinámico (ponderado)
            'lambda_ponderado': round(lambda_goles, 2),
            # Forma recent
            'forma': forma,
            # Datos de partidos para análisis
            'partidos': partidos[:5],  # Últimos 5 para display
        }
    
    except Exception as e:
        return None
