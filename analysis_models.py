"""
Scorpion Elite - Modelos de Análisis Matemático
==============================================
5 modelos combinados para predecir resultados de fútbol:
- Poisson (30%): Distribución de probabilidad para goles
- Dixon-Coles (25%): Corrige dependencia entre goles marcados/recibidos
- Monte Carlo (20%): Simulación de 3000 partidos
- Forma Reciente (15%): Análisis de últimos 5 partidos
- Estilo de Juego (10%): Corners, tarjetas, tiros

DATOS ADICIONALES:
- corners_promedio: Promedio de córners por partido
- tarjetas_promedio: Promedio de tarjetas por partido
- tiros_promedio: Promedio de tiros por partido
- tiros_arco_promedio: Promedio de tiros al arco por partido
- ultimos_5_partidos: Lista de últimos 5 partidos con resultados
"""

import random
from typing import Dict, List, Optional


def pp(lmbda: float, k: int) -> float:
    """Función de masa de probabilidad de Poisson P(X=k)"""
    if lmbda <= 0 or k < 0:
        return 0.0
    # Usar factorial para mayor precisión
    import math
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)


def poisson_1x2(xl: float, xv: float) -> tuple:
    """Modelo Poisson básico para 1X2"""
    p1 = px = p2 = 0.0
    # Aumentar rango para cubrir más casos
    for i in range(15):
        for j in range(15):
            p = pp(xl, i) * pp(xv, j)
            if i > j:
                p1 += p
            elif i == j:
                px += p
            else:
                p2 += p
    return round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1)


def poisson_over_under(xl: float, xv: float) -> Dict:
    """Modelo Poisson para Over/Under"""
    over_15 = over_25 = over_35 = 0.0
    under_15 = under_25 = under_35 = 0.0
    
    for i in range(15):
        for j in range(15):
            p = pp(xl, i) * pp(xv, j)
            total = i + j
            
            if total > 1.5:
                over_15 += p
            else:
                under_15 += p
                
            if total > 2.5:
                over_25 += p
            else:
                under_25 += p
                
            if total > 3.5:
                over_35 += p
            else:
                under_35 += p
    
    return {
        "over_15": round(over_15 * 100, 1),
        "under_15": round(under_15 * 100, 1),
        "over_25": round(over_25 * 100, 1),
        "under_25": round(under_25 * 100, 1),
        "over_35": round(over_35 * 100, 1),
        "under_35": round(under_35 * 100, 1),
    }


def dc_1x2(xl: float, xv: float, rho: float = -0.1) -> tuple:
    """Modelo Dixon-Coles"""
    m = {}
    for i in range(9):
        for j in range(9):
            tau = 1 - rho * (i + j) / 16 if i > 1 or j > 1 else (1 + rho if i == 0 and j == 0 else 1)
            p = pp(xl, i) * pp(xv, j) * tau
            m[(i, j)] = max(0, p)
    
    total = sum(m.values())
    if total > 0:
        m = {k: v / total for k, v in m.items()}
    
    p1 = sum(v for (i, j), v in m.items() if i > j)
    px = sum(v for (i, j), v in m.items() if i == j)
    p2 = sum(v for (i, j), v in m.items() if i < j)
    
    return round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1)


def monte_carlo(xl: float, xv: float, n: int = 3000) -> Dict:
    """Simulación Monte Carlo"""
    v1 = vx = v2 = 0
    goals_total = []
    score_map = {}
    
    random.seed(42)
    
    for _ in range(n):
        gl = gv = 0
        u = random.random()
        for k in range(15):
            if u <= pp(xl, k):
                gl = k
                break
        
        u = random.random()
        for k in range(15):
            if u <= pp(xv, k):
                gv = k
                break
        
        if gl > gv:
            v1 += 1
        elif gl == gv:
            vx += 1
        else:
            v2 += 1
        
        goals_total.append(gl + gv)
        score_key = f"{gl}-{gv}"
        score_map[score_key] = score_map.get(score_key, 0) + 1
    
    top_scores = dict(sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:6])
    top_scores = {k: round(v / n * 100, 1) for k, v in top_scores.items()}
    
    return {
        "p1": round(v1 / n * 100, 1),
        "px": round(vx / n * 100, 1),
        "p2": round(v2 / n * 100, 1),
        "avg_goals": round(sum(goals_total) / n, 2),
        "over_25": round(sum(1 for g in goals_total if g > 2) / n * 100, 1),
        "under_25": round(sum(1 for g in goals_total if g <= 2) / n * 100, 1),
        "top_scores": top_scores
    }


