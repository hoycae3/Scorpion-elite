"""SCORPION ENGINE V3 PRO — Sistema completo en un solo archivo"""
import streamlit as st
import os, json, re, time, math, io, base64, sqlite3, hashlib, warnings, requests
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime, time as dtime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import random
warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "124c9519df145caf883cd82f0b2a4671")
ADMIN_PWD        = os.getenv("ADMIN_PASSWORD",   "scorpion_admin_2025")
DB_PATH          = "/tmp/scorpion_v3.db"

LIGAS = {
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League":   39,
    "🇪🇸 La Liga":            140,
    "🇩🇪 Bundesliga":         78,
    "🇮🇹 Serie A":            135,
    "🇫🇷 Ligue 1":            61,
    "🇳🇱 Eredivisie":         88,
    "🇵🇹 Primeira Liga":      94,
    "🌍 Champions League":    2,
    "🌍 Europa League":       3,
    "🌍 Conference League":   848,
    "🌎 Libertadores":        13,
    "🌎 Sudamericana":        11,
    "🌎 Copa America":        9,
    "🌍 Mundial FIFA 2026":   1,
    "🇺🇸 MLS":                253,
    "🇲🇽 Liga MX":            262,
    "🇨🇴 Liga BetPlay":       239,
    "🇦🇷 Primera Division":   128,
    "🇧🇷 Brasileirao":        71,
    "🇹🇷 Super Lig":          203,
    "🇸🇦 Saudi Pro League":   307,
}

PROM_LIGA = {
    "premier":{"gm":1.54,"gc":1.11}, "la liga":{"gm":1.62,"gc":1.08},
    "bundesliga":{"gm":1.82,"gc":1.28}, "serie a":{"gm":1.48,"gc":1.07},
    "ligue":{"gm":1.51,"gc":1.07}, "libertadores":{"gm":1.32,"gc":1.08},
    "sudamericana":{"gm":1.28,"gc":1.07}, "eredivisie":{"gm":1.88,"gc":1.32},
    "mls":{"gm":1.45,"gc":1.20}, "colombia":{"gm":1.25,"gc":1.10},
    "mundial":{"gm":1.35,"gc":1.05}, "world cup":{"gm":1.35,"gc":1.05},
    "copa america":{"gm":1.28,"gc":1.08}, "champions":{"gm":1.45,"gc":1.05},
    "europa":{"gm":1.42,"gc":1.08}, "default":{"gm":1.40,"gc":1.15},
}

LIGAS_TOP = ["premier","la liga","bundesliga","serie a","ligue","champions",
             "europa","libertadores","mundial","world cup","copa america","eredivisie"]

UNDERSTAT_MAP = {
    "premier":"EPL","premier league":"EPL","la liga":"La_liga",
    "bundesliga":"Bundesliga","serie a":"Serie_A","ligue 1":"Ligue_1","ligue":"Ligue_1",
}

TORNEOS_FIFA = ["mundial","world cup","fifa","copa del mundo","nations league",
                "eurocopa","euro 20","copa america","gold cup","afcon"]

SELECCIONES = {
    "argentina","brasil","brazil","francia","france","alemania","germany",
    "espana","spain","portugal","inglaterra","england","italia","italy",
    "belgica","belgium","croacia","croatia","holanda","netherlands","uruguay",
    "colombia","chile","mexico","estados unidos","usa","japon","japan",
    "marruecos","morocco","senegal","australia","corea","korea","suiza",
    "switzerland","dinamarca","denmark","polonia","poland","austria",
    "turquia","turkey","serbia","ecuador","peru","ghana","nigeria","camerun",
    "sudafrica","south africa","arabia","saudi","iran","qatar","canada",
    "gales","wales","escocia","scotland","hungria","georgia","eslovenia",
}

SH = requests.Session()
SH.headers.update({"User-Agent":"Mozilla/5.0","Accept":"application/json,text/html,*/*"})

# ══════════════════════════════════════════════════════════
# BASE DE DATOS SQLITE
# ══════════════════════════════════════════════════════════
def get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = get_conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        cedula TEXT PRIMARY KEY, nombre TEXT NOT NULL, plan TEXT DEFAULT 'gratis',
        fecha_inicio TEXT, dias INTEGER DEFAULT 36500, activo INTEGER DEFAULT 1,
        es_admin INTEGER DEFAULT 0, pwd_hash TEXT, consultas_hoy INTEGER DEFAULT 0,
        fecha_reset TEXT, creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, liga TEXT, local TEXT,
        visitante TEXT, hora TEXT, mercado TEXT, cuota REAL, edge REAL,
        confianza REAL, rango TEXT, resultado TEXT, acierto INTEGER,
        notas TEXT, plan_min TEXT DEFAULT 'gratis',
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT, fecha TEXT,
        liga TEXT, local TEXT, visitante TEXT, p1 REAL, px REAL, p2 REAL,
        xg_l REAL, xg_v REAL, over25 REAL, btts REAL, mercado TEXT,
        rango TEXT, confianza REAL, creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    h = hashlib.sha256(ADMIN_PWD.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (cedula,nombre,plan,fecha_inicio,dias,activo,es_admin,pwd_hash) VALUES (?,?,?,?,?,?,?,?)",
              ("admin","Administrador","admin",str(date.today()),36500,1,1,h))
    c.execute("INSERT OR IGNORE INTO usuarios (cedula,nombre,plan,fecha_inicio,dias,activo) VALUES (?,?,?,?,?,?)",
              ("owner","Propietario Prueba","mes",str(date.today()),36500,1))
    c.commit(); c.close()

def db_get_usuario(cedula):
    c = get_conn()
    r = c.execute("SELECT * FROM usuarios WHERE cedula=?", (cedula,)).fetchone()
    c.close()
    return dict(r) if r else None

def db_todos_usuarios():
    c = get_conn()
    r = c.execute("SELECT * FROM usuarios ORDER BY creado DESC").fetchall()
    c.close()
    return [dict(x) for x in r]

def db_guardar_usuario(cedula, nombre, plan, dias, fi, activo=1):
    c = get_conn()
    c.execute("""INSERT OR REPLACE INTO usuarios (cedula,nombre,plan,fecha_inicio,dias,activo,es_admin,pwd_hash,creado)
                 VALUES (?,?,?,?,?,?,
                 COALESCE((SELECT es_admin FROM usuarios WHERE cedula=?),0),
                 COALESCE((SELECT pwd_hash FROM usuarios WHERE cedula=?),NULL),
                 COALESCE((SELECT creado   FROM usuarios WHERE cedula=?),CURRENT_TIMESTAMP))""",
              (cedula,nombre,plan,str(fi),int(dias),int(activo),cedula,cedula,cedula))
    c.commit(); c.close()

def db_verificar_acceso(cedula):
    u = db_get_usuario(cedula)
    if not u: return False,"no_existe",0
    if not u["activo"]: return False,"inactivo",0
    if u["es_admin"]: return True,"admin",99999
    if u["plan"]=="gratis": return True,"gratis",99999
    inicio = date.fromisoformat(u["fecha_inicio"])
    vence  = inicio + timedelta(days=u["dias"])
    dr     = (vence - date.today()).days
    if date.today() > vence: return False,"vencido",0
    return True, u["plan"], dr

def db_login_admin(pwd):
    u = db_get_usuario("admin")
    if not u: return False
    return u.get("pwd_hash") == hashlib.sha256(pwd.encode()).hexdigest()

