import streamlit as st
import os, json, time, math, re, warnings, requests, io, base64
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

# Temporada correcta por liga
TEMPORADA_LIGA = {
    1:   2026,  # Mundial FIFA 2026
    2:   2024,  # Champions League
    3:   2024,  # Europa League
    848: 2024,  # Conference League
    9:   2024,  # Copa America
    13:  2024,  # Libertadores
    11:  2024,  # Sudamericana
    39:  2024,  # Premier League
    140: 2024,  # La Liga
    78:  2024,  # Bundesliga
    135: 2024,  # Serie A
    61:  2024,  # Ligue 1
    88:  2024,  # Eredivisie
    94:  2024,  # Primeira Liga
    253: 2025,  # MLS
    262: 2025,  # Liga MX
    239: 2025,  # Liga BetPlay Colombia
    128: 2024,  # Argentina
    71:  2025,  # Brasileirao
    179: 2024,  # Scottish Premier
    203: 2024,  # Super Lig
    307: 2024,  # Saudi Pro League
}

def get_temporada(liga_id):
    return TEMPORADA_LIGA.get(int(liga_id), 2024)

LIGAS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League":     {"id": 39},
    "🇪🇸 La Liga":              {"id": 140},
    "🇩🇪 Bundesliga":           {"id": 78},
    "🇮🇹 Serie A":              {"id": 135},
    "🇫🇷 Ligue 1":              {"id": 61},
    "🇳🇱 Eredivisie":           {"id": 88},
    "🇵🇹 Primeira Liga":        {"id": 94},
    "🌍 Champions League":      {"id": 2},
    "🌍 Europa League":         {"id": 3},
    "🌍 Conference League":     {"id": 848},
    "🌎 Libertadores":          {"id": 13},
    "🌎 Sudamericana":          {"id": 11},
    "🌎 Copa America":          {"id": 9},
    "🌍 Mundial FIFA 2026":     {"id": 1},
    "🇺🇸 MLS":                  {"id": 253},
    "🇲🇽 Liga MX":              {"id": 262},
    "🇨🇴 Liga BetPlay":         {"id": 239},
    "🇦🇷 Primera Division":     {"id": 128},
    "🇧🇷 Brasileirao":          {"id": 71},
    "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Scottish Premier":   {"id": 179},
    "🇹🇷 Super Lig":            {"id": 203},
    "🇸🇦 Saudi Pro League":     {"id": 307},
}

