"""
Scorpion Elite - Optimizador de Modelos
======================================
Sistema de aprendizaje que mide el % de acierto de cada modelo
y ajusta los pesos automáticamente.

CÓMO FUNCIONA:
1. Guardar predicción de cada modelo (Poisson, Dixon-Coles, Monte Carlo, Forma, Estilo)
2. Cuando termina el partido, registrar resultado real
3. Comparar: ¿qué modelo predijo correctamente?
4. Ajustar pesos: dar más peso al modelo que más acierta
"""

from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pesos actuales (iniciales)
PESOS_ACTUALES = {
    'poisson': 0.30,
    'dixon_coles': 0.25,
    'monte_carlo': 0.20,
    'forma_reciente': 0.15,
    'estilo_juego': 0.10,
}


def calcular_resultado_real(goles_local: int, goles_visitante: int) -> Dict:
    """
    Calcula el resultado real de un partido.
    
    Returns:
        - resultado_1x2: '1', 'X', '2'
        - total_goles: int
        - ambos_marcan: 'SI', 'NO'
    """
    if goles_local > goles_visitante:
        resultado_1x2 = '1'
    elif goles_local < goles_visitante:
        resultado_1x2 = '2'
    else:
        resultado_1x2 = 'X'
    
    total_goles = goles_local + goles_visitante
    ambos_marcan = 'SI' if goles_local > 0 and goles_visitante > 0 else 'NO'
    
    return {
        'resultado_1x2': resultado_1x2,
        'total_goles': total_goles,
        'ambos_marcan': ambos_marcan,
    }


def determinar_acierto_modelo(
    prediccion: str,
    probabilidad: float,
    resultado_real: str,
    umbral: float = 50.0
) -> bool:
    """
    Determina si un modelo acertó o no.
    
    Un modelo acierta si:
    - La probabilidad de su predicción > umbral (ej: 50%)
    - Y la predicción coincide con el resultado real
    """
    # Solo cuenta como acierto si la confianza era > umbral
    if probabilidad < umbral:
        return False
    
    return prediccion == resultado_real


def calcular_acierto_1x2(
    modelo: str,
    p1: float,
    px: float,
    p2: float,
    resultado_real: str
) -> bool:
    """Calcula si el modelo acertó el 1X2."""
    # Determinar qué predijo este modelo
    if p1 >= px and p1 >= p2:
        prediccion = '1'
        probabilidad = p1
    elif p2 >= px and p2 >= p1:
        prediccion = '2'
        probabilidad = p2
    else:
        prediccion = 'X'
        probabilidad = px
    
    return determinar_acierto_modelo(prediccion, probabilidad, resultado_real)


def calcular_metricas_modelo(predicciones: List[Dict]) -> Dict:
    """
    Calcula las métricas de un modelo basándose en predicciones pasadas.
    
    Args:
        predicciones: Lista de dicts con:
            - acierto: bool
            - probabilidad: float
    
    Returns:
        - total: int
        - aciertos: int
        - porcentaje: float
        - precision_alta_confianza: float (% de aciertos cuando prob > 60%)
    """
    if not predicciones:
        return {
            'total': 0,
            'aciertos': 0,
            'porcentaje': 0,
            'precision_alta_confianza': 0,
        }
    
    total = len(predicciones)
    aciertos = sum(1 for p in predicciones if p.get('acierto'))
    porcentaje = (aciertos / total * 100) if total > 0 else 0
    
    # Precisión cuando la confianza era alta (>60%)
    alta_confianza = [p for p in predicciones if p.get('probabilidad', 0) >= 60]
    if alta_confianza:
        aciertos_alta = sum(1 for p in alta_confianza if p.get('acierto'))
        precision_alta = (aciertos_alta / len(alta_confianza) * 100)
    else:
        precision_alta = 0
    
    return {
        'total': total,
        'aciertos': aciertos,
        'porcentaje': round(porcentaje, 2),
        'precision_alta_confianza': round(precision_alta, 2),
    }


