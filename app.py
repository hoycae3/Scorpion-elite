import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False

# Modal de login
if st.session_state.show_login:
    with st.modal("🔐 Login"):
        password = st.text_input("Password", type="password", label_visibility="collapsed")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Entrar"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.session_state.show_login = False
                    st.rerun()
                else:
                    st.error("Incorrecta")
        with col2:
            if st.button("Cancelar"):
                st.session_state.show_login = False
                st.rerun()

# Header
left_col, right_col = st.columns([4, 1])

with left_col:
    st.markdown('<h1 style="color: #ffd700; font-size: 52px; margin: 0;">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)

with right_col:
    if not st.session_state.logged:
        if st.button("🔐 Login", type="primary"):
            st.session_state.show_login = True
            st.rerun()
    else:
        st.success("✅ Conectado")
        if st.button("Logout"):
            st.session_state.logged = False
            st.rerun()
