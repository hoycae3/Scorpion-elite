import streamlit as st
import pandas as pd

BG_COLOR = "#070b0e"
CARD_BG = "#0d131a"
BORDER_COLOR = "#1b2430"
GREEN_ACCENT = "#22c55e"
TITLE_GREEN = "#a3e635"
TEXT_MUTED = "#94a3b8"
ORANGE = "#f59e0b"

st.set_page_config(page_title="SCORPION ELITE", page_icon="scorpion", layout="wide")

st.markdown(f"""
<style>
.stApp {{ background-color: {BG_COLOR}; color: white; }}
.main-header {{ background-color: {CARD_BG}; padding: 15px 20px; border-bottom: 1px solid {BORDER_COLOR}; margin-bottom: 20px; }}
.logo-text {{ color: {ORANGE}; font-size: 24px; font-weight: bold; }}
.logo-sub {{ color: {TEXT_MUTED}; font-size: 10px; }}
.card-style {{ background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; border-radius: 8px; padding: 16px; height: 100%; }}
.section-title {{ color: {TITLE_GREEN}; font-size: 12px; font-weight: bold; margin-bottom: 15px; }}
.match-row {{ background-color: {BG_COLOR}; padding: 12px; border-bottom: 1px solid {BORDER_COLOR}; color: white; font-size: 12px; }}
.match-name {{ font-weight: bold; white-space: pre-line; }}
.match-time {{ color: {TEXT_MUTED}; }}
.match-league {{ color: {TEXT_MUTED}; font-size: 11px; }}
.odds-table {{ width: 100%; }}
.odds-table th {{ color: {TEXT_MUTED}; font-size: 10px; text-align: center; padding: 8px 5px; border-bottom: 1px solid {BORDER_COLOR}; }}
.odds-table td {{ color: white; font-size: 12px; text-align: center; padding: 10px 5px; border-bottom: 1px solid {BORDER_COLOR}; }}
.odds-table td:first-child {{ text-align: left; font-weight: bold; }}
.best-odds {{ color: {ORANGE}; font-weight: bold; }}
.metric-box {{ text-align: center; padding: 10px; }}
.metric-label {{ color: {TEXT_MUTED}; font-size: 9px; }}
.metric-value {{ color: {GREEN_ACCENT}; font-size: 20px; font-weight: bold; margin: 5px 0; }}
.metric-sub {{ color: {GREEN_ACCENT}; font-size: 8px; font-weight: bold; }}
.nav-btn {{ background-color: transparent; border: 1px solid {BORDER_COLOR}; color: {TEXT_MUTED}; padding: 6px 16px; border-radius: 4px; font-size: 12px; cursor: pointer; }}
.nav-btn-active {{ background-color: {GREEN_ACCENT}; color: {BG_COLOR}; font-weight: bold; }}
.search-input {{ background-color: {CARD_BG}; border: 1px solid {BORDER_COLOR}; color: white; border-radius: 4px; padding: 6px 12px; font-size: 12px; }}
.footer-link {{ color: {GREEN_ACCENT}; font-size: 11px; text-decoration: none; }}
</style>
""", unsafe_allow_html=True)

data_partidos = [
    {"Partido": "Manchester City\nArsenal", "Hora": "16:00", "Liga": "Premier League"},
    {"Partido": "Real Madrid\nBarcelona", "Hora": "17:30", "Liga": "LaLiga"},
    {"Partido": "Bayern Munchen\nDortmund", "Hora": "14:30", "Liga": "Bundesliga"},
    {"Partido": "PSG\nOlympique Lyon", "Hora": "15:00", "Liga": "Ligue 1"},
    {"Partido": "Inter\nAC Milan", "Hora": "20:45", "Liga": "Serie A"},
]

data_comparador = [
    {"CASA": "Pinnacle", "1": "1.91", "X": "3.80", "2": "4.20", "MEJOR": "BEST"},
    {"CASA": "Bet365", "1": "1.87", "X": "3.75", "2": "4.00", "MEJOR": "-"},
    {"CASA": "Betano", "1": "1.85", "X": "3.70", "2": "3.95", "MEJOR": "-"},
    {"CASA": "1xBet", "1": "1.90", "X": "3.78", "2": "4.10", "MEJOR": "-"},
    {"CASA": "Stake", "1": "1.88", "X": "3.76", "2": "4.05", "MEJOR": "-"},
]