def optimizar_pesos(metricas_modelos: Dict[str, Dict]) -> Dict[str, float]:
    """
    Optimiza los pesos de los modelos basándose en su % de acierto histórico.
    
    Usa un algoritmo simple:
    - Si un modelo tiene alto % de acierto → más peso
    - Si un modelo tiene bajo % de acierto → menos peso
    - Normaliza para que sumen 1.0
    
    Args:
        metricas_modelos: {
            'poisson': {'porcentaje': 55.5, 'total': 100},
            'dixon_coles': {'porcentaje': 52.0, 'total': 100},
            ...
        }
    
    Returns:
        Nuevos pesos normalizados: {'poisson': 0.35, 'dixon_coles': 0.25, ...}
    """
    if not metricas_modelos:
        return PESOS_ACTUALES.copy()
    
    # Filtrar modelos con suficientes datos (mínimo 20 predicciones)
    modelos_validos = {
        m: datos for m, datos in metricas_modelos.items()
        if datos.get('total', 0) >= 20
    }
    
    if len(modelos_validos) < 2:
        logger.warning("No hay suficientes datos para optimizar pesos")
        return PESOS_ACTUALES.copy()
    
    # Calcular score para cada modelo
    # Score = porcentaje de acierto + bonus por precisión alta confianza
    scores = {}
    for modelo, datos in modelos_validos.items():
        pct = datos.get('porcentaje', 0)
        alta = datos.get('precision_alta_confianza', 0)
        
        # Score ponderado: 70% acierto general + 30% acierto alta confianza
        score = pct * 0.7 + alta * 0.3
        scores[modelo] = max(score, 1)  # Mínimo 1 para evitar pesos 0
    
    # Normalizar scores a pesos
    total_score = sum(scores.values())
    if total_score == 0:
        return PESOS_ACTUALES.copy()
    
    nuevos_pesos = {
        modelo: round(score / total_score, 3)
        for modelo, score in scores.items()
    }
    
    # Asegurar que sumen exactamente 1.0
    suma = sum(nuevos_pesos.values())
    if suma != 1.0:
        # Ajustar el modelo con mayor peso
        mayor = max(nuevos_pesos, key=nuevos_pesos.get)
        nuevos_pesos[mayor] = round(nuevos_pesos[mayor] + (1.0 - suma), 3)
    
    logger.info(f"📊 Pesos optimizados: {nuevos_pesos}")
    return nuevos_pesos


def generar_recomendacion_peso(porcentaje: float) -> str:
    """Genera una recomendación basada en el % de acierto."""
    if porcentaje >= 60:
        return "🟢 Excelente"
    elif porcentaje >= 52:
        return "🟡 Bueno"
    elif porcentaje >= 45:
        return "🟠 Regular"
    else:
        return "🔴 Bajo"


