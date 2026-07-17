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

# Datos de partidos por deporte (conectar con API/DB)
PARTIDOS = {
    "FUTBOL": [],
    "BALONCESTO": [],
    "TENIS": []
}

# API Keys
FOOTBALL_DATA_KEY = "21a9a19125f3467c86579b79f71d359c"

def obtener_partidos_futbol():
    """Obtiene TODOS los partidos de futbol para hoy desde múltiples fuentes"""
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Fuente 1: WorldFootball.net - scraping COMPLETO de TODAS las ligas
    try:
        url = "https://www.worldfootball.net/matches-today/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        }
        
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar TODOS los contenedores de liga
            secciones = soup.find_all(['div', 'td'], class_=['sector', ' league-name'])
            
            for seccion in secciones:
                try:
                    # Obtener nombre de la liga
                    liga = seccion.get_text(strip=True)
                    if not liga or len(liga) < 3:
                        continue
                    
                    # Buscar la tabla o filas siguientes a esta liga
                    parent = seccion.find_parent(['tr', 'div', 'table'])
                    if parent:
                        # Buscar filas de partidos cercanas
                        if parent.name == 'td':
                            # Es un td de liga
                            next_row = parent.find_next_sibling(['tr', 'td'])
                            while next_row:
                                equipos = next_row.find_all('td', class_='team')
                                zeit = next_row.find('td', class_='zeit')
                                
                                if len(equipos) >= 2 and zeit:
                                    local = equipos[0].get_text(strip=True).replace('\n', ' ').strip()
                                    visita = equipos[1].get_text(strip=True).replace('\n', ' ').strip()
                                    hora = zeit.get_text(strip=True)
                                    
                                    if local and visita and hora and 'vs' not in local.lower():
                                        partidos.append({
                                            "equipo": f"{local} vs {visita}",
                                            "hora": hora,
                                            "liga": liga
                                        })
                                
                                # Buscar siguiente sección
                                if next_row.find(['td'], class_=['sector', ' league-name']):
                                    break
                                next_row = next_row.find_next_sibling(['tr', 'td'])
                except:
                    continue
    except Exception as e:
        print(f"Error WorldFootball: {e}")
    
    # Fuente 2: API-Football - TODAS las ligas disponibles
    try:
        hoy = datetime.now()
        fecha_str = hoy.strftime("%Y-%m-%d")
        
        # Solicitar TODOS los partidos sin filtro de liga
        url = f"https://v3.football.api-sports.io/fixtures?date={fecha_str}"
        headers = {"x-apisports-key": FOOTBALL_DATA_KEY}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("response"):
                for fixture in data["response"][:50]:  # Aumentar a 50
                    try:
                        home = fixture["teams"]["home"]["name"]
                        away = fixture["teams"]["away"]["name"]
                        league = fixture["league"]["name"]
                        hora = fixture["fixture"]["date"][11:16]
                        
                        # Convertir hora a UTC-3
                        try:
                            dt = datetime.strptime(hora, "%H:%M")
                            dt = dt + timedelta(hours=-3)
                            hora = dt.strftime("%H:%M")
                        except:
                            pass
                        
                        partidos.append({
                            "equipo": f"{home} vs {away}",
                            "hora": hora,
                            "liga": league
                        })
                    except:
                        continue
    except Exception as e:
        print(f"Error API-Football: {e}")
    
    # Fuente 3: Sofascore API - TODOS los partidos
    try:
        url = "https://www.sofascore.com/api/v1/sport/football/events/live"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("events"):
                for event in data["events"][:50]:  # Aumentar
                    try:
                        home = event.get("homeTeam", {}).get("shortName") or event.get("homeTeam", {}).get("name", "Local")
                        away = event.get("awayTeam", {}).get("shortName") or event.get("awayTeam", {}).get("name", "Visita")
                        league = event.get("tournament", {}).get("name", "Liga")
                        timestamp = event.get("startTimestamp", 0)
                        
                        if timestamp:
                            hora = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                        else:
                            hora = "--:--"
                        
                        partidos.append({
                            "equipo": f"{home} vs {away}",
                            "hora": hora,
                            "liga": league
                        })
                    except:
                        continue
    except Exception as e:
        print(f"Error Sofascore: {e}")
    
    # Fuente 4: Flashscore - scraping completo
    try:
        url = "https://www.flashscore.com.mx/futbol/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar todos los eventos
            eventos = soup.find_all(['div', 'tr'], class_=['event__match', 'event', 'match'])
            
            for evento in eventos[:30]:  # Aumentar
                try:
                    # Buscar hora
                    hora_elem = evento.find(['div', 'span'], class_=['event__time', 'time', 'match-time'])
                    hora = hora_elem.get_text(strip=True) if hora_elem else "--:--"
                    
                    # Buscar equipos
                    equipos = evento.find_all(['div', 'span'], class_=['event__participant', 'team', 'team-home', 'team-away'])
                    if len(equipos) >= 2:
                        local = equipos[0].get_text(strip=True)
                        visita = equipos[1].get_text(strip=True)
                        
                        if local and visita:
                            # Buscar liga
                            liga_parent = evento.find_parent(['div', 'tr'])
                            liga = "Partido"
                            if liga_parent:
                                liga_elem = liga_parent.find(['div', 'span', 'a'], class_=['event__league', 'league', 'tournament'])
                                if liga_elem:
                                    liga = liga_elem.get_text(strip=True)
                            
                            partidos.append({
                                "equipo": f"{local} vs {visita}",
                                "hora": hora,
                                "liga": liga
                            })
                except:
                    continue
    except Exception as e:
        print(f"Error Flashscore: {e}")
    
    # Fuente 5: Livescore
    try:
        url = "https://www.livescore.com/en/football/live/"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Buscar secciones de liga y partidos
            sections = soup.find_all(['div', 'section'], class_=['sport', 'category', 'league'])
            
            for section in sections[:20]:
                try:
                    # Nombre de liga
                    liga_elem = section.find(['h2', 'h3', 'div'], class_=['title', 'league-name', 'category'])
                    liga = liga_elem.get_text(strip=True) if liga_elem else "Liga"
                    
                    # Partidos en esta sección
                    matches = section.find_all(['div', 'tr'], class_=['match', 'event', 'row'])
                    
                    for match in matches[:10]:
                        try:
                            home = match.find(['span', 'div'], class_=['home', 'team-home', 'home-team'])
                            away = match.find(['span', 'div'], class_=['away', 'team-away', 'away-team'])
                            time_elem = match.find(['span', 'div'], class_=['time', 'match-time', 'scheduled'])
                            
                            if home and away:
                                home_name = home.get_text(strip=True)
                                away_name = away.get_text(strip=True)
                                hora = time_elem.get_text(strip=True) if time_elem else "--:--"
                                
                                partidos.append({
                                    "equipo": f"{home_name} vs {away_name}",
                                    "hora": hora,
                                    "liga": liga
                                })
                        except:
                            continue
                except:
                    continue
    except Exception as e:
        print(f"Error Livescore: {e}")
    
    # Eliminar duplicados
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = f"{p['equipo']}-{p['liga']}"
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        unique_partidos = [{"equipo": "Sin partidos disponibles", "hora": "--:--", "liga": "Verifica conexion"}]
    
    return unique_partidos[:15]  # Máximo 15 partidos

