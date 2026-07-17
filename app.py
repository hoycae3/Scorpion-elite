import streamlit as st

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
.header-container {{display:flex; justify-content:space-between; align-items:center;}}
.header-right {{display:flex; gap:8px; align-items:center;}}
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

# HEADER
col1, col2, col3 = st.columns([3, 3, 2])

with col1:
    st.markdown(f'<div style="color:{ORANGE}; font-size:22px; font-weight:bold;">SCORPION ELITE</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{MUTED}; font-size:9px; letter-spacing:2px;">ANALISIS Y TENDENCIAS DEPORTIVAS</div>', unsafe_allow_html=True)

with col2:
    c_futbol, c_basket, c_tenis = st.columns(3)
    with c_futbol:
        st.markdown(f'<span style="background:{GREEN}; color:{BG}; padding:6px 14px; border-radius:4px; font-size:11px; font-weight:bold;">FUTBOL</span>', unsafe_allow_html=True)
    with c_basket:
        st.markdown(f'<span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">BALONCESTO</span>', unsafe_allow_html=True)
    with c_tenis:
        st.markdown(f'<span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">TENIS</span>', unsafe_allow_html=True)

with col3:
    c_buscar, c_hoy, c_login = st.columns(3)
    with c_buscar:
        st.text_input("Buscar", placeholder="Buscar...", label_visibility="collapsed", key="buscar")
    with c_hoy:
        st.markdown(f'<span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 10px; border-radius:4px; font-size:11px;">HOY</span>', unsafe_allow_html=True)
    with c_login:
        if st.button("LOGIN", key="login_btn"):
            st.session_state.show_login = True
            st.rerun()

# 3 COLUMNAS
c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:14px; margin:8px;">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid {BORDER};">PARTIDOS DESTACADOS</div>', unsafe_allow_html=True)
    st.markdown(f'''<table style="width:100%;">
<tr><th style="color:{MUTED}; font-size:9px; text-align:left; padding:6px 8px; width:50%;">PARTIDO</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px 8px; width:20%;">HORA</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px 8px; width:30%;">LIGA</th></tr>
<tr><td style="padding:10px 8px; color:white; font-size:10px; text-align:left;">Manchester City vs Arsenal</td><td style="padding:10px 8px; color:{MUTED}; font-size:10px; text-align:center;">16:00</td><td style="padding:10px 8px; color:{MUTED}; font-size:10px; text-align:center;">Premier League</td></tr>
<tr><td style="padding:10px 8px; color:white; font-size:10px; text-align:left; border-top:1px solid {BORDER};">Real Madrid vs Barcelona</td><td style="padding:10px 8px; color:{MUTED}; font-size:10px; text-align:center; border-top:1px solid {BORDER};">17:30</td><td style="padding:10px 8px; color:{MUTED}; font-size:10px; text-align:center; border-top:1px solid {BORDER};">LaLiga</td></tr>
</table>''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:14px; margin:8px;">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid {BORDER};">MEJOR PICK DEL DIA</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; color:{MUTED}; font-size:10px; margin-bottom:8px;">Premier League - Jornada 36</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; margin:10px 0;"><span style="font-size:14px; font-weight:bold;">Manchester City</span> <span style="color:{MUTED};">VS</span> <span style="font-size:14px; font-weight:bold;">Arsenal</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:{BG}; border:1px solid {BORDER}; border-radius:6px; padding:10px; margin-bottom:10px; display:flex; justify-content:space-between;"><div><div style="color:{MUTED}; font-size:8px;">MERCADO</div><div style="color:{MUTED}; font-size:10px;">Resultado Final</div><div style="font-weight:bold; color:white; font-size:12px;">Manchester City Gana</div></div><div style="text-align:right;"><div style="color:{MUTED}; font-size:8px;">CUOTA</div><div><span style="font-size:20px; font-weight:bold; color:white;">1.91</span> <span style="background:#1e293b; color:white; font-size:9px; padding:2px 6px; border-radius:4px;">Pinnacle</span></div></div></div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">PROBABILIDAD</div><div style="color:{GREEN}; font-size:18px; font-weight:bold;">72%</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">CONFIANZA</div><div style="color:{GREEN}; font-size:18px; font-weight:bold;">92%</div><div style="color:{GREEN}; font-size:7px;">MUY ALTA</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">VALOR</div><div style="color:{GREEN}; font-size:18px; font-weight:bold;">+19%</div><div style="color:{GREEN}; font-size:7px;">VALUE</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">RIESGO</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">BAJO</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:14px; margin:8px;">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid {BORDER};">COMPARADOR DE CUOTAS</div>', unsafe_allow_html=True)
    st.markdown(f'''<table style="width:100%;">
<tr><th style="color:{MUTED}; font-size:9px; text-align:left; padding:6px 8px; width:30%;">CASA</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px 8px;">1</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px 8px;">X</th><th style="color:{MUTED}; font-size:9px; text-align:center; padding:6px 8px;">2</th></tr>
<tr><td style="padding:8px; color:white; font-weight:bold; font-size:10px; text-align:left;">Pinnacle</td><td style="padding:8px; color:{ORANGE}; font-weight:bold; font-size:10px; text-align:center;">1.91</td><td style="padding:8px; color:{ORANGE}; font-weight:bold; font-size:10px; text-align:center;">3.80</td><td style="padding:8px; color:{ORANGE}; font-weight:bold; font-size:10px; text-align:center;">4.20</td></tr>
<tr><td style="padding:8px; color:white; font-size:10px; text-align:left; border-top:1px solid {BORDER};">Bet365</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">1.87</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">3.75</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">4.00</td></tr>
<tr><td style="padding:8px; color:white; font-size:10px; text-align:left; border-top:1px solid {BORDER};">Betano</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">1.85</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">3.70</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">3.95</td></tr>
<tr><td style="padding:8px; color:white; font-size:10px; text-align:left; border-top:1px solid {BORDER};">1xBet</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">1.90</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">3.78</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">4.10</td></tr>
<tr><td style="padding:8px; color:white; font-size:10px; text-align:left; border-top:1px solid {BORDER};">Stake</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">1.88</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">3.76</td><td style="padding:8px; color:white; font-size:10px; text-align:center; border-top:1px solid {BORDER};">4.05</td></tr>
</table>''', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; margin-top:10px;"><a href="#" style="color:{GREEN}; font-size:10px;">Ver todas las cuotas</a></div></div>', unsafe_allow_html=True)

# FOOTER
st.markdown(f'<div style="text-align:center; padding:15px; border-top:1px solid {BORDER}; margin-top:10px;"><span style="color:{MUTED}; font-size:10px;">Scorpion Elite 2025 - Solo uso informativo</span></div>', unsafe_allow_html=True)