def analizar_forma_reciente(ultimos_5: List[Dict]) -> Dict:
    """
    Analiza la forma reciente del equipo basándose en los últimos 5 partidos.
    """
    if not ultimos_5:
        return {
            "forma_puntos": 0,
            "forma_letras": "-----",
            "victorias": 0,
            "empates": 0,
            "derrotas": 0,
            "goles_favor_5": 0,
            "goles_contra_5": 0,
            "corners_promedio_5": 0,
        }
    
    puntos = 0
    victorias = 0
    empates = 0
    derrotas = 0
    gf = 0
    gc = 0
    corners_total = 0
    forma_letras = []
    
    for match in ultimos_5[:5]:  # Solo últimos 5
        resultado = match.get('resultado', 'P')
        forma_letras.append(resultado)
        
        gf += match.get('goles_favor', 0)
        gc += match.get('goles_contra', 0)
        corners_total += match.get('corners', 0)
        
        if resultado == 'G':  # Ganó
            puntos += 3
            victorias += 1
        elif resultado == 'E':  # Empate
            puntos += 1
            empates += 1
        else:  # P (Perdió)
            derrotas += 1
    
    # Forma como porcentaje (máximo 15 puntos en 5 partidos)
    forma_puntos = round(puntos / 15 * 100, 1) if ultimos_5 else 0
    
    return {
        "forma_puntos": forma_puntos,
        "forma_letras": ''.join(forma_letras[:5]) if forma_letras else "-----",
        "victorias": victorias,
        "empates": empates,
        "derrotas": derrotas,
        "goles_favor_5": gf,
        "goles_contra_5": gc,
        "corners_promedio_5": round(corners_total / len(ultimos_5[:5]), 1) if ultimos_5 else 0,
    }


def analizar_estilo_juego(
    corners: float,
    tarjetas: float,
    tiros: float,
    tiros_arco: float
) -> Dict:
    """
    Analiza el estilo de juego del equipo.
    """
    # Clasificar según promedios típicos
    # Promedios típicos: corners=10, tarjetas=3.5, tiros=12, tiros_arco=4
    
    estilo_ofensivo = 50  # Base neutra
    estilo_defensivo = 50
    estilo_physical = 50
    
    # Corner tendency (>10 = ofensivo, <10 = defensivo)
    if corners > 12:
        estilo_ofensivo += 15
        estilo_defensivo -= 10
    elif corners < 8:
        estilo_ofensivo -= 10
        estilo_defensivo += 15
    
    # Tarjetas (>4 = physical, <2 = limpio)
    if tarjetas > 4:
        estilo_physical += 20
    elif tarjetas < 2:
        estilo_physical -= 15
    
    # Tiros al arco (>5 = dominante, <3 = dependent)
    if tiros_arco > 5:
        estilo_ofensivo += 10
    elif tiros_arco < 3:
        estilo_ofensivo -= 10
    
    return {
        "estilo_ofensivo": max(0, min(100, estilo_ofensivo)),
        "estilo_defensivo": max(0, min(100, estilo_defensivo)),
        "estilo_physical": max(0, min(100, estilo_physical)),
        "tipo": "Ofensivo" if estilo_ofensivo > 65 else ("Defensivo" if estilo_defensivo > 65 else "Equilibrado")
    }