def db_incrementar_consulta(cedula):
    c = get_conn()
    hoy = str(date.today())
    u = c.execute("SELECT consultas_hoy, fecha_reset FROM usuarios WHERE cedula=?", (cedula,)).fetchone()
    if u:
        if u["fecha_reset"] != hoy:
            c.execute("UPDATE usuarios SET consultas_hoy=1, fecha_reset=? WHERE cedula=?", (hoy,cedula))
            c.commit(); c.close(); return 1
        nuevo = (u["consultas_hoy"] or 0)+1
        c.execute("UPDATE usuarios SET consultas_hoy=? WHERE cedula=?", (nuevo,cedula))
        c.commit(); c.close(); return nuevo
    c.close(); return 0

def db_guardar_pick(fecha,liga,local,visitante,hora,mercado,cuota,edge,confianza,rango,notas,plan_min):
    c = get_conn()
    c.execute("INSERT INTO picks (fecha,liga,local,visitante,hora,mercado,cuota,edge,confianza,rango,notas,plan_min) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
              (fecha,liga,local,visitante,hora,mercado,cuota,edge,confianza,rango,notas,plan_min))
    c.commit(); c.close()

def db_get_picks(fecha=None, plan="gratis"):
    c = get_conn()
    orden = {"gratis":0,"dia":1,"semana":2,"mes":3,"admin":4}
    nivel = orden.get(plan,0)
    if fecha:
        rows = c.execute("SELECT * FROM picks WHERE fecha=? ORDER BY confianza DESC", (fecha,)).fetchall()
    else:
        rows = c.execute("SELECT * FROM picks ORDER BY fecha DESC, confianza DESC LIMIT 50").fetchall()
    c.close()
    resultado = []
    for r in [dict(x) for x in rows]:
        nivel_min = orden.get(r.get("plan_min","gratis"),0)
        if nivel < nivel_min:
            r["mercado"] = f"🔒 Requiere Plan {r['plan_min'].upper()}"
            r["cuota"] = None; r["edge"] = None
        resultado.append(r)
    return resultado

def db_guardar_historial(cedula, p, calc):
    c = get_conn()
    c.execute("INSERT INTO historial (cedula,fecha,liga,local,visitante,p1,px,p2,xg_l,xg_v,over25,btts,mercado,rango,confianza) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (cedula,p.get("dia",str(date.today())),p.get("liga",""),p.get("local",""),p.get("visitante",""),
               calc.get("p1"),calc.get("px"),calc.get("p2"),calc.get("xl"),calc.get("xv"),
               calc.get("over25"),calc.get("btts_si"),calc.get("mk2",""),calc.get("rango",""),calc.get("confianza")))
    c.commit(); c.close()

def db_get_historial(cedula, limite=30):
    c = get_conn()
    r = c.execute("SELECT * FROM historial WHERE cedula=? ORDER BY creado DESC LIMIT ?", (cedula,limite)).fetchall()
    c.close()
    return [dict(x) for x in r]

def db_stats():
    c = get_conn()
    tu = c.execute("SELECT COUNT(*) FROM usuarios WHERE es_admin=0").fetchone()[0]
    tp = c.execute("SELECT COUNT(*) FROM picks").fetchone()[0]
    th = c.execute("SELECT COUNT(*) FROM historial").fetchone()[0]
    c.close()
    activos = sum(1 for u in db_todos_usuarios() if u.get("es_admin")==0 and db_verificar_acceso(u["cedula"])[0])
    return {"usuarios":tu,"activos":activos,"picks":tp,"historial":th}

# ══════════════════════════════════════════════════════════
# MOTOR MATEMATICO
# ══════════════════════════════════════════════════════════
def pp(lam, k):
    if lam<=0 or k<0: return 0.0
    return (math.exp(-lam)*(lam**k))/math.factorial(min(k,20))

def dc_tau(x, y, xl, xv, rho=-0.1):
    if x==0 and y==0: return 1-xl*xv*rho
    if x==1 and y==0: return 1+xv*rho
    if x==0 and y==1: return 1+xl*rho
    if x==1 and y==1: return 1-rho
    return 1.0

def poisson_1x2(xl, xv):
    p1=px=p2=0.0
    for i in range(9):
        for j in range(9):
            p=pp(xl,i)*pp(xv,j)
            if i>j: p1+=p
            elif i==j: px+=p
            else: p2+=p
    return round(p1*100,1), round(px*100,1), round(p2*100,1)

def dc_1x2(xl, xv, rho=-0.1):
    m={}
    for i in range(9):
        for j in range(9):
            m[(i,j)]=max(0, pp(xl,i)*pp(xv,j)*dc_tau(i,j,xl,xv,rho))
    t=sum(m.values())
    if t>0: m={k:v/t for k,v in m.items()}
    p1=sum(v for (i,j),v in m.items() if i>j)
    px=sum(v for (i,j),v in m.items() if i==j)
    p2=sum(v for (i,j),v in m.items() if i<j)
    return round(p1*100,1), round(px*100,1), round(p2*100,1)

def monte_carlo(xl, xv, n=4000):
    v1=vx=v2=0; gt=[]; mk={}
    for _ in range(n):
        gl=gv=0; a=0.0; u=random.random()
        for k in range(15):
            a+=pp(xl,k)
            if u<=a: gl=k; break
        a=0.0; u=random.random()
        for k in range(15):
            a+=pp(xv,k)
            if u<=a: gv=k; break
        if gl>gv: v1+=1
        elif gl==gv: vx+=1
        else: v2+=1
        gt.append(gl+gv)
        mk[f"{gl}-{gv}"] = mk.get(f"{gl}-{gv}",0)+1
    top=dict(sorted(mk.items(),key=lambda x:x[1],reverse=True)[:6])
    top={k:round(v/n*100,1) for k,v in top.items()}
    return {"p1_mc":round(v1/n*100,1),"px_mc":round(vx/n*100,1),"p2_mc":round(v2/n*100,1),
            "avg_g":round(sum(gt)/n,2),"over25_mc":round(sum(1 for g in gt if g>2)/n*100),
            "top_mk":top}

def elo_1x2(elo_l, elo_v, ventaja=50):
    e_l=1/(1+10**((elo_v-(elo_l+ventaja))/400))
    e_v=1-e_l
    p1=round(e_l*100,1); p2=round(e_v*100,1); px=max(0,100-p1-p2)
    return p1, px, p2

def kelly(prob, cuota, f=0.25):
    if cuota<=1 or prob<=0: return 0.0
    b=cuota-1; q=1-prob/100
    k=(prob/100*b-q)/b
    return round(max(0,k)*f*100,1)

def get_prom(liga):
    l=liga.lower()
    for k in PROM_LIGA:
        if k in l: return PROM_LIGA[k]
    return PROM_LIGA["default"]

def es_liga_top(liga):
    l=liga.lower()
    return any(k in l for k in LIGAS_TOP)

