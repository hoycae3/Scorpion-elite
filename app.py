import streamlit as st

st.set_page_config(page_title='SCORPION ELITE', layout='wide')

BG = '#070b0e'
CARD = '#0d131a'
BORDER = '#1b2430'
GREEN = '#22c55e'
TITLE = '#a3e635'
MUTED = '#94a3b8'
ORANGE = '#f59e0b'

st.markdown(f'''
<style>
.stApp {{background-color:{BG}; padding-top:0px !important;}}
[data-testid="stSidebar"] {{display:none;}}
header {{display:none !important;}}
.stDeployButton {{display:none;}}
[data-testid="stMainBlockContainer"] {{padding:0; padding-top:0; background:{BG}; max-width:100%;}}
[data-testid="stMain"] {{padding:0; background:{BG};}}
</style>
''', unsafe_allow_html=True)

# HEADER - pegado arriba
st.markdown(f'''
<div style="background:{CARD}; padding:12px 30px; border-bottom:1px solid {BORDER}; display:flex; justify-content:space-between; align-items:center; margin-top:0;">
    <div><div style="color:{ORANGE}; font-size:22px; font-weight:bold;">SCORPION ELITE</div><div style="color:{MUTED}; font-size:9px; letter-spacing:2px;">ANALISIS Y TENDENCIAS DEPORTIVAS</div></div>
    <div style="display:flex; gap:6px; align-items:center;">
        <span style="background:{GREEN}; color:{BG}; padding:6px 14px; border-radius:4px; font-size:11px; font-weight:bold;">FUTBOL</span>
        <span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">BALONCESTO</span>
        <span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">TENIS</span>
        <span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 14px; border-radius:4px; font-size:11px;">MMA</span>
    </div>
    <div style="display:flex; gap:8px; align-items:center;">
        <input type="text" placeholder="Buscar..." style="background:{BG}; border:1px solid {BORDER}; color:white; padding:6px 10px; border-radius:4px; font-size:11px; width:160px;">
        <span style="border:1px solid {BORDER}; color:{MUTED}; padding:6px 10px; border-radius:4px; font-size:11px;">HOY</span>
    </div>
</div>
''', unsafe_allow_html=True)

# 3 COLUMNAS
c1, c2, c3 = st.columns(3)

matches = [
    ('Manchester City<br>Arsenal', '16:00', 'Premier League'),
    ('Real Madrid<br>Barcelona', '17:30', 'LaLiga'),
    ('Bayern<br>Dortmund', '14:30', 'Bundesliga'),
    ('PSG<br>Lyon', '15:00', 'Ligue 1'),
    ('Inter<br>AC Milan', '20:45', 'Serie A'),
]

