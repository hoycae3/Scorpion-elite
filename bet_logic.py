"""Lógica pura de evaluación de apuestas y resultados de partidos.

Extraída de elite.py para reducir el monolito. Estas funciones no dependen
del estado de Streamlit; las dos primeras son puras (testables sin mocks).
"""
import logging

logger = logging.getLogger(__name__)


def calcular_resultados_partido(score_local, score_visitante):
    """Calcula los resultados reales (1X2, O/U, BTTS) de un partido finalizado."""
    total_goles = score_local + score_visitante
    if score_local > score_visitante:
        resultado_real = "1"
    elif score_local < score_visitante:
        resultado_real = "2"
    else:
        resultado_real = "X"
    resultado_ou_real = "Over 2.5" if total_goles > 2.5 else "Under 2.5"
    btts_real = "Si" if (score_local > 0 and score_visitante > 0) else "No"
    return resultado_real, resultado_ou_real, btts_real


def evaluar_over_under(prediccion, real, linea_default):
    """Evalua si un pick Over/Under acerto comparando con el valor real."""
    if not prediccion or real is None:
        return False
    pred_lower = str(prediccion).lower()
    if 'over' in pred_lower:
        return real > linea_default
    if 'under' in pred_lower:
        return real < linea_default
    return False


def apuesta_ganada(apuesta, pick, resultado_real, resultado_ou_real, btts_real, stats_reales=None):
    """Determina si una apuesta del bankroll fue ganada según el mercado apostado.

    Evalúa EXPLÍCITAMENTE por mercado y soporta alias (Over/Under y O/U son
    el mismo mercado; la UI manual usa 'Over/Under', Capital usa 'O/U').
    Sin esto, apuestas manuales de Over/Under nunca se evaluaban y las
    de mercados especiales (Corners etc.) caían en fallback por goles."""
    mercado = apuesta.get('mercado', '')
    if mercado == '1X2':
        return pick.get('prediccion_1x2') == resultado_real
    if mercado in ('O/U', 'Over/Under'):
        return pick.get('prediccion_ou', '') == resultado_ou_real
    if mercado == 'BTTS':
        return pick.get('prediccion_btts', '') == btts_real
    if stats_reales:
        if mercado == 'Corners':
            pred = pick.get('prediccion_corners', '')
            real = stats_reales.get('corners_total', 0)
            return evaluar_over_under(pred, real, 9.5)
        if mercado == 'Tarjetas':
            pred = pick.get('prediccion_tarjetas', '')
            real = stats_reales.get('tarjetas_total', 0)
            return evaluar_over_under(pred, real, 6)
        if mercado == 'Remates':
            pred = pick.get('prediccion_remates', '')
            real = stats_reales.get('remates_total', 0)
            return evaluar_over_under(pred, real, 24)
        if mercado == 'Tiros Arco':
            pred = pick.get('prediccion_arco', '')
            real = stats_reales.get('tiros_arco_total', 0)
            return evaluar_over_under(pred, real, 8)
    return False


def actualizar_bankroll_apuestas(client, fix_id, pick, resultado_real, resultado_ou_real, btts_real, stats_reales=None):
    """Marca apuestas del bankroll como ganadas/perdidas para un fixture."""
    apuestas = client.table('bankroll_apuestas').select('*').eq('fixture_id', fix_id).execute()
    if not apuestas.data:
        return
    for apuesta in apuestas.data:
        apuesta_id = apuesta.get('id')
        cantidad = apuesta.get('cantidad', 0)
        cuota = apuesta.get('cuota', 2.0)
        gano = apuesta_ganada(apuesta, pick, resultado_real, resultado_ou_real, btts_real, stats_reales)
        ganancia = cantidad * (cuota - 1) if gano else -cantidad
        client.table('bankroll_apuestas').update({
            'resultado': gano,
            'ganancia': ganancia
        }).eq('id', apuesta_id).execute()
