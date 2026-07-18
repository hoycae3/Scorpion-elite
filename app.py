import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False

# CSS
st.markdown("""
<style>
.stApp { background: #0a0a0a; }
.title { color: #ffd700; font-size: 52px; font-weight: bold; margin: 0; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 20px 0; border-bottom: 2px solid #333; }
.welcome { color: #ffd700; font-size: 36px; text-align: center; margin-top: 50px; }
</style>
""", unsafe_allow_html=True)

# Login
if not st.session_state.logged:
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    with col2:
        with st.expander("🔐 Login", expanded=False):
            password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Ingresa password")
            if st.button("Entrar", type="primary"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.rerun()
                else:
                    st.error("Incorrecta")

# Pantalla después del login
else:
    # Header con logout
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
    with col2:
        if st.button("🔓 Logout"):
            st.session_state.logged = False
            st.rerun()
    
    # Bienvenida
    st.markdown('<h2 class="welcome">¡Bienvenido!</h2>', unsafe_allow_html=True)
    
    # Contenido de ejemplo
    st.markdown("""
    <style>
    .panel {
        background: #1a1a1a;
        padding: 30px;
        border-radius: 15px;
        margin: 30px auto;
        max-width: 800px;
        border: 1px solid #333;
    }
    .panel h3 { color: #ffd700; margin-top: 0; }
    .panel p { color: #ccc; }
    .btn {
        background: #ffd700;
        color: black;
        padding: 10px 20px;
        border-radius: 6px;
        text-decoration: none;
        display: inline-block;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="panel">
        <h3>📊 Panel de Control</h3>
        <p>Bienvenido a Scorpion Elite. Aquí podrás ver los partidos y predicciones.</p>
        <p>Próximamente: datos en tiempo real.</p>
    </div>
    """, unsafe_allow_html=True)
