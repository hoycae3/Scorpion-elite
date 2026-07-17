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
.header-row {{display:flex; justify-content:space-between; align-items:center; padding:12px 30px; background:{CARD}; border-bottom:1px solid {BORDER};}}
.header-center {{display:flex; gap:6px;}}
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
col_left, col_center, col_right = st.columns([3, 3, 2])

with col_left:
    st.markdown(f'<div style="color:{ORANGE}; font-size:22px; font-weight:bold;">SCORPION ELITE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{MUTED}; font-size:9px; letter-spacing:2px;">ANALISIS Y TENDENCIAS DEPORTIVAS</div>', unsafe_allow_html=True)

with col_center:
    s1, s2, s3 = st.columns(3)
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
    col_hoy, col_login = st.columns(2)
    with col_hoy:
        # Botón HOY que abre selector de fecha
        fecha_hoy = date.today().strftime("%d/%m")
        if st.button(f"📅 {fecha_hoy}", key="btn_hoy"):
            st.session_state.show_fecha = True
            
    # Modal para seleccionar fecha
    if st.session_state.get('show_fecha', False):
        st.markdown("### Seleccionar Fecha")
        cols_fecha = st.columns(3)
        with cols_fecha[0]:
            dia = st.selectbox("Día", list(range(1, 32)), index=date.today().day - 1, key="dia")
        with cols_fecha[1]:
            mes = st.selectbox("Mes", ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"], index=date.today().month - 1, key="mes")
        with cols_fecha[2]:
            year = st.selectbox("Año", [2025, 2026, 2027], index=1, key="year")
        
        if st.button("✓ Aplicar", key="aplicar_fecha"):
            st.session_state.fecha_seleccionada = date(year, date.today().month, dia)
            st.session_state.show_fecha = False
            st.rerun()
        if st.button("✕ Cerrar", key="cerrar_fecha"):
            st.session_state.show_fecha = False
            st.rerun()
    
    with col_login:
        if st.button("🔓 LOGIN", key="login_btn"):
            st.session_state.show_login = True
            st.rerun()

# Mostrar deporte y fecha seleccionados
st.markdown(f'<div style="text-align:center; color:{GREEN}; font-size:14px; margin:10px 0; background:{CARD}; padding:8px; border-radius:8px; border:1px solid {BORDER};">📋 {st.session_state.deporte} | 📅 {st.session_state.fecha_seleccionada.strftime("%d/%m/%Y")}</div>', unsafe_allow_html=True)

# CONTENEDOR UNIFICADO PARA LAS 3 TARJETAS
st.markdown(f'<div style="background:{CARD}; border:2px solid {BORDER}; border-radius:16px; padding:16px; margin:10px 0; box-shadow: 0 8px 32px rgba(0,0,0,0.4);">', unsafe_allow_html=True)

# 3 COLUMNAS - TARJETAS DEFINIDAS
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'''
    <div style="background:{CARD}; 
                 border:2px solid {BORDER}; 
                 border-radius:12px; 
                 padding:16px; 
                 margin:8px;
                 box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                 position:relative;
                 overflow:hidden;">
        <div style="position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, {TITLE}, {GREEN});"></div>
        <div style="color:{TITLE}; font-size:14px; font-weight:bold; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid {BORDER}; display:flex; align-items:center; gap:8px;">
            <span style="font-size:16px;">⚽</span> PARTIDOS DESTACADOS
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''<table style="width:100%; border-collapse:collapse;">
<tr style="border-bottom:1px solid {BORDER};"><th style="color:{MUTED}; font-size:10px; text-align:left; padding:8px 8px; width:50%;">PARTIDO</th><th style="color:{MUTED}; font-size:10px; text-align:center; padding:8px 8px; width:15%;">HORA</th><th style="color:{MUTED}; font-size:10px; text-align:center; padding:8px 8px; width:35%;">LIGA</th></tr>
<tr style="background:{BG};"><td style="padding:12px 8px; color:white; font-size:11px; text-align:left; border-radius:6px;">Manchester City vs Arsenal</td><td style="padding:12px 8px; color:{ORANGE}; font-size:11px; text-align:center; font-weight:bold;">16:00</td><td style="padding:12px 8px; color:{MUTED}; font-size:10px; text-align:center;">🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier</td></tr>
<tr><td style="padding:12px 8px; color:white; font-size:11px; text-align:left; border-top:1px solid {BORDER};">Real Madrid vs Barcelona</td><td style="padding:12px 8px; color:{ORANGE}; font-size:11px; text-align:center; font-weight:bold; border-top:1px solid {BORDER};">17:30</td><td style="padding:12px 8px; color:{MUTED}; font-size:10px; text-align:center; border-top:1px solid {BORDER};">🇪🇸 LaLiga</td></tr>
</table>''', unsafe_allow_html=True)

