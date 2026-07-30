"""
Scorpion Elite - Sistema de Calibracion Constante
=================================================
Ajusta lambdas y predicciones segun resultados reales.
Funciona para: 1X2, Over/Under, BTTS, Corners

Usa Supabase como backend para persistencia.
"""

import logging
import unicodedata
from typing import Dict, List, Optional
from datetime import datetime

try:
    from supabase import create_client
    SUPABASE_URL = "https://jjtifureeygvygxtpuku.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJleWV5Z3Z5Z3RwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEyMjg2NjYsImV4cCI6MjA2NjgwNDY2Nn0.W_Xr6q7NNd9P3BkQqA1q5YXr2t6Q9L0z0xL8mZP3k7Y"
    
    _client = None
    
    def _get_client():
        global _client
        if _client is None:
            _client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return _client
except ImportError:
    _get_client = None

logger = logging.getLogger(__name__)


def normalizar_equipo(nombre: str) -> str:
    """Normaliza nombre de equipo: lowercase, sin acentos, sin espacios extra."""
    if not nombre:
        return ""
    # Normalizar Unicode (quitar acentos)
    nombre = unicodedata.normalize('NFKD', nombre).encode('ASCII', 'ignore').decode('ASCII')
    # Lowercase y strip
    nombre = nombre.lower().strip()
    # Quitar espacios múltiples
    nombre = ' '.join(nombre.split())
    return nombre


def obtener_factor_correccion(equipo: str, como_local: bool) -> float:
    """Obtiene el factor de corrección para un equipo desde Supabase."""
    try:
        client = _get_client()
        equipo_norm = normalizar_equipo(equipo)
        
        resp = client.table('calibracion_equipos').select('*').eq('equipo_norm', equipo_norm).execute()
        
        if resp.data and len(resp.data) > 0:
            equipo_data = resp.data[0]
            if como_local:
                return float(equipo_data.get("factor_local", 1.0))
            else:
                return float(equipo_data.get("factor_visitante", 1.0))
    except Exception as e:
        logger.warning(f"Error obteniendo factor de corrección: {e}")
    
    return 1.0


def _actualizar_factor_equipo(equipo: str, error: float, es_local: bool, nombre_original: str = None):
    """Actualiza el factor de corrección para un equipo en Supabase."""
    try:
        client = _get_client()
        equipo_norm = normalizar_equipo(equipo)
        
        # Obtener datos actuales
        resp = client.table('calibracion_equipos').select('*').eq('equipo_norm', equipo_norm).execute()
        
        if resp.data and len(resp.data) > 0:
            equipo_data = resp.data[0]
            errores_local = equipo_data.get('errores_local', [])
            errores_visitante = equipo_data.get('errores_visitante', [])
            factor_local = float(equipo_data.get('factor_local', 1.0))
            factor_visitante = float(equipo_data.get('factor_visitante', 1.0))
            partidos_local = int(equipo_data.get('partidos_local', 0))
            partidos_visitante = int(equipo_data.get('partidos_visitante', 0))
        else:
            # Crear nuevo
            errores_local = []
            errores_visitante = []
            factor_local = 1.0
            factor_visitante = 1.0
            partidos_local = 0
            partidos_visitante = 0
        
        # Actualizar errores y factores
        if es_local:
            errores_local.append(error)
            if len(errores_local) > 10:
                errores_local = errores_local[-10:]
            partidos_local += 1
            errores = errores_local
            factor = factor_local
        else:
            errores_visitante.append(error)
            if len(errores_visitante) > 10:
                errores_visitante = errores_visitante[-10:]
            partidos_visitante += 1
            errores = errores_visitante
            factor = factor_visitante
        
        # Calcular error ponderado
        peso = 1.0
        error_ponderado = 0
        suma_pesos = 0
        for err in reversed(errores):
            error_ponderado += err * peso
            suma_pesos += peso
            peso *= 0.85
        
        error_promedio = error_ponderado / suma_pesos if suma_pesos > 0 else 0
        cambio_max = 0.1
        ajuste = max(-cambio_max, min(cambio_max, error_promedio * 0.3))
        nuevo_factor = factor + ajuste
        nuevo_factor = max(0.7, min(1.5, nuevo_factor))
        
        # Guardar
        data = {
            'equipo_norm': equipo_norm,
            'nombre_original': nombre_original or equipo,
            'factor_local': nuevo_factor if es_local else factor_local,
            'factor_visitante': nuevo_factor if not es_local else factor_visitante,
            'factor_over': 1.0,
            'factor_btts': 1.0,
            'partidos_local': partidos_local,
            'partidos_visitante': partidos_visitante,
            'errores_local': errores_local,
            'errores_visitante': errores_visitante,
            'actualizado_en': datetime.now().isoformat()
        }
        
        client.table('calibracion_equipos').upsert(data, on_conflict='equipo_norm').execute()
    except Exception as e:
        logger.error(f"Error actualizando factor de equipo: {e}")


