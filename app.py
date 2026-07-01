import streamlit as st
import os, json, time, math, re, warnings, requests, io
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, date, time as dtime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
warnings.filterwarnings("ignore")

# ═══════════════════════════════════════════════════════════
# CONFIGURACION
# ═══════════════════════════════════════════════════════════
API_FOOTBALL_KEY  = os.getenv("API_FOOTBALL_KEY",  "124c9519df145caf883cd82f0b2a4671")
ODDS_API_KEY      = os.getenv("ODDS_API_KEY",      "")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID",  "")
ADMIN_PASSWORD    = os.getenv("ADMIN_PASSWORD",    "scorpion_admin_2025")

# IDs de ligas en API-Football
LIGAS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League":     {"id": 39,  "pais": "England"},
    "🇪🇸 La Liga":              {"id": 140, "pais": "Spain"},
    "🇩🇪 Bundesliga":           {"id": 78,  "pais": "Germany"},
    "🇮🇹 Serie A":              {"id": 135, "pais": "Italy"},
    "🇫🇷 Ligue 1":              {"id": 61,  "pais": "France"},
    "🇳🇱 Eredivisie":           {"id": 88,  "pais": "Netherlands"},
    "🇵🇹 Primeira Liga":        {"id": 94,  "pais": "Portugal"},
    "🌍 Champions League":      {"id": 2,   "pais": "World"},
    "🌍 Europa League":         {"id": 3,   "pais": "World"},
    "🌍 Conference League":     {"id": 848, "pais": "World"},
    "🌎 Libertadores":          {"id": 13,  "pais": "World"},
    "🌎 Sudamericana":          {"id": 11,  "pais": "World"},
    "🌎 Copa America":          {"id": 9,   "pais": "World"},
    "🌍 Mundial FIFA":          {"id": 1,   "pais": "World"},
    "🇺🇸 MLS":                  {"id": 253, "pais": "USA"},
    "🇲🇽 Liga MX":              {"id": 262, "pais": "Mexico"},
    "🇨🇴 Liga BetPlay":         {"id": 239, "pais": "Colombia"},
    "🇦🇷 Primera Division":     {"id": 128, "pais": "Argentina"},
    "🇧🇷 Brasileirao":          {"id": 71,  "pais": "Brazil"},
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premier":   {"id": 179, "pais": "Scotland"},
    "🇹🇷 Super Lig":            {"id": 203, "pais": "Turkey"},
    "🇸🇦 Saudi Pro League":     {"id": 307, "pais": "Saudi-Arabia"},
}

TEMPORADA = 2024

# ═══════════════════════════════════════════════════════════
# BASE DE DATOS EN MEMORIA (session state)
# Para produccion real usar Supabase o similar
# ═══════════════════════════════════════════════════════════
def init_db():
    if "usuarios_db" not in st.session_state:
        st.session_state.usuarios_db = {
            "admin": {
                "nombre": "Administrador",
                "cedula": "admin",
                "plan": "admin",
                "fecha_inicio": str(date.today()),
                "dias": 9999,
                "activo": True,
                "password": ADMIN_PASSWORD,
            }
        }

def get_usuario(cedula):
    db = st.session_state.get("usuarios_db", {})
    for u in db.values():
        if u.get("cedula") == cedula:
            return u
    return None

def verificar_acceso(usuario):
    if not usuario: return False, "no_existe"
    if usuario["plan"] == "admin": return True, "admin"
    if not usuario.get("activo"): return False, "inactivo"
    inicio = date.fromisoformat(usuario["fecha_inicio"])
    vence  = inicio + timedelta(days=usuario["dias"])
    if date.today() > vence:
        return False, "vencido"
    return True, usuario["plan"]

def dias_restantes(usuario):
    inicio = date.fromisoformat(usuario["fecha_inicio"])
    vence  = inicio + timedelta(days=usuario["dias"])
    return max(0, (vence - date.today()).days)

