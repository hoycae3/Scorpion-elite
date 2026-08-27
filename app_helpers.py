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

# ══════════════════════════════════════════════════════════
# 🎯 VALUE BETS AUTOMATICOS (helpers puros, testeables)
# Detecta value bets comparando probabilidad del modelo vs cuota.
# Solo los 3 mercados de goles (1X2, O/U, BTTS) - corners/tarjetas
# requieren mas datos del modelo y son menos fiables aqui.
# ══════════════════════════════════════════════════════════

# clave interna -> (columna 'acertado_*' en picks, tipo_apuesta en tabla cuotas)
MERCADOS_EVAL = {
    '1X2': {'acertado': 'acertado_1x2', 'tipo_cuota': 'Match Winner'},
    'O/U': {'acertado': 'acertado_ou', 'tipo_cuota': 'Over/Under'},
    'BTTS': {'acertado': 'acertado_btts', 'tipo_cuota': 'Both Teams To Score'},
}

UMBRAL_VALUE_MIN = 3.0


def mercado_mas_acertado(picks):
    """Devuelve el mercado con mayor % de acierto en picks resueltos.
    Solo considera mercados con al menos 5 picks evaluados para que la
    estadistica tenga sentido. Si ninguno califica, retorna '1X2'."""
    mejor, mejor_pct = '1X2', -1.0
    for mercado, conf in MERCADOS_EVAL.items():
        col = conf['acertado']
        evaluados = [p for p in picks if p.get(col) is not None]
        n = len(evaluados)
        if n < 5:
            continue
        pct = sum(1 for p in evaluados if p.get(col)) / n * 100
        if pct > mejor_pct:
            mejor, mejor_pct = mercado, pct
    return mejor


def filtrar_value_bets_cuotas(cuotas, prob_1, prob_x, prob_2, prob_ou, prob_btts,
                               mercado, umbral=UMBRAL_VALUE_MIN):
    """Dada una lista de cuotas de un fixture, devuelve los value bets del
    `mercado` que superen `umbral`. Para cada opcion toma la mejor cuota
    (maxima) entre bookmakers.

    Retorna lista de dicts: {opcion, detalle, cuota, prob_modelo, prob_implicita,
                             value, bookie}
    """
    tipo_cuota = MERCADOS_EVAL[mercado]['tipo_cuota']
    mejores = {}
    for c in cuotas:
        if c.get('tipo_apuesta') != tipo_cuota:
            continue
        opcion = (c.get('opcion') or '').strip()
        try:
            valor = float(c.get('cuota') or 0)
        except (ValueError, TypeError):
            continue
        if valor <= 1.0:
            continue

        if mercado == '1X2':
            if 'Home' in opcion or opcion == '1':
                prob = prob_1; detalle = 'Local'
            elif 'Draw' in opcion or opcion == 'X':
                prob = prob_x; detalle = 'Empate'
            elif 'Away' in opcion or opcion == '2':
                prob = prob_2; detalle = 'Visitante'
            else:
                continue
        elif mercado == 'O/U':
            if opcion not in ('Over 2.5', 'Under 2.5'):
                continue
            prob = prob_ou if opcion == 'Over 2.5' else (100 - prob_ou)
            detalle = opcion
        else:  # BTTS
            if 'Yes' in opcion:
                prob = prob_btts; detalle = 'Sí'
            elif 'No' in opcion:
                prob = 100 - prob_btts; detalle = 'No'
            else:
                continue

        if opcion not in mejores or valor > mejores[opcion]['cuota']:
            mejores[opcion] = {'cuota': valor, 'prob': prob, 'detalle': detalle,
                               'bookie': c.get('bookmaker', '')}

    nuevos = []
    for opcion, d in mejores.items():
        value, prob_imp = calcular_value(d['prob'], d['cuota'])
        if value < umbral:
            continue
        nuevos.append({
            'opcion': opcion, 'detalle': d['detalle'], 'cuota': d['cuota'],
            'prob_modelo': round(d['prob'], 2),
            'prob_implicita': round(prob_imp, 2),
            'value': round(value, 2),
            'bookie': d['bookie'],
        })
    return nuevos

def aplicar_override_1x2(pick_modelo, p1, px, p2, seleccion_usuario):
    """Aplica la eleccion manual del usuario al pick 1X2.

    seleccion_usuario: set de mercados marcados en el Analizador
    (puede contener 'Local', 'Empate', 'Visitante' entre otros).

    Retorna (prediccion, prob, es_override):
    - Si el usuario marco exactamente UNA opcion de 1X2 distinta a la del
      modelo: (eleccion_usuario, prob_de_esa_opcion, True)
    - En cualquier otro caso: (pick_modelo, prob_del_modelo, False)

    Las elecciones se traducen al formato interno: Local='1', Empate='X',
    Visitante='2' (mismo formato que calcular_resultados_partido)."""
    mapa = {'Local': ('1', p1), 'Empate': ('X', px), 'Visitante': ('2', p2)}
    elegidas = [m for m in ('Local', 'Empate', 'Visitante') if m in (seleccion_usuario or set())]
    if len(elegidas) == 1:
        prediccion, prob = mapa[elegidas[0]]
        if prediccion != pick_modelo:
            return prediccion, prob, True
        prob_modelo = {'1': p1, 'X': px, '2': p2}.get(pick_modelo, 0)
        return pick_modelo, prob_modelo, False
    prob_modelo = {'1': p1, 'X': px, '2': p2}.get(pick_modelo, 0)
    return pick_modelo, prob_modelo, False




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
