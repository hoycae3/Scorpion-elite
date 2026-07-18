import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False

st.markdown("""
<style>
    .stApp { background: #0a0a0a; }
    .title { color: #ffd700; font-size: 40px; margin: 0; }
</style>
""", unsafe_allow_html=True)

# Header horizontal
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
