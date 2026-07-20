"""
Motor de análisis matemático con type hints y validación.
Incluye Poisson, Dixon-Coles, Monte Carlo y Elo.
"""
import math
import random
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

from scorpion.config import config, LIGAS_PROMEDIOS, LIGAS_TOP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelValidationError(Exception):
    """Error de validación en modelos matemáticos."""
    pass


@dataclass
class MercadoPick:
    """Representa un mercado/pick calculado."""
    nombre: str
    probabilidad: float
    cuota_referencia: float
    edge: Optional[float] = None
    es_recomendado: bool = False


@dataclass
class CalculoResultado:
    """Resultado completo del análisis de un partido."""
    xl: float; xv: float; xt: float
    p1_poisson: float; px_poisson: float; p2_poisson: float
    p1_dixon_coles: float; px_dixon_coles: float; p2_dixon_coles: float
    p1_monte_carlo: float; px_monte_carlo: float; p2_monte_carlo: float
    p1_elo: float; px_elo: float; p2_elo: float
    p1: float; px: float; p2: float
    confianza: float; rango: str
    over05: float; over15: float; over25: float; over35: float
    btts_si: float; btts_no: float
    corners_promedio: float; corners_over75: float
    corners_over85: float; corners_over95: float
    resultado_1x2: str; pick_clave: str
    mercados: List[MercadoPick] = field(default_factory=list)
    datos_reales: bool = False
    fuente_datos: str = "Sin datos"


