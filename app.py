import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="centered")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False

st.markdown("""
<style>
    .stApp { background: #0a0a0a; }
    .title { color: #ffd700; font-size: 50px; text-align: center; margin-bottom: 30px; }
    .header { display: flex; justify-content: center; align-items: center; gap: 20px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="title">🦂 Scorpion Elite</p>', unsafe_allow_html=True)

if not st.session_state.logged:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("Password", type="password")
        if st.button("Login"):
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
