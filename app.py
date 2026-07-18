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
.header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 0;
    border-bottom: 1px solid #333;
}
.title {
    color: #ffd700;
    font-size: 48px;
    font-weight: bold;
    margin: 0;
}
.login-box {
    background: #1a1a1a;
    padding: 15px 20px;
    border-radius: 10px;
    border: 1px solid #333;
}
.stTextInput > div > div > input {
    background: #0a0a0a;
    color: white;
    border: 1px solid #444;
    border-radius: 6px;
}
.stButton > button {
    background: #ffd700;
    color: black;
    border: none;
    border-radius: 6px;
    font-weight: bold;
}
.stButton > button:hover {
    background: #ffed4a;
}
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="header">
    <h1 class="title">🦂 Scorpion Elite</h1>
    <div class="login-box">
""", unsafe_allow_html=True)

# Login
if not st.session_state.logged:
    col1, col2 = st.columns([2, 1])
    with col1:
        password = st.text_input("", type="password", label_visibility="collapsed", placeholder="Password")
    with col2:
        if st.button("Login", type="primary"):
            if password == ADMIN_PASSWORD:
                st.session_state.logged = True
                st.rerun()
            else:
                st.error("❌")
else:
    st.markdown("### ✅ Conectado")
    if st.button("Logout"):
        st.session_state.logged = False
        st.rerun()

st.markdown("</div></div>", unsafe_allow_html=True)
