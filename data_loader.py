"""
Scorpion Elite - Cargador de datos desde Excel
Procesa volcados verticales de Flashscore
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
    
    for key, value in PAIS_MAP.items():
        if key in pais_lower:
            return value
    
    # Capitalizar primera letra
    return pais_lower.capitalize()


def parse_flashscore_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parsea un DataFrame de Excel formato Flashscore vertical.
    
    Formato esperado:
    - Filas con fecha (ej: "Hoy - 18.07." o "Mañana - 19.07.")
    - Filas con países: "BRASIL:"
    - Filas con ligas: nombre de la liga (fila anterior al país)
    - Filas con horas: "HH:MM"
    - Filas con equipos: nombre del equipo local, luego visitante
    """
    if df.empty:
        return pd.DataFrame()
    
    # Obtener todas las filas como lista
    rows = []
    for i in range(len(df)):
        val = df.iloc[i, 0]
        if pd.isna(val):
            rows.append("")
        else:
            rows.append(str(val).strip())
    
    # Detectar todas las fechas (headers)
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    fecha_por_posicion = {}  # {posicion: fecha}
    
    for i, row in enumerate(rows):
        # Detectar si es una fila de fecha
        if any(keyword in row.lower() for keyword in ['hoy', 'mañana', 'manana', 'tomorrow', 'today', 'yesterday']):
            fecha_por_posicion[i] = parse_date_from_header(row)
    
    # Si no encontró fechas con keywords, usar la primera celda
    if not fecha_por_posicion:
        first_cell = str(rows[0]) if rows else ""
        if first_cell:
            fecha_actual = parse_date_from_header(first_cell)
        fecha_por_posicion[0] = fecha_actual
    
    # Estados para el parser
    current_pais = ""
    current_liga = ""
    matches = []
    
    # Encontrar la fecha más reciente aplicable
    def get_fecha_actual(posicion):
        fecha = datetime.now().strftime("%Y-%m-%d")
        for pos in sorted(fecha_por_posicion.keys(), reverse=True):
            if pos <= posicion:
                fecha = fecha_por_posicion[pos]
                break
        return fecha
    
    i = 0
    while i < len(rows):
        row = rows[i]
        
        # Detectar país (termina con :)
        if row.endswith(':') and len(row) > 1:
            current_pais = get_pais_normalizado(row)
            # La liga es la fila anterior
            if i > 0:
                prev_row = rows[i - 1]
                if prev_row and not prev_row.endswith(':') and not re.match(r'^\d{1,2}:\d{2}', prev_row):
                    current_liga = prev_row.strip()
            i += 1
            continue
        
        # Detectar hora (HH:MM o HH:MM:SS)
        if re.match(r'^\d{1,2}:\d{2}(:\d{2})?$', row):
            hora = row[:5]  # Solo HH:MM
            fecha_partido = get_fecha_actual(i)
            
            # Los siguientes dos rows son los equipos
            home = ""
            away = ""
            
            if i + 1 < len(rows):
                home = clean_team_name(rows[i + 1])
            if i + 2 < len(rows):
                away = clean_team_name(rows[i + 2])
            
            if home and away and home != away:
                matches.append({
                    'fecha': fecha_partido,
                    'hora': hora,
                    'pais': current_pais,
                    'liga': current_liga,
                    'liga_codigo': get_league_code(current_liga),
                    'equipo_local': home,
                    'equipo_visitante': away
                })
            
            i += 3  # Saltar hora + 2 equipos
            continue
        
        i += 1
    
    # Crear DataFrame
    if matches:
        return pd.DataFrame(matches)
    
    return pd.DataFrame()


def validate_matches(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Valida los partidos y retorna errores"""
    errors = []
    
    if df.empty:
        errors.append("No se encontraron partidos")
        return df, errors
    
    # Verificar equipos duplicados
    for idx, row in df.iterrows():
        if row['equipo_local'] == row['equipo_visitante']:
            errors.append(f"Fila {idx+1}: Equipos idénticos '{row['equipo_local']}'")
        
        if len(row['equipo_local']) < 2:
            errors.append(f"Fila {idx+1}: Equipo local muy corto '{row['equipo_local']}'")
    
    return df, errors