with c2:
    st.markdown(f'''
    <div style="background:{CARD}; 
                 border:2px solid {ORANGE}; 
                 border-radius:12px; 
                 padding:16px; 
                 margin:8px;
                 box-shadow: 0 4px 15px rgba(245,158,11,0.2);
                 position:relative;
                 overflow:hidden;">
        <div style="position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, {ORANGE}, #ef4444);"></div>
        <div style="color:{ORANGE}; font-size:14px; font-weight:bold; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid {BORDER}; display:flex; align-items:center; gap:8px;">
            <span style="font-size:16px;">⭐</span> MEJOR PICK DEL DÍA
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; color:{GREEN}; font-size:11px; margin-bottom:8px; font-weight:bold;">🏆 Premier League - Jornada 36</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; margin:12px 0;"><span style="font-size:16px; font-weight:bold; color:white;">Manchester City</span> <span style="color:{MUTED}; font-size:14px;">⚽</span> <span style="font-size:16px; font-weight:bold; color:white;">Arsenal</span></div>', unsafe_allow_html=True)
    st.markdown(f'''
    <div style="background:{BG}; border:1px solid {ORANGE}; border-radius:8px; padding:12px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div style="color:{MUTED}; font-size:9px;">MERCADO</div>
            <div style="color:{MUTED}; font-size:10px;">Resultado Final</div>
            <div style="font-weight:bold; color:{GREEN}; font-size:13px;">Manchester City Gana</div>
        </div>
        <div style="text-align:right;">
            <div style="color:{MUTED}; font-size:9px;">CUOTA</div>
            <div><span style="font-size:24px; font-weight:bold; color:{ORANGE};">1.91</span></div>
            <span style="background:{GREEN}; color:{BG}; font-size:9px; padding:2px 8px; border-radius:4px;">Pinnacle ⭐</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div style="text-align:center; background:{BG}; padding:8px; border-radius:6px;"><div style="color:{MUTED}; font-size:8px;">PROBABILIDAD</div><div style="color:{GREEN}; font-size:20px; font-weight:bold;">72%</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div style="text-align:center; background:{BG}; padding:8px; border-radius:6px;"><div style="color:{MUTED}; font-size:8px;">CONFIANZA</div><div style="color:{GREEN}; font-size:20px; font-weight:bold;">92%</div><div style="color:{GREEN}; font-size:8px;">MUY ALTA</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div style="text-align:center; background:{BG}; padding:8px; border-radius:6px;"><div style="color:{MUTED}; font-size:8px;">VALOR</div><div style="color:{GREEN}; font-size:20px; font-weight:bold;">+19%</div><div style="color:{GREEN}; font-size:8px;">VALUE</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div style="text-align:center; background:{BG}; padding:8px; border-radius:6px;"><div style="color:{MUTED}; font-size:8px;">RIESGO</div><div style="color:{GREEN}; font-size:16px; font-weight:bold;">BAJO</div></div>', unsafe_allow_html=True)

with c3:
    st.markdown(f'''
    <div style="background:{CARD}; 
                 border:2px solid {GREEN}; 
                 border-radius:12px; 
                 padding:16px; 
                 margin:8px;
                 box-shadow: 0 4px 15px rgba(34,197,94,0.2);
                 position:relative;
                 overflow:hidden;">
        <div style="position:absolute; top:0; left:0; right:0; height:3px; background:linear-gradient(90deg, {GREEN}, {TITLE});"></div>
        <div style="color:{GREEN}; font-size:14px; font-weight:bold; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid {BORDER}; display:flex; align-items:center; gap:8px;">
            <span style="font-size:16px;">📊</span> COMPARADOR DE CUOTAS
        </div>
    </div>
    ''', unsafe_allow_html=True)
    st.markdown(f'''<table style="width:100%; border-collapse:collapse;">
<tr style="border-bottom:2px solid {BORDER};"><th style="color:{MUTED}; font-size:10px; text-align:left; padding:8px;">CASA</th><th style="color:{GREEN}; font-size:10px; text-align:center; padding:8px;">1</th><th style="color:{MUTED}; font-size:10px; text-align:center; padding:8px;">X</th><th style="color:{ORANGE}; font-size:10px; text-align:center; padding:8px;">2</th></tr>
<tr style="background:{BG};"><td style="padding:10px 8px; color:white; font-weight:bold; font-size:11px; text-align:left;">⭐ Pinnacle</td><td style="padding:10px 8px; color:{ORANGE}; font-weight:bold; font-size:11px; text-align:center;">1.91</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center;">3.80</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center;">4.20</td></tr>
<tr><td style="padding:10px 8px; color:white; font-size:11px; text-align:left; border-top:1px solid {BORDER};">Bet365</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">1.87</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">3.75</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">4.00</td></tr>
<tr><td style="padding:10px 8px; color:white; font-size:11px; text-align:left; border-top:1px solid {BORDER};">Betano</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">1.85</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">3.70</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">3.95</td></tr>
<tr><td style="padding:10px 8px; color:white; font-size:11px; text-align:left; border-top:1px solid {BORDER};">1xBet</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">1.90</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">3.78</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">4.10</td></tr>
<tr><td style="padding:10px 8px; color:white; font-size:11px; text-align:left; border-top:1px solid {BORDER};">Stake</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">1.88</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">3.76</td><td style="padding:10px 8px; color:white; font-size:11px; text-align:center; border-top:1px solid {BORDER};">4.05</td></tr>
</table>''', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; margin-top:12px;"><span style="background:{GREEN}; color:{BG}; padding:8px 16px; border-radius:6px; font-size:11px; font-weight:bold;">📋 Ver todas las cuotas</span></div>', unsafe_allow_html=True)

# Cerrar contenedor unificado
st.markdown('</div>')

# FOOTER
st.markdown(f'<div style="text-align:center; padding:15px; border-top:1px solid {BORDER}; margin-top:10px;"><span style="color:{MUTED}; font-size:10px;">Scorpion Elite 2025 - Solo uso informativo</span></div>', unsafe_allow_html=True)
