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
    if not lista:
        return "Sin datos"
    badges = ""
    for c in lista:
        if c in ['G', 'W']:
            badges += f"🟢{c} "
        elif c == 'D':
            badges += f"🟡{c} "
        else:
            badges += f"🔴{c} "
    return badges.strip()


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
    if cuota <= 0:
        return 0, 0
    prob_implicita = (1 / cuota) * 100
    value = prob_modelo - prob_implicita
    return value, prob_implicita


def format_money(valor, simbolo):
    return f"{simbolo}{valor:,.2f}"
