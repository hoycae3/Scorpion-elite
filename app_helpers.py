"""Funciones helper puras y constantes de Scorpion Elite.

Extraídas de elite.py para reducir el monolito. Estas funciones no dependen
del estado de Streamlit ni del cliente Supabase, solo de la librería estándar
y bcrypt, por lo que son seguras de reutilizar y testear.
"""
import logging
import bcrypt
from datetime import timedelta, datetime, timezone

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════
# 📋 SISTEMA DE DISEÑO - COLORES Y ESTILOS
# ══════════════════════════════════════════════════════════
COLORS = {
    'victoria': '#22c55e',
    'derrota': '#ef4444',
    'empate': '#eab308',
    'primary': '#00d4aa',
    'local': '#fff',
    'visitante': '#fff',
    'hora': '#fff',
    'bg_dark': '#0f172a',
    'bg_card': '#111111',
    'bg_header': '#121824',
    'text': '#f8fafc',
    'text_secondary': '#94a3b8',
}

# Mapeo de league_id por nombre de liga
LIGAS_MAP = {
    'Premier League': 39,
    'La Liga': 140,
    'Bundesliga': 78,
    'Serie A': 135,
    'Ligue 1': 61,
    'Liga MX': 262,
    'MLS': 1,
    'Copa Libertadores': 13,
    'Champions League': 2,
    'Europa League': 3,
    'Primeira Liga': 94,
    'Eredivisie': 88,
    'Belgian Pro League': 61,
    'Scottish Premiership': 50,
    'Brasileirao': 71,
    'Argentine Primera': 128,
    'Chile Primera Division': 215,
    'Primera Division': 215,
    'Primera A': 215,
    'Primera B': 216,
}


# ══════════════════════════════════════════════════════════
# 🔐 AUTENTICACIÓN
# ══════════════════════════════════════════════════════════
def hash_password(password: str) -> str:
    """Genera hash bcrypt con salt automático"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verifica password contra hash bcrypt"""
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception as e:
        logger.warning(f"verify_password falló: {e}")
        return False


# ══════════════════════════════════════════════════════════
# 📅 FECHAS Y TIEMPO
# ══════════════════════════════════════════════════════════
def get_hoy():
    return str(datetime.now(timezone(timedelta(hours=-5))).date())


def utc_to_colombia(utc_datetime_str):
    """Convierte datetime UTC a hora colombiana (UTC-5)"""
    try:
        if not utc_datetime_str:
            return ""
        utc_dt = datetime.fromisoformat(utc_datetime_str.replace('Z', '+00:00'))
        colombia_tz = timezone(timedelta(hours=-5))
        colombia_dt = utc_dt.astimezone(colombia_tz)
        return colombia_dt.strftime('%H:%M')
    except Exception:
        try:
            hora_str = utc_datetime_str[11:16]
            hora = int(hora_str.split(':')[0]) if hora_str else 0
            minuto = int(hora_str.split(':')[1]) if ':' in hora_str else 0
            hora_colombia = (hora - 5) % 24
            return f"{hora_colombia:02d}:{minuto:02d}"
        except Exception:
            return utc_datetime_str[11:16] if len(utc_datetime_str) > 16 else ""


# ══════════════════════════════════════════════════════════
# 🎨 FORMATO Y UI
# ══════════════════════════════════════════════════════════
def get_pais_emoji(pais):
    emojis = {
        'Argentina': '🇦🇷', 'Brasil': '🇧🇷', 'Colombia': '🇨🇴', 'Chile': '🇨🇱',
        'México': '🇲🇽', 'USA': '🇺🇸', 'Uruguay': '🇺🇾', 'Perú': '🇵🇪',
        'Paraguay': '🇵🇾', 'Ecuador': '🇪🇨', 'España': '🇪🇸', 'Inglaterra': '🏴󠁧󠁢󠁥󠁮',
        'Alemania': '🇩🇪', 'Italia': '🇮🇹', 'Francia': '🇫🇷', 'Portugal': '🇵🇹',
        'Holanda': '🇳🇱', 'Turquía': '🇹🇷', 'Escocia': '🏴󠁧󠁢󠁳󠁣', 'Bélgica': '🇧🇪', 'Mundial': '🏴'
    }
    return emojis.get(pais, '🏴')


