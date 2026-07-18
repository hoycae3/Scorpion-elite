import streamlit as st
import os
from datetime import date, timedelta

# ══════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Scorpion Elite",
    page_icon="🦂",
    layout="wide"
)

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ══════════════════════════════════════════════════════════
# SESIÓN
# ══════════════════════════════════════════════════════════
if "admin_logged" not in st.session_state:
    st.session_state.admin_logged = False

# ══════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%); }
    h1, h2, h3 { color: #ffd700 !important; font-family: 'Arial Black', sans-serif; }
    .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,215,0,0.3); 
            border-radius: 15px; padding: 25px; margin: 10px 0; }
    .match-card { background: rgba(255,255,255,0.08); border-radius: 10px; padding: 15px; 
                  margin: 8px 0; border-left: 4px solid #ffd700; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# FUNCIONES
# ══════════════════════════════════════════════════════════
def get_partidos():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client.table('partidos').select('*').execute().data or []
    except:
        return []

# ══════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown("<h1>🦂 SCORPION ELITE</h1>", unsafe_allow_html=True)
with col2:
    if st.session_state.admin_logged:
        if st.button("🔒 Cerrar", use_container_width=True):
            st.session_state.admin_logged = False
            st.rerun()
    else:
        if st.button("🔐 Login", use_container_width=True):
            st.session_state.admin_logged = True
            st.rerun()

st.markdown("<hr style='border-color:rgba(255,215,0,0.3)'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# LOGIN
# ══════════════════════════════════════════════════════════
if st.session_state.admin_logged:
    menu = st.radio("", ["📅 Partidos", "📊 Predicciones", "⚙️ Config"], horizontal=True)
else:
    menu = None

# ══════════════════════════════════════════════════════════
# PÁGINA: LOGIN
# ══════════════════════════════════════════════════════════
if not st.session_state.admin_logged:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center'>🔐 Login</h2>", unsafe_allow_html=True)
        pwd = st.text_input("Contraseña", type="password")
        if st.button("🔓 Ingresar"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.admin_logged = True
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta")

# ══════════════════════════════════════════════════════════
# PÁGINA: PARTIDOS
# ══════════════════════════════════════════════════════════
elif menu == "📅 Partidos":
    st.markdown("<h2>📅 Partidos del Día</h2>", unsafe_allow_html=True)
    
    partidos = get_partidos()
    
    # Filtros
    col1, col2 = st.columns([1, 1])
    with col1:
        filtro_fecha = st.selectbox("Fecha", ["Todas", "Hoy", "Mañana"])
    with col2:
        filtro_liga = st.selectbox("Liga", ["Todas"] + sorted(set(p.get('liga','') for p in partidos if p.get('liga'))) or ["Todas"])
    
    # Filtrar
    if filtro_fecha == "Hoy":
        partidos = [p for p in partidos if p.get('fecha') == date.today().isoformat()]
    elif filtro_fecha == "Mañana":
        partidos = [p for p in partidos if p.get('fecha') == (date.today() + timedelta(days=1)).isoformat()]
    
    if filtro_liga != "Todas":
        partidos = [p for p in partidos if p.get('liga') == filtro_liga]
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if partidos:
        st.success(f"✅ {len(partidos)} partidos encontrados")
        for p in sorted(partidos, key=lambda x: x.get('hora', '')):
            liga = p.get('liga', 'N/A')
            hora = p.get('hora', '--:--')
            local = p.get('equipo_local', '?')
            visitante = p.get('equipo_visitante', '?')
            
            st.markdown(f"""
            <div class="match-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <span style="color:#ffd700; font-size:12px;">{liga}</span>
                        <h3 style="margin:5px 0;">{local} <span style="color:#888">vs</span> {visitante}</h3>
                    </div>
                    <div style="text-align:right;">
                        <span style="color:#ffd700; font-size:20px; font-weight:bold;">{hora}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📭 No hay partidos para los filtros seleccionados")

# ══════════════════════════════════════════════════════════
# PÁGINA: PREDICCIONES
# ══════════════════════════════════════════════════════════
elif menu == "📊 Predicciones":
    st.markdown("<h2>📊 Predicciones</h2>", unsafe_allow_html=True)
    st.info("Pronto disponible...")

# ══════════════════════════════════════════════════════════
# PÁGINA: CONFIGURACIÓN
# ══════════════════════════════════════════════════════════
elif menu == "⚙️ Config":
    st.markdown("<h2>⚙️ Configuración</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class="card">
        <h3>🔑 API Keys</h3>
        <p>SUPABASE_URL: {'✅ Configurado' if SUPABASE_URL else '❌ Falta'}</p>
        <p>SUPABASE_KEY: {'✅ Configurado' if SUPABASE_KEY else '❌ Falta'}</p>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════
st.markdown("<br><hr style='border-color:rgba(255,215,0,0.3)'><p style='text-align:center;color:#555'>🦂 Scorpion Elite © 2026</p>", unsafe_allow_html=True)