# ═══════════════════════════════════════════════════════════
# PAGE CONFIG Y CSS
# ═══════════════════════════════════════════════════════════
st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:#080810}
.hdr{background:linear-gradient(135deg,#0d1b2a,#1a1a2e,#16213e);
  border:1px solid #ffd700;border-radius:16px;padding:1.5rem 2rem;
  text-align:center;margin-bottom:1.5rem}
.hdr h1{color:#ffd700;font-size:2.2rem;margin:0;letter-spacing:3px}
.hdr p{color:#aaa;margin:.3rem 0 0;font-size:.95rem}
.lbox{background:#12122a;border:1px solid #ffd700;border-radius:16px;
  padding:2.5rem;max-width:440px;margin:1.5rem auto}
.plan-card{border-radius:12px;padding:1.2rem;margin-bottom:.8rem;
  border:1px solid #334466;cursor:pointer;transition:all .2s}
.plan-free{background:#111122;border-color:#444}
.plan-dia{background:#0d1a0d;border-color:#00aa44}
.plan-semana{background:#0d0d1a;border-color:#4488ff}
.plan-mes{background:#1a0d00;border-color:#ffd700}
.plan-card h3{margin:0 0 4px;font-size:1rem}
.plan-card p{margin:0;font-size:.8rem;color:#aaa}
.mc{background:#12122a;border:1px solid #334466;border-radius:10px;
  padding:1rem;text-align:center}
.mc .v{color:#ffd700;font-size:1.8rem;font-weight:700}
.mc .l{color:#888;font-size:.75rem;margin-top:3px}
.badge-ap{background:#0d3b0d;color:#00ff7f;border:1px solid #00ff7f;
  padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600}
.badge-b{background:#0f3460;color:#5bc8ff;border:1px solid #5bc8ff;
  padding:2px 10px;border-radius:20px;font-size:11px}
.badge-c{background:#2a1a0a;color:#ffa500;border:1px solid #ffa500;
  padding:2px 10px;border-radius:20px;font-size:11px}
.pill-activo{background:#0d3b0d;color:#00ff7f;padding:3px 12px;border-radius:20px;font-size:12px}
.pill-vencido{background:#3b0d0d;color:#ff4444;padding:3px 12px;border-radius:20px;font-size:12px}
.pill-gratis{background:#1a1a0d;color:#ffd700;padding:3px 12px;border-radius:20px;font-size:12px}
.ft{text-align:center;color:#333;font-size:.7rem;margin-top:2rem;
  padding-top:1rem;border-top:1px solid #1a1a2e}
div[data-testid="stButton"] button{
  background:linear-gradient(135deg,#ffd700,#ff8c00)!important;
  color:#000!important;font-weight:700!important;border:none!important;
  border-radius:8px!important;width:100%}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# API-FOOTBALL: OBTENER FIXTURES
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def get_fixtures_dia(liga_id, fecha_str):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params  = {"league": liga_id, "season": TEMPORADA, "date": fecha_str}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        data = r.json()
        return data.get("response", [])
    except:
        return []

@st.cache_data(ttl=1800)
def get_fixtures_semana(liga_id, desde_str, hasta_str):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params  = {"league": liga_id, "season": TEMPORADA, "from": desde_str, "to": hasta_str}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        data = r.json()
        return data.get("response", [])
    except:
        return []

@st.cache_data(ttl=3600)
def get_stats_equipo_api(team_id):
    url = "https://v3.football.api-sports.io/teams/statistics"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params  = {"team": team_id, "season": TEMPORADA, "league": 39}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        data = r.json().get("response", {})
        gf = data.get("goals", {}).get("for", {}).get("average", {}).get("total")
        ga = data.get("goals", {}).get("against", {}).get("average", {}).get("total")
        return (float(gf) if gf else None, float(ga) if ga else None)
    except:
        return None, None

def fixture_a_partido(f):
    return {
        "dia":       f["fixture"]["date"][:10],
        "hora":      f["fixture"]["date"][11:16],
        "hora_sort": int(f["fixture"]["date"][11:13]) * 60 + int(f["fixture"]["date"][14:16]),
        "liga":      f["league"]["name"],
        "local":     f["teams"]["home"]["name"],
        "visitante": f["teams"]["away"]["name"],
        "team_id_local":  f["teams"]["home"]["id"],
        "team_id_visit":  f["teams"]["away"]["id"],
    }

# ═══════════════════════════════════════════════════════════
# MOTOR MATEMATICO
# ═══════════════════════════════════════════════════════════
PROM = {
    "premier":{"gm":1.54,"gc":1.11},"laliga":{"gm":1.62,"gc":1.08},
    "bundesliga":{"gm":1.82,"gc":1.28},"serie a":{"gm":1.48,"gc":1.07},
    "ligue":{"gm":1.51,"gc":1.07},"libertadores":{"gm":1.32,"gc":1.08},
    "sudamericana":{"gm":1.28,"gc":1.07},"eredivisie":{"gm":1.88,"gc":1.32},
    "mls":{"gm":1.45,"gc":1.20},"colombia":{"gm":1.25,"gc":1.10},
    "mundial":{"gm":1.35,"gc":1.05},"copa america":{"gm":1.28,"gc":1.08},
    "champions":{"gm":1.45,"gc":1.05},"europa":{"gm":1.42,"gc":1.08},
    "default":{"gm":1.40,"gc":1.15},
}

def gp(liga):
    l = liga.lower()
    for k in PROM:
        if k in l: return PROM[k]
    return PROM["default"]

def pp(lam, k):
    if lam <= 0: return 0
    return (math.exp(-lam) * (lam**k)) / math.factorial(min(k, 20))

def calcular(gml, gcl, gmv, gcv, liga, elo_l=None, elo_v=None):
    pr = gp(liga)
    if gml and gcv:   xl = round(gml * (gcv / pr["gc"]) * 1.08, 2)
    elif gml:         xl = round(gml * 1.08, 2)
    else:             xl = round(pr["gm"] * 1.08, 2)
    if gmv and gcl:   xv = round(gmv * (gcl / pr["gc"]), 2)
    elif gmv:         xv = round(gmv, 2)
    else:             xv = round(pr["gm"] * 0.78, 2)
    if elo_l and elo_v:
        f = 1 + (elo_l - elo_v) / 4000
        xl = round(xl * min(max(f, 0.75), 1.35), 2)
        xv = round(xv * min(max(1/f, 0.75), 1.35), 2)
    xl = max(0.15, xl); xv = max(0.10, xv); xt = round(xl + xv, 2)
    p1 = px = p2 = 0.0
    for i in range(9):
        for j in range(9):
            pij = pp(xl, i) * pp(xv, j)
            if i > j:    p1 += pij
            elif i == j: px += pij
            else:        p2 += pij
    p1 = round(p1*100); px = round(px*100); p2 = max(0, 100-p1-px)
    p0_=pp(xt,0);p1_=pp(xt,1);p2_=pp(xt,2);p3_=pp(xt,3)
    o15=round((1-p0_-p1_)*100); o25=round((1-p0_-p1_-p2_)*100); o35=round((1-p0_-p1_-p2_-p3_)*100)
    btts=round((1-pp(xl,0))*(1-pp(xv,0))*100)
    cmu=round(xt*2.1+4.5,1); sc2=2.5
    def poc(l):
        z=(l-cmu)/sc2; return max(5,min(95,round((1-0.5*(1+math.erf(z/math.sqrt(2))))*100)))
    c85=poc(8.5); c95=poc(9.5); c105=poc(10.5)
    tmu=round(3.5+(1-abs(p1-p2)/60)*1.8,1)
    g=None
    if p1>p2 and p1>px: mk="1"
    elif px>=p1 and px>=p2: mk="X"
    else: mk="2"
    if p1>p2 and p1>px and o25>=55: mk2="Gana Local + Over 1.5"
    elif p2>p1 and p2>px and o25>=55: mk2="Gana Visita + Over 1.5"
    elif o25>=65: mk2="Over 2.5 Goles"
    elif btts>=62: mk2="BTTS Ambos Marcan"
    elif c95>=65: mk2="Corners Over 9.5"
    else: mk2=f"1X2: {mk}"
    return {"xl":xl,"xv":xv,"xt":xt,"p1":p1,"px":px,"p2":p2,
            "o15":o15,"o25":o25,"o35":o35,"btts":btts,
            "cmu":cmu,"c85":c85,"c95":c95,"c105":c105,
            "tar":f"~{max(2,int(tmu)-1)}-{int(tmu)+1}",
            "corners":f"~{int(cmu)} (+9.5:{c95}% +8.5:{c85}%)",
            "mk":mk,"mk2":mk2}

def analizar_partidos(partidos, usar_api=True):
    resultados = []
    for p in partidos:
        gml = gcl = gmv = gcv = None
        fuente_l = fuente_v = "Prom.liga"
        if usar_api and p.get("team_id_local"):
            gml2, gcl2 = get_stats_equipo_api(p["team_id_local"])
            gmv2, gcv2 = get_stats_equipo_api(p["team_id_visit"])
            if gml2: gml=gml2; gcl=gcl2; fuente_l="API-Football"
            if gmv2: gmv=gmv2; gcv=gcv2; fuente_v="API-Football"
        calc = calcular(gml, gcl, gmv, gcv, p["liga"])
        p1,px,p2 = calc["p1"],calc["px"],calc["p2"]
        score = sum([
            (fuente_l!="Prom.liga")*25,
            (fuente_v!="Prom.liga")*25,
            25 if max(p1,p2)>=60 else (12 if max(p1,p2)>=50 else 0),
            20 if any(k in p["liga"].lower() for k in ["premier","liga","bundesliga","serie","ligue","libertadores","champions","mundial"]) else 0
        ])
        rango = "A+" if score>=75 else ("B" if score>=40 else "C")
        resultados.append({**p, **calc, "rango":rango,
                           "fuente_l":fuente_l, "fuente_v":fuente_v})
    return resultados

# ═══════════════════════════════════════════════════════════
# EXPORTAR EXCEL
# ═══════════════════════════════════════════════════════════
def generar_excel(resultados, titulo="Scorpion Elite"):
    def fill(c): return PatternFill("solid",fgColor=c)
    def brd():
        s=Side(border_style="thin",color="334466"); return Border(left=s,right=s,top=s,bottom=s)
    def al(h="center"): return Alignment(horizontal=h,vertical="center",wrap_text=True)
    def sc(cell,bg=None,fg="FFFFFF",bold=False,sz=9,h="center"):
        if bg: cell.fill=fill(bg)
        cell.font=Font(color=fg,bold=bold,size=sz,name="Arial")
        cell.alignment=al(h); cell.border=brd()
    def hrow(ws,row,vals,bg="1A1A2E",fg="FFD700",sz=9):
        for c,v in enumerate(vals,1): cl=ws.cell(row=row,column=c,value=v); sc(cl,bg=bg,fg=fg,bold=True,sz=sz)
    def title_row(ws,row,text,ncols,bg="1A1A2E",fg="FFD700",sz=13):
        ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=ncols)
        c=ws.cell(row=row,column=1,value=text); sc(c,bg=bg,fg=fg,bold=True,sz=sz)
    def set_w(ws,wl):
        for i,w in enumerate(wl,1): ws.column_dimensions[get_column_letter(i)].width=w

    wb = Workbook()
    COLS = ["HORA","LIGA","PARTIDO","1X2","P1%","PX%","P2%",
            "xG LOC","xG VIS","xG TOT","OVER 1.5","OVER 2.5","BTTS%",
            "CORNERS","C.9.5%","TARJETAS","MERCADO CLAVE","RANGO","FUENTE"]
    WW   = [9,22,32,7,7,7,7,8,8,8,9,9,8,18,9,12,26,7,18]

    for dia in list(dict.fromkeys(r["dia"] for r in resultados)):
        ws = wb.active if dia == list(dict.fromkeys(r["dia"] for r in resultados))[0] else wb.create_sheet()
        ws.title = str(dia)[:20]; ws.sheet_view.showGridLines=False; set_w(ws,WW)
        title_row(ws,1,f"🦂 {titulo} | {dia}",len(COLS),sz=13)
        ws.row_dimensions[1].height=24; hrow(ws,2,COLS,sz=8); ws.row_dimensions[2].height=36
        fila=3
        for p in [x for x in resultados if x["dia"]==dia]:
            r1x2=p["mk"]
            rv=[p["hora"],p["liga"][:20],f'{p["local"]} vs {p["visitante"]}',
                r1x2,f'{p["p1"]}%',f'{p["px"]}%',f'{p["p2"]}%',
                p["xl"],p["xv"],p["xt"],
                f'{p["o15"]}%',f'{p["o25"]}%',f'{p["btts"]}%',
                p["corners"][:18],f'{p["c95"]}%',p["tar"],
                p["mk2"],p["rango"],f'L:{p["fuente_l"][:8]} V:{p["fuente_v"][:8]}']
            bg="0D3B0D" if p["rango"]=="A+" else ("0F3460" if fila%2==0 else "16213E")
            for col,val in enumerate(rv,1):
                c=ws.cell(row=fila,column=col,value=val); fg="FFFFFF"
                if col==18: fg="FFD700" if p["rango"]=="A+" else ("00FF7F" if p["rango"]=="B" else "AAAAAA")
                elif col in (8,9,10): fg="00FFFF"
                elif col==19:
                    fg="00FF7F" if "API" in str(val) else "FFA500"
                sc(c,bg=bg,fg=fg,sz=9,bold=(p["rango"]=="A+" and col in (3,17,18)))
            ws.row_dimensions[fila].height=22; fila+=1

    # VALUE BETS sheet
    wsv=wb.create_sheet(title="VALUE BETS"); wsv.sheet_view.showGridLines=False
    vc=["HORA","PARTIDO","LIGA","PICK RECOMENDADO","P1%","PX%","P2%","xG TOT","OVER 2.5","BTTS","RANGO"]
    set_w(wsv,[9,32,20,28,7,7,7,8,9,8,7])
    title_row(wsv,1,"💰 PICKS RECOMENDADOS — Partidos con mayor ventaja estadistica",len(vc),bg="0A1A0A",fg="FFD700",sz=13)
    hrow(wsv,2,vc,bg="0A2E0A",fg="00FF7F",sz=8); fv=3
    top = sorted([r for r in resultados if r["rango"] in ("A+","B")],
                 key=lambda x: max(x["p1"],x["p2"]), reverse=True)[:15]
    for p in top:
        e=max(p["p1"],p["p2"]); bg="0D3B0D" if p["rango"]=="A+" else "0F3460"
        rv=[p["hora"],f'{p["local"]} vs {p["visitante"]}',p["liga"][:18],
            p["mk2"],f'{p["p1"]}%',f'{p["px"]}%',f'{p["p2"]}%',
            p["xt"],f'{p["o25"]}%',f'{p["btts"]}%',p["rango"]]
        for col,val in enumerate(rv,1):
            c=wsv.cell(row=fv,column=col,value=val); fg="FFFFFF"
            if col==4: fg="FFD700"
            elif col==11: fg="00FF7F" if p["rango"]=="A+" else "5bc8ff"
            sc(c,bg=bg,fg=fg,sz=9,bold=(col in (4,11)))
        wsv.row_dimensions[fv].height=20; fv+=1

    for ws_tab in wb.worksheets: ws_tab.freeze_panes="A3"
    buf=io.BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

# ═══════════════════════════════════════════════════════════
# LEER EXCEL/IMAGEN SUBIDA (plan gratis, max 5 partidos)
# ═══════════════════════════════════════════════════════════
def leer_excel_subido(file_bytes):
    import openpyxl
    wb_in=openpyxl.load_workbook(io.BytesIO(file_bytes),data_only=True); ws_in=wb_in.active
    partidos=[]; cur_liga=""
    TORN=["copa","liga","premier","bundesliga","serie","ligue","championship","apertura","clausura",
          "europa","champions","sudamericana","libertadores","mls","eredivisie","primera","superliga",
          "mundial","world cup","fifa","copa del mundo","nations","eurocopa","copa america"]
    def fix(s):
        s=str(s).strip().replace("\xa0","")
        for n in range(3,len(s)//2+1):
            if s[:n]==s[n:n*2]: return s[:n]
        return s
    for ri in range(1,ws_in.max_row+1):
        val=ws_in.cell(row=ri,column=1).value
        if val is None: continue
        if isinstance(val,dtime):
            try:
                l=fix(ws_in.cell(row=ri+1,column=1).value or "")
                v=fix(ws_in.cell(row=ri+2,column=1).value or "")
                if l not in ("","--") and v not in ("","--"):
                    partidos.append({"dia":str(date.today()),"hora":f"{val.hour:02d}:{val.minute:02d}",
                                     "hora_sort":val.hour*60+val.minute,
                                     "liga":cur_liga or "Sin Liga","local":l,"visitante":v,
                                     "team_id_local":None,"team_id_visit":None})
            except: pass
            continue
        vs=str(val).strip().replace("\xa0","")
        if any(k in vs.lower() for k in TORN) and len(vs)<80: cur_liga=vs
    return partidos

# ═══════════════════════════════════════════════════════════
# TELEGRAM
# ═══════════════════════════════════════════════════════════
def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return False
    try:
        url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url,json={"chat_id":TELEGRAM_CHAT_ID,"text":mensaje,"parse_mode":"HTML"},timeout=10)
        return True
    except: return False

def generar_picks_telegram(resultados):
    top3 = sorted([r for r in resultados if r["rango"]=="A+"],
                  key=lambda x: max(x["p1"],x["p2"]), reverse=True)[:3]
    if not top3:
        top3 = sorted(resultados, key=lambda x: max(x["p1"],x["p2"]), reverse=True)[:3]
    msg = "🦂 <b>SCORPION ELITE — PICKS DEL DIA</b>\n"
    msg += f"📅 {date.today().strftime('%d/%m/%Y')}\n\n"
    for i, p in enumerate(top3, 1):
        g = p["local"] if p["p1"] >= p["p2"] else p["visitante"]
        msg += f"<b>PICK {i}: {p['liga']}</b>\n"
        msg += f"⚽ {p['local']} vs {p['visitante']}\n"
        msg += f"🕐 {p['hora']} | 🎯 {p['mk2']}\n"
        msg += f"📊 xG: {p['xl']}-{p['xv']} | Over 2.5: {p['o25']}%\n"
        msg += f"🏆 Rango: {p['rango']}\n\n"
    msg += "⚠️ Solo informativo. Apuesta con responsabilidad."
    return msg

# ═══════════════════════════════════════════════════════════
# PANTALLAS
# ═══════════════════════════════════════════════════════════
def header():
    st.markdown('<div class="hdr"><h1>🦂 SCORPION ELITE</h1><p>Motor de Analisis Deportivo con Datos Reales · API-Football</p></div>', unsafe_allow_html=True)

def pantalla_login():
    header()
    st.markdown('<div class="lbox">', unsafe_allow_html=True)
    st.markdown("### 🔐 Acceder")
    cedula = st.text_input("Cedula / DNI", placeholder="Tu numero de cedula")
    if st.button("Entrar →"):
        if not cedula.strip():
            st.error("Ingresa tu cedula.")
        else:
            u = get_usuario(cedula.strip())
            if u is None:
                # Crear usuario gratis automaticamente
                st.session_state.usuarios_db[cedula.strip()] = {
                    "nombre": f"Usuario {cedula.strip()[:6]}",
                    "cedula": cedula.strip(),
                    "plan": "gratis",
                    "fecha_inicio": str(date.today()),
                    "dias": 9999,
                    "activo": True,
                    "password": "",
                }
                u = get_usuario(cedula.strip())
            ok, estado = verificar_acceso(u)
            if estado == "vencido":
                st.error("Tu acceso ha vencido. Contacta al administrador para renovar.")
            elif estado == "inactivo":
                st.error("Tu cuenta esta inactiva. Contacta al administrador.")
            else:
                st.session_state.cedula_actual = cedula.strip()
                st.session_state.usuario_actual = u
                st.session_state.logged_in = True
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    # Info de planes
    st.markdown("---")
    st.markdown("### 📋 Planes disponibles")
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown('<div class="plan-card plan-free"><h3>🆓 Gratis</h3><p>Sube Excel o imagen<br>Max 5 partidos/dia<br>Sin costo</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="plan-card plan-dia"><h3>📅 Plan Dia</h3><p>Selecciona liga<br>Partidos del dia<br>Descarga Excel</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="plan-card plan-semana"><h3>📆 Plan Semana</h3><p>Partidos de la semana<br>1 o mas ligas<br>Elige los dias</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="plan-card plan-mes"><h3>👑 Plan Mes</h3><p>Todo ilimitado<br>Todas las ligas<br>Multiple semanas</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 · Solo uso informativo · Las apuestas implican riesgo</div>', unsafe_allow_html=True)

def pantalla_admin():
    header()
    st.markdown("## ⚙️ Panel de Administrador")
    db = st.session_state.usuarios_db

    col1, col2 = st.columns([1,1])

    with col1:
        st.markdown("### ➕ Registrar / Actualizar Cliente")
        cedula_n = st.text_input("Cedula / DNI del cliente")
        nombre_n = st.text_input("Nombre del cliente")
        plan_n   = st.selectbox("Plan", ["gratis","dia","semana","mes"])
        dias_map = {"gratis": 9999, "dia": 1, "semana": 7, "mes": 30}
        dias_extra = st.number_input("Dias de acceso (personalizado)", min_value=1, max_value=365, value=dias_map[plan_n])
        fecha_ini = st.date_input("Fecha de inicio", value=date.today())
        if st.button("💾 Guardar cliente"):
            if cedula_n.strip():
                db[cedula_n.strip()] = {
                    "nombre":      nombre_n or f"Cliente {cedula_n[:6]}",
                    "cedula":      cedula_n.strip(),
                    "plan":        plan_n,
                    "fecha_inicio":str(fecha_ini),
                    "dias":        int(dias_extra),
                    "activo":      True,
                    "password":    "",
                }
                st.success(f"✅ Cliente {cedula_n} guardado con plan {plan_n} por {dias_extra} dias.")
            else:
                st.error("Ingresa la cedula.")

    with col2:
        st.markdown("### 📊 Clientes Activos")
        for ced, u in db.items():
            if u["plan"] == "admin": continue
            ok, estado = verificar_acceso(u)
            dr = dias_restantes(u) if u["plan"] != "gratis" else "∞"
            pill = f'<span class="pill-activo">Activo</span>' if ok else f'<span class="pill-vencido">Vencido</span>'
            if u["plan"] == "gratis": pill = f'<span class="pill-gratis">Gratis</span>'
            st.markdown(f"**{u['nombre']}** `{ced}` · {u['plan'].upper()} · {dr} dias restantes {pill}", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📡 Enviar Picks a Telegram")
    st.info("Primero analiza partidos en la pestaña principal, luego vuelve aqui a enviar los picks del dia.")
    liga_tg = st.selectbox("Liga para picks del dia", list(LIGAS.keys()))
    if st.button("🚀 Analizar y Enviar a Telegram"):
        hoy = str(date.today())
        with st.spinner("Obteniendo partidos..."):
            fixtures = get_fixtures_dia(LIGAS[liga_tg]["id"], hoy)
        if fixtures:
            partidos = [fixture_a_partido(f) for f in fixtures]
            resultados = analizar_partidos(partidos)
            msg = generar_picks_telegram(resultados)
            if enviar_telegram(msg):
                st.success("✅ Picks enviados a Telegram!")
                st.code(msg)
            else:
                st.warning("⚠️ No se pudo enviar. Verifica TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en Secrets.")
                st.code(msg)
        else:
            st.warning("No hay partidos hoy en esa liga.")

    if st.button("🚪 Cerrar sesion admin"):
        st.session_state.logged_in = False; st.rerun()

def pantalla_gratis(usuario):
    header()
    dr = f'<span class="pill-gratis">Plan Gratuito</span>'
    st.markdown(f"👋 Hola **{usuario['nombre']}** {dr} · Max 5 partidos/dia", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📁 Sube tu Excel o imagen con los partidos")
    st.info("Plan gratuito: se analizan los primeros 5 partidos. Actualiza a un plan de pago para acceso completo.")
    uploaded = st.file_uploader("Sube tu archivo", type=["xlsx","xls","png","jpg","jpeg"])
    if uploaded:
        fb = uploaded.read()
        if uploaded.name.endswith((".xlsx",".xls")):
            try:
                partidos = leer_excel_subido(fb)[:5]
            except Exception as e:
                st.error(f"Error leyendo Excel: {e}"); return
        else:
            st.warning("Lectura de imagen en desarrollo. Por ahora usa Excel.")
            return
        if not partidos:
            st.warning("No se encontraron partidos."); return
        st.success(f"✅ {len(partidos)} partidos encontrados (max 5 en plan gratis)")
        if st.button(f"🦂 Analizar {len(partidos)} partidos"):
            with st.spinner("Analizando..."):
                resultados = analizar_partidos(partidos, usar_api=False)
            st.success("✅ Listo")
            for r in resultados:
                g = r["local"] if r["p1"]>=r["p2"] else r["visitante"]
                badge = f'<span class="badge-{r["rango"].lower().replace("+","ap")}">{r["rango"]}</span>'
                st.markdown(f"{badge} **{r['local']} vs {r['visitante']}** · 1X2: {r['mk']} · xG: {r['xl']}-{r['xv']} · Over2.5: {r['o25']}% · Pick: {r['mk2']}", unsafe_allow_html=True)
            excel = generar_excel(resultados, "Scorpion Elite — Plan Gratis")
            st.download_button("⬇️ Descargar Excel", data=excel,
                file_name=f"ScorpionElite_gratis_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("🚪 Cerrar sesion"): st.session_state.logged_in=False; st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 · Solo uso informativo</div>', unsafe_allow_html=True)

def pantalla_pago(usuario, plan):
    header()
    dr = dias_restantes(usuario)
    plan_label = {"dia":"📅 Plan Dia","semana":"📆 Plan Semana","mes":"👑 Plan Mes"}.get(plan, plan)
    pill_color = {"dia":"pill-activo","semana":"pill-activo","mes":"pill-gratis"}.get(plan,"pill-activo")
    st.markdown(f'👋 Hola **{usuario["nombre"]}** <span class="{pill_color}">{plan_label}</span> · **{dr} dias restantes**', unsafe_allow_html=True)
    st.markdown("---")

    tab1, tab2 = st.tabs(["🏟️ Analizar por Liga", "📁 Subir Excel/Imagen"])

    with tab1:
        st.markdown("### Selecciona liga y periodo")
        c1, c2 = st.columns([2,1])
        with c1:
            if plan == "mes":
                ligas_sel = st.multiselect("Selecciona una o mas ligas", list(LIGAS.keys()), default=[list(LIGAS.keys())[0]])
            else:
                liga_sel = st.selectbox("Selecciona una liga", list(LIGAS.keys()))
                ligas_sel = [liga_sel]
        with c2:
            if plan == "dia":
                fecha_sel = st.date_input("Fecha", value=date.today())
                modo = "dia"
            elif plan == "semana":
                modo = st.radio("Periodo", ["Dia especifico", "Semana completa", "Dias especificos"])
                if modo == "Dia especifico":
                    fecha_sel = st.date_input("Fecha", value=date.today())
                    modo = "dia"
                elif modo == "Semana completa":
                    # Lunes de esta semana
                    hoy = date.today()
                    lunes = hoy - timedelta(days=hoy.weekday())
                    fecha_desde = st.date_input("Desde", value=lunes)
                    fecha_hasta = st.date_input("Hasta", value=lunes+timedelta(days=6))
                    modo = "semana"
                else:
                    dias_check = st.multiselect("Selecciona dias", ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"])
                    modo = "dias"
            else:  # mes
                modo = st.radio("Periodo", ["Hoy","Esta semana","Semana personalizada"])
                if modo == "Hoy":
                    fecha_sel = date.today(); modo="dia"
                elif modo == "Esta semana":
                    hoy=date.today(); lunes=hoy-timedelta(days=hoy.weekday())
                    fecha_desde=lunes; fecha_hasta=lunes+timedelta(days=6); modo="semana"
                else:
                    fecha_desde = st.date_input("Desde", value=date.today())
                    fecha_hasta = st.date_input("Hasta", value=date.today()+timedelta(days=6))
                    modo="semana"

        if st.button("🦂 Obtener y Analizar Partidos"):
            todos_partidos = []
            with st.spinner("Obteniendo partidos de API-Football..."):
                for liga_nombre in ligas_sel:
                    liga_id = LIGAS[liga_nombre]["id"]
                    if modo == "dia":
                        fixtures = get_fixtures_dia(liga_id, str(fecha_sel))
                    elif modo == "semana":
                        fixtures = get_fixtures_semana(liga_id, str(fecha_desde), str(fecha_hasta))
                    elif modo == "dias":
                        fixtures = []
                        hoy=date.today(); lunes=hoy-timedelta(days=hoy.weekday())
                        map_dias={"Lunes":0,"Martes":1,"Miercoles":2,"Jueves":3,"Viernes":4,"Sabado":5,"Domingo":6}
                        for d in dias_check:
                            fd=lunes+timedelta(days=map_dias.get(d,0))
                            fixtures+=get_fixtures_dia(liga_id, str(fd))
                    todos_partidos += [fixture_a_partido(f) for f in fixtures]
                    time.sleep(0.3)

            if not todos_partidos:
                st.warning("No se encontraron partidos para ese periodo y liga. Puede que la liga este en receso o la temporada no haya comenzado.")
                return

            st.info(f"🔍 Analizando {len(todos_partidos)} partidos con datos reales...")
            with st.spinner("Analizando..."):
                resultados = analizar_partidos(todos_partidos)

            # Metricas
            ap=sum(1 for r in resultados if r["rango"]=="A+")
            b=sum(1 for r in resultados if r["rango"]=="B")
            api_ok=sum(1 for r in resultados if "API" in r["fuente_l"])
            c1,c2,c3,c4=st.columns(4)
            with c1: st.markdown(f'<div class="mc"><div class="v">{len(resultados)}</div><div class="l">Partidos</div></div>',unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="mc"><div class="v">{ap}</div><div class="l">Rango A+</div></div>',unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="mc"><div class="v">{b}</div><div class="l">Rango B</div></div>',unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="mc"><div class="v">{api_ok}</div><div class="l">Datos reales</div></div>',unsafe_allow_html=True)

            # Top picks
            st.markdown("### 🏆 Top Picks")
            top = sorted([r for r in resultados if r["rango"] in ("A+","B")],
                         key=lambda x: max(x["p1"],x["p2"]),reverse=True)[:8]
            for r in top:
                badge_cls = "badge-ap" if r["rango"]=="A+" else "badge-b"
                st.markdown(f'<span class="{badge_cls}">{r["rango"]}</span> **{r["local"]} vs {r["visitante"]}** ({r["liga"][:20]}) · {r["hora"]} · Pick: **{r["mk2"]}** · xG: {r["xl"]}-{r["xv"]} · Over2.5: {r["o25"]}%', unsafe_allow_html=True)

            # Descargar
            st.markdown("### 📥 Descargar")
            excel = generar_excel(resultados, f"Scorpion Elite — {plan_label}")
            fecha_label = str(fecha_sel) if modo=="dia" else f"{fecha_desde}_al_{fecha_hasta}"
            st.download_button("⬇️ Descargar Excel completo", data=excel,
                file_name=f"ScorpionElite_{fecha_label}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        st.markdown("### 📁 Sube tu propio Excel o imagen")
        uploaded = st.file_uploader("Sube tu archivo", type=["xlsx","xls","png","jpg","jpeg"])
        if uploaded:
            fb = uploaded.read()
            if uploaded.name.endswith((".xlsx",".xls")):
                try: partidos = leer_excel_subido(fb)
                except Exception as e: st.error(f"Error: {e}"); return
            else:
                st.warning("Lectura de imagen en desarrollo. Usa Excel por ahora."); return
            if not partidos: st.warning("No se encontraron partidos."); return
            st.success(f"✅ {len(partidos)} partidos")
            if st.button("🦂 Analizar archivo"):
                with st.spinner("Analizando..."):
                    resultados = analizar_partidos(partidos)
                excel = generar_excel(resultados, "Scorpion Elite — Archivo Propio")
                st.download_button("⬇️ Descargar Excel", data=excel,
                    file_name=f"ScorpionElite_custom_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.button("🚪 Cerrar sesion"): st.session_state.logged_in=False; st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 · Solo uso informativo</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# ROUTER PRINCIPAL
# ═══════════════════════════════════════════════════════════
init_db()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    pantalla_login()
else:
    usuario = st.session_state.get("usuario_actual", {})
    ok, plan = verificar_acceso(usuario)
    if plan == "admin":
        pantalla_admin()
    elif plan == "gratis":
        pantalla_gratis(usuario)
    elif plan in ("dia","semana","mes"):
        pantalla_pago(usuario, plan)
    else:
        st.error("Acceso vencido o inactivo. Contacta al administrador.")
        if st.button("Volver al inicio"): st.session_state.logged_in=False; st.rerun()
