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


def parse_flashscore_excel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parsea un DataFrame de Excel formato Flashscore vertical.
    
    Formato del Excel:
    - Fecha header (ej: "2026-07-25 00:00:00")
    - Vacío
    - Liga
    - País duplicado (ej: "MexicoMéxico")
    - Fecha-hora Excel (para hora)
    - Hora (HH:MM:SS)
    - Separador "-" 
    - Equipo Local
    - Abreviatura Local
    - Equipo Visitante
    - Abreviatura Visitante
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
    
    # Detectar fecha del día (buscar "2026-..." que indica fecha real)
    fecha_del_dia = None
    for i, row in enumerate(rows):
        # Buscar fecha tipo "2026-07-25" (año actual)
        if re.match(r'^\d{4}-\d{2}-\d{2}', row):
            # Solo tomar fechas que parezcan ser del día (no 1900, 1901 que son horas de Excel)
            year = int(row[:4])
            if year >= 2025:  # Fechas reales
                fecha_del_dia = row[:10]
                break
    
    if not fecha_del_dia:
        fecha_del_dia = datetime.now().strftime("%Y-%m-%d")
    
    # Estados para el parser
    current_pais = ""
    current_liga = ""
    matches = []
    
    # Mapeo de países desde texto duplicado
    pais_map = {
        'Mexico': 'México',
        'Colombia': 'Colombia', 
        'Argentina': 'Argentina',
        'Brasil': 'Brasil',
        'Chile': 'Chile',
        'Peru': 'Perú',
        'Uruguay': 'Uruguay',
        'Paraguay': 'Paraguay',
        'Ecuador': 'Ecuador',
        'Venezuela': 'Venezuela',
    }
    
    def is_country_dup(text):
        """Verifica si el texto es un país duplicado"""
        if len(text) < 6:
            return False
        half = len(text) // 2
        first = text[:half]
        second = text[half:]
        return normalize_text(first) == normalize_text(second)
    
    def find_liga_above(posicion, pais_default=""):
        """Busca la liga en las filas anteriores. Si no encuentra, usa la del país."""
        # Patrones de liga conocidos
        liga_patterns = ['liga mx', 'liga mx apertura', 'primera a', 'copa de la liga', 'liga profesional',
                        'apertura', 'clausura', 'serie a', 'premier league', 'la liga', 'bundesliga',
                        'ligue 1', 'champions', 'copa libertadores', 'copa sudamericana']
        
        for back in range(1, 25):  # Buscar más hacia arriba
            if posicion - back < 0:
                break
            prev = rows[posicion - back]
            # Ignorar filas vacías, separadores
            if not prev or prev == '-':
                continue
            # Ignorar fechas de Excel (1900-01-xx)
            if re.match(r'^\d{4}-\d{2}-\d{2}', prev):
                continue
            # Ignorar horas
            if re.match(r'^\d{1,2}:\d{2}:\d{2}$', prev):
                continue
            # Ignorar países duplicados
            if is_country_dup(prev):
                continue
            # Detectar país con :
            if prev.endswith(':') and '(' not in prev:
                continue  # El país viene después de la liga, buscar más arriba
            # Ignorar "Clasificación", "Tabla", etc.
            if prev in ['Clasificación', 'Tabla', 'Cuadro', 'En Directo']:
                continue
            
            # Normalizar para comparación (quitar tildes)
            prev_lower = normalize_text(prev)
            
            # Si el texto contiene patrones de liga, devolverlo
            if any(pattern in prev_lower for pattern in liga_patterns):
                return prev.strip()
            
            # Excluir nombres que parecen equipos
            equipos_comunes = ['guadalajara', 'atl', 'santos', 'tigres', 'san luis', 
                              'boyaca', 'chico', 'medellin', 'pasto', 'millonarios',
                              'bucaramanga', 'tolima', 'junior', 'estudiantes', 'newells',
                              'talleres', 'river', 'barracas', 'lanus', 'lorenzo', 'cd ', 'juarez', 'atlas']
            if any(eq in prev_lower for eq in equipos_comunes):
                continue
            
            # Si no parece ser un equipo y tiene más de 5 caracteres, podría ser una liga
            if len(prev) > 5 and prev[0].isupper():
                return prev.strip()
        
        # Si no encontró liga, usar la del país
        if pais_default and pais_default in PAIS_LIGA_DEFAULT:
            return PAIS_LIGA_DEFAULT[pais_default]
        
        return ""
    
    def normalize_text(text):
        """Normaliza texto eliminando tildes y caracteres especiales para comparación"""
        import unicodedata
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        ).lower()
    
    def find_pais_above(posicion):
        """Busca el país en las filas anteriores"""
        # Primero buscar país con : (más confiable)
        for back in range(1, 25):
            if posicion - back < 0:
                break
            prev = rows[posicion - back]
            if not prev:
                continue
            # Detectar país con : (ej: "COLOMBIA:", "ARGENTINA:")
            if prev.endswith(':') and '(' not in prev:
                pais = get_pais_normalizado(prev)
                # Ignorar "SUDAMÉRICA:" y similares
                if pais and pais != "":  # Solo retornar si es un país válido
                    return pais
        
        # Si no encontró, buscar país duplicado
        for back in range(1, 25):
            if posicion - back < 0:
                break
            prev = rows[posicion - back]
            if not prev:
                continue
            # Ignorar "Clasificación", "Tabla", etc.
            if prev in ['Clasificación', 'Tabla', 'Cuadro', 'En Directo']:
                continue
            # Detectar país duplicado (ej: "MexicoMéxico")
            if is_country_dup(prev):
                half = len(prev) // 2
                first_half = prev[:half]
                # Verificar que sea un país conocido
                if first_half in pais_map or first_half.lower() in ['mexico', 'colombia', 'argentina', 'brasil']:
                    return pais_map.get(first_half, first_half)
        
        return ""
    
    # Procesar filas
    i = 0
    while i < len(rows):
        row = rows[i]
        
        # Ignorar filas vacías
        if not row:
            i += 1
            continue
        
        # Ignorar separadores "-"
        if row == '-':
            i += 1
            continue
        
        # Ignorar "Clasificación", "Tabla", etc.
        if row in ['Clasificación', 'Tabla', 'Cuadro', 'En Directo']:
            i += 1
            continue
        
        # Detectar hora (HH:MM:SS)
        if re.match(r'^\d{1,2}:\d{2}:\d{2}$', row):
            hora = row[:5]  # Solo HH:MM
            
            # Buscar país primero
            pais_encontrado = find_pais_above(i)
            if pais_encontrado:
                current_pais = pais_encontrado
            
            # Buscar liga (usando el país como default si no se encuentra)
            liga_encontrada = find_liga_above(i, current_pais)
            if liga_encontrada:
                current_liga = liga_encontrada
            
            # Los siguientes rows son los equipos
            home = ""
            away = ""
            
            # Buscar equipos en las siguientes filas
            for offset in range(1, 10):
                if i + offset >= len(rows):
                    break
                next_row = rows[i + offset]
                
                # Saltar separadores y vacíos
                if next_row == '-' or not next_row:
                    continue
                
                # Si aún estamos en horas o fechas, continuar
                if re.match(r'^\d{1,2}:\d{2}:\d{2}$', next_row):
                    continue
                if re.match(r'^\d{4}-\d{2}-\d{2}', next_row):
                    continue
                
                # Primera ocurrencia de texto = equipo local
                if not home and len(next_row) > 2:
                    home = clean_team_name(next_row)
                # Segunda ocurrencia de texto = equipo visitante
                elif home and not away and len(next_row) > 2:
                    # Verificar que no sea una abreviatura del local
                    if home.lower() in next_row.lower() or next_row.lower() in home.lower():
                        continue
                    away = clean_team_name(next_row)
                    break
            
            if home and away and home != away and len(home) > 1 and len(away) > 1:
                # Verificar países de los equipos
                pais_home = extract_pais_from_team(home)
                pais_away = extract_pais_from_team(away)
                
                # Si los equipos son de diferentes países → es torneo internacional
                es_internacional = False
                if pais_home and pais_away and pais_home != pais_away:
                    es_internacional = True
                    current_liga = "Copa Sudamericana"
                    current_pais = ""
                
                if not es_internacional:
                    # Torneos locales - mantener país
                    if not current_pais or current_pais == "":
                        if pais_away:
                            current_pais = pais_away
                        elif pais_home:
                            current_pais = pais_home
                
                matches.append({
                    'fecha': fecha_del_dia,
                    'hora': hora,
                    'pais': current_pais,
                    'liga': current_liga,
                    'liga_codigo': get_league_code(current_liga),
                    'equipo_local': home,
                    'equipo_visitante': away
                })
            
            i += 1
            continue
        
        # Detectar fecha tipo "2026-07-25 00:00:00" - es un header de fecha
        if re.match(r'^\d{4}-\d{2}-\d{2}', row):
            # Solo actualizar si es fecha real (año >= 2025)
            year = int(row[:4])
            if year >= 2025:
                fecha_del_dia = row[:10]
            i += 1
            continue
        
        i += 1
    
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
