import streamlit as st
from datetime import date
from datetime import datetime

st.set_page_config(page_title='SCORPION ELITE', layout='wide')

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
    s1, s2, s3 = st.columns([1, 1.2, 1])
    with s1:
        if st.button("⚽ FUTBOL", key="btn_futbol"):
            st.session_state.deporte = "FUTBOL"
    with s2:
        if st.button("🏀 BALONCESTO", key="btn_basket"):
            st.session_state.deporte = "BALONCESTO"
    with s3:
        if st.button("🎾 TENIS", key="btn_tenis"):
            st.session_state.deporte = "TENIS"

with col_right:
    c1, c2 = st.columns([1.5, 1])
    with c1:
        # Calendario nativo sin label
        fecha = st.date_input("", value=st.session_state.fecha_seleccionada, key="calendario", label_visibility="collapsed")
        st.session_state.fecha_seleccionada = fecha
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

# API Keys
API_FOOTBALL_KEY = "e3926f829cd848f4b2b54d722ca29701"  # API-Football (nueva key funciona)

# Prioridad de ligas segun interes mundial
LIGAS_PRIORIDAD = {
    # TOP TIER - Mayor atencion mundial
    "champions league": 15,
    "premier league": 14,
    "la liga": 13,
    "serie a": 12,
    "bundesliga": 11,
    "ligue 1": 10,
    
    # SECOND TIER - Alto interes
    "champions league": 15,
    "premier league": 14,
    "la liga": 13,
    "serie a": 12,
    "bundesliga": 11,
    "ligue 1": 10,
    "europa league": 9,  # Prioridad alta
    "libertadores": 8,
    "copa america": 8,
    "euro": 8,
    "world cup": 8,
    
    # THIRD TIER - Medio interes (ligas con muchos goles)
    "brasileiro": 7,
    "eredivisie": 7,  # Liga holandesa - muchos goles
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
    "colombia": 4,  # Liga colombiana
    "betplay": 4,   # Liga BetPlay Colombia
    "uruguay": 4,
    "peru": 4,
    "bolivia": 4,
    
    # FIFTH TIER - Divisions menores
    "league two": 2,
    "usl": 2,
    "national league": 2,
}