def obtener_partidos_baloncesto():
    """Obtiene partidos de baloncesto para hoy"""
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Fuente 1: API-Football Basketball
    try:
        hoy = datetime.now()
        fecha_str = hoy.strftime("%Y-%m-%d")
        
        # Buscar NBA y basketball leagues
        url = f"https://v3.football.api-sports.io/fixtures?date={fecha_str}&sport=basketball"
        headers = {"x-apisports-key": FOOTBALL_DATA_KEY}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("response"):
                for fixture in data["response"][:10]:
                    home = fixture["teams"]["home"]["name"]
                    away = fixture["teams"]["away"]["name"]
                    league = fixture["league"]["name"]
                    hora = fixture["fixture"]["date"][11:16]
                    
                    try:
                        dt = datetime.strptime(hora, "%H:%M")
                        dt = dt + timedelta(hours=-3)
                        hora = dt.strftime("%H:%M")
                    except:
                        pass
                    
                    partidos.append({
                        "equipo": f"{home} vs {away}",
                        "hora": hora,
                        "liga": league
                    })
    except Exception as e:
        print(f"Error API Basketball: {e}")
    
    # Fuente 2: Sofascore Basketball
    if len(partidos) < 3:
        try:
            url = "https://www.sofascore.com/api/v1/sport/basketball/events/live"
            headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for event in data.get("events", [])[:10]:
                    home = event.get("homeTeam", {}).get("shortName", "Local")
                    away = event.get("awayTeam", {}).get("shortName", "Visita")
                    league = event.get("tournament", {}).get("name", "Basketball")
                    timestamp = event.get("startTimestamp", 0)
                    
                    if timestamp:
                        hora = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                    else:
                        hora = "--:--"
                    
                    partidos.append({
                        "equipo": f"{home} vs {away}",
                        "hora": hora,
                        "liga": league
                    })
        except Exception as e:
            print(f"Error Sofascore Basketball: {e}")
    
    # Fuente 3: Flashscore Basketball
    if len(partidos) < 3:
        try:
            url = "https://www.flashscore.com.mx/baloncesto/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                eventos = soup.find_all('div', class_='event__match')
                
                for evento in eventos[:6]:
                    try:
                        hora_elem = evento.find('div', class_='event__time')
                        hora = hora_elem.text.strip() if hora_elem else "--:--"
                        
                        equipos = evento.find_all('div', class_='event__participant')
                        if len(equipos) >= 2:
                            partidos.append({
                                "equipo": f"{equipos[0].text.strip()} vs {equipos[1].text.strip()}",
                                "hora": hora,
                                "liga": "Basketball"
                            })
                    except:
                        continue
        except Exception as e:
            print(f"Error Flashscore Basketball: {e}")
    
    # Eliminar duplicados
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = p["equipo"]
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        unique_partidos = [{"equipo": "Sin partidos disponibles", "hora": "--:--", "liga": "NBA/Euroleague"}]
    
    return unique_partidos[:8]

