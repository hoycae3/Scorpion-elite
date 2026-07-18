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
.header { display: flex; justify-content: space-between; align-items: center; }
</style>
""", unsafe_allow_html=True)

# Header
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown('<h1 class="title">🦂 Scorpion Elite</h1>', unsafe_allow_html=True)
with col2:
    if not st.session_state.logged:
        with st.expander("🔐 Login", expanded=False):
            password = st.text_input("Password", type="password", label_visibility="collapsed", placeholder="Ingresa password")
            if st.button("Entrar", type="primary"):
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.rerun()
                else:
                    st.error("Incorrecta")
    else:
        st.success("✅ Conectado")
        if st.button("Logout"):
            st.session_state.logged = False
            st.rerun()