# ═══════════════════════════════════════════════════════════
# BASE DE DATOS EN SESSION STATE
# ═══════════════════════════════════════════════════════════
def init_db():
    if "usuarios_db" not in st.session_state:
        st.session_state.usuarios_db = {
            "admin": {
                "nombre": "Administrador",
                "cedula": "admin",
                "plan": "admin",
                "fecha_inicio": str(date.today()),
                "dias": 36500,
                "activo": True,
                "password": ADMIN_PASSWORD,
            },
            "owner": {
                "nombre": "Propietario (Prueba)",
                "cedula": "owner",
                "plan": "mes",
                "fecha_inicio": str(date.today()),
                "dias": 36500,
                "activo": True,
                "password": "",
            },
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
    if usuario["plan"] == "gratis": return True, "gratis"
    inicio = date.fromisoformat(usuario["fecha_inicio"])
    vence  = inicio + timedelta(days=usuario["dias"])
    if date.today() > vence:
        return False, "vencido"
    return True, usuario["plan"]

def dias_restantes(usuario):
    if usuario["plan"] in ("admin","gratis"): return "ilimitado"
    inicio = date.fromisoformat(usuario["fecha_inicio"])
    vence  = inicio + timedelta(days=usuario["dias"])
    return max(0, (vence - date.today()).days)

# ═══════════════════════════════════════════════════════════
# CSS Y PAGE CONFIG
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
.plan-card{border-radius:12px;padding:1.2rem;margin-bottom:.8rem;border:1px solid #334466}
.plan-free{background:#111122;border-color:#444}
.plan-dia{background:#0d1a0d;border-color:#00aa44}
.plan-semana{background:#0d0d1a;border-color:#4488ff}
.plan-mes{background:#1a0d00;border-color:#ffd700}
.plan-card h3{margin:0 0 4px;font-size:1rem}
.plan-card p{margin:0;font-size:.8rem;color:#aaa}
.mc{background:#12122a;border:1px solid #334466;border-radius:10px;padding:1rem;text-align:center}
.mc .v{color:#ffd700;font-size:1.8rem;font-weight:700}
.mc .l{color:#888;font-size:.75rem;margin-top:3px}
.badge-ap{background:#0d3b0d;color:#00ff7f;border:1px solid #00ff7f;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600}
.badge-b{background:#0f3460;color:#5bc8ff;border:1px solid #5bc8ff;padding:2px 10px;border-radius:20px;font-size:11px}
.badge-c{background:#2a1a0a;color:#ffa500;border:1px solid #ffa500;padding:2px 10px;border-radius:20px;font-size:11px}
.pill-activo{background:#0d3b0d;color:#00ff7f;padding:3px 12px;border-radius:20px;font-size:12px}
.pill-vencido{background:#3b0d0d;color:#ff4444;padding:3px 12px;border-radius:20px;font-size:12px}
.pill-gratis{background:#1a1a0d;color:#ffd700;padding:3px 12px;border-radius:20px;font-size:12px}
.ft{text-align:center;color:#333;font-size:.7rem;margin-top:2rem;padding-top:1rem;border-top:1px solid #1a1a2e}
div[data-testid="stButton"] button{background:linear-gradient(135deg,#ffd700,#ff8c00)!important;
  color:#000!important;font-weight:700!important;border:none!important;border-radius:8px!important;width:100%}
</style>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# API-FOOTBALL: FIXTURES
# ═══════════════════════════════════════════════════════════
@st.cache_data(ttl=1800)
def get_fixtures_dia(liga_id, fecha_str):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params  = {"league": liga_id, "season": get_temporada(liga_id), "date": fecha_str}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        return r.json().get("response", [])
    except:
        return []

@st.cache_data(ttl=1800)
def get_fixtures_semana(liga_id, desde_str, hasta_str):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params  = {"league": liga_id, "season": get_temporada(liga_id), "from": desde_str, "to": hasta_str}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        return r.json().get("response", [])
    except:
        return []

@st.cache_data(ttl=3600)
def get_stats_equipo_api(team_id, liga_id):
    url = "https://v3.football.api-sports.io/teams/statistics"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params  = {"team": team_id, "season": get_temporada(liga_id), "league": liga_id}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=12)
        data = r.json().get("response", {})
        gf = data.get("goals", {}).get("for", {}).get("average", {}).get("total")
        ga = data.get("goals", {}).get("against", {}).get("average", {}).get("total")
        return (float(gf) if gf else None, float(ga) if ga else None)
    except:
        return None, None

def fixture_a_partido(f):
    fecha_utc = f["fixture"]["date"]
    return {
        "dia":           fecha_utc[:10],
        "hora":          fecha_utc[11:16],
        "hora_sort":     int(fecha_utc[11:13])*60 + int(fecha_utc[14:16]),
        "liga":          f["league"]["name"],
        "liga_id":       f["league"]["id"],
        "local":         f["teams"]["home"]["name"],
        "visitante":     f["teams"]["away"]["name"],
        "team_id_local": f["teams"]["home"]["id"],
        "team_id_visit": f["teams"]["away"]["id"],
    }

# ═══════════════════════════════════════════════════════════
# LEER IMAGEN CON IA (Claude API)
# ═══════════════════════════════════════════════════════════
def leer_imagen_partidos(image_bytes, media_type="image/jpeg"):
    try:
        img_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {"type": "base64", "media_type": media_type, "data": img_b64}
                    },
                    {
                        "type": "text",
                        "text": """Analiza esta imagen de fixtures deportivos y extrae los partidos.
Devuelve SOLO un JSON valido con esta estructura exacta, sin texto adicional ni markdown:
{"partidos": [{"hora": "19:00", "liga": "Premier League", "local": "Arsenal", "visitante": "Chelsea"}]}
Reglas:
- Si no hay hora visible usa "00:00"
- Incluye solo partidos de futbol claramente legibles
- El nombre de la liga tal como aparece en la imagen
- No inventes partidos que no esten en la imagen"""
                    }
                ]
            }]
        }
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        result = r.json()
        text = result.get("content", [{}])[0].get("text", "")
        text = re.sub(r"```json|```", "", text).strip()
        data = json.loads(text)
        partidos_raw = data.get("partidos", [])
        partidos = []
        for p in partidos_raw:
            hora = str(p.get("hora", "00:00"))
            try:
                h, m = hora.split(":")
                hora_sort = int(h)*60 + int(m)
            except:
                hora_sort = 0
            if p.get("local") and p.get("visitante"):
                partidos.append({
                    "dia":           str(date.today()),
                    "hora":          hora,
                    "hora_sort":     hora_sort,
                    "liga":          p.get("liga", "Sin Liga"),
                    "liga_id":       0,
                    "local":         p.get("local", ""),
                    "visitante":     p.get("visitante", ""),
                    "team_id_local": None,
                    "team_id_visit": None,
                })
        return partidos
    except Exception as e:
        st.error(f"Error leyendo imagen: {e}")
        return []

# ═══════════════════════════════════════════════════════════
# LEER EXCEL SUBIDO
# ═══════════════════════════════════════════════════════════
def leer_excel_subido(file_bytes):
    import openpyxl
    wb_in = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws_in = wb_in.active
    partidos = []; cur_liga = ""
    TORN = ["copa","liga","premier","bundesliga","serie","ligue","championship","apertura","clausura",
            "europa","champions","sudamericana","libertadores","mls","eredivisie","primera","superliga",
            "mundial","world cup","fifa","copa del mundo","nations","eurocopa","copa america"]
    def fix(s):
        s = str(s).strip().replace("\xa0", "")
        for n in range(3, len(s)//2+1):
            if s[:n] == s[n:n*2]: return s[:n]
        return s
    for ri in range(1, ws_in.max_row+1):
        val = ws_in.cell(row=ri, column=1).value
        if val is None: continue
        if isinstance(val, dtime):
            try:
                l = fix(ws_in.cell(row=ri+1, column=1).value or "")
                v = fix(ws_in.cell(row=ri+2, column=1).value or "")
                if l not in ("","--") and v not in ("","--"):
                    partidos.append({
                        "dia": str(date.today()), "hora": f"{val.hour:02d}:{val.minute:02d}",
                        "hora_sort": val.hour*60+val.minute, "liga": cur_liga or "Sin Liga",
                        "liga_id": 0, "local": l, "visitante": v,
                        "team_id_local": None, "team_id_visit": None,
                    })
            except: pass
            continue
        vs = str(val).strip().replace("\xa0","")
        if any(k in vs.lower() for k in TORN) and len(vs) < 80:
            cur_liga = vs
    return partidos

# ═══════════════════════════════════════════════════════════
# MOTOR MATEMATICO
# ═══════════════════════════════════════════════════════════
PROM = {
    "premier":{"gm":1.54,"gc":1.11},"laliga":{"gm":1.62,"gc":1.08},
    "bundesliga":{"gm":1.82,"gc":1.28},"serie a":{"gm":1.48,"gc":1.07},
    "ligue":{"gm":1.51,"gc":1.07},"libertadores":{"gm":1.32,"gc":1.08},
    "sudamericana":{"gm":1.28,"gc":1.07},"eredivisie":{"gm":1.88,"gc":1.32},
    "mls":{"gm":1.45,"gc":1.20},"colombia":{"gm":1.25,"gc":1.10},
    "mundial":{"gm":1.35,"gc":1.05},"world cup":{"gm":1.35,"gc":1.05},
    "copa america":{"gm":1.28,"gc":1.08},"champions":{"gm":1.45,"gc":1.05},
    "europa":{"gm":1.42,"gc":1.08},"default":{"gm":1.40,"gc":1.15},
}

def gp(liga):
    l = liga.lower()
    for k in PROM:
        if k in l: return PROM[k]
    return PROM["default"]

def pp(lam, k):
    if lam <= 0: return 0
    return (math.exp(-lam) * (lam**k)) / math.factorial(min(k, 20))

def calcular(gml, gcl, gmv, gcv, liga):
    pr = gp(liga)
    if gml and gcv:   xl = round(gml * (gcv / pr["gc"]) * 1.08, 2)
    elif gml:         xl = round(gml * 1.08, 2)
    else:             xl = round(pr["gm"] * 1.08, 2)
    if gmv and gcl:   xv = round(gmv * (gcl / pr["gc"]), 2)
    elif gmv:         xv = round(gmv, 2)
    else:             xv = round(pr["gm"] * 0.78, 2)
    xl = max(0.15, xl); xv = max(0.10, xv); xt = round(xl+xv, 2)
    p1 = px = p2 = 0.0
    for i in range(9):
        for j in range(9):
            pij = pp(xl,i)*pp(xv,j)
            if i>j: p1+=pij
            elif i==j: px+=pij
            else: p2+=pij
    p1=round(p1*100); px=round(px*100); p2=max(0,100-p1-px)
    p0_=pp(xt,0);p1_=pp(xt,1);p2_=pp(xt,2);p3_=pp(xt,3)
    o15=round((1-p0_-p1_)*100); o25=round((1-p0_-p1_-p2_)*100); o35=round((1-p0_-p1_-p2_-p3_)*100)
    btts=round((1-pp(xl,0))*(1-pp(xv,0))*100)
    cmu=round(xt*2.1+4.5,1); sc2=2.5
    def poc(l):
        z=(l-cmu)/sc2; return max(5,min(95,round((1-0.5*(1+math.erf(z/math.sqrt(2))))*100)))
    c85=poc(8.5); c95=poc(9.5); c105=poc(10.5)
    tmu=round(3.5+(1-abs(p1-p2)/60)*1.8,1)
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
            "o15":o15,"o25":o25,"o35":o35,"btts":btts,"cmu":cmu,
            "c85":c85,"c95":c95,"c105":c105,
            "tar":f"~{max(2,int(tmu)-1)}-{int(tmu)+1}",
            "corners":f"~{int(cmu)} (+9.5:{c95}% +8.5:{c85}%)",
            "mk":mk,"mk2":mk2}

def analizar_partidos(partidos, usar_api=True):
    resultados = []
    for p in partidos:
        gml=gcl=gmv=gcv=None
        fuente_l=fuente_v="Prom.liga"
        if usar_api and p.get("team_id_local") and p.get("liga_id"):
            gml2,gcl2=get_stats_equipo_api(p["team_id_local"],p["liga_id"])
            gmv2,gcv2=get_stats_equipo_api(p["team_id_visit"],p["liga_id"])
            if gml2: gml=gml2;gcl=gcl2;fuente_l="API-Football"
            if gmv2: gmv=gmv2;gcv=gcv2;fuente_v="API-Football"
        calc=calcular(gml,gcl,gmv,gcv,p["liga"])
        p1,px,p2=calc["p1"],calc["px"],calc["p2"]
        score=sum([
            (fuente_l!="Prom.liga")*25,(fuente_v!="Prom.liga")*25,
            25 if max(p1,p2)>=60 else (12 if max(p1,p2)>=50 else 0),
            20 if any(k in p["liga"].lower() for k in ["premier","liga","bundesliga","serie","ligue","libertadores","champions","mundial","world cup"]) else 0
        ])
        rango="A+" if score>=75 else ("B" if score>=40 else "C")
        resultados.append({**p,**calc,"rango":rango,"fuente_l":fuente_l,"fuente_v":fuente_v})
    return resultados

# ═══════════════════════════════════════════════════════════
# GENERAR EXCEL
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
    wb=Workbook()
    COLS=["HORA","LIGA","PARTIDO","1X2","P1%","PX%","P2%","xG LOC","xG VIS","xG TOT",
          "OVER 1.5","OVER 2.5","BTTS%","CORNERS","C.9.5%","TARJETAS","MERCADO CLAVE","RANGO","FUENTE"]
    WW=[9,22,32,7,7,7,7,8,8,8,9,9,8,18,9,12,26,7,18]
    first=True
    for dia in list(dict.fromkeys(r["dia"] for r in resultados)):
        ws=wb.active if first else wb.create_sheet()
        first=False; ws.title=str(dia)[:20]; ws.sheet_view.showGridLines=False; set_w(ws,WW)
        title_row(ws,1,f"🦂 {titulo} | {dia}",len(COLS),sz=13)
        ws.row_dimensions[1].height=24; hrow(ws,2,COLS,sz=8); ws.row_dimensions[2].height=36; fila=3
        for p in [x for x in resultados if x["dia"]==dia]:
            rv=[p["hora"],p["liga"][:20],f'{p["local"]} vs {p["visitante"]}',
                p["mk"],f'{p["p1"]}%',f'{p["px"]}%',f'{p["p2"]}%',
                p["xl"],p["xv"],p["xt"],f'{p["o15"]}%',f'{p["o25"]}%',f'{p["btts"]}%',
                p["corners"][:18],f'{p["c95"]}%',p["tar"],p["mk2"],p["rango"],
                f'L:{p["fuente_l"][:8]} V:{p["fuente_v"][:8]}']
            bg="0D3B0D" if p["rango"]=="A+" else ("0F3460" if fila%2==0 else "16213E")
            for col,val in enumerate(rv,1):
                c=ws.cell(row=fila,column=col,value=val); fg="FFFFFF"
                if col==18: fg="FFD700" if p["rango"]=="A+" else ("00FF7F" if p["rango"]=="B" else "AAAAAA")
                elif col in (8,9,10): fg="00FFFF"
                elif col==19: fg="00FF7F" if "API" in str(val) else "FFA500"
                sc(c,bg=bg,fg=fg,sz=9,bold=(p["rango"]=="A+" and col in (3,17,18)))
            ws.row_dimensions[fila].height=22; fila+=1
    wsv=wb.create_sheet(title="TOP PICKS"); wsv.sheet_view.showGridLines=False
    vc=["HORA","PARTIDO","LIGA","PICK","P1%","PX%","P2%","xG TOT","OVER 2.5","BTTS","RANGO"]
    set_w(wsv,[9,32,20,28,7,7,7,8,9,8,7])
    title_row(wsv,1,"💰 TOP PICKS — Mayor ventaja estadistica",len(vc),bg="0A1A0A",fg="FFD700",sz=13)
    hrow(wsv,2,vc,bg="0A2E0A",fg="00FF7F",sz=8); fv=3
    top=sorted([r for r in resultados if r["rango"] in ("A+","B")],key=lambda x:max(x["p1"],x["p2"]),reverse=True)[:15]
    for p in top:
        bg="0D3B0D" if p["rango"]=="A+" else "0F3460"
        rv=[p["hora"],f'{p["local"]} vs {p["visitante"]}',p["liga"][:18],p["mk2"],
            f'{p["p1"]}%',f'{p["px"]}%',f'{p["p2"]}%',p["xt"],f'{p["o25"]}%',f'{p["btts"]}%',p["rango"]]
        for col,val in enumerate(rv,1):
            c=wsv.cell(row=fv,column=col,value=val); fg="FFFFFF"
            if col==4: fg="FFD700"
            elif col==11: fg="00FF7F" if p["rango"]=="A+" else "5bc8ff"
            sc(c,bg=bg,fg=fg,sz=9,bold=(col in (4,11)))
        wsv.row_dimensions[fv].height=20; fv+=1
    for ws_tab in wb.worksheets: ws_tab.freeze_panes="A3"
    buf=io.BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

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
    top3=sorted([r for r in resultados if r["rango"]=="A+"],key=lambda x:max(x["p1"],x["p2"]),reverse=True)[:3]
    if not top3: top3=sorted(resultados,key=lambda x:max(x["p1"],x["p2"]),reverse=True)[:3]
    msg=f"🦂 <b>SCORPION ELITE — PICKS DEL DIA</b>\n📅 {date.today().strftime('%d/%m/%Y')}\n\n"
    for i,p in enumerate(top3,1):
        msg+=f"<b>PICK {i}: {p['liga']}</b>\n"
        msg+=f"⚽ {p['local']} vs {p['visitante']}\n"
        msg+=f"🕐 {p['hora']} | 🎯 {p['mk2']}\n"
        msg+=f"📊 xG: {p['xl']}-{p['xv']} | Over 2.5: {p['o25']}%\n"
        msg+=f"🏆 Rango: {p['rango']}\n\n"
    msg+="⚠️ Solo informativo. Apuesta con responsabilidad."
    return msg

# ═══════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════
def header():
    st.markdown('<div class="hdr"><h1>🦂 SCORPION ELITE</h1><p>Motor de Analisis Deportivo con Datos Reales</p></div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PANTALLA LOGIN
# ═══════════════════════════════════════════════════════════
def pantalla_login():
    header()
    st.markdown('<div class="lbox">',unsafe_allow_html=True)
    st.markdown("### 🔐 Acceder")
    cedula=st.text_input("Cedula / DNI",placeholder="Tu numero de cedula o 'admin'")
    es_admin=cedula.strip().lower()=="admin"
    password=""
    if es_admin:
        password=st.text_input("Contrasena admin",type="password",placeholder="........")
    if st.button("Entrar →"):
        if not cedula.strip():
            st.error("Ingresa tu cedula.")
        elif es_admin:
            if password.strip()==ADMIN_PASSWORD:
                u=get_usuario("admin")
                st.session_state.cedula_actual="admin"
                st.session_state.usuario_actual=u
                st.session_state.logged_in=True
                st.rerun()
            else:
                st.error("Contrasena de administrador incorrecta.")
        else:
            u=get_usuario(cedula.strip())
            if u is None:
                st.session_state.usuarios_db[cedula.strip()]={
                    "nombre":f"Usuario {cedula.strip()[:6]}","cedula":cedula.strip(),
                    "plan":"gratis","fecha_inicio":str(date.today()),
                    "dias":36500,"activo":True,"password":"",
                }
                u=get_usuario(cedula.strip())
            ok,estado=verificar_acceso(u)
            if estado=="vencido":
                st.error("Tu acceso ha vencido. Contacta al administrador para renovar.")
            elif estado=="inactivo":
                st.error("Tu cuenta esta inactiva. Contacta al administrador.")
            else:
                st.session_state.cedula_actual=cedula.strip()
                st.session_state.usuario_actual=u
                st.session_state.logged_in=True
                st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📋 Planes")
    c1,c2,c3,c4=st.columns(4)
    with c1: st.markdown('<div class="plan-card plan-free"><h3>🆓 Gratis</h3><p>Sube Excel o imagen<br>Max 5 partidos/dia</p></div>',unsafe_allow_html=True)
    with c2: st.markdown('<div class="plan-card plan-dia"><h3>📅 Plan Dia</h3><p>Partidos del dia<br>Liga a eleccion</p></div>',unsafe_allow_html=True)
    with c3: st.markdown('<div class="plan-card plan-semana"><h3>📆 Plan Semana</h3><p>Semana completa<br>Dias especificos</p></div>',unsafe_allow_html=True)
    with c4: st.markdown('<div class="plan-card plan-mes"><h3>👑 Plan Mes</h3><p>Todo ilimitado<br>Todas las ligas</p></div>',unsafe_allow_html=True)
    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 · Solo uso informativo</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PANTALLA ADMIN
# ═══════════════════════════════════════════════════════════
def pantalla_admin():
    header()
    st.markdown("## ⚙️ Panel de Administrador")
    db=st.session_state.usuarios_db
    col1,col2=st.columns([1,1])
    with col1:
        st.markdown("### ➕ Registrar / Actualizar Cliente")
        cedula_n=st.text_input("Cedula / DNI del cliente")
        nombre_n=st.text_input("Nombre del cliente")
        plan_n=st.selectbox("Plan",["gratis","dia","semana","mes"])
        dias_map={"gratis":30,"dia":1,"semana":7,"mes":30}
        dias_extra=st.number_input("Dias de acceso",min_value=1,max_value=3650,value=int(dias_map[plan_n]))
        fecha_ini=st.date_input("Fecha de inicio",value=date.today())
        if st.button("💾 Guardar cliente"):
            if cedula_n.strip():
                db[cedula_n.strip()]={
                    "nombre":nombre_n or f"Cliente {cedula_n[:6]}",
                    "cedula":cedula_n.strip(),"plan":plan_n,
                    "fecha_inicio":str(fecha_ini),"dias":int(dias_extra),
                    "activo":True,"password":"",
                }
                st.success(f"✅ {cedula_n} guardado — Plan {plan_n} por {dias_extra} dias.")
            else:
                st.error("Ingresa la cedula.")
    with col2:
        st.markdown("### 👥 Clientes")
        for ced,u in db.items():
            if u["plan"]=="admin": continue
            ok,estado=verificar_acceso(u)
            dr=dias_restantes(u)
            if u["plan"]=="gratis": pill='<span class="pill-gratis">Gratis</span>'
            elif ok: pill='<span class="pill-activo">Activo</span>'
            else: pill='<span class="pill-vencido">Vencido</span>'
            st.markdown(f"**{u['nombre']}** `{ced}` · {u['plan'].upper()} · {dr} dias {pill}",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📡 Picks a Telegram")
    liga_tg=st.selectbox("Liga para picks",list(LIGAS.keys()))
    if st.button("🚀 Analizar y Enviar a Telegram"):
        hoy=str(date.today())
        with st.spinner("Obteniendo partidos..."):
            fixtures=get_fixtures_dia(LIGAS[liga_tg]["id"],hoy)
        if fixtures:
            partidos=[fixture_a_partido(f) for f in fixtures]
            resultados=analizar_partidos(partidos)
            msg=generar_picks_telegram(resultados)
            if enviar_telegram(msg): st.success("✅ Enviado a Telegram!")
            else: st.warning("⚠️ Configura TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en Secrets.")
            st.code(msg)
        else:
            st.warning("No hay partidos hoy en esa liga.")
    if st.button("🚪 Cerrar sesion"): st.session_state.logged_in=False; st.rerun()

# ═══════════════════════════════════════════════════════════
# WIDGET SUBIR ARCHIVO (Excel o Imagen)
# ═══════════════════════════════════════════════════════════
def widget_subir_archivo(max_partidos=None):
    uploaded=st.file_uploader("Sube tu archivo",type=["xlsx","xls","png","jpg","jpeg","webp"])
    if not uploaded: return None
    fb=uploaded.read()
    nombre=uploaded.name.lower()
    if nombre.endswith((".xlsx",".xls")):
        try:
            partidos=leer_excel_subido(fb)
        except Exception as e:
            st.error(f"Error leyendo Excel: {e}"); return None
    else:
        # Detectar media type
        if nombre.endswith(".png"): mt="image/png"
        elif nombre.endswith(".webp"): mt="image/webp"
        else: mt="image/jpeg"
        with st.spinner("Leyendo imagen con IA... esto toma unos segundos"):
            partidos=leer_imagen_partidos(fb, mt)
    if not partidos:
        st.warning("No se encontraron partidos. Verifica el archivo."); return None
    if max_partidos:
        partidos=partidos[:max_partidos]
    st.success(f"✅ {len(partidos)} partidos encontrados")
    return partidos

# ═══════════════════════════════════════════════════════════
# PANTALLA GRATIS
# ═══════════════════════════════════════════════════════════
def pantalla_gratis(usuario):
    header()
    st.markdown(f'👋 Hola **{usuario["nombre"]}** <span class="pill-gratis">Plan Gratuito</span> · Max 5 partidos/dia',unsafe_allow_html=True)
    st.info("Plan gratuito: se analizan los primeros 5 partidos. Actualiza tu plan para acceso completo.")
    st.markdown("### 📁 Sube tu Excel o captura de pantalla")
    partidos=widget_subir_archivo(max_partidos=5)
    if partidos:
        if st.button(f"🦂 Analizar {len(partidos)} partidos"):
            with st.spinner("Analizando..."): resultados=analizar_partidos(partidos,usar_api=False)
            for r in resultados:
                bc="badge-ap" if r["rango"]=="A+" else ("badge-b" if r["rango"]=="B" else "badge-c")
                st.markdown(f'<span class="{bc}">{r["rango"]}</span> **{r["local"]} vs {r["visitante"]}** · {r["liga"]} · Pick: **{r["mk2"]}** · xG: {r["xl"]}-{r["xv"]} · Over2.5: {r["o25"]}%',unsafe_allow_html=True)
            excel=generar_excel(resultados,"Scorpion Elite — Plan Gratis")
            st.download_button("⬇️ Descargar Excel",data=excel,
                file_name=f"ScorpionElite_gratis_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if st.button("🚪 Cerrar sesion"): st.session_state.logged_in=False; st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 · Solo uso informativo</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# PANTALLA PAGO
# ═══════════════════════════════════════════════════════════
def pantalla_pago(usuario, plan):
    header()
    dr=dias_restantes(usuario)
    plan_label={"dia":"📅 Plan Dia","semana":"📆 Plan Semana","mes":"👑 Plan Mes"}.get(plan,plan)
    st.markdown(f'👋 Hola **{usuario["nombre"]}** <span class="pill-activo">{plan_label}</span> · **{dr} dias restantes**',unsafe_allow_html=True)
    st.markdown("---")
    tab1,tab2=st.tabs(["🏟️ Analizar por Liga","📁 Subir Excel o Imagen"])

    with tab1:
        st.markdown("### Selecciona liga y periodo")
        c1,c2=st.columns([2,1])
        with c1:
            if plan=="mes":
                ligas_sel=st.multiselect("Selecciona una o mas ligas",list(LIGAS.keys()),default=[list(LIGAS.keys())[0]])
            else:
                liga_sel=st.selectbox("Selecciona una liga",list(LIGAS.keys()))
                ligas_sel=[liga_sel]
        with c2:
            if plan=="dia":
                fecha_sel=st.date_input("Fecha",value=date.today())
                modo="dia"
            else:
                opciones=["Hoy","Dia especifico","Esta semana","Semana personalizada"]
                if plan=="semana": opciones.append("Dias especificos")
                modo_label=st.radio("Periodo",opciones)
                if modo_label=="Hoy": fecha_sel=date.today(); modo="dia"
                elif modo_label=="Dia especifico": fecha_sel=st.date_input("Fecha",value=date.today()); modo="dia"
                elif modo_label=="Esta semana":
                    hoy=date.today(); lunes=hoy-timedelta(days=hoy.weekday())
                    fecha_desde=lunes; fecha_hasta=lunes+timedelta(days=6); modo="semana"
                elif modo_label=="Semana personalizada":
                    fecha_desde=st.date_input("Desde",value=date.today())
                    fecha_hasta=st.date_input("Hasta",value=date.today()+timedelta(days=6)); modo="semana"
                elif modo_label=="Dias especificos":
                    dias_nombres=st.multiselect("Dias",["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"])
                    modo="dias"

        if st.button("🦂 Obtener y Analizar Partidos"):
            todos=[]
            with st.spinner("Obteniendo partidos de API-Football..."):
                for liga_nombre in ligas_sel:
                    lid=LIGAS[liga_nombre]["id"]
                    if modo=="dia":
                        fx=get_fixtures_dia(lid,str(fecha_sel))
                    elif modo=="semana":
                        fx=get_fixtures_semana(lid,str(fecha_desde),str(fecha_hasta))
                    elif modo=="dias":
                        fx=[]; hoy=date.today(); lunes=hoy-timedelta(days=hoy.weekday())
                        map_d={"Lunes":0,"Martes":1,"Miercoles":2,"Jueves":3,"Viernes":4,"Sabado":5,"Domingo":6}
                        for d in dias_nombres:
                            fd=lunes+timedelta(days=map_d.get(d,0))
                            fx+=get_fixtures_dia(lid,str(fd))
                    todos+=[fixture_a_partido(f) for f in fx]
                    time.sleep(0.3)
            if not todos:
                st.warning("No se encontraron partidos. La liga puede estar en receso o la temporada no ha comenzado.")
            else:
                with st.spinner(f"Analizando {len(todos)} partidos..."): resultados=analizar_partidos(todos)
                ap=sum(1 for r in resultados if r["rango"]=="A+")
                b=sum(1 for r in resultados if r["rango"]=="B")
                api_ok=sum(1 for r in resultados if "API" in r["fuente_l"])
                c1,c2,c3,c4=st.columns(4)
                with c1: st.markdown(f'<div class="mc"><div class="v">{len(resultados)}</div><div class="l">Partidos</div></div>',unsafe_allow_html=True)
                with c2: st.markdown(f'<div class="mc"><div class="v">{ap}</div><div class="l">Rango A+</div></div>',unsafe_allow_html=True)
                with c3: st.markdown(f'<div class="mc"><div class="v">{b}</div><div class="l">Rango B</div></div>',unsafe_allow_html=True)
                with c4: st.markdown(f'<div class="mc"><div class="v">{api_ok}</div><div class="l">Datos reales</div></div>',unsafe_allow_html=True)
                st.markdown("### 🏆 Top Picks")
                top=sorted([r for r in resultados if r["rango"] in ("A+","B")],key=lambda x:max(x["p1"],x["p2"]),reverse=True)[:8]
                for r in top:
                    bc="badge-ap" if r["rango"]=="A+" else "badge-b"
                    st.markdown(f'<span class="{bc}">{r["rango"]}</span> **{r["local"]} vs {r["visitante"]}** ({r["liga"][:18]}) · {r["hora"]} · **{r["mk2"]}** · xG:{r["xl"]}-{r["xv"]} · O2.5:{r["o25"]}%',unsafe_allow_html=True)
                excel=generar_excel(resultados,f"Scorpion Elite — {plan_label}")
                fecha_label=str(fecha_sel) if modo=="dia" else f"{fecha_desde}_al_{fecha_hasta}"
                st.download_button("⬇️ Descargar Excel completo",data=excel,
                    file_name=f"ScorpionElite_{fecha_label}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tab2:
        st.markdown("### 📁 Sube tu propio Excel o captura de pantalla")
        st.info("Puedes subir una captura de Sofascore, FlashScore o cualquier app de fixtures. La IA lee los partidos automaticamente.")
        partidos=widget_subir_archivo()
        if partidos:
            if st.button("🦂 Analizar archivo"):
                with st.spinner("Analizando..."): resultados=analizar_partidos(partidos)
                excel=generar_excel(resultados,"Scorpion Elite — Archivo Propio")
                st.download_button("⬇️ Descargar Excel",data=excel,
                    file_name=f"ScorpionElite_custom_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    if st.button("🚪 Cerrar sesion"): st.session_state.logged_in=False; st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 · Solo uso informativo</div>',unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# ROUTER
# ═══════════════════════════════════════════════════════════
init_db()
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False

if not st.session_state.logged_in:
    pantalla_login()
else:
    usuario=st.session_state.get("usuario_actual",{})
    ok,plan=verificar_acceso(usuario)
    if plan=="admin": pantalla_admin()
    elif plan=="gratis": pantalla_gratis(usuario)
    elif plan in ("dia","semana","mes"): pantalla_pago(usuario,plan)
    else:
        st.error("Acceso vencido o inactivo. Contacta al administrador.")
        if st.button("Volver al inicio"): st.session_state.logged_in=False; st.rerun()