def obtener_partidos_futbol(todos=False):
    """Obtiene partidos de futbol para hoy desde API-Football
    
    Args:
        todos: Si True, retorna todos los partidos. Si False, solo los 3 mas importantes.
    """
    import requests
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Fuente: API-Football
    try:
        hoy = datetime.now()
        fecha_str = hoy.strftime("%Y-%m-%d")
        
        url = f"https://v3.football.api-sports.io/fixtures?date={fecha_str}"
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get("response"):
                for fixture in data["response"]:
                    try:
                        home = fixture["teams"]["home"]["name"]
                        away = fixture["teams"]["away"]["name"]
                        league = fixture["league"]["name"].lower()
                        country = fixture["league"]["country"]
                        hora = fixture["fixture"]["date"][11:16]
                        
                        # Convertir UTC a UTC-3 (America)
                        try:
                            dt = datetime.strptime(hora, "%H:%M")
                            dt = dt + timedelta(hours=-3)
                            hora_local = dt.strftime("%H:%M")
                        except:
                            hora_local = hora
                        
                        # Calcular prioridad
                        prioridad = 0
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
                            "league_lower": league
                        })
                    except:
                        continue
    except Exception as e:
        print(f"Error API-Football: {e}")
    
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
                    home = event.get("strHomeTeam", "")
                    away = event.get("strAwayTeam", "")
                    
                    if home and away and home != "None" and away != "None":
                        league = event.get("strLeague", "ATP").lower()
                        date = event.get("dateEvent", "")
                        time = event.get("strTime", "")
                        hora = time.split(" ")[-1][:5] if time and time != "None" else "--:--"
                        
                        # Calcular prioridad
                        prioridad = 0
                        for nombre, prio in TENIS_PRIORIDAD.items():
                            if nombre in league:
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
                                        "liga": event.get("strLeague", "ATP"),
                                        "prioridad": prioridad,
                                        "fecha": date
                                    })
                            except:
                                pass
                except:
                    continue
    except Exception as e:
        print(f"Error TheSportsDB Tennis: {e}")
    
    # Fuente: TheSportsDB Tennis WTA
    try:
        url = "https://www.thesportsdb.com/api/v1/json/3/eventspastleague.php?id=4499"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            for event in events[:10]:
                try:
                    home = event.get("strHomeTeam", "")
                    away = event.get("strAwayTeam", "")
                    
                    if home and away and home != "None" and away != "None":
                        league = event.get("strLeague", "WTA")
                        date = event.get("dateEvent", "")
                        time = event.get("strTime", "")
                        hora = time.split(" ")[-1][:5] if time and time != "None" else "--:--"
                        
                        if date:
                            try:
                                event_date = datetime.strptime(date, "%Y-%m-%d")
                                today = datetime.now()
                                days_diff = (today - event_date).days
                                
                                if days_diff <= 7:
                                    partidos.append({
                                        "equipo": f"{home} vs {away}",
                                        "hora": hora,
                                        "liga": league,
                                        "prioridad": 5,  # WTA
                                        "fecha": date
                                    })
                            except:
                                pass
                except:
                    continue
    except Exception as e:
        print(f"Error WTA Tennis: {e}")
    
    # Eliminar duplicados y ordenar
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = p["equipo"]
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        return [{"equipo": "Sin partidos hoy", "hora": "--:--", "liga": "Verificar mañana"}]
    
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
    # Variables para datos del pick (conectar con API/DB)
    PICK_LIGA = "Liga"  # {{liga}}
    PICK_LOCAL = "Equipo Local"  # {{equipo_local}}
    PICK_VISITA = "Equipo Visita"  # {{equipo_visita}}
    PICK_NOMBRE = "Pick"  # {{pick}} - Ej: Gana Arsenal, Over 2.5, Corners +9.5
    PICK_CUOTA = "0.00"  # {{cuota}}
    PICK_PROB = "0"  # {{probabilidad}}
    PICK_CONF = "0"  # {{confianza}}
    PICK_VALOR = "+0%"  # {{valor}}
    
    st.markdown(f'''
    <div style="background:{BG}; border:2px solid {ORANGE}; border-radius:10px; padding:12px;">
        <div style="color:{ORANGE}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px; margin-bottom:10px;">
            ⭐ MEJOR PICK DEL DÍA
        </div>
        <div style="background:{BG}; border:1px solid {ORANGE}; border-radius:6px; padding:10px;">
            <div style="text-align:center; color:{GREEN}; font-size:10px; margin-bottom:6px;">🏆 {PICK_LIGA}</div>
            <div style="text-align:center; margin:6px 0;"><span style="font-size:14px; font-weight:bold;">{PICK_LOCAL}</span> <span style="color:{MUTED};">vs</span> <span style="font-size:14px; font-weight:bold;">{PICK_VISITA}</span></div>
            <div style="background:{CARD}; border:1px solid {ORANGE}; border-radius:6px; padding:8px; display:flex; justify-content:space-between; margin-top:8px;"><div><div style="color:{MUTED}; font-size:8px;">MERCADO</div><div style="font-weight:bold; color:white; font-size:11px;">{PICK_NOMBRE}</div></div><div style="text-align:right;"><div style="color:{MUTED}; font-size:8px;">CUOTA</div><div style="font-size:18px; font-weight:bold; color:{ORANGE};">{PICK_CUOTA}</div></div></div>
            <div style="display:flex; justify-content:space-around; margin-top:8px;">
                <div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">PROB</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">{PICK_PROB}%</div></div>
                <div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">CONF</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">{PICK_CONF}%</div></div>
                <div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">VALOR</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">{PICK_VALOR}</div></div>
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
