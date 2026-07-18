import streamlit as st
from datetime import date, timedelta
from datetime import datetime
import sys
import time
import os
sys.path.append('/workspace/project/Scorpion-elite')

st.set_page_config(page_title='SCORPION ELITE', layout='wide')

# Configuración Supabase (usa secrets.toml en Streamlit Cloud)
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.environ.get("SUPABASE_KEY", ""))
except:
    SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
    SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Cache global para partidos (dura 5 minutos)
PARTIDOS_CACHE = {
    "data": None,
    "timestamp": 0,
    "ttl": 300  # 5 minutos
}

# Cache para datos de un partido específico (dura 10 minutos)
PARTIDO_CACHE = {
    "data": {},
    "ttl": 600  # 10 minutos
}

# Función para formatear fechas
def format_date_display(fecha_date):
    """Convierte fecha a formato DD/MM/YYYY"""
    return fecha_date.strftime("%d/%m/%Y")

def format_date_for_query(fecha_date):
    """Convierte fecha a formato YYYY-MM-DD para consultas"""
    return fecha_date.strftime("%Y-%m-%d")

# Generar opciones de fechas (hoy + 6 días)
def get_date_options():
    """Genera opciones de fechas para el selector"""
    today = date.today()
    options = []
    for i in range(7):
        d = today + timedelta(days=i)
        options.append((d, format_date_display(d)))
    return options

BG = '#070b0e'
CARD = '#0d131a'
BORDER = '#1b2430'
GREEN = '#22c55e'
TITLE = '#a3e635'
MUTED = '#94a3b8'
ORANGE = '#f59e0b'

ADMIN_USER = "admin"
ADMIN_PASS = "scorpion_admin_2025"

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'show_login' not in st.session_state:
    st.session_state.show_login = False
if 'deporte' not in st.session_state:
    st.session_state.deporte = "FUTBOL"
if 'fecha_seleccionada' not in st.session_state:
    st.session_state.fecha_seleccionada = date.today()

# Asegurar que la fecha siempre sea valida
try:
    if st.session_state.fecha_seleccionada > date.today():
        st.session_state.fecha_seleccionada = date.today()
except:
    st.session_state.fecha_seleccionada = date.today()

st.markdown(f'''
<style>
.stApp {{background-color:{BG}; padding-top:0px !important;}}
[data-testid="stSidebar"] {{display:none;}}
header {{display:none !important;}}
.stDeployButton {{display:none;}}
[data-testid="stMainBlockContainer"] {{padding:0; padding-top:0; background:{BG}; max-width:100%;}}
[data-testid="stMain"] {{padding:0; background:{BG};}}
table {{border-collapse: collapse; width: 100%;}}
th, td {{border: none;}}
.stHorizontalBlock {{gap:0.5rem;}}
</style>
''', unsafe_allow_html=True)