def predecir_corners(
    corners_local: float,
    corners_visitante: float,
    estilo_local: Dict,
    estilo_visitante: Dict
) -> Dict:
    """
    Predice el total de córners en el partido.
    
    corners_local: córners que genera el equipo local POR PARTIDO
    corners_visitante: córners que genera el equipo visitante POR PARTIDO
    """
    # Los córners totales son la SUMA de ambos
    # Si Local genera 5/partido y Visitante genera 6/partido
    # El partido tendrá ~11 córners totales
    total_estimado = corners_local + corners_visitante
    
    # Desglose: Local genera más como local (ventaja de campo)
    # Visitante genera un poco menos fuera de casa
    factor_local = 1.05  # 5% más córners como local
    factor_visitante = 0.95  # 5% menos córners como visitante
    
    corners_local_estimado = total_estimado * factor_local / (factor_local + factor_visitante)
    corners_visitante_estimado = total_estimado - corners_local_estimado
    
    # Over/Under - ajustar umbrales
    # Umbral de 10.5 es típico para córners totales
    if total_estimado > 11:
        over_105 = 70
        under_105 = 30
    elif total_estimado > 10.5:
        over_105 = 55
        under_105 = 45
    elif total_estimado > 9.5:
        over_105 = 40
        under_105 = 60
    else:
        over_105 = 25
        under_105 = 75
    
    return {
        "total_estimado": round(total_estimado, 1),
        "corners_local_estimado": round(corners_local_estimado, 1),
        "corners_visitante_estimado": round(corners_visitante_estimado, 1),
        "over_105": over_105,
        "under_105": under_105,
        "over_95": min(90, max(10, 50 + (total_estimado - 9.5) * 15)),
        "under_95": min(90, max(10, 50 - (total_estimado - 9.5) * 15)),
    }