st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
            <span class="logo-text">SCORPION ELITE</span>
            <div class="logo-sub">ANALISIS Y TENDENCIAS DEPORTIVAS</div>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <span class="nav-btn nav-btn-active">FUTBOL</span>
            <span class="nav-btn">BALONCESTO</span>
            <span class="nav-btn">TENIS</span>
            <span class="nav-btn">HOCKEY</span>
            <span class="nav-btn">BEISBOL</span>
            <span class="nav-btn">MMA</span>
        </div>
        <div style="display: flex; gap: 10px; align-items: center;">
            <input class="search-input" type="text" placeholder="Buscar...">
            <span class="nav-btn">HOY</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="card-style">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">PARTIDOS DESTACADOS</div>', unsafe_allow_html=True)
    for p in data_partidos:
        st.markdown(f'<div class="match-row"><div class="match-name">{p["Partido"]}</div><div style="display: flex; justify-content: space-between;"><span class="match-league">{p["Liga"]}</span><span class="match-time">{p["Hora"]}</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card-style">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">MEJOR PICK DEL DIA</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center; color: {TEXT_MUTED}; font-size: 11px; margin-bottom: 10px;">Premier League - Jornada 36</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center; margin: 15px 0;"><span style="font-size: 16px; font-weight: bold;">Manchester City</span><span style="color: {TEXT_MUTED}; margin: 0 10px;"> VS </span><span style="font-size: 16px; font-weight: bold;">Arsenal</span></div>', unsafe_allow_html=True)
    st.markdown(f"""<div style="background-color: {BG_COLOR}; border: 1px solid {BORDER_COLOR}; border-radius: 6px; padding: 12px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
        <div><div style="color: {TEXT_MUTED}; font-size: 9px;">MERCADO</div><div style="color: {TEXT_MUTED}; font-size: 11px;">Resultado Final</div><div style="color: white; font-size: 13px; font-weight: bold;">Manchester City Gana</div></div>
        <div style="text-align: right;"><div style="color: {TEXT_MUTED}; font-size: 9px;">CUOTA</div><div style="display: flex; align-items: center; gap: 8px;"><span style="font-size: 22px; font-weight: bold; color: white;">1.91</span><span style="background-color: #1e293b; color: white; font-size: 10px; padding: 2px 8px; border-radius: 4px;">Pinnacle</span></div></div>
    </div>""", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><div class="metric-label">PROBABILIDAD</div><div class="metric-value">72%</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><div class="metric-label">CONFIANZA</div><div class="metric-value">92%</div><div class="metric-sub">MUY ALTA</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-box"><div class="metric-label">VALOR</div><div class="metric-value">+19%</div><div class="metric-sub">VALUE BET</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-box"><div class="metric-label">RIESGO</div><div class="metric-value" style="font-size: 15px;">BAJO</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="card-style">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">COMPARADOR DE CUOTAS</div>', unsafe_allow_html=True)
    html = f'<table class="odds-table"><thead><tr><th>CASA</th><th>1</th><th>X</th><th>2</th><th>MEJOR</th></tr></thead><tbody>'
    for row in data_comparador:
        cls = "best-odds" if row["MEJOR"] == "BEST" else ""
        html += f'<tr><td>{row["CASA"]}</td><td class="{cls}">{row["1"]}</td><td class="{cls}">{row["X"]}</td><td class="{cls}">{row["2"]}</td><td class="{cls}">{row["MEJOR"]}</td></tr>'
    html += '</tbody></table>'
    st.markdown(html, unsafe_allow_html=True)
    st.markdown(f'<div style="text-align: center; margin-top: 15px;"><a href="#" class="footer-link">Ver todas las cuotas</a></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown(f'<div style="text-align: center; margin-top: 30px; padding: 20px; border-top: 1px solid {BORDER_COLOR};"><span style="color: {TEXT_MUTED}; font-size: 11px;">Scorpion Elite 2025 - Solo uso informativo</span></div>', unsafe_allow_html=True)
