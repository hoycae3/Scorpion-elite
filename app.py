"""
SCORPION ELITE - Dashboard
Diseño: GitHub Dark Style
"""
import streamlit as st
import requests
import os

# CONFIG - Keys en Secrets
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

# ESTILOS CSS
st.set_page_config(page_title="SCORPION ELITE", page_icon="🦂", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0d1117; color: #e6edf3; }
[data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
h1, h2, h3, h4, h5, h6 { color: #f0f6fc !important; }
.css-1r6sl5, .st-dx { background-color: #161b22 !important; border: 1px solid #30363d !important; border-radius: 8px !important; }
.stButton > button { background-color: #d97706 !important; color: white !important; border: none !important; border-radius: 6px !important; }
.stTextInput > div > div > input { background-color: #0d1117 !important; color: #e6edf3 !important; border: 1px solid #30363d !important; }
table { color: #e6edf3 !important; }
th { background-color: #161b22 !important; color: #8b949e !important; }
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# FUNCIONES API
@st.cache_data(ttl=3600)
def buscar_equipos(nombre):
    resultados = []
    if not nombre or len(nombre) < 2 or not FOOTBALL_DATA_KEY:
        return resultados
    try:
        headers = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        leagues = [("PD", "La Liga"), ("PL", "Premier League"), ("BL1", "Bundesliga"), ("SA", "Serie A"), ("FL1", "Ligue 1")]
        for league_code, league_name in leagues:
            url = f"https://api.football-data.org/v4/competitions/{league_code}/teams"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                for t in r.json().get("teams", []):
                    if nombre.lower() in t.get("name", "").lower():
                        resultados.append({"id": t.get("id"), "nombre": t.get("name", ""), "short": t.get("shortName", ""), "pais": t.get("country", ""), "liga": league_name})
    except Exception as e:
        st.error(f"Error: {e}")
    return resultados

@st.cache_data(ttl=3600)
def obtener_cuotas(league_key="soccer_epl"):
    if not ODDS_API_KEY:
        return []
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {"apiKey": ODDS_API_KEY, "regions": "eu,us,uk", "markets": "h2h"}
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            resultados = []
            for m in r.json()[:15]:
                home, away = m.get("home_team", ""), m.get("away_team", "")
                mejor_l, mejor_e, mejor_v = 0, 0, 0
                for bm in m.get("bookmakers", [])[:3]:
                    for market in bm.get("markets", []):
                        if market.get("key") == "h2h":
                            for o in market.get("outcomes", []):
                                name, price = o.get("name", ""), o.get("price", 0)
                                if "Home" in name or home in name:
                                    if price > mejor_l: mejor_l = price
                                elif "Draw" in name:
                                    if price > mejor_e: mejor_e = price
                                else:
                                    if price > mejor_v: mejor_v = price
                if mejor_l > 0:
                    resultados.append({"partido": f"{home} vs {away}", "local": mejor_l, "empate": mejor_e, "visita": mejor_v})
            return resultados
    except:
        pass
    return []

@st.cache_data(ttl=1800)
def obtener_clima(ciudad):
    if not OPENWEATHER_KEY:
        return None
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": ciudad, "appid": OPENWEATHER_KEY, "units": "metric", "lang": "es"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"ciudad": data.get("name", ""), "temp": data.get("main", {}).get("temp", 0), "clima": data.get("weather", [{}])[0].get("description", ""), "humedad": data.get("main", {}).get("humidity", 0), "viento": data.get("wind", {}).get("speed", 0)}
    except:
        pass
    return None

# SIDEBAR
with st.sidebar:
    st.markdown("""<div style="text-align:center;padding:10px 0;"><h2 style="color:#d97706;margin:0;">🦂 SCORPION ELITE</h2><p style="color:#8b949e;font-size:11px;">ANÁLISIS Y TENDENCIAS</p></div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📋 MENÚ")
    page = st.radio("Navegación", options=["📊 Dashboard", "🔍 Equipos", "🌤️ Clima", "💰 Cuotas", "🎯 Picks"], label_visibility="collapsed")
    st.markdown("---")
    st.markdown("""<div style="background:#161b22;padding:15px;border-radius:8px;text-align:center;"><p style="color:#d97706;font-weight:bold;margin:0;">🦂 Premium</p><p style="color:#8b949e;font-size:12px;margin:5px 0;">Todas las funciones activas</p></div>""", unsafe_allow_html=True)

# DASHBOARD
if page == "📊 Dashboard":
    st.markdown("""<div style="background:linear-gradient(90deg,#161b22 0%,#0d1117 100%);padding:20px;border-radius:8px;margin-bottom:20px;"><h1 style="color:#d97706;margin:0;">🦂 SCORPION ELITE</h1><p style="color:#8b949e;margin:5px 0 0 0;">Panel de análisis deportivo</p></div>""", unsafe_allow_html=True)
    
    st.markdown("### 💰 Cuotas de Hoy")
    liga = st.selectbox("Selecciona una liga:", options=[("soccer_epl","🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League"), ("soccer_esp La Liga","🇪🇸 La Liga"), ("soccer_deu Bundesliga","🇩🇪 Bundesliga"), ("soccer_ita Serie A","🇮🇹 Serie A"), ("soccer_fra Ligue 1","🇫🇷 Ligue 1")], format_func=lambda x: x[1], label_visibility="collapsed")
    liga_key = liga[0] if isinstance(liga, tuple) else liga
    
    with st.spinner("Cargando cuotas..."):
        cuotas = obtener_cuotas(liga_key)
    
    if cuotas:
        for c in cuotas[:8]:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1: st.markdown(f"<span style='color:#e6edf3;'>{c['partido']}</span>", unsafe_allow_html=True)
            with col2: st.markdown(f"<span style='color:#3fb950;'>{c['local']}</span>", unsafe_allow_html=True)
            with col3: st.markdown(f"<span style='color:#8b949e;'>{c['empate']}</span>", unsafe_allow_html=True)
            with col4: st.markdown(f"<span style='color:#3fb950;'>{c['visita']}</span>", unsafe_allow_html=True)
    elif not ODDS_API_KEY:
        st.warning("⚠️ Configura ODDS_API_KEY en Secrets para ver cuotas")
    else:
        st.info("No hay cuotas disponibles para esta liga")
    
    st.markdown("---")
    st.markdown("### 🔍 Buscar Equipos")
    col1, col2 = st.columns([3, 1])
    with col1:
        equipo = st.text_input("Nombre del equipo:", placeholder="Ej: Barcelona, Real Madrid...", label_visibility="collapsed")
    with col2:
        buscar = st.button("🔍 Buscar", use_container_width=True)
    
    if buscar and equipo:
        with st.spinner("Buscando..."):
            resultados = buscar_equipos(equipo)
        if resultados:
            st.success(f"✅ {len(resultados)} equipos encontrados")
            cols = st.columns(3)
            for i, eq in enumerate(resultados[:9]):
                with cols[i % 3]:
                    st.markdown(f"""<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin-bottom:10px;"><h4 style="color:#e6edf3;margin:0 0 5px 0;">{eq['nombre']}</h4><p style="color:#8b949e;font-size:12px;margin:0;">{eq['liga']} • {eq['pais']}</p></div>""", unsafe_allow_html=True)
        elif not FOOTBALL_DATA_KEY:
            st.warning("⚠️ Configura FOOTBALL_DATA_KEY en Secrets")
        else:
            st.error(f"❌ No se encontró: {equipo}")

# EQUIPOS
elif page == "🔍 Equipos":
    st.markdown("## 🔍 Buscar Equipos")
    col1, col2 = st.columns([3, 1])
    with col1:
        equipo = st.text_input("Nombre del equipo:", placeholder="Barcelona, Liverpool, Bayern...", label_visibility="collapsed")
    with col2:
        buscar = st.button("🔍 Buscar", use_container_width=True)
    
    if buscar and equipo:
        with st.spinner("Buscando equipos..."):
            resultados = buscar_equipos(equipo)
        if resultados:
            st.success(f"✅ {len(resultados)} equipos encontrados")
            for eq in resultados:
                with st.expander(f"⚽ {eq['nombre']} ({eq['liga']})"):
                    st.markdown(f"**País:** {eq['pais']}  \n**Liga:** {eq['liga']}  \n**ID:** {eq['id']}")
        else:
            st.error(f"❌ No se encontró '{equipo}'")
    else:
        st.info("👆 Escribe el Nombre de un equipo y presiona Buscar")

# CLIMA
elif page == "🌤️ Clima":
    st.markdown("## 🌤️ Clima")
    col1, col2 = st.columns([3, 1])
    with col1:
        ciudad = st.text_input("Ciudad:", placeholder="Madrid, Buenos Aires, London...", label_visibility="collapsed")
    with col2:
        buscar = st.button("🌡️ Buscar", use_container_width=True)
    
    if buscar and ciudad:
        with st.spinner("Obteniendo clima..."):
            clima = obtener_clima(ciudad)
        if clima:
            st.success(f"📍 {clima['ciudad']}")
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1: st.metric("🌡️ Temperatura", f"{clima['temp']:.1f}°C")
            with col_c2: st.metric("☁️ Condición", clima['clima'].capitalize())
            with col_c3: st.metric("💧 Humedad", f"{clima['humedad']}%")
            with col_c4: st.metric("💨 Viento", f"{clima['viento']} m/s")
        elif not OPENWEATHER_KEY:
            st.warning("⚠️ OpenWeather se está activando o no está configurado")
        else:
            st.error(f"❌ No se encontró el clima para: {ciudad}")
    else:
        st.info("👆 Escribe una ciudad y presiona Buscar")

# CUOTAS
elif page == "💰 Cuotas":
    st.markdown("## 💰 Cuotas de Apuestas")
    if not ODDS_API_KEY:
        st.warning("⚠️ Configura ODDS_API_KEY en Secrets para ver las cuotas")
    else:
        liga = st.selectbox("Selecciona una liga:", options=[("soccer_epl","🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League"), ("soccer_esp La Liga","🇪🇸 La Liga"), ("soccer_deu Bundesliga","🇩🇪 Bundesliga"), ("soccer_ita Serie A","🇮🇹 Serie A"), ("soccer_fra Ligue 1","🇫🇷 Ligue 1")], format_func=lambda x: x[1])
        liga_key = liga[0] if isinstance(liga, tuple) else liga
        
        with st.spinner("Cargando cuotas..."):
            cuotas = obtener_cuotas(liga_key)
        
        if cuotas:
            st.success(f"✅ {len(cuotas)} partidos disponibles")
            for c in cuotas:
                st.markdown(f"""<div style="background:#161b22;border:1px solid #30363d;border-radius:8px;padding:15px;margin-bottom:10px;"><div style="display:flex;justify-content:space-between;align-items:center;"><div style="flex:2;"><h4 style="color:#e6edf3;margin:0;">{c['partido']}</h4></div><div style="flex:1;text-align:center;"><div style="color:#8b949e;font-size:11px;">LOCAL</div><div style="color:#3fb950;font-size:18px;font-weight:bold;">{c['local']}</div></div><div style="flex:1;text-align:center;"><div style="color:#8b949e;font-size:11px;">EMPATE</div><div style="color:#8b949e;font-size:18px;font-weight:bold;">{c['empate']}</div></div><div style="flex:1;text-align:center;"><div style="color:#8b949e;font-size:11px;">VISITA</div><div style="color:#3fb950;font-size:18px;font-weight:bold;">{c['visita']}</div></div></div></div>""", unsafe_allow_html=True)
        else:
            st.warning("No hay cuotas disponibles para esta liga")

# PICKS
elif page == "🎯 Picks":
    st.markdown("## 🎯 Picks del Día")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#161b22 0%,#1a2332 100%);border:2px solid #d97706;border-radius:12px;padding:25px;text-align:center;margin-bottom:20px;">
        <h3 style="color:#d97706;margin:0 0 10px 0;">⭐ PICK DESTACADO</h3>
        <h2 style="color:#e6edf3;margin:0 0 15px 0;">Manchester City vs Arsenal</h2>
        <div style="background:#0d1117;border-radius:8px;padding:15px;margin-bottom:15px;">
            <p style="color:#8b949e;margin:0;">MERCADO: Manchester City Gana</p>
            <h1 style="color:#3fb950;margin:10px 0 0 0;">Cuota: 1.91</h1>
        </div>
        <div style="display:flex;justify-content:center;gap:30px;">
            <div><p style="color:#8b949e;margin:0;font-size:12px;">PROBABILIDAD IA</p><h2 style="color:#3fb950;margin:5px 0 0 0;">72%</h2></div>
            <div><p style="color:#8b949e;margin:0;font-size:12px;">CONFIANZA</p><h2 style="color:#3fb950;margin:5px 0 0 0;">92%</h2></div>
            <div><p style="color:#8b949e;margin:0;font-size:12px;">VALOR</p><h2 style="color:#3fb950;margin:5px 0 0 0;">+19%</h2></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 📊 Análisis")
    st.markdown("- ✅ Manchester City ha ganado 8 de los últimos 10 partidos\n- ⚠️ Arsenal tiene 3 bajas importantes en defensa\n- 📈 City promedia 2.4 goles por partido en casa\n- 🎯 xG ofensivo City: 2.35 | Arsenal: 1.15")
    st.markdown("### 📈 Nivel de Confianza")
    st.progress(92, text="92% - MUY ALTA")

# FOOTER
st.markdown("---")
st.markdown("""<div style="text-align:center;color:#8b949e;padding:20px;"><p style="margin:0;">🦂 SCORPION ELITE - Análisis y Tendencias Deportivas</p><p style="font-size:12px;margin:5px 0 0 0;">© 2025</p></div>""", unsafe_allow_html=True)
