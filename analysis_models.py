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


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES BASE - PROBABILIDAD POISSON
# ═══════════════════════════════════════════════════════════════════════════════
def pp(lmbda: float, k: int) -> float:
    """Función de masa de probabilidad de Poisson P(X=k) = lambda^k * e^(-lambda) / k!"""
    if lmbda <= 0 or k < 0:
        return 0.0
    # Usar aproximación para estabilidad numérica
    log_p = k * log_factorial_approx(lmbda) - lmbda
    return exp_approx(log_p)


def log_factorial_approx(n: float) -> float:
    """Aproximación log(n!) usando Stirling"""
    if n <= 1:
        return 0.0
    if n < 60:
        # Calcular directamente para valores pequeños
        result = 0.0
        for i in range(2, int(n) + 1):
            result += log_approx(i)
        return result
    return n * log_approx(n) - n + 0.5 * log_approx(6.28 * n)


def log_approx(x: float) -> float:
    """Logaritmo natural aproximado"""
    if x <= 0:
        return -float('inf')
    return x - 1 if abs(x - 1) < 0.5 else log_approx(x / 2.71828)


def exp_approx(x: float) -> float:
    """Exponencial aproximada"""
    if x < -20:
        return 0.0
    if x > 10:
        return 22026.0
    # Serie de Taylor para e^x
    result = 1.0
    term = 1.0
    for i in range(1, 20):
        term *= x / i
        result += term
        if abs(term) < 1e-10:
            break
    return max(0.0, result)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELO 1: POISSON
# ═══════════════════════════════════════════════════════════════════════════════
def poisson_1x2(xl: float, xv: float) -> tuple:
    """Modelo Poisson básico - calcula probabilidades 1X2
    
    Args:
        xl: Lambda (goles esperados) equipo local
        xv: Lambda (goles esperados) equipo visitante
    
    Returns:
        (prob_home, prob_draw, prob_away) en porcentaje
    """
    p1 = px = p2 = 0.0
    for i in range(9):  # 0-8 goles
        for j in range(9):
            p = pp(xl, i) * pp(xv, j)
            if i > j:
                p1 += p
            elif i == j:
                px += p
            else:
                p2 += p
    return round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELO 2: DIXON-COLES
# ═══════════════════════════════════════════════════════════════════════════════
def dc_tau_func(i: int, j: int, rho: float) -> float:
    """Función tau de Dixon-Coles - corrige dependencia entre goles"""
    if i <= 1 and j <= 1:
        if i == 0 and j == 0:
            return 1 + rho
        elif i == j:
            return 1
        else:
            return 1 + rho * 0.5
    else:
        return 1 - rho * (i + j) / 16


def dc_1x2(xl: float, xv: float, rho: float = -0.1) -> tuple:
    """Modelo Dixon-Coles - corrige scores 0-0, 0-1, 1-0
    
    Args:
        xl: Lambda equipo local
        xv: Lambda equipo visitante
        rho: Parámetro de correlación (-0.25 a 0.25, típicamente -0.1)
    
    Returns:
        (prob_home, prob_draw, prob_away) en porcentaje
    """
    m = {}
    for i in range(9):
        for j in range(9):
            p = pp(xl, i) * pp(xv, j) * dc_tau_func(i, j, rho)
            m[(i, j)] = max(0, p)
    
    total = sum(m.values())
    if total > 0:
        m = {k: v / total for k, v in m.items()}
    
    p1 = sum(v for (i, j), v in m.items() if i > j)
    px = sum(v for (i, j), v in m.items() if i == j)
    p2 = sum(v for (i, j), v in m.items() if i < j)
    
    return round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1)


