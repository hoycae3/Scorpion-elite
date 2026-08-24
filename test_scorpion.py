"""
Scorpion Elite - Tests automatizados
=====================================
Cobertura:
1. Modelos matematicos (analysis_models.py)
2. Helpers (app_helpers.py)
3. Parsing de cuotas (funciones_stats.py)
4. Calibracion (calibration.py)

Ejecutar: python3 -m pytest test_scorpion.py -v
O sin pytest: python3 test_scorpion.py
"""

import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================================
# TESTS: analysis_models.py
# ============================================================================

def test_calcular_retorna_todas_las_claves():
    """calcular() debe retornar todas las claves esperadas."""
    from analysis_models import calcular
    r = calcular(1.5, 1.2)
    claves_esperadas = [
        'p1', 'px', 'p2', 'pick_1x2', 'prob_1x2',
        'over_under', 'pick_over_under', 'prob_over_under',
        'btts_yes', 'btts_no', 'pick_btts',
        'corners', 'pick_corners',
        'tiros', 'pick_tiros', 'prob_tiros',
        'tarjetas', 'pick_tarjetas', 'prob_tarjetas',
        'tiros_arco', 'pick_tiros_arco', 'prob_tiros_arco',
        'confianza', 'rango', 'modelos',
    ]
    for clave in claves_esperadas:
        assert clave in r, f"Falta clave '{clave}' en resultado de calcular()"


def test_calcular_probabilidades_suman_100():
    """p1 + px + p2 debe sumar aproximadamente 100."""
    from analysis_models import calcular
    r = calcular(1.5, 1.2)
    total = r['p1'] + r['px'] + r['p2']
    assert 99 <= total <= 101, f"1X2 no suma 100: {total} (p1={r['p1']}, px={r['px']}, p2={r['p2']})"


def test_calcular_btts_suman_100():
    """btts_yes + btts_no debe sumar 100."""
    from analysis_models import calcular
    r = calcular(1.5, 1.2)
    total = r['btts_yes'] + r['btts_no']
    assert 99 <= total <= 101, f"BTTS no suma 100: {total}"


def test_calcular_over_under_suman_100():
    """over_25 + under_25 debe sumar 100."""
    from analysis_models import calcular
    r = calcular(1.5, 1.2)
    ou = r['over_under']
    total = ou['over_25'] + ou['under_25']
    assert 99 <= total <= 101, f"Over/Under 2.5 no suma 100: {total}"


def test_calcular_pick_consistente():
    """El pick de 1X2 debe ser el de mayor probabilidad."""
    from analysis_models import calcular
    r = calcular(1.5, 1.2)
    probs = {'1': r['p1'], 'X': r['px'], '2': r['p2']}
    max_key = max(probs, key=probs.get)
    assert r['pick_1x2'] == max_key, f"Pick {r['pick_1x2']} != esperado {max_key}"


def test_calcular_lambda_alto_favor_local():
    """Con lambda_local muy alto, p1 debe ser la mayor probabilidad."""
    from analysis_models import calcular
    r = calcular(3.0, 0.5)
    assert r['p1'] > r['p2'], f"Local favorito deberia tener p1 > p2 (p1={r['p1']}, p2={r['p2']})"


def test_calcular_lambda_alto_favor_visitante():
    """Con lambda_visitante muy alto, p2 debe ser la mayor probabilidad."""
    from analysis_models import calcular
    r = calcular(0.5, 3.0)
    assert r['p2'] > r['p1'], f"Visitante favorito deberia tener p2 > p1 (p1={r['p1']}, p2={r['p2']})"


def test_calcular_determinista_con_seed():
    """Monte Carlo con misma seed debe dar mismo resultado."""
    from analysis_models import calcular
    r1 = calcular(1.5, 1.2)
    r2 = calcular(1.5, 1.2)
    # Poisson y Dixon-Coles son deterministas; el ensemble deberia ser estable
    assert abs(r1['p1'] - r2['p1']) < 1, "calcular() no es determinista"


