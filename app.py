import streamlit as st
import os

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "scorpion2026")

# CSS
st.markdown("""
<style>
.stApp { background: #0a0a0a; }
.main-title { color: #ffd700; font-size: 56px; font-weight: bold; text-align: center; margin: 0; }
</style>
""", unsafe_allow_html=True)

# Session state
if "logged" not in st.session_state:
    st.session_state.logged = False

# Header con logo y login
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<p class="main-title">🦂 Scorpion Elite</p>', unsafe_allow_html=True)
with col2:
    if not st.session_state.logged:
        with st.form("login_form", clear_on_submit=True):
            password = st.text_input("Password", type="password", label_visibility="collapsed")
            submitted = st.form_submit_button("Login")
            if submitted:
                if password == ADMIN_PASSWORD:
                    st.session_state.logged = True
                    st.rerun()
                else:
                    st.error("Incorrecta")
    else:
        st.markdown("### ✅ Conectado")
        if st.button("Logout"):
            st.session_state.logged = False
            st.rerun()