def obtener_partidos_tenis():
    """Obtiene partidos de tenis para hoy"""
    import requests
    from bs4 import BeautifulSoup
    from datetime import datetime, timedelta
    
    partidos = []
    
    # Fuente 1: Sofascore Tennis
    try:
        url = "https://www.sofascore.com/api/v1/sport/tennis/events/live"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            for event in data.get("events", [])[:10]:
                home = event.get("homeTeam", {}).get("shortName", "Jugador 1")
                away = event.get("awayTeam", {}).get("shortName", "Jugador 2")
                league = event.get("tournament", {}).get("name", "Tenis")
                timestamp = event.get("startTimestamp", 0)
                
                if timestamp:
                    hora = datetime.fromtimestamp(timestamp).strftime("%H:%M")
                else:
                    hora = "--:--"
                
                partidos.append({
                    "equipo": f"{home} vs {away}",
                    "hora": hora,
                    "liga": league
                })
    except Exception as e:
        print(f"Error Sofascore Tennis: {e}")
    
    # Fuente 2: Flashscore Tennis
    if len(partidos) < 3:
        try:
            url = "https://www.flashscore.com.mx/tenis/"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                eventos = soup.find_all('div', class_='event__match')
                
                for evento in eventos[:6]:
                    try:
                        hora_elem = evento.find('div', class_='event__time')
                        hora = hora_elem.text.strip() if hora_elem else "--:--"
                        
                        nombres = evento.find_all('div', class_='event__participant')
                        if len(nombres) >= 2:
                            partidos.append({
                                "equipo": f"{nombres[0].text.strip()} vs {nombres[1].text.strip()}",
                                "hora": hora,
                                "liga": "ATP/WTA"
                            })
                    except:
                        continue
        except Exception as e:
            print(f"Error Flashscore Tennis: {e}")
    
    # Fuente 3: WorldFootball Tennis (si existe)
    if len(partidos) < 3:
        try:
            url = "https://www.worldfootball.net/matches-today/tennis/"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                eventos = soup.find_all('tr', class_=['row_today'])
                
                for evento in eventos[:6]:
                    try:
                        equipos = evento.find_all('td', class_='team')
                        zeit = evento.find('td', class_='zeit')
                        
                        if len(equipos) >= 2 and zeit:
                            local = equipos[0].get_text(strip=True)
                            visita = equipos[1].get_text(strip=True)
                            hora = zeit.get_text(strip=True)
                            
                            partidos.append({
                                "equipo": f"{local} vs {visita}",
                                "hora": hora,
                                "liga": "Tennis"
                            })
                    except:
                        continue
        except Exception as e:
            print(f"Error WorldFootball Tennis: {e}")
    
    # Eliminar duplicados
    seen = set()
    unique_partidos = []
    for p in partidos:
        key = p["equipo"]
        if key not in seen:
            seen.add(key)
            unique_partidos.append(p)
    
    if not unique_partidos:
        unique_partidos = [{"equipo": "Sin partidos disponibles", "hora": "--:--", "liga": "ATP/WTA"}]
    
    return unique_partidos[:8]

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