with c1:
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:14px; margin:8px;">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid {BORDER};">PARTIDOS DESTACADOS</div>', unsafe_allow_html=True)
    for m in matches:
        st.markdown(f'<div style="background:{BG}; padding:8px; margin-bottom:6px; border-radius:4px; border-left:3px solid {ORANGE};"><div style="font-weight:bold; font-size:11px; color:white;">{m[0]}</div><div style="display:flex; justify-content:space-between; margin-top:3px;"><span style="color:{MUTED}; font-size:9px;">{m[2]}</span><span style="color:{MUTED}; font-size:9px;">{m[1]}</span></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:14px; margin:8px;">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid {BORDER};">MEJOR PICK DEL DIA</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; color:{MUTED}; font-size:10px; margin-bottom:8px;">Premier League - Jornada 36</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="text-align:center; margin:10px 0;"><span style="font-size:14px; font-weight:bold;">Manchester City</span> <span style="color:{MUTED};">VS</span> <span style="font-size:14px; font-weight:bold;">Arsenal</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div style="background:{BG}; border:1px solid {BORDER}; border-radius:6px; padding:10px; margin-bottom:10px; display:flex; justify-content:space-between;"><div><div style="color:{MUTED}; font-size:8px;">MERCADO</div><div style="color:{MUTED}; font-size:10px;">Resultado Final</div><div style="font-weight:bold; color:white; font-size:12px;">Manchester City Gana</div></div><div style="text-align:right;"><div style="color:{MUTED}; font-size:8px;">CUOTA</div><div><span style="font-size:20px; font-weight:bold; color:white;">1.91</span> <span style="background:#1e293b; color:white; font-size:9px; padding:2px 6px; border-radius:4px;">Pinnacle</span></div></div></div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">PROBABILIDAD</div><div style="color:{GREEN}; font-size:18px; font-weight:bold;">72%</div></div>', unsafe_allow_html=True)
    with m2: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">CONFIANZA</div><div style="color:{GREEN}; font-size:18px; font-weight:bold;">92%</div><div style="color:{GREEN}; font-size:7px;">MUY ALTA</div></div>', unsafe_allow_html=True)
    with m3: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">VALOR</div><div style="color:{GREEN}; font-size:18px; font-weight:bold;">+19%</div><div style="color:{GREEN}; font-size:7px;">VALUE</div></div>', unsafe_allow_html=True)
    with m4: st.markdown(f'<div style="text-align:center;"><div style="color:{MUTED}; font-size:8px;">RIESGO</div><div style="color:{GREEN}; font-size:14px; font-weight:bold;">BAJO</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3:
    odds = [
        ('Pinnacle', '1.91', '3.80', '4.20', True),
        ('Bet365', '1.87', '3.75', '4.00', False),
        ('Betano', '1.85', '3.70', '3.95', False),
        ('1xBet', '1.90', '3.78', '4.10', False),
        ('Stake', '1.88', '3.76', '4.05', False),
    ]
    st.markdown(f'<div style="background:{CARD}; border:1px solid {BORDER}; border-radius:8px; padding:14px; margin:8px;">', unsafe_allow_html=True)
    st.markdown(f'<div style="color:{TITLE}; font-size:12px; font-weight:bold; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid {BORDER};">COMPARADOR DE CUOTAS</div>', unsafe_allow_html=True)
    st.markdown(f'<table style="width:100%;"><tr style="border-bottom:1px solid {BORDER};"><th style="color:{MUTED}; font-size:9px; text-align:left; padding:6px;">CASA</th><th style="color:{MUTED}; font-size:9px; text-align:center;">1</th><th style="color:{MUTED}; font-size:9px; text-align:center;">X</th><th style="color:{MUTED}; font-size:9px; text-align:center;">2</th><th style="color:{MUTED}; font-size:9px; text-align:center;">*</th></tr>', unsafe_allow_html=True)
    for o in odds:
        cls = f'color:{ORANGE}; font-weight:bold;' if o[4] else 'color:white;'
        st.markdown(f'<tr style="border-bottom:1px solid {BORDER};"><td style="padding:6px; color:white; font-weight:bold; font-size:11px;">{o[0]}</td><td style="text-align:center; padding:6px; font-size:11px; {cls}">{o[1]}</td><td style="text-align:center; padding:6px; font-size:11px; {cls}">{o[2]}</td><td style="text-align:center; padding:6px; font-size:11px; {cls}">{o[3]}</td><td style="text-align:center; padding:6px; font-size:11px; {cls}">{"*" if o[4] else "-"}</td></tr>', unsafe_allow_html=True)
    st.markdown(f'</table><div style="text-align:center; margin-top:10px;"><a href="#" style="color:{GREEN}; font-size:10px;">Ver todas las cuotas</a></div></div>', unsafe_allow_html=True)

# FOOTER
st.markdown(f'<div style="text-align:center; padding:15px; border-top:1px solid {BORDER}; margin-top:10px;"><span style="color:{MUTED}; font-size:10px;">Scorpion Elite 2025 - Solo uso informativo</span></div>', unsafe_allow_html=True)
