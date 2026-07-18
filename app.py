import streamlit as st
import os
from datetime import date, timedelta

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if "logged" not in st.session_state:
    st.session_state.logged = False

st.markdown("""
<style>
    .stApp { background: #0a0a0a; }
    .title { color: #ffd700; font-size: 48px; margin: 0; }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([3, 1])

with col1:
    st.markdown('<p class="title">🦂 Scorpion Elite</p>', unsafe_allow_html=True)

with col2:
    if not st.session_state.logged:
        password = st.text_input("Password", label_visibility="collapsed", placeholder="Password", type="password")
        if password:
            if password == ADMIN_PASSWORD:
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Incorrecta")
    else:
        st.success("Bienvenido")
        if st.button("Logout"):
            st.session_state.logged = False
            st.rerun()

st.markdown("---")

# Partidos
def get_partidos():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client.table('partidos').select('*').execute().data or []
    except:
        return []

partidos = get_partidos()

# Filtros
col1, col2 = st.columns([1, 1])
with col1:
    filtro = st.selectbox("Fecha", ["Todas", "Hoy", "Mañana"])
with col2:
    ligas = ["Todas"] + sorted(set(p.get('liga','') for p in partidos if p.get('liga')))
    filtro_liga = st.selectbox("Liga", ligas if ligas else ["Todas"])

# Filtrar
if filtro == "Hoy":
    partidos = [p for p in partidos if p.get('fecha') == date.today().isoformat()]
elif filtro == "Mañana":
    partidos = [p for p in partidos if p.get('fecha') == (date.today() + timedelta(days=1)).isoformat()]

if filtro_liga != "Todas":
    partidos = [p for p in partidos if p.get('liga') == filtro_liga]

st.markdown("---")

# Tabla
if partidos:
    st.success(f"{len(partidos)} partidos")
    data = [{
        "Hora": p.get('hora', '--:--'),
        "Liga": p.get('liga', 'N/A'),
        "Local": p.get('equipo_local', '?'),
        "Visitante": p.get('equipo_visitante', '?')
    } for p in sorted(partidos, key=lambda x: x.get('hora', ''))]
    
    st.dataframe(data, use_container_width=True, hide_index=True)
else:
    st.info("No hay partidos")