def calcular(gml, gcl, gmv, gcv, liga, elo_l=None, elo_v=None):
    pr=get_prom(liga)
    if gml and gcv:  xl=round(gml*(gcv/pr["gc"])*1.08,2)
    elif gml:        xl=round(gml*1.08,2)
    else:            xl=round(pr["gm"]*1.08,2)
    if gmv and gcl:  xv=round(gmv*(gcl/pr["gc"]),2)
    elif gmv:        xv=round(gmv,2)
    else:            xv=round(pr["gm"]*0.78,2)
    if elo_l and elo_v:
        f=1+(elo_l-elo_v)/4000
        xl=round(xl*min(max(f,0.7),1.4),2)
        xv=round(xv*min(max(1/f,0.7),1.4),2)
    xl=max(0.15,xl); xv=max(0.10,xv); xt=round(xl+xv,2)
    p1_po,px_po,p2_po = poisson_1x2(xl,xv)
    p1_dc,px_dc,p2_dc = dc_1x2(xl,xv)
    mc = monte_carlo(xl,xv,3000)
    p1_mc,px_mc,p2_mc = mc["p1_mc"],mc["px_mc"],mc["p2_mc"]
    if elo_l and elo_v: p1_el,px_el,p2_el=elo_1x2(elo_l,elo_v)
    else: p1_el,px_el,p2_el=p1_po,px_po,p2_po
    # Scorpion Score ponderado
    p1=round(p1_po*.35+p1_dc*.30+p1_mc*.20+p1_el*.15,1)
    px=round(px_po*.35+px_dc*.30+px_mc*.20+px_el*.15,1)
    p2=round(max(0,100-p1-px),1)
    conv=100-(abs(p1_po-p1_dc)*.4+abs(p1_po-p1_mc)*.3+abs(p1_po-p1_el)*.3)
    conf=round(max(0,min(100,conv)))
    datos_r = gml is not None and gmv is not None
    if datos_r and conf>=75 and es_liga_top(liga): rango="A+"
    elif datos_r and conf>=55:                     rango="B"
    elif conf>=40:                                 rango="C"
    else:                                          rango="D"
    # Over/Under
    p0=pp(xt,0);p1_=pp(xt,1);p2_=pp(xt,2);p3_=pp(xt,3)
    o15=round((1-p0-p1_)*100); o25=round((1-p0-p1_-p2_)*100); o35=round((1-p0-p1_-p2_-p3_)*100)
    # BTTS
    btts_si=round((1-pp(xl,0))*(1-pp(xv,0))*100); btts_no=100-btts_si
    # Corners dinamicos
    cmu=round(xt*2.1+4.5,1); sc=2.5
    def poc(l):
        z=(l-cmu)/sc; return max(5,min(95,round((1-0.5*(1+math.erf(z/math.sqrt(2))))*100)))
    c75=poc(7.5);c85=poc(8.5);c95=poc(9.5);c105=poc(10.5)
    # Tarjetas
    dif=abs(p1-p2); tmu=round(3.5+(1-dif/60)*1.8,1)
    base=3.8 if any(k in liga.lower() for k in ["la liga","serie a","ligue","libertadores","colombia"]) else 3.2
    tmu=round(base+(1-dif/60)*1.8,1)
    # Marcado clave
    mk="1" if p1>p2 and p1>px else ("X" if px>=p1 and px>=p2 else "2")
    if p1>p2 and p1>px and o25>=55:   mk2="Gana Local + Over 1.5"
    elif p2>p1 and p2>px and o25>=55: mk2="Gana Visita + Over 1.5"
    elif o25>=65:                      mk2="Over 2.5 Goles"
    elif btts_si>=62:                  mk2="BTTS — Ambos Marcan"
    elif c95>=65:                      mk2="Corners Over 9.5"
    elif p1>p2 and p1>px:             mk2="Victoria Local"
    elif p2>p1 and p2>px:             mk2="Victoria Visitante"
    else:                              mk2="Empate posible"
    # Resultado exacto top
    top_ex={}
    for i in range(7):
        for j in range(7):
            pij=round(pp(xl,i)*pp(xv,j)*100,1)
            if pij>=0.5: top_ex[f"{i}-{j}"]=pij
    top_ex=dict(sorted(top_ex.items(),key=lambda x:x[1],reverse=True)[:8])
    return {
        "xl":xl,"xv":xv,"xt":xt,
        "p1_po":p1_po,"px_po":px_po,"p2_po":p2_po,
        "p1_dc":p1_dc,"px_dc":px_dc,"p2_dc":p2_dc,
        "p1_mc":p1_mc,"px_mc":px_mc,"p2_mc":p2_mc,
        "p1_el":p1_el,"px_el":px_el,"p2_el":p2_el,
        "p1":p1,"px":px,"p2":p2,"confianza":conf,"rango":rango,
        "over15":o15,"over25":o25,"over35":o35,
        "btts_si":btts_si,"btts_no":btts_no,
        "cmu":cmu,"c75":c75,"c85":c85,"c95":c95,"c105":c105,
        "corners_str":f"~{int(cmu)} (+9.5:{c95}% | +8.5:{c85}%)",
        "tar_str":f"~{max(2,int(tmu)-1)}-{int(tmu)+1} tarjetas",
        "mk":mk,"mk2":mk2,"top_ex":top_ex,
        "avg_g":mc["avg_g"],"top_mc":mc["top_mk"],"datos_r":datos_r,
    }

# ══════════════════════════════════════════════════════════
# DATOS REALES
# ══════════════════════════════════════════════════════════
_temp_cache={}
def get_temporada(lid):
    if lid in _temp_cache: return _temp_cache[lid]
    fallback={1:2026,253:2025,262:2025,239:2025,71:2025}
    try:
        r=SH.get("https://v3.football.api-sports.io/leagues",
                  headers={"x-apisports-key":API_FOOTBALL_KEY},
                  params={"id":lid,"current":"true"},timeout=10)
        data=r.json().get("response",[])
        if data:
            seasons=data[0].get("seasons",[])
            activa=[s for s in seasons if s.get("current")]
            if activa: t=activa[0]["year"]; _temp_cache[lid]=t; return t
            if seasons: t=seasons[-1]["year"]; _temp_cache[lid]=t; return t
    except: pass
    t=fallback.get(lid,2024); _temp_cache[lid]=t; return t

def get_fixtures_dia(lid, fecha):
    t=get_temporada(lid); h={"x-apisports-key":API_FOOTBALL_KEY}
    for p in [{"league":lid,"season":t,"date":fecha},{"league":lid,"date":fecha}]:
        try:
            r=SH.get("https://v3.football.api-sports.io/fixtures",headers=h,params=p,timeout=15)
            d=r.json().get("response",[])
            if d: return d
        except: pass
    return []

def get_fixtures_rango(lid, desde, hasta):
    t=get_temporada(lid); h={"x-apisports-key":API_FOOTBALL_KEY}
    for p in [{"league":lid,"season":t,"from":desde,"to":hasta},{"league":lid,"from":desde,"to":hasta}]:
        try:
            r=SH.get("https://v3.football.api-sports.io/fixtures",headers=h,params=p,timeout=15)
            d=r.json().get("response",[])
            if d: return d
        except: pass
    return []

def fx_to_partido(f):
    dt=f["fixture"]["date"]
    return {"dia":dt[:10],"hora":dt[11:16],"hora_sort":int(dt[11:13])*60+int(dt[14:16]),
            "liga":f["league"]["name"],"liga_id":f["league"]["id"],
            "local":f["teams"]["home"]["name"],"visitante":f["teams"]["away"]["name"],
            "tid_l":f["teams"]["home"]["id"],"tid_v":f["teams"]["away"]["id"]}

_stats_cache={}
def get_stats_api(tid, lid):
    k=f"{tid}_{lid}"
    if k in _stats_cache: return _stats_cache[k]
    t=get_temporada(lid)
    try:
        r=SH.get("https://v3.football.api-sports.io/teams/statistics",
                  headers={"x-apisports-key":API_FOOTBALL_KEY},
                  params={"team":tid,"season":t,"league":lid},timeout=12)
        d=r.json().get("response",{})
        gf=d.get("goals",{}).get("for",{}).get("average",{}).get("total")
        ga=d.get("goals",{}).get("against",{}).get("average",{}).get("total")
        res=(float(gf) if gf else None, float(ga) if ga else None)
        _stats_cache[k]=res; return res
    except: pass
    _stats_cache[k]=(None,None); return None,None

