"""Funciones auxiliares."""
import re
from datetime import date, datetime
from typing import Optional


def limpiar_nombre(nombre: str) -> str:
    """
    Limpia sufijos de ciudad/país de nombres de equipos.
    
    Args:
        nombre: Nombre del equipo.
        
    Returns:
        Nombre limpio.
    """
    nombre = re.sub(r"-\s*[A-Z]{2,3}$", "", nombre.strip())
    nombre = re.sub(r"\s*\([^)]+\)", "", nombre)
    return nombre.strip(" .-")


def formatear_fecha(fecha: date, formato: str = "%d/%m/%Y") -> str:
    """
    Formatea una fecha.
    
    Args:
        fecha: Fecha a formatear.
        formato: Formato strftime.
        
    Returns:
        Fecha formateada como string.
    """
    if isinstance(fecha, str):
        try:
            fecha = date.fromisoformat(fecha)
        except ValueError:
            return fecha
    return fecha.strftime(formato)


def es_seleccion(nombre: str) -> bool:
    """Verifica si es nombre de selección."""
    selecciones = {
        "argentina", "brasil", "francia", "espana", "portugal",
        "inglaterra", "italia", "alemania", "belgica", "croacia",
        "holanda", "uruguay", "colombia", "chile", "mexico",
        "japon", "marruecos", "senegal", "australia", "suiza",
        "dinamarca", "polonia", "austria", "turquia", "serbia",
    }
    return any(s in nombre.lower() for s in selecciones)


def calcular_kelly(cuota: float, probabilidad: float) -> float:
    """
    Calcula el criterio de Kelly para apuesta óptima.
    
    Args:
        cuota: Cuota decimales de la apuesta.
        probabilidad: Probabilidad estimada (0-100).
        
    Returns:
        Porcentaje óptimo del bankroll (0-100).
    """
    if probabilidad <= 0 or cuota <= 1:
        return 0.0
    p = probabilidad / 100
    b = cuota - 1
    q = 1 - p
    kelly = (b * p - q) / b
    # Kelly conservador (1/4)
    return max(0, round(kelly * 25, 2))
