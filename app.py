import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

if "logged" not in st.session_state:
    st.session_state.logged = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False

# CSS
st.markdown("""
<style>
.header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding: 10px 0;
}
.title { color: #ffd700; font-size: 52px; margin: 0; }
.dropdown {
    position: relative;
    display: inline-block;
    text-align: right;
}
.dropbtn {
    background: #1a1a1a;
    color: white;
    padding: 10px 20px;
    font-size: 16px;
    border: none;
    cursor: pointer;
    border-radius: 6px;
}
.dropdown-content {
    display: none;
    position: absolute;
    right: 0;
    background: #1a1a1a;
    min-width: 220px;
    box-shadow: 0px 8px 16px rgba(0,0,0,0.3);
    border-radius: 8px;
    padding: 20px;
    z-index: 1;
    border: 1px solid #444;
    text-align: center;
}
.dropdown:hover .dropdown-content {
    display: block;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header">
    <h1 class="title">🦂 Scorpion Elite</h1>
    <div class="dropdown">
        <button class="dropbtn">🔐 Login ▾</button>
        <div class="dropdown-content">
""", unsafe_allow_html=True)

# Campos del login (dentro del dropdown)
if not st.session_state.logged:
    password = st.text_input("", type="password", label_visibility="collapsed", placeholder="Password", key="pw")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Entrar", type="primary"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("Incorrecta")
    with col2:
        if st.button("Cancelar"):
            pass
else:
    st.success("✅ Conectado")
    if st.button("Logout"):
        st.session_state.logged = False
        st.rerun()

# Cerrar dropdown
st.markdown("""
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