def test_pp_poisson_valido():
    """pp(lambda, 0) debe dar probabilidad valida entre 0 y 1."""
    from analysis_models import pp
    p = pp(1.5, 0)
    assert 0 < p < 1, f"pp(1.5, 0) fuera de rango: {p}"


def test_pp_poisson_k_mayor_lambda():
    """pp(lambda, k) con k > lambda*3 debe ser muy pequeno."""
    from analysis_models import pp
    p = pp(1.0, 5)
    assert p < 0.01, f"pp(1.0, 5) deberia ser <0.01: {p}"


def test_normal_cdf_rangos():
    """normal_cdf debe retornar valores entre 0 y 1."""
    from analysis_models import normal_cdf
    assert 0 <= normal_cdf(-3) <= 1
    assert 0 <= normal_cdf(0) <= 1
    assert 0 <= normal_cdf(3) <= 1
    assert normal_cdf(0) > 0.49 and normal_cdf(0) < 0.51  # ≈ 0.5


# ============================================================================
# TESTS: app_helpers.py
# ============================================================================

def test_get_pais_emoji_conocido():
    """get_pais_emoji debe retornar emoji para paises conocidos."""
    from app_helpers import get_pais_emoji
    assert '🇨🇴' in get_pais_emoji('Colombia')
    assert '🇦🇷' in get_pais_emoji('Argentina')
    assert '🇧🇷' in get_pais_emoji('Brasil')


def test_get_pais_emoji_desconocido():
    """get_pais_emoji debe retornar algo para paises desconocidos."""
    from app_helpers import get_pais_emoji
    result = get_pais_emoji('PaisInventado')
    assert isinstance(result, str)


def test_get_hoy_formato_fecha():
    """get_hoy debe retornar string en formato YYYY-MM-DD."""
    from app_helpers import get_hoy
    hoy = get_hoy()
    assert len(hoy) == 10, f"Fecha debe tener 10 chars: {hoy}"
    parts = hoy.split('-')
    assert len(parts) == 3, f"Fecha debe tener 3 partes: {hoy}"
    assert len(parts[0]) == 4, f"Año debe tener 4 digitos: {hoy}"


def test_hash_password_y_verify():
    """hash_password + verify_password debe funcionar correctamente."""
    from app_helpers import hash_password, verify_password
    password = 'miPassword123'
    h = hash_password(password)
    assert h != password, "Hash no debe ser igual al password"
    assert verify_password(password, h), "verify_password debe retornar True para password correcto"
    assert not verify_password('otraPassword', h), "verify_password debe retornar False para password incorrecto"


def test_format_money():
    """format_money debe formatear montos correctamente."""
    from app_helpers import format_money
    result = format_money(1000.50, '$')
    assert '1,000' in result or '1000' in result, f"format_money falla: {result}"


def test_utc_to_colombia_conversion():
    """utc_to_colombia debe convertir UTC a Colombia (UTC-5)."""
    from app_helpers import utc_to_colombia
    # 00:30 UTC → 19:30 Colombia (dia anterior)
    hora = utc_to_colombia('2026-08-18T00:30:00Z')
    assert hora == '19:30', f"UTC 00:30 → Colombia deberia ser 19:30, no {hora}"


def test_utc_to_colombia_vacio():
    """utc_to_colombia con string vacio debe retornar string vacio."""
    from app_helpers import utc_to_colombia
    assert utc_to_colombia('') == ''
    assert utc_to_colombia(None) == ''


def test_calcular_value():
    """calcular_value: EV% = prob × cuota − 100."""
    from app_helpers import calcular_value
    # prob=60%, cuota=2.0 → EV = 60×2.0−100 = +20%
    value, prob_implicita = calcular_value(60, 2.0)
    assert abs(value - 20) < 1, f"calcular_value(60, 2.0) value deberia ser ~20, no {value}"
    assert abs(prob_implicita - 50) < 1, f"prob_implicita deberia ser ~50, no {prob_implicita}"


# ============================================================================
# TESTS: funciones_stats.py (parsing de cuotas)
# ============================================================================

