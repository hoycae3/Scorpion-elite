import streamlit as st
from datetime import date

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
col_left, col_center, col_right = st.columns([2, 4, 2])

with col_left:
    st.markdown(f'''
    <div style="display:flex; align-items:center; gap:6px;">
        <span style="font-size:20px;">🦂</span>
        <div style="font-size:14px; font-weight:bold;">
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
    c1, c2 = st.columns([1, 1])
    with c1:
        fecha = st.date_input("", value=st.session_state.fecha_seleccionada, key="calendario", help="Seleccionar fecha", label_visibility="collapsed")
        st.session_state.fecha_seleccionada = fecha
    with c2:
        if st.button("🔓", key="login_btn"):
            st.session_state.show_login = True
            st.rerun()

# CONTENEDOR UNIFICADO PARA LAS 3 TARJETAS - COMPACTO
st.markdown(f'<div style="background:{CARD}; border:2px solid {BORDER}; border-radius:12px; padding:12px; margin:8px 0; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">', unsafe_allow_html=True)

# 3 COLUMNAS - TARJETAS COMPACTAS
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'''
    <div style="background:{BG}; border:2px solid {TITLE}; border-radius:10px; padding:12px; position:relative;">
        <div style="color:{TITLE}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px;">
            ⚽ PARTIDOS DESTACADOS
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''<table style="width:100%; border-collapse:collapse;">
<tr><td style="padding:8px; color:white; font-size:10px;">Manchester City vs Arsenal</td><td style="padding:8px; color:{ORANGE}; font-size:10px; text-align:center;">16:00</td><td style="padding:8px; color:{MUTED}; font-size:9px;">🏴󠁧󠁢󠁥󠁮󠁧󠁿</td></tr>
<tr><td style="padding:8px; color:white; font-size:10px; border-top:1px solid {BORDER};">Real Madrid vs Barcelona</td><td style="padding:8px; color:{ORANGE}; font-size:10px; text-align:center; border-top:1px solid {BORDER};">17:30</td><td style="padding:8px; color:{MUTED}; font-size:9px; border-top:1px solid {BORDER};">🇪🇸</td></tr>
</table>''', unsafe_allow_html=True)

with c2:
    st.markdown(f'''
    <div style="background:{BG}; border:2px solid {ORANGE}; border-radius:10px; padding:12px;">
        <div style="color:{ORANGE}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px;">
            ⭐ MEJOR PICK DEL DÍA
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; color:{GREEN}; font-size:10px; margin:6px 0;">🏆 Premier League</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; margin:6px 0;"><span style="font-size:14px; font-weight:bold;">Man City</span> <span style="color:{MUTED};">vs</span> <span style="font-size:14px; font-weight:bold;">Arsenal</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:6px; padding:8px; display:flex; justify-content:space-between;"><div><div style="color:{MUTED}; font-size:8px;">MERCADO</div><div style="font-weight:bold; color:white; font-size:11px;">1 Gana</div></div><div style="text-align:right;"><div style="color:{MUTED}; font-size:8px;">CUOTA</div><div style="font-size:18px; font-weight:bold; color:{ORANGE};">1.91</div></div></div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    with m1: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">PROB</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">72%</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">CONF</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">92%</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:7px;">VALOR</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">+19%</div></div>', unsafe_allow_html=True)

with c3:
    st.markdown(f'''
    <div style="background:{BG}; border:2px solid {GREEN}; border-radius:10px; padding:12px;">
        <div style="color:{GREEN}; font-size:12px; font-weight:bold; display:flex; align-items:center; gap:6px;">
            📊 COMPARADOR
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''<table style="width:100%;">
<tr><th style="color:{MUTED}; font-size:9px; text-align:left; padding:6px;">CASA</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px;">1</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px;">X</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px;">2</th></tr>
<tr><td style="padding:6px; color:white; font-size:9px;">⭐ Pinnacle</td><td style="padding:6px; color:{ORANGE}; font-size:9px; text-align:center;">1.91</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">3.80</td><td style="padding:6px; color:white; font-size:9px; text-align:center;">4.20</td></tr>
<tr><td style="padding:6px; color:white; font-size:9px; border-top:1px solid {BORDER};">Bet365</td><td style="padding:6px; color:white; font-size:9px; text-align:center; border-top:1px solid {BORDER};">1.87</td><td style="padding:6px; color:white; font-size:9px; text-align:center; border-top:1px solid {BORDER};">3.75</td><td style="padding:6px; color:white; font-size:9px; text-align:center; border-top:1px solid {BORDER};">4.00</td></tr>
<tr><td style="padding:6px; color:white; font-size:9px; border-top:1px solid {BORDER};">Betano</td><td style="padding:6px; color:white; font-size:9px; text-align:center; border-top:1px solid {BORDER};">1.85</td><td style="padding:6px; color:white; font-size:9px; text-align:center; border-top:1px solid {BORDER};">3.70</td><td style="padding:6px; color:white; font-size:9px; text-align:center; border-top:1px solid {BORDER};">3.95</td></tr>
</table>''', unsafe_allow_html=True)

# Cerrar contenedor unificado
st.markdown('</div>')

# FOOTER
st.markdown(f'<div style="text-align:center; padding:15px; border-top:1px solid {BORDER}; margin-top:10px;"><span style="color:{MUTED}; font-size:10px;">Scorpion Elite 2025 - Solo uso informativo</span></div>', unsafe_allow_html=True)