def analizar_modelos(historial: List[Dict]) -> Dict:
    """
    Analiza todos los modelos con el historial de predicciones.
    
    Args:
        historial: Lista de predicciones con resultados reales
    
    Returns:
        Dict con métricas por modelo, pesos óptimos, y recomendaciones
    """
    if not historial:
        return {
            'error': 'No hay historial suficiente',
            'modelos': {},
            'pesos_recomendados': PESOS_ACTUALES.copy(),
        }
    
    # Agrupar predicciones por modelo
    poisson_preds = []
    dc_preds = []
    mc_preds = []
    forma_preds = []
    
    for pred in historial:
        # Poisson
        poisson_preds.append({
            'acierto': pred.get('poisson_acierto', False),
            'probabilidad': max(
                pred.get('poisson_1', 0),
                pred.get('poisson_X', 0),
                pred.get('poisson_2', 0)
            ),
        })
        
        # Dixon-Coles
        dc_preds.append({
            'acierto': pred.get('dc_acierto', False),
            'probabilidad': max(
                pred.get('dc_1', 0),
                pred.get('dc_X', 0),
                pred.get('dc_2', 0)
            ),
        })
        
        # Monte Carlo
        mc_preds.append({
            'acierto': pred.get('mc_acierto', False),
            'probabilidad': max(
                pred.get('mc_1', 0),
                pred.get('mc_X', 0),
                pred.get('mc_2', 0)
            ),
        })
        
        # Forma Reciente
        forma_preds.append({
            'acierto': pred.get('forma_acierto', False),
            'probabilidad': 50,  # La forma no tiene probabilidad asociada directamente
        })
    
    # Calcular métricas
    metricas = {
        'poisson': calcular_metricas_modelo(poisson_preds),
        'dixon_coles': calcular_metricas_modelo(dc_preds),
        'monte_carlo': calcular_metricas_modelo(mc_preds),
        'forma_reciente': calcular_metricas_modelo(forma_preds),
    }
    
    # Generar recomendaciones
    recomendaciones = {}
    for modelo, datos in metricas.items():
        pct = datos.get('porcentaje', 0)
        if pct > 0:
            recomendaciones[modelo] = generar_recomendacion_peso(pct)
    
    # Calcular pesos óptimos
    pesos_optimos = optimizar_pesos(metricas)
    
    return {
        'total_predicciones': len(historial),
        'modelos': metricas,
        'recomendaciones': recomendaciones,
        'pesos_actuales': PESOS_ACTUALES.copy(),
        'pesos_recomendados': pesos_optimos,
        'cambios_pesos': {
            m: round(pesos_optimos.get(m, 0) - PESOS_ACTUALES.get(m, 0), 3)
            for m in PESOS_ACTUALES.keys()
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIONES PARA INTEGRACIÓN CON EL MODELO
# ═══════════════════════════════════════════════════════════════════════════════

def guardar_prediccion(
    resultado_analisis: Dict,
    datos_equipos: Dict,
    fixture_id: int = None,
    fecha: str = None,
    liga: str = None
) -> Dict:
    """
    Prepara un registro de predicción para guardar en la base de datos.
    
    Esta función se llama después de hacer un análisis y antes de guardar.
    """
    modelos = resultado_analisis.get('modelos', {})
    forma_local = resultado_analisis.get('forma_local', {})
    forma_visitante = resultado_analisis.get('forma_visitante', {})
    estilo_local = resultado_analisis.get('estilo_local', {})
    estilo_visitante = resultado_analisis.get('estilo_visitante', {})
    
    # Preparar registro para historial
    registro = {
        'fixture_id': fixture_id,
        'fecha': fecha,
        'liga': liga,
        'equipo_local': datos_equipos.get('local', {}).get('equipo', 'Unknown'),
        'equipo_visitante': datos_equipos.get('visitante', {}).get('equipo', 'Unknown'),
        
        # Poisson
        'poisson_1': modelos.get('poisson', {}).get('p1', 0),
        'poisson_X': modelos.get('poisson', {}).get('px', 0),
        'poisson_2': modelos.get('poisson', {}).get('p2', 0),
        
        # Dixon-Coles
        'dc_1': modelos.get('dixon_coles', {}).get('p1', 0),
        'dc_X': modelos.get('dixon_coles', {}).get('px', 0),
        'dc_2': modelos.get('dixon_coles', {}).get('p2', 0),
        
        # Monte Carlo
        'mc_1': modelos.get('monte_carlo', {}).get('p1', 0),
        'mc_X': modelos.get('monte_carlo', {}).get('px', 0),
        'mc_2': modelos.get('monte_carlo', {}).get('p2', 0),
        
        # Forma Reciente
        'forma_local_pct': forma_local.get('forma_puntos', 0),
        'forma_visitante_pct': forma_visitante.get('forma_puntos', 0),
        
        # Estilo
        'estilo_local': estilo_local.get('tipo', 'Unknown'),
        'estilo_visitante': estilo_visitante.get('tipo', 'Unknown'),
        
        # Predicción final
        'prediccion_final': resultado_analisis.get('pick_1x2', ''),
        'probabilidad_final': resultado_analisis.get('prob_1x2', 0),
        
        # Pesos usados
        'peso_poisson': PESOS_ACTUALES['poisson'],
        'peso_dixon': PESOS_ACTUALES['dixon_coles'],
        'peso_montecarlo': PESOS_ACTUALES['monte_carlo'],
        'peso_forma': PESOS_ACTUALES['forma_reciente'],
        'peso_estilo': PESOS_ACTUALES['estilo_juego'],
        
        # Confianza
        'confianza': resultado_analisis.get('confianza', 0),
        'rango': resultado_analisis.get('rango', 'D'),
    }
    
    return registro


def actualizar_resultado(
    registro: Dict,
    goles_local: int,
    goles_visitante: int
) -> Dict:
    """
    Actualiza un registro de predicción con el resultado real.
    
    Esto marca qué modelos acertaron y cuál fue el resultado final.
    """
    resultado_real = calcular_resultado_real(goles_local, goles_visitante)
    
    # Actualizar campos de resultado
    registro['goles_local'] = goles_local
    registro['goles_visitante'] = goles_visitante
    registro['resultado_real'] = resultado_real['resultado_1x2']
    registro['total_goles'] = resultado_real['total_goles']
    registro['ambos_marcan'] = resultado_real['ambos_marcan']
    
    # Marcar aciertos de cada modelo
    registro['poisson_acierto'] = calcular_acierto_1x2(
        'poisson',
        registro.get('poisson_1', 0),
        registro.get('poisson_X', 0),
        registro.get('poisson_2', 0),
        resultado_real['resultado_1x2']
    )
    
    registro['dc_acierto'] = calcular_acierto_1x2(
        'dixon_coles',
        registro.get('dc_1', 0),
        registro.get('dc_X', 0),
        registro.get('dc_2', 0),
        resultado_real['resultado_1x2']
    )
    
    registro['mc_acierto'] = calcular_acierto_1x2(
        'monte_carlo',
        registro.get('mc_1', 0),
        registro.get('mc_X', 0),
        registro.get('mc_2', 0),
        resultado_real['resultado_1x2']
    )
    
    # Forma reciente: acierta si el equipo con mejor forma ganó
    forma_local = registro.get('forma_local_pct', 0)
    forma_visitante = registro.get('forma_visitante_pct', 0)
    
    if forma_local > forma_visitante:
        pred_forma = '1'
    elif forma_visitante > forma_local:
        pred_forma = '2'
    else:
        pred_forma = 'X'
    
    registro['forma_acierto'] = (pred_forma == resultado_real['resultado_1x2'])
    
    # Acierto final (predicción combinada)
    registro['acierto'] = (
        registro['prediccion_final'] == resultado_real['resultado_1x2']
    )
    
    return registro


def resumen_rendimiento(historial: List[Dict]) -> str:
    """Genera un resumen de rendimiento en texto."""
    if not historial:
        return "No hay predicciones para analizar."
    
    analisis = analizar_modelos(historial)
    
    total = len(historial)
    aciertos = sum(1 for p in historial if p.get('acierto'))
    pct_general = round(aciertos / total * 100, 1) if total > 0 else 0
    
    lines = [
        f"📊 RESUMEN DE RENDIMIENTO",
        f"=" * 40,
        f"Total predicciones: {total}",
        f"Aciertos: {aciertos}",
        f"% General: {pct_general}%",
        f"",
        f"POR MODELO:",
        f"-" * 40,
    ]
    
    for modelo, datos in analisis.get('modelos', {}).items():
        nombre = modelo.replace('_', ' ').title()
        pct = datos.get('porcentaje', 0)
        total_m = datos.get('total', 0)
        rec = analisis.get('recomendaciones', {}).get(modelo, '')
        lines.append(f"{nombre}: {pct}% ({total_m} preds) {rec}")
    
    lines.extend([
        f"",
        f"PESOS ACTUALES vs RECOMENDADOS:",
        f"-" * 40,
    ])
    
    cambios = analisis.get('cambios_pesos', {})
    pesos = analisis.get('pesos_recomendados', {})
    
    for modelo in ['poisson', 'dixon_coles', 'monte_carlo', 'forma_reciente', 'estilo_juego']:
        nombre = modelo.replace('_', ' ').title()
        actual = analisis.get('pesos_actuales', {}).get(modelo, 0)
        nuevo = pesos.get(modelo, 0)
        cambio = cambios.get(modelo, 0)
        
        flecha = "↑" if cambio > 0 else ("↓" if cambio < 0 else "=")
        lines.append(f"{nombre}: {actual:.0%} → {nuevo:.0%} ({flecha}{abs(cambio):.0%})")
    
    return "\n".join(lines)
