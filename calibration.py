"""
Scorpion Elite - Sistema de Calibracion Constante
=================================================
Ajusta las lambdas segun resultados reales.
"""

import json
import os
from typing import Dict
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
    prediccion: str,
    resultado_real: str,
    confianza: int,
    rango: str
):
    data = cargar_calibracion()
    equipo_local_norm = equipo_local.lower().strip()
    equipo_visitante_norm = equipo_visitante.lower().strip()
    
    error_local = goles_local_real - lambda_local_predicha
    error_visitante = goles_visitante_real - lambda_visitante_predicha
    
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
        "prediccion": prediccion,
        "resultado_real": resultado_real,
        "acertado": prediccion == resultado_real,
        "confianza": confianza,
        "rango": rango
    }
    data["historico"].append(registro)
    
    if len(data["historico"]) > 100:
        data["historico"] = data["historico"][-100:]
    
    _actualizar_factor_equipo(data, equipo_local_norm, error_local, es_local=True)
    _actualizar_factor_equipo(data, equipo_visitante_norm, error_visitante, es_local=False)
    
    guardar_calibracion(data)
    
    return {
        "error_local": error_local,
        "error_visitante": error_visitante,
        "factor_local": data["equipos"].get(equipo_local_norm, {}).get("factor_local", 1.0),
        "factor_visitante": data["equipos"].get(equipo_visitante_norm, {}).get("factor_visitante", 1.0)
    }


def _actualizar_factor_equipo(data: Dict, equipo: str, error: float, es_local: bool):
    if equipo not in data["equipos"]:
        data["equipos"][equipo] = {
            "nombre_original": equipo,
            "factor_local": 1.0,
            "factor_visitante": 1.0,
            "partidos_local": 0,
            "partidos_visitante": 0,
            "errores_local": [],
            "errores_visitante": []
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
        "ajuste": "subio" if factor > 1 else ("bajo" if factor < 1 else "sin_cambio"),
        "como_local": como_local
    }


def obtener_estadisticas_calibracion() -> Dict:
    data = cargar_calibracion()
    total_picks = len(data["historico"])
    
    if total_picks == 0:
        return {
            "total_picks": 0,
            "aciertos": 0,
            "porcentaje_acierto": 0,
            "equipos_calibrados": 0,
            "mensaje": "No hay datos de calibracion aun"
        }
    
    aciertos = sum(1 for h in data["historico"] if h.get("acertado", False))
    
    return {
        "total_picks": total_picks,
        "aciertos": aciertos,
        "fallos": total_picks - aciertos,
        "porcentaje_acierto": round(aciertos / total_picks * 100, 1),
        "equipos_calibrados": len(data["equipos"]),
        "historico": data["historico"][-20:]
    }


def resetear_calibracion():
    if os.path.exists(CALIBRATION_FILE):
        os.remove(CALIBRATION_FILE)
    return {"status": "ok", "mensaje": "Calibracion reseteada"}
