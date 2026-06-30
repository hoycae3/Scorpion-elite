import streamlit as st
import os, json, time, math, re, warnings, requests
from bs4 import BeautifulSoup
from datetime import datetime, time as dtime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import io
warnings.filterwarnings("ignore")

# ── USUARIOS — agrega/quita clientes aqui, luego commit en GitHub ──────────
USUARIOS = {
    "admin":    {"password": "scorpion2025", "nombre": "Administrador"},
    "cliente1": {"password": "clave001",     "nombre": "Cliente 1"},
    "cliente2": {"password": "clave002",     "nombre": "Cliente 2"},
}

ODDS_API_KEY      = os.getenv("ODDS_API_KEY", "")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "")

st.set_page_config(page_title="Scorpion Elite", page_icon="🦂", layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:#0a0a14}
.hdr{background:linear-gradient(135deg,#0d1b2a,#1a1a2e,#16213e);border:1px solid #ffd700;
  border-radius:16px;padding:2rem;text-align:center;margin-bottom:2rem}
.hdr h1{color:#ffd700;font-size:2.4rem;margin:0;letter-spacing:2px}
.hdr p{color:#aaa;margin:.4rem 0 0}
.lbox{background:#16213e;border:1px solid #ffd700;border-radius:16px;padding:2.5rem;max-width:420px;margin:2rem auto}
.mc{background:#16213e;border:1px solid #334466;border-radius:12px;padding:1.2rem;text-align:center;margin-bottom:.5rem}
.mc .v{color:#ffd700;font-size:2rem;font-weight:700}
.mc .l{color:#888;font-size:.8rem;margin-top:4px}
.sb{background:#1a1a2e;border-left:3px solid #ffd700;border-radius:8px;padding:1rem 1.2rem;margin-bottom:.8rem}
.sb .n{color:#ffd700;font-weight:700}
.sb .t{color:#ccc;font-size:.85rem;margin-top:4px}
.ft{text-align:center;color:#444;font-size:.75rem;margin-top:3rem;padding-top:1rem;border-top:1px solid #222}
div[data-testid="stButton"] button{background:linear-gradient(135deg,#ffd700,#ff8c00)!important;
  color:#000!important;font-weight:700!important;border:none!important;border-radius:8px!important;width:100%}
</style>""", unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.usuario   = ""
    st.session_state.nombre    = ""

def pantalla_login():
    st.markdown('<div class="hdr"><h1>🦂 SCORPION ELITE</h1><p>Motor de Analisis Deportivo con Datos Reales</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="lbox">', unsafe_allow_html=True)
    st.markdown("### Iniciar Sesion")
    usuario  = st.text_input("Usuario", placeholder="tu_usuario")
    password = st.text_input("Contrasena", type="password", placeholder="........")
    if st.button("Entrar"):
        u = USUARIOS.get(usuario.strip())
        if u and u["password"] == password.strip():
            st.session_state.logged_in = True
            st.session_state.usuario   = usuario
            st.session_state.nombre    = u["nombre"]
            st.rerun()
        else:
            st.error("Usuario o contrasena incorrectos.")
    st.markdown('</div>', unsafe_allow_html=True)

# ── FUENTES DE DATOS ────────────────────────────────────────────────────────
SH = requests.Session()
SH.headers.update({"User-Agent": "Mozilla/5.0", "Accept": "application/json,text/html,*/*"})

SPORTS_MAP = {
    "premier": "soccer_epl", "laliga": "soccer_spain_la_liga", "la liga": "soccer_spain_la_liga",
    "bundesliga": "soccer_germany_bundesliga", "serie a": "soccer_italy_serie_a",
    "ligue": "soccer_france_ligue_one", "eredivisie": "soccer_netherlands_eredivisie",
    "champions": "soccer_uefa_champs_league", "europa": "soccer_uefa_europa_league",
    "libertadores": "soccer_conmebol_libertadores", "sudamericana": "soccer_conmebol_sudamericana",
    "mls": "soccer_usa_mls", "colombia": "soccer_colombia_primera_a",
    "argentina": "soccer_argentina_primera_division", "mexico": "soccer_mexico_ligamx",
    "mundial": "soccer_fifa_world_cup", "world cup": "soccer_fifa_world_cup",
    "fifa world cup": "soccer_fifa_world_cup", "copa del mundo": "soccer_fifa_world_cup",
    "eurocopa": "soccer_uefa_european_championship", "euro": "soccer_uefa_european_championship",
    "nations league": "soccer_uefa_nations_league", "copa america": "soccer_conmebol_copa_america",
}

UNDERSTAT_L = {
    "premier": "EPL", "laliga": "La_liga", "la liga": "La_liga",
    "bundesliga": "Bundesliga", "serie a": "Serie_A", "ligue": "Ligue_1",
}

FDORG_C = {
    "premier": "PL", "laliga": "PD", "la liga": "PD", "bundesliga": "BL1",
    "serie a": "SA", "ligue": "FL1", "eredivisie": "DED", "champions": "CL",
}

PROM = {
    "premier":      {"gm": 1.54, "gc": 1.11},
    "laliga":       {"gm": 1.62, "gc": 1.08},
    "bundesliga":   {"gm": 1.82, "gc": 1.28},
    "serie a":      {"gm": 1.48, "gc": 1.07},
    "ligue":        {"gm": 1.51, "gc": 1.07},
    "libertadores": {"gm": 1.32, "gc": 1.08},
    "sudamericana": {"gm": 1.28, "gc": 1.07},
    "eredivisie":   {"gm": 1.88, "gc": 1.32},
    "mls":          {"gm": 1.45, "gc": 1.20},
    "colombia":     {"gm": 1.25, "gc": 1.10},
    "mundial":      {"gm": 1.35, "gc": 1.05},
    "world cup":    {"gm": 1.35, "gc": 1.05},
    "copa del mundo": {"gm": 1.35, "gc": 1.05},
    "copa america": {"gm": 1.28, "gc": 1.08},
    "eurocopa":     {"gm": 1.42, "gc": 1.10},
    "euro":         {"gm": 1.42, "gc": 1.10},
    "nations":      {"gm": 1.38, "gc": 1.08},
    "default":      {"gm": 1.40, "gc": 1.15},
}

_fdc = {}

def gp(liga):
    l = liga.lower()
    for k in PROM:
        if k in l: return PROM[k]
    return PROM["default"]

def es_torneo_fifa(liga):
    kw = ["mundial", "world cup", "fifa", "copa del mundo", "nations league",
          "eurocopa", "euro 20", "copa america", "gold cup", "african cup", "afcon"]
    return any(k in liga.lower() for k in kw)

def es_seleccion(nombre):
    sel = ["argentina", "brasil", "brazil", "francia", "france", "alemania", "germany",
           "espana", "spain", "portugal", "inglaterra", "england", "italia", "italy",
           "belgica", "belgium", "croacia", "croatia", "holanda", "netherlands", "uruguay",
           "colombia", "chile", "mexico", "estados unidos", "usa", "japon", "japan",
           "marruecos", "morocco", "senegal", "australia", "corea", "korea", "suiza",
           "switzerland", "dinamarca", "denmark", "polonia", "poland", "austria",
           "turquia", "turkey", "rumania", "romania", "eslovaquia", "slovakia",
           "serbia", "albania", "chequia", "czech", "ecuador", "peru", "bolivia",
           "venezuela", "panama", "canada", "ghana", "nigeria", "camerun", "cameroon",
           "sudafrica", "south africa", "arabia saudita", "saudi", "iran", "qatar",
           "nueva zelanda", "new zealand", "gales", "wales", "escocia", "scotland",
           "hungria", "hungary", "georgia", "eslovenia", "slovenia"]
    n = nombre.lower()
    return any(s in n for s in sel)

def buscar_cuotas(local, visitante, liga):
    if not ODDS_API_KEY: return None
    sk = next((v for k, v in SPORTS_MAP.items() if k in liga.lower()), None)
    if not sk: return None
    try:
        r = SH.get(f"https://api.the-odds-api.com/v4/sports/{sk}/odds/?regions=eu&markets=h2h&apiKey={ODDS_API_KEY}", timeout=10)
        if r.status_code != 200: return None
        for game in r.json():
            ht = game.get("home_team", "").lower()
            at = game.get("away_team", "").lower()
            if not (any(p in ht for p in local.lower().split()[:2]) and
                    any(p in at for p in visitante.lower().split()[:2])): continue
            for bm in game.get("bookmakers", []):
                cl = ce = cv = None
                for o in (bm.get("markets") or [{}])[0].get("outcomes", []):
                    n = o["name"].lower()
                    if n == game["home_team"].lower(): cl = o["price"]
                    elif n == game["away_team"].lower(): cv = o["price"]
                    elif o["name"] == "Draw": ce = o["price"]
                if all([cl, ce, cv]):
                    return {"cuota_local": round(cl, 2), "cuota_empate": round(ce, 2),
                            "cuota_visita": round(cv, 2), "fuente": bm.get("title", "")}
    except: pass
    return None

def buscar_understat(equipo, liga, temporada=2024):
    lu = next((v for k, v in UNDERSTAT_L.items() if k in liga.lower()), None)
    if not lu: return None, None, None, None
    try:
        r = SH.get(f"https://understat.com/league/{lu}/{temporada}", timeout=12)
        for sc2 in BeautifulSoup(r.text, "lxml").find_all("script"):
            if "teamsData" in str(sc2):
                m = re.search(r"JSON\.parse\(.(.*?)\.replace", str(sc2))
                if m:
                    data = json.loads(m.group(1).encode().decode("unicode_escape"))
                    el = equipo.lower()
                    for tn, stats in data.items():
                        if any(p in tn.lower() for p in el.split()[:2]):
                            h = stats.get("history", [])[-10:]
                            if h:
                                return (round(sum(x.get("xG", 0) for x in h) / len(h), 2),
                                        round(sum(x.get("xGA", 0) for x in h) / len(h), 2),
                                        round(sum(x.get("scored", 0) for x in h) / len(h), 2),
                                        round(sum(x.get("missed", 0) for x in h) / len(h), 2))
    except: pass
    return None, None, None, None

def buscar_fdorg(nombre, liga):
    if not FOOTBALL_DATA_KEY: return None
    comp = next((v for k, v in FDORG_C.items() if k in liga.lower()), None)
    if not comp: return None
    if comp not in _fdc:
        try:
            r = requests.get(f"https://api.football-data.org/v4/competitions/{comp}/standings",
                             headers={"X-Auth-Token": FOOTBALL_DATA_KEY}, timeout=10)
            t = {}
            for x in r.json()["standings"][0]["table"]:
                j = x["playedGames"] or 1
                t[x["team"]["name"]] = {"gf_pg": round(x["goalsFor"] / j, 2), "gc_pg": round(x["goalsAgainst"] / j, 2)}
            _fdc[comp] = t
        except: _fdc[comp] = {}
    nl = nombre.lower()
    return next((v for k, v in _fdc.get(comp, {}).items() if any(p in k.lower() for p in nl.split()[:2])), None)

def buscar_tsdb(nombre):
    try:
        r = SH.get(f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={requests.utils.quote(nombre)}", timeout=8)
        d = r.json()
        if d and d.get("teams"): return d["teams"][0]
    except: pass
    return None

def stats_tsdb(tid):
    try:
        r = SH.get(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={tid}", timeout=8)
        d = r.json()
        if d and d.get("results"):
            raw = d["results"][-10:]
            gml = []; gcl = []
            for x in raw:
                try:
                    sh = int(x.get("intHomeScore") or 0)
                    sa = int(x.get("intAwayScore") or 0)
                    if str(x.get("idHomeTeam", "")) == str(tid): gml.append(sh); gcl.append(sa)
                    else: gml.append(sa); gcl.append(sh)
                except: pass
            if gml: return round(sum(gml) / len(gml), 2), round(sum(gcl) / len(gcl), 2)
    except: pass
    return None, None

def buscar_elo(equipo):
    try:
        r = SH.get(f"http://api.clubelo.com/{equipo.replace(' ', '-').replace('.', '')}", timeout=8)
        if r.status_code == 200 and len(r.text) > 50:
            ul = r.text.strip().split("\n")[-1].split(",")
            if len(ul) >= 4: return float(ul[3])
    except: pass
    return None

def obtener_stats(nombre, liga):
    s = {"goles_marcados": None, "goles_concedidos": None, "xg": None, "xga": None,
         "elo": None, "fuente": "Sin datos", "encontrado": False}
    # Para selecciones y torneos FIFA: saltar Understat (no las cubre) e ir directo a TheSportsDB
    torneo_fifa = es_torneo_fifa(liga)
    seleccion   = es_seleccion(nombre)
    if not torneo_fifa and not seleccion:
        xg, xga, gm, gc = buscar_understat(nombre, liga)
        if xg is not None:
            s.update({"xg": xg, "xga": xga, "goles_marcados": gm, "goles_concedidos": gc,
                      "fuente": "Understat", "encontrado": True})
        time.sleep(0.2)
        fd = buscar_fdorg(nombre, liga)
        if fd:
            if s["goles_marcados"] is None:
                s.update({"goles_marcados": fd["gf_pg"], "goles_concedidos": fd["gc_pg"],
                          "fuente": "FD.org", "encontrado": True})
            else: s["fuente"] += " +FD"
    # TheSportsDB: funciona para selecciones nacionales y clubes
    if not s["encontrado"]:
        td = buscar_tsdb(nombre)
        if td:
            gm2, gc2 = stats_tsdb(td.get("idTeam"))
            if gm2:
                tipo = "Seleccion" if seleccion else "TheSportsDB"
                s.update({"goles_marcados": gm2, "goles_concedidos": gc2,
                          "fuente": tipo, "encontrado": True})
        time.sleep(0.3)
    elo = buscar_elo(nombre)
    if elo: s["elo"] = elo
    return s

# ── MOTOR MATEMATICO ────────────────────────────────────────────────────────
def pp(lam, k):
    if lam <= 0: return 0
    return (math.exp(-lam) * (lam ** k)) / math.factorial(min(k, 20))

def calcular(stl, stv, liga, cuotas=None):
    pr = gp(liga)
    gml = stl.get("goles_marcados"); gcl = stl.get("goles_concedidos")
    xgl = stl.get("xg");            xgal = stl.get("xga")
    gmv = stv.get("goles_marcados"); gcv = stv.get("goles_concedidos")
    xgv = stv.get("xg");            xgav = stv.get("xga")
    if xgl and xgav:     xl = round((xgl + xgav) / 2 * 1.08, 2)
    elif gml and gcv:    xl = round(gml * (gcv / pr["gc"]) * 1.08, 2)
    elif gml:            xl = round(gml * 1.08, 2)
    else:                xl = round(pr["gm"] * 1.08, 2)
    if xgv and xgal:     xv = round((xgv + xgal) / 2, 2)
    elif gmv and gcl:    xv = round(gmv * (gcl / pr["gc"]), 2)
    elif gmv:            xv = round(gmv, 2)
    else:                xv = round(pr["gm"] * 0.78, 2)
    el2 = stl.get("elo"); ev2 = stv.get("elo")
    if el2 and ev2:
        f = 1 + (el2 - ev2) / 4000
        xl = round(xl * min(max(f, 0.75), 1.35), 2)
        xv = round(xv * min(max(1 / f, 0.75), 1.35), 2)
    xl = max(0.15, xl); xv = max(0.10, xv); xt = round(xl + xv, 2)
    p1 = px = p2 = 0.0
    for i in range(9):
        for j in range(9):
            pij = pp(xl, i) * pp(xv, j)
            if i > j: p1 += pij
            elif i == j: px += pij
            else: p2 += pij
    p1 = round(p1 * 100); px = round(px * 100); p2 = max(0, 100 - p1 - px)
    p0_ = pp(xt, 0); p1_ = pp(xt, 1); p2_ = pp(xt, 2); p3_ = pp(xt, 3)
    o15 = round((1 - p0_ - p1_) * 100)
    o25 = round((1 - p0_ - p1_ - p2_) * 100)
    o35 = round((1 - p0_ - p1_ - p2_ - p3_) * 100)
    btts = round((1 - pp(xl, 0)) * (1 - pp(xv, 0)) * 100)
    cmu = round(xt * 2.1 + 4.5, 1); sc2 = 2.5
    def poc(l):
        z = (l - cmu) / sc2
        return max(5, min(95, round((1 - 0.5 * (1 + math.erf(z / math.sqrt(2)))) * 100)))
    c75 = poc(7.5); c85 = poc(8.5); c95 = poc(9.5); c105 = poc(10.5)
    tmu = round(3.5 + (1 - abs(p1 - p2) / 60) * 1.8, 1)
    el_ = ee = ev_ = None
    if cuotas:
        el_ = round((p1 / 100 * cuotas["cuota_local"]  - 1) * 100, 1)
        ee  = round((px / 100 * cuotas["cuota_empate"] - 1) * 100, 1)
        ev_ = round((p2 / 100 * cuotas["cuota_visita"] - 1) * 100, 1)
    return {"xg_local": xl, "xg_visit": xv, "xg_total": xt, "p1": p1, "px": px, "p2": p2,
            "over15": o15, "over25": o25, "over35": o35, "btts": btts, "cmu": cmu,
            "c75": c75, "c85": c85, "c95": c95, "c105": c105,
            "corners_str": f"~{int(cmu)} (+9.5:{c95}% | +8.5:{c85}%)",
            "tar_str": f"~{max(2, int(tmu)-1)}-{int(tmu)+1} tarjetas",
            "edge_local": el_, "edge_empate": ee, "edge_visita": ev_}

def value_bets(calc, local, visitante, cuotas=None):
    p1, px, p2 = calc["p1"], calc["px"], calc["p2"]
    g = local if p1 >= p2 else visitante
    cg = cuotas["cuota_local"] if cuotas and p1 >= p2 else (cuotas["cuota_visita"] if cuotas else None)
    mds = [(f"{g} Gana", max(p1, p2), cg),
           ("Empate", px, cuotas["cuota_empate"] if cuotas else None),
           ("Over 1.5", calc["over15"], 1.25), ("Over 2.5", calc["over25"], 1.85),
           ("Over 3.5", calc["over35"], 3.20), ("BTTS Si", calc["btts"], 1.80),
           ("BTTS No", 100 - calc["btts"], 1.98), ("Corners +7.5", calc["c75"], 1.40),
           ("Corners +8.5", calc["c85"], 1.58), ("Corners +9.5", calc["c95"], 1.88),
           ("Corners +10.5", calc["c105"], 2.35)]
    vbs = []
    for nm, prob, cuota in mds:
        if prob <= 0 or cuota is None: continue
        e = round((prob / 100 * cuota - 1) * 100, 1)
        cj = round(100 / max(prob, 1), 2)
        pb = prob / 100; b = cuota - 1
        kl = round(max(0, (pb * b - (1 - pb)) / b if b > 0 else 0) * 0.25 * 100, 1)
        con = cuotas is not None and nm in (f"{g} Gana", "Empate")
        label = "VALOR ALTO" if e >= 5 else ("VALOR" if e >= 2 else ("neutro" if e >= 0 else "negativo"))
        vbs.append({"mercado": nm, "prob": prob, "cuota_justa": cj, "cuota_ref": cuota,
                    "edge": e, "kelly": kl, "label": label, "con_odds": con})
    return sorted(vbs, key=lambda x: x["edge"], reverse=True)

def leer_partidos(file_bytes):
    wb_in = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    ws_in = wb_in.active
    partidos = []; cur_dia = "Partidos"; cur_liga = ""
    TORN = ["copa", "liga", "premier", "bundesliga", "serie", "ligue", "championship",
            "apertura", "clausura", "europa", "champions", "sudamericana", "libertadores",
            "mls", "eredivisie", "primera", "superliga", "mundial", "world cup", "fifa",
            "copa del mundo", "nations league", "eurocopa", "euro 2", "copa america",
            "gold cup", "african", "afcon", "olimpic", "olimpico"]
    def fix(s):
        s = str(s).strip().replace("\xa0", "")
        for n in range(3, len(s) // 2 + 1):
            if s[:n] == s[n:n * 2]: return s[:n]
        return s
    for ri in range(1, ws_in.max_row + 1):
        val = ws_in.cell(row=ri, column=1).value
        if val is None: continue
        if isinstance(val, dtime):
            try:
                l = fix(ws_in.cell(row=ri + 1, column=1).value or "")
                v = fix(ws_in.cell(row=ri + 2, column=1).value or "")
                if l not in ("", "--") and v not in ("", "--"):
                    partidos.append({"dia": cur_dia, "hora": f"{val.hour:02d}:{val.minute:02d}",
                                     "hora_sort": val.hour * 60 + val.minute,
                                     "liga": cur_liga or "Sin Liga", "local": l, "visitante": v})
            except: pass
            continue
        vs = str(val).strip().replace("\xa0", "")
        if vs in ["Lunes", "Martes", "Miercoles", "Miércoles", "Jueves", "Viernes", "Sabado", "Sábado", "Domingo"]:
            cur_dia = vs; continue
        if any(k in vs.lower() for k in TORN) and len(vs) < 80:
            cur_liga = vs; continue
    return partidos

# ── EXPORTAR EXCEL ──────────────────────────────────────────────────────────
def generar_excel(resultados):
    def fill(c): return PatternFill("solid", fgColor=c)
    def brd():
        s = Side(border_style="thin", color="334466")
        return Border(left=s, right=s, top=s, bottom=s)
    def al(h="center"): return Alignment(horizontal=h, vertical="center", wrap_text=True)
    def sc(cell, bg=None, fg="FFFFFF", bold=False, sz=9, h="center"):
        if bg: cell.fill = fill(bg)
        cell.font = Font(color=fg, bold=bold, size=sz, name="Arial")
        cell.alignment = al(h); cell.border = brd()
    def hrow(ws, row, vals, bg="1A1A2E", fg="FFD700", sz=9):
        for c, v in enumerate(vals, 1):
            cl = ws.cell(row=row, column=c, value=v); sc(cl, bg=bg, fg=fg, bold=True, sz=sz)
    def title(ws, row, text, ncols, bg="1A1A2E", fg="FFD700", sz=13):
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
        c = ws.cell(row=row, column=1, value=text); sc(c, bg=bg, fg=fg, bold=True, sz=sz)
    def set_w(ws, wl):
        for i, w in enumerate(wl, 1): ws.column_dimensions[get_column_letter(i)].width = w

    wb = openpyxl.Workbook()
    ws1 = wb.active; ws1.title = "LEER ANTES"
    ws1.sheet_view.showGridLines = False; set_w(ws1, [30, 85])
    title(ws1, 1, "SCORPION ELITE -- GLOSARIO Y DESCARGO", 2, sz=14)
    glos = [("TERMINO", "DEFINICION"),
            ("Rango A+", "Datos reales de AMBOS equipos. Maxima fiabilidad."),
            ("Rango B",  "Datos reales de al menos UN equipo."),
            ("Rango C",  "Solo promedios de liga o torneo."),
            ("Fuentes",  "Understat / FD.org / TheSportsDB / ClubElo"),
            ("xG",       "Expected Goals: ataque real x debilidad real del rival."),
            ("BTTS",     "Ambos Marcan. Calculado con Poisson por equipo."),
            ("Corners",  "Calculados desde xG total real del partido."),
            ("Edge%",    "(Prob x Cuota - 1) x 100. Positivo = ventaja estadistica."),
            ("Kelly%",   "Fraccion optima del bankroll (Kelly/4)."),
            ("", ""), ("DESCARGO", ""),
            ("", "Solo informativo. Las apuestas implican riesgo real de perdida."),
            ("", f"Scorpion Elite | {datetime.now().strftime('%d/%m/%Y %H:%M')}")]
    for i, (term, defi) in enumerate(glos, 3):
        bg = "0D4F2E" if term in ("TERMINO", "DESCARGO") else ("0F3460" if i % 2 == 0 else "16213E")
        c1 = ws1.cell(row=i, column=1, value=term)
        sc(c1, bg=bg, fg="FFD700" if term.strip() else "888888", bold=bool(term.strip()), h="left")
        c2 = ws1.cell(row=i, column=2, value=defi); sc(c2, bg=bg, fg="FFFFFF", h="left")

    COLS = ["HORA", "LIGA", "PARTIDO", "1X2", "P1%", "PX%", "P2%", "xG LOC", "xG VIS", "xG TOT",
            "OVER 1.5", "OVER 2.5", "BTTS%", "CORNERS", "C.9.5%", "TARJETAS",
            "MERCADO CLAVE", "RANGO", "C.LOC", "C.EMP", "C.VIS", "EDGE", "FUENTE", "TRACKING"]
    WW = [9, 22, 30, 7, 7, 7, 7, 7, 7, 7, 9, 9, 8, 18, 9, 12, 24, 7, 8, 8, 8, 10, 20, 14]

    for dia in list(dict.fromkeys(r["dia"] for r in resultados)):
        wsd = wb.create_sheet(title=str(dia)[:20])
        wsd.sheet_view.showGridLines = False; set_w(wsd, WW)
        title(wsd, 1, f"SCORPION ELITE | {str(dia).upper()}", len(COLS), sz=13)
        wsd.row_dimensions[1].height = 24
        hrow(wsd, 2, COLS, sz=8); wsd.row_dimensions[2].height = 36
        fila = 3
        for p in [x for x in resultados if x["dia"] == dia]:
            p1, px, p2 = p["p1"], p["px"], p["p2"]
            r1x2 = "1" if p1 > p2 and p1 > px else ("X" if px >= p1 and px >= p2 else "2")
            cl = p["cuotas"]["cuota_local"]  if p["cuotas"] else ""
            ce = p["cuotas"]["cuota_empate"] if p["cuotas"] else ""
            cv = p["cuotas"]["cuota_visita"] if p["cuotas"] else ""
            if p["edge_local"] is not None:
                me = max([p["edge_local"] or -99, p["edge_empate"] or -99, p["edge_visita"] or -99])
                edge_str = f"+{me:.1f}%" if me > 0 else f"{me:.1f}%"
            else: edge_str = ""
            ft = f'L:{p["fuente_local"][:8]} V:{p["fuente_visit"][:8]}'
            g = p["local"] if p1 >= p2 else p["visitante"]
            if p1 > p2 and p1 > px:        mk = f"{g} Gana"
            elif p["over25"] >= 65:         mk = "Over 2.5 Goles"
            elif p["btts"] >= 62:           mk = "BTTS Ambos Marcan"
            elif p["c95"] >= 65:            mk = "Corners Over 9.5"
            else:                           mk = f"{g} Gana / Over 1.5"
            rv = [p["hora"], p["liga"][:20], f'{p["local"]} vs {p["visitante"]}',
                  r1x2, f"{p1}%", f"{px}%", f"{p2}%", p["xg_local"], p["xg_visit"], p["xg_total"],
                  f'{p["over15"]}%', f'{p["over25"]}%', f'{p["btts"]}%',
                  p["corners_str"][:18], f'{p["c95"]}%', p["tar_str"],
                  mk, p["rango"], cl, ce, cv, edge_str, ft, "PENDIENTE"]
            bg = "0D3B0D" if p["rango"] == "A+" else ("0F3460" if fila % 2 == 0 else "16213E")
            for col, val in enumerate(rv, 1):
                c = wsd.cell(row=fila, column=col, value=val); fg = "FFFFFF"
                if col == 18:   fg = "FFD700" if p["rango"] == "A+" else ("00FF7F" if p["rango"] == "B" else "AAAAAA")
                elif col in (8, 9, 10): fg = "00FFFF"
                elif col == 22: fg = "00FF7F" if "+" in str(edge_str) else ("FF6666" if edge_str else "AAAAAA")
                elif col == 23:
                    ambos = p["datos_local"] and p["datos_visit"]
                    uno   = p["datos_local"] or  p["datos_visit"]
                    fg = "00FF7F" if ambos else ("FFA500" if uno else "FF6666")
                sc(c, bg=bg, fg=fg, sz=9, bold=(p["rango"] == "A+" and col in (3, 17, 18)))
            wsd.row_dimensions[fila].height = 22; fila += 1

    wsv = wb.create_sheet(title="VALUE BETS"); wsv.sheet_view.showGridLines = False
    vc = ["HORA", "PARTIDO", "LIGA", "MERCADO", "PROB%", "C.JUSTA", "C.REF", "EDGE%", "KELLY%", "ETIQUETA", "TIPO", "TRACKING"]
    set_w(wsv, [9, 30, 20, 18, 7, 9, 9, 9, 9, 16, 12, 13])
    title(wsv, 1, "VALUE BETTING -- Edge Real + Kelly Criterion", len(vc), bg="0A1A0A", fg="FFD700", sz=13)
    hrow(wsv, 2, vc, bg="0A2E0A", fg="00FF7F", sz=8); fv = 3
    for p in resultados:
        for vb in [v for v in p["value_bets"] if v["edge"] >= 2][:5]:
            e = vb["edge"]; bg = "0D3B0D" if e >= 5 else ("0F3460" if e >= 2 else "2A1A0A")
            rv = [p["hora"], f'{p["local"]} vs {p["visitante"]}', p["liga"][:18],
                  vb["mercado"], f'{vb["prob"]}%', str(vb["cuota_justa"]), str(vb["cuota_ref"]),
                  f'{vb["edge"]:+.1f}%', f'{vb["kelly"]}%', vb["label"],
                  "Odds reales" if vb.get("con_odds") else "Modelo", "PENDIENTE"]
            for col, val in enumerate(rv, 1):
                c = wsv.cell(row=fv, column=col, value=val); fg = "FFFFFF"
                if col == 8:  fg = "00FF7F" if e >= 5 else ("AAFFAA" if e >= 2 else "FFA500")
                elif col == 10: fg = "FFD700" if "ALTO" in str(val) else ("00FF7F" if "VALOR" in str(val) else "888888")
                elif col == 11: fg = "00FF7F" if "reales" in str(val) else "AAAAAA"
                sc(c, bg=bg, fg=fg, sz=9)
            wsv.row_dimensions[fv].height = 20; fv += 1

    wsvip = wb.create_sheet(title="VIP A+"); wsvip.sheet_view.showGridLines = False
    vipc = ["HORA", "ENCUENTRO", "CAT", "MERCADO 1", "P%", "EDGE", "MERCADO 2", "P%", "EDGE",
            "xG LOC", "xG VIS", "xG TOT", "CORNERS", "TARJ.", "CUOTAS", "FUENTE", "TRACKING"]
    set_w(wsvip, [9, 30, 5, 22, 7, 9, 22, 7, 9, 8, 8, 8, 16, 12, 22, 22, 13])
    title(wsvip, 1, "VIP A+ -- Analisis Profundo por Partido", len(vipc), bg="0D0D0D", fg="FFD700", sz=13)
    hrow(wsvip, 2, vipc, bg="0A0A0A", fg="FFD700", sz=8)
    for i, p in enumerate([r for r in resultados if r["rango"] == "A+"], 3):
        bg = "0D2E0D" if i % 2 == 0 else "091F09"
        vbs = p["value_bets"]
        def gvb(n): return (vbs[n]["mercado"], f'{vbs[n]["prob"]}%', f'{vbs[n]["edge"]:+.1f}%') if len(vbs) > n else ("--", "--", "--")
        m1, pr1, e1 = gvb(0); m2, pr2, e2 = gvb(1)
        ct = f'{p["cuotas"]["cuota_local"]}/{p["cuotas"]["cuota_empate"]}/{p["cuotas"]["cuota_visita"]}' if p["cuotas"] else "Sin cuotas"
        rv = [p["hora"], f'{p["local"]} vs {p["visitante"]}', "A+", m1, pr1, e1, m2, pr2, e2,
              p["xg_local"], p["xg_visit"], p["xg_total"], p["corners_str"][:14], p["tar_str"],
              ct, f'L:{p["fuente_local"][:9]}/V:{p["fuente_visit"][:9]}', "PENDIENTE"]
        for col, val in enumerate(rv, 1):
            c = wsvip.cell(row=i, column=col, value=val); fg = "FFFFFF"
            if col == 3: fg = "FFD700"
            elif col in (6, 9): fg = "00FF7F" if "+" in str(val) and val != "--" else ("FF4444" if "-" in str(val) else "888888")
            elif col in (10, 11, 12): fg = "00FFFF"
            elif col == 15: fg = "00FF7F" if p["cuotas"] else "AAAAAA"
            elif col == 16: fg = "00FF7F" if p["datos_local"] and p["datos_visit"] else ("FFA500" if p["datos_local"] or p["datos_visit"] else "FF6666")
            sc(c, bg=bg, fg=fg, sz=9, bold=(col <= 3))
        wsvip.row_dimensions[i].height = 26

    for ws_tab in wb.worksheets: ws_tab.freeze_panes = "A3"
    tab_c = {"LEER ANTES": "FFD700", "VALUE BETS": "00CC44", "VIP A+": "FFD700"}
    for ws_tab in wb.worksheets:
        ws_tab.sheet_properties.tabColor = tab_c.get(ws_tab.title, "1E90FF")
    buf = io.BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

# ── APP PRINCIPAL ────────────────────────────────────────────────────────────
def app_principal():
    nombre = st.session_state.nombre
    c1, c2 = st.columns([8, 1])
    with c1:
        st.markdown(f'<div class="hdr"><h1>🦂 SCORPION ELITE</h1><p>Bienvenido, {nombre} — Motor de Analisis Deportivo con Datos Reales</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("Salir"): st.session_state.logged_in = False; st.rerun()

    st.markdown("### Como usar")
    cols = st.columns(4)
    pasos = [("1", "Sube tu Excel", "Con los partidos en el formato habitual"),
             ("2", "Clic en Analizar", "El motor busca stats reales de cada equipo"),
             ("3", "Espera", "3-5 seg por partido. Progreso en pantalla"),
             ("4", "Descarga el Excel", "Hojas: dias, value bets, VIP A+")]
    for col, (n, t, d) in zip(cols, pasos):
        with col:
            st.markdown(f'<div class="sb"><div class="n">Paso {n} — {t}</div><div class="t">{d}</div></div>', unsafe_allow_html=True)

    st.divider()
    uploaded = st.file_uploader("Sube tu Excel de partidos", type=["xlsx"])
    if uploaded:
        fb = uploaded.read()
        try: partidos = leer_partidos(fb)
        except Exception as e: st.error(f"Error leyendo el archivo: {e}"); return
        if not partidos: st.warning("No se encontraron partidos. Verifica el formato."); return

        dias_u  = list(dict.fromkeys(p["dia"]  for p in partidos))
        ligas_u = list(dict.fromkeys(p["liga"] for p in partidos))
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="mc"><div class="v">{len(partidos)}</div><div class="l">Partidos</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="mc"><div class="v">{len(dias_u)}</div><div class="l">Dias</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="mc"><div class="v">{len(ligas_u)}</div><div class="l">Ligas</div></div>', unsafe_allow_html=True)

        prev = [[p["dia"], p["hora"], p["liga"][:25], p["local"], p["visitante"]] for p in partidos[:6]]
        st.table({"Dia": [r[0] for r in prev], "Hora": [r[1] for r in prev], "Liga": [r[2] for r in prev],
                  "Local": [r[3] for r in prev], "Visitante": [r[4] for r in prev]})
        if len(partidos) > 6: st.caption(f"... y {len(partidos)-6} partidos mas")

        if st.button(f"🦂 Analizar {len(partidos)} partidos"):
            resultados = []; prog = st.progress(0, "Iniciando..."); status = st.empty()
            SIN_WEB = ["argelia", "jamaica", "bosnia", "amapaense", "bahrein", "faroe"]
            for idx, p in enumerate(partidos):
                local = p["local"]; visitante = p["visitante"]; liga = p["liga"]
                status.markdown(f"🔍 **[{idx+1}/{len(partidos)}]** {local} vs {visitante}")
                prog.progress((idx + 1) / len(partidos), text=f"{idx+1}/{len(partidos)}")
                sin_cob = any(s in liga.lower() for s in SIN_WEB)
                if sin_cob:
                    pm = gp(liga)
                    stl = {"goles_marcados": pm["gm"], "goles_concedidos": pm["gc"], "xg": None, "xga": None, "elo": None, "fuente": "Prom.liga", "encontrado": False}
                    stv = {"goles_marcados": pm["gm"] * 0.78, "goles_concedidos": pm["gc"], "xg": None, "xga": None, "elo": None, "fuente": "Prom.liga", "encontrado": False}
                    cuotas = None
                else:
                    stl    = obtener_stats(local, liga)
                    stv    = obtener_stats(visitante, liga)
                    cuotas = buscar_cuotas(local, visitante, liga)
                calc  = calcular(stl, stv, liga, cuotas)
                vbets = value_bets(calc, local, visitante, cuotas)
                p1, px, p2 = calc["p1"], calc["px"], calc["p2"]
                score = sum([stl["encontrado"] * 25, stv["encontrado"] * 25,
                             25 if max(p1, p2) >= 60 else (12 if max(p1, p2) >= 50 else 0),
                             20 if any(k in liga.lower() for k in ["premier", "laliga", "la liga", "bundesliga", "serie a", "ligue", "libertadores", "champions", "mundial", "world cup", "eurocopa", "copa america"]) else 0])
                rango = "A+" if score >= 75 else ("B" if score >= 40 else "C")
                resultados.append({**p, "p1": p1, "px": px, "p2": p2,
                    "xg_local": calc["xg_local"], "xg_visit": calc["xg_visit"], "xg_total": calc["xg_total"],
                    "over15": calc["over15"], "over25": calc["over25"], "btts": calc["btts"],
                    "corners_str": calc["corners_str"], "c95": calc["c95"], "tar_str": calc["tar_str"],
                    "rango": rango, "value_bets": vbets, "cuotas": cuotas,
                    "edge_local": calc["edge_local"], "edge_empate": calc["edge_empate"], "edge_visita": calc["edge_visita"],
                    "fuente_local": stl["fuente"], "fuente_visit": stv["fuente"],
                    "datos_local": stl["encontrado"], "datos_visit": stv["encontrado"]})

            prog.progress(1.0, "Listo ✅"); status.empty()
            st.success(f"✅ {len(resultados)} partidos analizados")
            ap        = sum(1 for r in resultados if r["rango"] == "A+")
            ambos     = sum(1 for r in resultados if r["datos_local"] and r["datos_visit"])
            vb_tot    = sum(len([v for v in r["value_bets"] if v["edge"] >= 2]) for r in resultados)
            with_odds = sum(1 for r in resultados if r["cuotas"])
            c1, c2, c3, c4 = st.columns(4)
            for col, (val, lbl) in zip([c1, c2, c3, c4], [(ap, "VIP A+"), (ambos, "Datos reales"), (vb_tot, "Value bets"), (with_odds, "Cuotas reales")]):
                with col: st.markdown(f'<div class="mc"><div class="v">{val}</div><div class="l">{lbl}</div></div>', unsafe_allow_html=True)

            ap_list = [r for r in resultados if r["rango"] == "A+"]
            if ap_list:
                st.markdown("### Top picks A+")
                for r in ap_list[:5]:
                    vb0 = r["value_bets"][0] if r["value_bets"] else None
                    mk  = vb0["mercado"] if vb0 else "Ver analisis"
                    et  = f" — Edge:{vb0['edge']:+.1f}%" if vb0 else ""
                    st.markdown(f"🟢 **{r['local']} vs {r['visitante']}** ({r['liga'][:20]}) · {mk}{et}")

            excel_bytes = generar_excel(resultados)
            fecha = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button("⬇️ Descargar Excel completo", data=excel_bytes,
                file_name=f"ScorpionElite_{fecha}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    st.markdown('<div class="ft">🦂 Scorpion Elite 2025 — Solo uso informativo</div>', unsafe_allow_html=True)

# ── ROUTER ───────────────────────────────────────────────────────────────────
if not st.session_state.logged_in:
    pantalla_login()
else:
    app_principal()