def crear_badges(lista):
    if not lista or lista == '-----' or lista == 'Sin datos':
        return "Sin datos"
    badges = ""
    for c in lista:
        if c in ['G', 'W']:
            badges += f"🟢{c} "
        elif c in ['E', 'D']:
            badges += f"🟡{c} "
        elif c in ['P', 'L']:
            badges += f"🔴{c} "
        else:
            badges += f"⚫{c} "
    return badges.strip() if badges else "Sin datos"


def fila_dato(valor_l, indicador, valor_v, color_val='white', bg_par=False):
    bg = '#162031' if bg_par else '#0a0a0a'
    return f"""<div style='background:{bg};padding:8px 5px;border-radius:4px;margin:2px 0;display:flex;'><div style='width:33%;text-align:center;color:{color_val};font-size:13px;'>{valor_l}</div><div style='width:34%;text-align:center;color:#fff;font-size:12px;'>{indicador}</div><div style='width:33%;text-align:center;color:{color_val};font-size:13px;'>{valor_v}</div></div>"""


def safe_fmt(val, fmt='.1f'):
    """Convierte valor a string, manteniendo '?' si no hay datos."""
    if val == '?' or val is None or val == 0:
        return '?'
    try:
        return f'{float(val):{fmt}}'
    except Exception as e:
        logger.debug(f"safe_fmt falló con val={val!r}: {e}")
        return str(val)


def safe_fmt_int(val):
    """Convierte valor a string entero, manteniendo '?' si no hay datos."""
    if val == '?' or val is None:
        return '?'
    try:
        return f'{int(float(val))}'
    except Exception as e:
        logger.debug(f"safe_fmt_int falló con val={val!r}: {e}")
        return str(val)


# ══════════════════════════════════════════════════════════
# 💰 APUESTAS
# ══════════════════════════════════════════════════════════
def calcular_value(prob_modelo, cuota):
    """Calcula value de una apuesta.

    prob_modelo: probabilidad estimada por el modelo (%)
    cuota: cuota decimal (ej: 2.10)
    Retorna (value, prob_implicita).
    value = EV% = prob_modelo × cuota − 100 (valor esperado en %).
    Positivo = apuesta con valor (el modelo ve más prob. que la casa).
    """
    if cuota <= 0:
        return 0, 0
    prob_implicita = (1 / cuota) * 100
    value = prob_modelo * cuota - 100
    return value, prob_implicita


def format_money(valor, simbolo):
    return f"{simbolo}{valor:,.2f}"


# ══════════════════════════════════════════════════════════
# 🛡️ VALIDACIÓN DE INPUT
# ══════════════════════════════════════════════════════════
def sanitizar_input(texto, max_len=100, permitir_espacios=True):
    """Sanitiza texto de entrada: recorta, quita caracteres peligrosos.

    - Recorta espacios al inicio/final
    - Limita longitud (default 100 chars)
    - Quita caracteres usados en inyección SQL/HTML: ; ' " < > \\ -- /*
    - Si permitir_espacios=False, quita todos los espacios internos
    """
    if not texto or not isinstance(texto, str):
        return ""
    texto = texto.strip()
    if not permitir_espacios:
        texto = texto.replace(" ", "")
    # Quitar caracteres peligrosos para SQL/HTML
    for char in [';', "'", '"', '<', '>', '\\', '--', '/*', '*/']:
        texto = texto.replace(char, "")
    # Limitar longitud
    if len(texto) > max_len:
        texto = texto[:max_len]
    return texto.strip()


def normalizar_mercados_para_capital(sel):
    """Mapea los nombres de mercados del Analizador a los tipos que espera Capital.
    El Analizador usa 'Local'/'Empate'/'Visitante', pero Capital usa '1X2'.
    Los mercados no soportados por Capital (1X, X2, 12, OU 1.5, OU 3.5,
    Goles Local, Goles Visitante) se omiten.
    Retorna un set de strings."""
    mapeo = {
        'Local': '1X2', 'Empate': '1X2', 'Visitante': '1X2',
        'O/U': 'O/U', 'BTTS': 'BTTS', 'Corners': 'Corners',
        'Remates': 'Remates', 'Tiros Arco': 'Tiros Arco', 'Tarjetas': 'Tarjetas',
    }
    return {mapeo[s] for s in sel if s in mapeo}