def test_parse_cuotas_estructura_bookmakers():
    """El parser de cuotas debe manejar bookmakers[] (plural, array)."""
    from funciones_stats import parse_cuotas_response
    # Estructura real de API-Football /odds
    mock_response = {
        'response': [
            {
                'fixture': {'id': 12345},
                'bookmakers': [
                    {
                        'name': 'Bet365',
                        'bets': [
                            {
                                'name': 'Match Winner',
                                'values': [
                                    {'value': 'Home', 'odd': '1.50'},
                                    {'value': 'Draw', 'odd': '3.20'},
                                    {'value': 'Away', 'odd': '5.00'},
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    cuotas = parse_cuotas_response(mock_response, fixture_id=12345)
    assert len(cuotas) > 0, "Parser no extrajo cuotas"
    c = cuotas[0]
    assert c['fixture_id'] == 12345
    assert c['bookmaker'] == 'Bet365'
    assert c['cuota'] == 1.50
    assert c['opcion'] == 'Home'


def test_parse_cuotas_vacio():
    """El parser debe manejar respuesta vacia sin crashear."""
    from funciones_stats import parse_cuotas_response
    cuotas = parse_cuotas_response({'response': []}, fixture_id=1)
    assert cuotas == [], "Parser deberia retornar lista vacia"


def test_parse_cuotas_sin_bookmakers():
    """El parser debe manejar fixture sin bookmakers (plural)."""
    from funciones_stats import parse_cuotas_response
    mock = {
        'response': [
            {'fixture': {'id': 1}, 'bookmaker': {'name': 'Old'}}
        ]
    }
    cuotas = parse_cuotas_response(mock, fixture_id=1)
    # El parser moderno usa bookmakers (plural); si viene singular, no extrae nada
    assert isinstance(cuotas, list)
    assert len(cuotas) == 0  # 'bookmaker' singular no se procesa


def test_dedup_cuotas():
    """Las cuotas duplicadas deben eliminarse antes del upsert."""
    from funciones_stats import dedup_cuotas_lista
    # 2 con misma clave (dup), 1 con cuota distinta pero MISMA clave → se colapsa a 1
    # para testear dedup real, usamos claves diferentes
    cuotas = [
        {'fixture_id': 1, 'bookmaker': 'Bet365', 'tipo_apuesta': 'Match Winner', 'opcion': 'Home', 'cuota': 1.5},
        {'fixture_id': 1, 'bookmaker': 'Bet365', 'tipo_apuesta': 'Match Winner', 'opcion': 'Home', 'cuota': 1.5},
        {'fixture_id': 1, 'bookmaker': 'Bet365', 'tipo_apuesta': 'Match Winner', 'opcion': 'Draw', 'cuota': 3.2},
        {'fixture_id': 2, 'bookmaker': 'Bet365', 'tipo_apuesta': 'Match Winner', 'opcion': 'Home', 'cuota': 2.0},
    ]
    deduped = dedup_cuotas_lista(cuotas)
    assert len(deduped) == 3, f"Deberia tener 3 cuotas unicas, no {len(deduped)}"


# ============================================================================
# TESTS: calibration.py (logica pura)
# ============================================================================

def test_normalizar_equipo_acentos():
    """normalizar_equipo debe quitar acentos y lowercase."""
    from calibration import normalizar_equipo
    assert normalizar_equipo('Atlético') == 'atletico'
    assert normalizar_equipo('  CA Colón  ') == 'ca colon'
    assert normalizar_equipo('Boca Juniors') == 'boca juniors'


def test_ajustar_lambda():
    """ajustar_lambda multiplica correctamente."""
    from calibration import ajustar_lambda
    assert ajustar_lambda(1.5, 1.0) == 1.5
    assert abs(ajustar_lambda(1.5, 1.2) - 1.8) < 0.001
    assert ajustar_lambda(2.0, 0.5) == 1.0


def test_normalizar_equipo_vacio():
    """normalizar_equipo con None/vacio no debe crashear."""
    from calibration import normalizar_equipo
    assert normalizar_equipo('') == ''
    assert normalizar_equipo(None) == ''


# ============================================================================
# TESTS: app_helpers.py (validación de input)
# ============================================================================

def test_sanitizar_input_basico():
    """sanitizar_input recorta espacios y respeta texto normal."""
    from app_helpers import sanitizar_input
    assert sanitizar_input('  Hola  ') == 'Hola'
    assert sanitizar_input('Juan Pérez') == 'Juan Pérez'


def test_sanitizar_input_quita_peligroso():
    """sanitizar_input quita caracteres de inyección SQL/HTML."""
    from app_helpers import sanitizar_input
    # ; ' " < > \ -- /* */ se eliminan, el resto se mantiene
    assert "'" not in sanitizar_input("'; DROP TABLE--")
    assert "--" not in sanitizar_input("'; DROP TABLE--")
    assert ";" not in sanitizar_input("'; DROP TABLE--")
    assert "<" not in sanitizar_input("<script>alert('xss')</script>")
    assert ">" not in sanitizar_input("<script>alert('xss')</script>")
    assert '"' not in sanitizar_input('" OR 1=1')


def test_sanitizar_input_longitud():
    """sanitizar_input limita la longitud."""
    from app_helpers import sanitizar_input
    largo = 'A' * 200
    assert len(sanitizar_input(largo, max_len=50)) == 50
    assert len(sanitizar_input(largo, max_len=10)) == 10


def test_sanitizar_input_vacio():
    """sanitizar_input con None/vacio retorna string vacio."""
    from app_helpers import sanitizar_input
    assert sanitizar_input('') == ''
    assert sanitizar_input(None) == ''


def test_sanitizar_input_no_espacios():
    """sanitizar_input con permitir_espacios=False quita espacios internos."""
    from app_helpers import sanitizar_input
    assert sanitizar_input('mi password 123', permitir_espacios=False) == 'mipassword123'


# ============================================================================
# TESTS: bet_logic.py (resultados y evaluación de apuestas)
# ============================================================================

def test_calcular_resultados_gana_local():
    """calcular_resultados_partido con 2-0 → 1, Under, No."""
    from bet_logic import calcular_resultados_partido
    r, ou, btts = calcular_resultados_partido(2, 0)
    assert r == "1"
    assert ou == "Under 2.5"
    assert btts == "No"


def test_calcular_resultados_empate():
    """calcular_resultados_partido con 1-1 → X, Under, Si."""
    from bet_logic import calcular_resultados_partido
    r, ou, btts = calcular_resultados_partido(1, 1)
    assert r == "X"
    assert ou == "Under 2.5"
    assert btts == "Si"


def test_calcular_resultados_gana_visitante_over():
    """calcular_resultados_partido con 1-3 → 2, Over, Si."""
    from bet_logic import calcular_resultados_partido
    r, ou, btts = calcular_resultados_partido(1, 3)
    assert r == "2"
    assert ou == "Over 2.5"
    assert btts == "Si"


def test_calcular_resultados_over_exacto():
    """calcular_resultados_partido con 2-1 (3 goles) → Over 2.5."""
    from bet_logic import calcular_resultados_partido
    _, ou, _ = calcular_resultados_partido(2, 1)
    assert ou == "Over 2.5"


def test_evaluar_over_under_acierto():
    """evaluar_over_under: Over con real>linea → True."""
    from bet_logic import evaluar_over_under
    assert evaluar_over_under("Over 2.5", 3, 2.5) is True
    assert evaluar_over_under("Under 2.5", 2, 2.5) is True


def test_evaluar_over_under_fallo():
    """evaluar_over_under: Over con real<linea → False."""
    from bet_logic import evaluar_over_under
    assert evaluar_over_under("Over 2.5", 2, 2.5) is False
    assert evaluar_over_under("Under 2.5", 3, 2.5) is False


def test_evaluar_over_under_vacio():
    """evaluar_over_under con prediccion None → False."""
    from bet_logic import evaluar_over_under
    assert evaluar_over_under(None, 3, 2.5) is False
    assert evaluar_over_under("", 3, 2.5) is False


def test_apuesta_ganada_1x2_acierto():
    """apuesta_ganada: 1X2 correcto → True."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': '1X2'}
    pick = {'prediccion_1x2': '1'}
    assert apuesta_ganada(apuesta, pick, '1', 'Under 2.5', 'No') is True


def test_apuesta_ganada_1x2_fallo():
    """apuesta_ganada: 1X2 incorrecto → False."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': '1X2'}
    pick = {'prediccion_1x2': '1'}
    assert apuesta_ganada(apuesta, pick, '2', 'Over 2.5', 'Si') is False


def test_apuesta_ganada_ou_acierto():
    """apuesta_ganada: Over acertado → True (mercado canónico 'O/U')."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': 'O/U'}
    pick = {'prediccion_ou': 'Over 2.5'}
    assert apuesta_ganada(apuesta, pick, '1', 'Over 2.5', 'Si') is True


def test_apuesta_ganada_ou_alias():
    """Over/Under (alias de O/U) debe evaluarse igual — fix bug de apuestas manuales."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': 'Over/Under'}
    pick = {'prediccion_ou': 'Over 2.5'}
    assert apuesta_ganada(apuesta, pick, '1', 'Over 2.5', 'Si') is True
    assert apuesta_ganada(apuesta, pick, '1', 'Under 2.5', 'No') is False


def test_apuesta_ganada_btts_acierto():
    """apuesta_ganada: BTTS Si correcto → True."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': 'BTTS'}
    pick = {'prediccion_btts': 'Si'}
    assert apuesta_ganada(apuesta, pick, '1', 'Over 2.5', 'Si') is True


def test_apuesta_ganada_corners_no_goles():
    """Regresión: apuesta Corners debe usar corners reales, NO goles."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': 'Corners'}
    pick = {'prediccion_ou': 'Over 2.5', 'prediccion_corners': 'Over'}
    stats = {'corners_total': 12}
    # Si usara goles (resultado Over 2.5) diría True con goles; con corners 12>9.5 también True
    # pero contra corners bajos debe perder aunque el pick de goles aciertte:
    apuesta2 = {'mercado': 'Corners'}
    pick2 = {'prediccion_ou': 'Over 2.5', 'prediccion_corners': 'Over'}
    stats2 = {'corners_total': 8}
    assert apuesta_ganada(apuesta, pick, '2', 'Over 2.5', 'Si', stats) is True
    assert apuesta_ganada(apuesta2, pick2, '2', 'Over 2.5', 'Si', stats2) is False


def test_apuesta_ganada_remates_regresion():
    """Regresión: Remates evalúa tiros reales, ignorando prediccion_ou del pick."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': 'Remates'}
    pick = {'prediccion_ou': 'Under 2.5', 'prediccion_remates': 'Under'}
    stats = {'remates_total': 28}
    # Goles Under acertaría → pero remates 28 > 24 → la apuesta es perdida
    assert apuesta_ganada(apuesta, pick, '1', 'Under 2.5', 'No', stats) is False


def test_apuesta_ganada_tarjetas_arco_regresion():
    """Regresión: Tarjetas/TirosArco evalúan su propio stat."""
    from bet_logic import apuesta_ganada
    assert apuesta_ganada({'mercado': 'Tarjetas'},
                          {'prediccion_ou': 'Over 2.5', 'prediccion_tarjetas': 'Over'},
                          '1', 'Over 2.5', 'Si', {'tarjetas_total': 3}) is False
    assert apuesta_ganada({'mercado': 'Tiros Arco'},
                          {'prediccion_ou': 'Over 2.5', 'prediccion_arco': 'Over'},
                          '1', 'Over 2.5', 'Si', {'tiros_arco_total': 10}) is True


def test_apuesta_ganada_ou_sin_prediccion():
    """O/U sin prediccion_ou en el pick → False (no hace fallback a otros mercados)."""
    from bet_logic import apuesta_ganada
    apuesta = {'mercado': 'O/U'}
    pick = {'prediccion_btts': 'Si'}
    assert apuesta_ganada(apuesta, pick, '1', 'Over 2.5', 'Si') is False


def test_normal_cdf_precision():
    """normal_cdf debe coincidir con Φ de la normal estándar (regresión bug A&S)."""
    from analysis_models import normal_cdf
    casos = {0: 0.5, 1: 0.8413, -1: 0.1587, 2: 0.9772, -2: 0.0228, 1.5: 0.9332}
    for z, esperado in casos.items():
        assert abs(normal_cdf(z) - esperado) < 0.001, f"cdf({z})={normal_cdf(z)}"


def test_dixon_coles_canonico():
    """dc_1x2 con rho=0 debe igualar Poisson (tau=1 en todas las celdas)."""
    from analysis_models import dc_1x2, poisson_1x2
    p1_dc, px_dc, p2_dc = dc_1x2(1.5, 1.2, rho=0)
    p1_po, px_po, p2_po = poisson_1x2(1.5, 1.2)
    # Deben coincidir dentro del redondeo (DC usa grid 9x9 vs 15x15, ±0.5%)
    assert abs(p1_dc - p1_po) < 1.0
    assert abs(px_dc - px_po) < 1.0
    assert abs(p2_dc - p2_po) < 1.0


def test_over_prob_normal_simetria():
    """_over_prob_normal en la media debe dar ~50% (linea = media)."""
    from analysis_models import _over_prob_normal
    prob = _over_prob_normal(media=10, linea=9.5)
    assert 45 < prob < 55


def test_calcular_value_ev():
    """calcular_value: EV% = prob × cuota − 100. Value>0 solo si EV>0."""
    from app_helpers import calcular_value
    v, pi = calcular_value(55, 2.0)   # 55% × 2.0 − 100 = +10 EV
    assert abs(v - 10.0) < 0.01
    v2, _ = calcular_value(45, 2.0)   # 45% × 2.0 − 100 = −10 EV
    assert abs(v2 + 10.0) < 0.01
    v3, _ = calcular_value(50, 0)     # cuota inválida → 0
    assert v3 == 0


def test_estilo_umbrales():
    """analizar_estilo_juego: equipo con muchos corners/tiros → Ofensivo."""
    from analysis_models import analizar_estilo_juego
    ofensivo = analizar_estilo_juego(corners=13, tarjetas=2.0, tiros=15, tiros_arco=11)
    assert ofensivo['tipo'] == 'Ofensivo'
    # Equipo con pocos corners y tiros → puntaje ofensivo bajo
    defensivo = analizar_estilo_juego(corners=5, tarjetas=2.0, tiros=8, tiros_arco=4)
    assert defensivo['estilo_ofensivo'] < 40
    assert defensivo['tipo'] != 'Ofensivo'


def test_confianza_sin_datos():
    """calcular sin últimos-5 debe reducir confianza vs con datos."""
    from analysis_models import calcular
    base = dict(corners_local=5.5, corners_visitante=4.5, tarjetas_local=2.5,
                tarjetas_visitante=2.8, tiros_local=13, tiros_visitante=11,
                tiros_arco_local=4.5, tiros_arco_visitante=3.8)
    sin_datos = calcular(1.8, 0.9, **base)
    con_datos = calcular(1.8, 0.9,
                         ultimos_5_local=[{'resultado': 'W', 'goles_favor': 2, 'goles_contra': 1} for _ in range(5)],
                         ultimos_5_visitante=[{'resultado': 'L', 'goles_favor': 0, 'goles_contra': 2} for _ in range(5)],
                         **base)
    assert con_datos['confianza'] >= sin_datos['confianza']


# ============================================================================
# TESTS: app_helpers.py (normalización de mercados)
# ============================================================================

def test_normalizar_mercados_local_empate_visitante():
    """Local, Empate y Visitante se mapean todos a '1X2'."""
    from app_helpers import normalizar_mercados_para_capital
    result = normalizar_mercados_para_capital({'Local', 'Empate', 'Visitante'})
    assert result == {'1X2'}


def test_normalizar_mercados_directos():
    """Los mercados con el mismo nombre se mantienen."""
    from app_helpers import normalizar_mercados_para_capital
    result = normalizar_mercados_para_capital({'O/U', 'BTTS', 'Corners', 'Remates', 'Tiros Arco', 'Tarjetas'})
    assert result == {'O/U', 'BTTS', 'Corners', 'Remates', 'Tiros Arco', 'Tarjetas'}


def test_normalizar_mercados_ignora_no_soportados():
    """Los mercados no soportados por Capital se omiten."""
    from app_helpers import normalizar_mercados_para_capital
    result = normalizar_mercados_para_capital({'1X', 'X2', '12', 'OU 1.5', 'OU 3.5', 'Goles Local', 'Goles Visitante'})
    assert result == set()


def test_normalizar_mercados_mixto():
    """Mezcla de soportados y no soportados: solo quedan los soportados."""
    from app_helpers import normalizar_mercados_para_capital
    result = normalizar_mercados_para_capital({'Local', 'O/U', '1X', 'Corners', 'OU 1.5'})
    assert result == {'1X2', 'O/U', 'Corners'}


def test_normalizar_mercados_vacio():
    """Set vacío retorna set vacío."""
    from app_helpers import normalizar_mercados_para_capital
    assert normalizar_mercados_para_capital(set()) == set()


def test_mercado_mas_acertado_con_stats():
    """Elige el mercado con mayor % de acierto entre los que tienen >=5 evaluados."""
    from app_helpers import mercado_mas_acertado

    # 1X2: 3/5 (60%), BTTS: 5/5 (100%), OU: 4/5 (80%) -> BTTS gana
    picks = [
        {'acertado_1x2': True, 'acertado_ou': True, 'acertado_btts': True},
        {'acertado_1x2': True, 'acertado_ou': True, 'acertado_btts': True},
        {'acertado_1x2': True, 'acertado_ou': True, 'acertado_btts': True},
        {'acertado_1x2': False, 'acertado_ou': True, 'acertado_btts': True},
        {'acertado_1x2': False, 'acertado_ou': False, 'acertado_btts': True},
    ]
    assert mercado_mas_acertado(picks) == 'BTTS'


def test_mercado_mas_acertado_sin_datos():
    """Sin picks evaluados en ningun mercado, retorna 1X2 por defecto."""
    from app_helpers import mercado_mas_acertado
    assert mercado_mas_acertado([]) == '1X2'


def test_filtrar_value_bets_cuotas_filtra_por_umbral():
    """Solo devuelve value bets que superan el umbral (30% por defecto)."""
    from app_helpers import filtrar_value_bets_cuotas

    cuotas = [
        {'tipo_apuesta': 'Match Winner', 'opcion': 'Home', 'cuota': 5.0, 'bookmaker': 'B1'},
        {'tipo_apuesta': 'Match Winner', 'opcion': 'Draw', 'cuota': 3.5, 'bookmaker': 'B1'},
        {'tipo_apuesta': 'Over/Under', 'opcion': 'Over 2.5', 'cuota': 2.0, 'bookmaker': 'B1'},
    ]
    # p1=80% vs cuota 5.0 -> value = 80*5-100 = 300% (supera 30%)
    # px=15% vs cuota 3.5 -> value = 15*3.5-100 = -47.5% (no supera)
    resultado = filtrar_value_bets_cuotas(cuotas, 80.0, 15.0, 5.0, 50, 50, '1X2', umbral=30.0)
    assert len(resultado) == 1
    assert resultado[0]['detalle'] == 'Local'
    assert resultado[0]['value'] >= 30.0


def test_filtrar_value_bets_cuotas_sin_cuotas():
    """Sin cuotas del mercado objetivo, no devuelve nada."""
    from app_helpers import filtrar_value_bets_cuotas
    cuotas = [{'tipo_apuesta': 'Over/Under', 'opcion': 'Over 2.5', 'cuota': 2.0, 'bookmaker': 'B1'}]
    resultado = filtrar_value_bets_cuotas(cuotas, 50, 25, 25, 50, 50, '1X2')
    assert resultado == []


# ============================================================================
# RUNNER (para ejecutar sin pytest)
# ============================================================================

if __name__ == '__main__':
    tests = [
        # analysis_models
        test_calcular_retorna_todas_las_claves,
        test_calcular_probabilidades_suman_100,
        test_calcular_btts_suman_100,
        test_calcular_over_under_suman_100,
        test_calcular_pick_consistente,
        test_calcular_lambda_alto_favor_local,
        test_calcular_lambda_alto_favor_visitante,
        test_calcular_determinista_con_seed,
        test_pp_poisson_valido,
        test_pp_poisson_k_mayor_lambda,
        test_normal_cdf_rangos,
        # app_helpers
        test_get_pais_emoji_conocido,
        test_get_pais_emoji_desconocido,
        test_get_hoy_formato_fecha,
        test_hash_password_y_verify,
        test_format_money,
        test_utc_to_colombia_conversion,
        test_utc_to_colombia_vacio,
        test_calcular_value,
        # funciones_stats
        test_parse_cuotas_estructura_bookmakers,
        test_parse_cuotas_vacio,
        test_parse_cuotas_sin_bookmakers,
        test_dedup_cuotas,
        # calibration
        test_normalizar_equipo_acentos,
        test_ajustar_lambda,
        test_normalizar_equipo_vacio,
        # input validation
        test_sanitizar_input_basico,
        test_sanitizar_input_quita_peligroso,
        test_sanitizar_input_longitud,
        test_sanitizar_input_vacio,
        test_sanitizar_input_no_espacios,
        # bet_logic
        test_calcular_resultados_gana_local,
        test_calcular_resultados_empate,
        test_calcular_resultados_gana_visitante_over,
        test_calcular_resultados_over_exacto,
        test_evaluar_over_under_acierto,
        test_evaluar_over_under_fallo,
        test_evaluar_over_under_vacio,
        test_apuesta_ganada_1x2_acierto,
        test_apuesta_ganada_1x2_fallo,
        test_apuesta_ganada_ou_acierto,
        test_apuesta_ganada_ou_alias,
        test_apuesta_ganada_btts_acierto,
        test_apuesta_ganada_corners_no_goles,
        test_apuesta_ganada_remates_regresion,
        test_apuesta_ganada_tarjetas_arco_regresion,
        test_apuesta_ganada_ou_sin_prediccion,
        test_normal_cdf_precision,
        test_dixon_coles_canonico,
        test_over_prob_normal_simetria,
        test_calcular_value_ev,
        test_estilo_umbrales,
        test_confianza_sin_datos,
        # normalizacion mercados
        test_normalizar_mercados_local_empate_visitante,
        test_normalizar_mercados_directos,
        test_normalizar_mercados_ignora_no_soportados,
        test_normalizar_mercados_mixto,
        test_normalizar_mercados_vacio,
        # value bets automaticos
        test_mercado_mas_acertado_con_stats,
        test_mercado_mas_acertado_sin_datos,
        test_filtrar_value_bets_cuotas_filtra_por_umbral,
        test_filtrar_value_bets_cuotas_sin_cuotas,
    ]

    passed = 0
    failed = 0
    errors = []

    for test in tests:
        try:
            test()
            print(f'  ✔ {test.__name__}')
            passed += 1
        except Exception as e:
            print(f'  ✗ {test.__name__}: {e}')
            failed += 1
            errors.append((test.__name__, str(e)))

    print(f'\n{"="*60}')
    print(f'Resultado: {passed} pasaron, {failed} fallaron, {len(tests)} total')
    if errors:
        print('\nFallos:')
        for name, err in errors:
            print(f'  ✗ {name}: {err}')
    print(f'{"="*60}')
    sys.exit(0 if failed == 0 else 1)
