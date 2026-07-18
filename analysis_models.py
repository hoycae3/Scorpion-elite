"""
Scorpion Elite - Modelos de Análisis Matemático
==============================================
4 modelos combinados para predecir resultados de fútbol:
- Poisson (35%): Distribución de probabilidad para goles
- Dixon-Coles (30%): Corrige dependencia entre goles marcados/recibidos
- Monte Carlo (20%): Simulación de 3000 partidos
- Elo (15%): Rating histórico de equipos
"""

import random
from typing import Dict


def pp(lmbda: float, k: int) -> float:
    """Función de masa de probabilidad de Poisson P(X=k)"""
    if lmbda <= 0 or k < 0:
        return 0.0
    result = 1.0
    for i in range(2, k + 1):
        result *= lmbda / i
    return result * (2.71828 ** (-lmbda))


def poisson_1x2(xl: float, xv: float) -> tuple:
    """Modelo Poisson básico"""
    p1 = px = p2 = 0.0
    for i in range(9):
        for j in range(9):
            p = pp(xl, i) * pp(xv, j)
            if i > j:
                p1 += p
            elif i == j:
                px += p
            else:
                p2 += p
    return round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1)


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
        "top_scores": top_scores
    }


def elo_1x2(elo_l: float, elo_v: float, home_adv: float = 50) -> tuple:
    """Modelo Elo"""
    expected = 1 / (1 + 10 ** ((elo_v - (elo_l + home_adv)) / 400))
    p1 = round(expected * 100, 1)
    p2 = round((1 - expected) * 100, 1)
    px = max(0, round(100 - p1 - p2, 1))
    return p1, px, p2


def calcular(
    lambda_local: float,
    lambda_visitante: float
) -> Dict:
    """Calcula probabilidades usando los 4 modelos combinados"""
    xl = max(0.15, lambda_local)
    xv = max(0.10, lambda_visitante)
    
    p1_po, px_po, p2_po = poisson_1x2(xl, xv)
    p1_dc, px_dc, p2_dc = dc_1x2(xl, xv)
    
    mc = monte_carlo(xl, xv)
    p1_mc, px_mc, p2_mc = mc["p1"], mc["px"], mc["p2"]
    
    # Elo usa 1500 por defecto (neutro)
    p1_el, px_el, p2_el = elo_1x2(1500, 1500)
    
    # Combinar
    p1 = round(p1_po * 0.35 + p1_dc * 0.30 + p1_mc * 0.20 + p1_el * 0.15, 1)
    px = round(px_po * 0.35 + px_dc * 0.30 + px_mc * 0.20 + px_el * 0.15, 1)
    p2 = round(max(0, 100 - p1 - px), 1)
    
    # Confianza
    conf = round(max(0, min(100, 100 - (
        abs(p1_po - p1_dc) * 0.4 +
        abs(p1_po - p1_mc) * 0.3 +
        abs(p1_po - p1_el) * 0.3
    ))))
    
    # Rating
    if conf >= 75:
        rango = "A+"
    elif conf >= 55:
        rango = "B"
    elif conf >= 40:
        rango = "C"
    else:
        rango = "D"
    
    # Pick
    if p1 > px and p1 > p2:
        pick = "1"
        prob_pick = p1
    elif p2 > px and p2 > p1:
        pick = "2"
        prob_pick = p2
    else:
        pick = "X"
        prob_pick = px
    
    return {
        "lambda_local": xl,
        "lambda_visitante": xv,
        "poisson": {"p1": p1_po, "px": px_po, "p2": p2_po},
        "dixon_coles": {"p1": p1_dc, "px": px_dc, "p2": p2_dc},
        "monte_carlo": {"p1": p1_mc, "px": px_mc, "p2": p2_mc},
        "elo": {"p1": p1_el, "px": px_el, "p2": p2_el},
        "p1": p1,
        "px": px,
        "p2": p2,
        "pick": pick,
        "prob_pick": prob_pick,
        "confianza": conf,
        "rango": rango,
    }


def analyze(home: str, away: str, lambda_h: float, lambda_v: float) -> Dict:
    """Función simple para analizar un partido"""
    return calcular(lambda_h, lambda_v)
