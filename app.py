import streamlit as st

BG = '#070b0e'
CARD = '#0d131a'
BORDER = '#1b2430'
GREEN = '#22c55e'
TITLE = '#a3e635'
MUTED = '#94a3b8'
ORANGE = '#f59e0b'

st.set_page_config(page_title='SCORPION ELITE', layout='wide')

st.markdown(f"""
<style>
[data-testid="stSidebar"], header, .stDeployButton {{display:none !important;}}
.stApp {{padding:0 !important; background: {BG};}}
[data-testid="stMainBlockContainer"] {{padding:0 !important; background: {BG};}}
</style>
<div style="background:{BG}; min-height:100vh; font-family:Arial,sans-serif;">

<div style="background:{CARD}; padding:12px 30px; border-bottom:1px solid {BORDER}; display:flex; justify-content:space-between; align-items:center;">
<div><div style="color:{ORANGE}; font-size:22px; font-weight:bold;">SCORPION ELITE</div>
<div style="color:{MUTED}; font-size:10px; letter-spacing:2px;">ANALISIS Y TENDENCIAS</div></div>
<div style="display:flex; gap:6px;">
<button style="background:{GREEN}; color:{BG}; border:none; padding:6px 14px; border-radius:4px; font-size:11px; font-weight:bold;">FUTBOL</button>
<button style="background:transparent; color:{MUTED}; border:1px solid {BORDER}; padding:6px 14px; border-radius:4px; font-size:11px;">BALONCESTO</button>
<button style="background:transparent; color:{MUTED}; border:1px solid {BORDER}; padding:6px 14px; border-radius:4px; font-size:11px;">TENIS</button>
<button style="background:transparent; color:{MUTED}; border:1px solid {BORDER}; padding:6px 14px; border-radius:4px; font-size:11px;">HOCKEY</button>
<button style="background:transparent; color:{MUTED}; border:1px solid {BORDER}; padding:6px 14px; border-radius:4px; font-size:11px;">MMA</button>
</div>
<div style="display:flex; gap:10px; align-items:center;">
<input type="text" placeholder="Buscar..." style="background:{BG}; border:1px solid {BORDER}; color:white; padding:6px 12px; border-radius:4px; font-size:12px; width:180px;">
<button style="background:transparent; color:{MUTED}; border:1px solid {BORDER}; padding:6px 12px; border-radius:4px; font-size:11px;">HOY</button>
</div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)

matches = [('Manchester City\nArsenal','16:00','Premier League'),('Real Madrid\nBarcelona','17:30','LaLiga'),('Bayern\nDortmund','14:30','Bundesliga'),('PSG\nOlympique','15:00','Ligue 1'),('Inter\nAC Milan','20:45','Serie A')]
odds = [('Pinnacle','1.91','3.80','4.20','BEST'),('Bet365','1.87','3.75','4.00','-'),('Betano','1.85','3.70','3.95','-'),('1xBet','1.90','3.78','4.10','-'),('Stake','1.88','3.76','4.05','-')]

with c1:
    st.markdown(f"""<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:16px; margin:15px; min-height:400px;">
    <div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:15px; border-bottom:1px solid {BORDER}; padding-bottom:8px;">PARTIDOS DESTACADOS</div>""", unsafe_allow_html=True)
    for m in matches:
        st.markdown(f"""<div style="background:{BG}; padding:10px; margin-bottom:8px; border-radius:4px; border-left:3px solid {ORANGE};">
        <div style="font-weight:bold; font-size:12px; color:white; white-space:pre-line;">{m[0]}</div>
        <div style="display:flex; justify-content:space-between; margin-top:4px;">
        <span style="color:{MUTED}; font-size:10px;">{m[2]}</span>
        <span style="color:{MUTED}; font-size:10px;">{m[1]}</span></div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f"""<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:16px; margin:15px; min-height:400px;">
    <div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:15px; border-bottom:1px solid {BORDER}; padding-bottom:8px;">MEJOR PICK DEL DIA</div>
    <div style="text-align:center; color:{MUTED}; font-size:11px; margin-bottom:10px;">Premier League - Jornada 36</div>
    <div style="text-align:center; margin:15px 0;">
    <span style="font-size:16px; font-weight:bold;">Manchester City</span>
    <span style="color:{MUTED}; margin:0 10px;">VS</span>
    <span style="font-size:16px; font-weight:bold;">Arsenal</span></div>
    <div style="background:{BG}; border:1px solid {BORDER}; border-radius:6px; padding:12px; margin-bottom:15px; display:flex; justify-content:space-between; align-items:center;">
    <div><div style="color:{MUTED}; font-size:9px;">MERCADO</div><div style="color:{MUTED}; font-size:11px;">Resultado Final</div><div style="color:white; font-size:13px; font-weight:bold;">Manchester City Gana</div></div>
    <div style="text-align:right;"><div style="color:{MUTED}; font-size:9px;">CUOTA</div><div style="display:flex; align-items:center; gap:8px;"><span style="font-size:22px; font-weight:bold; color:white;">1.91</span><span style="background:#1e293b; color:white; font-size:10px; padding:2px 8px; border-radius:4px;">Pinnacle</span></div></div>
    </div>""", unsafe_allow_html=True)
    m1,m2,m3,m4 = st.columns(4)
    with m1: st.markdown(f"""<div style="text-align:center;"><div style="color:{MUTED}; font-size:9px;">PROBABILIDAD</div><div style="color:{GREEN}; font-size:20px; font-weight:bold;">72%</div></div>""", unsafe_allow_html=True)
    with m2: st.markdown(f"""<div style="text-align:center;"><div style="color:{MUTED}; font-size:9px;">CONFIANZA</div><div style="color:{GREEN}; font-size:20px; font-weight:bold;">92%</div><div style="color:{GREEN}; font-size:8px; font-weight:bold;">MUY ALTA</div></div>""", unsafe_allow_html=True)
    with m3: st.markdown(f"""<div style="text-align:center;"><div style="color:{MUTED}; font-size:9px;">VALOR</div><div style="color:{GREEN}; font-size:20px; font-weight:bold;">+19%</div><div style="color:{GREEN}; font-size:8px; font-weight:bold;">VALUE</div></div>""", unsafe_allow_html=True)
    with m4: st.markdown(f"""<div style="text-align:center;"><div style="color:{MUTED}; font-size:9px;">RIESGO</div><div style="color:{GREEN}; font-size:15px; font-weight:bold;">BAJO</div></div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    st.markdown(f"""<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:16px; margin:15px; min-height:400px;">
    <div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:15px; border-bottom:1px solid {BORDER}; padding-bottom:8px;">COMPARADOR DE CUOTAS</div>
    <table style="width:100%;"><tr style="border-bottom:1px solid {BORDER};"><th style="color:{MUTED}; font-size:10px; text-align:center; padding:8px 5px; font-weight:bold;">CASA</th><th style="color:{MUTED}; font-size:10px; text-align:center;">1</th><th style="color:{MUTED}; font-size:10px; text-align:center;">X</th><th style="color:{MUTED}; font-size:10px; text-align:center;">2</th><th style="color:{MUTED}; font-size:10px; text-align:center;">MEJOR</th></tr>""", unsafe_allow_html=True)
    for o in odds:
        cls = f'color:{ORANGE}; font-weight:bold;' if o[4] == 'BEST' else 'color:white;'
        st.markdown(f"""<tr style="border-bottom:1px solid {BORDER};"><td style="text-align:left; font-weight:bold; padding:10px 5px; color:white; font-size:12px;">{o[0]}</td><td style="text-align:center; padding:10px 5px; font-size:12px; {cls}">{o[1]}</td><td style="text-align:center; padding:10px 5px; font-size:12px; {cls}">{o[2]}</td><td style="text-align:center; padding:10px 5px; font-size:12px; {cls}">{o[3]}</td><td style="text-align:center; padding:10px 5px; font-size:12px; {cls}">{o[4]}</td></tr>""", unsafe_allow_html=True)
    st.markdown(f"""</table><div style="text-align:center; margin-top:15px;"><a href="#" style="color:{GREEN}; font-size:11px; text-decoration:none;">Ver todas las cuotas</a></div></div>""", unsafe_allow_html=True)

st.markdown(f"""<div style="text-align:center; padding:20px; border-top:1px solid {BORDER}; margin-top:10px;"><span style="color:{MUTED}; font-size:11px;">Scorpion Elite 2025 - Solo uso informativo</span></div></div>""", unsafe_allow_html=True)
