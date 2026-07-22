"""
Scorpion Elite - Sistema de Calibracion Constante
=================================================
Ajusta lambdas y predicciones segun resultados reales.
Funciona para: 1X2, Over/Under, BTTS, Corners
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime

CALIBRATION_FILE = "/tmp/scorpion_calibration.json"


def cargar_calibracion() -> Dict:
    if os.path.exists(CALIBRATION_FILE):
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"equipos": {}, "historico": []}


def guardar_calibracion(data: Dict):
    try:
        with open(CALIBRATION_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error guardando calibracion: {e}")


def registrar_resultado(
    equipo_local: str,
    equipo_visitante: str,
    lambda_local_predicha: float,
    lambda_visitante_predicha: float,
    goles_local_real: int,
    goles_visitante_real: int,
    predicciones: Dict,  # Todas las predicciones del analisis
    resultado_real: Optional[str] = None,  # Resultado 1X2
    marcador: Optional[str] = None,  # Marcador "2-1"
    confianza: int = 0,
    rango: str = "D"
):
    """
    Registra el resultado completo de un analisis.
    
    predicciones = {
        '1x2': {'pick': '1', 'prob': 55.0},
        'over_under': {'pick': 'Over 2.5', 'prob': 60.0},
        'btts': {'pick': 'Si', 'prob': 50.0},
        'corners': {'pick': 'Over 10.5', 'prob': 55.0}
    }
    """
    data = cargar_calibracion()
    equipo_local_norm = equipo_local.lower().strip()
    equipo_visitante_norm = equipo_visitante.lower().strip()
    
    # Calcular errores de goles
    error_local = goles_local_real - lambda_local_predicha
    error_visitante = goles_visitante_real - lambda_visitante_predicha
    
    # Determinar resultados reales
    total_goles = goles_local_real + goles_visitante_real
    ambos_marcan = goles_local_real > 0 and goles_visitante_real > 0
    
    # Evaluar cada prediccion
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
    
    # Corners (estimado - necesita mas datos)
    resultados_evaluados['corners'] = {
        'prediccion': predicciones.get('corners', {}).get('pick', ''),
        'resultado_real': marcador if marcador else str(goles_local_real + goles_visitante_real),
        'acertado': None  # Se determina despues si hay datos de corners
    }
    
    registro = {
        "fecha": datetime.now().isoformat(),
        "equipo_local": equipo_local,
        "equipo_visitante": equipo_visitante,
        "lambda_local_predicha": lambda_local_predicha,
        "lambda_visitante_predicha": lambda_visitante_predicha,
        "goles_local_real": goles_local_real,
        "goles_visitante_real": goles_visitante_real,
        "error_local": error_local,
        "error_visitante": error_visitante,
        "marcador": marcador,
        "confianza": confianza,
        "rango": rango,
        "resultados": resultados_evaluados,
        "acertado_1x2": resultados_evaluados.get('1x2', {}).get('acertado'),
        "acertado_ou25": resultados_evaluados.get('ou25', {}).get('acertado'),
        "acertado_btts": resultados_evaluados.get('btts', {}).get('acertado')
    }
    
    data["historico"].append(registro)
    
    if len(data["historico"]) > 200:
        data["historico"] = data["historico"][-200:]
    
    # Actualizar factores de correccion
    _actualizar_factor_equipo(data, equipo_local_norm, error_local, es_local=True)
    _actualizar_factor_equipo(data, equipo_visitante_norm, error_visitante, es_local=False)
    
    guardar_calibracion(data)
    
    return {
        "error_local": error_local,
        "error_visitante": error_visitante,
        "resultados_evaluados": resultados_evaluados
    }


def _actualizar_factor_equipo(data: Dict, equipo: str, error: float, es_local: bool):
    if equipo not in data["equipos"]:
        data["equipos"][equipo] = {
            "nombre_original": equipo,
            "factor_local": 1.0,
            "factor_visitante": 1.0,
            "factor_over": 1.0,
            "factor_btts": 1.0,
            "partidos_local": 0,
            "partidos_visitante": 0,
            "errores_local": [],
            "errores_visitante": [],
            "over_real": [],
            "over_predicho": []
        }
    
    equipo_data = data["equipos"][equipo]
    clave_error = "errores_local" if es_local else "errores_visitante"
    clave_factor = "factor_local" if es_local else "factor_visitante"
    clave_partidos = "partidos_local" if es_local else "partidos_visitante"
    
    equipo_data[clave_error].append(error)
    equipo_data[clave_partidos] += 1
    
    if len(equipo_data[clave_error]) > 10:
        equipo_data[clave_error] = equipo_data[clave_error][-10:]
    
    errores = equipo_data[clave_error]
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
    nuevo_factor = equipo_data[clave_factor] + ajuste
    equipo_data[clave_factor] = max(0.7, min(1.5, nuevo_factor))


def obtener_factor_correccion(equipo: str, como_local: bool) -> float:
    data = cargar_calibracion()
    equipo_norm = equipo.lower().strip()
    
    if equipo_norm in data["equipos"]:
        equipo_data = data["equipos"][equipo_norm]
        if como_local:
            return equipo_data.get("factor_local", 1.0)
        else:
            return equipo_data.get("factor_visitante", 1.0)
    
    return 1.0


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
    data = cargar_calibracion()
    total_picks = len(data["historico"])
    
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
    
    # Contar aciertos por tipo
    aciertos_1x2 = sum(1 for h in data["historico"] if h.get("acertado_1x2") == True)
    aciertos_ou25 = sum(1 for h in data["historico"] if h.get("acertado_ou25") == True)
    aciertos_btts = sum(1 for h in data["historico"] if h.get("acertado_btts") == True)
    
    # Contar total evaluados
    total_1x2 = sum(1 for h in data["historico"] if h.get("acertado_1x2") is not None)
    total_ou25 = total_picks  # Siempre se evalua
    total_btts = total_picks  # Siempre se evalua
    
    return {
        "total_picks": total_picks,
        "aciertos_1x2": aciertos_1x2,
        "aciertos_ou25": aciertos_ou25,
        "aciertos_btts": aciertos_btts,
        "porcentaje_1x2": round(aciertos_1x2 / total_1x2 * 100, 1) if total_1x2 > 0 else 0,
        "porcentaje_ou25": round(aciertos_ou25 / total_ou25 * 100, 1) if total_ou25 > 0 else 0,
        "porcentaje_btts": round(aciertos_btts / total_btts * 100, 1) if total_btts > 0 else 0,
        "equipos_calibrados": len(data["equipos"]),
        "historico": data["historico"][-30:]
    }


def resetear_calibracion():
    if os.path.exists(CALIBRATION_FILE):
        os.remove(CALIBRATION_FILE)
    return {"status": "ok", "mensaje": "Calibracion reseteada"}


def get_predicciones_calibradas(
    predicciones_base: Dict,
    lambda_local: float,
    lambda_visitante: float,
    equipo_local: str,
    equipo_visitante: str
) -> Dict:
    """
    Ajusta todas las predicciones basandose en la calibracion.
    """
    # Obtener factores de correccion
    factor_local = obtener_factor_correccion(equipo_local, como_local=True)
    factor_visitante = obtener_factor_correccion(equipo_visitante, como_local=False)
    
    # Calcular lambda ajustada
    lambda_local_ajustada = lambda_local * factor_local
    lambda_visitante_ajustada = lambda_visitante * factor_visitante
    
    # Ajustar total de goles esperados
    goles_esperados_original = lambda_local + lambda_visitante
    goles_esperados_ajustados = lambda_local_ajustada + lambda_visitante_ajustada
    
    # Recalcular Over/Under basado en nueva expectativa
    ou_ajustado = {}
    if goles_esperados_original > 0:
        ratio_ajuste = goles_esperados_ajustados / goles_esperados_original
        
        # Ajustar probabilidades de Over/Under
        ou_base = predicciones_base.get('over_under', {})
        over_prob = ou_base.get('over_25', 50)
        
        # Si esperamos mas goles, Over es mas probable
        ajuste_over = (ratio_ajuste - 1) * 50  # Maximo +-50%
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