_und_cache={}
def get_understat(equipo, liga, temp=2024):
    lu=next((v for k,v in UNDERSTAT_MAP.items() if k in liga.lower()),None)
    if not lu: return None,None,None,None
    ck=f"{lu}_{temp}"
    if ck not in _und_cache:
        try:
            r=SH.get(f"https://understat.com/league/{lu}/{temp}",timeout=15)
            soup=BeautifulSoup(r.text,"lxml")
            for sc in soup.find_all("script"):
                if "teamsData" in str(sc):
                    m=re.search(r"JSON\.parse\(.(.*?)\.replace",str(sc))
                    if m:
                        _und_cache[ck]=json.loads(m.group(1).encode().decode("unicode_escape"))
                        break
        except: _und_cache[ck]={}
    data=_und_cache.get(ck,{})
    el=equipo.lower()
    for tn,stats in data.items():
        if any(p in tn.lower() for p in el.split()[:2]):
            h=stats.get("history",[])[-10:]
            if h:
                return (round(sum(x.get("xG",0) for x in h)/len(h),2),
                        round(sum(x.get("xGA",0) for x in h)/len(h),2),
                        round(sum(x.get("scored",0) for x in h)/len(h),2),
                        round(sum(x.get("missed",0) for x in h)/len(h),2))
    return None,None,None,None