def registrar_resultado(
    equipo_local: str,
    equipo_visitante: str,
    lambda_local_predicha: float,
    lambda_visitante_predicha: float,
    goles_local_real: int,
    goles_visitante_real: int,
    predicciones: Dict,
    resultado_real: Optional[str] = None,
    marcador: Optional[str] = None,
    confianza: int = 0,
    rango: str = "D",
    corners_local_real: Optional[int] = None,
    corners_visitante_real: Optional[int] = None
):
    """
    Registra el resultado completo de un analisis en Supabase.
    """
    try:
        client = _get_client()
        
        # Calcular errores
        error_local = goles_local_real - lambda_local_predicha
        error_visitante = goles_visitante_real - lambda_visitante_predicha
        
        # Determinar resultados reales
        total_goles = goles_local_real + goles_visitante_real
        ambos_marcan = goles_local_real > 0 and goles_visitante_real > 0
        
        # Evaluar predicciones
        resultados_evaluados = {}
        
        # 1X2
        if resultado_real:
            resultados_evaluados['1x2'] = {
                'prediccion': predicciones.get('1x2', {}).get('pick', ''),
                'resultado_real': resultado_real,
                'acertado': predicciones.get('1x2', {}).get('pick', '') == resultado_real
            }
        
        # Over/Under 2.5
        resultados_evaluados['ou25'] = {
            'prediccion': predicciones.get('over_under', {}).get('pick', ''),
            'resultado_real': f"{'Over' if total_goles > 2.5 else 'Under'} 2.5",
            'acertado': ('Over' in predicciones.get('over_under', {}).get('pick', '') and total_goles > 2.5) or
                        ('Under' in predicciones.get('over_under', {}).get('pick', '') and total_goles <= 2.5)
        }
        
        # BTTS
        resultados_evaluados['btts'] = {
            'prediccion': predicciones.get('btts', {}).get('pick', ''),
            'resultado_real': 'Si' if ambos_marcan else 'No',
            'acertado': ('Si' in predicciones.get('btts', {}).get('pick', '') and ambos_marcan) or
                        ('No' in predicciones.get('btts', {}).get('pick', '') and not ambos_marcan)
        }
        
        # Corners
        if corners_local_real is not None and corners_visitante_real is not None:
            total_corners_real = corners_local_real + corners_visitante_real
            pick_corners = predicciones.get('corners', {}).get('pick', '')
            if 'Over' in pick_corners:
                acertado_corners = total_corners_real > 9.5
            elif 'Under' in pick_corners:
                acertado_corners = total_corners_real <= 9.5
            else:
                acertado_corners = None
            resultados_evaluados['corners'] = {
                'prediccion': pick_corners,
                'resultado_real': total_corners_real,
                'acertado': acertado_corners
            }
        else:
            resultados_evaluados['corners'] = {
                'prediccion': predicciones.get('corners', {}).get('pick', ''),
                'resultado_real': str(total_goles),
                'acertado': None
            }
        
        # Guardar histórico
        historico_data = {
            'fecha': datetime.now().isoformat(),
            'equipo_local': equipo_local,
            'equipo_visitante': equipo_visitante,
            'lambda_local_predicha': lambda_local_predicha,
            'lambda_visitante_predicha': lambda_visitante_predicha,
            'goles_local_real': goles_local_real,
            'goles_visitante_real': goles_visitante_real,
            'resultados': resultados_evaluados,
            'acertado_1x2': resultados_evaluados.get('1x2', {}).get('acertado'),
            'acertado_ou25': resultados_evaluados.get('ou25', {}).get('acertado'),
            'acertado_btts': resultados_evaluados.get('btts', {}).get('acertado'),
            'confianza': confianza,
            'rango': rango
        }
        client.table('calibracion_historico').insert(historico_data).execute()
        
        # Actualizar factores de equipos
        _actualizar_factor_equipo(equipo_local, error_local, es_local=True, nombre_original=equipo_local)
        _actualizar_factor_equipo(equipo_visitante, error_visitante, es_local=False, nombre_original=equipo_visitante)
        
        return {
            "error_local": error_local,
            "error_visitante": error_visitante,
            "resultados_evaluados": resultados_evaluados
        }
    except Exception as e:
        logger.error(f"Error registrando resultado: {e}")
        return {
            "error_local": error_local if 'error_local' in dir() else 0,
            "error_visitante": error_visitante if 'error_visitante' in dir() else 0,
            "resultados_evaluados": {}
        }


def ajustar_lambda(lambda_original: float, factor: float) -> float:
    return lambda_original * factor


def get_lambda_ajustada(equipo: str, lambda_original: float, como_local: bool) -> Dict:
    factor = obtener_factor_correccion(equipo, como_local)
    lambda_ajustada = ajustar_lambda(lambda_original, factor)
    
    return {
        "equipo": equipo,
        "lambda_original": lambda_original,
        "lambda_ajustada": round(lambda_ajustada, 2),
        "factor": round(factor, 3),
        "ajuste": "sube" if factor > 1 else ("baja" if factor < 1 else "sin_cambio"),
        "como_local": como_local
    }


