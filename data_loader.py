"""
Scorpion Elite - Cargador de datos
Procesa volcados de datos y normaliza equipos/ligas
"""
import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Tuple

# Mapeo de ligas a códigos
LIGA_MAP = {
    'brasileirao': 'BRA_A',
    'brasileirão': 'BRA_A',
    'serie a brasil': 'BRA_A',
    'brasileirao serie b': 'BRA_B',
    'brasileirão serie b': 'BRA_B',
    'serie b brasil': 'BRA_B',
    'premier league': 'ENG_PL',
    'premier league inglaterra': 'ENG_PL',
    'la liga': 'ESP_LL',
    'laliga': 'ESP_LL',
    'bundesliga': 'GER_BL',
    'serie a': 'ITA_SA',
    'ligue 1': 'FRA_L1',
    'liga mx': 'MEX_LM',
    'liga mx - apertura': 'MEX_LM',
    'liga argentina': 'ARG_LA',
    'liga profesional argentina': 'ARG_LA',
    'copa argentina': 'ARG_CA',
    'mls': 'USA_MLS',
    'copa libertadores': 'CONM_CL',
    'copa sudamericana': 'CONM_CS',
    'champions league': 'UEFA_CL',
    'eurocopa': 'UEFA_EC',
    'copa america': 'CONMEB_CA',
    'mundial': 'FIFA_WC',
    'world cup': 'FIFA_WC',
}

# Mapeo de países
PAIS_MAP = {
    'brasil': 'Brasil',
    'brazil': 'Brasil',
    'inglaterra': 'Inglaterra',
    'england': 'Inglaterra',
    'espana': 'España',
    'spain': 'España',
    'alemania': 'Alemania',
    'germany': 'Alemania',
    'italia': 'Italia',
    'italy': 'Italia',
    'francia': 'Francia',
    'france': 'Francia',
    'argentina': 'Argentina',
    'mexico': 'México',
    'usa': 'Estados Unidos',
    'estados unidos': 'Estados Unidos',
    'colombia': 'Colombia',
    'chile': 'Chile',
    'peru': 'Perú',
    'paraguay': 'Paraguay',
    'uruguay': 'Uruguay',
    'venezuela': 'Venezuela',
    'ecuador': 'Ecuador',
    'bolivia': 'Bolivia',
}

# Mapeo de países a ligas por defecto
PAIS_LIGA_DEFAULT = {
    'México': 'Liga MX, Apertura',
    'Brasil': 'Brasileirão',
    'Argentina': 'Liga Profesional Argentina',
    'Colombia': 'Primera A - Clausura',
    'Chile': 'Primera División',
    'Perú': 'Liga 1',
    'Uruguay': 'Primera División',
    'Paraguay': 'Primera División',
    'Ecuador': 'Liga Pro',
    'Venezuela': 'Primera División',
    'Estados Unidos': 'MLS',
}


def parse_date_from_header(text: str) -> str:
    """Extrae fecha del header (ej: 'Hoy - 18.07.' → 2026-07-18)"""
    # Buscar patrón de fecha
    patterns = [
        r'(\d{1,2})\.(\d{2})',  # 18.07
        r'(\d{1,2})/(\d{2})',   # 18/07
        r'(\d{1,2})-(\d{2})',    # 18-07
    ]
    
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            day = int(match.group(1))
            month = int(match.group(2))
            
            # Ajustar año si el mes es mayor al actual (año anterior)
            year = current_year
            if month > current_month:
                year = current_year - 1
            
            return f"{year}-{month:02d}-{day:02d}"
    
    return datetime.now().strftime("%Y-%m-%d")


def split_duplicate_team(text: str) -> str:
    """
    Divide texto de equipo duplicado.
    Ej: 'CriciúmaCriciúma' → 'Criciúma'
    Ej: 'Sport RecifeSport Recife' → 'Sport Recife'
    """
    if not text or len(text) < 2:
        return text
    
    text = text.strip()
    length = len(text)
    
    # Si la longitud es par, comparar mitades
    if length % 2 == 0:
        half = length // 2
        first_half = text[:half]
        second_half = text[half:]
        
        # Si son idénticas, devolver una
        if first_half == second_half:
            return first_half
        
        # Si la segunda mitad empieza como la primera (diferencia menor)
        if second_half.startswith(first_half):
            return first_half
        
        # Buscar el punto medio natural (donde se repite)
        # Ej: "Sport Recife" + "Sport Recife" = "Sport RecifeSport Recife"
        for i in range(1, half):
            if text[:i] == text[i:i*2]:
                return text[:i]
    
    # Intentar por palabras
    words = text.split()
    if len(words) >= 2:
        mid = len(words) // 2
        first_part = ' '.join(words[:mid])
        second_part = ' '.join(words[mid:])
        
        if first_part == second_part:
            return first_part
        
        # Si la segunda parte empieza con la primera
        if second_part.startswith(first_part):
            return first_part
    
    return text


def clean_team_name(text: str) -> str:
    """Limpia el nombre de un equipo"""
    if not text:
        return ""
    
    text = text.strip()
    
    # Eliminar caracteres especiales al inicio/final
    text = re.sub(r'^[\s\-\–\—]+|[\s\-\–\—]+$', '', text)
    
    # Dividir si está duplicado
    text = split_duplicate_team(text)
    
    return text


def get_league_code(liga: str) -> str:
    """Obtiene el código de liga"""
    if not liga:
        return 'OTHER'
    
    liga_lower = liga.lower().strip()
    
    for key, code in LIGA_MAP.items():
        if key in liga_lower:
            return code
    
    return 'OTHER'


def get_pais_normalizado(pais: str) -> str:
    """Normaliza el nombre del país"""
    if not pais:
        return 'Other'
    
    pais_lower = pais.lower().strip()
    
    # Quitar los dos puntos del final
    pais_lower = pais_lower.rstrip(':').strip()
    
    # Ignorar "sudamérica" o "america del sur"
    if 'sudam' in pais_lower or 'am' in pais_lower.replace(' ', '')[:5]:
        return ""  # No es un país, retornar vacío para buscar en los equipos
    
    for key, value in PAIS_MAP.items():
        if key in pais_lower:
            return value
    
    # Capitalizar primera letra
    return pais_lower.capitalize()


def extract_pais_from_team(team_name: str) -> str:
    """Extrae el país de la abreviatura del equipo (Bra, Bol, Ven, Col, Chi, Arg, etc.)"""
    if not team_name:
        return ""
    
    pais_abbrev = {
        'bra': 'Brasil',
        'bol': 'Bolivia', 
        'ven': 'Venezuela',
        'col': 'Colombia',
        'chi': 'Chile',
        'arg': 'Argentina',
        'uru': 'Uruguay',
        'par': 'Paraguay',
        'ecu': 'Ecuador',
        'per': 'Perú',
        'mex': 'México',
        'usa': 'Estados Unidos',
        'eu': 'Estados Unidos',
    }
    
    # Buscar patrón (XXX)
    import re
    match = re.search(r'\(([a-zA-Z]{2,4})\)', team_name)
    if match:
        abbrev = match.group(1).lower()
        return pais_abbrev.get(abbrev, "")
    
    return ""


