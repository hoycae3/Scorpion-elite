import streamlit as st
import os
from supabase import create_client

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

# Configuración Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://jjtifureeygvygxtpuku.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpqdGlmdXJlZXlndnlneHRwdWt1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQzMTI2NDcsImV4cCI6MjA5OTg4ODY0N30.6f8dgLmHx9x9W-5X2Ld31rPkeZ6HJGSeGgx3oq9XSRA")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

# Inicializar Supabase
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase = init_supabase()

# CSS
st.markdown("""
<style>
.stApp { background: #0a0a0a; }
.title { color: #ffd700; font-size: 48px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Session state
if "logged" not in st.session_state:
    st.session_state.logged = False

# Header
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<p class="title">🦂 Scorpion Elite</p>', unsafe_allow_html=True)
with col2:
    if not st.session_state.logged:
        password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Password")
        if st.button("Login", type="primary"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Incorrecta")
    else:
        st.success("Conectado")
        if st.button("Logout"):
            st.session_state.logged = False
            st.rerun()

# Mostrar datos solo si está logueado
if st.session_state.logged:
    try:
        response = supabase.table('partidos').select('*').execute()
        
        if response.data:
            st.success(f"{len(response.data)} partidos")
        else:
            st.info("No hay partidos")
    except Exception as e:
        st.error(f"Error: {str(e)[:100]}")
