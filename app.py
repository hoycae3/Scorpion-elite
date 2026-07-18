import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False
if "show_password" not in st.session_state:
    st.session_state.show_password = False

# Header - título a la izquierda, login a la derecha
left_col, right_col = st.columns([4, 1])

with left_col:
    st.markdown('<h1 style="color: #ffd700; font-size: 52px; margin: 0;">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)

with right_col:
    if not st.session_state.logged:
        if not st.session_state.show_password:
            # Mostrar solo el botón
            if st.button("🔐 Login", type="primary"):
                st.session_state.show_password = True
                st.rerun()
        else:
            # Mostrar campo de contraseña y botón entrar
            password = st.text_input("", type="password", label_visibility="collapsed", placeholder="Password", key="pw")
            if st.button("Entrar", type="primary"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.session_state.show_password = False
                    st.rerun()
                else:
                    st.error("Incorrecta")
            if st.button("Cancelar"):
                st.session_state.show_password = False
                st.rerun()
    else:
        st.success("✅")
        if st.button("Logout"):
            st.session_state.logged = False
            st.rerun()