def get_tsdb(nombre):
    try:
        r=SH.get(f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={requests.utils.quote(nombre)}",timeout=8)
        d=r.json()
        if d and d.get("teams"): return d["teams"][0]
    except: pass
    return None

def stats_tsdb(tid):
    try:
        r=SH.get(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={tid}",timeout=8)
        d=r.json()
        if d and d.get("results"):
            raw=d["results"][-10:]; gml=[]; gcl=[]
            for x in raw:
                try:
                    sh=int(x.get("intHomeScore") or 0); sa=int(x.get("intAwayScore") or 0)
                    if str(x.get("idHomeTeam",""))==str(tid): gml.append(sh);gcl.append(sa)
                    else: gml.append(sa);gcl.append(sh)
                except: pass
            if gml: return round(sum(gml)/len(gml),2),round(sum(gcl)/len(gcl),2)
    except: pass
    return None,None

_elo_cache={}
def get_elo(equipo):
    if equipo in _elo_cache: return _elo_cache[equipo]
    try:
        r=SH.get(f"http://api.clubelo.com/{equipo.replace(' ','-').replace('.','')}",timeout=8)
        if r.status_code==200 and len(r.text)>50:
            ul=r.text.strip().split("\n")[-1].split(",")
            if len(ul)>=4:
                elo=float(ul[3]); _elo_cache[equipo]=elo; return elo
    except: pass
    _elo_cache[equipo]=None; return None

def obtener_stats(nombre, liga, tid=None, lid=None):
    s={"gm":None,"gc":None,"xg":None,"xga":None,"elo":None,"fuente":"Prom.liga","ok":False}
    torneo=any(k in liga.lower() for k in TORNEOS_FIFA)
    selec=any(k in nombre.lower() for k in SELECCIONES)
    if not torneo and tid and lid:
        gm,gc=get_stats_api(tid,lid)
        if gm: s.update({"gm":gm,"gc":gc,"fuente":"API-Football","ok":True})
    if not torneo and not selec and not s["ok"]:
        xg,xga,gm_u,gc_u=get_understat(nombre,liga)
        if xg: s.update({"xg":xg,"xga":xga,"gm":gm_u,"gc":gc_u,"fuente":"Understat","ok":True})
        time.sleep(0.2)
    if not s["ok"]:
        td=get_tsdb(nombre)
        if td:
            gm2,gc2=stats_tsdb(td.get("idTeam",""))
            if gm2: s.update({"gm":gm2,"gc":gc2,"fuente":"TSDB","ok":True})
        time.sleep(0.25)
    elo=get_elo(nombre)
    if elo: s["elo"]=elo
    return s

def leer_imagen(img_bytes, mt="image/jpeg"):
    try:
        b64=base64.standard_b64encode(img_bytes).decode()
        payload={"model":"claude-sonnet-4-6","max_tokens":1500,"messages":[{"role":"user","content":[
            {"type":"image","source":{"type":"base64","media_type":mt,"data":b64}},
            {"type":"text","text":"""Analiza esta imagen de fixtures de futbol.
Devuelve SOLO JSON valido sin markdown:
{"partidos":[{"hora":"19:00","liga":"Premier League","local":"Arsenal","visitante":"Chelsea"}]}
Si no hay hora usa "00:00". Solo partidos claramente legibles. No inventes."""}
        ]}]}
        r=requests.post("https://api.anthropic.com/v1/messages",
                        headers={"Content-Type":"application/json"},json=payload,timeout=30)
        text=r.json().get("content",[{}])[0].get("text","")
        text=re.sub(r"```json|```","",text).strip()
        data=json.loads(text)
        result=[]
        for p in data.get("partidos",[]):
            hora=str(p.get("hora","00:00"))
            try: h,m=hora.split(":"); hs=int(h)*60+int(m)
            except: hs=0
            if p.get("local") and p.get("visitante"):
                result.append({"dia":str(date.today()),"hora":hora,"hora_sort":hs,
                               "liga":p.get("liga","Sin Liga"),"liga_id":0,
                               "local":p["local"],"visitante":p["visitante"],
                               "tid_l":None,"tid_v":None})
        return result
    except Exception as e:
        st.error(f"Error leyendo imagen: {e}"); return []

def leer_excel(fb):
    import openpyxl
    wb=openpyxl.load_workbook(io.BytesIO(fb),data_only=True); ws=wb.active
    partidos=[]; cur_liga=""
    TORN=["copa","liga","premier","bundesliga","serie","ligue","championship","apertura","clausura",
          "europa","champions","sudamericana","libertadores","mls","eredivisie","primera","superliga",
          "mundial","world cup","fifa","copa del mundo","nations","eurocopa","copa america"]
    def fix(s):
        s=str(s).strip().replace("\xa0","")
        for n in range(3,len(s)//2+1):
            if s[:n]==s[n:n*2]: return s[:n]
        return s
    for ri in range(1,ws.max_row+1):
        val=ws.cell(row=ri,column=1).value
        if val is None: continue
        if isinstance(val,dtime):
            try:
                l=fix(ws.cell(row=ri+1,column=1).value or "")
                v=fix(ws.cell(row=ri+2,column=1).value or "")
                if l not in ("","--") and v not in ("","--"):
                    partidos.append({"dia":str(date.today()),"hora":f"{val.hour:02d}:{val.minute:02d}",
                                     "hora_sort":val.hour*60+val.minute,"liga":cur_liga or "Sin Liga",
                                     "liga_id":0,"local":l,"visitante":v,"tid_l":None,"tid_v":None})
            except: pass
            continue
        vs=str(val).strip().replace("\xa0","")
        if any(k in vs.lower() for k in TORN) and len(vs)<80: cur_liga=vs
    return partidos

# ══════════════════════════════════════════════════════════
# ANALIZAR PARTIDOS
# ══════════════════════════════════════════════════════════
def analizar_lista(partidos, usar_api=True, prog=None):
    resultados=[]; n=len(partidos)
    for idx,p in enumerate(partidos):
        gml=gcl=gmv=gcv=elo_l=elo_v=None; fl=fv="Prom.liga"
        if usar_api:
            sl=obtener_stats(p["local"],p["liga"],p.get("tid_l"),p.get("liga_id"))
            sv=obtener_stats(p["visitante"],p["liga"],p.get("tid_v"),p.get("liga_id"))
            if sl["ok"]: gml=sl["gm"];gcl=sl["gc"];elo_l=sl["elo"];fl=sl["fuente"]
            if sv["ok"]: gmv=sv["gm"];gcv=sv["gc"];elo_v=sv["elo"];fv=sv["fuente"]
        calc=calcular(gml,gcl,gmv,gcv,p["liga"],elo_l,elo_v)
        resultados.append({**p,**calc,"fuente_l":fl,"fuente_v":fv})
        if prog: prog.progress((idx+1)/n,text=f"Analizando {idx+1}/{n}: {p['local']} vs {p['visitante']}")
    return resultados

# ══════════════════════════════════════════════════════════
# EXCEL EXPORT
# ══════════════════════════════════════════════════════════
def exportar_excel(resultados, titulo="Scorpion Elite V3 Pro"):
    def fill(c): return PatternFill("solid",fgColor=c)
    def brd():
        s=Side(border_style="thin",color="1a2a4a"); return Border(left=s,right=s,top=s,bottom=s)
    def al(h="center"): return Alignment(horizontal=h,vertical="center",wrap_text=True)
    def sc(cell,bg=None,fg="FFFFFF",bold=False,sz=9,h="center"):
        if bg: cell.fill=fill(bg)
        cell.font=Font(color=fg,bold=bold,size=sz,name="Arial")
        cell.alignment=al(h); cell.border=brd()
    def hr(ws,row,vals,bg="080820",fg="ffd700",sz=9):
        for c,v in enumerate(vals,1): cl=ws.cell(row=row,column=c,value=v); sc(cl,bg=bg,fg=fg,bold=True,sz=sz)
    def tr(ws,row,text,nc,bg="080820",fg="ffd700",sz=12):
        ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=nc)
        c=ws.cell(row=row,column=1,value=text); sc(c,bg=bg,fg=fg,bold=True,sz=sz)
    def sw(ws,wl):
        for i,w in enumerate(wl,1): ws.column_dimensions[get_column_letter(i)].width=w
    wb=Workbook(); first=True
    COLS=["HORA","LIGA","PARTIDO","1X2","P1%","PX%","P2%","CONF%",
          "xG L","xG V","xG T","O1.5","O2.5","O3.5","BTTS",
          "CORNERS","TARJ","PICK CLAVE","RANGO","POISSON","DC","MC","ELO","FUENTE"]
    WW=[9,20,30,7,7,7,7,7,7,7,7,8,8,8,7,16,11,26,7,9,9,9,9,16]
    for dia in list(dict.fromkeys(r["dia"] for r in resultados)):
        ws=wb.active if first else wb.create_sheet(title=str(dia)[:20])
        first=False
        if ws==wb.active: ws.title=str(dia)[:20]
        ws.sheet_view.showGridLines=False; sw(ws,WW)
        tr(ws,1,f"🦂 {titulo} | {dia}",len(COLS),sz=12)
        ws.row_dimensions[1].height=24; hr(ws,2,COLS,sz=8); ws.row_dimensions[2].height=36; fi=3
        for p in sorted([x for x in resultados if x["dia"]==dia],key=lambda x:x.get("hora_sort",0)):
            rg=p.get("rango","C")
            rv=[p.get("hora",""),p.get("liga","")[:18],f'{p["local"]} vs {p["visitante"]}',
                p.get("mk","?"),f'{p.get("p1",0):.1f}%',f'{p.get("px",0):.1f}%',f'{p.get("p2",0):.1f}%',
                f'{p.get("confianza",0)}%',p.get("xl",0),p.get("xv",0),p.get("xt",0),
                f'{p.get("over15",0)}%',f'{p.get("over25",0)}%',f'{p.get("over35",0)}%',
                f'{p.get("btts_si",0)}%',p.get("corners_str","")[:14],p.get("tar_str",""),
                p.get("mk2",""),rg,
                f'{p.get("p1_po",0):.1f}%',f'{p.get("p1_dc",0):.1f}%',
                f'{p.get("p1_mc",0):.1f}%',f'{p.get("p1_el",0):.1f}%',
                f'L:{p.get("fuente_l","?")[:6]} V:{p.get("fuente_v","?")[:6]}']
            bg="0a2810" if rg=="A+" else ("0a0a28" if fi%2==0 else "0d0d1e")
            for col,val in enumerate(rv,1):
                c=ws.cell(row=fi,column=col,value=val); fg="FFFFFF"
                if col==19: fg=("ffd700" if rg=="A+" else ("44aaff" if rg=="B" else "888888"))
                elif col in (9,10,11): fg="00ddff"
                elif col==24: fg="00cc44" if "API" in str(val) else "ffaa00"
                sc(c,bg=bg,fg=fg,sz=9,bold=(rg=="A+" and col in (3,18,19)))
            ws.row_dimensions[fi].height=22; fi+=1
    # Hoja Top Picks
    wsp=wb.create_sheet(title="TOP PICKS"); wsp.sheet_view.showGridLines=False
    pc=["HORA","PARTIDO","LIGA","PICK CLAVE","P1%","PX%","P2%","xG T","O2.5","BTTS","CONF%","RANGO","MARCADORES TOP"]
    sw(wsp,[9,30,18,28,7,7,7,7,8,7,8,7,30])
    tr(wsp,1,"🏆 TOP PICKS — Mayor confianza y ventaja estadistica",len(pc),bg="081208",fg="ffd700",sz=12)
    hr(wsp,2,pc,bg="0a1e0a",fg="00ff88",sz=8); fp=3
    top=sorted([r for r in resultados if r.get("rango") in ("A+","B")],
               key=lambda x:(x.get("confianza",0),max(x.get("p1",0),x.get("p2",0))),reverse=True)[:15]
    for p in top:
        bg="0a2810" if p.get("rango")=="A+" else "0a0a28"
        top_mk=" | ".join([f"{k}({v}%)" for k,v in list(p.get("top_ex",{}).items())[:4]])
        rv=[p.get("hora",""),f'{p["local"]} vs {p["visitante"]}',p.get("liga","")[:16],
            p.get("mk2",""),f'{p.get("p1",0):.1f}%',f'{p.get("px",0):.1f}%',f'{p.get("p2",0):.1f}%',
            p.get("xt",0),f'{p.get("over25",0)}%',f'{p.get("btts_si",0)}%',
            f'{p.get("confianza",0)}%',p.get("rango",""),top_mk]
        for col,val in enumerate(rv,1):
            c=wsp.cell(row=fp,column=col,value=val); fg="FFFFFF"
            if col==4: fg="ffd700"
            elif col==12: fg="00ff88" if p.get("rango")=="A+" else "44aaff"
            elif col==13: fg="aaaaaa"
            sc(c,bg=bg,fg=fg,sz=9,bold=(col in (4,12)))
        wsp.row_dimensions[fp].height=20; fp+=1
    # Hoja Modelos
    wsm=wb.create_sheet(title="DETALLE MODELOS"); wsm.sheet_view.showGridLines=False
    mc=["PARTIDO","LIGA","Poisson","D-Coles","M.Carlo","Elo","FINAL","Confianza","Rango","xG Total","Over2.5","BTTS","Marcadores Top 3"]
    sw(wsm,[30,18,10,10,10,10,10,9,7,9,9,8,30])
    tr(wsm,1,"🔬 DETALLE POR MODELO — Scorpion Engine V3",len(mc),sz=12)
    hr(wsm,2,mc,sz=8); fm=3
    for p in resultados:
        bg="0a2810" if p.get("rango")=="A+" else ("0a0a28" if fm%2==0 else "0d0d1e")
        top3=" | ".join([f"{k}({v}%)" for k,v in list(p.get("top_ex",{}).items())[:3]])
        rv=[f'{p["local"]} vs {p["visitante"]}',p.get("liga","")[:16],
            f'{p.get("p1_po",0):.1f}%',f'{p.get("p1_dc",0):.1f}%',
            f'{p.get("p1_mc",0):.1f}%',f'{p.get("p1_el",0):.1f}%',
            f'{p.get("p1",0):.1f}%',f'{p.get("confianza",0)}%',p.get("rango",""),
            p.get("xt",0),f'{p.get("over25",0)}%',f'{p.get("btts_si",0)}%',top3]
        for col,val in enumerate(rv,1):
            c=wsm.cell(row=fm,column=col,value=val); fg="FFFFFF"
            if col==9: fg=("ffd700" if p.get("rango")=="A+" else ("44aaff" if p.get("rango")=="B" else "888"))
            sc(c,bg=bg,fg=fg,sz=9)
        wsm.row_dimensions[fm].height=20; fm+=1
    for ws_tab in wb.worksheets: ws_tab.freeze_panes="A3"
    buf=io.BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

# ══════════════════════════════════════════════════════════
# CSS Y PAGE CONFIG
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="Scorpion Elite V3",page_icon="🦂",layout="wide")
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.stApp{background:#07070e}
.hdr{background:linear-gradient(135deg,#08102a,#10102e,#181838);
  border:1px solid #cc9900;border-radius:16px;padding:1.5rem 2rem;
  text-align:center;margin-bottom:1.5rem}
.hdr h1{color:#ffd700;font-size:2.2rem;margin:0;letter-spacing:4px;text-shadow:0 0 30px #ffd70055}
.hdr p{color:#888;margin:.3rem 0 0;font-size:.88rem}
.lbox{background:#0e0e22;border:1px solid #cc9900;border-radius:16px;padding:2.5rem;max-width:440px;margin:1.5rem auto}
.mc{background:#0e0e22;border:1px solid #1a2a44;border-radius:10px;padding:1rem;text-align:center;margin:.3rem 0}
.mc .v{color:#ffd700;font-size:1.8rem;font-weight:700}
.mc .l{color:#555;font-size:.7rem;margin-top:3px;text-transform:uppercase;letter-spacing:1px}
.badge-AP{background:#082a12;color:#00ee66;border:1px solid #00aa44;padding:2px 9px;border-radius:20px;font-size:11px;font-weight:700}
.badge-B{background:#081840;color:#44aaff;border:1px solid #2255aa;padding:2px 9px;border-radius:20px;font-size:11px}
.badge-C{background:#1a1200;color:#ccaa00;border:1px solid #886600;padding:2px 9px;border-radius:20px;font-size:11px}
.badge-D{background:#200a0a;color:#ee4444;border:1px solid #882222;padding:2px 9px;border-radius:20px;font-size:11px}
.pill-ok{background:#082a12;color:#00ee66;padding:2px 10px;border-radius:20px;font-size:11px}
.pill-v{background:#2a0808;color:#ee4444;padding:2px 10px;border-radius:20px;font-size:11px}
.pill-f{background:#1a1500;color:#ccaa00;padding:2px 10px;border-radius:20px;font-size:11px}
.pick-box{background:#0e0e22;border:1px solid #1a2a44;border-radius:10px;padding:.9rem 1rem;margin:.4rem 0}
.pick-box.ap{border-color:#00aa44}.pick-box.b{border-color:#2255aa}
.ft{text-align:center;color:#1e1e2e;font-size:.68rem;margin-top:2rem;padding-top:.8rem;border-top:1px solid #10102a}
div[data-testid="stButton"] button{background:linear-gradient(135deg,#ffd700,#cc7700)!important;
  color:#000!important;font-weight:700!important;border:none!important;border-radius:8px!important;width:100%}
</style>""",unsafe_allow_html=True)

def hdr(sub="Motor de Analisis Deportivo — 4 Modelos + Datos Reales"):
    st.markdown(f'<div class="hdr"><h1>🦂 SCORPION ELITE</h1><p>{sub}</p></div>',unsafe_allow_html=True)

def bdg(rango):
    return f'<span class="badge-{rango}">{rango}</span>'

def pll(plan,dr):
    if plan=="gratis": return f'<span class="pill-f">Plan Gratis</span>'
    if plan in ("dia","semana","mes","admin"):
        return f'<span class="pill-ok">{"Admin" if plan=="admin" else plan.upper()} · {dr} dias</span>'
    return f'<span class="pill-v">Vencido</span>'

def widget_archivo(max_p=None, key="up"):
    up=st.file_uploader("Sube Excel o captura de pantalla",type=["xlsx","xls","png","jpg","jpeg","webp"],key=key)
    if not up: return None
    fb=up.read(); nm=up.name.lower()
    if nm.endswith((".xlsx",".xls")):
        try: p=leer_excel(fb)
        except Exception as e: st.error(f"Error: {e}"); return None
    else:
        mt="image/png" if nm.endswith(".png") else ("image/webp" if nm.endswith(".webp") else "image/jpeg")
        with st.spinner("Leyendo imagen con IA..."): p=leer_imagen(fb,mt)
    if not p: st.warning("No se encontraron partidos."); return None
    if max_p: p=p[:max_p]
    st.success(f"✅ {len(p)} partidos detectados"); return p

# ══════════════════════════════════════════════════════════
# PANTALLAS
# ══════════════════════════════════════════════════════════
def pantalla_login():
    hdr()
    st.markdown('<div class="lbox">',unsafe_allow_html=True)
    st.markdown("### 🔐 Acceder")
    ced=st.text_input("Cedula / DNI",placeholder="Tu cedula o 'admin'")
    es_adm=ced.strip().lower()=="admin"
    pwd=st.text_input("Contrasena admin",type="password") if es_adm else ""
    if st.button("Entrar →"):
        if not ced.strip(): st.error("Ingresa tu cedula."); return
        if es_adm:
            if db_login_admin(pwd.strip()):
                u=db_get_usuario("admin")
                st.session_state.update({"li":True,"u":u,"ced":ced.strip()}); st.rerun()
            else: st.error("Contrasena incorrecta.")
        else:
            u=db_get_usuario(ced.strip())
            if not u:
                db_guardar_usuario(ced.strip(),f"Usuario {ced.strip()[:6]}","gratis",36500,date.today())
                u=db_get_usuario(ced.strip())
            ok,plan,dr=db_verificar_acceso(ced.strip())
            if not ok: st.error("Acceso vencido o inactivo. Contacta al administrador.")
            else: st.session_state.update({"li":True,"u":u,"ced":ced.strip()}); st.rerun()
    st.markdown('</div>',unsafe_allow_html=True)
    st.markdown("---")
    c1,c2,c3,c4=st.columns(4)
    infos=[("🆓 Gratis","Sube Excel o imagen\nMax 5 partidos/dia\nPicks del dia"),
           ("📅 Plan Dia","Liga a eleccion\nPartidos del dia\nExcel con 4 modelos"),
           ("📆 Plan Semana","Semana completa\nDias especificos\nMulti-liga"),
           ("👑 Plan Mes","Todo ilimitado\nTodas las ligas\nHistorial completo")]
    for col,(t,d) in zip([c1,c2,c3,c4],infos):
        with col: st.info(f"**{t}**\n\n{d}")
    st.markdown('<div class="ft">🦂 Scorpion Elite V3 Pro 2025 · Solo uso informativo · Las apuestas implican riesgo real de perdida</div>',unsafe_allow_html=True)

def pantalla_admin():
    hdr("Panel de Administrador")
    s=db_stats()
    c1,c2,c3,c4=st.columns(4)
    for col,(v,l) in zip([c1,c2,c3,c4],[(s["usuarios"],"Usuarios"),(s["activos"],"Activos"),(s["picks"],"Picks"),(s["historial"],"Analisis")]):
        with col: st.markdown(f'<div class="mc"><div class="v">{v}</div><div class="l">{l}</div></div>',unsafe_allow_html=True)
    st.markdown("---")
    t1,t2,t3=st.tabs(["👥 Clientes","📢 Publicar Pick","📊 Stats"])
    with t1:
        c1,c2=st.columns(2)
        with c1:
            st.markdown("### ➕ Registrar / Actualizar")
            ced2=st.text_input("Cedula"); nom2=st.text_input("Nombre")
            plan2=st.selectbox("Plan",["gratis","dia","semana","mes"])
            dm={"gratis":30,"dia":1,"semana":7,"mes":30}
            dias2=st.number_input("Dias",min_value=1,max_value=3650,value=int(dm[plan2]))
            fi2=st.date_input("Inicio",value=date.today())
            if st.button("💾 Guardar"):
                if ced2.strip():
                    db_guardar_usuario(ced2.strip(),nom2 or f"Cliente {ced2[:6]}",plan2,int(dias2),fi2)
                    st.success(f"✅ {ced2} guardado — {plan2.upper()} {dias2} dias")
                else: st.error("Ingresa la cedula")
        with c2:
            st.markdown("### 👥 Clientes")
            for u in db_todos_usuarios():
                if u["cedula"]=="admin": continue
                ok2,plan2,dr2=db_verificar_acceso(u["cedula"])
                p=pll(u["plan"],dr2)
                st.markdown(f"**{u['nombre']}** `{u['cedula']}` {p}",unsafe_allow_html=True)
    with t2:
        st.markdown("### 📢 Publicar Pick")
        c1,c2=st.columns(2)
        with c1:
            fp=st.date_input("Fecha",value=date.today()); lp=st.text_input("Liga")
            lop=st.text_input("Local"); vip=st.text_input("Visitante"); hop=st.text_input("Hora","20:00")
        with c2:
            mep=st.text_input("Mercado","ej: Gana Local + Over 1.5")
            cup=st.number_input("Cuota",1.0,50.0,1.85,0.05)
            edp=st.number_input("Edge %",-20.0,50.0,3.5,0.1)
            cop=st.number_input("Confianza %",0,100,75)
            rap=st.selectbox("Rango",["A+","B","C"])
            pmp=st.selectbox("Plan minimo",["gratis","dia","semana","mes"])
            nop=st.text_area("Notas",height=60)
        if st.button("📢 Publicar"):
            if lop and vip and mep:
                db_guardar_pick(str(fp),lp,lop,vip,hop,mep,cup,edp,cop,rap,nop,pmp)
                st.success("✅ Pick publicado")
            else: st.error("Completa equipos y mercado")
    with t3:
        st.info("El backtesting se activa cuando el administrador marca resultados en los picks publicados.")
        picks_todos=db_get_picks(plan="admin")
        if picks_todos:
            aciertos=[p for p in picks_todos if p.get("acierto")==1]
            fallos=[p for p in picks_todos if p.get("acierto")==0]
            c1,c2,c3=st.columns(3)
            with c1: st.markdown(f'<div class="mc"><div class="v">{len(picks_todos)}</div><div class="l">Total picks</div></div>',unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="mc"><div class="v">{len(aciertos)}</div><div class="l">Aciertos</div></div>',unsafe_allow_html=True)
            with c3:
                ta=round(len(aciertos)/len(picks_todos)*100) if picks_todos else 0
                st.markdown(f'<div class="mc"><div class="v">{ta}%</div><div class="l">Tasa acierto</div></div>',unsafe_allow_html=True)
    if st.button("🚪 Cerrar sesion"): st.session_state.clear(); st.rerun()

def pantalla_gratis(u):
    hdr()
    ok,plan,dr=db_verificar_acceso(u["cedula"])
    st.markdown(f'👋 Hola **{u["nombre"]}** {pll("gratis",dr)} · Max 5 partidos / dia',unsafe_allow_html=True)
    t1,t2=st.tabs(["📁 Analizar archivo","📢 Picks del dia"])
    with t1:
        st.info("Plan gratuito: primeros 5 partidos, sin datos reales de API. Actualiza para acceso completo.")
        cons=db_incrementar_consulta(u["cedula"])
        if cons>5:
            st.warning("Alcanzaste el limite de 5 consultas hoy. Vuelve manana o actualiza tu plan.")
        else:
            p=widget_archivo(max_p=5,key="free")
            if p and st.button(f"🦂 Analizar {len(p)} partidos"):
                prg=st.progress(0,"Analizando...")
                res=analizar_lista(p,usar_api=False,prog=prg)
                prg.progress(1.0,"Listo ✅")
                for r in res:
                    st.markdown(f'{bdg(r["rango"])} **{r["local"]} vs {r["visitante"]}** · {r["liga"][:18]} · {r["hora"]} · **{r["mk2"]}** · xG:{r["xl"]}-{r["xv"]} · O2.5:{r["over25"]}% · Conf:{r["confianza"]}%',unsafe_allow_html=True)
                st.download_button("⬇️ Descargar Excel",data=exportar_excel(res,"Scorpion — Plan Gratis"),
                    file_name=f"Scorpion_gratis_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with t2:
        picks=db_get_picks(str(date.today()),"gratis")
        if picks:
            for p in picks:
                cls="ap" if p.get("rango")=="A+" else "b"
                bl="🔒" in str(p.get("mercado",""))
                if bl: st.markdown(f'<div class="pick-box"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}<br><small>{p["mercado"]}</small></div>',unsafe_allow_html=True)
                else: st.markdown(f'<div class="pick-box {cls}"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}<br>📌 <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Edge:{p.get("edge","?")}% · Conf:{p.get("confianza","?")}%</div>',unsafe_allow_html=True)
        else: st.info("No hay picks publicados hoy.")
    if st.button("🚪 Cerrar sesion"): st.session_state.clear(); st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite V3 Pro 2025 · Solo uso informativo</div>',unsafe_allow_html=True)

def pantalla_pago(u, plan):
    hdr()
    ok,plan_v,dr=db_verificar_acceso(u["cedula"])
    pl_lbl={"dia":"📅 Plan Dia","semana":"📆 Plan Semana","mes":"👑 Plan Mes"}.get(plan,plan)
    st.markdown(f'👋 Hola **{u["nombre"]}** {pll(plan,dr)}',unsafe_allow_html=True)
    st.markdown("---")
    tabs_list=["🏟️ Por Liga","📁 Subir Archivo","📢 Picks"]
    if plan=="mes": tabs_list.append("📈 Historial")
    tabs=st.tabs(tabs_list)

    with tabs[0]:
        st.markdown("### Selecciona liga y periodo")
        c1,c2=st.columns([2,1])
        with c1:
            if plan=="mes":
                ligas_sel=st.multiselect("Una o mas ligas",list(LIGAS.keys()),default=[list(LIGAS.keys())[0]])
            else:
                ligas_sel=[st.selectbox("Liga",list(LIGAS.keys()))]
        with c2:
            if plan=="dia":
                fecha_s=st.date_input("Fecha",value=date.today()); modo="dia"
            else:
                ops=["Hoy","Dia especifico","Esta semana","Semana personalizada"]
                if plan in ("semana","mes"): ops.append("Dias de la semana")
                ml=st.radio("Periodo",ops)
                if ml=="Hoy": fecha_s=date.today(); modo="dia"
                elif ml=="Dia especifico": fecha_s=st.date_input("Fecha"); modo="dia"
                elif ml=="Esta semana":
                    hoy=date.today(); lu=hoy-timedelta(days=hoy.weekday())
                    fd=lu; fh=lu+timedelta(days=6); modo="rango"
                elif ml=="Semana personalizada":
                    fd=st.date_input("Desde",value=date.today())
                    fh=st.date_input("Hasta",value=date.today()+timedelta(days=6)); modo="rango"
                elif ml=="Dias de la semana":
                    dias_n=st.multiselect("Dias",["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado","Domingo"])
                    modo="dias"

        if st.button("🦂 Obtener y Analizar"):
            todos=[]
            with st.spinner("Obteniendo fixtures de API-Football..."):
                for ln in ligas_sel:
                    lid=LIGAS[ln]
                    if modo=="dia": fx=get_fixtures_dia(lid,str(fecha_s))
                    elif modo=="rango": fx=get_fixtures_rango(lid,str(fd),str(fh))
                    elif modo=="dias":
                        fx=[]; hoy=date.today(); lu=hoy-timedelta(days=hoy.weekday())
                        mp={"Lunes":0,"Martes":1,"Miercoles":2,"Jueves":3,"Viernes":4,"Sabado":5,"Domingo":6}
                        for d in dias_n:
                            fd2=lu+timedelta(days=mp.get(d,0))
                            fx+=get_fixtures_dia(lid,str(fd2))
                    todos+=[fx_to_partido(f) for f in fx]
                    time.sleep(0.3)
            if not todos:
                st.warning("No se encontraron partidos. La liga puede estar en receso o la temporada no ha comenzado.")
            else:
                prg=st.progress(0,"Analizando partidos...")
                res=analizar_lista(todos,usar_api=True,prog=prg)
                prg.progress(1.0,"Listo ✅")
                ap=sum(1 for r in res if r["rango"]=="A+")
                b=sum(1 for r in res if r["rango"]=="B")
                api_ok=sum(1 for r in res if "API" in r.get("fuente_l",""))
                conf_p=round(sum(r.get("confianza",0) for r in res)/len(res)) if res else 0
                c1,c2,c3,c4=st.columns(4)
                for col,(v,l) in zip([c1,c2,c3,c4],[(len(res),"Partidos"),(ap,"Rango A+"),(api_ok,"Datos reales"),(f"{conf_p}%","Confianza prom")]):
                    with col: st.markdown(f'<div class="mc"><div class="v">{v}</div><div class="l">{l}</div></div>',unsafe_allow_html=True)
                st.markdown("### 🏆 Top Picks")
                top=sorted([r for r in res if r["rango"] in ("A+","B")],
                           key=lambda x:(x.get("confianza",0),max(x.get("p1",0),x.get("p2",0))),reverse=True)[:8]
                for r in top:
                    st.markdown(f'{bdg(r["rango"])} **{r["local"]} vs {r["visitante"]}** ({r["liga"][:16]}) · {r["hora"]} · **{r["mk2"]}** · xG:{r["xl"]}-{r["xv"]} · O2.5:{r["over25"]}% · Conf:{r["confianza"]}%',unsafe_allow_html=True)
                if top:
                    st.markdown("### 🔬 Detalle de modelos")
                    for r in top[:3]:
                        with st.expander(f"{r['local']} vs {r['visitante']} — {r['rango']} ({r['confianza']}% conf)"):
                            dc1,dc2,dc3,dc4=st.columns(4)
                            with dc1: st.metric("Poisson",f'{r.get("p1_po",0):.1f}%')
                            with dc2: st.metric("Dixon-Coles",f'{r.get("p1_dc",0):.1f}%')
                            with dc3: st.metric("Monte Carlo",f'{r.get("p1_mc",0):.1f}%')
                            with dc4: st.metric("Elo",f'{r.get("p1_el",0):.1f}%')
                            st.markdown(f"**xG:** {r['xl']} vs {r['xv']} (Total: {r['xt']})")
                            st.markdown(f"**Marcadores mas probables:** {' | '.join([f'{k}({v}%)' for k,v in list(r.get('top_ex',{}).items())[:5]])}")
                            st.markdown(f"**Monte Carlo top:** {' | '.join([f'{k}({v}%)' for k,v in list(r.get('top_mc',{}).items())[:5]])}")
                fl=str(fecha_s) if modo=="dia" else f"{fd}_al_{fh}"
                xl=exportar_excel(res,f"Scorpion Elite — {pl_lbl}")
                st.download_button("⬇️ Descargar Excel completo",data=xl,
                    file_name=f"ScorpionElite_{fl}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                for r in res: db_guardar_historial(u["cedula"],r,r)

    with tabs[1]:
        st.info("Sube una captura de Sofascore, FlashScore o cualquier app. La IA lee los partidos automaticamente.")
        p=widget_archivo(key="pago_up")
        if p and st.button("🦂 Analizar archivo"):
            prg=st.progress(0,"Analizando...")
            res=analizar_lista(p,usar_api=True,prog=prg)
            prg.progress(1.0,"Listo ✅")
            xl=exportar_excel(res,"Scorpion Elite — Archivo Propio")
            st.download_button("⬇️ Descargar Excel",data=xl,
                file_name=f"ScorpionElite_custom_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tabs[2]:
        picks=db_get_picks(str(date.today()),plan)
        if picks:
            for p in picks:
                cls="ap" if p.get("rango")=="A+" else "b"
                bl="🔒" in str(p.get("mercado",""))
                if bl: st.markdown(f'<div class="pick-box"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}<br><small>{p["mercado"]}</small></div>',unsafe_allow_html=True)
                else: st.markdown(f'<div class="pick-box {cls}"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}<br>📌 <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Edge:{p.get("edge","?")}% · Conf:{p.get("confianza","?")}%{"<br><small>" + p["notas"] + "</small>" if p.get("notas") else ""}</div>',unsafe_allow_html=True)
        else: st.info("No hay picks publicados para hoy.")

    if plan=="mes" and len(tabs)>3:
        with tabs[3]:
            hist=db_get_historial(u["cedula"],30)
            if hist:
                for h in hist:
                    st.markdown(f'**{h["local"]} vs {h["visitante"]}** · {h["liga"]} · {h["fecha"]} · {h["mercado"]} · {h["rango"]}')
            else: st.info("No tienes analisis guardados aun.")

    if st.button("🚪 Cerrar sesion"): st.session_state.clear(); st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite V3 Pro 2025 · Solo uso informativo</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════
init_db()
if "li" not in st.session_state: st.session_state.li=False
if not st.session_state.li:
    pantalla_login()
else:
    u=st.session_state.get("u",{}); ced=st.session_state.get("ced","")
    ok,plan,dr=db_verificar_acceso(ced)
    if plan=="admin":              pantalla_admin()
    elif plan=="gratis":           pantalla_gratis(u)
    elif plan in("dia","semana","mes"): pantalla_pago(u,plan)
    else:
        st.error("Acceso vencido. Contacta al administrador.")
        if st.button("Volver"): st.session_state.clear(); st.rerun()