class MotorAnalisis:
    """Motor de análisis matemático combinando 4 modelos."""

    def __init__(
        self,
        peso_poisson: float = config.WEIGHT_POISSON,
        peso_dixon_coles: float = config.WEIGHT_DIXON_COLES,
        peso_monte_carlo: float = config.WEIGHT_MONTE_CARLO,
        peso_elo: float = config.WEIGHT_ELO,
        num_simulaciones: int = config.MONTE_CARLO_SIMULATIONS,
        rho: float = config.DC_RHO_CORRELATION,
    ) -> None:
        total = peso_poisson + peso_dixon_coles + peso_monte_carlo + peso_elo
        if abs(total - 1.0) > 0.001:
            logger.warning(f"Pesos no suman 1.0 ({total}), ajustando...")
        self.pesos = {
            "poisson": peso_poisson,
            "dixon_coles": peso_dixon_coles,
            "monte_carlo": peso_monte_carlo,
            "elo": peso_elo,
        }
        self.num_simulaciones = num_simulaciones
        self.rho = rho
        logger.info(f"Motor inicializado con pesos: {self.pesos}")

    def poisson_probabilidad(self, lam: float, k: int) -> float:
        """Calcula P(X=k) para distribución de Poisson."""
        if k < 0:
            return 0.0
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        try:
            return (math.exp(-lam) * (lam ** k)) / math.factorial(min(k, 20))
        except (OverflowError, ValueError):
            logger.warning(f"Overflow en poisson({lam}, {k})")
            return 0.0

    def dixon_coles_tau(self, x: int, y: int, xl: float, xv: float, rho: Optional[float] = None) -> float:
        """Factor tau de Dixon-Coles."""
        rho = rho or self.rho
        if x == 0 and y == 0: return 1 - xl * xv * rho
        if x == 1 and y == 0: return 1 + xv * rho
        if x == 0 and y == 1: return 1 + xl * rho
        if x == 1 and y == 1: return 1 - rho
        return 1.0

    def modelo_poisson_1x2(self, xl: float, xv: float) -> Tuple[float, float, float]:
        """Calcula probabilidades 1X2 usando Poisson."""
        p1 = px = p2 = 0.0
        for i in range(config.MAX_GOALS_CALC):
            for j in range(config.MAX_GOALS_CALC):
                p = self.poisson_probabilidad(xl, i) * self.poisson_probabilidad(xv, j)
                if i > j: p1 += p
                elif i == j: px += p
                else: p2 += p
        return (round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1))

    def modelo_dixon_coles_1x2(self, xl: float, xv: float, rho: Optional[float] = None) -> Tuple[float, float, float]:
        """Calcula probabilidades 1X2 usando Dixon-Coles."""
        rho = rho or self.rho
        matriz: Dict[Tuple[int, int], float] = {}
        for i in range(config.MAX_GOALS_CALC):
            for j in range(config.MAX_GOALS_CALC):
                p = self.poisson_probabilidad(xl, i) * self.poisson_probabilidad(xv, j)
                matriz[(i, j)] = max(0, p * self.dixon_coles_tau(i, j, xl, xv, rho))
        total = sum(matriz.values())
        if total > 0:
            matriz = {k: v / total for k, v in matriz.items()}
        p1 = sum(v for (i, j), v in matriz.items() if i > j)
        px = sum(v for (i, j), v in matriz.items() if i == j)
        p2 = sum(v for (i, j), v in matriz.items() if i < j)
        return (round(p1 * 100, 1), round(px * 100, 1), round(p2 * 100, 1))

    def _simular_goles_poisson(self, lam: float) -> int:
        """Simula número de goles."""
        u = random.random()
        acumulada = 0.0
        for k in range(15):
            acumulada += self.poisson_probabilidad(lam, k)
            if u <= acumulada:
                return k
        return 14

    def modelo_monte_carlo_1x2(self, xl: float, xv: float, n: Optional[int] = None) -> Tuple[float, float, float, float, float]:
        """Simula n partidos usando Monte Carlo."""
        n = n or self.num_simulaciones
        v1 = vx = v2 = 0
        goles_totales: List[int] = []
        for _ in range(n):
            gl = self._simular_goles_poisson(xl)
            gv = self._simular_goles_poisson(xv)
            if gl > gv: v1 += 1
            elif gl == gv: vx += 1
            else: v2 += 1
            goles_totales.append(gl + gv)
        prom_goles = sum(goles_totales) / n
        over_25 = sum(1 for g in goles_totales if g > 2) / n * 100
        return (round(v1 / n * 100, 1), round(vx / n * 100, 1), round(v2 / n * 100, 1), round(prom_goles, 2), round(over_25, 1))

    def modelo_elo_1x2(self, elo_l: float, elo_v: float, ventaja_local: int = config.HOME_ADVANTAGE) -> Tuple[float, float, float]:
        """Calcula probabilidades usando ratings Elo."""
        if elo_l is None or elo_v is None:
            return (33.3, 33.3, 33.3)
        diferencia = elo_l + ventaja_local - elo_v
        e_l = 1 / (1 + 10 ** (-diferencia / 400))
        p1 = round(e_l * 100, 1)
        p2 = round((1 - e_l) * 100, 1)
        px = max(0.1, round(100 - p1 - p2, 1))
        return (p1, px, p2)

    def calcular_over_under(self, xt: float) -> Tuple[float, float, float, float]:
        """Calcula probabilidades Over/Under."""
        p0 = self.poisson_probabilidad(xt, 0)
        p1 = self.poisson_probabilidad(xt, 1)
        p2 = self.poisson_probabilidad(xt, 2)
        p3 = self.poisson_probabilidad(xt, 3)
        return (
            round((1 - p0) * 100, 1),
            round((1 - p0 - p1) * 100, 1),
            round((1 - p0 - p1 - p2) * 100, 1),
            round((1 - p0 - p1 - p2 - p3) * 100, 1),
        )

    def calcular_btts(self, xl: float, xv: float) -> Tuple[float, float]:
        """Calcula probabilidades BTTS."""
        local_no = self.poisson_probabilidad(xl, 0)
        visitante_no = self.poisson_probabilidad(xv, 0)
        btts_si = round((1 - local_no) * (1 - visitante_no) * 100, 1)
        return (btts_si, round(100 - btts_si, 1))

    def calcular_corners(self, xt: float) -> Tuple[float, float, float, float, float]:
        """Calcula probabilidades de corners."""
        cmu = round(min(14, xt * 1.4 + 6.5), 1)
        sc = 2.0
        def prob_over(t: float) -> float:
            z = (t - cmu) / sc
            return max(5, min(95, round((1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))) * 100)))
        return (cmu, prob_over(7.5), prob_over(8.5), prob_over(9.5), prob_over(10.5))

    def _calcular_cuota_referencia(self, probabilidad: float) -> float:
        """Calcula cuota de referencia con margen del 7%."""
        if probabilidad <= 0:
            return 1.0
        return round((100 / probabilidad) * 1.07, 2)

    def _es_liga_top(self, liga: str) -> bool:
        """Verifica si es liga top."""
        return any(top in liga.lower() for top in LIGAS_TOP)

    def _get_promedio_liga(self, liga: str) -> Dict[str, float]:
        """Obtiene promedios de liga."""
        for key, valores in LIGAS_PROMEDIOS.items():
            if key in liga.lower():
                return valores
        return LIGAS_PROMEDIOS["default"]

    def _calcular_xg(self, gm_l: Optional[float], gc_l: Optional[float], gm_v: Optional[float], gc_v: Optional[float], prom: Dict[str, float]) -> Tuple[float, float]:
        """Calcula xG ajustados."""
        if gm_l is not None and gc_l is not None:
            xl = round(gm_l * (gc_l / prom["gc"]) * config.HOME_GOALS_FACTOR, 2)
        elif gm_l is not None:
            xl = round(gm_l * config.HOME_GOALS_FACTOR, 2)
        else:
            xl = round(prom["gm"] * config.HOME_GOALS_FACTOR, 2)
        if gm_v is not None and gc_v is not None:
            xv = round(gm_v * (gc_v / prom["gc"]), 2)
        elif gm_v is not None:
            xv = round(gm_v, 2)
        else:
            xv = round(prom["gm"] * config.AWAY_GOALS_FACTOR, 2)
        return (xl, xv)

    def _ajustar_por_elo(self, xl: float, xv: float, elo_l: float, elo_v: float) -> Tuple[float, float]:
        """Ajusta xG basado en Elo."""
        factor = 1 + (elo_l - elo_v) / config.ELO_ADJUSTMENT_FACTOR
        factor = min(max(factor, config.ELO_MIN_FACTOR), config.ELO_MAX_FACTOR)
        return (round(xl * factor, 2), round(xv / factor, 2))

    def _determinar_rango(self, confianza: float, datos_reales: bool, liga_top: bool) -> str:
        """Determina el rango."""
        if datos_reales and confianza >= 75 and liga_top:
            return "A+"
        elif datos_reales and confianza >= 55:
            return "B"
        elif confianza >= 40:
            return "C"
        return "D"

    def _determinar_pick_clave(self, resultado: 'CalculoResultado') -> str:
        """Determina el pick clave."""
        p1, px, p2 = resultado.p1, resultado.px, resultado.p2
        if p1 > p2 and p1 > px and resultado.over25 >= 55:
            return "Gana Local + Over 1.5"
        elif p2 > p1 and p2 > px and resultado.over25 >= 55:
            return "Gana Visita + Over 1.5"
        elif resultado.over25 >= 65:
            return "Over 2.5 Goles"
        elif resultado.btts_si >= 62:
            return "BTTS — Ambos Marcan"
        elif resultado.corners_over95 >= 65:
            return "Corners Over 9.5"
        elif p1 > p2 and p1 > px:
            return "Victoria Local"
        elif p2 > p1 and p2 > px:
            return "Victoria Visitante"
        return "Empate posible"

    def _generar_mercados(self, resultado: 'CalculoResultado') -> List[MercadoPick]:
        """Genera lista de mercados."""
        mercados = []
        # 1X2
        if resultado.p1 > resultado.px and resultado.p1 > resultado.p2:
            mercados.append(MercadoPick("Victoria Local (1)", resultado.p1, self._calcular_cuota_referencia(resultado.p1)))
        elif resultado.p2 > resultado.px and resultado.p2 > resultado.p1:
            mercados.append(MercadoPick("Victoria Visitante (2)", resultado.p2, self._calcular_cuota_referencia(resultado.p2)))
        else:
            mercados.append(MercadoPick("Empate (X)", resultado.px, self._calcular_cuota_referencia(resultado.px)))
        # Over/Under
        for nombre, prob in [("Over 0.5 Goles", resultado.over05), ("Over 1.5 Goles", resultado.over15), ("Over 2.5 Goles", resultado.over25), ("Over 3.5 Goles", resultado.over35)]:
            mercados.append(MercadoPick(nombre, prob, self._calcular_cuota_referencia(prob), es_recomendado=prob >= 65))
        # BTTS
        mercados.append(MercadoPick("BTTS — Ambos Marcan", resultado.btts_si, self._calcular_cuota_referencia(resultado.btts_si), es_recomendado=resultado.btts_si >= 62))
        mercados.append(MercadoPick("BTTS — No", resultado.btts_no, self._calcular_cuota_referencia(resultado.btts_no)))
        # Corners
        for nombre, prob in [("Corners +7.5", resultado.corners_over75), ("Corners +8.5", resultado.corners_over85), ("Corners +9.5", resultado.corners_over95)]:
            mercados.append(MercadoPick(nombre, prob, self._calcular_cuota_referencia(prob), es_recomendado=prob >= 65))
        return mercados

    def analizar(
        self,
        gm_local: Optional[float] = None,
        gc_local: Optional[float] = None,
        gm_visitante: Optional[float] = None,
        gc_visitante: Optional[float] = None,
        liga: str = "",
        elo_local: Optional[float] = None,
        elo_visitante: Optional[float] = None,
        usar_datos_reales: bool = False,
    ) -> CalculoResultado:
        """Realiza análisis completo de un partido."""
        prom_liga = self._get_promedio_liga(liga)
        xl, xv = self._calcular_xg(gm_local, gc_local, gm_visitante, gc_visitante, prom_liga)
        if elo_local is not None and elo_visitante is not None:
            xl, xv = self._ajustar_por_elo(xl, xv, elo_local, elo_visitante)
        xl = max(0.15, xl)
        xv = max(0.10, xv)
        xt = round(xl + xv, 2)

        p1_p, px_p, p2_p = self.modelo_poisson_1x2(xl, xv)
        p1_dc, px_dc, p2_dc = self.modelo_dixon_coles_1x2(xl, xv)
        p1_mc, px_mc, p2_mc, _, _ = self.modelo_monte_carlo_1x2(xl, xv)
        p1_el, px_el, p2_el = self.modelo_elo_1x2(elo_local or 1500, elo_visitante or 1500)

        p1 = round(p1_p * self.pesos["poisson"] + p1_dc * self.pesos["dixon_coles"] + p1_mc * self.pesos["monte_carlo"] + p1_el * self.pesos["elo"], 1)
        px = round(px_p * self.pesos["poisson"] + px_dc * self.pesos["dixon_coles"] + px_mc * self.pesos["monte_carlo"] + px_el * self.pesos["elo"], 1)
        p2 = round(max(0, 100 - p1 - px), 1)

        conv = 100 - (abs(p1_p - p1_dc) * 0.4 + abs(p1_p - p1_mc) * 0.3 + abs(p1_p - p1_el) * 0.3)
        confianza = round(max(0, min(100, conv)))

        over05, over15, over25, over35 = self.calcular_over_under(xt)
        btts_si, btts_no = self.calcular_btts(xl, xv)
        cmu, c75, c85, c95, c105 = self.calcular_corners(xt)

        resultado_1x2 = "1" if p1 > p2 and p1 > px else ("X" if px >= p1 and px >= p2 else "2")
        es_liga_top = self._es_liga_top(liga)
        rango = self._determinar_rango(confianza, usar_datos_reales, es_liga_top)

        resultado = CalculoResultado(
            xl=xl, xv=xv, xt=xt,
            p1_poisson=p1_p, px_poisson=px_p, p2_poisson=p2_p,
            p1_dixon_coles=p1_dc, px_dixon_coles=px_dc, p2_dixon_coles=p2_dc,
            p1_monte_carlo=p1_mc, px_monte_carlo=px_mc, p2_monte_carlo=p2_mc,
            p1_elo=p1_el, px_elo=px_el, p2_elo=p2_el,
            p1=p1, px=px, p2=p2,
            confianza=confianza, rango=rango,
            over05=over05, over15=over15, over25=over25, over35=over35,
            btts_si=btts_si, btts_no=btts_no,
            corners_promedio=cmu, corners_over75=c75, corners_over85=c85, corners_over95=c95,
            resultado_1x2=resultado_1x2, pick_clave="",
            datos_reales=usar_datos_reales,
        )
        resultado.pick_clave = self._determinar_pick_clave(resultado)
        resultado.mercados = self._generar_mercados(resultado)
        return resultado
