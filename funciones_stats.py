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
            
            if home_team.get('id') == team_id:
                es_local = True
                resultado_str = home_team.get('winner') or False
                gf = home_team.get('goals') or 0
                gv = away_team.get('goals') or 0
            else:
                es_local = False
                resultado_str = away_team.get('winner') or False
                gf = away_team.get('goals') or 0
                gv = home_team.get('goals') or 0
            
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
    Guarda las estadísticas de partidos de un equipo.
    ★ NO borra partidos - acumula TODOS los partidos históricos.
    La función calcular_promedios_equipo se encarga de ponderar.
    """
    try:
        partidos_guardados = 0
        
        # Guardar cada partido (upsert no duplica)
        for ps in partidos_stats:
            data = {
                'team_id': team_id,
                'equipo': equipo,
                'fixture_id': ps['fixture_id'],
                'fecha': ps['fecha'],
                'liga': ps['liga'],
                'es_local': ps['es_local'],
                'resultado': ps['resultado'],
                'goles_favor': ps.get('goles_favor', 0),
                'goles_contra': ps.get('goles_contra', 0),
                'tiros_totales': ps.get('tiros_totales', 0),
                'tiros_arco': ps.get('tiros_arco', 0),
                'tiros_fuera': ps.get('tiros_fuera', 0),
                'corners': ps.get('corners', 0),
                'amarillas': ps.get('amarillas', 0),
                'rojas': ps.get('rojas', 0),
                'posesion': ps.get('posesion', 0),
                'faltas': ps.get('faltas', 0),
                'ahorradas': ps.get('ahorradas', 0),
            }
            
            client.table('equipo_partidos_stats').upsert(data, on_conflict='team_id,fixture_id').execute()
            partidos_guardados += 1
        
        # ★ NO BORRAMOS NADA - Acumulamos todos los partidos
        return True
    
    except Exception as e:
        return False


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