# ═══════════════════════════════════════════════════════════════════════════════
# MODELO 3: MONTE CARLO
# ═══════════════════════════════════════════════════════════════════════════════
def monte_carlo(xl: float, xv: float, n: int = 3000) -> Dict:
    """Simulación Monte Carlo - simula n partidos
    
    Args:
        xl: Lambda equipo local
        xv: Lambda equipo visitante
        n: Número de simulaciones (default 3000)
    
    Returns:
        Dict con probabilidades y estadísticas
    """
    v1 = vx = v2 = 0
    goals_total = []
    score_map = {}
    
    random.seed(42)  # Reproducibilidad
    
    for _ in range(n):
        # Simular goles del local usando Poisson
        gl = 0
        u = random.random()
        cum_prob = 0.0
        for k in range(15):
            cum_prob += pp(xl, k)
            if u <= cum_prob:
                gl = k
                break
        
        # Simular goles del visitante
        gv = 0
        u = random.random()
        cum_prob = 0.0
        for k in range(15):
            cum_prob += pp(xv, k)
            if u <= cum_prob:
                gv = k
                break
        
        # Clasificar resultado
        if gl > gv:
            v1 += 1
        elif gl == gv:
            vx += 1
        else:
            v2 += 1
        
        # Goals totales para Over/Under
        goals_total.append(gl + gv)
        
        # Score más frecuente
        score_key = f"{gl}-{gv}"
        score_map[score_key] = score_map.get(score_key, 0) + 1
    
    # Top 6 scores más probables
    top_scores = dict(sorted(score_map.items(), key=lambda x: x[1], reverse=True)[:6])
    top_scores = {k: round(v / n * 100, 1) for k, v in top_scores.items()}
    
    return {
        "p1": round(v1 / n * 100, 1),
        "px": round(vx / n * 100, 1),
        "p2": round(v2 / n * 100, 1),
        "avg_goals": round(sum(goals_total) / n, 2),
        "over_25": round(sum(1 for g in goals_total if g > 2) / n * 100, 1),
        "top_scores": top_scores,
        "simulations": n
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MODELO 4: ELO
# ═══════════════════════════════════════════════════════════════════════════════
def elo_1x2(elo_l: float, elo_v: float, home_advantage: float = 50) -> tuple:
    """Modelo Elo - rating histórico de equipos
    
    Args:
        elo_l: Rating Elo equipo local
        elo_v: Rating Elo equipo visitante
        home_advantage: Ventaja local en puntos Elo (default 50)
    
    Returns:
        (prob_home, prob_draw, prob_away) en porcentaje
    """
    # Esperanza de victoria del local
    expected = 1 / (1 + 10 ** ((elo_v - (elo_l + home_advantage)) / 400))
    
    p1 = round(expected * 100, 1)
    p2 = round((1 - expected) * 100, 1)
    px = max(0, round(100 - p1 - p2, 1))
    
    return p1, px, p2


# ═══════════════════════════════════════════════════════════════════════════════
# CÁLCULO PRINCIPAL - COMBINA LOS 4 MODELOS
# ═══════════════════════════════════════════════════════════════════════════════
def calcular(
    gml: float = None,
    gcl: float = None,
    gmv: float = None,
    gcv: float = None,
    prom_liga_goles: float = 2.7,
    elo_l: float = None,
    elo_v: float = None
) -> Dict:
    """Calcula probabilidades usando los 4 modelos combinados
    
    Args:
        gml: Goles marcados local (promedio temporada)
        gcl: Goles recibidos local
        gmv: Goles marcados visitante
        gcv: Goles recibidos visitante
        prom_liga_goles: Promedio de goles de la liga (default 2.7)
        elo_l: Rating Elo local (opcional)
        elo_v: Rating Elo visitante (opcional)
    
    Returns:
        Dict con todos los resultados de los 4 modelos
    """
    # Calcular lambda (goles esperados) ajustado
    if gml and gcv:
        xl = round(gml * (gcv / prom_liga_goles) * 1.08, 2)  # 1.08 = factor casa
    elif gml:
        xl = round(gml * 1.08, 2)
    else:
        xl = round(prom_liga_goles * 0.8, 2)
    
    if gmv and gcl:
        xv = round(gmv * (gcl / prom_liga_goles), 2)
    elif gmv:
        xv = round(gmv, 2)
    else:
        xv = round(prom_liga_goles * 0.6, 2)
    
    # Ajustar por Elo si está disponible
    if elo_l and elo_v:
        factor = 1 + (elo_l - elo_v) / 4000
        xl = round(xl * min(max(factor, 0.7), 1.4), 2)
        xv = round(xv * min(max(1 / factor, 0.7), 1.4), 2)
    
    xl = max(0.15, xl)
    xv = max(0.10, xv)
    xt = round(xl + xv, 2)
    
    # Ejecutar los 4 modelos
    p1_po, px_po, p2_po = poisson_1x2(xl, xv)
    p1_dc, px_dc, p2_dc = dc_1x2(xl, xv)
    
    mc = monte_carlo(xl, xv)
    p1_mc, px_mc, p2_mc = mc["p1"], mc["px"], mc["p2"]
    
    if elo_l and elo_v:
        p1_el, px_el, p2_el = elo_1x2(elo_l, elo_v)
    else:
        p1_el, px_el, p2_el = p1_po, px_po, p2_po
    
    # Combinar con pesos
    p1 = round(p1_po * 0.35 + p1_dc * 0.30 + p1_mc * 0.20 + p1_el * 0.15, 1)
    px = round(px_po * 0.35 + px_dc * 0.30 + px_mc * 0.20 + px_el * 0.15, 1)
    p2 = round(max(0, 100 - p1 - px), 1)
    
    # Calcular confianza basada en convergencia de modelos
    conv = 100 - (
        abs(p1_po - p1_dc) * 0.4 +
        abs(p1_po - p1_mc) * 0.3 +
        abs(p1_po - p1_el) * 0.3
    )
    conf = round(max(0, min(100, conv)))
    
    # Determinar rating
    datos_reales = gml is not None and gmv is not None
    if datos_reales and conf >= 75:
        rango = "A+"
    elif datos_reales and conf >= 55:
        rango = "B"
    elif conf >= 40:
        rango = "C"
    else:
        rango = "D"
    
    # Over/Under
    p0 = pp(xt, 0)
    p1_ = pp(xt, 1)
    p2_ = pp(xt, 2)
    p3_ = pp(xt, 3)
    
    over_05 = round((1 - p0) * 100)
    over_15 = round((1 - p0 - p1_) * 100)
    over_25 = round((1 - p0 - p1_ - p2_) * 100)
    over_35 = round((1 - p0 - p1_ - p2_ - p3_) * 100)
    
    # BTTS (Both Teams To Score)
    btts_yes = round((1 - pp(xl, 0)) * (1 - pp(xv, 0)) * 100)
    btts_no = 100 - btts_yes
    
    # Pick recomendado
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
        # Lambdas
        "lambda_local": xl,
        "lambda_visitante": xv,
        "lambda_total": xt,
        
        # Modelo individual
        "poisson": {"p1": p1_po, "px": px_po, "p2": p2_po},
        "dixon_coles": {"p1": p1_dc, "px": px_dc, "p2": p2_dc},
        "monte_carlo": {"p1": p1_mc, "px": px_mc, "p2": p2_mc, **mc},
        "elo": {"p1": p1_el, "px": px_el, "p2": p2_el, "elo_l": elo_l, "elo_v": elo_v},
        
        # Combinado
        "p1": p1,
        "px": px,
        "p2": p2,
        
        # Mercados
        "over_05": over_05,
        "over_15": over_15,
        "over_25": over_25,
        "over_35": over_35,
        "btts_yes": btts_yes,
        "btts_no": btts_no,
        
        # Pick
        "pick": pick,
        "prob_pick": prob_pick,
        "confianza": conf,
        "rango": rango,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════
class FootballAnalyzer:
    """Analizador de partidos con 4 modelos matemáticos."""
    
    def __init__(self):
        self.elo_ratings = {}
        self.default_elo = 1500
    
    def analyze(
        self,
        home_team: str,
        away_team: str,
        home_goals_avg: float = None,
        away_goals_avg: float = None,
        home_goals_conceded: float = None,
        away_goals_conceded: float = None,
        prom_liga_goles: float = 2.7,
        elo_l: float = None,
        elo_v: float = None
    ) -> Dict:
        """Analiza un partido"""
        return calcular(
            gml=home_goals_avg,
            gcl=home_goals_conceded,
            gmv=away_goals_avg,
            gcv=away_goals_conceded,
            prom_liga_goles=prom_liga_goles,
            elo_l=elo_l or self.elo_ratings.get(home_team),
            elo_v=elo_v or self.elo_ratings.get(away_team)
        )
    
    def update_elo(self, home: str, away: str, home_goals: int, away_goals: int):
        """Actualiza ratings Elo después de un partido"""
        elo_h = self.elo_ratings.get(home, self.default_elo)
        elo_a = self.elo_ratings.get(away, self.default_elo)
        
        expected_h = 1 / (1 + 10 ** ((elo_a - elo_h) / 400))
        
        if home_goals > away_goals:
            actual_h, actual_a = 1, 0
        elif home_goals < away_goals:
            actual_h, actual_a = 0, 1
        else:
            actual_h, actual_a = 0.5, 0.5
        
        k = 32
        self.elo_ratings[home] = elo_h + k * (actual_h - expected_h)
        self.elo_ratings[away] = elo_a + k * (actual_a - (1 - expected_h))


# Función helper simple
def analyze(home: str, away: str, **kwargs) -> Dict:
    """Función simple para analizar un partido"""
    return FootballAnalyzer().analyze(home, away, **kwargs)