def obtener_estadisticas_calibracion() -> Dict:
    """Obtiene estadísticas de calibración desde Supabase."""
    try:
        client = _get_client()
        
        # Obtener histórico (últimos 200 registros)
        resp_historico = client.table('calibracion_historico').select('*').order('fecha', desc=True).limit(200).execute()
        historico = resp_historico.data if resp_historico.data else []
        
        # Obtener equipos calibrados
        resp_equipos = client.table('calibracion_equipos').select('equipo_norm').execute()
        equipos_calibrados = len(resp_equipos.data) if resp_equipos.data else 0
        
        total_picks = len(historico)
        
        if total_picks == 0:
            return {
                "total_picks": 0,
                "aciertos_1x2": 0,
                "aciertos_ou25": 0,
                "aciertos_btts": 0,
                "porcentaje_1x2": 0,
                "porcentaje_ou25": 0,
                "porcentaje_btts": 0,
                "equipos_calibrados": 0,
                "mensaje": "No hay datos aun"
            }
        
        # Contar aciertos
        aciertos_1x2 = sum(1 for h in historico if h.get("acertado_1x2") == True)
        aciertos_ou25 = sum(1 for h in historico if h.get("acertado_ou25") == True)
        aciertos_btts = sum(1 for h in historico if h.get("acertado_btts") == True)
        
        total_1x2 = sum(1 for h in historico if h.get("acertado_1x2") is not None)
        
        return {
            "total_picks": total_picks,
            "aciertos_1x2": aciertos_1x2,
            "aciertos_ou25": aciertos_ou25,
            "aciertos_btts": aciertos_btts,
            "porcentaje_1x2": round(aciertos_1x2 / total_1x2 * 100, 1) if total_1x2 > 0 else 0,
            "porcentaje_ou25": round(aciertos_ou25 / total_picks * 100, 1) if total_picks > 0 else 0,
            "porcentaje_btts": round(aciertos_btts / total_picks * 100, 1) if total_picks > 0 else 0,
            "equipos_calibrados": equipos_calibrados,
            "historico": historico[:30]
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de calibración: {e}")
        return {
            "total_picks": 0,
            "aciertos_1x2": 0,
            "aciertos_ou25": 0,
            "aciertos_btts": 0,
            "porcentaje_1x2": 0,
            "porcentaje_ou25": 0,
            "porcentaje_btts": 0,
            "equipos_calibrados": 0,
            "mensaje": f"Error: {e}"
        }


def resetear_calibracion():
    """Borra todos los datos de calibración en Supabase."""
    try:
        client = _get_client()
        client.table('calibracion_equipos').delete().neq('id', 0).execute()
        client.table('calibracion_historico').delete().neq('id', 0).execute()
        return {"status": "ok", "mensaje": "Calibración reseteada en Supabase"}
    except Exception as e:
        logger.error(f"Error reseteando calibración: {e}")
        return {"status": "error", "mensaje": str(e)}


def get_predicciones_calibradas(
    predicciones_base: Dict,
    lambda_local: float,
    lambda_visitante: float,
    equipo_local: str,
    equipo_visitante: str
) -> Dict:
    """Ajusta predicciones basándose en la calibración."""
    factor_local = obtener_factor_correccion(equipo_local, como_local=True)
    factor_visitante = obtener_factor_correccion(equipo_visitante, como_local=False)
    
    lambda_local_ajustada = lambda_local * factor_local
    lambda_visitante_ajustada = lambda_visitante * factor_visitante
    
    goles_esperados_original = lambda_local + lambda_visitante
    goles_esperados_ajustados = lambda_local_ajustada + lambda_visitante_ajustada
    
    ou_ajustado = {}
    if goles_esperados_original > 0:
        ratio_ajuste = goles_esperados_ajustados / goles_esperados_original
        ou_base = predicciones_base.get('over_under', {})
        over_prob = ou_base.get('over_25', 50)
        ajuste_over = (ratio_ajuste - 1) * 50
        over_prob_ajustado = min(95, max(5, over_prob + ajuste_over))
        
        ou_ajustado = {
            'over_25': round(over_prob_ajustado, 1),
            'under_25': round(100 - over_prob_ajustado, 1),
            'pick': 'Over 2.5' if over_prob_ajustado > 50 else 'Under 2.5'
        }
    
    return {
        "lambda_local_original": lambda_local,
        "lambda_local_ajustada": round(lambda_local_ajustada, 2),
        "lambda_visitante_original": lambda_visitante,
        "lambda_visitante_ajustada": round(lambda_visitante_ajustada, 2),
        "factor_local": round(factor_local, 3),
        "factor_visitante": round(factor_visitante, 3),
        "over_under_ajustado": ou_ajustado
    }
