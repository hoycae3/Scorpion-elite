import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="centered")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False

st.markdown("""
<style>
    .stApp { background: #0a0a0a; }
    h1 { color: #ffd700; text-align: center; font-size: 60px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>🦂</h1>", unsafe_allow_html=True)
st.markdown("<h1 style='font-size:30px'>SCORPION ELITE</h1>", unsafe_allow_html=True)

if not st.session_state.logged:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Contraseña", type="password")
        if st.button("🔓 Ingresar"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("❌ Incorrecta")
else:
    st.success("✅ Bienvenido")
    if st.button("🔒 Cerrar"):
        st.session_state.logged = False
        st.rerun()