def calcular(
    lambda_local: float,
    lambda_visitante: float,
    # Nuevos datos
    corners_local: float = 10.0,
    corners_visitante: float = 10.0,
    tarjetas_local: float = 3.5,
    tarjetas_visitante: float = 3.5,
    tiros_local: float = 12.0,
    tiros_visitante: float = 12.0,
    tiros_arco_local: float = 4.0,
    tiros_arco_visitante: float = 4.0,
    ultimos_5_local: List[Dict] = None,
    ultimos_5_visitante: List[Dict] = None,
) -> Dict:
    """
    Calcula probabilidades usando los 5 modelos combinados.
    
    Incluye:
    - 1X2 (Victoria Local / Empate / Victoria Visitante)
    - Over/Under 1.5, 2.5, 3.5
    - Ambos marcan (BTTS)
    - Córners Over/Under
    - Análisis de forma reciente
    - Estilo de juego
    """
    xl = max(0.15, lambda_local)
    xv = max(0.10, lambda_visitante)
    
    # Datos por defecto
    ultimos_5_local = ultimos_5_local or []
    ultimos_5_visitante = ultimos_5_visitante or []
    
    # MODELOS DE GOLES
    p1_po, px_po, p2_po = poisson_1x2(xl, xv)
    p1_dc, px_dc, p2_dc = dc_1x2(xl, xv)
    
    mc = monte_carlo(xl, xv)
    p1_mc, px_mc, p2_mc = mc["p1"], mc["px"], mc["p2"]
    
    # Combinar modelos de goles
    p1 = round(p1_po * 0.30 + p1_dc * 0.25 + p1_mc * 0.20, 1)
    px = round(px_po * 0.30 + px_dc * 0.25 + px_mc * 0.20, 1)
    p2 = round(max(0, 100 - p1 - px), 1)
    
    # OVER/UNDER
    ou = poisson_over_under(xl, xv)
    
    # AMBOS MARCAN (BTTS)
    # Probabilidad de que ambos marquen ≈ P(gl>0) * P(gv>0)
    p_btts_yes = round((1 - pp(xl, 0)) * (1 - pp(xv, 0)) * 100, 1)
    p_btts_no = round(100 - p_btts_yes, 1)
    
    # ANÁLISIS DE FORMA RECIENTE
    forma_local = analizar_forma_reciente(ultimos_5_local)
    forma_visitante = analizar_forma_reciente(ultimos_5_visitante)
    
    # Ajustar probabilidades basándose en forma reciente
    ajuste_forma = (forma_local['forma_puntos'] - forma_visitante['forma_puntos']) / 100 * 5
    p1_ajustado = max(0, min(100, p1 + ajuste_forma))
    p2_ajustado = max(0, min(100, p2 - ajuste_forma))
    px_ajustado = max(0, min(100, 100 - p1_ajustado - p2_ajustado))
    
    # ESTILO DE JUEGO
    estilo_local = analizar_estilo_juego(corners_local, tarjetas_local, tiros_local, tiros_arco_local)
    estilo_visitante = analizar_estilo_juego(corners_visitante, tarjetas_visitante, tiros_visitante, tiros_arco_visitante)
    
    # PREDICCIÓN DE CORNERS
    prediccion_corners = predecir_corners(
        corners_local, corners_visitante,
        estilo_local, estilo_visitante
    )
    
    # CONFIANZA - basada en acuerdo entre modelos
    conf = round(max(0, min(100, 100 - (
        abs(p1_po - p1_dc) * 0.5 +
        abs(p1_po - p1_mc) * 0.3 +
        abs(p1_ajustado - p1) * 0.2
    ))))
    
    # RANGO
    if conf >= 80:
        rango = "A+"
    elif conf >= 65:
        rango = "A"
    elif conf >= 50:
        rango = "B"
    elif conf >= 35:
        rango = "C"
    else:
        rango = "D"
    
    # PICK 1X2
    if p1_ajustado > px and p1_ajustado > p2:
        pick_1x2 = "1"
        prob_pick = p1_ajustado
    elif p2 > px and p2 > p1_ajustado:
        pick_1x2 = "2"
        prob_pick = p2
    else:
        pick_1x2 = "X"
        prob_pick = px_ajustado
    
    # PICK OVER/UNDER
    pick_ou = "Over 2.5" if ou["over_25"] > 50 else "Under 2.5"
    prob_ou = max(ou["over_25"], ou["under_25"])
    
    # Pick Corners
    pick_corners = f"Over {prediccion_corners['total_estimado']:.0f}" if prediccion_corners['over_95'] > 50 else f"Under {prediccion_corners['total_estimado']:.0f}"
    
    return {
        # Datos de entrada
        "lambda_local": xl,
        "lambda_visitante": xv,
        "goles_esperados": round((xl + xv) / 2 * 2, 1),
        
        # 1X2
        "p1": p1_ajustado,
        "px": px_ajustado,
        "p2": p2_ajustado,
        "pick_1x2": pick_1x2,
        "prob_1x2": prob_pick,
        
        # Over/Under
        "over_under": {
            "over_15": ou["over_15"],
            "under_15": ou["under_15"],
            "over_25": ou["over_25"],
            "under_25": ou["under_25"],
            "over_35": ou["over_35"],
            "under_35": ou["under_35"],
        },
        "pick_over_under": pick_ou,
        "prob_over_under": prob_ou,
        
        # Ambos Marcan
        "btts_yes": p_btts_yes,
        "btts_no": p_btts_no,
        "pick_btts": "Sí" if p_btts_yes > 50 else "No",
        
        # Córners
        "corners": prediccion_corners,
        "pick_corners": pick_corners,
        
        # Forma Reciente
        "forma_local": forma_local,
        "forma_visitante": forma_visitante,
        
        # Estilo de Juego
        "estilo_local": estilo_local,
        "estilo_visitante": estilo_visitante,
        
        # Confianza y Rango
        "confianza": conf,
        "rango": rango,
        
        # Detalle de modelos
        "modelos": {
            "poisson": {"p1": p1_po, "px": px_po, "p2": p2_po},
            "dixon_coles": {"p1": p1_dc, "px": px_dc, "p2": p2_dc},
            "monte_carlo": {"p1": p1_mc, "px": px_mc, "p2": p2_mc},
        },
        
        # Top marcadores predichos
        "top_scores": mc["top_scores"],
    }


def analyze(
    home: str,
    away: str,
    lambda_h: float,
    lambda_v: float,
    # Nuevos parámetros opcionales
    corners_home: float = 10.0,
    corners_away: float = 10.0,
    tarjetas_home: float = 3.5,
    tarjetas_away: float = 3.5,
    tiros_home: float = 12.0,
    tiros_away: float = 12.0,
    tiros_arco_home: float = 4.0,
    tiros_arco_away: float = 4.0,
    ultimos_5_home: List[Dict] = None,
    ultimos_5_away: List[Dict] = None,
) -> Dict:
    """
    Función para analizar un partido con todos los datos disponibles.
    """
    return calcular(
        lambda_h,
        lambda_v,
        corners_home,
        corners_away,
        tarjetas_home,
        tarjetas_away,
        tiros_home,
        tiros_away,
        tiros_arco_home,
        tiros_arco_away,
        ultimos_5_home,
        ultimos_5_away,
    )