# LOGIN MODAL
if st.session_state.show_login:
    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:12px; padding:30px; margin-top:60px; text-align:center;">', unsafe_allow_html=True)
            st.markdown(f'<div style="color:{ORANGE}; font-size:24px; font-weight:bold; margin-bottom:5px;">INICIAR SESION</div>', unsafe_allow_html=True)
            
            username = st.text_input("Usuario", placeholder="Ingrese usuario", key="user_input")
            password = st.text_input("Contrasena", type="password", placeholder="Ingrese contrasena", key="pass_input")
            
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("ENTRAR", use_container_width=True):
                    if username == ADMIN_USER and password == ADMIN_PASS:
                        st.session_state.logged_in = True
                        st.session_state.is_admin = True
                        st.session_state.user_name = username
                        st.session_state.show_login = False
                        st.rerun()
                    else:
                        st.error("Datos incorrectos")
            with col_b:
                if st.button("CANCELAR", use_container_width=True):
                    st.session_state.show_login = False
                    st.rerun()
            
            st.markdown(f'<div style="color:{MUTED}; font-size:9px; margin-top:10px;">Scorpion Elite 2025</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ADMIN VIEW
if st.session_state.is_admin:
    st.markdown(f'''
    <div style="background:{CARD}; padding:12px 30px; border-bottom:1px solid {BORDER}; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="color:{ORANGE}; font-size:20px; font-weight:bold;">PANEL DE ADMINISTRADOR</div>
            <div style="color:{MUTED}; font-size:9px;">Bienvenido, {st.session_state.user_name}</div>
        </div>
        <div style="display:flex; gap:8px;">
            <span style="background:{GREEN}; color:{BG}; padding:6px 14px; border-radius:4px; font-size:11px;">Dashboard</span>
            <span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">Gestionar Picks</span>
            <span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">Usuarios</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Gestionar Picks", "Usuarios"])
    
    with tab1:
        m1, m2, m3, m4 = st.columns(4)
        with m1: st.metric("Usuarios Totales", "156")
        with m2: st.metric("Picks Publicados", "89")
        with m3: st.metric("Aciertos", "72%")
        with m4: st.metric("Ingresos", "$1,250")
    
    with tab2:
        st.markdown("### Crear Pick")
        col_a, col_b = st.columns(2)
        with col_a:
            liga = st.selectbox("Liga", ["Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1"])
            partido = st.text_input("Partido", "Manchester City vs Arsenal")
            mercado = st.selectbox("Mercado", ["Resultado Final", "Over/Under", "Ambos marcan", "Handicap"])
        with col_b:
            cuota = st.number_input("Cuota", min_value=1.01, max_value=100.0, value=1.91)
            rango = st.selectbox("Rango", ["A+", "A", "B", "C"])
            confianza = st.slider("Confianza", 50, 100, 85)
        
        if st.button("Publicar Pick"):
            st.success("Pick publicado exitosamente!")
    
    with tab3:
        st.markdown("### Gestion de Usuarios")
        st.table({"Usuario": ["juan123", "maria456", "pedro789"], "Plan": ["Premium", "Basico", "Premium"], "Estado": ["Activo", "Activo", "Suspendido"]})
    
    if st.button("Cerrar Sesion"):
        st.session_state.logged_in = False
        st.session_state.is_admin = False
        st.session_state.user_name = ""
        st.rerun()
    st.stop()

# HEADER con columnas
col_left, col_center, col_right = st.columns([2.5, 4, 2])

with col_left:
    st.markdown(f'''
    <div style="display:flex; align-items:center; gap:8px;">
        <span style="font-size:22px;">🦂</span>
        <div style="font-size:16px; font-weight:bold;">
            <span style="color:white;">SCORPION</span><span style="color:{ORANGE};"> ELITE</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

with col_center:
    if st.button("⚽ FUTBOL", key="btn_futbol"):
        st.session_state.deporte = "FUTBOL"
    # with s2:
    #     if st.button("🏀 BALONCESTO", key="btn_basket"):
    #         st.session_state.deporte = "BALONCESTO"
    # with s3:
    #     if st.button("🎾 TENIS", key="btn_tenis"):
    #         st.session_state.deporte = "TENIS"

with col_right:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        # Selector de fechas con formato DD/MM/YYYY
        date_options = get_date_options()
        date_labels = [opt[1] for opt in date_options]  # ["17/07/2026", "18/07/2026", ...]
        date_values = [opt[0] for opt in date_options]  # [date objects]
        
        # Encontrar el índice de la fecha seleccionada o usar 0 (hoy)
        try:
            selected_index = date_values.index(st.session_state.fecha_seleccionada)
        except:
            selected_index = 0
            st.session_state.fecha_seleccionada = date_values[0]
        
        selected_label = st.selectbox("", date_labels, index=selected_index, key="calendario")
        
        # Actualizar la fecha seleccionada
        idx = date_labels.index(selected_label)
        st.session_state.fecha_seleccionada = date_values[idx]
        fecha = st.session_state.fecha_seleccionada
    with c2:
        if st.button("LOGIN", key="login_btn"):
            st.session_state.show_login = True
            st.rerun()

# CONTENEDOR UNIFICADO PARA LAS 3 TARJETAS - COMPACTO
st.markdown(f'<div style="background:{CARD}; border:2px solid {BORDER}; border-radius:12px; padding:12px; margin:8px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">', unsafe_allow_html=True)

# 3 COLUMNAS - TARJETAS COMPACTAS
c1, c2, c3 = st.columns(3)

# Iconos por deporte
DEPORTE_ICONS = {
    "FUTBOL": "⚽",
    "BALONCESTO": "🏀",
    "TENIS": "🎾"
}

# API Keys - Múltiples para mayor cobertura
API_KEYS = [
    "e3926f829cd848f4b2b54d722ca29701",  # API-Football key 1
    "124c9519df145caf883cd82f0b2a4671",  # API-Football key 2
]


def obtener_partidos_de_supabase(fecha_str):
    """Obtiene partidos desde Supabase ( fuente principal )"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Consultar partidos de la fecha, ordenados por prioridad DESCENDENTE
        response = supabase.table("partidos").select("*").eq("fecha", fecha_str).order("prioridad", desc=True).execute()
        
        if response.data:
            return response.data
        return None
    except Exception as e:
        print(f"Error conectando a Supabase: {e}")
        return None


def convertir_partidos_supabase_a_fixture(datos_supabase):
    """Convierte datos de Supabase al formato de fixture que usa la app"""
    fixtures = []
    for p in datos_supabase:
        # Mantener la prioridad para ordenar correctamente
        fixtures.append({
            "fixture": {
                "id": p.get("fixture_id", 0),
                "date": f"{p.get('fecha', '')}T{p.get('hora_utc', '00:00')}",
                "prioridad": p.get("prioridad", 1)
            },
            "league": {
                "id": p.get("liga_id", 0),
                "name": p.get("liga", "Liga"),
                "country": p.get("pais", "")
            },
            "teams": {
                "home": {"id": 0, "name": p.get("equipo_home", "Local")},
                "away": {"id": 0, "name": p.get("equipo_away", "Visita")}
            }
        })
    return fixtures

def obtener_partidos_todas_apis(fecha_str):
    """Obtiene partidos de Supabase (primario) o APIs (fallback)"""
    import requests
    from datetime import datetime, timedelta
    from bs4 import BeautifulSoup
    
    # Verificar caché
    cache_key = f"partidos_{fecha_str}"
    now = time.time()
    
    if cache_key in st.session_state:
        cached = st.session_state[cache_key]
        if cached and (now - cached.get("time", 0)) < 300:  # 5 min cache
            return cached.get("data", [])
    
    all_partidos = []
    
    # 1. PRIMERO: Intentar con Supabase (fuente principal)
    datos_supabase = obtener_partidos_de_supabase(fecha_str)
    if datos_supabase:
        all_partidos = convertir_partidos_supabase_a_fixture(datos_supabase)
        print(f"✅ Obtenidos {len(all_partidos)} partidos de Supabase")
    else:
        print("📡 Supabase vacío, usando APIs como fallback...")
    
    # 2. FALLBACK: Si no hay datos en Supabase, usar APIs
    if not all_partidos:
        # Intentar con API-Football
        for api_key in API_KEYS:
            try:
                url = f"https://v3.football.api-sports.io/fixtures?date={fecha_str}"
                headers = {"x-apisports-key": api_key}
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("response"):
                        all_partidos.extend(data["response"])
            except:
                continue
        
        # Si no hay partidos, intentar con TheSportsDB
        if not all_partidos:
            try:
                url = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php"
                params = {"d": fecha_str}
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    events = data.get("events", []) or []
                    
                    for event in events:
                        sport = event.get("strSport", "")
                        if sport != "Soccer":
                            continue
                        
                        all_partidos.append({
                            "fixture": {
                                "id": event.get("idEvent", 0),
                                "date": event.get("dateEvent", "") + "T" + event.get("strTime", "00:00"),
                                "timestamp": 0
                            },
                            "league": {
                                "id": 0,
                                "name": event.get("strLeague", "Liga"),
                                "country": ""
                            },
                            "teams": {
                                "home": {"id": 0, "name": event.get("strHomeTeam", "Local")},
                                "away": {"id": 0, "name": event.get("strAwayTeam", "Visita")}
                            }
                        })
            except:
                pass
        
        # Si sigue sin haber partidos, hacer scraping de Flashscore
        if not all_partidos:
            try:
                url = "https://www.flashscore.com/"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Buscar partidos en la página
                    events = soup.find_all('div', class_='event__match')
                    
                    for event in events[:10]:
                        try:
                            home = event.find('div', class_='event__homeParticipant')
                            away = event.find('div', class_='event__awayParticipant')
                            time_elem = event.find('div', class_='event__time')
                            league = event.find_previous('div', class_='event__league')
                            
                            if home and away:
                                all_partidos.append({
                                    "fixture": {
                                        "id": hash(home.text + away.text),
                                        "date": fecha_str + "T" + (time_elem.text if time_elem else "00:00"),
                                        "timestamp": 0
                                    },
                                    "league": {
                                        "id": 0,
                                        "name": league.text if league else "Liga",
                                        "country": ""
                                    },
                                    "teams": {
                                        "home": {"id": 0, "name": home.text.strip()},
                                        "away": {"id": 0, "name": away.text.strip()}
                                    }
                                })
                        except:
                            continue
            except:
                pass
    
    # Eliminar duplicados por fixture_id
    seen_ids = set()
    unique_partidos = []
    for p in all_partidos:
        fixture_id = p["fixture"]["id"]
        if fixture_id not in seen_ids:
            seen_ids.add(fixture_id)
            unique_partidos.append(p)
    
    # Guardar en caché
    st.session_state[cache_key] = {
        "data": unique_partidos,
        "time": time.time()
    }
    
    return unique_partidos

# Prioridad de ligas segun interes mundial (SIN DUPLICADOS)
LIGAS_PRIORIDAD = {
    # TOP TIER - Mayor atencion mundial
    "champions league": 15,
    "premier league": 14,
    "la liga": 13,
    "serie a": 12,  # Italia
    "bundesliga": 11,
    "ligue 1": 10,
    
    # SECOND TIER - Alto interes
    "europa league": 9,
    "libertadores": 8,
    "copa america": 8,
    "euro": 8,
    "world cup": 8,
    
    # THIRD TIER - Medio interes (ligas con muchos goles)
    "brasileiro": 7,  # Brasil Serie A
    "brasil": 7,      # Alternativa para Brasil
    "eredivisie": 7,
    "liga mx": 6,
    "major league soccer": 5,
    "primeira liga": 5,
    "super lig": 5,
    "copa argentina": 5,
    "copa sudamericana": 5,
    
    # FOURTH TIER - Menor interes
    "canadian premier league": 4,
    "liga pro": 4,
    "paraguay": 4,
    "chile": 4,
    "colombia": 4,
    "betplay": 4,
    "uruguay": 4,
    "peru": 4,
    "bolivia": 4,
    
    # FIFTH TIER - Divisions menores
    "league two": 2,
    "usl": 2,
    "national league": 2,
}

# Mapeo de league_id a prioridad para evitar ambiguedades
LIGAS_POR_ID = {
    71: 7,   # Serie A Brasil (Brasileiro)
    39: 14,  # Premier League
    140: 13, # La Liga
    135: 12, # Serie A Italia
    78: 11,  # Bundesliga
    61: 10,  # Ligue 1
    253: 5,  # MLS
    262: 6,  # Liga MX
}

def obtener_partidos_futbol(todos=False):
    """Obtiene partidos de futbol para hoy desde TODAS las APIs
    
    Args:
        todos: Si True, retorna todos los partidos. Si False, solo los 3 mas importantes.
    """
    import requests
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Buscar en TODAS las APIs
    try:
        # Usar la fecha seleccionada por el usuario
        fecha_str = format_date_for_query(fecha)
        
        # Usar función que busca en todas las APIs
        todos_fixture = obtener_partidos_todas_apis(fecha_str)
        
        if todos_fixture:
            for fixture in todos_fixture:
                try:
                    home = fixture["teams"]["home"]["name"]
                    away = fixture["teams"]["away"]["name"]
                    league = fixture["league"]["name"].lower()
                    league_id = fixture["league"]["id"]
                    country = fixture["league"]["country"]
                    hora = fixture["fixture"]["date"][11:16]
                    
                    # Convertir UTC a UTC-3 (America)
                    try:
                        dt = datetime.strptime(hora, "%H:%M")
                        dt = dt + timedelta(hours=-3)
                        hora_local = dt.strftime("%H:%M")
                    except:
                        hora_local = hora
                    
                    # Calcular prioridad por league_id (mas preciso)
                    prioridad = LIGAS_POR_ID.get(league_id, 0)
                    
                    # Si no hay prioridad por ID, buscar por nombre
                    if prioridad == 0:
                        for nombre_liga, prio in LIGAS_PRIORIDAD.items():
                            if nombre_liga in league:
                                prioridad = prio
                                break
                    
                    # Combinar liga + pais
                    liga_completa = fixture["league"]["name"]
                    if country:
                        liga_completa = f"{liga_completa} ({country})"
                    
                    partidos.append({
                        "equipo": f"{home} vs {away}",
                        "hora": hora_local,
                        "liga": liga_completa,
                        "prioridad": prioridad,
                        "league_lower": league,
                        "league_id": league_id
                    })
                except:
                    continue
    except Exception as e:
        print(f"Error buscando partidos: {e}")
    
    # Eliminar duplicados
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = p["equipo"]
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        return [{"equipo": "Sin partidos disponibles", "hora": "--:--", "liga": "Verifica conexion"}]
    
    # Si no queremos todos, filtrar solo los mas importantes
    if not todos:
        # Ordenar por prioridad (descendente)
        unique_partidos.sort(key=lambda x: x.get("prioridad", 0), reverse=True)
        # Tomar solo los 3 primeros
        unique_partidos = unique_partidos[:3]
    
    return unique_partidos


def obtener_mejor_pick():
    """Obtiene el mejor partido del día con datos REALES de cuotas y predicciones (con caché)"""
    import requests
    from datetime import datetime, timedelta
    
    mejor_partido = None
    mejor_prioridad = 0
    
    # Buscar en TODAS las APIs disponibles
    try:
        # Usar la fecha seleccionada por el usuario
        fecha_str = format_date_for_query(fecha)
        
        # Usar función que busca en todas las APIs
        todos_fixture = obtener_partidos_todas_apis(fecha_str)
        
        if todos_fixture:
            for fixture in todos_fixture:
                try:
                    home = fixture["teams"]["home"]["name"]
                    away = fixture["teams"]["away"]["name"]
                    league = fixture["league"]["name"].lower()
                    league_id = fixture["league"]["id"]
                    country = fixture["league"]["country"]
                    fixture_id = fixture["fixture"]["id"]
                    hora = fixture["fixture"]["date"][11:16]
                    
                    # Convertir UTC a UTC-3 (America)
                    try:
                        dt = datetime.strptime(hora, "%H:%M")
                        dt = dt + timedelta(hours=-3)
                        hora_local = dt.strftime("%H:%M")
                    except:
                        hora_local = hora
                    
                    # Calcular prioridad por league_id (mas preciso)
                    prioridad = LIGAS_POR_ID.get(league_id, 0)
                    
                    # Si no hay prioridad por ID, buscar por nombre
                    if prioridad == 0:
                        for nombre_liga, prio in LIGAS_PRIORIDAD.items():
                            if nombre_liga in league:
                                prioridad = prio
                                break
                    
                    # Seleccionar el de mayor prioridad
                    if prioridad > mejor_prioridad:
                        mejor_prioridad = prioridad
                        liga_completa = fixture["league"]["name"]
                        if country:
                            liga_completa = f"{liga_completa} ({country})"
                        
                        mejor_partido = {
                            "home": home,
                            "away": away,
                            "liga": liga_completa,
                            "hora": hora_local,
                            "prioridad": prioridad,
                            "fixture_id": fixture_id,
                            "league_id": league_id
                        }
                except:
                    continue
    except Exception as e:
        print(f"Error obteniendo mejor pick: {e}")
    
    if not mejor_partido:
        return None
    
    # Verificar caché para predicciones/cuotas
    fixture_id = mejor_partido["fixture_id"]
    cache_key = f"pick_{fixture_id}"
    now = time.time()
    
    if cache_key in st.session_state:
        cached = st.session_state[cache_key]
        if cached and (now - cached.get("time", 0)) < 600:  # 10 min cache
            return cached.get("data")
    
    # Obtener datos REALES: cuotas y predicciones de API-Football
    try:
        # Obtener predictions reales
        url_pred = f"https://v3.football.api-sports.io/predictions?fixture={fixture_id}"
        response_pred = requests.get(url_pred, headers={"x-apisports-key": API_KEYS[0]}, timeout=15)
        
        prob_home = 50
        prob_draw = 30
        prob_away = 20
        
        if response_pred.status_code == 200:
            data_pred = response_pred.json()
            pred_response = data_pred.get("response", [])
            if pred_response:
                pred = pred_response[0].get("predictions", {})
                
                # Extraer porcentajes reales
                percent = pred.get("percent", {})
                if percent:
                    home_pct = percent.get("home", "50%").replace("%", "")
                    draw_pct = percent.get("draw", "30%").replace("%", "")
                    away_pct = percent.get("away", "20%").replace("%", "")
                    
                    try:
                        prob_home = int(home_pct)
                        prob_draw = int(draw_pct)
                        prob_away = int(away_pct)
                    except:
                        pass
        
        # Obtener cuotas reales del mercado
        url_odds = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"
        response_odds = requests.get(url_odds, headers={"x-apisports-key": API_KEYS[0]}, timeout=15)
        
        cuota_1 = 1.90
        cuota_x = 3.50
        cuota_2 = 4.00
        cuota_over25 = 1.90
        cuota_btts_si = 1.80
        bookie = "Mercado"
        
        if response_odds.status_code == 200:
            data_odds = response_odds.json()
            odds_response = data_odds.get("response", [])
            if odds_response:
                bookmakers = odds_response[0].get("bookmakers", [])
                if bookmakers:
                    bookie = bookmakers[0].get("name", "Mercado")
                    bets = bookmakers[0].get("bets", [])
                    
                    for bet in bets:
                        bet_name = bet.get("name", "")
                        values = bet.get("values", [])
                        
                        if bet_name == "Match Winner":
                            for v in values:
                                if v.get("value") == "Home":
                                    cuota_1 = float(v.get("odd", cuota_1))
                                elif v.get("value") == "Draw":
                                    cuota_x = float(v.get("odd", cuota_x))
                                elif v.get("value") == "Away":
                                    cuota_2 = float(v.get("odd", cuota_2))
                        
                        elif "Goals Over/Under" in bet_name and "2.5" in str(values):
                            for v in values:
                                if "Over 2.5" in v.get("value", ""):
                                    cuota_over25 = float(v.get("odd", cuota_over25))
                        
                        elif "Both Teams Score" in bet_name:
                            for v in values:
                                if v.get("value") == "Yes":
                                    cuota_btts_si = float(v.get("odd", cuota_btts_si))
        
        # Determinar pick basado en la predicción real
        if prob_home >= prob_draw and prob_home >= prob_away:
            pick = f"Gana {mejor_partido['home']}"
            cuota_pick = cuota_1
            prob_pick = prob_home
        elif prob_away >= prob_draw and prob_away >= prob_home:
            pick = f"Gana {mejor_partido['away']}"
            cuota_pick = cuota_2
            prob_pick = prob_away
        else:
            pick = "Empate"
            cuota_pick = cuota_x
            prob_pick = prob_draw
        
        # Calcular valor (comparando con probabilidad implícita)
        prob_implicita = round(100 / cuota_pick, 1) if cuota_pick > 0 else 50
        valor = round(prob_pick - prob_implicita, 1)
        
        # Calcular confianza basada en consistencia
        total_prob = prob_home + prob_draw + prob_away
        confianza = round((max(prob_home, prob_draw, prob_away) / total_prob) * 100, 0) if total_prob > 0 else 50
        
        result = {
            "liga": mejor_partido["liga"],
            "home": mejor_partido["home"],
            "away": mejor_partido["away"],
            "hora": mejor_partido["hora"],
            "pick": pick,
            "cuota": cuota_pick,
            "probabilidad": prob_pick,
            "confianza": confianza,
            "valor": f"{'+' if valor > 0 else ''}{valor}%",
            "rango": "A" if confianza >= 60 else ("B" if confianza >= 50 else "C"),
            "over25": round(100 / cuota_over25, 0) if cuota_over25 > 0 else 50,
            "btts": round(100 / cuota_btts_si, 0) if cuota_btts_si > 0 else 50,
            "bookie": bookie,
            "p1": prob_home,
            "px": prob_draw,
            "p2": prob_away,
            "cuota_1": cuota_1,
            "cuota_x": cuota_x,
            "cuota_2": cuota_2
        }
        
        # Guardar en caché
        st.session_state[cache_key] = {
            "data": result,
            "time": time.time()
        }
        
        return result
    except Exception as e:
        print(f"Error obteniendo datos reales: {e}")
        return None


# Prioridad de competiciones de baloncesto
BALONCESTO_PRIORIDAD = {
    # TOP TIER
    "nba": 10,
    "euroleague": 9,
    "olimpicos": 9,
    "mundial": 9,
    
    # SECOND TIER
    "eurocup": 7,
    "liga acb": 7,
    "liga endesa": 7,
    "serie a1": 6,
    
    # THIRD TIER
    "wnba": 5,
    "ligue 1": 4,
    "bundesliga": 4,
}

def obtener_partidos_baloncesto():
    """Obtiene partidos de baloncesto para hoy - solo los 3 mas importantes"""
    import requests
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Fuente: TheSportsDB Basketball (NBA)
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/eventspastleague.php?id=4387"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            for event in events[:10]:
                try:
                    home = event.get("strHomeTeam", "")
                    away = event.get("strAwayTeam", "")
                    league = event.get("strLeague", "")
                    
                    # Verificar que sea basketball (filtrar partidos de futbol)
                    if home and away and home != "None" and away != "None":
                        if "basketball" not in league.lower() and "nba" not in league.lower():
                            continue  # Saltar si no es basketball
                            
                        date = event.get("dateEvent", "")
                        time = event.get("strTime", "")
                        hora = time.split(" ")[-1][:5] if time and time != "None" else "--:--"
                        
                        # Solo mostrar partidos recientes (ultimos 7 dias)
                        if date:
                            try:
                                event_date = datetime.strptime(date, "%Y-%m-%d")
                                today = datetime.now()
                                days_diff = (today - event_date).days
                                
                                if days_diff <= 7:
                                    partidos.append({
                                        "equipo": f"{home} vs {away}",
                                        "hora": hora,
                                        "liga": league if league else "NBA",
                                        "prioridad": 10,
                                        "fecha": date
                                    })
                            except:
                                pass
                except:
                    continue
    except Exception as e:
        print(f"Error Basketball: {e}")
    
    # Eliminar duplicados y ordenar
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = p["equipo"]
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        return [{"equipo": "Temporada baja", "hora": "--:--", "liga": "NBA/EuroLeague - Inicia Oct"}]
    
    # Ordenar por prioridad y luego por fecha
    unique_partidos.sort(key=lambda x: (-x.get("prioridad", 0), x.get("fecha", "")))
    return unique_partidos[:3]

# Prioridad de torneos de tenis
TENIS_PRIORIDAD = {
    # TOP TIER - Grand Slams
    "australian open": 10,
    "roland garros": 10,
    "wimbledon": 10,
    "us open": 10,
    "grand slam": 10,
    
    # SECOND TIER - Masters 1000
    "masters": 8,
    "atp finals": 8,
    "wta finals": 8,
    
    # THIRD TIER - ATP/WTA Tour
    "atp": 6,
    "wta": 5,
    "challenger": 3,
    "itf": 2,
}

def obtener_partidos_tenis():
    """Obtiene partidos de tenis para hoy - solo los 3 mas importantes"""
    import requests
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Fuente: TheSportsDB Tennis ATP
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/eventspastleague.php?id=4464"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            for event in events[:15]:
                try:
                    home = event.get("strHomeTeam") or ""
                    away = event.get("strAwayTeam") or ""
                    league = event.get("strLeague") or ""
                    
                    # Verificar que sea tenis (filtrar partidos de otros deportes)
                    league_lower = league.lower()
                    if "tennis" in league_lower or "tenis" in league_lower or "atp" in league_lower:
                        # Para tenis, puede que venga sin nombres de jugadores
                        if home and away and str(home) != "None" and str(away) != "None":
                            date = event.get("dateEvent") or ""
                            time = event.get("strTime") or ""
                            hora = time.split(" ")[-1][:5] if time and str(time) != "None" else "--:--"
                            
                            # Calcular prioridad
                            prioridad = 0
                            for nombre, prio in TENIS_PRIORIDAD.items():
                                if nombre in league_lower:
                                    prioridad = prio
                                    break
                            
                            if not prioridad:
                                prioridad = 5  # Default para ATP
                            
                            # Solo partidos de ultimos 7 dias
                            if date:
                                try:
                                    event_date = datetime.strptime(date, "%Y-%m-%d")
                                    today = datetime.now()
                                    days_diff = (today - event_date).days
                                    
                                    if days_diff <= 7:
                                        partidos.append({
                                            "equipo": f"{home} vs {away}",
                                            "hora": hora,
                                            "liga": league if league else "ATP",
                                            "prioridad": prioridad,
                                            "fecha": date
                                        })
                                except:
                                    pass
                except Exception as e:
                    print(f"Error parsing tennis event: {e}")
                    continue
    except Exception as e:
        print(f"Error Tennis: {e}")
    
    # Eliminar duplicados y ordenar
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = p["equipo"]
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        return [{"equipo": "Sin partidos hoy", "hora": "--:--", "liga": "ATP/WTA - Verificar mañana"}]
    
    # Ordenar por prioridad y tomar los 3 primeros
    unique_partidos.sort(key=lambda x: (-x.get("prioridad", 0), x.get("fecha", "")))
    return unique_partidos[:3]

def obtener_partidos_en_vivo(deporte):
    """Función general para obtener partidos en vivo"""
    if deporte == "FUTBOL":
        return obtener_partidos_futbol()
    elif deporte == "BALONCESTO":
        return obtener_partidos_baloncesto()
    elif deporte == "TENIS":
        return obtener_partidos_tenis()
    return []

deporte = st.session_state.deporte
icono = DEPORTE_ICONS.get(deporte, "⚽")

# Obtener partidos en tiempo real
partidos = obtener_partidos_en_vivo(deporte)

# Obtener el Mejor Pick del Día (analizado con modelos matemáticos)
mejor_pick = obtener_mejor_pick()

with c1:
    # Construir filas de la tabla
    filas_html = ""
    for i, p in enumerate(partidos):
        borde = f"border-top:1px solid {BORDER};" if i > 0 else ""
        filas_html += f'''<tr style="{borde}">
<td style="padding:8px 6px; color:white; font-size:10px;">{p["equipo"]}</td>
<td style="padding:8px 6px; color:{ORANGE}; font-size:10px; text-align:center; font-weight:bold;">{p["hora"]}</td>
<td style="padding:8px 6px; color:{MUTED}; font-size:9px; text-align:center;" title="{p["liga"]}">{p["liga"]}</td>
</tr>'''
    
    tabla_html = f'''<div style="background:{BG}; border:2px solid {TITLE}; border-radius:10px; padding:12px;">
<div style="color:{TITLE}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px; margin-bottom:10px;">
{icono} PARTIDOS DESTACADOS
</div>
<table style="width:100%; border-collapse:collapse;">
<tr style="border-bottom:1px solid {BORDER};">
<th style="color:{MUTED}; font-size:9px; text-align:left; padding:4px 6px; width:50%;">EQUIPO</th>
<th style="color:{MUTED}; font-size:9px; text-align:center; padding:4px 6px; width:20%;">HORA</th>
<th style="color:{MUTED}; font-size:9px; text-align:center; padding:4px 6px; width:30%;">LIGA</th>
</tr>
{filas_html}
</table></div>'''
    st.markdown(tabla_html, unsafe_allow_html=True)

with c2:
    # Usar datos REALES del partido
    if mejor_pick:
        PICK_LIGA = mejor_pick.get("liga", "Liga")
        PICK_LOCAL = mejor_pick.get("home", "Local")
        PICK_VISITA = mejor_pick.get("away", "Visita")
        PICK_NOMBRE = mejor_pick.get("pick", "Pick")
        PICK_CUOTA = f"{mejor_pick.get('cuota', 1.50):.2f}"
        PICK_PROB = f"{mejor_pick.get('probabilidad', 0):.0f}"
        PICK_CONF = f"{mejor_pick.get('confianza', 0):.0f}"
        PICK_VALOR = mejor_pick.get("valor", "+0%")
        PICK_HORA = mejor_pick.get("hora", "--:--")
        PICK_RANGO = mejor_pick.get("rango", "C")
        PICK_BOOKIE = mejor_pick.get("bookie", "Mercado")
        PICK_OVER25 = f"{mejor_pick.get('over25', 0):.0f}%"
        PICK_BTTS = f"{mejor_pick.get('btts', 0):.0f}%"
        # Cuotas 1X2
        PICK_C1 = f"{mejor_pick.get('cuota_1', 1.90):.2f}"
        PICK_CX = f"{mejor_pick.get('cuota_x', 3.50):.2f}"
        PICK_C2 = f"{mejor_pick.get('cuota_2', 4.00):.2f}"
        # Probabilidades reales
        PICK_P1 = f"{mejor_pick.get('p1', 50)}%"
        PICK_PX = f"{mejor_pick.get('px', 30)}%"
        PICK_P2 = f"{mejor_pick.get('p2', 20)}%"
    else:
        PICK_LIGA = "Sin partidos"
        PICK_LOCAL = "Sin datos"
        PICK_VISITA = ""
        PICK_NOMBRE = "Sin analisis"
        PICK_CUOTA = "0.00"
        PICK_PROB = "0"
        PICK_CONF = "0"
        PICK_VALOR = "+0%"
        PICK_HORA = "--:--"
        PICK_RANGO = "D"
        PICK_BOOKIE = "N/A"
        PICK_OVER25 = "0%"
        PICK_BTTS = "0%"
        PICK_C1 = "1.90"
        PICK_CX = "3.50"
        PICK_C2 = "4.00"
        PICK_P1 = "50%"
        PICK_PX = "30%"
        PICK_P2 = "20%"
    
    st.markdown(f'''
    <div style="background:{BG}; border:2px solid {ORANGE}; border-radius:10px; padding:12px;">
        <div style="color:{ORANGE}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px; margin-bottom:10px;">
            ⭐ MEJOR PICK DEL DÍA
        </div>
        <div style="background:{BG}; border:1px solid {ORANGE}; border-radius:6px; padding:10px;">
            <div style="text-align:center; color:{GREEN}; font-size:10px; margin-bottom:4px;">🏆 {PICK_LIGA} · {PICK_HORA}</div>
            <div style="text-align:center; margin:4px 0;"><span style="font-size:13px; font-weight:bold;">{PICK_LOCAL}</span> <span style="color:{MUTED};">vs</span> <span style="font-size:13px; font-weight:bold;">{PICK_VISITA}</span></div>
            <div style="background:{CARD}; border:1px solid {ORANGE}; border-radius:6px; padding:6px; display:flex; justify-content:space-between; margin-top:6px;"><div><div style="color:{MUTED}; font-size:7px;">MERCADO</div><div style="font-weight:bold; color:white; font-size:10px;">{PICK_NOMBRE}</div></div><div style="text-align:right;"><div style="color:{MUTED}; font-size:7px;">CUOTA</div><div style="font-size:16px; font-weight:bold; color:{ORANGE};">{PICK_CUOTA}</div></div></div>
            <div style="display:flex; justify-content:space-around; margin-top:6px;">
                <div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">PROB</div><div style="color:{GREEN}; font-size:13px; font-weight:bold;">{PICK_PROB}%</div></div>
                <div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">CONF</div><div style="color:{GREEN}; font-size:13px; font-weight:bold;">{PICK_CONF}%</div></div>
                <div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">VALOR</div><div style="color:{GREEN}; font-size:13px; font-weight:bold;">{PICK_VALOR}</div></div>
            </div>
            <div style="border-top:1px solid {BORDER}; margin-top:6px; padding-top:6px;">
                <div style="text-align:center; color:{MUTED}; font-size:8px; margin-bottom:4px;">📊 CUOTAS REALES ({PICK_BOOKIE})</div>
                <div style="display:flex; justify-content:space-around; font-size:9px;">
                    <div><span style="color:{MUTED};">1:</span> <span style="color:white; font-weight:bold;">{PICK_C1}</span> <span style="color:{GREEN};">({PICK_P1})</span></div>
                    <div><span style="color:{MUTED};">X:</span> <span style="color:white; font-weight:bold;">{PICK_CX}</span> <span style="color:{GREEN};">({PICK_PX})</span></div>
                    <div><span style="color:{MUTED};">2:</span> <span style="color:white; font-weight:bold;">{PICK_C2}</span> <span style="color:{GREEN};">({PICK_P2})</span></div>
                </div>
            </div>
            <div style="border-top:1px solid {BORDER}; margin-top:6px; padding-top:6px; display:flex; justify-content:space-between; font-size:8px;">
                <div style="color:{MUTED};">O2.5: {PICK_OVER25}</div>
                <div style="color:{MUTED};">BTTS: {PICK_BTTS}</div>
                <div style="color:{ORANGE}; font-weight:bold;">Rango: {PICK_RANGO}</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)

with c3:
    st.markdown(f'''
    <div style="background:{BG}; border:2px solid {GREEN}; border-radius:10px; padding:12px;">
        <div style="color:{GREEN}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px; margin-bottom:10px;">
            📊 COMPARADOR
        </div>
        <div style="background:{BG}; border:1px solid {GREEN}; border-radius:6px; padding:10px;">
            <table style="width:100%; border-collapse:collapse;">
                <tr style="border-bottom:1px solid {BORDER};">
                    <th style="color:{MUTED}; font-size:9px; text-align:left; padding:6px;">CASA</th>
                    <th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px;">1</th>
                    <th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px;">X</th>
                    <th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px;">2</th>
                </tr>
                <tr>
                    <td style="padding:6px; color:white; font-size:9px;">⭐ Pinnacle</td><td style="padding:6px; color:{ORANGE}; font-size:9px; text-align:center; font-weight:bold;">1.91</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">3.80</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">4.20</td>
                </tr>
                <tr style="border-top:1px solid {BORDER};">
                    <td style="padding:6px; color:white; font-size:9px;">Bet365</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">1.87</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">3.75</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">4.00</td>
                </tr>
                <tr style="border-top:1px solid {BORDER};">
                    <td style="padding:6px; color:white; font-size:9px;">Betano</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">1.85</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">3.70</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">3.95</td>
                </tr>
            </table>
        </div>
    </div>
    ''', unsafe_allow_html=True)

# Cerrar contenedor unificado
st.markdown('</div>')

# FOOTER
st.markdown(f'<div style="text-align:center; padding:15px; border-top:1px solid {BORDER}; margin-top:10px;"><span style="color:{MUTED}; font-size:10px;">Scorpion Elite 2025 - Solo uso informativo</span></div>', unsafe_allow_html=True)
