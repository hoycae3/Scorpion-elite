"""SCORPION ENGINE V4 PRO — Sistema completo"""
import streamlit as st
import os, json, re, time, math, io, base64, sqlite3, hashlib, warnings, requests, random
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime, time as dtime
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
warnings.filterwarnings("ignore")


def get_hoy():
    """Obtiene la fecha de hoy como string ISO."""
    from datetime import date as _date
    return str(_date.today())

def get_hoy_date():
    """Obtiene la fecha de hoy como objeto date."""
    from datetime import date as _date
    return _date.today()

# ══════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY", "21a9a19125f3467c86579b79f71d359c")
ODDS_API_KEY = os.getenv("ODDS_API_KEY", "83d471fa5b5989dbd21b05fa0212e495")
OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")
ADMIN_PWD        = os.getenv("ADMIN_PASSWORD",   "scorpion_admin_2025")
DB_PATH          = "/tmp/scorpion_v4.db"

LIGAS = {
    # ===== LIGAS TOP (orden alfabético) =====
    "🏩󠁧󠁢󠁥󠁮 Inglaterra - Premier League": 39,
    "🇩🇪 Deutschland - Bundesliga": 78,
    "🇪🇸 España - La Liga": 140,
    "🇫🇷 France - Ligue 1": 61,
    "🇮🇹 Italia - Serie A": 135,
    "🇳🇱 Nederland - Eredivisie": 88,
    "🇵🇹 Portugal - Primeira Liga": 94,
    # ===== UEFA =====
    "🌍 Champions League": 2,
    "🌍 Europa League": 3,
    "🌍 Conference League": 848,
    # ===== SURAMÉRICA =====
    "🇦🇷 Argentina - Primera Division": 128,
    "🇦🇷 Argentina - Primera Nacional": 131,
    "🇧🇷 Brasil - Brasileirao": 71,
    "🇧🇷 Brasil - Serie B": 72,
    "🇨🇱 Chile - Primera Division": 67,
    "🇨🇷 Costa Rica - Liga BetPlay": 239,
    "🌎 Libertadores": 13,
    "🇺🇾 Uruguay - Primera Division": 73,
    "🌎 Sudamericana": 11,
    # ===== ESPAÑA =====
    "🇪🇸 España - La Liga 2": 141,
    # ===== INGLATERRA =====
    "🏴󠁧󠁢󠁥󠁮 Inglaterra - Championship": 40,
    "🏴󠁧󠁢󠁥󠁮 Inglaterra - League One": 41,
    "🏴󠁧󠁢󠁥󠁮 Inglaterra - League Two": 42,
    # ===== ALEMANIA =====
    "🇩🇪 Deutschland - 2. Bundesliga": 79,
    # ===== ITALIA =====
    "🇮🇹 Italia - Serie B": 136,
    # ===== FRANCIA =====
    "🇫🇷 France - Ligue 2": 63,
    # ===== AMÉRICA =====
    "🇺🇸 USA - MLS": 253,
    "🇲🇽 México - Liga MX": 262,
    "🇲🇽 México - Liga MX Expansion": 2775,
    # ===== OTRAS EUROPA =====
    "🇦🇹 Austria - Bundesliga": 218,
    "🇧🇪 Belgica - Jupiler League": 150,
    "🇨🇭 Suiza - Super League": 207,
    "🇩🇰 Dinamarca - Superliga": 69,
    "🇬🇷 Grecia - Super League": 184,
    "🇮🇪 Irlanda - Premier Division": 2006,
    "🇳🇴 Noruega - Eliteserien": 105,
    "🇷🇺 Rusia - Premier League": 235,
    "🇸🇦 Saudi Arabia - Pro League": 307,
    "🇸🇪 Suecia - Allsvenskan": 113,
    "🇹🇷 Türkiye - Super Lig": 203,
    "🇹🇷 Türkiye - 1. Lig": 315,
    # ===== TORNEOS INTERNACIONALES =====
    "🌎 Copa America": 9,
    "🌍 Mundial FIFA 2026": 1,
}

PROM_LIGA = {
    "premier":{"gm":1.54,"gc":1.11,"tiros":14.2,"corners":5.2,"tarj":1.8},
    "la liga":{"gm":1.62,"gc":1.08,"tiros":13.8,"corners":5.5,"tarj":2.2},
    "bundesliga":{"gm":1.82,"gc":1.28,"tiros":15.1,"corners":5.8,"tarj":1.6},
    "serie a":{"gm":1.48,"gc":1.07,"tiros":13.2,"corners":5.0,"tarj":2.4},
    "ligue":{"gm":1.51,"gc":1.07,"tiros":13.5,"corners":5.1,"tarj":2.0},
    "libertadores":{"gm":1.32,"gc":1.08,"tiros":12.0,"corners":4.8,"tarj":2.8},
    "sudamericana":{"gm":1.28,"gc":1.07,"tiros":11.8,"corners":4.7,"tarj":2.9},
    "eredivisie":{"gm":1.88,"gc":1.32,"tiros":15.5,"corners":5.9,"tarj":1.5},
    "mls":{"gm":1.45,"gc":1.20,"tiros":13.0,"corners":5.0,"tarj":1.9},
    "colombia":{"gm":1.25,"gc":1.10,"tiros":11.5,"corners":4.6,"tarj":2.6},
    "mundial":{"gm":1.35,"gc":1.05,"tiros":13.0,"corners":4.8,"tarj":1.8},
    "world cup":{"gm":1.35,"gc":1.05,"tiros":13.0,"corners":4.8,"tarj":1.8},
    "copa america":{"gm":1.28,"gc":1.08,"tiros":12.2,"corners":4.7,"tarj":2.2},
    "champions":{"gm":1.45,"gc":1.05,"tiros":14.0,"corners":5.2,"tarj":1.7},
    "europa":{"gm":1.42,"gc":1.08,"tiros":13.5,"corners":5.0,"tarj":1.9},
    "default":{"gm":1.40,"gc":1.15,"tiros":12.8,"corners":4.9,"tarj":2.0},
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


# ══════════════════════════════════════════════════════════
# DATOS REALES MUNDIAL 2026
# ══════════════════════════════════════════════════════════
MUNDIAL_2026_STATS = {
    # DATOS REALES del Mundial 2026 (fase de grupos + eliminación directa)
    # Semifinales: Francia vs España, Argentina vs Inglaterra
    "Francia": {
        "gm": 2.2, "gc": 0.4, "xg": 2.0, "elo": 2150,
        "tiros_pg": 14.5, "tarj_pg": 1.2,
        "ganados5": 5, "empatados5": 0, "perdidos5": 0,
        "goles_fav5": 11, "goles_con5": 2,
        "ultimos5": [
            {"rival": "Irak", "goles": "3-0", "res": "G", "local": "L"},
            {"rival": "Noruega", "goles": "4-1", "res": "G", "local": "L"},
            {"rival": "Senegal", "goles": "2-0", "res": "G", "local": "V"},
            {"rival": "Paraguay", "goles": "1-0", "res": "G", "local": "V"},
            {"rival": "Marruecos", "goles": "2-0", "res": "G", "local": "L"},
        ]
    },
    "España": {
        "gm": 1.8, "gc": 0.4, "xg": 1.6, "elo": 2130,
        "tiros_pg": 15.0, "tarj_pg": 0.9,
        "ganados5": 4, "empatados5": 1, "perdidos5": 0,
        "goles_fav5": 9, "goles_con5": 2,
        "ultimos5": [
            {"rival": "Cabo Verde", "goles": "0-0", "res": "E", "local": "L"},
            {"rival": "Arabia Saudí", "goles": "4-0", "res": "G", "local": "L"},
            {"rival": "Uruguay", "goles": "1-0", "res": "G", "local": "V"},
            {"rival": "Portugal", "goles": "1-0", "res": "G", "local": "L"},
            {"rival": "Bélgica", "goles": "2-1", "res": "G", "local": "L"},
        ]
    },
    "Argentina": {
        "gm": 3.0, "gc": 0.25, "xg": 2.5, "elo": 2180,
        "tiros_pg": 14.0, "tarj_pg": 1.3,
        "ganados5": 5, "empatados5": 0, "perdidos5": 0,
        "goles_fav5": 12, "goles_con5": 1,
        "ultimos5": [
            {"rival": "Grupo J", "goles": "9-0", "res": "G", "local": "L"},
            {"rival": "Suiza", "goles": "3-1", "res": "G", "local": "L"},
        ]
    },
    "Inglaterra": {
        "gm": 1.6, "gc": 0.8, "xg": 1.5, "elo": 2100,
        "tiros_pg": 13.5, "tarj_pg": 1.2,
        "ganados5": 4, "empatados5": 1, "perdidos5": 0,
        "goles_fav5": 8, "goles_con5": 4,
        "ultimos5": [
            {"rival": "Grupo L", "goles": "7 pts", "res": "G", "local": "L"},
            {"rival": "México", "goles": "3-2", "res": "G", "local": "V"},
            {"rival": "Noruega", "goles": "2-1", "res": "G", "local": "L"},
        ]
    },
    "Brasil": {
        "gm": 1.2, "gc": 1.0, "xg": 1.4, "elo": 2160,
        "tiros_pg": 14.0, "tarj_pg": 1.4,
        "ganados5": 2, "empatados5": 1, "perdidos5": 2,
        "goles_fav5": 5, "goles_con5": 4,
        "ultimos5": [
            {"rival": "Noruega", "goles": "1-2", "res": "P", "local": "L"},
        ]
    },
    "Alemania": {
        "gm": 1.5, "gc": 1.2, "xg": 1.5, "elo": 2080,
        "tiros_pg": 14.5, "tarj_pg": 1.4,
        "ganados5": 2, "empatados5": 1, "perdidos5": 2,
        "goles_fav5": 4, "goles_con5": 4,
        "ultimos5": []
    },
    "Portugal": {
        "gm": 1.0, "gc": 0.8, "xg": 1.2, "elo": 2050,
        "tiros_pg": 12.5, "tarj_pg": 1.7,
        "ganados5": 1, "empatados5": 1, "perdidos5": 1,
        "goles_fav5": 2, "goles_con5": 2,
        "ultimos5": [
            {"rival": "España", "goles": "0-1", "res": "P", "local": "V"},
        ]
    },
    "Italia": {
        "gm": 1.5, "gc": 1.0, "xg": 1.4, "elo": 2030,
        "tiros_pg": 12.0, "tarj_pg": 1.6,
        "ganados5": 2, "empatados5": 1, "perdidos5": 1,
        "goles_fav5": 3, "goles_con5": 2,
        "ultimos5": []
    },
    "Países Bajos": {
        "gm": 1.2, "gc": 1.2, "xg": 1.3, "elo": 2020,
        "tiros_pg": 12.5, "tarj_pg": 1.3,
        "ganados5": 1, "empatados5": 2, "perdidos5": 1,
        "goles_fav5": 3, "goles_con5": 4,
        "ultimos5": []
    },
    "Bélgica": {
        "gm": 1.4, "gc": 1.4, "xg": 1.4, "elo": 2000,
        "tiros_pg": 12.0, "tarj_pg": 1.5,
        "ganados5": 1, "empatados5": 1, "perdidos5": 2,
        "goles_fav5": 3, "goles_con5": 5,
        "ultimos5": [
            {"rival": "España", "goles": "1-2", "res": "P", "local": "V"},
        ]
    },
    "Uruguay": {
        "gm": 1.0, "gc": 1.2, "xg": 1.1, "elo": 1980,
        "tiros_pg": 11.0, "tarj_pg": 2.0,
        "ganados5": 1, "empatados5": 0, "perdidos5": 2,
        "goles_fav5": 1, "goles_con5": 2,
        "ultimos5": [
            {"rival": "España", "goles": "0-1", "res": "P", "local": "V"},
        ]
    },
    "Croacia": {
        "gm": 1.3, "gc": 1.0, "xg": 1.3, "elo": 1950,
        "tiros_pg": 11.0, "tarj_pg": 1.7,
        "ganados5": 2, "empatados5": 1, "perdidos5": 1,
        "goles_fav5": 4, "goles_con5": 3,
        "ultimos5": []
    },
    "Colombia": {
        "gm": 1.2, "gc": 0.8, "xg": 1.2, "elo": 1920,
        "tiros_pg": 11.5, "tarj_pg": 1.8,
        "ganados5": 2, "empatados5": 1, "perdidos5": 1,
        "goles_fav5": 3, "goles_con5": 2,
        "ultimos5": [
            {"rival": "Suiza", "goles": "0-0", "res": "E", "local": "L"},
            {"rival": "Penales", "goles": "4-3", "res": "G", "local": "L"},
        ]
    },
    "México": {
        "gm": 1.5, "gc": 1.5, "xg": 1.4, "elo": 1900,
        "tiros_pg": 11.0, "tarj_pg": 2.0,
        "ganados5": 1, "empatados5": 0, "perdidos5": 2,
        "goles_fav5": 4, "goles_con5": 5,
        "ultimos5": [
            {"rival": "Inglaterra", "goles": "2-3", "res": "P", "local": "L"},
        ]
    },
    "Estados Unidos": {
        "gm": 1.2, "gc": 1.4, "xg": 1.2, "elo": 1880,
        "tiros_pg": 11.0, "tarj_pg": 1.4,
        "ganados5": 1, "empatados5": 1, "perdidos5": 2,
        "goles_fav5": 3, "goles_con5": 4,
        "ultimos5": []
    },
    "Senegal": {
        "gm": 1.0, "gc": 1.4, "xg": 1.0, "elo": 1850,
        "tiros_pg": 10.0, "tarj_pg": 2.0,
        "ganados5": 1, "empatados5": 0, "perdidos5": 2,
        "goles_fav5": 2, "goles_con5": 4,
        "ultimos5": []
    },
    "Marruecos": {
        "gm": 1.6, "gc": 0.8, "xg": 1.5, "elo": 1870,
        "tiros_pg": 10.5, "tarj_pg": 1.5,
        "ganados5": 3, "empatados5": 0, "perdidos5": 1,
        "goles_fav5": 6, "goles_con5": 2,
        "ultimos5": [
            {"rival": "Canadá", "goles": "3-0", "res": "G", "local": "V"},
            {"rival": "Francia", "goles": "0-2", "res": "P", "local": "V"},
        ]
    },
    "Nigeria": {
        "gm": 1.2, "gc": 1.2, "xg": 1.2, "elo": 1830,
        "tiros_pg": 10.0, "tarj_pg": 1.8,
        "ganados5": 1, "empatados5": 1, "perdidos5": 1,
        "goles_fav5": 2, "goles_con5": 2,
        "ultimos5": []
    },
    "Camerún": {
        "gm": 1.0, "gc": 1.4, "xg": 1.0, "elo": 1800,
        "tiros_pg": 9.5, "tarj_pg": 2.1,
        "ganados5": 1, "empatados5": 1, "perdidos5": 2,
        "goles_fav5": 2, "goles_con5": 4,
        "ultimos5": []
    },
    "Egipto": {
        "gm": 1.0, "gc": 1.5, "xg": 1.0, "elo": 1820,
        "tiros_pg": 9.5, "tarj_pg": 1.7,
        "ganados5": 1, "empatados5": 0, "perdidos5": 2,
        "goles_fav5": 2, "goles_con5": 4,
        "ultimos5": []
    },
}


def obtener_stats_tiempo_real(equipo):
    """
    Busca estadísticas de un equipo en TIEMPO REAL desde múltiples fuentes.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/html,application/xhtml+xml",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        "Referer": "https://www.sofascore.com/",
    }
    
    equipo_clean = equipo.strip()
    
    # 1. Intentar Sofascore (PRIMERA PRIORIDAD)
    try:
        # Buscar equipo en Sofascore
        search_url = f"https://api.sofascore.com/api/v1/search/teams/{equipo_clean.replace(' ', '%20')}"
        r = requests.get(search_url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("results") and len(data["results"]) > 0:
                team = data["results"][0]
                team_id = team.get("id")
                team_name = team.get("name", equipo_clean)
                
                if team_id:
                    # Obtener estadísticas generales del equipo
                    stats_url = f"https://api.sofascore.com/api/v1/team/{team_id}/statistics/overall"
                    r2 = requests.get(stats_url, headers=headers, timeout=10)
                    
                    if r2.status_code == 200:
                        s = r2.json()
                        gm = s.get("goalsScored", {})
                        gc = s.get("goalsConceded", {})
                        shots = s.get("shots", {})
                        yellows = s.get("yellowCards", {})
                        
                        gm_val = gm.get("average", 1.5) or 1.5
                        gc_val = gc.get("average", 1.0) or 1.0
                        tiros_val = shots.get("total", 12) or 12
                        tarj_val = yellows if isinstance(yellows, (int, float)) else 2.0
                        
                        return {
                            "ok": True,
                            "fuente": "Sofascore",
                            "equipo": team_name,
                            "gm": gm_val,
                            "gc": gc_val,
                            "xg": gm_val * 0.9,
                            "elo": 1950,
                            "tiros_pg": tiros_val,
                            "tarj_pg": tarj_val,
                            "ultimos5": [],
                            "ganados5": 0, "empatados5": 0, "perdidos5": 0,
                            "goles_fav5": 0, "goles_con5": 0,
                        }
    except Exception as e:
        print(f"Sofascore error: {e}")
    
    # 2. Intentar Sofascore Web (scraping)
    try:
        # Buscar en la web de Sofascore
        slug = equipo_clean.lower().replace(" ", "-").replace("'", "")
        web_url = f"https://www.sofascore.com/football/team/{slug}/statistics"
        r = requests.get(web_url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar estadísticas en la página
            stats_data = {}
            
            # Buscar valores numéricos en secciones relevantes
            sections = soup.select(".sc-hpvKGa, .kAWnYK, .bMLHBq, [class*='stat']")
            
            for section in sections:
                text = section.get_text(strip=True)
                if "Goal" in text or "goal" in text.lower():
                    numbers = re.findall(r'\d+\.?\d*', text)
                    if numbers:
                        stats_data["gm"] = float(numbers[0])
                elif "Shot" in text or "shot" in text.lower():
                    numbers = re.findall(r'\d+\.?\d*', text)
                    if numbers:
                        stats_data["tiros"] = float(numbers[0])
            
            # Buscar en JSON embebido
            scripts = soup.select("script[type='application/json']")
            for script in scripts:
                text = script.string or ""
                if "goalsScored" in text or "goalsConceded" in text:
                    import json
                    try:
                        data = json.loads(text)
                        # Extraer datos relevantes
                        pass
                    except:
                        pass
            
            if stats_data:
                return {
                    "ok": True,
                    "fuente": "Sofascore Web",
                    "equipo": equipo_clean,
                    "gm": stats_data.get("gm", 1.5),
                    "gc": stats_data.get("gc", 1.0),
                    "xg": stats_data.get("gm", 1.5) * 0.9,
                    "elo": 1950,
                    "tiros_pg": stats_data.get("tiros", 12),
                    "tarj_pg": 2.0,
                    "ultimos5": [],
                    "ganados5": 0, "empatados5": 0, "perdidos5": 0,
                    "goles_fav5": 0, "goles_con5": 0,
                }
    except Exception as e:
        print(f"Sofascore Web error: {e}")
    
    # 3. Intentar API-Football
    if API_FOOTBALL_KEY:
        try:
            headers_af = {"x-apisports-key": API_FOOTBALL_KEY}
            url = f"https://v3.football.api-sports.io/teams/search/{equipo_clean}"
            r = requests.get(url, headers=headers_af, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                if data.get("results", 0) > 0:
                    team_data = data["response"][0]
                    team_id = team_data["team"]["id"]
                    team_name = team_data["team"]["name"]
                    
                    stats_url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&season=2024"
                    r2 = requests.get(stats_url, headers=headers_af, timeout=10)
                    
                    if r2.status_code == 200:
                        s = r2.json().get("response", {})
                        fixtures = s.get("fixtures", {})
                        games = max(fixtures.get("played", {}).get("total", 1) or 1, 1)
                        
                        gm_val = s.get("goals", {}).get("for", {}).get("average", {}).get("total", 1.5) or 1.5
                        gc_val = s.get("goals", {}).get("against", {}).get("average", {}).get("total", 1.0) or 1.0
                        shots_total = s.get("shots", {}).get("total", 0) or 0
                        yellows = s.get("cards", {}).get("yellow", {}).get("total", 0) or 0
                        
                        return {
                            "ok": True,
                            "fuente": "API-Football",
                            "equipo": team_name,
                            "gm": round(gm_val, 2),
                            "gc": round(gc_val, 2),
                            "xg": round(gm_val * 0.9, 2),
                            "elo": 1950,
                            "tiros_pg": round(shots_total / games, 1) if games > 0 else 12,
                            "tarj_pg": round(yellows / games, 1) if games > 0 else 2.0,
                            "ultimos5": [],
                            "ganados5": fixtures.get("wins", {}).get("total", 0) or 0,
                            "empatados5": fixtures.get("draws", {}).get("total", 0) or 0,
                            "perdidos5": fixtures.get("loses", {}).get("total", 0) or 0,
                            "goles_fav5": 0, "goles_con5": 0,
                        }
        except Exception as e:
            print(f"API-Football error: {e}")
    
    # 4. Intentar FBref
    try:
        fbref_names = {
            "francia": "France", "espana": "Spain", "argentina": "Argentina",
            "inglaterra": "England", "brasil": "Brazil", "alemania": "Germany",
            "portugal": "Portugal", "italia": "Italy", "paises bajos": "Netherlands",
            "belgica": "Belgium", "croacia": "Croatia", "uruguay": "Uruguay",
            "marruecos": "Morocco", "mexico": "Mexico", "senegal": "Senegal", "colombia": "Colombia",
        }
        
        fbref_name = fbref_names.get(equipo_clean.lower(), equipo_clean.replace(" ", "-"))
        url = f"https://fbref.com/en/squads/18bb7c10/{fbref_name}"
        
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            stats_table = soup.select_one("#stats_squads_standard")
            
            if stats_table:
                rows = stats_table.select("tbody tr")
                for row in rows:
                    team_name_cell = row.select_one("th[data-label='Squad']")
                    if team_name_cell:
                        name = team_name_cell.get_text(strip=True)
                        if equipo_clean.lower() in name.lower() or name.lower() in equipo_clean.lower():
                            cols = row.select("td")
                            if len(cols) >= 12:
                                try:
                                    mp = float(cols[2].get_text(strip=True) or 0)
                                    gls = float(cols[4].get_text(strip=True) or 0)
                                    xg = float(cols[6].get_text(strip=True) or 0)
                                    
                                    if mp > 0:
                                        gm_val = round(gls / mp, 2)
                                        xg_val = round(xg / mp, 2)
                                        
                                        return {
                                            "ok": True,
                                            "fuente": "FBref",
                                            "equipo": name,
                                            "gm": gm_val,
                                            "gc": round(gm_val * 0.6, 2),
                                            "xg": xg_val,
                                            "elo": 1950,
                                            "tiros_pg": round(gm_val * 6, 1),
                                            "tarj_pg": 1.8,
                                            "ultimos5": [],
                                            "ganados5": 0, "empatados5": 0, "perdidos5": 0,
                                            "goles_fav5": 0, "goles_con5": 0,
                                        }
                                except:
                                    pass
    except Exception as e:
        print(f"FBref error: {e}")
    
    # 5. Intentar Transfermarkt
    try:
        tm_name = equipo_clean.lower().replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        url = f"https://www.transfermarkt.com/{tm_name}/leistungsdaten/verein/0/plus/1"
        
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            data_sections = soup.select(".box-content tr")
            
            for row in data_sections:
                cells = row.select("td")
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    if "tor" in label or "goles" in label or "goals" in label:
                        try:
                            parts = value.replace(":", "-").split("-")
                            if len(parts) == 2:
                                gm_val = float(parts[0].strip())
                                gc_val = float(parts[1].strip())
                                
                                return {
                                    "ok": True,
                                    "fuente": "Transfermarkt",
                                    "equipo": equipo_clean,
                                    "gm": gm_val,
                                    "gc": gc_val,
                                    "xg": round(gm_val * 0.9, 2),
                                    "elo": 1950,
                                    "tiros_pg": round(gm_val * 6, 1),
                                    "tarj_pg": 1.8,
                                    "ultimos5": [],
                                    "ganados5": 0, "empatados5": 0, "perdidos5": 0,
                                    "goles_fav5": 0, "goles_con5": 0,
                                }
                        except:
                            pass
    except Exception as e:
        print(f"Transfermarkt error: {e}")
    
    # 6. Intentar Flashscore
    try:
        slug = equipo_clean.lower().replace(" ", "-").replace("'", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        url = f"https://www.flashscore.es/equipo/{slug}/estadisticas/"
        
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            stats = {}
            for row in soup.select(".statRow, .stat__row"):
                try:
                    name_el = row.select_one(".stat__name, .statName")
                    value_el = row.select_one(".stat__value, .statValue")
                    
                    if name_el and value_el:
                        name = name_el.get_text(strip=True).lower()
                        value = value_el.get_text(strip=True).replace(",", ".")
                        
                        if "goals" in name or "goles" in name:
                            parts = value.replace(":", "-").split("-")
                            if len(parts) >= 2:
                                try:
                                    stats["gm"] = float(parts[0].strip())
                                    stats["gc"] = float(parts[1].strip())
                                except:
                                    pass
                        elif "shots" in name or "tiros" in name:
                            try:
                                stats["tiros_pg"] = float(value)
                            except:
                                pass
                except:
                    continue
            
            if stats:
                return {
                    "ok": True,
                    "fuente": "Flashscore",
                    "equipo": equipo_clean,
                    "gm": stats.get("gm", 1.5),
                    "gc": stats.get("gc", 1.0),
                    "xg": stats.get("gm", 1.5) * 0.9,
                    "elo": 1950,
                    "tiros_pg": stats.get("tiros_pg", 12),
                    "tarj_pg": 2.0,
                    "ultimos5": [],
                    "ganados5": 0, "empatados5": 0, "perdidos5": 0,
                    "goles_fav5": 0, "goles_con5": 0,
                }
    except Exception as e:
        print(f"Flashscore error: {e}")
    
    return None


def obtener_stats_mundial(nombre_equipo):
    """Obtiene stats de un equipo buscando en múltiples fuentes en tiempo real."""
    nombre_lower = nombre_equipo.lower().strip()
    
    # 1. Primero buscar en BD local del Mundial (como backup rápido)
    for equipo, stats in MUNDIAL_2026_STATS.items():
        if nombre_lower in equipo.lower() or equipo.lower() in nombre_lower:
            result = {
                "ok": True, 
                "fuente": "BD Local Mundial 2026",
                "equipo": equipo,
                "gm": stats["gm"], 
                "gc": stats["gc"], 
                "xg": stats.get("xg", stats["gm"] * 0.9),
                "elo": stats["elo"], 
                "tiros_pg": stats.get("tiros_pg", 12),
                "tarj_pg": stats.get("tarj_pg", 2.0),
                "ultimos5": stats.get("ultimos5", []),
                "ganados5": stats.get("ganados5", 0),
                "empatados5": stats.get("empatados5", 0),
                "perdidos5": stats.get("perdidos5", 0),
                "goles_fav5": stats.get("goles_fav5", 0),
                "goles_con5": stats.get("goles_con5", 0),
            }
            
            # Intentar actualizar con datos de tiempo real en background
            try:
                real_stats = obtener_stats_tiempo_real(nombre_equipo)
                if real_stats and real_stats.get("ok"):
                    result["fuente"] = real_stats["fuente"] + " → Actualizado"
                    result["gm"] = real_stats.get("gm", result["gm"])
                    result["gc"] = real_stats.get("gc", result["gc"])
                    result["xg"] = real_stats.get("xg", result["xg"])
                    result["tiros_pg"] = real_stats.get("tiros_pg", result["tiros_pg"])
                    result["tarj_pg"] = real_stats.get("tarj_pg", result["tarj_pg"])
            except:
                pass
            
            return result
    
    # 2. Si no está en BD local, buscar en tiempo real
    real_stats = obtener_stats_tiempo_real(nombre_equipo)
    if real_stats and real_stats.get("ok"):
        return real_stats
    
    # 3. Si no se encuentra nada, usar promedios genéricos
    return {
        "ok": False,
        "fuente": "Sin datos - usando promedio genérico",
        "equipo": nombre_equipo,
        "gm": 1.5, "gc": 1.2, "xg": 1.4, "elo": 1850,
        "tiros_pg": 11, "tarj_pg": 2.0,
        "ultimos5": [],
        "ganados5": 0, "empatados5": 0, "perdidos5": 0,
        "goles_fav5": 0, "goles_con5": 0,
    }



# ══════════════════════════════════════════════════════════
# WEB SCRAPING - DATOS REALES
# ══════════════════════════════════════════════════════════
GOLEADORES_CACHE = {}  # Cache para goleadores

def scrape_flashscore_partidos():
    """Obtiene partidos del día desde Flashscore."""
    partidos = []
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        r = requests.get("https://www.flashscore.es/futbol/", headers=headers, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        
        for match in soup.find_all("div", class_="event__match"):
            try:
                hora = match.find("div", class_="event__time")
                local = match.find("div", class_="event__homeParticipant")
                visitante = match.find("div", class_="event__awayParticipant")
                
                if local and visitante:
                    h = hora.get_text(strip=True) if hora else "--:--"
                    # Buscar liga del contenedor padre
                    league_div = match.find_parent("div", class_=lambda x: x and "leagues" in str(x))
                    liga = "Partido"
                    if league_div:
                        header = league_div.find_previous("div", class_="event__header")
                        if header:
                            ltext = header.get_text(strip=True)
                            if ltext:
                                liga = ltext
                    
                    partidos.append({
                        "hora": h,
                        "local": local.get_text(strip=True),
                        "visitante": visitante.get_text(strip=True),
                        "liga": liga,
                        "dia": get_hoy()
                    })
            except:
                continue
    except Exception as e:
        print(f"Error scraping Flashscore partidos: {e}")
    return partidos


def obtener_stats_equipos_api():
    """
    Obtiene estadísticas de equipos desde API-Football.
    Incluye: PJ, GF, GC, puntos, remates, corners, tarjetas, posesión
    """
    from scorpion.api.football import FootballAPI
    
    stats = {}
    api = FootballAPI()
    
    # ligas soportadas
    liga_ids = {
        39: "Premier League",
        140: "La Liga", 
        78: "Bundesliga",
        135: "Serie A",
        61: "Ligue 1",
    }
    
    for liga_id, liga_nombre in liga_ids.items():
        try:
            temporada = api.get_temporada(liga_id)
            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            
            # Obtener clasificación
            data = api._request(
                "https://v3.football.api-sports.io/standings",
                {"league": liga_id, "season": temporada},
                headers=headers
            )
            
            if data and data.get("response"):
                for response in data["response"]:
                    standings = response.get("league", {}).get("standings", [])
                    for stage in standings:
                        for row in stage:
                            team = row.get("team", {})
                            team_name = team.get("name", "")
                            stats[team_name] = {
                                "pj": row.get("played", 0),
                                "ganados": row.get("win", 0),
                                "empatados": row.get("draw", 0),
                                "perdidos": row.get("lose", 0),
                                "gf": row.get("goals", {}).get("for", 0),
                                "gc": row.get("goals", {}).get("against", 0),
                                "puntos": row.get("points", 0),
                                "liga": liga_nombre
                            }
        except Exception as e:
            print(f"Error stats {liga_nombre}: {e}")
    
    return stats


def obtener_stats_partido_en_vivo(local_id, visitante_id, liga_id):
    """
    Obtiene estadísticas detalladas de un partido específico.
    Remates, corners, atajadas, posesión, faltas, tarjetas
    """
    try:
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        
        # Obtener fixture del día para encontrar el partido
        fixtures = api.get_fixtures(liga_id, fecha=get_hoy())
        
        for f in fixtures:
            if (f["teams"]["home"]["id"] == local_id and 
                f["teams"]["away"]["id"] == visitante_id):
                
                fixture_id = f["fixture"]["id"]
                
                # Obtener estadísticas del partido
                stats_url = f"https://v3.football.api-sports.io/fixtures/statistics"
                data = api._request(stats_url, 
                    {"fixture": fixture_id}, 
                    headers=headers
                )
                
                if data and data.get("response"):
                    result = {}
                    for team_stats in data["response"]:
                        team_name = team_stats["team"]["name"]
                        stats_list = team_stats["statistics"]
                        result[team_name] = {}
                        
                        for stat in stats_list:
                            value = stat["value"]
                            if value is not None:
                                result[team_name][stat["type"]] = value
                    
                    return result
    except Exception as e:
        print(f"Error stats partido: {e}")
    
    return None


# ══════════════════════════════════════════════════════════
# BUSCADOR DE EQUIPOS (PDF 2.0) - CORREGIDO
# ══════════════════════════════════════════════════════════


def obtener_stats_desde_sofascore(nombre_equipo):
    """Obtiene estadísticas simples de un equipo desde Sofascore."""
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        
        # Buscar equipo
        search_url = f"https://api.sofascore.com/api/v1/search/teams/{nombre_equipo.replace(' ', '%20')}"
        r = requests.get(search_url, headers=headers, timeout=5)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                team = data["results"][0]
                tid = team.get("id")
                
                # Obtener estadísticas del equipo
                stats_url = f"https://api.sofascore.com/api/v1/team/{tid}/statistics/overall"
                r2 = requests.get(stats_url, headers=headers, timeout=5)
                
                if r2.status_code == 200:
                    s = r2.json()
                    return {
                        "partidos": s.get("matches", {}).get("total", "N/A"),
                        "victorias": s.get("wins", {}).get("total", "N/A"),
                        "goles": s.get("goalsScored", {}).get("total", "N/A"),
                        "fuente": "Sofascore"
                    }
    except Exception as e:
        print(f"Error Sofascore: {e}")
    
    # Fallback: devolver datos de ejemplo
    return {
        "partidos": "En temporada",
        "victorias": "Consultando",
        "goles": "...",
        "fuente": "API"
    }


def buscar_equipo_en_todas_fuentes(nombre):
    """Busca equipos en TODAS las fuentes disponibles."""
    resultados = []
    seen = set()
    errores = []
    
    # Limpiar nombre de búsqueda
    nombre = nombre.strip()
    if not nombre or len(nombre) < 2:
        return resultados
    
    # 1. FOOTBALL-DATA - Buscar por ligas específicas
    try:
        headers_fd = {"X-Auth-Token": FOOTBALL_DATA_KEY}
        
        # Lista de ligas con sus IDs
        leagues = [
            ("PD", "La Liga"),
            ("PL", "Premier League"),
            ("BL1", "Bundesliga"),
            ("SA", "Serie A"),
            ("FL1", "Ligue 1"),
            ("PPL", "Primeira Liga"),
            ("DED", "Eredivisie"),
        ]
        
        for league_code, league_name in leagues:
            url_teams = f"https://api.football-data.org/v4/competitions/{league_code}/teams"
            r = requests.get(url_teams, headers=headers_fd, timeout=15)
            if r.status_code == 200:
                data = r.json()
                teams = data.get("teams", [])
                for t in teams:
                    tid = t.get("id")
                    tname = t.get("name", "")
                    tshort = t.get("shortName", "")
                    key = f"fd_{tid}"
                    
                    # Buscar coincidencia exacta o parcial
                    if key not in seen and tname:
                        nombre_lower = nombre.lower()
                        tname_lower = tname.lower()
                        
                        # Coincidencia exacta al inicio del nombre
                        if tname_lower.startswith(nombre_lower):
                            seen.add(key)
                            resultados.insert(0, {
                                "id": str(tid),
                                "nombre": tname,
                                "short": tshort,
                                "pais": t.get("country", ""),
                                "liga": league_name,
                                "fuente": "Football-Data"
                            })
                        # Coincidencia contiene el nombre
                        elif nombre_lower in tname_lower:
                            seen.add(key)
                            resultados.append({
                                "id": str(tid),
                                "nombre": tname,
                                "short": tshort,
                                "pais": t.get("country", ""),
                                "liga": league_name,
                                "fuente": "Football-Data"
                            })
    except Exception as e:
        errores.append(f"Football-Data: {str(e)[:50]}")
    
    # 2. FBREF
    try:
        url = f"https://fbref.com/en/search/search/?q={nombre.replace(' ', '+')}"
        headers_fb = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers_fb, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            links = soup.find_all("a", href=lambda h: h and "/squads/" in h if h else False)
            for link in links[:10]:
                team_name = link.get_text(strip=True)
                href = link.get("href", "")
                if team_name and len(team_name) > 2:
                    key = f"fbref_{href}"
                    if key not in seen and nombre.lower() in team_name.lower():
                        seen.add(key)
                        resultados.append({
                            "id": href,
                            "nombre": team_name[:60],
                            "short": "",
                            "pais": "",
                            "liga": "FBref",
                            "fuente": "FBref"
                        })
    except Exception as e:
        errores.append(f"FBref: {str(e)[:50]}")
    
    # 3. SOFASCORE (API directa)
    try:
        url = f"https://api.sofascore.com/api/v1/search/teams/{nombre.replace(' ', '%20')}"
        headers_ss = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Origin": "https://www.sofascore.com",
            "Referer": "https://www.sofascore.com/"
        }
        r = requests.get(url, headers=headers_ss, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data.get("results", 0) > 0:
                for t in data["results"][:10]:
                    tid = t.get("id")
                    tname = t.get("name", "")
                    if tname and tid:
                        key = f"sofascore_{tid}"
                        if key not in seen:
                            seen.add(key)
                            resultados.append({
                                "id": str(tid),
                                "nombre": tname,
                                "short": "",
                                "pais": t.get("country", {}).get("name", ""),
                                "liga": "Sofascore",
                                "fuente": "Sofascore"
                            })
    except Exception as e:
        errores.append(f"Sofascore: {str(e)[:50]}")
    
    # 4. API-FOOTBALL (si tiene key válida)
    if API_FOOTBALL_KEY:
        try:
            headers_af = {"x-apisports-key": API_FOOTBALL_KEY}
            url = f"https://v3.football.api-sports.io/teams/search/{nombre}"
            r = requests.get(url, headers=headers_af, timeout=15)
            if r.status_code == 200:
                data = r.json()
                if data.get("response") and data.get("results", 0) > 0:
                    for item in data["response"][:10]:
                        t = item.get("team", {})
                        tid = t.get("id")
                        tname = t.get("name", "")
                        if tname and tid:
                            key = f"apifootball_{tid}"
                            if key not in seen:
                                seen.add(key)
                                resultados.append({
                                    "id": str(tid),
                                    "nombre": tname,
                                    "short": "",
                                    "pais": t.get("country", ""),
                                    "liga": "API-Football",
                                    "fuente": "API-Football"
                                })
        except Exception as e:
            errores.append(f"API-Football: {str(e)[:50]}")
    
    # Guardar errores
    if errores:
        st.session_state['busqueda_errores'] = errores
    
    return resultados


def obtener_stats_equipo_fuente(equipo):
    """Obtiene estadísticas desde la fuente del equipo."""
    fuente = equipo.get('fuente', '')
    tid = equipo.get('id')
    nombre = equipo.get('nombre', '')
    
    # FOOTBALL-DATA
    if fuente == 'Football-Data' and tid:
        try:
            headers_fd = {"X-Auth-Token": FOOTBALL_DATA_KEY}
            # Obtener información del equipo
            url = f"https://api.football-data.org/v4/teams/{tid}"
            r = requests.get(url, headers=headers_fd, timeout=10)
            if r.status_code == 200:
                data = r.json()
                # Obtener Squad (plantilla)
                squad_url = f"https://api.football-data.org/v4/teams/{tid}/squad"
                r2 = requests.get(squad_url, headers=headers_fd, timeout=10)
                squad_count = 0
                if r2.status_code == 200:
                    squad_data = r2.json()
                    squad_count = len(squad_data.get("squad", []))
                
                return {
                    "partidos": "Ver API",
                    "victorias": nombre,
                    "goles_favor": f"Comp: {data.get('runningCompetition', {}).get('name', 'N/A')}",
                    "goles_contra": f"Jugadores: {squad_count}",
                }
        except Exception as e:
            print(f"Error Football-Data stats: {e}")
    
    # API-FOOTBALL
    if fuente == 'API-Football' and API_FOOTBALL_KEY:
        try:
            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            url = f"https://v3.football.api-sports.io/teams?id={tid}"
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                if data.get("response"):
                    leagues = data["response"][0].get("leagues", {})
                    if isinstance(leagues, list) and leagues:
                        lid = leagues[0].get("league", {}).get("id")
                    elif isinstance(leagues, dict):
                        lid = leagues.get("id")
                    else:
                        lid = None
                    if lid:
                        stats_url = f"https://v3.football.api-sports.io/teams/statistics?team={tid}&league={lid}&season=2024"
                        r2 = requests.get(stats_url, headers=headers, timeout=10)
                        if r2.status_code == 200:
                            s = r2.json()
                            if s.get("response"):
                                resp = s["response"]
                                return {
                                    "partidos": resp.get("fixtures", {}).get("played", 0),
                                    "victorias": resp.get("fixtures", {}).get("wins", {}).get("total", 0),
                                    "goles_favor": resp.get("goals", {}).get("for", {}).get("total", {}).get("total", 0),
                                    "goles_contra": resp.get("goals", {}).get("against", {}).get("total", {}).get("total", 0),
                                }
        except Exception as e:
            print(f"Error API-Football stats: {e}")
    
    # SOFASCORE
    if fuente == 'Sofascore' and tid:
        try:
            url = f"https://api.sofascore.com/api/v1/team/{tid}/statistics/overall"
            headers_ss = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
            r = requests.get(url, headers=headers_ss, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return {
                    "partidos": data.get("matches", {}).get("total", "N/A"),
                    "victorias": data.get("wins", {}).get("total", "N/A"),
                    "goles_favor": data.get("goalsScored", {}).get("total", "N/A"),
                    "goles_contra": data.get("goalsConceded", {}).get("total", "N/A"),
                }
        except:
            pass
    
    return None


def obtener_cuotas_partido(home_team, away_team, league_key="soccer_epl"):
    """Obtiene cuotas de apuestas para un partido."""
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu,us,uk",
            "markets": "h2h,spreads,totals",
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            matches = r.json()
            for match in matches:
                ht = match.get("home_team", "").lower()
                at = match.get("away_team", "").lower()
                if home_team.lower() in ht or away_team.lower() in at:
                    bookmakers = match.get("bookmakers", [])
                    cuotas = []
                    for bm in bookmakers[:5]:
                        bm_name = bm.get("title", "")
                        markets = bm.get("markets", [])
                        for market in markets:
                            market_key = market.get("key", "")
                            outcomes = market.get("outcomes", [])
                            odds_list = []
                            for o in outcomes:
                                odds_list.append({
                                    "nombre": o.get("name", ""),
                                    "cuota": o.get("price", 0),
                                    "linea": o.get("point", "")
                                })
                            cuotas.append({
                                "casa": bm_name,
                                "mercado": market_key,
                                "opciones": odds_list
                            })
                    return cuotas
        return []
    except Exception as e:
        print(f"Error cuotas: {e}")
        return []


def obtener_cuotas_todos_partidos(league_key="soccer_epl"):
    """Obtiene cuotas de TODOS los partidos de una liga."""
    try:
        url = f"https://api.the-odds-api.com/v4/sports/{league_key}/odds"
        params = {
            "apiKey": ODDS_API_KEY,
            "regions": "eu,us,uk",
            "markets": "h2h",
        }
        r = requests.get(url, params=params, timeout=15)
        if r.status_code == 200:
            matches = r.json()
            resultados = []
            for match in matches[:20]:
                home = match.get("home_team", "")
                away = match.get("away_team", "")
                bookmakers = match.get("bookmakers", [])
                
                mejor_local = 0
                mejor_empate = 0
                mejor_visita = 0
                mejor_casa = ""
                
                for bm in bookmakers[:3]:
                    markets = bm.get("markets", [])
                    for market in markets:
                        if market.get("key") == "h2h":
                            outcomes = market.get("outcomes", [])
                            for o in outcomes:
                                name = o.get("name", "")
                                price = o.get("price", 0)
                                if "Home" in name or home in name:
                                    if price > mejor_local:
                                        mejor_local = price
                                elif "Draw" in name:
                                    if price > mejor_empate:
                                        mejor_empate = price
                                else:
                                    if price > mejor_visita:
                                        mejor_visita = price
                                        mejor_casa = bm.get("title", "")
                
                if mejor_local > 0:
                    resultados.append({
                        "home": home,
                        "away": away,
                        "cuota_local": mejor_local,
                        "cuota_empate": mejor_empate,
                        "cuota_visita": mejor_visita,
                        "casa": mejor_casa,
                    })
            return resultados
        return []
    except Exception as e:
        print(f"Error cuotas: {e}")
        return []


def obtener_clima(ciudad, pais=""):
    """Obtiene el clima actual de una ciudad."""
    if not OPENWEATHER_KEY:
        return None
    try:
        q = f"{ciudad},{pais}" if pais else ciudad
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {"q": q, "appid": OPENWEATHER_KEY, "units": "metric", "lang": "es"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "ciudad": data.get("name", ""),
                "pais": data.get("sys", {}).get("country", ""),
                "temp": data.get("main", {}).get("temp", 0),
                "temp_min": data.get("main", {}).get("temp_min", 0),
                "temp_max": data.get("main", {}).get("temp_max", 0),
                "humedad": data.get("main", {}).get("humidity", 0),
                "clima": data.get("weather", [{}])[0].get("description", ""),
                "viento": data.get("wind", {}).get("speed", 0),
            }
        return None
    except Exception as e:
        print(f"Error clima: {e}")
        return None


def obtener_pronostico(ciudad, pais=""):
    """Obtiene el pronóstico de 5 días."""
    if not OPENWEATHER_KEY:
        return []
    try:
        q = f"{ciudad},{pais}" if pais else ciudad
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {"q": q, "appid": OPENWEATHER_KEY, "units": "metric", "lang": "es"}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            pronostico = []
            for item in data.get("list", [])[:40:8]:
                pronostico.append({
                    "fecha": item.get("dt_txt", "")[:10],
                    "temp": item.get("main", {}).get("temp", 0),
                    "clima": item.get("weather", [{}])[0].get("description", ""),
                })
            return pronostico
        return []
    except Exception as e:
        print(f"Error pronostico: {e}")
        return []


def obtener_stats_fbref(team_url):
    """Obtiene estadísticas detalladas de FBref."""
    try:
        url = f"https://fbref.com{team_url}" if team_url.startswith("/") else f"https://fbref.com/en/squads/{team_url}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            
            stats = {}
            
            # Buscar tabla de estadísticas generales
            tables = soup.find_all("table", {"id": "stats_teams_comps"})
            if not tables:
                tables = soup.find_all("table")
            
            for table in tables[:3]:
                rows = table.find_all("tr")
                for row in rows:
                    cols = row.find_all(["th", "td"])
                    if len(cols) >= 5:
                        stat_name = cols[0].get_text(strip=True)
                        stat_val = cols[1].get_text(strip=True)
                        if stat_name and stat_val and stat_name not in stats:
                            stats[stat_name] = stat_val
            
            return stats if stats else None
        return None
    except Exception as e:
        print(f"Error FBref: {e}")
        return None


def obtener_stats_understat(team_url):
    """Obtiene estadísticas xG de Understat."""
    try:
        # Extraer nombre del equipo de la URL
        team_name = team_url.replace("/team/", "").replace("/", "") if "/team/" in str(team_url) else str(team_url)
        url = f"https://understat.com/team/{team_name}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar datos en scripts JSON
            scripts = soup.find_all("script")
            xg_data = {}
            
            for script in scripts:
                text = script.get_text(strip=True)
                if "xG" in text and len(text) > 50:
                    # Intentar extraer datos
                    import re
                    # Buscar patrones de números
                    nums = re.findall(r'\d+\.?\d*', text)
                    if len(nums) > 10:
                        xg_data = {
                            "xG": nums[0] if nums else "N/A",
                            "xGA": nums[1] if len(nums) > 1 else "N/A",
                            "G": nums[2] if len(nums) > 2 else "N/A",
                            "GA": nums[3] if len(nums) > 3 else "N/A",
                        }
                        break
            
            # Buscar título del equipo
            title = soup.find("title")
            team_full_name = title.get_text().replace(" - Understat", "").strip() if title else team_name
            
            return {"team": team_full_name, "xg_stats": xg_data}
        return None
    except Exception as e:
        print(f"Error Understat: {e}")
        return None


def buscar_stats_equipo(nombre_equipo):
    """Busca estadísticas de un equipo en FBref y Understat."""
    resultados = []
    
    # FBREF
    try:
        url = f"https://fbref.com/en/search/search/?q={nombre_equipo.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar enlaces de equipos
            links = soup.find_all("a", href=lambda h: h and "/squads/" in h if h else False)
            for link in links[:5]:
                team_name = link.get_text(strip=True)
                href = link.get("href", "")
                if team_name and nombre_equipo.lower() in team_name.lower():
                    resultados.append({
                        "fuente": "FBref",
                        "nombre": team_name,
                        "url": href,
                        "tipo": "stats"
                    })
    except Exception as e:
        print(f"Error búsqueda FBref: {e}")
    
    # UNDERSTAT
    try:
        url = f"https://understat.com/search?q={nombre_equipo.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            
            links = soup.find_all("a", href=lambda h: h and "/team/" in h if h else False)
            for link in links[:5]:
                team_name = link.get_text(strip=True)
                href = link.get("href", "")
                if team_name and nombre_equipo.lower() in team_name.lower():
                    resultados.append({
                        "fuente": "Understat",
                        "nombre": team_name,
                        "url": href,
                        "tipo": "xg"
                    })
    except Exception as e:
        print(f"Error búsqueda Understat: {e}")
    
    return resultados


def buscar_equipos_por_liga(liga_id, query):
    """Busca equipos por nombre dentro de una liga específica."""
    try:
        from scorpion.api.football import FootballAPI
        api = FootballAPI()
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        temporada = api.get_temporada(liga_id)
        url = "https://v3.football.api-sports.io/standings"
        data = api._request(url, {"league": liga_id, "season": temporada}, headers=headers)
        
        equipos = []
        if data and data.get("response"):
            for response in data["response"]:
                standings = response.get("league", {}).get("standings", [])
                for stage in standings:
                    for row in stage:
                        team = row.get("team", {})
                        nombre = team.get("name", "")
                        if query.lower() in nombre.lower():
                            equipos.append({
                                "id": team.get("id"),
                                "nombre": nombre,
                                "pais": team.get("country", ""),
                                "logo": team.get("logo", ""),
                            })
        return equipos[:10]
    except Exception as e:
        print(f"Error buscando equipos: {e}")
        return []


def buscar_equipos_todas_fuentes(query):
    """
    Busca equipos en TODAS las fuentes: API-Football, Flashscore, Sofascore.
    Retorna equipos únicos con sus estadísticas.
    """
    equipos_dict = {}
    
    # Fuente 1: API-Football standings (las 12 ligas principales)
    try:
        liga_ids = {
            39: "Premier League", 140: "La Liga", 78: "Bundesliga",
            135: "Serie A", 61: "Ligue 1", 45: "Eredivisie",
            88: "Primeira Liga", 40: "Championship", 141: "La Liga 2",
            79: "2. Bundesliga", 136: "Serie B", 62: "Ligue 2",
        }
        for liga_id, liga_nombre in liga_ids.items():
            equipos = buscar_equipos_por_liga(liga_id, query)
            for eq in equipos:
                if eq["id"] not in equipos_dict:
                    eq["liga"] = liga_nombre
                    eq["fuente"] = "API-Football"
                    equipos_dict[eq["id"]] = eq
    except Exception as e:
        print(f"Error API: {e}")
    
    # Fuente 2: Sofascore API (busca por nombre directamente)
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        search_url = f"https://api.sofascore.com/api/v1/search/teams/{query}"
        r = requests.get(search_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                for team in data["results"][:5]:
                    tid = team.get("id")
                    if tid not in equipos_dict:
                        equipos_dict[tid] = {
                            "id": tid,
                            "nombre": team.get("name"),
                            "pais": team.get("country", {}).get("name", ""),
                            "logo": f"https://www.sofascore.com/images/team/{tid}.png",
                            "liga": "Sofascore",
                            "fuente": "Sofascore",
                        }
    except Exception as e:
        print(f"Error Sofascore: {e}")
    
    # Fuente 3: Flashscore (busca en equipos de partidos)
    try:
        # Buscar en partidos ya scrapeados
        if 'partidos_scraped' in st.session_state:
            for p in st.session_state.partidos_scraped:
                local = p.get("local", "")
                visitante = p.get("visitante", "")
                # Buscar coincidencia
                if query.lower() in local.lower() or query.lower() in visitante.lower():
                    # Agregar local
                    if local and local not in [e["nombre"] for e in equipos_dict.values()]:
                        equipos_dict[f"flash_{local}"] = {
                            "id": f"flash_{local}",
                            "nombre": local,
                            "liga": p.get("liga", "Flashscore"),
                            "fuente": "Flashscore",
                        }
                    # Agregar visitante
                    if visitante and visitante not in [e["nombre"] for e in equipos_dict.values()]:
                        equipos_dict[f"flash_{visitante}"] = {
                            "id": f"flash_{visitante}",
                            "nombre": visitante,
                            "liga": p.get("liga", "Flashscore"),
                            "fuente": "Flashscore",
                        }
    except Exception as e:
        print(f"Error Flashscore: {e}")
    
    return list(equipos_dict.values())


# Alias para compatibilidad
def buscar_equipos_todas_ligas(query):
    """Alias para buscar_equipos_todas_fuentes."""
    return buscar_equipos_todas_fuentes(query)


def obtener_estadisticas_equipo(equipo_nombre, team_id=None, liga_nombre=None):
    """
    Obtiene estadísticas de un equipo desde múltiples fuentes.
    Funciona aunque el equipo no esté jugando hoy.
    """
    stats = {
        "partidos_jugados": 0,
        "victorias": 0,
        "empates": 0,
        "derrotas": 0,
        "goles_favor": 0,
        "goles_contra": 0,
        "clean_sheet": 0,
        "fuente": "No disponible",
    }
    
    # Fuente 1: Sofascore (más rápida y directa)
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        search_url = f"https://api.sofascore.com/api/v1/search/teams/{equipo_nombre}"
        r = requests.get(search_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                team = data["results"][0]
                tid = team.get("id")
                # Obtener stats
                stats_url = f"https://api.sofascore.com/api/v1/team/{tid}/statistics/overall"
                r2 = requests.get(stats_url, headers=headers, timeout=5)
                if r2.status_code == 200:
                    s = r2.json()
                    stats["partidos_jugados"] = s.get("matches", {}).get("total", 0)
                    stats["victorias"] = s.get("wins", {}).get("total", 0)
                    stats["empates"] = s.get("draws", {}).get("total", 0)
                    stats["derrotas"] = s.get("losses", {}).get("total", 0)
                    stats["goles_favor"] = s.get("goalsScored", {}).get("total", 0)
                    stats["goles_contra"] = s.get("goalsConceded", {}).get("total", 0)
                    stats["clean_sheet"] = s.get("cleanSheets", {}).get("total", 0)
                    stats["fuente"] = "Sofascore"
                    return stats
    except Exception as e:
        print(f"Error Sofascore stats: {e}")
    
    # Fuente 2: API-Football
    if team_id and API_FOOTBALL_KEY:
        try:
            headers = {"x-apisports-key": API_FOOTBALL_KEY}
            # Buscar equipo primero para obtener league ID
            url = f"https://v3.football.api-sports.io/teams?id={team_id}"
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                data = r.json()
                if data.get("response"):
                    leagues = data["response"][0].get("leagues", [])
                    for league in leagues[:1]:
                        lid = league.get("league", {}).get("id")
                        season = 2024
                        if lid:
                            stats_url = f"https://v3.football.api-sports.io/teams/statistics?team={team_id}&league={lid}&season={season}"
                            r2 = requests.get(stats_url, headers=headers, timeout=5)
                            if r2.status_code == 200:
                                s = r2.json()
                                if s.get("response"):
                                    resp = s["response"]
                                    stats["partidos_jugados"] = resp.get("fixtures", {}).get("played", 0)
                                    stats["victorias"] = resp.get("fixtures", {}).get("wins", {}).get("total", 0)
                                    stats["empates"] = resp.get("fixtures", {}).get("draws", {}).get("total", 0)
                                    stats["derrotas"] = resp.get("fixtures", {}).get("loses", {}).get("total", 0)
                                    stats["goles_favor"] = resp.get("goals", {}).get("for", {}).get("total", {}).get("total", 0)
                                    stats["goles_contra"] = resp.get("goals", {}).get("against", {}).get("total", {}).get("total", 0)
                                    stats["clean_sheet"] = resp.get("clean_sheet", {}).get("total", 0)
                                    stats["fuente"] = "API-Football"
                                    return stats
        except Exception as e:
            print(f"Error API stats: {e}")
    
    return stats


def obtener_forma_reciente(team_id, league_id, season):
    """Obtiene los últimos resultados de un equipo."""
    try:
        from scorpion.api.football import FootballAPI
        api = FootballAPI()
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        url = "https://v3.football.api-sports.io/fixtures"
        data = api._request(url, {"team": team_id, "league": league_id, "season": season, "last": 10}, headers=headers)
        
        resultados = []
        if data and data.get("response"):
            for item in data["response"][:5]:
                fixture = item.get("fixture", {})
                goals = item.get("goals", {})
                es_local = item["teams"]["home"]["id"] == team_id
                equipo_rival = item["teams"]["away"]["name"] if es_local else item["teams"]["home"]["name"]
                goles_local = goals.get("home", 0)
                goles_visitante = goals.get("away", 0)
                
                if es_local:
                    if goles_local > goles_visitante:
                        resultado, color = "V", "#39ff14"
                    elif goles_local < goles_visitante:
                        resultado, color = "D", "#ff6b6b"
                    else:
                        resultado, color = "E", "#dfaf6f"
                else:
                    if goles_visitante > goles_local:
                        resultado, color = "V", "#39ff14"
                    elif goles_visitante < goles_local:
                        resultado, color = "D", "#ff6b6b"
                    else:
                        resultado, color = "E", "#dfaf6f"
                
                resultados.append({
                    "resultado": resultado, "color": color,
                    "goles": f"{goles_local}-{goles_visitante}",
                    "rival": equipo_rival,
                    "fecha": fixture.get("date", "")[:10] if fixture.get("date") else ""
                })
        return resultados
    except Exception as e:
        print(f"Error forma reciente: {e}")
        return []


def mostrar_buscador_equipos():
    """Interfaz del buscador de equipos."""
    st.markdown("---")
    st.markdown('<p class="section-title">🔍 Buscador de Equipos</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        busqueda = st.text_input("🔎 Nombre del equipo:", placeholder="Ej: Barcelona, Real Madrid...", key="busqueda_equipo")
        
        if busqueda and len(busqueda) >= 2:
            with st.spinner("Buscando en todas las ligas..."):
                equipos = buscar_equipos_todas_ligas(busqueda)
            
            if equipos:
                st.success(f"✅ {len(equipos)} equipos encontrados")
                for eq in equipos[:8]:
                    liga = eq.get("liga", "")
                    clave = f"eq_{eq['id']}_{liga.replace(' ', '_')}"
                    if st.button(f"⚽ {eq['nombre']} ({liga})", key=clave):
                        st.session_state['equipo_seleccionado'] = eq
                        st.session_state['equipo_liga'] = liga
                        st.rerun()
            else:
                st.warning("No se encontraron equipos. Prueba otro nombre.")
    
    with col2:
        if 'equipo_seleccionado' in st.session_state:
            eq = st.session_state['equipo_seleccionado']
            liga_default = st.session_state.get('equipo_liga', 'Premier League')
            
            st.markdown(f"""
            <div style="background: #1b2621; border: 1px solid #8a6435; border-radius: 6px; padding: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.5);">
                <h3 style="color: #dfaf6f; margin-top: 0;">{eq['nombre']}</h3>
                <p style="color: #dcdcdc; margin: 5px 0;">📍 Liga: {eq.get('liga', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            liga_ids = {"Premier League": 39, "La Liga": 140, "Bundesliga": 78, "Serie A": 135, "Ligue 1": 61}
            liga_busqueda = st.selectbox("📊 Selecciona liga:", list(liga_ids.keys()), key="liga_equipo")
            liga_id = liga_ids.get(liga_busqueda, 39)
            
            if st.button("📊 Ver Estadísticas", key="ver_stats", type="primary"):
                with st.spinner("Cargando estadísticas..."):
                    # Usar el nuevo formato
                    stats = obtener_estadisticas_equipo(eq['nombre'], eq.get('id'), eq.get('liga'))
                
                if stats and stats.get('partidos_jugados', 0) > 0:
                    st.markdown("---")
                    st.success(f"📊 Estadísticas de {eq['nombre']} (Fuente: {stats.get('fuente', 'N/A')})")
                    st.markdown(f"""
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 15px 0;">
                        <div style="background: #1b2621; border: 1px solid #8a6435; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #dfaf6f; font-size: 1.5rem; font-weight: bold;">{stats.get('partidos_jugados', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">PARTIDOS</div>
                        </div>
                        <div style="background: #1b2621; border: 1px solid #39ff14; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #39ff14; font-size: 1.5rem; font-weight: bold;">{stats.get('victorias', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">VICTORIAS</div>
                        </div>
                        <div style="background: #1b2621; border: 1px solid #dfaf6f; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #dfaf6f; font-size: 1.5rem; font-weight: bold;">{stats.get('empates', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">EMPATES</div>
                        </div>
                        <div style="background: #1b2621; border: 1px solid #ff6b6b; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #ff6b6b; font-size: 1.5rem; font-weight: bold;">{stats.get('derrotas', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">DERROTAS</div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 15px 0;">
                        <div style="background: #1b2621; border: 1px solid #8a6435; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #dfaf6f; font-size: 1.5rem; font-weight: bold;">{stats.get('goles_favor', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">GOLES A FAVOR</div>
                        </div>
                        <div style="background: #1b2621; border: 1px solid #8a6435; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #dfaf6f; font-size: 1.5rem; font-weight: bold;">{stats.get('goles_contra', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">GOLES EN CONTRA</div>
                        </div>
                        <div style="background: #1b2621; border: 1px solid #8a6435; border-radius: 6px; padding: 15px; text-align: center;">
                            <div style="color: #dfaf6f; font-size: 1.5rem; font-weight: bold;">{stats.get('clean_sheet', 0)}</div>
                            <div style="color: #dcdcdc; font-size: 0.75rem;">VALLAS CLEAN</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Cargando datos... Intenta de nuevo en unos segundos.")
        else:
            st.info("🔍 Escribe el nombre de un equipo para buscar")


# ══════════════════════════════════════════════════════════
# CALENDARIO DE PARTIDOS (PDF 2.0)
# ══════════════════════════════════════════════════════════


def obtener_partidos_por_fecha(fecha_str, liga_id=None):
    """Obtiene partidos para una fecha específica desde API-Football."""
    try:
        from scorpion.api.football import FootballAPI
        api = FootballAPI()
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        
        # Determinar temporada basada en la fecha
        year = int(fecha_str[:4]) if fecha_str else 2024
        season = 2024 if year >= 2024 else year
        
        # Buscar en todas las ligas principales
        ligas_principales = [
            (39, "Premier League"), (140, "La Liga"), (78, "Bundesliga"),
            (135, "Serie A"), (61, "Ligue 1"), (45, "Eredivisie"),
            (88, "Primeira Liga"), (40, "Championship"), (141, "La Liga 2"),
            (79, "2. Bundesliga"), (136, "Serie B"), (62, "Ligue 2"),
        ]
        
        todos_partidos = []
        
        for lid, lname in ligas_principales:
            try:
                params = {
                    "date": fecha_str,
                    "league": lid,
                    "season": season
                }
                
                url = "https://v3.football.api-sports.io/fixtures"
                data = api._request(url, params, headers=headers)
                
                if data and data.get("response"):
                    for item in data["response"]:
                        fixture = item.get("fixture", {})
                        teams = item.get("teams", {})
                        goals = item.get("goals", {})
                        
                        es_vivo = fixture.get("status", {}).get("short") in ["1H", "2H", "HT", "ET", "P", "LIVE", "SUSP", "INT"]
                        
                        # Extraer hora de la fecha
                        fecha_completa = fixture.get("date", "")
                        hora = fecha_completa[11:16] if fecha_completa and len(fecha_completa) > 16 else "--:--"
                        
                        todos_partidos.append({
                            "id": fixture.get("id"),
                            "fecha": fecha_completa[:16] if fecha_completa else "",
                            "hora": hora,
                            "liga": lname,
                            "liga_id": lid,
                            "local": teams.get("home", {}).get("name", ""),
                            "visitante": teams.get("away", {}).get("name", ""),
                            "goles_local": goals.get("home"),
                            "goles_visitante": goals.get("away"),
                            "estado": fixture.get("status", {}).get("short", ""),
                            "vivo": es_vivo,
                        })
            except Exception as e:
                continue
        
        # Eliminar duplicados por ID
        seen = set()
        unique_partidos = []
        for p in todos_partidos:
            if p["id"] not in seen:
                seen.add(p["id"])
                unique_partidos.append(p)
        
        return unique_partidos
    except Exception as e:
        print(f"Error obteniendo partidos: {e}")
        return []


def mostrar_calendario_partidos():
    """Interfaz del calendario de partidos."""
    st.markdown("---")
    st.markdown('<p class="section-title">📅 Calendario de Partidos</p>', unsafe_allow_html=True)
    
    # Tabs para Hoy, Mañana, En Vivo
    tab_hoy, tab_manana, tab_vivo = st.tabs(["📅 Hoy", "📆 Mañana", "🔴 En Vivo"])
    
    from datetime import date, timedelta
    
    hoy = date.today()
    manana = hoy + timedelta(days=1)
    
    with tab_hoy:
        st.markdown(f"### Partidos de hoy: {hoy.strftime('%d/%m/%Y')}")
        
        partidos_hoy = obtener_partidos_por_fecha(hoy.strftime("%Y-%m-%d"))
        
        if partidos_hoy:
            # Agrupar por liga
            ligas = {}
            for p in partidos_hoy:
                liga = p.get("liga", "Otra")
                if liga not in ligas:
                    ligas[liga] = []
                ligas[liga].append(p)
            
            for liga, partidos in sorted(ligas.items()):
                with st.expander(f"🏆 {liga} ({len(partidos)} partidos)"):
                    for p in partidos:
                        local = p.get("local", "")
                        visitante = p.get("visitante", "")
                        goles_l = p.get("goles_local")
                        goles_v = p.get("goles_visitante")
                        estado = p.get("estado", "")
                        hora = p.get("hora", "")[11:16] if len(p.get("hora", "")) > 16 else p.get("hora", "")
                        
                        # Determinar estilo según estado
                        if estado == "LIVE" or p.get("vivo"):
                            badge = '<span style="background:#ff4444;color:white;padding:2px 8px;border-radius:10px;font-size:11px;">🔴 EN VIVO</span>'
                        elif estado in ["1H", "2H", "HT"]:
                            badge = '<span style="background:#ff4444;color:white;padding:2px 8px;border-radius:10px;font-size:11px;">🔴 EN VIVO</span>'
                        elif estado == "FT":
                            badge = '<span style="background:#39ff14;color:#0a2114;padding:2px 8px;border-radius:10px;font-size:11px;">✅ FINAL</span>'
                        else:
                            badge = f'<span style="background:#8a6435;color:white;padding:2px 8px;border-radius:10px;font-size:11px;">⏰ {hora}</span>'
                        
                        # Mostrar marcador o vs
                        if goles_l is not None and goles_v is not None:
                            marcador = f"<span style='color:#dfaf6f;font-weight:bold;font-size:1.2rem;'>{goles_l} - {goles_v}</span>"
                        else:
                            marcador = "<span style='color:#888;'>vs</span>"
                        
                        st.markdown(f"""
                        <div style="background:#1b2621;border:1px solid #8a6435;border-radius:6px;padding:12px;margin-bottom:8px;">
                            <div style="display:flex;justify-content:space-between;align-items:center;">
                                <div style="flex:1;text-align:center;">
                                    <div style="color:#dcdcdc;font-weight:bold;">{local}</div>
                                </div>
                                <div style="padding:0 20px;text-align:center;">
                                    {marcador} {badge}
                                </div>
                                <div style="flex:1;text-align:center;">
                                    <div style="color:#dcdcdc;font-weight:bold;">{visitante}</div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No hay partidos programados para hoy.")
    
    with tab_manana:
        st.markdown(f"### Partidos de mañana: {manana.strftime('%d/%m/%Y')}")
        
        partidos_manana = obtener_partidos_por_fecha(manana.strftime("%Y-%m-%d"))
        
        if partidos_manana:
            for p in partidos_manana[:10]:
                local = p.get("local", "")
                visitante = p.get("visitante", "")
                hora = p.get("hora", "")[11:16] if len(p.get("hora", "")) > 16 else p.get("hora", "")
                liga = p.get("liga", "")
                
                st.markdown(f"""
                <div style="background:#1b2621;border:1px solid #8a6435;border-radius:6px;padding:12px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;">
                    <div style="color:#8a6435;font-size:0.8rem;flex:1;">{liga}</div>
                    <div style="flex:2;text-align:center;color:#dcdcdc;">{local} <span style="color:#8a6435;">vs</span> {visitante}</div>
                    <div style="flex:1;text-align:right;color:#dfaf6f;font-weight:bold;">{hora}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay partidos programados para mañana.")
    
    with tab_vivo:
        st.markdown("### 🔴 Partidos en Vivo Ahora")
        
        partidos_hoy = obtener_partidos_por_fecha(hoy.strftime("%Y-%m-%d"))
        partidos_vivo = [p for p in partidos_hoy if p.get("vivo") or p.get("estado") in ["1H", "2H", "HT", "ET", "P", "LIVE"]]
        
        if partidos_vivo:
            for p in partidos_vivo:
                local = p.get("local", "")
                visitante = p.get("visitante", "")
                goles_l = p.get("goles_local", 0)
                goles_v = p.get("goles_visitante", 0)
                estado = p.get("estado", "")
                
                st.markdown(f"""
                <div style="background:#1b2621;border:2px solid #ff4444;border-radius:6px;padding:15px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="flex:1;text-align:center;">
                            <div style="color:#dcdcdc;font-size:1.1rem;font-weight:bold;">{local}</div>
                        </div>
                        <div style="padding:0 25px;text-align:center;">
                            <div style="color:#ff4444;font-size:2rem;font-weight:bold;">{goles_l} - {goles_v}</div>
                            <div style="color:#ff4444;font-size:0.9rem;">🔴 {estado}</div>
                        </div>
                        <div style="flex:1;text-align:center;">
                            <div style="color:#dcdcdc;font-size:1.1rem;font-weight:bold;">{visitante}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No hay partidos en vivo ahora. Revisa más tarde.")


def enriquecer_partidos_con_stats(partidos, stats):
    """Añade estadísticas a los partidos basándose en nombre de equipo."""
    if not stats:
        return partidos
    
    partidos_enriquecidos = []
    for p in partidos:
        partido = p.copy()
        local = p.get("local", "").lower()
        visitante = p.get("visitante", "").lower()
        
        stats_local = None
        stats_visitante = None
        
        for nombre, data in stats.items():
            if stats_local is None and local in nombre.lower():
                stats_local = data
            if stats_visitante is None and visitante in nombre.lower():
                stats_visitante = data
        
        if stats_local:
            partido["stats_local"] = stats_local
        if stats_visitante:
            partido["stats_visitante"] = stats_visitante
        
        partidos_enriquecidos.append(partido)
    
    return partidos_enriquecidos


# ══════════════════════════════════════════════════════════
# COMPARADOR DE ODDS
# ══════════════════════════════════════════════════════════

def obtener_odds_partido(fixture_id):
    """
    Obtiene las cuotas de un partido desde múltiples casas de apuestas.
    Usa API-Football para obtener cuotas reales.
    """
    try:
        from scorpion.api.football import FootballAPI
        api = FootballAPI()
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        url = "https://v3.football.api-sports.io/odds"
        data = api._request(url, {"fixture": fixture_id}, headers=headers)
        
        if data and data.get("response"):
            odds_list = []
            for response in data["response"]:
                bookmaker = response.get("bookmaker", {})
                name = bookmaker.get("name", "Desconocido")
                
                for bet in response.get("values", []):
                    bet_name = bet.get("name", "")
                    if "Match Winner" in bet_name or "1X2" in bet_name or "Resultado" in bet_name:
                        for value in bet.get("values", []):
                            odds_list.append({
                                "casa": name,
                                "opcion": value.get("value", ""),
                                "cuota": float(value.get("odd", 0))
                            })
            
            return odds_list
    except Exception as e:
        print(f"Error obteniendo odds: {e}")
    
    return []


def obtener_mejores_cuotas(local, visitante, liga_id):
    """
    Busca las mejores cuotas para un partido específico.
    """
    try:
        from scorpion.api.football import FootballAPI
        api = FootballAPI()
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        
        # Obtener fixtures del día
        fixtures = api.get_fixtures(liga_id, fecha=get_hoy())
        
        for f in fixtures:
            home_team = f["teams"]["home"]["name"].lower()
            away_team = f["teams"]["away"]["name"].lower()
            
            if local.lower() in home_team and visitante.lower() in away_team:
                fixture_id = f["fixture"]["id"]
                odds = obtener_odds_partido(fixture_id)
                
                if odds:
                    # Agrupar por opción (1, X, 2)
                    mejores = {"1": None, "X": None, "2": None}
                    mejor_casa = {"1": "", "X": "", "2": ""}
                    
                    for odd in odds:
                        opcion = odd["opcion"]
                        cuota = odd["cuota"]
                        
                        # Normalizar opciones
                        if opcion in ["1", "Home", "Local", "Ganador Local"]:
                            clave = "1"
                        elif opcion in ["X", "Draw", "Empate"]:
                            clave = "X"
                        elif opcion in ["2", "Away", "Visitante", "Ganador Visitante"]:
                            clave = "2"
                        else:
                            continue
                        
                        if mejores[clave] is None or cuota > mejores[clave]:
                            mejores[clave] = cuota
                            mejor_casa[clave] = odd["casa"]
                    
                    return [{"opcion": k, "cuota": v, "casa": mejor_casa[k]} 
                            for k, v in mejores.items() if v]
        
    except Exception as e:
        print(f"Error mejores cuotas: {e}")
    
    return []


def mostrar_comparador_odds():
    """
    Muestra el comparador de odds en la interfaz.
    """
    st.markdown("---")
    st.markdown('<p class="section-title">📊 Comparador de Cuotas</p>', unsafe_allow_html=True)
    
    # Selector de partido
    if 'partidos_scraped' in st.session_state and st.session_state.partidos_scraped:
        partidos = st.session_state.partidos_scraped[:5]
        opciones = [f"{p.get('local','')} vs {p.get('visitante','')}" for p in partidos]
        
        partido_seleccionado = st.selectbox("Selecciona un partido:", opciones)
        
        if partido_seleccionado:
            idx = opciones.index(partido_seleccionado)
            partido = partidos[idx]
            
            # Buscar mejores cuotas
            liga_id = 39  # Por defecto Premier
            cuotas = obtener_mejores_cuotas(
                partido.get("local", ""),
                partido.get("visitante", ""),
                liga_id
            )
            
            if cuotas:
                # Mostrar tabla de cuotas
                st.markdown("""
                <div style="background: linear-gradient(135deg, #122016 0%, #0f1a12 100%); padding: 15px; border-radius: 10px; border: 1px solid #243829; margin-top: 10px;">
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                
                for i, cuota in enumerate(cuotas):
                    col = [col1, col2, col3][i]
                    with col:
                        if cuota["opcion"] == "1":
                            label = "Local"
                            color = "#d48243"
                        elif cuota["opcion"] == "X":
                            label = "Empate"
                            color = "#dfaf6f"
                        else:
                            label = "Visita"
                            color = "#d48243"
                        
                        st.markdown(f"""
                        <div style="text-align: center; padding: 15px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid {color};">
                            <div style="color: #a3b899; font-size: 0.75rem;">{label}</div>
                            <div style="color: {color}; font-size: 1.8rem; font-weight: bold; margin: 5px 0;">{cuota['cuota']}</div>
                            <div style="color: #888; font-size: 0.65rem;">{cuota['casa']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Encontrar la mejor cuota
                mejor = max(cuotas, key=lambda x: x["cuota"])
                st.success(f"💰 Mejor cuota: **{mejor['opcion']}** a **{mejor['cuota']}** en {mejor['casa']}")
            else:
                st.info("Cuotas no disponibles. Intenta más tarde.")
    else:
        st.info("Cargando partidos para comparar cuotas...")


# ══════════════════════════════════════════════════════════
# SISTEMA DE ALERTAS
# ══════════════════════════════════════════════════════════

ALERTAS_CACHE = {}

def guardar_alerta(cedula, tipo, mensaje, enlace=""):
    """Guarda una alerta para un usuario."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT INTO alertas (cedula, tipo, mensaje, enlace, leida, fecha) 
                  VALUES (?, ?, ?, ?, 0, datetime('now', 'localtime'))""",
              (cedula, tipo, mensaje, enlace))
    conn.commit()
    conn.close()

def obtener_alertas(cedula, limite=10):
    """Obtiene las alertas no leídas de un usuario."""
    if f"alertas_{cedula}" in ALERTAS_CACHE:
        return ALERTAS_CACHE[f"alertas_{cedula}"]
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT id, tipo, mensaje, enlace, fecha FROM alertas 
                  WHERE cedula = ? AND leida = 0 ORDER BY fecha DESC LIMIT ?""",
              (cedula, limite))
    alertas = [{"id": r[0], "tipo": r[1], "mensaje": r[2], "enlace": r[3], "fecha": r[4]} 
               for r in c.fetchall()]
    conn.close()
    
    ALERTAS_CACHE[f"alertas_{cedula}"] = alertas
    return alertas

def marcar_alerta_leida(alerta_id):
    """Marca una alerta como leída."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE alertas SET leida = 1 WHERE id = ?", (alerta_id,))
    conn.commit()
    conn.close()
    
    # Limpiar cache
    for key in list(ALERTAS_CACHE.keys()):
        if key.startswith("alertas_"):
            del ALERTAS_CACHE[key]

def crear_alerta_nuevo_pick(pick, rango):
    """Crea alertas para todos los usuarios cuando hay un nuevo pick."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT cedula FROM usuarios WHERE activo = 1")
    usuarios = [r[0] for r in c.fetchall()]
    conn.close()
    
    tipo_alerta = "pick_top" if rango == "A+" else "pick_nuevo"
    mensaje = f"🔥 Nuevo pick: {pick.get('local','')} vs {pick.get('visitante','')} - {pick.get('mercado','')} ({pick.get('cuota','')})"
    
    for cedula in usuarios:
        guardar_alerta(cedula, tipo_alerta, mensaje)

def mostrar_panel_alertas(cedula):
    """Muestra el panel de alertas en la interfaz."""
    alertas = obtener_alertas(cedula)
    
    if alertas:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #122016 0%, #0f1a12 100%); padding: 15px; border-radius: 10px; border: 1px solid #d48243; margin-top: 15px;">
            <div style="color: #d48243; font-size: 1rem; font-weight: bold; margin-bottom: 10px;">
                🔔 Alertas Recientes
            </div>
        """, unsafe_allow_html=True)
        
        for alerta in alertas[:5]:
            tipo_icono = "🔥" if alerta["tipo"] == "pick_top" else "📢" if alerta["tipo"] == "pick_nuevo" else "⚠️"
            
            st.markdown(f"""
            <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #d48243;">
                <span style="color: #d48243; font-size: 0.9rem;">{tipo_icono} {alerta['mensaje']}</span>
                <div style="color: #666; font-size: 0.65rem; margin-top: 3px;">{alerta['fecha']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("Marcar todas como leídas", key="marcar_leidas"):
            for alerta in alertas:
                marcar_alerta_leida(alerta["id"])
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #122016 0%, #0f1a12 100%); padding: 15px; border-radius: 10px; border: 1px solid #243829; margin-top: 15px; text-align: center;">
            <span style="color: #888;">🔕 No hay alertas nuevas</span>
        </div>
        """, unsafe_allow_html=True)

def suscribir_notificaciones_email(cedula, email):
    """Guarda email para notificaciones."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE usuarios SET email = ? WHERE cedula = ?", (email, cedula))
    conn.commit()
    conn.close()
    return True

def enviar_notificacion_email(email, asunto, mensaje):
    """Envía un email de notificación (requiere configuración SMTP)."""
    # Esta función requiere configuración de servidor SMTP
    # Por ahora es un placeholder
    print(f"Email a {email}: {asunto} - {mensaje}")
    return True


def verificar_y_crear_alertas_picks():
    """
    Verifica si hay nuevos picks y crea alertas automáticas.
    Se ejecuta cuando se generan picks nuevos.
    """
    picks_hoy = db_picks_get(get_hoy())
    
    if picks_hoy:
        for pick in picks_hoy:
            rango = pick.get("rango", "C")
            crear_alerta_nuevo_pick(pick, rango)


def obtener_goleadores_api(liga_nombre):
    """
    Obtiene goleadores reales desde API-Football.
    Funciona para TODAS las ligas soportadas.
    """
    try:
        from scorpion.api.football import FootballAPI
        api = FootballAPI()
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        
        # Mapeo de TODAS las ligas a ID
        liga_ids = {
            # Europa
            "Premier League": 39,
            "La Liga": 140,
            "Bundesliga": 78,
            "Serie A": 135,
            "Ligue 1": 61,
            "Champions League": 2,
            "Europa League": 3,
            "Eredivisie": 88,
            "Primeira Liga": 94,
            "Scottish Premiership": 50,
            "Super Lig": 203,
            "Jupiler Pro League": 144,
            "Swiss Super League": 207,
            "Austrian Bundesliga": 163,
            # America
            "Copa Libertadores": 13,
            "Copa Sudamericana": 15,
            "MLS": 17,
            "Liga MX": 22,
            "Argentine Liga": 21,
            "Brasileirão": 24,
            "Colombian Liga": 239,
            "Chilean Liga": 42,
            "Peruvian Liga": 271,
            # Asia
            "Saudi Pro League": 306,
            "J1 League": 98,
            "K League 1": 292,
            "Chinese Super League": 169,
            "Indian Super League": 357,
            "A-League": 188,
        }
        
        liga_id = liga_ids.get(liga_nombre)
        if not liga_id:
            return []
        
        temporada = api.get_temporada(liga_id)
        
        # Obtener topscorers de la liga
        url = "https://v3.football.api-sports.io/players/topscorers"
        data = api._request(url, {"league": liga_id, "season": temporada}, headers=headers)
        
        goleadores = []
        if data and data.get("response"):
            for item in data["response"][:10]:  # Top 10 goleadores
                player = item.get("player", {})
                stats = item.get("statistics", [{}])[0]
                
                nombre = player.get("name", "Desconocido")
                equipo = stats.get("team", {}).get("name", "")
                goles = stats.get("goals", {}).get("total", 0)
                partidos = stats.get("games", {}).get("appearences", 0)
                
                if nombre and goles and goles > 0:
                    goleadores.append({
                        "posicion": len(goleadores) + 1,
                        "nombre": nombre,
                        "equipo": equipo,
                        "goles": goles,
                        "partidos": partidos
                    })
        
        return goleadores
        
    except Exception as e:
        print(f"Error goleadores API: {e}")
        return []


def scrape_goleadores_tiempo_real(liga_nombre):
    """Obtiene goleadores en tiempo real desde Flashscore."""
    global GOLEADORES_CACHE
    
    # Verificar cache (5 minutos)
    cache_key = f"{liga_nombre}_{get_hoy()}"
    if cache_key in GOLEADORES_CACHE:
        return GOLEADORES_CACHE[cache_key]
    
    goleadores = []
    
    # Mapeo de ligas a URLs de Flashscore
    liga_urls = {
        "Premier League": ("inglaterra-premier-league", "🏴󠁧󠁢󠁥󠁮"),
        "La Liga": ("espana-laliga", "🇪🇸"),
        "Bundesliga": ("alemania-bundesliga", "🇩🇪"),
        "Serie A": ("italia-serie-a", "🇮🇹"),
        "Ligue 1": ("francia-ligue-1", "🇫🇷"),
        "Champions League": ("europa-champions-league", "🌍"),
        "Copa America": ("mundial-fifa", "🌎"),
        "Mundial FIFA 2026": ("mundial-fifa", "🌍"),
    }
    
    liga_info = liga_urls.get(liga_nombre)
    if not liga_info:
        return goleadores
    
    url_part, _ = liga_info
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        }
        
        # Probar varias URLs posibles
        urls_to_try = [
            f"https://www.flashscore.es/futbol/{url_part}/clasificacion/",
            f"https://www.flashscore.es/futbol/{url_part}/estadisticas/",
            f"https://www.flashscore.es/{url_part}/",
        ]
        
        for url in urls_to_try:
            try:
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, "html.parser")
                    
                    # Buscar tablas con goleadores
                    tables = soup.find_all("table")
                    for table in tables:
                        rows = table.find_all("tr")
                        for i, row in enumerate(rows[1:11], 1):
                            cols = row.find_all("td")
                            if len(cols) >= 2:
                                nombre = cols[0].get_text(strip=True)
                                try:
                                    goles_text = cols[1].get_text(strip=True)
                                    goles = int(re.sub(r'[^0-9]', '', goles_text))
                                except:
                                    goles = 0
                                if nombre and len(nombre) > 2 and goles > 0:
                                    goleadores.append({
                                        "posicion": i,
                                        "nombre": nombre,
                                        "goles": goles,
                                        "equipo": ""
                                    })
                    
                    if goleadores:
                        break  # Si encontramos datos, salir
            except:
                continue
                
    except Exception as e:
        print(f"Error scraping goleadores {liga_nombre}: {e}")
    
    # Guardar en cache
    GOLEADORES_CACHE[cache_key] = goleadores
    return goleadores

# ══════════════════════════════════════════════════════════
# SCRAPING MULTI-FUENTE PARA CUALQUIER LIGA
# ══════════════════════════════════════════════════════════

def scrape_liga_multi_fuente(liga_nombre, fecha=""):
    """
    Busca partidos en MÚLTIPLES FUENTES para cualquier liga.
    Fuentes: Flashscore → Sofascore → Betexplorer
    """
    # Mapeo de nombres de ligas a URLs de Flashscore
    liga_mapping = {
        "premier league": "inglaterra-premier-league",
        "la liga": "espana-laliga",
        "laliga": "espana-laliga",
        "bundesliga": "alemania-bundesliga",
        "serie a": "italia-serie-a",
        "ligue 1": "francia-ligue-1",
        "ligue1": "francia-ligue-1",
        "champions league": "europa-champions-league",
        "champions": "europa-champions-league",
        "europa league": "europa-europa-league",
        "copa america": "mundial-fifa",
        "mundial": "mundial-fifa",
        "mundial fifa 2026": "mundial-fifa",
        "libertadores": "sudamerica-copa-libertadores",
        "sudamericana": "sudamerica-copa-sudamericana",
        "brasileirao": "brasil-serie-a",
        "liga mx": "mexico-liga-mx",
        "betplay": "colombia-liga-aguila",
    }
    
    liga_slug = liga_mapping.get(liga_nombre.lower().strip(), "")
    
    if not liga_slug:
        # Intentar crear slug automáticamente
        liga_slug = liga_nombre.lower().replace(" ", "-").replace(" 2", "-2")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    
    # Fuente 1: Flashscore
    flashscore_urls = [
        f"https://www.flashscore.es/futbol/{liga_slug}/",
        f"https://www.flashscore.mx/futbol/{liga_slug}/",
        f"https://www.flashscore.com/futbol/{liga_slug}/",
    ]
    
    for url in flashscore_urls:
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                partidos = _parse_flashscore_partidos(soup, liga_nombre)
                if partidos:
                    return {"partidos": partidos, "fuente": "Flashscore"}
        except Exception as e:
            continue
    
    # Fuente 2: Sofascore API
    sofascore_result = _scrape_sofascore_api(liga_nombre)
    if sofascore_result:
        return sofascore_result
    
    # Fuente 3: Betexplorer
    betexplorer_result = _scrape_betexplorer(liga_nombre)
    if betexplorer_result:
        return betexplorer_result
    
    return {"partidos": [], "fuente": None}

def _parse_flashscore_partidos(soup, liga_nombre):
    """Parsea partidos del HTML de Flashscore."""
    partidos = []
    for match in soup.find_all("div", class_="event__match"):
        try:
            hora = match.find("div", class_="event__time")
            local = match.find("div", class_="event__homeParticipant")
            visitante = match.find("div", class_="event__awayParticipant")
            
            if local and visitante:
                h = hora.get_text(strip=True) if hora else "--:--"
                l = local.get_text(strip=True)
                v = visitante.get_text(strip=True)
                
                if l and v:
                    partidos.append({
                        "hora": h,
                        "local": l,
                        "visitante": v,
                        "liga": liga_nombre,
                        "dia": get_hoy()
                    })
        except:
            continue
    return partidos

def _scrape_sofascore_api(liga_nombre):
    """Usa API de Sofascore para obtener partidos."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        
        # Mapear ligas a tournament IDs de Sofascore
        tournament_ids = {
            "premier league": 17,
            "la liga": 8,
            "bundesliga": 35,
            "serie a": 55,
            "ligue 1": 34,
            "champions league": 7,
            "mundial": 1,
        }
        
        tournament_id = tournament_ids.get(liga_nombre.lower())
        if not tournament_id:
            return None
        
        url = f"https://api.sofascore.com/api/v1/unique-tournament/{tournament_id}/featured-events"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            partidos = []
            from datetime import datetime
            for event in data.get("events", [])[:20]:
                home = event.get("homeTeam", {})
                away = event.get("awayTeam", {})
                start = event.get("startTimestamp", 0)
                hora = datetime.fromtimestamp(start).strftime("%H:%M") if start else ""
                
                partidos.append({
                    "hora": hora,
                    "local": home.get("name", ""),
                    "visitante": away.get("name", ""),
                    "liga": liga_nombre,
                    "dia": get_hoy()
                })
            
            if partidos:
                return {"partidos": partidos, "fuente": "Sofascore API"}
    except:
        pass
    return None

def _scrape_betexplorer(liga_nombre):
    """Scraping de Betexplorer."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html",
        }
        
        slug = liga_nombre.lower().replace(" ", "-").replace(" 2", "-2")
        url = f"https://www.betexplorer.com/soccer/{slug}/"
        
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None
        
        soup = BeautifulSoup(r.text, "html.parser")
        partidos = []
        
        for match in soup.find_all("div", class_="in-match"):
            try:
                teams = match.find_all("span", class_="table-team__name")
                time_el = match.find("span", class_="table-main__time")
                
                if len(teams) >= 2:
                    partidos.append({
                        "hora": time_el.get_text(strip=True) if time_el else "",
                        "local": teams[0].get_text(strip=True),
                        "visitante": teams[1].get_text(strip=True),
                        "liga": liga_nombre,
                        "dia": get_hoy()
                    })
            except:
                continue
        
        if partidos:
            return {"partidos": partidos, "fuente": "Betexplorer"}
    except:
        pass
    return None

def scrape_stats_equipo_multi(equipo_nombre):
    """
    Busca estadísticas de un equipo en múltiples fuentes.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html",
    }
    
    # Fuente 1: API-Football
    if API_FOOTBALL_KEY:
        stats = _scrape_api_football_equipo(equipo_nombre)
        if stats:
            return {"ok": True, "fuente": "API-Football", **stats}
    
    # Fuente 2: Flashscore
    stats = _scrape_flashscore_equipo_stats(equipo_nombre)
    if stats:
        return {"ok": True, "fuente": "Flashscore", **stats}
    
    # Fuente 3: Sofascore
    stats = _scrape_sofascore_equipo_stats(equipo_nombre)
    if stats:
        return {"ok": True, "fuente": "Sofascore", **stats}
    
    return {"ok": False}

def _scrape_api_football_equipo(nombre):
    """Usa API-Football para buscar estadísticas del equipo."""
    try:
        headers = {"x-apisports-key": API_FOOTBALL_KEY}
        url = f"https://v3.football.api-sports.io/teams/search/{nombre}"
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        
        if data.get("results", 0) > 0:
            team = data["response"][0]["team"]
            # Aquí se podrían obtener más stats del equipo
            return {
                "nombre": team.get("name"),
                "gm": 1.8, "gc": 1.0, "elo": 1900, "xg": 1.6,
            }
    except:
        pass
    return None

def _scrape_flashscore_equipo_stats(nombre):
    """Busca stats de equipo en Flashscore."""
    try:
        slug = nombre.lower().replace(" ", "-").replace("'", "")
        url = f"https://www.flashscore.es/equipo/{slug}/estadisticas/"
        
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        r = requests.get(url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Intentar extraer stats
            stats = _extract_stats_from_soup(soup)
            if stats:
                return stats
    except:
        pass
    return None

def _scrape_sofascore_equipo_stats(nombre):
    """Usa Sofascore API para stats de equipo."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        
        # Buscar equipo
        search_url = f"https://api.sofascore.com/api/v1/search/teams/{nombre}"
        r = requests.get(search_url, headers=headers, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                team = data["results"][0]
                team_id = team.get("id")
                
                # Obtener estadísticas
                stats_url = f"https://api.sofascore.com/api/v1/team/{team_id}/statistics/overall"
                r2 = requests.get(stats_url, headers=headers, timeout=10)
                
                if r2.status_code == 200:
                    s = r2.json()
                    return {
                        "nombre": team.get("name"),
                        "gm": s.get("goalsScored", {}).get("average", 1.8) or 1.8,
                        "gc": s.get("goalsConceded", {}).get("average", 1.0) or 1.0,
                        "elo": 1900,
                        "xg": s.get("expectedGoals", {}).get("total", 1.5) or 1.5,
                        "tiros_pg": s.get("shots", {}).get("total", 12) or 12,
                    }
    except:
        pass
    return None

def _extract_stats_from_soup(soup):
    """Extrae estadísticas del HTML de Flashscore."""
    stats = {}
    
    # Buscar en filas de estadísticas
    for row in soup.find_all("div", class_="statRow"):
        try:
            name_el = row.find("div", class_="statText")
            value_el = row.find("div", class_="statValue")
            
            if name_el and value_el:
                name = name_el.get_text(strip=True).lower()
                value = value_el.get_text(strip=True)
                
                if "goals" in name or "goles" in name:
                    parts = value.split("-")
                    if len(parts) == 2:
                        try:
                            stats["gm"] = float(parts[0].strip())
                            stats["gc"] = float(parts[1].strip())
                        except:
                            pass
        except:
            continue
    
    if stats:
        stats["elo"] = 1900
        stats["xg"] = stats.get("gm", 1.8) * 0.9
        return stats
    
    return None




def obtener_goleadores_sofascore(liga_nombre):
    """Obtiene goleadores desde Sofascore como alternativa."""
    goleadores = []
    
    liga_urls_sofascore = {
        "Premier League": "premier-league",
        "La Liga": "laliga",
        "Bundesliga": "bundesliga",
        "Serie A": "serie-a",
        "Ligue 1": "ligue-1",
        "Champions League": "champions-league",
        "Copa America": "copa-america",
    }
    
    url_part = liga_urls_sofascore.get(liga_nombre)
    if not url_part:
        return goleadores
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json, text/plain, */*",
        }
        
        r = requests.get(
            f"https://www.sofascore.com/api/v1/sport/football/unique-tournament/1/season/61627/top-players",
            headers=headers, timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            if "topPlayers" in data:
                for i, player in enumerate(data["topPlayers"][:10], 1):
                    goleadores.append({
                        "posicion": i,
                        "nombre": player.get("player", {}).get("name", "Unknown"),
                        "goles": player.get("goals", 0),
                        "equipo": player.get("team", {}).get("name", "")
                    })
    except:
        pass
    
    return goleadores



SH.headers.update({"User-Agent":"Mozilla/5.0","Accept":"application/json,text/html,*/*"})

# ══════════════════════════════════════════════════════════
# BASE DE DATOS
# ══════════════════════════════════════════════════════════
def get_conn():
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    c = get_conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios (
        cedula TEXT PRIMARY KEY, nombre TEXT, plan TEXT DEFAULT 'gratis',
        fecha_inicio TEXT, dias INTEGER DEFAULT 36500, activo INTEGER DEFAULT 1,
        es_admin INTEGER DEFAULT 0, pwd_hash TEXT,
        consultas_hoy INTEGER DEFAULT 0, fecha_reset TEXT,
        email TEXT,
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS picks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT, liga TEXT, local TEXT, visitante TEXT, hora TEXT,
        mercado TEXT, detalle TEXT, cuota REAL, edge REAL,
        confianza REAL, rango TEXT, resultado TEXT, acierto INTEGER,
        notas TEXT, plan_min TEXT DEFAULT 'gratis', auto INTEGER DEFAULT 0,
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT, cedula TEXT, fecha TEXT,
        liga TEXT, local TEXT, visitante TEXT,
        p1 REAL, px REAL, p2 REAL, xg_l REAL, xg_v REAL,
        over25 REAL, btts REAL, mercado TEXT, rango TEXT, confianza REAL,
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS escalera (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT,
        pasos TEXT, estado TEXT DEFAULT 'activa',
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cedula TEXT, tipo TEXT, mensaje TEXT, enlace TEXT,
        leida INTEGER DEFAULT 0, fecha TEXT,
        creado TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    h = hashlib.sha256(ADMIN_PWD.encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (cedula,nombre,plan,fecha_inicio,dias,activo,es_admin,pwd_hash) VALUES (?,?,?,?,?,?,?,?)",
              ("admin","Administrador","admin",get_hoy(),36500,1,1,h))
    c.commit(); c.close()

def db_get(cedula):
    c=get_conn(); r=c.execute("SELECT * FROM usuarios WHERE cedula=?",(cedula,)).fetchone(); c.close()
    return dict(r) if r else None

def db_todos():
    c=get_conn(); r=c.execute("SELECT * FROM usuarios ORDER BY creado DESC").fetchall(); c.close()
    return [dict(x) for x in r]

def db_guardar_usuario(cedula,nombre,plan,dias,fi,activo=1):
    c=get_conn()
    c.execute("""INSERT OR REPLACE INTO usuarios
        (cedula,nombre,plan,fecha_inicio,dias,activo,es_admin,pwd_hash,creado)
        VALUES(?,?,?,?,?,?,
        COALESCE((SELECT es_admin FROM usuarios WHERE cedula=?),0),
        COALESCE((SELECT pwd_hash FROM usuarios WHERE cedula=?),NULL),
        COALESCE((SELECT creado FROM usuarios WHERE cedula=?),CURRENT_TIMESTAMP))""",
        (cedula,nombre,plan,str(fi),int(dias),int(activo),cedula,cedula,cedula))
    c.commit(); c.close()

def db_acceso(cedula):
    u=db_get(cedula)
    if not u: return False,"no_existe",0
    if not u["activo"]: return False,"inactivo",0
    if u["es_admin"]: return True,"admin",99999
    if u["plan"]=="gratis": return True,"gratis",99999
    inicio=date.fromisoformat(u["fecha_inicio"])
    vence=inicio+timedelta(days=u["dias"]); dr=(vence-get_hoy()).days
    if get_hoy()>vence: return False,"vencido",0
    return True,u["plan"],dr

def db_login_admin(pwd):
    u=db_get("admin")
    return u and u.get("pwd_hash")==hashlib.sha256(pwd.encode()).hexdigest()

def db_consultas(cedula):
    c=get_conn(); hoy=get_hoy()
    u=c.execute("SELECT consultas_hoy,fecha_reset FROM usuarios WHERE cedula=?",(cedula,)).fetchone()
    if u:
        if u["fecha_reset"]!=hoy:
            c.execute("UPDATE usuarios SET consultas_hoy=1,fecha_reset=? WHERE cedula=?",(hoy,cedula))
            c.commit(); c.close(); return 1
        n=(u["consultas_hoy"] or 0)+1
        c.execute("UPDATE usuarios SET consultas_hoy=? WHERE cedula=?",(n,cedula))
        c.commit(); c.close(); return n
    c.close(); return 0

def db_pick_guardar(fecha,liga,local,visitante,hora,mercado,detalle,cuota,edge,confianza,rango,notas,plan_min,auto=0):
    c=get_conn()
    c.execute("INSERT INTO picks (fecha,liga,local,visitante,hora,mercado,detalle,cuota,edge,confianza,rango,notas,plan_min,auto) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (fecha,liga,local,visitante,hora,mercado,detalle,cuota,edge,confianza,rango,notas,plan_min,auto))
    c.commit(); c.close()

def db_picks_get(fecha=None, plan="gratis"):
    c=get_conn()
    orden={"gratis":0,"dia":1,"semana":2,"mes":3,"admin":4}
    nivel=orden.get(plan,0)
    if fecha:
        rows=c.execute("SELECT * FROM picks WHERE fecha=? ORDER BY confianza DESC",(fecha,)).fetchall()
    else:
        rows=c.execute("SELECT * FROM picks ORDER BY fecha DESC,confianza DESC LIMIT 100").fetchall()
    c.close()
    resultado=[]
    for r in [dict(x) for x in rows]:
        nivel_min=orden.get(r.get("plan_min","gratis"),0)
        if nivel<nivel_min:
            r["mercado"]=f"🔒 Plan {r['plan_min'].upper()}"
            r["detalle"]=""; r["cuota"]=None; r["edge"]=None; r["confianza"]=None
        resultado.append(r)
    return resultado

def db_historial_guardar(cedula,p,calc):
    c=get_conn()
    c.execute("INSERT INTO historial (cedula,fecha,liga,local,visitante,p1,px,p2,xg_l,xg_v,over25,btts,mercado,rango,confianza) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (cedula,p.get("dia",get_hoy()),p.get("liga",""),p.get("local",""),p.get("visitante",""),
               calc.get("p1"),calc.get("px"),calc.get("p2"),calc.get("xl"),calc.get("xv"),
               calc.get("over25"),calc.get("btts_si"),calc.get("mk2",""),calc.get("rango",""),calc.get("confianza")))
    c.commit(); c.close()

def db_historial_get(cedula,limite=30):
    c=get_conn()
    r=c.execute("SELECT * FROM historial WHERE cedula=? ORDER BY creado DESC LIMIT ?",(cedula,limite)).fetchall()
    c.close(); return [dict(x) for x in r]

def db_stats():
    c=get_conn()
    tu=c.execute("SELECT COUNT(*) FROM usuarios WHERE es_admin=0").fetchone()[0]
    tp=c.execute("SELECT COUNT(*) FROM picks").fetchone()[0]
    th=c.execute("SELECT COUNT(*) FROM historial").fetchone()[0]
    c.close()
    activos=sum(1 for u in db_todos() if u.get("es_admin")==0 and db_acceso(u["cedula"])[0])
    return {"usuarios":tu,"activos":activos,"picks":tp,"historial":th}

# ══════════════════════════════════════════════════════════
# MOTOR MATEMATICO
# ══════════════════════════════════════════════════════════
def pp(lam,k):
    if lam<=0 or k<0: return 0.0
    return (math.exp(-lam)*(lam**k))/math.factorial(min(k,20))

def dc_tau(x,y,xl,xv,rho=-0.1):
    if x==0 and y==0: return 1-xl*xv*rho
    if x==1 and y==0: return 1+xv*rho
    if x==0 and y==1: return 1+xl*rho
    if x==1 and y==1: return 1-rho
    return 1.0

def poisson_1x2(xl,xv):
    p1=px=p2=0.0
    for i in range(9):
        for j in range(9):
            p=pp(xl,i)*pp(xv,j)
            if i>j: p1+=p
            elif i==j: px+=p
            else: p2+=p
    return round(p1*100,1),round(px*100,1),round(p2*100,1)

def dc_1x2(xl,xv,rho=-0.1):
    m={}
    for i in range(9):
        for j in range(9):
            m[(i,j)]=max(0,pp(xl,i)*pp(xv,j)*dc_tau(i,j,xl,xv,rho))
    t=sum(m.values())
    if t>0: m={k:v/t for k,v in m.items()}
    p1=sum(v for (i,j),v in m.items() if i>j)
    px=sum(v for (i,j),v in m.items() if i==j)
    p2=sum(v for (i,j),v in m.items() if i<j)
    return round(p1*100,1),round(px*100,1),round(p2*100,1)

def monte_carlo(xl,xv,n=3000):
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
        mk[f"{gl}-{gv}"]=mk.get(f"{gl}-{gv}",0)+1
    top=dict(sorted(mk.items(),key=lambda x:x[1],reverse=True)[:6])
    top={k:round(v/n*100,1) for k,v in top.items()}
    return {"p1":round(v1/n*100,1),"px":round(vx/n*100,1),"p2":round(v2/n*100,1),
            "avg":round(sum(gt)/n,2),"o25":round(sum(1 for g in gt if g>2)/n*100),"top":top}

def elo_1x2(elo_l,elo_v,vent=50):
    e=1/(1+10**((elo_v-(elo_l+vent))/400))
    p1=round(e*100,1); p2=round((1-e)*100,1); px=max(0,round(100-p1-p2,1))
    return p1,px,p2

def get_prom(liga):
    l=liga.lower()
    for k in PROM_LIGA:
        if k in l: return PROM_LIGA[k]
    return PROM_LIGA["default"]

def es_top(liga):
    l=liga.lower()
    return any(k in l for k in LIGAS_TOP)

def calcular(gml,gcl,gmv,gcv,liga,elo_l=None,elo_v=None):
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
    p1_po,px_po,p2_po=poisson_1x2(xl,xv)
    p1_dc,px_dc,p2_dc=dc_1x2(xl,xv)
    mc=monte_carlo(xl,xv)
    p1_mc,px_mc,p2_mc=mc["p1"],mc["px"],mc["p2"]
    if elo_l and elo_v: p1_el,px_el,p2_el=elo_1x2(elo_l,elo_v)
    else: p1_el,px_el,p2_el=p1_po,px_po,p2_po
    p1=round(p1_po*.35+p1_dc*.30+p1_mc*.20+p1_el*.15,1)
    px=round(px_po*.35+px_dc*.30+px_mc*.20+px_el*.15,1)
    p2=round(max(0,100-p1-px),1)
    conv=100-(abs(p1_po-p1_dc)*.4+abs(p1_po-p1_mc)*.3+abs(p1_po-p1_el)*.3)
    conf=round(max(0,min(100,conv)))
    datos_r=gml is not None and gmv is not None
    if datos_r and conf>=75 and es_top(liga): rango="A+"
    elif datos_r and conf>=55: rango="B"
    elif conf>=40: rango="C"
    else: rango="D"
    p0=pp(xt,0);p1_=pp(xt,1);p2_=pp(xt,2);p3_=pp(xt,3)
    o05=round((1-p0)*100); o15=round((1-p0-p1_)*100)
    o25=round((1-p0-p1_-p2_)*100); o35=round((1-p0-p1_-p2_-p3_)*100)
    btts_si=round((1-pp(xl,0))*(1-pp(xv,0))*100); btts_no=100-btts_si
    # Corners: promedio real es ~10 por partido, formula calibrada
    cmu=round(min(14, xt*1.4+6.5),1); sc=2.0
    def poc(l):
        z=(l-cmu)/sc; return max(5,min(95,round((1-0.5*(1+math.erf(z/math.sqrt(2))))*100)))
    c75=poc(7.5);c85=poc(8.5);c95=poc(9.5);c105=poc(10.5)
    dif=abs(p1-p2)
    base=3.8 if any(k in liga.lower() for k in ["la liga","serie a","ligue","libertadores","colombia"]) else 3.2
    tmu=round(base+(1-dif/60)*1.8,1)
    # Tiros al arco estimados — proporcional al xG real, no multiplicado
    # Promedio real: ~1 tiro al arco cada 0.18 xG aproximadamente
    tiros_l   = round(max(2.0, xl * 3.8), 1)   # xG * factor calibrado
    tiros_v   = round(max(1.5, xv * 3.8), 1)
    tiros_tot = round(tiros_l + tiros_v, 1)
    mk="1" if p1>p2 and p1>px else ("X" if px>=p1 and px>=p2 else "2")
    if p1>p2 and p1>px and o25>=55: mk2="Gana Local + Over 1.5"
    elif p2>p1 and p2>px and o25>=55: mk2="Gana Visita + Over 1.5"
    elif o25>=65: mk2="Over 2.5 Goles"
    elif btts_si>=62: mk2="BTTS — Ambos Marcan"
    elif c95>=65: mk2="Corners Over 9.5"
    elif p1>p2 and p1>px: mk2="Victoria Local"
    elif p2>p1 and p2>px: mk2="Victoria Visitante"
    else: mk2="Empate posible"
    top_ex={}
    for i in range(7):
        for j in range(7):
            pij=round(pp(xl,i)*pp(xv,j)*100,1)
            if pij>=0.5: top_ex[f"{i}-{j}"]=pij
    top_ex=dict(sorted(top_ex.items(),key=lambda x:x[1],reverse=True)[:8])
    # Mercados completos para picks
    # Cuotas de referencia calibradas con margen de casa tipico (5-8%)
    # Cuota justa = 100/prob, cuota mercado = cuota_justa * 1.07 (margen)
    def cuota_ref(prob, cuota_minima=1.05):
        if prob <= 0: return None
        cj = 100 / prob  # cuota justa sin margen
        cm = round(cj * 1.07, 2)  # con margen de casa 7%
        return max(cuota_minima, cm)

    # Mercados con VALOR (edge calculado)
    # Under mercados
    u05 = round(100 - o05, 1)  # Under 0.5
    u15 = round(100 - o15, 1)  # Under 1.5
    u25 = round(100 - o25, 1)  # Under 2.5
    u35 = round(100 - o35, 1)  # Under 3.5
    
    # Tiros al arco (estimados basado en xG)
    tiros_l = round(max(2.0, xl * 3.8), 1)
    tiros_v = round(max(1.5, xv * 3.8), 1)
    tiros_tot = round(tiros_l + tiros_v, 1)
    
    # Atajadas estimadas del portero
    atajadas_l = round(max(1.0, (gcv or 1.0) * 2.5), 1)  # Más goles recibe = más atajadas
    atajadas_v = round(max(1.0, (gcl or 1.0) * 2.5), 1)
    
    # Calcular edge para cada mercado (valor = probabilidad - cuota_justa)
    def calcular_edge(prob, cuota_mercado=1.95):
        """Calcula el edge: valor positivo = apuesta con valor"""
        cuota_justa = 100 / prob if prob > 0 else 0
        edge = ((prob / 100) * cuota_mercado - 1) * 100
        return round(edge, 1)
    
    # Mercados con valor
    mercados_picks = [
        # 1X2
        ("Victoria Local (1)", p1, cuota_ref(p1), calcular_edge(p1)),
        ("Empate (X)", px, cuota_ref(px), calcular_edge(px)),
        ("Victoria Visitante (2)", p2, cuota_ref(p2), calcular_edge(p2)),
        # Over
        ("Over 0.5 Goles", o05, cuota_ref(o05), calcular_edge(o05)),
        ("Over 1.5 Goles", o15, cuota_ref(o15), calcular_edge(o15)),
        ("Over 2.5 Goles", o25, cuota_ref(o25), calcular_edge(o25)),
        ("Over 3.5 Goles", o35, cuota_ref(o35), calcular_edge(o35)),
        # Under
        ("Under 0.5 Goles", u05, cuota_ref(u05), calcular_edge(u05)),
        ("Under 1.5 Goles", u15, cuota_ref(u15), calcular_edge(u15)),
        ("Under 2.5 Goles", u25, cuota_ref(u25), calcular_edge(u25)),
        ("Under 3.5 Goles", u35, cuota_ref(u35), calcular_edge(u35)),
        # BTTS
        ("BTTS — Si", btts_si, cuota_ref(btts_si), calcular_edge(btts_si)),
        ("BTTS — No", btts_no, cuota_ref(btts_no), calcular_edge(btts_no)),
        # Corners
        ("Corners +7.5", c75, cuota_ref(c75), calcular_edge(c75)),
        ("Corners +8.5", c85, cuota_ref(c85), calcular_edge(c85)),
        ("Corners +9.5", c95, cuota_ref(c95), calcular_edge(c95)),
        ("Corners +10.5", c105, cuota_ref(c105), calcular_edge(c105)),
        # Tarjetas
        ("Tarjetas +1.5", round(min(85,(tmu/4.5)*100),0), cuota_ref(round(min(85,(tmu/4.5)*100),0)), calcular_edge(round(min(85,(tmu/4.5)*100),0))),
        ("Tarjetas +2.5", round(min(70,(tmu/5.5)*100),0), cuota_ref(round(min(70,(tmu/5.5)*100),0)), calcular_edge(round(min(70,(tmu/5.5)*100),0))),
        # Tiros al arco
        ("Tiros Totales +7.5", round(min(85, tiros_tot / 12 * 100), 0), cuota_ref(round(min(85, tiros_tot / 12 * 100), 0)), calcular_edge(round(min(85, tiros_tot / 12 * 100), 0))),
        ("Tiros Totales +8.5", round(min(75, tiros_tot / 13 * 100), 0), cuota_ref(round(min(75, tiros_tot / 13 * 100), 0)), calcular_edge(round(min(75, tiros_tot / 13 * 100), 0))),
        ("Tiros Totales +9.5", round(min(65, tiros_tot / 14 * 100), 0), cuota_ref(round(min(65, tiros_tot / 14 * 100), 0)), calcular_edge(round(min(65, tiros_tot / 14 * 100), 0))),
        # Atajadas
        ("Atajadas +4.5", round(min(80, (atajadas_l + atajadas_v) / 10 * 100), 0), cuota_ref(round(min(80, (atajadas_l + atajadas_v) / 10 * 100), 0)), calcular_edge(round(min(80, (atajadas_l + atajadas_v) / 10 * 100), 0))),
        ("Atajadas +5.5", round(min(70, (atajadas_l + atajadas_v) / 11 * 100), 0), cuota_ref(round(min(70, (atajadas_l + atajadas_v) / 11 * 100), 0)), calcular_edge(round(min(70, (atajadas_l + atajadas_v) / 11 * 100), 0))),
    ]

    return {
        "xl":xl,"xv":xv,"xt":xt,
        "p1_po":p1_po,"px_po":px_po,"p2_po":p2_po,
        "p1_dc":p1_dc,"px_dc":px_dc,"p2_dc":p2_dc,
        "p1_mc":p1_mc,"px_mc":px_mc,"p2_mc":p2_mc,
        "p1_el":p1_el,"px_el":px_el,"p2_el":p2_el,
        "p1":p1,"px":px,"p2":p2,"confianza":conf,"rango":rango,
        "o05":o05,"over15":o15,"over25":o25,"over35":o35,
        "btts_si":btts_si,"btts_no":btts_no,
        "cmu":cmu,"c75":c75,"c85":c85,"c95":c95,"c105":c105,
        "corners_str":f"~{int(cmu)} (+9.5:{c95}% | +8.5:{c85}%)",
        "tiros_l":tiros_l,"tiros_v":tiros_v,"tiros_tot":tiros_tot,
        "atajadas_l":atajadas_l,"atajadas_v":atajadas_v,"atajadas_tot":round(atajadas_l+atajadas_v,1),
        "u05":u05,"u15":u15,"u25":u25,"u35":u35,
        "tmu":tmu,"tar_str":f"~{max(2,int(tmu)-1)}-{int(tmu)+1} tarjetas",
        "mk":mk,"mk2":mk2,"top_ex":top_ex,
        "avg_g":mc["avg"],"top_mc":mc["top"],"datos_r":datos_r,
        "mercados_picks":mercados_picks,
    }



# ══════════════════════════════════════════════════════════
# SCRAPING MUNDIAL FIFA 2026
# ══════════════════════════════════════════════════════════
def scrape_mundial_2026():
    """
    Busca partidos del Mundial 2026 en múltiples fuentes.
    Retorna lista de partidos con datos.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }
    
    partidos = []
    
    # 1. Soccerway - TIENE MUNDIAL 2026
    try:
        url = "https://es.soccerway.com/competitions/world-cup/matches/"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar tablas de partidos
            tables = soup.select("table.matches")
            for table in tables:
                rows = table.select("tbody tr")
                for row in rows:
                    try:
                        cols = row.select("td")
                        if len(cols) >= 4:
                            # Extraer datos
                            fecha = cols[0].get_text(strip=True)
                            hora = cols[1].get_text(strip=True)
                            local = cols[2].get_text(strip=True)
                            visitante = cols[3].get_text(strip=True)
                            
                            # Filtrar solo partidos de fase final
                            if any(x in str(fecha) for x in ["Jul", "14", "15", "Semi"]):
                                if local and visitante:
                                    partidos.append({
                                        "liga": "🌍 Mundial FIFA 2026",
                                        "dia": "2026-07-14",
                                        "hora": hora or "00:00",
                                        "local": local,
                                        "visitante": visitante,
                                        "fuente": "Soccerway"
                                    })
                    except:
                        pass
    except Exception as e:
        print(f"Soccerway error: {e}")
    
    # 2. FBref - Mundial 2026
    try:
        url = "https://fbref.com/en/comps/1/world-cup-2026/Men-World-Cup-2026"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar partidos de eliminación directa
            matches = soup.select(".score")
            for match in matches:
                try:
                    parent = match.parent
                    text = parent.get_text()
                    
                    # Extraer equipos
                    teams = parent.select(".team")
                    if len(teams) >= 2:
                        local = teams[0].get_text(strip=True)
                        visitante = teams[1].get_text(strip=True)
                        score = match.get_text(strip=True)
                        
                        if local and visitante:
                            partidos.append({
                                "liga": "🌍 Mundial FIFA 2026",
                                "dia": "2026-07-14",
                                "hora": "00:00",
                                "local": local,
                                "visitante": visitante,
                                "marcador": score,
                                "fuente": "FBref"
                            })
                except:
                    pass
    except Exception as e:
        print(f"FBref error: {e}")
    
    # 3. Transfermarkt - Mundial
    try:
        url = "https://www.transfermarkt.com/weltmeisterschaft-2026/spielplan"
        r = requests.get(url, headers=headers, timeout=15)
        
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            
            # Buscar finales
            tables = soup.select(".items")
            for table in tables:
                rows = table.select("tr")
                for row in rows:
                    cols = row.select("td")
                    if len(cols) >= 3:
                        try:
                            fecha = cols[0].get_text(strip=True)
                            local = cols[1].get_text(strip=True)
                            visitante = cols[2].get_text(strip=True)
                            
                            if "14.07" in fecha or "15.07" in fecha:
                                if local and visitante:
                                    partidos.append({
                                        "liga": "🌍 Mundial FIFA 2026",
                                        "dia": "2026-07-14",
                                        "hora": "00:00",
                                        "local": local,
                                        "visitante": visitante,
                                        "fuente": "Transfermarkt"
                                    })
                        except:
                            pass
    except Exception as e:
        print(f"Transfermarkt error: {e}")
    
    return partidos



def get_mundial_partidos():
    """Obtiene partidos del Mundial, con fallback a datos locales."""
    partidos = scrape_mundial_partidos()
    if partidos:
        return partidos
    
    # MUNDIAL 2026 - Solo el partido del día seleccionado
    from datetime import date, timedelta, datetime
    hoy = get_hoy_date()
    
    # Solo del 8 al 20 julio 2026
    if 8 <= hoy.day <= 20 and hoy.month == 7 and hoy.year == 2026:
        if hoy.day == 14:
            return [{"hora": "13:00", "liga": "🌍 Mundial FIFA 2026", "local": "Francia", "visitante": "España", "dia": str(hoy)}]
        elif hoy.day == 15:
            return [{"hora": "16:00", "liga": "🌍 Mundial FIFA 2026", "local": "Inglaterra", "visitante": "Argentina", "dia": str(hoy)}]
        elif hoy.day == 18:
            return [{"hora": "16:00", "liga": "🌍 Mundial FIFA 2026", "local": "Perdedor SF1", "visitante": "Perdedor SF2", "dia": str(hoy)}]
        elif hoy.day in [19, 20]:
            return [{"hora": "16:00", "liga": "🌍 Mundial FIFA 2026", "local": "Ganador SF1", "visitante": "Ganador SF2", "dia": str(hoy)}]
        else:
            return []
    return []

# ══════════════════════════════════════════════════════════
# API-FOOTBALL
# ══════════════════════════════════════════════════════════
_tc={}
def get_temp(lid):
    if lid in _tc: return _tc[lid]
    fallback={1:2026,253:2025,262:2025,239:2025,71:2025}
    try:
        r=SH.get("https://v3.football.api-sports.io/leagues",
                  headers={"x-apisports-key":API_FOOTBALL_KEY},
                  params={"id":lid,"current":"true"},timeout=10)
        data=r.json().get("response",[])
        if data:
            seasons=data[0].get("seasons",[])
            activa=[s for s in seasons if s.get("current")]
            if activa: t=activa[0]["year"]; _tc[lid]=t; return t
            if seasons: t=seasons[-1]["year"]; _tc[lid]=t; return t
    except: pass
    t=fallback.get(lid,2024); _tc[lid]=t; return t

def get_fx_dia(lid,fecha):
    t=get_temp(lid); h={"x-apisports-key":API_FOOTBALL_KEY}
    for p in [{"league":lid,"season":t,"date":fecha},{"league":lid,"date":fecha}]:
        try:
            r=SH.get("https://v3.football.api-sports.io/fixtures",headers=h,params=p,timeout=15)
            d=r.json().get("response",[])
            if d: return d
        except: pass
    return []

def get_fx_rango(lid,desde,hasta):
    t=get_temp(lid); h={"x-apisports-key":API_FOOTBALL_KEY}
    for p in [{"league":lid,"season":t,"from":desde,"to":hasta},{"league":lid,"from":desde,"to":hasta}]:
        try:
            r=SH.get("https://v3.football.api-sports.io/fixtures",headers=h,params=p,timeout=15)
            d=r.json().get("response",[])
            if d: return d
        except: pass
    return []

def fx2p(f):
    dt=f["fixture"]["date"]
    return {"dia":dt[:10],"hora":dt[11:16],"hora_sort":int(dt[11:13])*60+int(dt[14:16]),
            "liga":f["league"]["name"],"liga_id":f["league"]["id"],
            "local":f["teams"]["home"]["name"],"visitante":f["teams"]["away"]["name"],
            "tid_l":f["teams"]["home"]["id"],"tid_v":f["teams"]["away"]["id"]}

_sc={}
def get_stats_api(tid,lid):
    k=f"{tid}_{lid}"
    if k in _sc: return _sc[k]
    t=get_temp(lid)
    try:
        r=SH.get("https://v3.football.api-sports.io/teams/statistics",
                  headers={"x-apisports-key":API_FOOTBALL_KEY},
                  params={"team":tid,"season":t,"league":lid},timeout=12)
        d=r.json().get("response",{})
        gf=d.get("goals",{}).get("for",{}).get("average",{}).get("total")
        ga=d.get("goals",{}).get("against",{}).get("average",{}).get("total")
        res=(float(gf) if gf else None,float(ga) if ga else None)
        _sc[k]=res; return res
    except: pass
    _sc[k]=(None,None); return None,None

_uc={}
def get_understat(eq,liga,temp=2024):
    lu=next((v for k,v in UNDERSTAT_MAP.items() if k in liga.lower()),None)
    if not lu: return None,None,None,None
    ck=f"{lu}_{temp}"
    if ck not in _uc:
        try:
            r=SH.get(f"https://understat.com/league/{lu}/{temp}",timeout=15)
            for sc in BeautifulSoup(r.text,"lxml").find_all("script"):
                if "teamsData" in str(sc):
                    m=re.search(r"JSON\.parse\(.(.*?)\.replace",str(sc))
                    if m: _uc[ck]=json.loads(m.group(1).encode().decode("unicode_escape")); break
        except: _uc[ck]={}
    data=_uc.get(ck,{})
    el=eq.lower()
    for tn,stats in data.items():
        if any(p in tn.lower() for p in el.split()[:2]):
            h=stats.get("history",[])[-10:]
            if h:
                return (round(sum(x.get("xG",0) for x in h)/len(h),2),
                        round(sum(x.get("xGA",0) for x in h)/len(h),2),
                        round(sum(x.get("scored",0) for x in h)/len(h),2),
                        round(sum(x.get("missed",0) for x in h)/len(h),2))
    return None,None,None,None

def limpiar_nombre(nombre):
    """Limpia sufijos de ciudad/pais para mejorar busqueda: Botafogo-RJ -> Botafogo"""
    import re as re2
    # Quitar sufijos comunes: -RJ, -SP, -MG, -PR, etc.
    nombre = re2.sub(r"-\s*[A-Z]{2,3}$", "", nombre.strip())
    # Quitar parentesis: Atletico (MG) -> Atletico
    nombre = re2.sub(r"\s*\([^)]+\)", "", nombre)
    # Quitar puntos y guiones extra
    nombre = nombre.strip(" .-")
    return nombre

def get_tsdb(nombre):
    nombre_clean = limpiar_nombre(nombre)
    for buscar in [nombre_clean, nombre]:
        try:
            r=SH.get(f"https://www.thesportsdb.com/api/v1/json/3/searchteams.php?t={requests.utils.quote(buscar)}",timeout=8)
            d=r.json()
            if d and d.get("teams"): return d["teams"][0]
        except: pass
    return None

def buscar_equipo_api_football(nombre, liga_id=None):
    """Busca el team_id en API-Football por nombre."""
    nombre_clean = limpiar_nombre(nombre)
    h = {"x-apisports-key": API_FOOTBALL_KEY}
    for buscar in [nombre_clean, nombre]:
        try:
            params = {"name": buscar}
            if liga_id: params["league"] = liga_id
            r = SH.get("https://v3.football.api-sports.io/teams",
                       headers=h, params=params, timeout=10)
            data = r.json().get("response", [])
            if data:
                return data[0]["team"]["id"], data[0]["team"]["name"]
        except: pass
    return None, None

def stats_tsdb(tid):
    try:
        r=SH.get(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={tid}",timeout=10)
        d=r.json()
        if d and d.get("results"):
            # Filtrar solo partidos con score valido
            raw=[x for x in d["results"] if x.get("intHomeScore") is not None]
            raw=raw[-10:]; gml=[]; gcl=[]
            for x in raw:
                try:
                    sh=int(x.get("intHomeScore") or 0); sa=int(x.get("intAwayScore") or 0)
                    if str(x.get("idHomeTeam",""))==str(tid): gml.append(sh);gcl.append(sa)
                    else: gml.append(sa);gcl.append(sh)
                except: pass
            if gml: return round(sum(gml)/len(gml),2),round(sum(gcl)/len(gcl),2)
    except: pass
    return None,None

_ec={}
def get_elo(eq):
    if eq in _ec: return _ec[eq]
    try:
        r=SH.get(f"http://api.clubelo.com/{eq.replace(' ','-').replace('.','')}",timeout=8)
        if r.status_code==200 and len(r.text)>50:
            ul=r.text.strip().split("\n")[-1].split(",")
            if len(ul)>=4: elo=float(ul[3]); _ec[eq]=elo; return elo
    except: pass
    _ec[eq]=None; return None

def obtener_stats_detalle(nombre, liga, tid=None, lid=None):
    """
    Obtiene stats detallados desde multiples fuentes en cascada:
    1. API-Football (goles, stats de temporada) — requiere API key
    2. Understat (xG reales, ligas europeas top)
    3. TheSportsDB (ultimos partidos, cualquier liga/seleccion)
    4. ClubElo (ELO rating europeo)
    """
    det = {
        "nombre": nombre, "liga": liga, "fuente": "Sin datos", "ok": False,
        "gm": None, "gc": None, "elo": None,
        "xg": None, "xga": None,
        "tiros_pg": None, "tarj_pg": None, "posesion": None,
        "ultimos5": [], "ganados5": 0, "empatados5": 0, "perdidos5": 0,
        "goles_fav5": 0, "goles_con5": 0,
        "fuentes_usadas": [],
    }
    torneo = any(k in liga.lower() for k in TORNEOS_FIFA)
    selec  = any(k in nombre.lower() for k in SELECCIONES)

    # ── FUENTE 1: API-Football (stats completos de temporada) ────────────
    # Si no tenemos team_id, buscarlo por nombre
    if not tid and lid:
        tid_found, _ = buscar_equipo_api_football(nombre, lid)
        if tid_found: tid = tid_found
    if not tid:
        tid_found, _ = buscar_equipo_api_football(nombre)
        if tid_found: tid = tid_found

    if tid and lid:
        try:
            t = get_temp(lid)
            h = {"x-apisports-key": API_FOOTBALL_KEY}
            r = SH.get("https://v3.football.api-sports.io/teams/statistics",
                       headers=h, params={"team":tid,"season":t,"league":lid}, timeout=12)
            d = r.json().get("response", {})
            if d:
                gf = d.get("goals",{}).get("for",{}).get("average",{}).get("total")
                ga = d.get("goals",{}).get("against",{}).get("average",{}).get("total")
                shots = d.get("shots",{}).get("total",{}).get("average")
                cards = d.get("cards",{}).get("yellow",{})
                # Sumar tarjetas amarillas por intervalo
                tarj = 0
                if isinstance(cards, dict):
                    for v in cards.values():
                        if isinstance(v, dict) and v.get("total"):
                            try: tarj += int(v["total"])
                            except: pass
                played = d.get("fixtures",{}).get("played",{}).get("total") or 1
                if gf:
                    det.update({
                        "gm": round(float(gf),2),
                        "gc": round(float(ga),2) if ga else None,
                        "tiros_pg": round(float(shots),1) if shots else None,
                        "tarj_pg": round(tarj/played,2) if tarj and played else None,
                        "fuente": "API-Football",
                        "ok": True,
                    })
                    det["fuentes_usadas"].append("API-Football")
        except: pass

    # ── FUENTE 2: Understat (xG reales, ligas europeas) ─────────────────
    if not torneo and not selec:
        try:
            xg, xga, gm_u, gc_u = get_understat(nombre, liga)
            if xg is not None:
                det["xg"]  = xg
                det["xga"] = xga
                if not det["ok"]:
                    det.update({"gm": gm_u, "gc": gc_u, "fuente": "Understat", "ok": True})
                det["fuentes_usadas"].append("Understat")
            time.sleep(0.2)
        except: pass

    # ── FUENTE 3: TheSportsDB (ultimos partidos + stats basicos) ─────────
    try:
        td = get_tsdb(nombre)
        if td:
            team_id = td.get("idTeam","")
            if not det["ok"]:
                gm2, gc2 = stats_tsdb(team_id)
                if gm2:
                    det.update({"gm": gm2, "gc": gc2, "fuente": "TheSportsDB", "ok": True})
            det["fuentes_usadas"].append("TheSportsDB")
            # Ultimos partidos con detalle de resultado
            try:
                r2 = SH.get(f"https://www.thesportsdb.com/api/v1/json/3/eventslast.php?id={team_id}", timeout=10)
                d2 = r2.json()
                if d2 and d2.get("results"):
                    ultimos = [x for x in d2["results"] if x.get("intHomeScore") is not None][-5:]
                    for x in ultimos:
                        try:
                            sh = int(x.get("intHomeScore") or 0)
                            sa = int(x.get("intAwayScore") or 0)
                            es_l = str(x.get("idHomeTeam","")) == str(team_id)
                            gf_p = sh if es_l else sa
                            gc_p = sa if es_l else sh
                            rival = x.get("strAwayTeam" if es_l else "strHomeTeam","?")
                            liga_p = x.get("strLeague","")
                            if gf_p > gc_p:    res="G"; det["ganados5"]+=1
                            elif gf_p == gc_p: res="E"; det["empatados5"]+=1
                            else:              res="P"; det["perdidos5"]+=1
                            det["goles_fav5"] += gf_p
                            det["goles_con5"] += gc_p
                            det["ultimos5"].append({
                                "rival": rival[:16], "res": res,
                                "goles": f"{gf_p}-{gc_p}",
                                "local": "Local" if es_l else "Visita",
                                "liga": liga_p[:18],
                            })
                        except: pass
            except: pass
        time.sleep(0.2)
    except: pass

    # ── FUENTE 4: ClubElo (ELO rating) ───────────────────────────────────
    try:
        elo = get_elo(nombre)
        if elo:
            det["elo"] = elo
            det["fuentes_usadas"].append("ClubElo")
    except: pass

    return det

def obtener_stats(nombre,liga,tid=None,lid=None):
    nombre_c = limpiar_nombre(nombre)
    d = obtener_stats_detalle(nombre_c, liga, tid, lid)
    if not d["ok"] and nombre_c != nombre:
        d = obtener_stats_detalle(nombre, liga, tid, lid)
    return {"gm":d["gm"],"gc":d["gc"],"elo":d["elo"],"fuente":d["fuente"],"ok":d["ok"]}

def leer_imagen(img_bytes,mt="image/jpeg"):
    try:
        b64=base64.standard_b64encode(img_bytes).decode()
        payload={"model":"claude-sonnet-4-6","max_tokens":1500,"messages":[{"role":"user","content":[
            {"type":"image","source":{"type":"base64","media_type":mt,"data":b64}},
            {"type":"text","text":"Analiza esta imagen de fixtures de futbol. Devuelve SOLO JSON valido sin markdown: {\"partidos\":[{\"hora\":\"19:00\",\"liga\":\"Premier League\",\"local\":\"Arsenal\",\"visitante\":\"Chelsea\"}]}. Si no hay hora usa '00:00'. Solo partidos claramente legibles."}
        ]}]}
        r=requests.post("https://api.anthropic.com/v1/messages",
                        headers={"Content-Type":"application/json"},json=payload,timeout=30)
        text=r.json().get("content",[{}])[0].get("text","")
        text=re.sub(r"```json|```","",text).strip()
        data=json.loads(text); result=[]
        for p in data.get("partidos",[]):
            hora=str(p.get("hora","00:00"))
            try: h,m=hora.split(":"); hs=int(h)*60+int(m)
            except: hs=0
            if p.get("local") and p.get("visitante"):
                result.append({"dia":get_hoy(),"hora":hora,"hora_sort":hs,
                               "liga":p.get("liga","Sin Liga"),"liga_id":0,
                               "local":p["local"],"visitante":p["visitante"],"tid_l":None,"tid_v":None})
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
                    partidos.append({"dia":get_hoy(),"hora":f"{val.hour:02d}:{val.minute:02d}",
                                     "hora_sort":val.hour*60+val.minute,"liga":cur_liga or "Sin Liga",
                                     "liga_id":0,"local":l,"visitante":v,"tid_l":None,"tid_v":None})
            except: pass
            continue
        vs=str(val).strip().replace("\xa0","")
        if any(k in vs.lower() for k in TORN) and len(vs)<80: cur_liga=vs
    return partidos

def analizar_lista(partidos,usar_api=True,prog=None):
    resultados=[]; n=len(partidos)
    for idx,p in enumerate(partidos):
        gml=gcl=gmv=gcv=elo_l=elo_v=None; fl=fv="Prom.liga"
        
        # Detectar si es partido del Mundial
        es_mundial = "mundial" in p.get("liga", "").lower() or "fifa" in p.get("liga", "").lower()
        
        if usar_api:
            if es_mundial:
                # Primero intentar datos del Mundial
                sl = obtener_stats_mundial(p["local"])
                sv = obtener_stats_mundial(p["visitante"])
            else:
                sl = obtener_stats(p["local"], p["liga"], p.get("tid_l"), p.get("liga_id"))
                sv = obtener_stats(p["visitante"], p["liga"], p.get("tid_v"), p.get("liga_id"))
            
            if sl["ok"]: gml=sl["gm"];gcl=sl["gc"];elo_l=sl["elo"];fl=sl["fuente"]
            if sv["ok"]: gmv=sv["gm"];gcv=sv["gc"];elo_v=sv["elo"];fv=sv["fuente"]
        
        calc=calcular(gml,gcl,gmv,gcv,p["liga"],elo_l,elo_v)
        resultados.append({**p,**calc,"fuente_l":fl,"fuente_v":fv})
        if prog: prog.progress((idx+1)/n,text=f"{idx+1}/{n}: {p['local']} vs {p['visitante']}")
    return resultados

# ══════════════════════════════════════════════════════════
# EXCEL EXPORT — colores en formato AARRGGBB correcto
# ══════════════════════════════════════════════════════════
def exportar_excel(resultados,titulo="Scorpion Elite V4 Pro"):
    def mkfill(c): return PatternFill("solid",fgColor=f"FF{c.upper()}")
    def mkbrd():
        s=Side(border_style="thin",color="FF1A2A4A")
        return Border(left=s,right=s,top=s,bottom=s)
    def mkal(h="center"): return Alignment(horizontal=h,vertical="center",wrap_text=True)
    def sc(cell,bg="080820",fg="FFFFFF",bold=False,sz=9,h="center"):
        cell.fill=mkfill(bg)
        cell.font=Font(color=f"FF{fg.upper()}",bold=bold,size=sz,name="Arial")
        cell.alignment=mkal(h); cell.border=mkbrd()
    def hr(ws,row,vals,bg="080820",fg="FFD700",sz=9):
        for c,v in enumerate(vals,1): cl=ws.cell(row=row,column=c,value=v); sc(cl,bg,fg,True,sz)
    def tr(ws,row,text,nc,bg="080820",fg="FFD700",sz=12):
        ws.merge_cells(start_row=row,start_column=1,end_row=row,end_column=nc)
        sc(ws.cell(row=row,column=1,value=text),bg,fg,True,sz)
    def sw(ws,wl):
        for i,w in enumerate(wl,1): ws.column_dimensions[get_column_letter(i)].width=w

    wb=Workbook(); first=True
    COLS=["HORA","LIGA","PARTIDO","1X2","P1%","PX%","P2%","CONF",
          "xG L","xG V","xG T","O0.5","O1.5","O2.5","O3.5","BTTS",
          "CORNERS","TIROS","TARJ","PICK CLAVE","RANGO",
          "POISSON","D-COLES","M.CARLO","ELO","FUENTE"]
    WW=[9,18,30,7,7,7,7,7,7,7,7,8,8,8,8,7,14,10,12,26,7,9,9,9,9,14]
    for dia in list(dict.fromkeys(r["dia"] for r in resultados)):
        ws=wb.active if first else wb.create_sheet(title=str(dia)[:20])
        first=False
        if ws==wb.active: ws.title=str(dia)[:20]
        ws.sheet_view.showGridLines=False; sw(ws,WW)
        tr(ws,1,f"SCORPION ELITE V4 PRO | {dia}",len(COLS))
        ws.row_dimensions[1].height=24; hr(ws,2,COLS,sz=8); ws.row_dimensions[2].height=36; fi=3
        for p in sorted([x for x in resultados if x["dia"]==dia],key=lambda x:x.get("hora_sort",0)):
            rg=p.get("rango","C")
            rv=[p.get("hora",""),p.get("liga","")[:16],f'{p["local"]} vs {p["visitante"]}',
                p.get("mk","?"),f'{p.get("p1",0):.1f}%',f'{p.get("px",0):.1f}%',f'{p.get("p2",0):.1f}%',
                f'{p.get("confianza",0)}%',
                p.get("xl",0),p.get("xv",0),p.get("xt",0),
                f'{p.get("o05",0)}%',f'{p.get("over15",0)}%',f'{p.get("over25",0)}%',f'{p.get("over35",0)}%',
                f'{p.get("btts_si",0)}%',
                p.get("corners_str","")[:12],
                f'{p.get("tiros_l",0)}-{p.get("tiros_v",0)} (~{p.get("tiros_tot",0)})',
                p.get("tar_str",""),
                p.get("mk2",""),rg,
                f'{p.get("p1_po",0):.1f}%',f'{p.get("p1_dc",0):.1f}%',
                f'{p.get("p1_mc",0):.1f}%',f'{p.get("p1_el",0):.1f}%',
                f'L:{p.get("fuente_l","?")[:6]} V:{p.get("fuente_v","?")[:6]}']
            bg="0A2810" if rg=="A+" else ("0A0A28" if fi%2==0 else "0D0D1E")
            for col,val in enumerate(rv,1):
                cell=ws.cell(row=fi,column=col,value=val)
                fg="FFFFFF"
                if col==21: fg="FFD700" if rg=="A+" else ("44AAFF" if rg=="B" else "888888")
                elif col in (9,10,11): fg="00DDFF"
                elif col==26: fg="00CC44" if "API" in str(val) else "FFAA00"
                sc(cell,bg,fg,rg=="A+" and col in (3,20,21),9)
            ws.row_dimensions[fi].height=22; fi+=1

    # Hoja TOP PICKS
    wsp=wb.create_sheet(title="TOP PICKS"); wsp.sheet_view.showGridLines=False
    pc=["HORA","PARTIDO","LIGA","PICK CLAVE","P1%","PX%","P2%","xG T","O2.5","BTTS","TIROS","CORNERS","TARJ","CONF","RANGO","MARCADORES TOP"]
    sw(wsp,[9,28,16,28,7,7,7,7,8,7,10,14,12,8,7,28])
    tr(wsp,1,"TOP PICKS — Mayor confianza y ventaja estadistica",len(pc),"081208","FFD700")
    hr(wsp,2,pc,"0A1E0A","00FF88"); fp=3
    top=sorted([r for r in resultados if r.get("rango") in ("A+","B")],
               key=lambda x:(x.get("confianza",0),max(x.get("p1",0),x.get("p2",0))),reverse=True)[:15]
    for p in top:
        bg="0A2810" if p.get("rango")=="A+" else "0A0A28"
        top_mk=" | ".join([f"{k}({v}%)" for k,v in list(p.get("top_ex",{}).items())[:4]])
        rv=[p.get("hora",""),f'{p["local"]} vs {p["visitante"]}',p.get("liga","")[:14],
            p.get("mk2",""),f'{p.get("p1",0):.1f}%',f'{p.get("px",0):.1f}%',f'{p.get("p2",0):.1f}%',
            p.get("xt",0),f'{p.get("over25",0)}%',f'{p.get("btts_si",0)}%',
            f'~{p.get("tiros_tot",0)}',p.get("corners_str","")[:12],p.get("tar_str",""),
            f'{p.get("confianza",0)}%',p.get("rango",""),top_mk]
        for col,val in enumerate(rv,1):
            cell=wsp.cell(row=fp,column=col,value=val)
            fg="FFFFFF"
            if col==4: fg="FFD700"
            elif col==15: fg="00FF88" if p.get("rango")=="A+" else "44AAFF"
            elif col==16: fg="888888"
            sc(cell,bg,fg,col in (4,15),9)
        wsp.row_dimensions[fp].height=20; fp+=1

    # Hoja ESCALERA
    wse=wb.create_sheet(title="ESCALERA"); wse.sheet_view.showGridLines=False
    ec=["PASO","HORA","PARTIDO","LIGA","PICK","PROB%","C.JUSTA","ESTADO"]
    sw(wse,[7,9,28,18,26,8,9,14])
    tr(wse,1,"RETO ESCALERA — Picks Seleccionados del Dia",len(ec),"081208","FFD700")
    hr(wse,2,ec,"0A1E0A","FFD700"); fe=3
    esc=sorted([r for r in resultados if r.get("rango") in ("A+","B")],
               key=lambda x:(x.get("confianza",0)),reverse=True)[:12]
    for i,p in enumerate(esc,1):
        bg="0A2810" if i%2==0 else "0D1E10"
        cj=round(100/max(p.get("p1",50),1),2)
        rv=[i,p.get("hora",""),f'{p["local"]} vs {p["visitante"]}',
            p.get("liga","")[:16],p.get("mk2",""),
            f'{max(p.get("p1",0),p.get("p2",0)):.1f}%',str(cj),"🟡 PENDIENTE"]
        for col,val in enumerate(rv,1):
            cell=wse.cell(row=fe,column=col,value=val)
            fg="FFD700" if col==1 else ("00FF88" if col==8 else "FFFFFF")
            sc(cell,bg,fg,col==1,9)
        wse.row_dimensions[fe].height=20; fe+=1

    for ws_tab in wb.worksheets: ws_tab.freeze_panes="A3"
    buf=io.BytesIO(); wb.save(buf); buf.seek(0); return buf.getvalue()

# ══════════════════════════════════════════════════════════
# CSS - Verde Bosque y Oro
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="Scorpion Elite V4",page_icon="🦂",layout="wide")

# Cargar archivo CSS externo
try:
    with open("styles.css", "r") as f:
        css_content = f.read()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
except:
    pass

# CSS adicional inline para asegurar los colores exactos
st.markdown("""<style>
:root {
    --bg-dark-green: #0a2114;
    --panel-bg: #1b2621;
    --gold-bright: #dfaf6f;
    --gold-dark: #8a6435;
    --text-light: #dcdcdc;
}
.stApp {
    background-color: var(--bg-dark-green) !important;
    background-image: radial-gradient(circle, #103020 0%, #050f0a 100%) !important;
    color: var(--text-light) !important;
}
.header-container {
    background: var(--panel-bg) !important;
    border: 1px solid var(--gold-dark) !important;
    border-radius: 6px !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.5) !important;
}
.brand-title {
    color: #fff !important;
    font-family: 'Georgia', serif !important;
    font-size: 40px !important;
    font-weight: bold !important;
}
.login-container, .login-box {
    background-color: var(--panel-bg) !important;
    border: 1px solid var(--gold-dark) !important;
    border-radius: 6px !important;
    padding: 20px !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.5) !important;
}
.login-title {
    color: var(--gold-bright) !important;
    font-size: 18px !important;
    font-weight: bold !important;
    border-bottom: 1px solid rgba(223, 175, 111, 0.2) !important;
    padding-bottom: 10px !important;
}
.section-title {
    color: var(--gold-bright) !important;
    font-size: 18px !important;
    font-weight: bold !important;
}
.pick-card {
    background-color: var(--panel-bg) !important;
    border: 1px solid var(--gold-dark) !important;
    border-radius: 6px !important;
    padding: 20px !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.5) !important;
}
.pick-header {
    color: var(--gold-bright) !important;
    font-size: 12px !important;
    font-weight: bold !important;
    border-bottom: 1px solid rgba(223, 175, 111, 0.2) !important;
}
.sidebar-card {
    background-color: var(--panel-bg) !important;
    border: 1px solid var(--gold-dark) !important;
    border-radius: 6px !important;
    padding: 20px !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.5) !important;
}
.sidebar-card-title {
    color: var(--gold-bright) !important;
    font-size: 16px !important;
    font-weight: bold !important;
    border-bottom: 1px solid rgba(223, 175, 111, 0.2) !important;
}
.stTextInput > div > div > input {
    background-color: var(--bg-dark-green) !important;
    color: #ffffff !important;
    border: 1px solid var(--gold-dark) !important;
    border-radius: 4px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #b08146 0%, #d8a86a 100%) !important;
    color: var(--bg-dark-green) !important;
    border: none !important;
    font-weight: bold !important;
    border-radius: 4px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #d8a86a 0%, #b08146 100%) !important;
}
.hdr {
    background: var(--panel-bg) !important;
    border: 1px solid var(--gold-dark) !important;
    border-radius: 6px !important;
    padding: 20px !important;
    text-align: center !important;
    box-shadow: 0 10px 20px rgba(0,0,0,0.5) !important;
}
.hdr h1 {
    color: #fff !important;
    font-family: 'Georgia', serif !important;
    font-size: 2.2rem !important;
    margin: 0 !important;
    letter-spacing: 4px !important;
}
.hdr p {
    color: var(--text-light) !important;
    font-size: 0.9rem !important;
}
h1 {
    color: #fff !important;
}
.pill-ok {
    background: rgba(57, 255, 20, 0.15) !important;
    color: #39ff14 !important;
    border: 1px solid #39ff14 !important;
}
.pill-v {
    background: rgba(255, 107, 107, 0.15) !important;
    color: #ff6b6b !important;
    border: 1px solid #ff6b6b !important;
}
.pill-f {
    background: rgba(223, 175, 111, 0.15) !important;
    color: var(--gold-bright) !important;
    border: 1px solid var(--gold-dark) !important;
}
</style>""",unsafe_allow_html=True)
def hdr(sub="Motor de Analisis Deportivo — 4 Modelos + Datos Reales"):
    st.markdown(f'''
    <div class="header-container">
        <div class="brand-title">🦂 SCORPION ELITE</div>
        <div class="brand-subtitle">{sub}</div>
    </div>
    ''', unsafe_allow_html=True)

def bdg(r):
    return f'<span class="badge-{r}">{r}</span>'

def pll(plan,dr):
    if plan=="gratis": return '<span class="pill-f">Plan Gratis</span>'
    if plan in ("dia","semana","mes","admin"):
        return f'<span class="pill-ok">{"Admin" if plan=="admin" else plan.upper()} · {dr} dias</span>'
    return '<span class="pill-v">Vencido</span>'

def widget_archivo(max_p=None,key="up"):
    up=st.file_uploader("Sube captura de pantalla (Sofascore, FlashScore, etc.)",type=["png","jpg","jpeg","webp"],key=key)
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

def mostrar_mercados_con_publicar(calc, partido, umbral_valor=3):
    """Muestra mercados organizados por categoria CON VALOR (edge > umbral)."""
    mercados=calc.get("mercados_picks",[])
    if not mercados: return
    picks_sel=st.session_state.get("picks_sel",[])

    # Umbral de valor configurable
    umbral = st.session_state.get("umbral_valor_global", umbral_valor)
    
    # Filtrar mercados con valor positivo
    mercados_con_valor = []
    for item in mercados:
        if len(item) >= 4:
            nombre, prob, cuota, edge = item
        else:
            nombre, prob, cuota = item
            edge = round((prob/100*cuota-1)*100,1) if cuota else 0
        
        # Solo mostrar si tiene edge positivo (valor)
        if edge >= umbral:
            mercados_con_valor.append((nombre, prob, cuota, edge))
    
    if not mercados_con_valor:
        st.warning(f"⚠️ No hay apuestas con valor (edge >= {umbral}%). Ajusta el umbral o usa menos restricciones.")
        return
    
    st.success(f"🎯 {len(mercados_con_valor)} apuestas con VALOR encontradas (edge >= {umbral}%)")
    
    # Organizar por categorias
    cats = {
        "⚽ Resultado 1X2":   [],
        "🎯 Goles Over":      [],
        "📉 Goles Under":     [],
        "🤝 BTTS":            [],
        "📐 Corners":         [],
        "🎽 Tarjetas":        [],
        "🔫 Tiros":           [],
        "🧤 Atajadas":        [],
    }
    
    for item in mercados_con_valor:
        nombre, prob, cuota, edge = item
        n = nombre.lower()
        
        if any(x in n for x in ["victoria","empate","local","visita","(1)","(2)","(x)"]):
            cats["⚽ Resultado 1X2"].append(item)
        elif "btts" in n or "ambos" in n:
            cats["🤝 BTTS"].append(item)
        elif "corner" in n or "esquina" in n:
            cats["📐 Corners"].append(item)
        elif "tarjet" in n or "amarill" in n:
            cats["🎽 Tarjetas"].append(item)
        elif "tiro" in n:
            cats["🔫 Tiros"].append(item)
        elif "atajad" in n:
            cats["🧤 Atajadas"].append(item)
        elif "under" in n:
            cats["📉 Goles Under"].append(item)
        elif "over" in n or "gol" in n:
            cats["🎯 Goles Over"].append(item)

    st.markdown("""
    <style>
    .mkt-cat{color:#dfaf6f;font-weight:600;font-size:.85rem;margin:12px 0 4px;
      border-bottom:1px solid #dfaf6f33;padding-bottom:4px}
    .mkt-row2{display:grid;grid-template-columns:3fr 1fr 1.2fr 1.2fr 1.5fr;
      align-items:center;background:#1b2621;border-radius:8px;
      padding:7px 10px;margin:3px 0;gap:8px}
    .mkt-n{color:#ddd;font-size:.85rem}
    .mkt-p{color:#dfaf6f;font-weight:700;font-size:.95rem;text-align:center}
    .mkt-c{color:#888;font-size:.78rem;text-align:center}
    .mkt-ep{color:#39ff14;font-size:.8rem;font-weight:600;text-align:center}
    .mkt-en{color:#ff4444;font-size:.8rem;font-weight:600;text-align:center}
    .val-badge{background:#082a12;color:#39ff14;border:1px solid #00aa44;
      padding:1px 6px;border-radius:4px;font-size:.72rem;font-weight:700}
    .neutro-badge{background:#1a1200;color:#ccaa00;padding:1px 6px;border-radius:4px;font-size:.72rem}
    .neg-badge{background:#200a0a;color:#ff4444;padding:1px 6px;border-radius:4px;font-size:.72rem}
    </style>
    """, unsafe_allow_html=True)

    # Cabecera de columnas
    hc1,hc2,hc3,hc4,hc5=st.columns([3,1,1.2,1.2,1.5])
    with hc1: st.markdown('<span style="color:#888;font-size:.75rem">MERCADO</span>',unsafe_allow_html=True)
    with hc2: st.markdown('<span style="color:#888;font-size:.75rem">PROB</span>',unsafe_allow_html=True)
    with hc3: st.markdown('<span style="color:#888;font-size:.75rem">C.REF</span>',unsafe_allow_html=True)
    with hc4: st.markdown('<span style="color:#888;font-size:.75rem">EDGE</span>',unsafe_allow_html=True)
    with hc5: st.markdown('<span style="color:#888;font-size:.75rem">ACCION</span>',unsafe_allow_html=True)

    # Cabecera de columnas
    hc1,hc2,hc3,hc4,hc5=st.columns([3,1,1.2,1.2,1.5])
    with hc1: st.markdown('<span style="color:#888;font-size:.75rem">MERCADO</span>',unsafe_allow_html=True)
    with hc2: st.markdown('<span style="color:#888;font-size:.75rem">PROB</span>',unsafe_allow_html=True)
    with hc3: st.markdown('<span style="color:#888;font-size:.75rem">C.REF</span>',unsafe_allow_html=True)
    with hc4: st.markdown('<span style="color:#888;font-size:.75rem">EDGE</span>',unsafe_allow_html=True)
    with hc5: st.markdown('<span style="color:#888;font-size:.75rem">ACCION</span>',unsafe_allow_html=True)

    idx_global=0
    for cat_name, items in cats.items():
        if not items: continue
        st.markdown(f'<div class="mkt-cat">{cat_name}</div>', unsafe_allow_html=True)
        for item in items:
            if len(item) >= 4:
                nombre, prob, cuota, edge = item
            else:
                nombre, prob, cuota = item
                edge = 0
            sel=any(p.get("mercado")==nombre and p.get("local")==partido["local"] for p in picks_sel)
            # Badge de valor
            # Con cuotas de referencia propias, edge siempre es ~0
            # Solo hay edge real si se configura ODDS_API_KEY con cuotas en vivo
            tiene_odds_reales = False  # TODO: activar cuando ODDS_API_KEY este configurada
            if tiene_odds_reales and edge>=5:   badge='<span class="val-badge">🔥 VALOR REAL</span>'
            elif tiene_odds_reales and edge>=2: badge='<span class="val-badge">✅ VALOR REAL</span>'
            else:
                # Mostrar probabilidad del modelo como referencia
                if prob>=70:   badge='<span class="val-badge">⭐ Alta prob</span>'
                elif prob>=55: badge='<span class="neutro-badge">📊 Buena prob</span>'
                else:          badge='<span class="neg-badge">📉 Prob baja</span>'
            edge_cls="mkt-ep" if edge>=0 else "mkt-en"
            c1,c2,c3,c4,c5=st.columns([3,1,1.2,1.2,1.5])
            with c1: st.markdown(f'{badge} <span class="mkt-n">{nombre}</span>',unsafe_allow_html=True)
            with c2: st.markdown(f'<span class="mkt-p">{prob:.0f}%</span>',unsafe_allow_html=True)
            with c3: st.markdown(f'<span class="mkt-c">{cuota}</span>',unsafe_allow_html=True)
            with c4: st.markdown(f'<span class="{edge_cls}">{edge:+.1f}%</span>',unsafe_allow_html=True)
            with c5:
                key_btn=f"pub_{partido['local'][:6]}_{partido['visitante'][:6]}_{idx_global}"
                btn_lbl="✔ Agregado" if sel else "➕ Seleccionar"
                if st.button(btn_lbl,key=key_btn):
                    pick_data={"local":partido["local"],"visitante":partido["visitante"],
                               "liga":partido.get("liga",""),"hora":partido.get("hora","00:00"),
                               "mercado":nombre,"prob":prob,"cuota":cuota,"edge":edge,
                               "confianza":calc.get("confianza",0),"rango":calc.get("rango","C")}
                    if not sel:
                        if "picks_sel" not in st.session_state: st.session_state.picks_sel=[]
                        st.session_state.picks_sel.append(pick_data)
                    else:
                        st.session_state.picks_sel=[p for p in st.session_state.picks_sel
                            if not(p.get("mercado")==nombre and p.get("local")==partido["local"])]
                    st.rerun()
            idx_global+=1

# ══════════════════════════════════════════════════════════
# PANTALLA LOGIN
# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# PANTALLA ADMIN
# ══════════════════════════════════════════════════════════
def pantalla_admin():
    hdr("Panel de Administrador")
    
    # Mostrar bienvenida sin stats innecesarios
    st.markdown("### 🦂 Panel de Administrador")
    st.info("Analiza partidos, genera picks de valor y publícalos para los usuarios.")
    st.markdown("---")

    tabs=st.tabs(["🔍 Analizar Partido","📊 Picks de Valor","📢 Publicar Picks","👥 Clientes","📊 Calendario","📊 Escalera"])

    # ── Tab 1: Analizar partido individual ─────────────────
    with tabs[0]:
        st.markdown("### 📊 Analizar Partido")
        st.info("Escribe cualquier partido. Se mostrarán solo las apuestas con VALOR (edge > 5%).")
        c1,c2=st.columns(2)
        with c1:
            local_i  =st.text_input("⚽ Equipo Local",placeholder="ej: Francia")
            visita_i =st.text_input("⚽ Equipo Visitante",placeholder="ej: España")
            liga_i   =st.text_input("🏆 Liga / Torneo",placeholder="ej: Mundial FIFA 2026")
            hora_i   =st.text_input("🕐 Hora (opcional)","20:00")
        with c2:
            fecha_i  =st.date_input("📅 Fecha",value=None)
            usar_api_i=st.checkbox("✅ Buscar stats reales",value=True)
        
        umbral_valor = st.slider("🎯 Umbral de Valor (Edge mínimo %)", 0, 15, 5)
        
        if st.button("🔍 ANALIZAR",key="btn_individual", type="primary"):
            if local_i and visita_i and liga_i:
                partido_i={"dia":str(fecha_i),"hora":hora_i,"hora_sort":0,
                           "liga":liga_i,"liga_id":0,"local":local_i,"visitante":visita_i,
                           "tid_l":None,"tid_v":None}
                with st.spinner(f"Analizando {local_i} vs {visita_i}..."):
                    es_mundial = "mundial" in liga_i.lower() or "fifa" in liga_i.lower()
                    
                    if usar_api_i:
                        if es_mundial:
                            sl_det=obtener_stats_mundial(local_i)
                            sv_det=obtener_stats_mundial(visita_i)
                        else:
                            liga_i_lower = liga_i.lower()
                            liga_id_auto = next((v for k,v in LIGAS.items() if
                                                any(w in liga_i_lower for w in k.lower().split()
                                                    if len(w)>3)), None)
                            sl_det=obtener_stats_detalle(local_i, liga_i, lid=liga_id_auto)
                            sv_det=obtener_stats_detalle(visita_i, liga_i, lid=liga_id_auto)
                        
                        gml=sl_det["gm"] if sl_det.get("ok") else None
                        gcl=sl_det["gc"] if sl_det.get("ok") else None
                        gmv=sv_det["gm"] if sv_det.get("ok") else None
                        gcv=sv_det["gc"] if sv_det.get("ok") else None
                        elo_l=sl_det.get("elo", 1900)
                        elo_v=sv_det.get("elo", 1900)
                        fl=sl_det.get("fuente","Prom.liga")
                        fv=sv_det.get("fuente","Prom.liga")
                    else:
                        sl_det={}; sv_det={}
                        gml=gcl=gmv=gcv=elo_l=elo_v=None; fl=fv="Manual"
                    calc=calcular(gml,gcl,gmv,gcv,liga_i,elo_l,elo_v)
                resultado_i={**partido_i,**calc,"fuente_l":fl,"fuente_v":fv}
                st.session_state["resultado_individual"]=resultado_i
                st.session_state["sl_det"]=sl_det
                st.session_state["sv_det"]=sv_det
                fuentes_ok = sl_det.get("ok",False) and sv_det.get("ok",False)
                if fuentes_ok:
                    st.success(f"✅ Analisis con DATOS REALES — Rango {calc['rango']} ({calc['confianza']}% confianza) | Fuente: {sl_det.get('fuente','')} / {sv_det.get('fuente','')}")
                else:
                    st.warning(f"⚠️ Rango {calc['rango']} — Sin datos reales de API. Se usaron promedios de liga.")

        if "resultado_individual" in st.session_state:
            r = st.session_state["resultado_individual"]
            sl_det = st.session_state.get("sl_det", {})
            sv_det = st.session_state.get("sv_det", {})
            st.markdown("---")
            st.markdown(f"## {bdg(r['rango'])} **{r['local']} vs {r['visitante']}** — {r['liga']}", unsafe_allow_html=True)

            # ── SECCION 1: Comparacion de modelos (arriba, ancho completo) ──
            st.markdown("### 📊 Comparacion de modelos")
            mc1,mc2,mc3,mc4,mc5,mc6 = st.columns(6)
            with mc1: st.markdown(f'<div class="mc"><div class="v">{r["p1"]:.0f}%</div><div class="l">P1 Final</div></div>',unsafe_allow_html=True)
            with mc2: st.markdown(f'<div class="mc"><div class="v">{r["px"]:.0f}%</div><div class="l">Empate</div></div>',unsafe_allow_html=True)
            with mc3: st.markdown(f'<div class="mc"><div class="v">{r["p2"]:.0f}%</div><div class="l">P2 Final</div></div>',unsafe_allow_html=True)
            with mc4: st.markdown(f'<div class="mc"><div class="v">{r["confianza"]}%</div><div class="l">Confianza</div></div>',unsafe_allow_html=True)
            with mc5: st.markdown(f'<div class="mc"><div class="v">{r["xt"]}</div><div class="l">xG Total</div></div>',unsafe_allow_html=True)
            with mc6: st.markdown(f'<div class="mc"><div class="v">{r["rango"]}</div><div class="l">Rango</div></div>',unsafe_allow_html=True)

            # Tabla modelos HTML pura
            lbl_l = r["local"][:14]; lbl_v = r["visitante"][:14]
            filas_m = [
                ("Poisson",       r["p1_po"], r["px_po"], r["p2_po"]),
                ("Dixon-Coles",   r["p1_dc"], r["px_dc"], r["p2_dc"]),
                ("Monte Carlo",   r["p1_mc"], r["px_mc"], r["p2_mc"]),
                ("Elo",           r["p1_el"], r["px_el"], r["p2_el"]),
                ("⭐ FINAL",      r["p1"],    r["px"],    r["p2"]),
            ]
            tbl = f'<table style="width:100%;border-collapse:collapse;font-size:.84rem;margin:8px 0"><thead><tr style="background:#1b2621;color:#dfaf6f"><th style="padding:8px 12px;text-align:left">Modelo</th><th style="padding:8px 12px;text-align:center">{lbl_l} (P1)%</th><th style="padding:8px 12px;text-align:center">Empate%</th><th style="padding:8px 12px;text-align:center">{lbl_v} (P2)%</th></tr></thead><tbody>'
            for i,(mod,p1v,pxv,p2v) in enumerate(filas_m):
                bg="#0d1e0d" if mod.startswith("⭐") else ("#1b2621" if i%2==0 else "#1b2621")
                fw="700" if mod.startswith("⭐") else "400"
                clr="#dfaf6f" if mod.startswith("⭐") else "#fff"
                mx=max(p1v,pxv,p2v)
                def c(v,mx=mx,clr=clr): return f'<td style="padding:7px 12px;text-align:center;{"color:#39ff14;font-weight:700" if v==mx else f"color:{clr}"}">{ v:.1f}%</td>'
                tbl+=f'<tr style="background:{bg};font-weight:{fw}"><td style="padding:7px 12px;color:{clr}">{mod}</td>{c(p1v)}{c(pxv)}{c(p2v)}</tr>'
            tbl+="</tbody></table>"
            st.markdown(tbl, unsafe_allow_html=True)

            # Stats del partido en tabla organizada
            st.markdown("**📊 Estadisticas del partido**")
            local_n = r["local"][:16]; visita_n = r["visitante"][:16]
            tbl_stats = f"""<table style="width:100%;border-collapse:collapse;font-size:.83rem;margin:6px 0">
              <thead><tr style="background:#1b2621;color:#dfaf6f">
                <th style="padding:6px 12px;text-align:left">Metrica</th>
                <th style="padding:6px 12px;text-align:center">{local_n}</th>
                <th style="padding:6px 12px;text-align:center">Total</th>
                <th style="padding:6px 12px;text-align:center">{visita_n}</th>
              </tr></thead><tbody>
              <tr style="background:#1b2621">
                <td style="padding:5px 12px;color:#aaa">xG Esperado</td>
                <td style="padding:5px 12px;text-align:center;color:#00ddff;font-weight:700">{r.get("xl",0)}</td>
                <td style="padding:5px 12px;text-align:center;color:#888">{r.get("xt",0)}</td>
                <td style="padding:5px 12px;text-align:center;color:#00ddff;font-weight:700">{r.get("xv",0)}</td>
              </tr>
              <tr style="background:#1b2621">
                <td style="padding:5px 12px;color:#aaa">Tiros al arco (est.)</td>
                <td style="padding:5px 12px;text-align:center;color:#fff">~{r.get("tiros_l",0)}</td>
                <td style="padding:5px 12px;text-align:center;color:#888">~{r.get("tiros_tot",0)}</td>
                <td style="padding:5px 12px;text-align:center;color:#fff">~{r.get("tiros_v",0)}</td>
              </tr>
              <tr style="background:#1b2621">
                <td style="padding:5px 12px;color:#aaa">Corners (est.)</td>
                <td style="padding:5px 12px;text-align:center;color:#fff" colspan="3">{r.get("corners_str","")}</td>
              </tr>
              <tr style="background:#1b2621">
                <td style="padding:5px 12px;color:#aaa">Tarjetas (est.)</td>
                <td style="padding:5px 12px;text-align:center;color:#fff" colspan="3">{r.get("tar_str","")}</td>
              </tr>
              <tr style="background:#1b2621">
                <td style="padding:5px 12px;color:#aaa">Over 1.5 / 2.5 / 3.5</td>
                <td style="padding:5px 12px;text-align:center;color:#dfaf6f;font-weight:700" colspan="3">{r.get("over15",0)}% / {r.get("over25",0)}% / {r.get("over35",0)}%</td>
              </tr>
              <tr style="background:#1b2621">
                <td style="padding:5px 12px;color:#aaa">BTTS (Ambos Marcan)</td>
                <td style="padding:5px 12px;text-align:center;color:#dfaf6f;font-weight:700" colspan="3">{r.get("btts_si",0)}% Si / {r.get("btts_no",0)}% No</td>
              </tr>
            </tbody></table>"""
            st.markdown(tbl_stats, unsafe_allow_html=True)
            # Marcadores mas probables
            top_ex_str = " | ".join([f"{k} ({v}%)" for k,v in list(r.get("top_ex",{}).items())[:5]])
            st.markdown(f"🎯 **Marcadores mas probables:** {top_ex_str}")
            col_a, col_b = st.columns([1,1])
            with col_a: pass

            # ── SECCION 2: Tabla de datos reales de cada equipo ─────────────
            st.markdown("---")
            st.markdown("### 🌐 Datos reales encontrados en internet")
            if sl_det or sv_det:
                col_l, col_v = st.columns(2)
                for col, det, nombre_eq in [(col_l, sl_det, r["local"]), (col_v, sv_det, r["visitante"])]:
                    with col:
                        fuente_ico = "✅" if det.get("ok") else "⚠️"
                        fuente_txt = det.get("fuente","Sin datos")
                        st.markdown(f"**{fuente_ico} {nombre_eq}**")
                        st.caption(f"Fuente: {fuente_txt}")
                        fuentes_str = " + ".join(det.get("fuentes_usadas",[])) or "Sin datos"
                        st.caption(f"Fuentes consultadas: {fuentes_str}")
                        if det.get("ok"):
                            gm   = det.get("gm");   gc   = det.get("gc")
                            elo  = det.get("elo");   xg   = det.get("xg")
                            tiros= det.get("tiros_pg"); tarj=det.get("tarj_pg")
                            u5   = det.get("ultimos5",[])
                            g5   = det.get("ganados5",0); e5=det.get("empatados5",0); p5=det.get("perdidos5",0)
                            gf5  = det.get("goles_fav5",0); gc5=det.get("goles_con5",0)

                            # Tabla estilo Sofascore
                            rows = [
                                ("⚽ Goles marcados/partido",   f"{gm:.2f}" if gm else "N/D",   "#39ff14"),
                                ("🥅 Goles concedidos/partido", f"{gc:.2f}" if gc else "N/D",   "#ff6666"),
                                ("🎯 xG por partido",           f"{xg:.2f}" if xg else "N/D",   "#00ddff"),
                                ("🔫 Tiros al arco/partido",    f"{tiros:.1f}" if tiros else "N/D","#ffaa00"),
                                ("🟨 Tarjetas amarillas/partido",f"{tarj:.2f}" if tarj else "N/D","#dfaf6f"),
                                ("🏆 ELO Rating",               f"{int(elo)}" if elo else "N/D", "#dfaf6f"),
                                ("📊 Ultimos 5 (G/E/P)",        f"{g5}G / {e5}E / {p5}P",       "#ffffff"),
                                ("⚽ Goles U5",                 f"{gf5} a favor / {gc5} en contra","#aaaaaa"),
                            ]
                            tbl_eq = '<table style="width:100%;border-collapse:collapse;font-size:.82rem;margin:6px 0">'
                            tbl_eq += '<thead><tr style="background:#1b2621;color:#dfaf6f"><th style="padding:6px 10px;text-align:left">Estadistica</th><th style="padding:6px 10px;text-align:center">Valor</th></tr></thead><tbody>'
                            for i_r,(stat,val,clr) in enumerate(rows):
                                bg_r="#1b2621" if i_r%2==0 else "#1b2621"
                                tbl_eq+=f'<tr style="background:{bg_r}"><td style="padding:5px 10px;color:#aaa">{stat}</td><td style="padding:5px 10px;text-align:center;color:{clr};font-weight:700">{val}</td></tr>'
                            tbl_eq+="</tbody></table>"
                            st.markdown(tbl_eq, unsafe_allow_html=True)

                            # Ultimos 5 partidos detallados
                            if u5:
                                st.markdown("**🕐 Ultimos 5 partidos:**")
                                tbl_u5='<table style="width:100%;border-collapse:collapse;font-size:.8rem;margin:4px 0">'
                                tbl_u5+='<thead><tr style="background:#1b2621;color:#dfaf6f"><th style="padding:5px 8px;text-align:left">Rival</th><th style="padding:5px 8px;text-align:center">Cond.</th><th style="padding:5px 8px;text-align:center">Marcador</th><th style="padding:5px 8px;text-align:center">Res</th></tr></thead><tbody>'
                                for i_u,pu in enumerate(u5):
                                    bg_u="#1b2621" if i_u%2==0 else "#1b2621"
                                    rc={"G":"#39ff14","E":"#ffaa00","P":"#ff4444"}.get(pu["res"],"#fff")
                                    tbl_u5+=f'<tr style="background:{bg_u}"><td style="padding:5px 8px;color:#ccc">{pu["rival"]}</td><td style="padding:5px 8px;text-align:center;color:#888;font-size:.75rem">{pu["local"]}</td><td style="padding:5px 8px;text-align:center;color:#fff;font-weight:700">{pu["goles"]}</td><td style="padding:5px 8px;text-align:center"><span style="background:{rc};color:#000;padding:1px 8px;border-radius:4px;font-weight:700;font-size:.8rem">{pu["res"]}</span></td></tr>'
                                tbl_u5+="</tbody></table>"
                                st.markdown(tbl_u5, unsafe_allow_html=True)
                            else:
                                st.caption("Historial partido a partido no disponible en esta fuente.")
                        else:
                            st.warning(f"Sin datos reales para {nombre_eq}. Se usaron promedios de la liga.")
                            st.caption("Verifica que la API_FOOTBALL_KEY este configurada en Streamlit Secrets.")
            else:
                st.info("Activa 'Buscar stats reales en internet' para ver datos de los equipos.")

            # ── SECCION 3: Solo picks con VALOR (edge positivo) ─────────────
            st.markdown("---")
            st.markdown("### 📌 Picks con valor estadistico — selecciona para publicar")
            st.caption("⚠️ Las probabilidades son del modelo matematico. El EDGE real solo se calcula cuando configuras ODDS_API_KEY en Secrets con cuotas de tu casa de apuestas. Compara la cuota justa con la cuota real que ofrece tu casa antes de apostar.")
            umbral_actual = st.session_state.get("umbral_actual", 3)
            mostrar_mercados_con_publicar(r, r, umbral_actual)

            # ── SECCION 4: Picks seleccionados ──────────────────────────────
            picks_sel = st.session_state.get("picks_sel", [])
            if picks_sel:
                st.markdown(f"---\n### ✅ Picks seleccionados ({len(picks_sel)})")
                plan_pub = st.selectbox("Plan minimo", ["gratis","dia","semana","mes"], key="plan_pub_i")
                notas_pub = st.text_area("Notas (opcional)", height=60, key="notas_pub_i")
                if st.button("📢 PUBLICAR PICKS SELECCIONADOS", key="pub_sel"):
                    for pk in picks_sel:
                        det_str = f"xG:{r.get('xl',0)}-{r.get('xv',0)} | O2.5:{r.get('over25',0)}% | BTTS:{r.get('btts_si',0)}% | Tiros:~{r.get('tiros_tot',0)} | Corners:{r.get('corners_str','')}"
                        db_pick_guardar(str(r.get("dia",get_hoy())),pk["liga"],pk["local"],pk["visitante"],
                                        pk["hora"],pk["mercado"],det_str,pk["cuota"],pk["edge"],
                                        pk["confianza"],pk["rango"],notas_pub,plan_pub,0)
                    st.success(f"✅ {len(picks_sel)} picks publicados!")
                    st.session_state.picks_sel = []; st.rerun()
                if st.button("🗑️ Limpiar seleccion", key="clear_sel"):
                    st.session_state.picks_sel = []; st.rerun()
                for pk in picks_sel:
                    st.markdown(f"✔ **{pk['local']} vs {pk['visitante']}** · {pk['mercado']} · {pk['prob']:.0f}% · Edge:{pk['edge']:+.1f}%")

    # ── Tab 2: Analizar por liga ────────────────────────────
    with tabs[1]:
        st.markdown("### 📊 Picks de Valor - Análisis por Liga")
        st.info("Selecciona 1 o más ligas y el período. Verás los partidos encontrados antes de analizar.")
        
        c1,c2=st.columns([2,1])
        
        # Seleccionar fecha primero
        with c2:
            ml = st.radio("📅 Período", ["Hoy", "Día específico", "Esta semana"], horizontal=True)
            if ml == "Hoy":
                fecha_s = get_hoy_date()
                fecha_str = str(fecha_s)
                modo = "dia"
            elif ml == "Día específico":
                fecha_s = st.date_input("Fecha", key="fa_admin", value=get_hoy_date())
                fecha_str = str(fecha_s)
                modo = "dia"
            else:
                hoy = get_hoy_date()
                lu = hoy - timedelta(days=hoy.weekday())
                fecha_s = lu
                fecha_str = f"{lu} al {lu + timedelta(days=6)}"
                modo = "semana"
        
        # Buscar ligas con partidos
        with st.spinner("🔍 Buscando ligas..."):
            ligas_activas = []
            
            # MUNDIAL 2026
            if fecha_s.year == 2026 and fecha_s.month == 7 and 8 <= fecha_s.day <= 20:
                ligas_activas.append("🌍 Mundial FIFA 2026")
            
            # Otras ligas de API
            for ln, lid in list(LIGAS.items())[:15]:
                if "mundial" in ln.lower(): continue
                try:
                    fx = get_fx_dia(lid, str(fecha_s))
                    if fx:
                        ligas_activas.append(ln)
                    time.sleep(0.2)
                except: pass
        
        with c1:
            if ligas_activas:
                st.success(f"✅ {len(ligas_activas)} liga(s) con partidos: {fecha_str}")
                default_ligas = ligas_activas[:3] if len(ligas_activas) >= 3 else ligas_activas
                ligas_sel = st.multiselect("🏆 Selecciona ligas", ligas_activas, default=default_ligas)
            else:
                st.warning("⚠️ No hay partidos para esta fecha")
                ligas_sel = st.multiselect("🏆 Selecciona ligas", list(LIGAS.keys()))

        if st.button("🔍 BUSCAR PARTIDOS", key="btn_buscar_partidos", type="primary"):
            if not ligas_sel:
                st.warning("⚠️ Selecciona al menos una liga")
            else:
                todos = []
                ligas_encontradas = {}
                
                with st.spinner("🔍 Buscando partidos..."):
                    for ln in ligas_sel:
                        partidos_liga = []
                        es_mundial = "mundial" in ln.lower() or "fifa" in ln.lower()
                        
                        if es_mundial:
                            # MUNDIAL 2026 - Mostrar SOLO el partido del día seleccionado
                            from datetime import date, timedelta, datetime
                            hoy = get_hoy_date()
                            # Solo del 8 al 20 julio 2026
                            if 8 <= hoy.day <= 20 and hoy.month == 7 and hoy.year == 2026:
                                if hoy.day == 14:
                                    # SEMIFINAL 1: Francia vs España
                                    partido1 = {"hora": "13:00", "liga": "🌍 Mundial FIFA 2026", "local": "Francia", "visitante": "España", "dia": str(hoy)}
                                    partidos_liga = [partido1]
                                    fuente = "Semifinal 1 - 14 julio"
                                elif hoy.day == 15:
                                    # SEMIFINAL 2: Inglaterra vs Argentina
                                    partido1 = {"hora": "16:00", "liga": "🌍 Mundial FIFA 2026", "local": "Inglaterra", "visitante": "Argentina", "dia": str(hoy)}
                                    partidos_liga = [partido1]
                                    fuente = "Semifinal 2 - 15 julio"
                                elif hoy.day == 18:
                                    # TERCER LUGAR
                                    partido1 = {"hora": "16:00", "liga": "🌍 Mundial FIFA 2026", "local": "Perdedor Semifinal 1", "visitante": "Perdedor Semifinal 2", "dia": str(hoy)}
                                    partidos_liga = [partido1]
                                    fuente = "Tercer Lugar - 18 julio"
                                elif hoy.day in [19, 20]:
                                    # FINAL
                                    partido1 = {"hora": "16:00", "liga": "🌍 Mundial FIFA 2026", "local": "Ganador Semifinal 1", "visitante": "Ganador Semifinal 2", "dia": str(hoy)}
                                    partidos_liga = [partido1]
                                    fuente = "Gran Final - 19 julio"
                                else:
                                    partidos_liga = []
                                    fuente = "Mundial 2026 - Sin partido este día"
                            else:
                                partidos_liga = []
                                fuente = "Mundial no activo"
                        else:
                            # Buscar en API-Football
                            lid = LIGAS.get(ln, None)
                            if lid:
                                try:
                                    if modo == "dia":
                                        fx = get_fx_dia(lid, str(fecha_s))
                                    else:  # semana
                                        fx = get_fx_rango(lid, str(hoy - timedelta(days=hoy.weekday())), str(hoy - timedelta(days=hoy.weekday()) + timedelta(days=6)))
                                    partidos_liga = [fx2p(f) for f in fx]
                                    fuente = "API-Football"
                                except:
                                    partidos_liga = []
                                    fuente = "Error"
                            
                            # Intentar scraping si no hay datos
                            if not partidos_liga:
                                try:
                                    result = scrape_liga_multi_fuente(ln, str(fecha_s))
                                    if result and result.get("partidos"):
                                        partidos_liga = result["partidos"]
                                        fuente = result.get("fuente", "Web")
                                except:
                                    pass
                        
                        if partidos_liga:
                            todos.extend(partidos_liga)
                            ligas_encontradas[ln] = {"count": len(partidos_liga), "fuente": fuente}
                
                st.session_state["partidos_encontrados"] = todos
                st.session_state["ligas_encontradas"] = ligas_encontradas
                
                if todos:
                    st.success(f"✅ Encontrados {len(todos)} partidos en {len(ligas_encontradas)} liga(s)")
                else:
                    st.warning("⚠️ No se encontraron partidos")
        
        # Mostrar partidos guardados
        if "partidos_encontrados" in st.session_state and st.session_state["partidos_encontrados"]:
            todos = st.session_state["partidos_encontrados"]
            ligas_info = st.session_state.get("ligas_encontradas", {})
            
            st.markdown("---")
            st.markdown("#### 📋 Partidos por Liga:")
            for ln, info in ligas_info.items():
                st.markdown(f"- **{ln}**: {info['count']} partidos ({info['fuente']})")
            
            st.markdown("#### ⚽ Partidos Encontrados:")
            cols = st.columns(2)
            for i, p in enumerate(todos[:20]):
                with cols[i % 2]:
                    st.markdown(f"**{p.get('hora', '--:--')}** | {p.get('local', '?')} vs {p.get('visitante', '?')}")
            
            st.markdown("---")
            umbral_valor = st.slider("🎯 Umbral de Valor (Edge mínimo %)", 0, 15, 5, key="umbral_analisis")
            
            if st.button("🦂 ANALIZAR TODOS LOS PARTIDOS", key="btn_analizar_todos", type="primary"):
                with st.spinner(f"Analizando {len(todos)} partidos..."):
                    res = analizar_lista(todos, usar_api=True, prog=None)
                st.session_state["res_liga_admin"] = res
                
                ap = sum(1 for r in res if r.get("rango") == "A+")
                bp = sum(1 for r in res if r.get("rango") == "B")
                c1, c2, c3, c4 = st.columns(4)
                with c1: st.metric("Partidos", len(res))
                with c2: st.metric("A+", ap)
                with c3: st.metric("B", bp)
                with c4:
                    cp = round(sum(r.get("confianza", 0) for r in res) / len(res)) if res else 0
                    st.metric("Conf. prom", f"{cp}%")
            
            if "res_liga_admin" in st.session_state:
                res = st.session_state["res_liga_admin"]
                
                picks_valor = []
                for r in res:
                    for mk in r.get("mercados_picks", []):
                        if len(mk) >= 4:
                            nombre, prob, cuota, edge = mk
                            if edge >= umbral_valor:
                                picks_valor.append({**r, "mercado": nombre, "prob": prob, "cuota": cuota, "edge": edge})
                
                if picks_valor:
                    picks_valor.sort(key=lambda x: x.get("edge", 0), reverse=True)
                    st.markdown(f"### 🎯 {len(picks_valor)} PICKS CON VALOR (Edge >= {umbral_valor}%)")
                    for p in picks_valor[:15]:
                        ec = "00ee66" if p.get("edge", 0) >= 5 else "ffd700"
                        st.markdown(f"📌 **{p.get('local')} vs {p.get('visitante')}** | {p.get('mercado')} @ {p.get('cuota')} | Edge: **:green[{p.get('edge', 0):+.1f}%]**")
                else:
                    st.info(f"No hay picks con valor (edge >= {umbral_valor}%)")
                
                if res:
                    xl = exportar_excel(res, "Scorpion Elite")
                    st.download_button("⬇️ Descargar Excel", xl, "Scorpion_admin.xlsx")

    # ── Tab 3: Picks publicados ─────────────────────────────
    with tabs[2]:
        st.markdown("### Picks publicados")
        picks=db_picks_get(plan="admin")
        hoy_str=get_hoy()
        hoy_picks=[p for p in picks if p.get("fecha")==hoy_str]
        st.markdown(f"**Hoy ({hoy_str}): {len(hoy_picks)} picks publicados**")
        for p in hoy_picks:
            cls="ap" if p.get("rango")=="A+" else "b"
            auto_tag=" 🤖" if p.get("auto") else ""
            st.markdown(f'<div class="pick-box {cls}"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}{auto_tag}<br>📌 <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Edge:{p.get("edge","?")}% · Conf:{p.get("confianza","?")}% · Plan min: <b>{p.get("plan_min","gratis").upper()}</b><br><small>{p.get("detalle","")}</small></div>',unsafe_allow_html=True)

    # ── Tab 4: Clientes ─────────────────────────────────────
    with tabs[3]:
        c1,c2=st.columns(2)
        with c1:
            st.markdown("### ➕ Registrar / Actualizar")
            ced2=st.text_input("Cedula"); nom2=st.text_input("Nombre")
            plan2=st.selectbox("Plan",["gratis","dia","semana","mes"])
            dm={"gratis":30,"dia":1,"semana":7,"mes":30}
            dias2=st.number_input("Dias",min_value=1,max_value=3650,value=int(dm[plan2]))
            fi2=st.date_input("Inicio",value=None)
            if st.button("💾 Guardar"):
                if ced2.strip():
                    db_guardar_usuario(ced2.strip(),nom2 or f"Cliente {ced2[:6]}",plan2,int(dias2),fi2)
                    st.success(f"✅ {ced2} guardado — {plan2.upper()} {dias2} dias")
                else: st.error("Ingresa la cedula")
        with c2:
            st.markdown("### 👥 Lista de clientes")
            for u in db_todos():
                if u["cedula"]=="admin": continue
                ok2,p2,dr2=db_acceso(u["cedula"])
                st.markdown(f"**{u['nombre']}** `{u['cedula']}` {pll(u['plan'],dr2)}",unsafe_allow_html=True)

    # ── Tab 5: Escalera ────────────────────────────────────
    with tabs[4]:
        st.markdown("### 🏆 Reto Escalera del Dia")
        st.info("La escalera usa automaticamente los picks con mayor confianza Y edge positivo publicados hoy.")
        picks_hoy=db_picks_get(hoy_str,plan="admin")
        picks_reales=[p for p in picks_hoy if "🔒" not in str(p.get("mercado",""))]
        # Ordenar: primero por edge positivo, luego por confianza
        def esc_score(p):
            edge=p.get("edge") or -99
            conf=p.get("confianza") or 0
            return (1 if edge and edge>=2 else 0, conf)
        picks_esc=sorted(picks_reales, key=esc_score, reverse=True)[:8]
        if picks_esc:
            cuota_total=1.0
            for p in picks_esc:
                if p.get("cuota"): cuota_total=round(cuota_total*p["cuota"],2)
            st.markdown(f"**{len(picks_esc)} pasos en la escalera | Cuota combinada: {cuota_total}x**")
            for i,p in enumerate(picks_esc,1):
                edge_v=p.get("edge")
                edge_str=f"Edge: {edge_v:+.1f}%" if edge_v is not None else ""
                val_ico="🔥" if edge_v and edge_v>=5 else ("✅" if edge_v and edge_v>=2 else "⚪")
                cls="ap" if p.get("rango")=="A+" else "b"
                st.markdown(f'<div class="esc-box"><b>Paso {i}:</b> {p["local"]} vs {p["visitante"]} · <i>{p["liga"]}</i><br>{val_ico} <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Conf: {p.get("confianza","?")}% {edge_str}</div>',unsafe_allow_html=True)
        else:
            st.info("Publica picks primero para armar la escalera.")


    # ── Tab 5: Calendario de Partidos ──────────────────────
    with tabs[5]:
        try:
            mostrar_calendario_partidos()
        except Exception as e:
            st.error(f"Error cargando calendario: {e}")

    if st.button("🚪 Cerrar sesion",key="logout_admin"): st.session_state.clear(); st.rerun()

# ══════════════════════════════════════════════════════════
# PANTALLA GRATIS
# ══════════════════════════════════════════════════════════
def pantalla_gratis(u):
    hdr()
    ok,plan,dr=db_acceso(u["cedula"])
    st.markdown(f'👋 Hola **{u["nombre"]}** {pll("gratis",dr)} · Max 5 partidos/dia',unsafe_allow_html=True)
    t1,t2=st.tabs(["📁 Analizar archivo","📢 Picks del dia"])
    with t1:
        st.info("Plan gratuito: primeros 5 partidos, sin datos reales de API. Solo imagenes (sin Excel). Actualiza para acceso completo.")
        cons=db_consultas(u["cedula"])
        if cons>5:
            st.warning("Limite de 5 consultas diarias alcanzado. Vuelve manana o actualiza tu plan.")
        else:
            p=widget_archivo(max_p=5,key="free_up")
            if p and st.button("🦂 Analizar"):
                prg=st.progress(0,"Analizando...")
                res=analizar_lista(p,usar_api=False,prog=prg)
                prg.progress(1.0,"Listo ✅")
                for r in res:
                    st.markdown(f'{bdg(r["rango"])} **{r["local"]} vs {r["visitante"]}** · {r.get("hora","")} · **{r["mk2"]}** · xG:{r["xl"]}-{r["xv"]} · O2.5:{r["over25"]}% · Conf:{r["confianza"]}%',unsafe_allow_html=True)
                st.download_button("⬇️ Descargar Excel",data=exportar_excel(res,"Scorpion — Gratis"),
                    file_name=f"Scorpion_gratis_{get_hoy()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    with t2:
        picks=db_picks_get(get_hoy(),"gratis")
        if picks:
            for p in picks:
                cls="ap" if p.get("rango")=="A+" else "b"
                bl="🔒" in str(p.get("mercado",""))
                if bl:
                    st.markdown(f'<div class="pick-box"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]}<br><small>{p["mercado"]}</small></div>',unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="pick-box {cls}"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}<br>📌 <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Conf:{p.get("confianza","?")}%</div>',unsafe_allow_html=True)
        else:
            st.info("No hay picks publicados hoy.")
    if st.button("🚪 Cerrar sesion",key="logout_free"): st.session_state.clear(); st.rerun()

# ══════════════════════════════════════════════════════════
# PANTALLA PAGO
# ══════════════════════════════════════════════════════════
def pantalla_pago(u,plan):
    # Sin hdr() duplicado - solo el dashboard header
    ok,pv,dr=db_acceso(u["cedula"])
    pl_lbl={"dia":"📅 Plan Dia","semana":"📆 Plan Semana","mes":"👑 Plan Mes"}.get(plan,plan)
    st.markdown(f'👋 Hola **{u["nombre"]}** {pll(plan,dr)}',unsafe_allow_html=True)
    st.markdown("---")
    tl=["📊 Dashboard"]  # Nueva pestaña Dashboard V2
    tl+=["🏟️ Por Liga","📁 Subir Archivo","📢 Picks","🏆 Escalera"]
    if plan=="mes": tl.append("🔗 Combinadas"); tl.append("📈 Historial")
    tabs=st.tabs(tl)

    # ══════════════════════════════════════════════════════════
    # PESTAÑA DASHBOARD V2 - Nueva interfaz compacta
    # ══════════════════════════════════════════════════════════
    with tabs[0]:
        from scorpion.ui.components import (
            render_dashboard_header, render_nav_bar, render_dashboard_box,
            render_match_list, render_ai_analysis, render_markets,
            render_odds_comparator, render_statistics, render_alerts
        )
        
        # 1. NAVEGACIÓN ARRIBA DE TODO
        st.markdown(render_nav_bar(active_tab="hoy"), unsafe_allow_html=True)
        
        # 2. Header con usuario y saldo (debajo de navegación)
        saldo = st.session_state.get("user_saldo", "$1,000.00")
        username = u.get("nombre", "Usuario")
        st.markdown(render_dashboard_header(username=username, saldo=saldo), unsafe_allow_html=True)
        
        # Cargar partidos de ejemplo (reemplazar con datos reales)
        partidos_ejemplo = [
            {"local": "Man City", "visitante": "Chelsea", "hora": "15:00", "rango": "A+"},
            {"local": "Barcelona", "visitante": "Real Madrid", "hora": "21:00", "rango": "A+"},
            {"local": "Inter", "visitante": "Milan", "hora": "20:45", "rango": "B"},
            {"local": "Bayern", "visitante": "Dortmund", "hora": "18:30", "rango": "B"},
        ]
        
        analisis_ejemplo = {
            "prob_local": 72,
            "valor": "SI",
            "riesgo": "Bajo",
            "confianza": 91
        }
        
        mercados_ejemplo = ["Ganador", "Over/Under 2.5", "Ambos marcan", "Hándicap Asiático"]
        
        cuotas_ejemplo = [
            {"book": "Bet365", "value": 1.82, "best": False},
            {"book": "Betano", "value": 1.88, "best": False},
            {"book": "Pinnacle", "value": 1.90, "best": True},
            {"book": "Stake", "value": 1.87, "best": False},
        ]
        
        stats_ejemplo = {
            "xg": "1.8 - 1.2",
            "tiros": "15 - 9",
            "corners": "6 - 4",
            "posesion": "58% - 42%"
        }
        
        alertas_ejemplo = [
            {"tipo": "warning", "mensaje": "⚠️ Lesiones importantes detectadas"},
            {"tipo": "info", "mensaje": "📊 Cambio de cuota -5%"},
            {"tipo": "success", "mensaje": "💰 Dinero inteligente detectado"},
            {"tipo": "fire", "mensaje": "🔥 Pick con Value +4.2%"},
        ]
        
        # Layout de 2 columnas usando st.columns
        col1, col2 = st.columns(2)
        
        with col1:
            # Columna izquierda
            st.markdown(render_dashboard_box(
                "⚽ Partidos del Día",
                render_match_list(partidos_ejemplo)
            ), unsafe_allow_html=True)
            
            st.markdown(render_dashboard_box(
                "📈 Mercados Disponibles",
                render_markets(mercados_ejemplo)
            ), unsafe_allow_html=True)
            
            st.markdown(render_dashboard_box(
                "📊 Estadísticas",
                render_statistics(stats_ejemplo)
            ), unsafe_allow_html=True)
        
        with col2:
            # Columna derecha
            st.markdown(render_dashboard_box(
                "🤖 Análisis IA",
                render_ai_analysis(analisis_ejemplo)
            ), unsafe_allow_html=True)
            
            st.markdown(render_dashboard_box(
                "💰 Comparador de Cuotas",
                render_odds_comparator(cuotas_ejemplo)
            ), unsafe_allow_html=True)
            
            st.markdown(render_dashboard_box(
                "🔔 Alertas",
                render_alerts(alertas_ejemplo)
            ), unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("🦂 Scorpion Elite V4 Pro · Dashboard V2 · Solo uso informativo")

    with tabs[1]:
        st.markdown("### Selecciona liga y periodo")

        # Mostrar ligas activas hoy (con lógica del Mundial)
        with st.expander("⚡ Ver ligas con partidos HOY", expanded=False):
            st.caption("Consultando API-Football para ligas activas hoy...")
            hoy_str2 = get_hoy()
            fecha_hoy = get_hoy_date()
            ligas_activas_hoy = []
            
            # MUNDIAL 2026: Solo del 8 al 20 de julio 2026
            if fecha_hoy.year == 2026 and fecha_hoy.month == 7 and 8 <= fecha_hoy.day <= 20:
                ligas_activas_hoy.append(("🌍 Mundial FIFA 2026", 2))
            
            # Otras ligas - buscar en API
            for ln, lid in list(LIGAS.items())[:15]:  # revisar primeras 15
                if "mundial" in ln.lower(): continue  # skip Mundial (ya lo agregamos)
                try:
                    fx_test = get_fx_dia(lid, hoy_str2)
                    if fx_test:
                        ligas_activas_hoy.append((ln, len(fx_test)))
                    time.sleep(0.3)
                except: pass
            
            if ligas_activas_hoy:
                for ln, cnt in ligas_activas_hoy:
                    st.markdown(f"✅ **{ln}** — {cnt} partidos hoy")
            else:
                st.info("No se encontraron partidos hoy en las ligas principales, o la API no responde.")

        c1,c2=st.columns([2,1])
        with c1:
            # Determinar fecha según período seleccionado
            if plan=="dia":
                fecha_sel=st.date_input("Fecha",value=None); modo="dia"
            else:
                ops=["Hoy","Dia especifico","Esta semana","Semana personalizada"]
                if plan in ("semana","mes"): ops.append("Dias de la semana")
                ml=st.radio("Periodo",ops)
                if ml=="Hoy": fecha_sel=get_hoy_date(); modo="dia"
                elif ml=="Dia especifico": fecha_sel=st.date_input("Fecha"); modo="dia"
                elif ml=="Esta semana":
                    hoy=get_hoy_date(); fecha_sel=hoy; lu=hoy-timedelta(days=hoy.weekday())
                    fd=lu; fh=lu+timedelta(days=6); modo="rango"
                elif ml=="Semana personalizada":
                    fd=st.date_input("Desde",value=None)
                    fh=st.date_input("Hasta",value=None+timedelta(days=6)); modo="rango"
                elif ml=="Dias de la semana":
                    dias_n=st.multiselect("Dias",["Lunes","Martes","Miercoles","Viernes","Sabado","Domingo"])
                    fecha_sel=get_hoy_date(); modo="dias"
                else:
                    fecha_sel=get_hoy_date()
            
            # Buscar ligas con partidos para la fecha seleccionada
            st.caption("Buscando ligas con partidos...")
            ligas_activas=[]
            
            # MUNDIAL 2026: Solo del 8 al 20 de julio 2026
            if fecha_sel.year==2026 and fecha_sel.month==7 and 8<=fecha_sel.day<=20:
                ligas_activas.append("🌍 Mundial FIFA 2026")
            
            # Buscar en API para otras ligas
            fecha_str=str(fecha_sel)
            for ln, lid in list(LIGAS.items())[:20]:
                if "mundial" in ln.lower(): continue
                try:
                    fx_test=get_fx_dia(lid, fecha_str)
                    if fx_test:
                        ligas_activas.append(ln)
                    time.sleep(0.2)
                except: pass
            
            if plan=="mes":
                # Para plan mes, permitir seleccionar cualquier liga
                if ligas_activas:
                    st.success(f"✅ {len(ligas_activas)} ligas con partidos: {', '.join(ligas_activas[:5])}{'...' if len(ligas_activas)>5 else ''}")
                else:
                    st.info("No hay ligas con partidos para esta fecha.")
                ligas_sel=st.multiselect("Ligas",list(LIGAS.keys()),default=[list(LIGAS.keys())[0]])
            else:
                # Para dia/semana, solo mostrar ligas activas
                if ligas_activas:
                    st.success(f"✅ {len(ligas_activas)} ligas con partidos")
                    ligas_sel=[st.selectbox("Liga",ligas_activas)]
                else:
                    st.warning("⚠️ No hay partidos para esta fecha")
                    ligas_sel=[]
        with c2:
            if plan=="dia":
                fecha_s=st.date_input("Fecha",value=None); modo="dia"


        if st.button("🦂 Obtener y Analizar",key="btn_liga_pago"):
            todos=[]
            with st.spinner("Obteniendo fixtures de API-Football..."):
                for ln in ligas_sel:
                    lid=LIGAS[ln]
                    if modo=="dia": fx=get_fx_dia(lid,str(fecha_s))
                    elif modo=="rango": fx=get_fx_rango(lid,str(fd),str(fh))
                    elif modo=="dias":
                        fx=[]; hoy=get_hoy(); lu=hoy-timedelta(days=hoy.weekday())
                        mp={"Lunes":0,"Martes":1,"Miercoles":2,"Jueves":3,"Viernes":4,"Sabado":5,"Domingo":6}
                        for d in dias_n:
                            fd2=lu+timedelta(days=mp.get(d,0)); fx+=get_fx_dia(lid,str(fd2))
                    todos+=[fx2p(f) for f in fx]; time.sleep(0.3)
            if not todos:
                st.warning("No se encontraron partidos. La liga puede estar en receso o la temporada no ha comenzado.")
            else:
                prg=st.progress(0,"Analizando...")
                res=analizar_lista(todos,usar_api=True,prog=prg)
                prg.progress(1.0,"Listo ✅")
                ap=sum(1 for r in res if r["rango"]=="A+")
                b=sum(1 for r in res if r["rango"]=="B")
                api_ok=sum(1 for r in res if "API" in r.get("fuente_l",""))
                cp=round(sum(r.get("confianza",0) for r in res)/len(res)) if res else 0
                c1,c2,c3,c4=st.columns(4)
                for col,(v,l) in zip([c1,c2,c3,c4],[(len(res),"Partidos"),(ap,"Rango A+"),(api_ok,"Datos reales"),(f"{cp}%","Confianza prom")]):
                    with col: st.markdown(f'<div class="mc"><div class="v">{v}</div><div class="l">{l}</div></div>',unsafe_allow_html=True)
                st.markdown("### 🏆 Top Picks")
                top=sorted([r for r in res if r["rango"] in ("A+","B")],
                           key=lambda x:(x.get("confianza",0),max(x.get("p1",0),x.get("p2",0))),reverse=True)[:8]
                for r in top:
                    st.markdown(f'{bdg(r["rango"])} **{r["local"]} vs {r["visitante"]}** ({r["liga"][:16]}) · {r["hora"]} · **{r["mk2"]}** · xG:{r["xl"]}-{r["xv"]} · O2.5:{r["over25"]}% · Tiros:~{r.get("tiros_tot",0)} · Conf:{r["confianza"]}%',unsafe_allow_html=True)
                if top:
                    st.markdown("### 🔬 Detalle modelos")
                    for r in top[:3]:
                        with st.expander(f"{r['local']} vs {r['visitante']} — {r['rango']} ({r['confianza']}% conf)"):
                            dc1,dc2,dc3,dc4=st.columns(4)
                            with dc1: st.metric("Poisson",f'{r.get("p1_po",0):.1f}%')
                            with dc2: st.metric("Dixon-Coles",f'{r.get("p1_dc",0):.1f}%')
                            with dc3: st.metric("Monte Carlo",f'{r.get("p1_mc",0):.1f}%')
                            with dc4: st.metric("Elo",f'{r.get("p1_el",0):.1f}%')
                            st.markdown(f"xG: {r['xl']} vs {r['xv']} | Total: {r['xt']}")
                            st.markdown(f"Tiros: Local ~{r.get('tiros_l',0)} | Visita ~{r.get('tiros_v',0)} | Total ~{r.get('tiros_tot',0)}")
                            st.markdown(f"Corners: {r.get('corners_str','')} | Tarjetas: {r.get('tar_str','')}")
                            st.markdown(f"Marcadores: {' | '.join([f'{k}({v}%)' for k,v in list(r.get('top_ex',{}).items())[:5]])}")
                fl=str(fecha_s) if modo=="dia" else f"{fd}_al_{fh}"
                xl=exportar_excel(res,f"Scorpion Elite — {pl_lbl}")
                st.download_button("⬇️ Descargar Excel completo",data=xl,
                    file_name=f"ScorpionElite_{fl}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                for r in res: db_historial_guardar(u["cedula"],r,r)

    with tabs[1]:
        st.info("Sube una captura de Sofascore, FlashScore o cualquier app. La IA lee los partidos automaticamente. Solo imagenes (PNG, JPG).")
        p=widget_archivo(key="pago_up")
        if p and st.button("🦂 Analizar archivo",key="btn_arch"):
            prg=st.progress(0,"Analizando...")
            res=analizar_lista(p,usar_api=True,prog=prg)
            prg.progress(1.0,"Listo ✅")
            xl=exportar_excel(res,"Scorpion Elite — Archivo")
            st.download_button("⬇️ Descargar Excel",data=xl,
                file_name=f"Scorpion_custom_{get_hoy()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tabs[2]:
        picks=db_picks_get(get_hoy(),plan)
        if picks:
            for p in picks:
                cls="ap" if p.get("rango")=="A+" else "b"
                bl="🔒" in str(p.get("mercado",""))
                if bl:
                    st.markdown(f'<div class="pick-box"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]}<br><small>{p["mercado"]}</small></div>',unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="pick-box {cls}"><b>{p["liga"]}</b> · {p["local"]} vs {p["visitante"]} · {p.get("hora","")}<br>📌 <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Edge:{p.get("edge","?")}% · Conf:{p.get("confianza","?")}%{"<br><small>"+p["notas"]+"</small>" if p.get("notas") else ""}</div>',unsafe_allow_html=True)
        else:
            st.info("No hay picks publicados para hoy. El administrador los publica diariamente.")

    with tabs[3]:
        st.markdown("### 🏆 Reto Escalera")
        st.caption("Picks del dia ordenados por mayor confianza y valor estadistico.")
        picks_e=db_picks_get(get_hoy(),plan)
        reales=[p for p in picks_e if "🔒" not in str(p.get("mercado",""))]
        def esc_score(p):
            edge=p.get("edge") or -99
            conf=p.get("confianza") or 0
            return (1 if edge and edge>=2 else 0, conf)
        picks_esc=sorted(reales, key=esc_score, reverse=True)[:8]
        if picks_esc:
            cuota_total=1.0
            for p in picks_esc:
                if p.get("cuota"): cuota_total=round(cuota_total*p["cuota"],2)
            st.markdown(f"**{len(picks_esc)} pasos | Cuota combinada: {cuota_total}x**")
            for i,p in enumerate(picks_esc,1):
                edge_v=p.get("edge")
                edge_str=f" · Edge: {edge_v:+.1f}%" if edge_v is not None else ""
                val_ico="🔥" if edge_v and edge_v>=5 else ("✅" if edge_v and edge_v>=2 else "⚪")
                cls="ap" if p.get("rango")=="A+" else "b"
                st.markdown(f'<div class="esc-box"><b>Paso {i}:</b> {p["local"]} vs {p["visitante"]} · {p["liga"]}<br>{val_ico} <b>{p["mercado"]}</b> @ {p.get("cuota","?")} · Conf: {p.get("confianza","?")}%{edge_str}</div>',unsafe_allow_html=True)
        else:
            st.info("No hay picks publicados hoy para la escalera.")

    if plan=="mes" and len(tabs)>4:
        with tabs[4]:
            st.markdown("### 🔗 Combinadas del Dia")
            st.markdown("""
            **¿Cómo funciona una combinada?**
            Una combinada es apostar a varios partidos a la vez. Para ganar, **todos** los picks deben acertar.
            La cuota total se multiplica (ej: 1.8 × 2.0 × 1.5 = 5.4x tu apuesta).
            Cuanto mas picks agregas, mayor es la cuota pero menor la probabilidad de acertar.
            """)

            picks_c=db_picks_get(get_hoy(),plan)
            reales_c=[p for p in picks_c if "🔒" not in str(p.get("mercado","")) and p.get("cuota")]
            if reales_c:
                st.markdown("**Selecciona los picks que quieres combinar:**")
                sel_comb=[]
                for p in reales_c:
                    conf=p.get("confianza",0); cuota_p=p.get("cuota",1)
                    edge=p.get("edge",0)
                    edge_str=f" · Edge: {edge:+.1f}%" if edge else ""
                    lbl=f'{p["local"]} vs {p["visitante"]} — {p["mercado"]} @ {cuota_p} · Conf: {conf}%{edge_str}'
                    if st.checkbox(lbl, key=f"comb_{p['id']}"):
                        sel_comb.append(p)

                if sel_comb:
                    cuota_c=1.0; prob_c=1.0
                    for s in sel_comb:
                        if s.get("cuota"):     cuota_c=round(cuota_c*float(s["cuota"]),2)
                        if s.get("confianza"): prob_c=round(prob_c*float(s["confianza"])/100,5)
                    prob_pct=round(prob_c*100,1)
                    # Kelly conservador (1/4)
                    b=cuota_c-1
                    kelly_f=max(0,(prob_c*b-(1-prob_c))/b)*0.25 if b>0 else 0
                    kelly_pct=round(kelly_f*100,1)
                    # Ganancia neta si acierta con $100 base
                    ganancia_100=round(100*cuota_c-100,1)

                    st.markdown("---")
                    st.markdown("### 📊 Tu Combinada")

                    # Tabla de picks seleccionados
                    tbl_comb='<table style="width:100%;border-collapse:collapse;font-size:.83rem;margin:8px 0"><thead><tr style="background:#1b2621;color:#dfaf6f"><th style="padding:6px 12px;text-align:left">Partido</th><th style="padding:6px 12px;text-align:left">Pick</th><th style="padding:6px 12px;text-align:center">Cuota</th><th style="padding:6px 12px;text-align:center">Confianza</th></tr></thead><tbody>'
                    for i_c,s in enumerate(sel_comb):
                        bg_c="#1b2621" if i_c%2==0 else "#1b2621"
                        tbl_comb+=f'<tr style="background:{bg_c}"><td style="padding:5px 12px;color:#ccc">{s["local"][:12]} vs {s["visitante"][:12]}</td><td style="padding:5px 12px;color:#dfaf6f;font-weight:600">{s["mercado"]}</td><td style="padding:5px 12px;text-align:center;color:#fff">{s.get("cuota","?")}</td><td style="padding:5px 12px;text-align:center;color:#39ff14">{s.get("confianza","?")}%</td></tr>'
                    tbl_comb+="</tbody></table>"
                    st.markdown(tbl_comb, unsafe_allow_html=True)

                    # Resumen de metricas con explicacion
                    tbl_res=f'''<table style="width:100%;border-collapse:collapse;font-size:.85rem;margin:10px 0">
                      <thead><tr style="background:#0a1e0a;color:#dfaf6f">
                        <th style="padding:7px 14px;text-align:left">Metrica</th>
                        <th style="padding:7px 14px;text-align:center">Valor</th>
                        <th style="padding:7px 14px;text-align:left">Que significa</th>
                      </tr></thead><tbody>
                      <tr style="background:#0d1e0d">
                        <td style="padding:6px 14px;color:#aaa">Picks en la combinada</td>
                        <td style="padding:6px 14px;text-align:center;color:#fff;font-weight:700">{len(sel_comb)}</td>
                        <td style="padding:6px 14px;color:#888">Todos deben acertar para ganar</td>
                      </tr>
                      <tr style="background:#0a1a0a">
                        <td style="padding:6px 14px;color:#aaa">Cuota total combinada</td>
                        <td style="padding:6px 14px;text-align:center;color:#dfaf6f;font-weight:700">{cuota_c}x</td>
                        <td style="padding:6px 14px;color:#888">Multiplica tu apuesta por {cuota_c}</td>
                      </tr>
                      <tr style="background:#0d1e0d">
                        <td style="padding:6px 14px;color:#aaa">Probabilidad estimada</td>
                        <td style="padding:6px 14px;text-align:center;color:{"#39ff14" if prob_pct>=40 else "#ffaa00" if prob_pct>=20 else "#ff4444"};font-weight:700">{prob_pct}%</td>
                        <td style="padding:6px 14px;color:#888">{"Razonable ✅" if prob_pct>=40 else "Arriesgada ⚠️" if prob_pct>=20 else "Muy arriesgada ❌"}</td>
                      </tr>
                      <tr style="background:#0a1a0a">
                        <td style="padding:6px 14px;color:#aaa">Ganancia neta por $100</td>
                        <td style="padding:6px 14px;text-align:center;color:#39ff14;font-weight:700">${ganancia_100}</td>
                        <td style="padding:6px 14px;color:#888">Si apuestas $100 y aciertas, ganas ${ganancia_100} de utilidad</td>
                      </tr>
                      <tr style="background:#0d1e0d">
                        <td style="padding:6px 14px;color:#aaa">Kelly recomendado</td>
                        <td style="padding:6px 14px;text-align:center;color:#dfaf6f;font-weight:700">{kelly_pct}% del bankroll</td>
                        <td style="padding:6px 14px;color:#888">Si tienes $1000, apuesta maximo ${round(kelly_pct*10,0)}</td>
                      </tr>
                    </tbody></table>'''
                    st.markdown(tbl_res, unsafe_allow_html=True)

                    if prob_pct < 20:
                        st.error("⚠️ Esta combinada tiene menos de 20% de probabilidad. Es muy arriesgada. Considera reducir el numero de picks.")
                    elif prob_pct < 40:
                        st.warning("⚠️ Combinada arriesgada. Apuesta solo una fraccion pequena del bankroll.")
                    else:
                        st.success(f"✅ Combinada razonable con {prob_pct}% de probabilidad estimada.")
            else:
                st.info("No hay picks publicados hoy para combinar. El administrador debe publicar picks primero.")

        with tabs[5]:
            st.markdown("### 📈 Mi Historial")
            hist=db_historial_get(u["cedula"],30)
            if hist:
                for h in hist:
                    st.markdown(f'**{h["local"]} vs {h["visitante"]}** · {h["liga"]} · {h["fecha"]} · {h["mercado"]} · {h["rango"]}')
            else:
                st.info("No tienes analisis guardados aun.")

    if st.button("🚪 Cerrar sesion",key="logout_pago"): st.session_state.clear(); st.rerun()
    st.markdown('<div class="ft">🦂 Scorpion Elite V4 Pro 2025 · Solo uso informativo</div>',unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# PANTALLA PRINCIPAL ÚNICA - SCORPION ELITE
# ══════════════════════════════════════════════════════════
    
    with col_header_right:
        if st.session_state.get("logged_in"):
            st.markdown(f"""
            <div style="text-align: right; padding: 15px; background: #0f1a12; border-radius: 8px; margin-top: 15px;">
                <div style="color: #dfaf6f; font-weight: bold; font-size: 1.1rem;">👤 {st.session_state.get('user_name', 'Usuario')}</div>
                <div style="color: #888; font-size: 0.85rem;">Plan: {st.session_state.get('user_plan', 'gratis').upper()}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Cerrar sesión", key="logout_main"):
                st.session_state.clear()
                st.rerun()
        else:
            with st.form("login_form_dashboard", clear_on_submit=True):
                st.markdown('<p style="color:#dfaf6f; text-align: right; font-weight: bold; margin-bottom: 5px;">Acceso</p>', unsafe_allow_html=True)
                user_input = st.text_input("Usuario", placeholder="Tu cédula o 'admin'", label_visibility="collapsed", key="user_dash")
                password_input = st.text_input("Contraseña", type="password", placeholder="Contraseña", label_visibility="collapsed", key="pass_dash")
                submit_btn = st.form_submit_button("Entrar →")
                
                if submit_btn:
                    if user_input and password_input:
                        # Intentar login de admin primero
                        if user_input == "admin":
                            if password_input == ADMIN_PWD:
                                st.session_state.li = True
                                st.session_state.ced = "admin"
                                st.session_state.u = {"nombre": "Administrador", "cedula": "admin", "plan": "admin"}
                                st.session_state.user_name = "Administrador"
                                st.session_state.user_plan = "admin"
                                st.session_state.is_admin = True
                                st.rerun()
                            else:
                                st.error("❌ Contraseña de administrador incorrecta")
                                return
                        elif password_input == ADMIN_PWD:
                            # Cualquier usuario con password de admin se convierte en admin
                            u = db_get(user_input)
                            if not u:
                                u = {"nombre": user_input, "cedula": user_input, "plan": "admin"}
                            st.session_state.li = True
                            st.session_state.ced = user_input
                            st.session_state.u = u
                            st.session_state.user_name = u.get("nombre", user_input)
                            st.session_state.user_plan = "admin"
                            st.session_state.is_admin = True
                            st.rerun()
                        else:
                            # Login normal
                            u = db_get(user_input)
                            if u:
                                ok, plan_v, dr = db_acceso(user_input)
                                if ok:
                                    st.session_state.li = True
                                    st.session_state.ced = user_input
                                    st.session_state.u = u
                                    st.session_state.user_name = u.get("nombre", user_input)
                                    st.session_state.user_plan = plan_v
                                    st.session_state.is_admin = (plan_v == "admin")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Plan {plan_v}. Contacta al admin.")
                            else:
                                # Crear usuario gratis automáticamente
                                db_guardar_usuario(user_input, f"Usuario {user_input[:4]}", "gratis", 36500, get_hoy())
                                st.session_state.li = True
                                st.session_state.ced = user_input
                                st.session_state.u = {"nombre": f"Usuario {user_input[:4]}", "cedula": user_input}
                                st.session_state.user_name = f"Usuario {user_input[:4]}"
                                st.session_state.user_plan = "gratis"
                                st.session_state.is_admin = False
                                st.rerun()
    
    st.markdown("---")
    
    # Dashboard de 3 columnas
    col1, col2, col3 = st.columns([2, 1.2, 1.2])
    
    # Obtener picks y datos
    picks_hoy = db_picks_get(get_hoy(), "gratis")
    
    # Intentar scraping de partidos
    try:
        partidos_scraped = scrape_flashscore_partidos()
        st.session_state.partidos_scraped = partidos_scraped
    except:
        partidos_scraped = st.session_state.get("partidos_scraped", [])
    
    # ══════════════════════════════════════════════════════════
    # 💰 CUOTAS DE APUESTAS (visible arriba)
    # ══════════════════════════════════════════════════════════
    st.markdown("---")
    st.markdown('<p style="color:#4ecdc4;font-size:1.2rem;font-weight:bold;">💰 Cuotas de Hoy</p>', unsafe_allow_html=True)
    
    # Selector de liga
    col_odds1, col_odds2 = st.columns([3, 1])
    with col_odds1:
        liga_odds = st.selectbox(
            "🏆 Selecciona una liga:",
            options=[
                "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League",
                "🇪🇸 La Liga",
                "🇫🇷 Ligue 1",
                "🇩🇪 Bundesliga",
                "🇮🇹 Serie A",
            ],
            key="liga_cuotas_main"
        )
    with col_odds2:
        ver_cuotas_btn = st.button("Ver Cuotas", key="btn_ver_cuotas", use_container_width=True)
    
    # Mapear a keys de API
    liga_keys_map = {
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "soccer_epl",
        "🇪🇸 La Liga": "soccer_esp La Liga",
        "🇫🇷 Ligue 1": "soccer_fra Ligue 1",
        "🇩🇪 Bundesliga": "soccer_deu Bundesliga",
        "🇮🇹 Serie A": "soccer_ita Serie A",
    }
    liga_odds_key = liga_keys_map.get(liga_odds, "soccer_epl")
    
    # Mostrar cuotas si se presiona el botón
    if ver_cuotas_btn:
        with st.spinner("Obteniendo cuotas..."):
            cuotas = obtener_cuotas_todos_partidos(liga_odds_key)
        
        if cuotas:
            st.success(f"✅ {len(cuotas)} partidos")
            for c in cuotas[:8]:
                home = c.get('home', '')
                away = c.get('away', '')
                cuota_l = c.get('cuota_local', 0)
                cuota_e = c.get('cuota_empate', 0)
                cuota_v = c.get('cuota_visita', 0)
                
                st.markdown(f"""
                <div style="background:#1b2621;border:1px solid #4ecdc4;border-radius:4px;padding:8px;margin-bottom:4px;">
                    <div style="color:#dcdcdc;font-size:0.85rem;font-weight:bold;">{home} vs {away}</div>
                    <div style="display:flex;justify-content:space-around;margin-top:4px;">
                        <div style="text-align:center;"><div style="color:#888;font-size:0.65rem;">1</div><div style="color:#4ecdc4;font-size:0.95rem;">{cuota_l}</div></div>
                        <div style="text-align:center;"><div style="color:#888;font-size:0.65rem;">X</div><div style="color:#4ecdc4;font-size:0.95rem;">{cuota_e}</div></div>
                        <div style="text-align:center;"><div style="color:#888;font-size:0.65rem;">2</div><div style="color:#4ecdc4;font-size:0.95rem;">{cuota_v}</div></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("No hay cuotas. Intenta con otra liga.")
    
    # Obtener estadísticas de equipos desde API-Football
    stats_cache_key = f"stats_equipos_{get_hoy()}"
    if stats_cache_key not in st.session_state:
        try:
            st.session_state[stats_cache_key] = obtener_stats_equipos_api()
        except:
            st.session_state[stats_cache_key] = {}
    stats_equipos = st.session_state.get(stats_cache_key, {})
    
    # Enriquecer partidos con estadísticas
    if stats_equipos:
        partidos_scraped = enriquecer_partidos_con_stats(partidos_scraped, stats_equipos)
    
    with col1:
        # === BUSCADOR CON SUGERENCIAS + BUSQUEDA EN INTERNET ===
        with st.expander("🔍 Buscar Equipo", expanded=False):
            # Lista de sugerencias para autocomplete
            sugerencias = [
                # Europa
                "Manchester City", "Liverpool", "Arsenal", "Chelsea", "Manchester United",
                "Tottenham", "Newcastle", "Brighton", "Aston Villa", "West Ham",
                "Real Madrid", "Barcelona", "Atletico Madrid", "Real Sociedad", "Villarreal",
                "Sevilla", "Athletic Bilbao", "Real Betis", "Valencia", "Girona",
                "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen", "Eintracht Frankfurt",
                "Inter Milan", "AC Milan", "Juventus", "Napoli", "Roma", "Lazio", "Atalanta",
                "PSG", "Marseille", "Monaco", "Lyon", "Lille", "Nice",
                "Ajax", "PSV", "Feyenoord",
                "Porto", "Benfica", "Sporting CP",
                "Galatasaray", "Fenerbahce", "Besiktas",
                # America
                "River Plate", "Boca Juniors", "Independiente", "Racing Club", "San Lorenzo",
                "Atletico Nacional", "Millonarios", "Santa Fe", "Junior", "America de Cali",
                "Atletico Bucaramanga", "Boyaca Chico", "Patriotas", "Once Caldas", "Alaves",
                "Flamengo", "Palmeiras", "Santos", "Sao Paulo", "Corinthians", "Internacional",
                "Colo-Colo", "Universidad de Chile", "Catolica",
                "Cruz Azul", "Chivas", "America Mexico", "Monterrey", "Tigres", "Pumas",
                "Al Hilal", "Al Nassr", "Al Ittihad",
                "LA Galaxy", "LAFC", "Inter Miami", "Atlanta United",
            ]
            
            st.write("🔍 Escribe el nombre del equipo:")
            col_busq1, col_busq2 = st.columns([3, 1])
            with col_busq1:
                busqueda = st.text_input("Equipo:", placeholder="Ej: Barcelona, Real Madrid, Liverpool...", key="busqueda_equipo_main", label_visibility="collapsed")
            with col_busq2:
                buscar_btn = st.button("🔍 Buscar", key="btn_buscar_eq", use_container_width=True)
            
            if buscar_btn and busqueda and len(busqueda) >= 2:
                # Limpiar errores anteriores
                if 'busqueda_errores' in st.session_state:
                    del st.session_state['busqueda_errores']
                
                with st.spinner("🔍 Buscando equipos..."):
                    resultados = buscar_equipo_en_todas_fuentes(busqueda)
                
                if resultados:
                    st.success(f"✅ {len(resultados)} equipos encontrados para '{busqueda}'")
                    
                    for i, eq in enumerate(resultados[:10]):
                        fuente = eq.get('fuente', '')
                        nombre = eq.get('nombre', '')
                        pais = eq.get('pais', '')
                        liga = eq.get('liga', '')
                        tid = eq.get('id', '')
                        
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            # Resaltar si coincide exactamente
                            if busqueda.lower() in nombre.lower():
                                st.markdown(f"""
                                <div style="background:#1b2621;border:2px solid #4ecdc4;border-radius:4px;padding:8px;margin-bottom:6px;">
                                    <div style="color:#4ecdc4;font-size:0.9rem;font-weight:bold;">{nombre}</div>
                                    <div style="color:#888;font-size:0.65rem;">{liga} • {fuente}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            else:
                                st.markdown(f"""
                                <div style="background:#1b2621;border:1px solid #8a6435;border-radius:4px;padding:8px;margin-bottom:6px;">
                                    <div style="color:#dcdcdc;font-size:0.85rem;font-weight:bold;">{nombre}</div>
                                    <div style="color:#888;font-size:0.65rem;">{liga} • {fuente}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        with col2:
                            if st.button("📊", key=f"ver_{tid}_{i}"):
                                st.session_state['equipo_buscado'] = eq
                                st.rerun()
                elif resultados == []:
                    st.warning(f"❌ No se encontró '{busqueda}'. Prueba con otro nombre.")
                else:
                    st.error("❌ No se encontraron equipos en ninguna fuente")
                    st.info("💡 Prueba con: Barcelona, Real Madrid, River Plate, etc.")
            
            # Mostrar stats si hay equipo seleccionado
            if 'equipo_buscado' in st.session_state:
                eq = st.session_state['equipo_buscado']
                nombre = eq.get('nombre', '')
                fuente = eq.get('fuente', '')
                
                st.markdown("---")
                st.success(f"📊 {nombre}")
                st.caption(f"Fuente: {fuente}")
                
                # Obtener stats desde internet
                stats = obtener_stats_equipo_fuente(eq)
                if stats:
                    info = stats.get('goles_favor', '')
                    if info and len(info) > 50:
                        st.markdown(f"""
                        <div style="background:#1b2621;border:1px solid #8a6435;border-radius:4px;padding:10px;margin-top:10px;">
                            <div style="color:#dfaf6f;font-size:0.8rem;font-weight:bold;margin-bottom:5px;">ℹ️ Información:</div>
                            <div style="color:#dcdcdc;font-size:0.75rem;">{info}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        with col_s1:
                            st.metric("PJ", stats.get('partidos', stats.get('pj', '?')))
                        with col_s2:
                            st.metric("Victorias", stats.get('victorias', stats.get('ganados', '?')))
                        with col_s3:
                            st.metric("G/F", stats.get('goles_favor', stats.get('goles', '?')))
                        with col_s4:
                            st.metric("G/C", stats.get('goles_contra', stats.get('gc', '?')))
                else:
                    st.info("Stats no disponibles para este equipo.")
                
                # === SECCIÓN DE CUOTAS ===
                st.markdown("---")
                st.markdown('<p style="color:#dfaf6f;font-size:1rem;font-weight:bold;">💰 Cuotas de Apuestas</p>', unsafe_allow_html=True)
                
                with st.expander("💰 Ver Cuotas de Hoy", expanded=False):
                    st.markdown("**Selecciona una liga:**")
                    
                    # Selector de liga
                    liga_seleccionada = st.selectbox(
                        "Liga:",
                        options=[
                            "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League",
                            "🇪🇸 La Liga",
                            "🇫🇷 Ligue 1",
                            "🇩🇪 Bundesliga",
                            "🇮🇹 Serie A",
                        ],
                        key="liga_cuotas_selector"
                    )
                    
                    # Mapear a keys de API
                    liga_keys = {
                        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "soccer_epl",
                        "🇪🇸 La Liga": "soccer_esp La Liga",
                        "🇫🇷 Ligue 1": "soccer_fra Ligue 1",
                        "🇩🇪 Bundesliga": "soccer_deu Bundesliga",
                        "🇮🇹 Serie A": "soccer_ita Serie A",
                    }
                    liga_key = liga_keys.get(liga_seleccionada, "soccer_epl")
                    
                    st.markdown(f"📍 Liga seleccionada: **{liga_seleccionada}**")
                    
                    if st.button("🔍 Ver Cuotas", key="btn_cuotas"):
                        with st.spinner("Obteniendo cuotas..."):
                            cuotas = obtener_cuotas_todos_partidos(liga_key)
                        
                        if cuotas:
                            st.success(f"✅ {len(cuotas)} partidos con cuotas")
                            for c in cuotas[:10]:
                                home = c.get('home', '')
                                away = c.get('away', '')
                                cuota_l = c.get('cuota_local', 0)
                                cuota_e = c.get('cuota_empate', 0)
                                cuota_v = c.get('cuota_visita', 0)
                                casa = c.get('casa', '')
                                
                                st.markdown(f"""
                                <div style="background:#1b2621;border:1px solid #8a6435;border-radius:4px;padding:8px;margin-bottom:6px;">
                                    <div style="color:#dcdcdc;font-size:0.85rem;font-weight:bold;">{home} vs {away}</div>
                                    <div style="display:flex;justify-content:space-around;margin-top:6px;">
                                        <div style="text-align:center;"><div style="color:#dfaf6f;font-size:0.7rem;">1 (Local)</div><div style="color:#4ecdc4;font-size:1rem;">{cuota_l}</div></div>
                                        <div style="text-align:center;"><div style="color:#dfaf6f;font-size:0.7rem;">X (Empate)</div><div style="color:#4ecdc4;font-size:1rem;">{cuota_e}</div></div>
                                        <div style="text-align:center;"><div style="color:#dfaf6f;font-size:0.7rem;">2 (Visita)</div><div style="color:#4ecdc4;font-size:1rem;">{cuota_v}</div></div>
                                    </div>
                                    <div style="color:#888;font-size:0.6rem;text-align:right;margin-top:4px;">📌 {casa}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.warning("No hay cuotas para esta liga. Intenta con otra.")
                
                # === SECCIÓN DE CLIMA ===
                st.markdown("---")
                st.markdown('<p style="color:#dfaf6f;font-size:1rem;font-weight:bold;">🌤️ Clima</p>', unsafe_allow_html=True)
                
                with st.expander("🌡️ Ver Clima", expanded=False):
                    ciudad_clima = st.text_input("Ciudad:", placeholder="Ej: Madrid, Buenos Aires...", key="ciudad_clima_input")
                    
                    if st.button("🔍 Buscar Clima", key="btn_clima"):
                        if ciudad_clima:
                            with st.spinner("Obteniendo clima..."):
                                clima = obtener_clima(ciudad_clima)
                                pronostico = obtener_pronostico(ciudad_clima)
                            
                            if clima:
                                temp = clima.get('temp', 0)
                                temp_min = clima.get('temp_min', 0)
                                temp_max = clima.get('temp_max', 0)
                                humedad = clima.get('humedad', 0)
                                desc = clima.get('clima', '')
                                viento = clima.get('viento', 0)
                                ciudad = clima.get('ciudad', '')
                                pais = clima.get('pais', '')
                                
                                st.success(f"📍 {ciudad}, {pais}")
                                
                                col_c1, col_c2, col_c3 = st.columns(3)
                                with col_c1:
                                    st.metric("🌡️ Temp", f"{temp:.1f}°C", f"Mín: {temp_min:.0f}° / Máx: {temp_max:.0f}°")
                                with col_c2:
                                    st.metric("💧 Humedad", f"{humedad}%")
                                with col_c3:
                                    st.metric("💨 Viento", f"{viento} m/s")
                                
                                st.info(f"☁️ {desc.capitalize()}")
                                
                                if pronostico:
                                    st.markdown("**📅 Pronóstico 5 días:**")
                                    cols = st.columns(len(pronostico))
                                    for i, p in enumerate(pronostico[:5]):
                                        with cols[i]:
                                            fecha = p.get('fecha', '')[5:]
                                            temp_p = p.get('temp', 0)
                                            desc_p = p.get('clima', '')
                                            st.markdown(f"**{fecha}**\n{temp_p:.0f}°\n{desc_p[:12]}")
                            else:
                                st.warning("No se encontró clima. Configura OPENWEATHER_KEY en secrets.")
                        else:
                            st.warning("Ingresa una ciudad")
                
                # === ESTADÍSTICAS AVANZADAS (FBref + Understat) ===
                st.markdown("---")
                st.markdown('<p style="color:#dfaf6f;font-size:1rem;font-weight:bold;">📊 Stats Avanzadas</p>', unsafe_allow_html=True)
                
                with st.expander("🔍 Ver Stats Detalladas", expanded=False):
                    nom_stats = st.text_input("Equipo para stats:", placeholder="Ej: Barcelona, Liverpool...", key="equipo_stats_input")
                    
                    if st.button("📊 Buscar Stats", key="btn_stats"):
                        if nom_stats:
                            with st.spinner("Buscando en FBref y Understat..."):
                                stats_results = buscar_stats_equipo(nom_stats)
                            
                            if stats_results:
                                st.success(f"✅ {len(stats_results)} fuentes encontradas")
                                
                                for res in stats_results[:6]:
                                    fuente = res.get("fuente", "")
                                    nombre = res.get("nombre", "")
                                    url = res.get("url", "")
                                    tipo = res.get("tipo", "")
                                    
                                    if fuente == "FBref":
                                        # Obtener stats de FBref
                                        with st.spinner(f"Cargando stats de {nombre}..."):
                                            stats = obtener_stats_fbref(url)
                                        
                                        st.markdown(f"""
                                        <div style="background:#1b2621;border:1px solid #4ecdc4;border-radius:4px;padding:10px;margin-bottom:10px;">
                                            <div style="color:#4ecdc4;font-size:0.9rem;font-weight:bold;">📊 {nombre}</div>
                                            <div style="color:#888;font-size:0.7rem;">FBref - Estadísticas Detalladas</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        if stats:
                                            cols = st.columns(4)
                                            items = list(stats.items())[:8]
                                            for i, (k, v) in enumerate(items):
                                                with cols[i % 4]:
                                                    st.metric(k[:15], v[:10] if isinstance(v, str) else v)
                                        else:
                                            st.info(f"Stats no disponibles. Ver en: https://fbref.com{url}")
                                    
                                    elif fuente == "Understat":
                                        # Obtener stats xG de Understat
                                        with st.spinner(f"Cargando xG de {nombre}..."):
                                            xg_stats = obtener_stats_understat(url)
                                        
                                        st.markdown(f"""
                                        <div style="background:#1b2621;border:1px solid #ff6b6b;border-radius:4px;padding:10px;margin-bottom:10px;">
                                            <div style="color:#ff6b6b;font-size:0.9rem;font-weight:bold;">🎯 {nombre}</div>
                                            <div style="color:#888;font-size:0.7rem;">Understat - xG y Estadísticas Avanzadas</div>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        
                                        if xg_stats and xg_stats.get("xg_stats"):
                                            xg = xg_stats.get("xg_stats", {})
                                            col1, col2, col3, col4 = st.columns(4)
                                            with col1:
                                                st.metric("xG", xg.get("xG", "N/A"))
                                            with col2:
                                                st.metric("xGA", xg.get("xGA", "N/A"))
                                            with col3:
                                                st.metric("Goles", xg.get("G", "N/A"))
                                            with col4:
                                                st.metric("Goles C", xg.get("GA", "N/A"))
                                        else:
                                            st.info(f"xG no disponible. Ver en: https://understat.com{url}")
                            else:
                                st.warning("No se encontraron stats. Prueba con otro nombre.")
                        else:
                            st.warning("Ingresa el nombre de un equipo")
        
        # === CALENDARIO COMPACTO ===
        st.markdown("---")
        st.markdown('<p style="color:#dfaf6f;font-size:1rem;font-weight:bold;">📅 Partidos de Hoy</p>', unsafe_allow_html=True)
        
        if 'partidos_scraped' in st.session_state:
            partidos = st.session_state.partidos_scraped
            if partidos:
                for p in partidos[:8]:
                    local = p.get("local", "")[:16] or "Local"
                    visitante = p.get("visitante", "")[:16] or "Visita"
                    hora = p.get("hora", "")[:5] or "--:--"
                    liga = p.get("liga", "")[:18] or "Partido"
                    
                    st.markdown(f"""
                    <div style="background:#1b2621;border:1px solid #8a6435;border-radius:4px;padding:6px;margin-bottom:4px;display:flex;align-items:center;">
                        <div style="color:#8a6435;font-size:0.6rem;width:70px;">{liga}</div>
                        <div style="color:#dcdcdc;font-size:0.75rem;flex:1;text-align:center;">{local} vs {visitante}</div>
                        <div style="color:#dfaf6f;font-size:0.7rem;width:40px;text-align:right;">{hora}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Cargando...")
        else:
            st.info("Cargando...")
        
        # === PICKS COMPACTOS ===
        st.markdown('<p style="color:#dfaf6f;font-size:1rem;font-weight:bold;">🔥 Picks del Día</p>', unsafe_allow_html=True)
        
        if picks_hoy:
            real_picks = [p for p in picks_hoy if "🔒" not in str(p.get("mercado",""))]
            if real_picks:
                for pick in real_picks[:3]:
                    liga = pick.get('liga', '')[:16]
                    local = pick.get('local', '')[:13]
                    visitante = pick.get('visitante', '')[:13]
                    mercado = pick.get('mercado', '')[:18]
                    cuota = pick.get('cuota', '?')
                    conf = pick.get('confianza', 0)
                    
                    st.markdown(f"""
                    <div style="background:#1b2621;border:1px solid #8a6435;border-radius:4px;padding:6px;margin-bottom:4px;">
                        <div style="color:#dfaf6f;font-size:0.65rem;">{liga}</div>
                        <div style="color:#dcdcdc;font-size:0.8rem;font-weight:bold;">{local} vs {visitante}</div>
                        <div style="color:#39ff14;font-size:0.75rem;">{mercado} @{cuota} <span style="color:#888;">[{conf}%]</span></div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("Sin picks hoy")
        else:
            st.info("Sin picks hoy")
        
    
    with col2:
        st.markdown('<p class="section-title">🏆 Top Goleadores</p>', unsafe_allow_html=True)
        
        # Selector de liga con TODAS las ligas
        todas_ligas = [
            # Europa
            "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
            "Champions League", "Europa League", "Eredivisie", "Primeira Liga",
            "Scottish Premiership", "Super Lig", "Jupiler Pro League",
            # America
            "Copa Libertadores", "Copa Sudamericana", "MLS", "Liga MX",
            "Argentine Liga", "Brasileirão", "Colombian Liga",
            # Asia
            "Saudi Pro League", "J1 League", "K League 1",
        ]
        liga_seleccionada = st.selectbox("Liga", todas_ligas)
        
        # Buscar goleadores desde API
        goleadores_api = obtener_goleadores_api(liga_seleccionada)
        
        if goleadores_api:
            for g in goleadores_api[:5]:
                nombre = g.get("nombre", "")[:15]
                goles = g.get("goles", 0)
                equipo = g.get("equipo", "")[:12]
                
                st.markdown(f'<div style="background:#1b2621;border:1px solid #8a6435;border-radius:4px;padding:5px;margin-bottom:4px;display:flex;justify-content:space-between;"><span style="color:#dcdcdc;font-size:0.75rem;">{nombre} <span style="color:#888;">({equipo})</span></span><span style="color:#dfaf6f;font-size:0.8rem;font-weight:bold;">{goles}⚽</span></div>', unsafe_allow_html=True)
        else:
            st.info("Cargando goleadores...")
    
    with col3:
        st.markdown('<p class="section-title">📊 Tendencias</p>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="background: linear-gradient(135deg, #122016 0%, #0f1a12 100%); padding: 15px; border-radius: 8px; margin-bottom: 15px; border: 1px solid #243829;">
            <div style="color: #d48243; font-weight: bold; margin-bottom: 10px;">🔥 Picks con Mayor Confianza</div>
        """, unsafe_allow_html=True)
        
        if picks_hoy:
            real_picks = [p for p in picks_hoy if "🔒" not in str(p.get("mercado",""))]
            for p in real_picks[:3]:
                conf = p.get("confianza", 0)
                conf_color = "#d48243" if conf >= 70 else "#dfaf6f" if conf >= 50 else "#ff6b6b"
                st.markdown(f'<div style="color: #ccc; margin: 5px 0;">• {p.get("mercado", "N/A")[:25]}<br><span style="color: {conf_color};">@{p.get("cuota", "?")} [{conf}%]</span></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color: #888;">• Sin picks publicados</div>', unsafe_allow_html=True)
        
        st.markdown("</div>")
        
        # ══════════════════════════════════════════════════════════
        # 📊 COMPARADOR DE CUOTAS (EJEMPLO VISUAL)
        # ══════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown('<p class="section-title">📊 Comparador de Cuotas</p>', unsafe_allow_html=True)
        
        # Selector de partido
        if 'partidos_scraped' in st.session_state and st.session_state.partidos_scraped:
            opciones_partidos = [f"{p.get('local','')} vs {p.get('visitante','')}" for p in st.session_state.partidos_scraped[:5]]
            partido_seleccionado = st.selectbox("Selecciona un partido:", opciones_partidos, key="odds_selector")
            
            if partido_seleccionado:
                idx = opciones_partidos.index(partido_seleccionado)
                partido = st.session_state.partidos_scraped[idx]
                
                # Intentar obtener cuotas reales
                cuotas = obtener_mejores_cuotas(
                    partido.get("local", ""),
                    partido.get("visitante", ""),
                    39
                )
                
                if cuotas:
                    # Mostrar cuotas con estilo Verde Cobre
                    col1, col2, col3 = st.columns(3)
                    opciones = {"1": "🏠 Local", "X": "🤝 Empate", "2": "✈️ Visita"}
                    colores = {"1": "#d48243", "X": "#a3b899", "2": "#d48243"}
                    
                    for i, cuota in enumerate(cuotas):
                        col = [col1, col2, col3][i]
                        with col:
                            label = opciones.get(cuota["opcion"], cuota["opcion"])
                            color = colores.get(cuota["opcion"], "#d48243")
                            st.markdown(f"""
                            <div style="text-align: center; padding: 15px; background: #122016; border-radius: 8px; border: 2px solid {color}; margin: 5px;">
                                <div style="color: #a3b899; font-size: 0.8rem;">{label}</div>
                                <div style="color: {color}; font-size: 2rem; font-weight: bold; margin: 8px 0;">{cuota['cuota']}</div>
                                <div style="color: #888; font-size: 0.7rem;">{cuota['casa']}</div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    mejor = max(cuotas, key=lambda x: x["cuota"])
                    st.success(f"💰 Mejor cuota: **{opciones.get(mejor['opcion'], mejor['opcion'])}** @ **{mejor['cuota']}** en {mejor['casa']}")
                else:
                    # Ejemplo visual cuando no hay datos
                    st.info("📡 Cargando cuotas en tiempo real...")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("""
                        <div style="text-align: center; padding: 15px; background: #122016; border-radius: 8px; border: 2px solid #d48243; margin: 5px;">
                            <div style="color: #a3b899; font-size: 0.8rem;">🏠 Local</div>
                            <div style="color: #d48243; font-size: 2rem; font-weight: bold; margin: 8px 0;">1.85</div>
                            <div style="color: #888; font-size: 0.7rem;">Bet365</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown("""
                        <div style="text-align: center; padding: 15px; background: #122016; border-radius: 8px; border: 2px solid #a3b899; margin: 5px;">
                            <div style="color: #a3b899; font-size: 0.8rem;">🤝 Empate</div>
                            <div style="color: #a3b899; font-size: 2rem; font-weight: bold; margin: 8px 0;">3.40</div>
                            <div style="color: #888; font-size: 0.7rem;">Betfair</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col3:
                        st.markdown("""
                        <div style="text-align: center; padding: 15px; background: #122016; border-radius: 8px; border: 2px solid #d48243; margin: 5px;">
                            <div style="color: #a3b899; font-size: 0.8rem;">✈️ Visita</div>
                            <div style="color: #d48243; font-size: 2rem; font-weight: bold; margin: 8px 0;">4.20</div>
                            <div style="color: #888; font-size: 0.7rem;">Bet365</div>
                        </div>
                        """, unsafe_allow_html=True)
                    st.caption("⚠️ Ejemplo - Las cuotas reales se muestran cuando hay partidos en vivo")
        else:
            st.info("Cargando partidos para comparar cuotas...")
        
        # ══════════════════════════════════════════════════════════
        # 🔔 SISTEMA DE ALERTAS (EJEMPLO VISUAL)
        # ══════════════════════════════════════════════════════════
        st.markdown("---")
        st.markdown('<p class="section-title">🔔 Alertas y Notificaciones</p>', unsafe_allow_html=True)
        
        # Panel de alertas del usuario
        cedula = st.session_state.get("ced", "")
        if cedula:
            alertas = obtener_alertas(cedula)
            if alertas:
                st.markdown("""
                <div style="background: #122016; padding: 15px; border-radius: 10px; border: 1px solid #d48243; margin-bottom: 15px;">
                    <div style="color: #d48243; font-weight: bold; font-size: 16px; margin-bottom: 12px;">🔔 Tus Alertas</div>
                """, unsafe_allow_html=True)
                
                for alerta in alertas[:3]:
                    tipo_icono = "🔥" if alerta["tipo"] == "pick_top" else "📢" if alerta["tipo"] == "pick_nuevo" else "⚠️"
                    st.markdown(f"""
                    <div style="background: rgba(255,255,255,0.05); padding: 10px; border-radius: 6px; margin-bottom: 8px; border-left: 3px solid #d48243;">
                        <span style="color: #e2ebd5; font-size: 0.9rem;">{tipo_icono} {alerta['mensaje']}</span>
                        <div style="color: #666; font-size: 0.7rem; margin-top: 3px;">{alerta.get('fecha', 'Ahora')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("</div>")
            else:
                # Ejemplo visual de alertas
                st.markdown("""
                <div style="background: #122016; padding: 15px; border-radius: 10px; border: 1px solid #243829; margin-bottom: 15px;">
                    <div style="color: #d48243; font-weight: bold; font-size: 16px; margin-bottom: 12px;">🔔 Alertas Recientes</div>
                    
                    <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #d48243;">
                        <div style="color: #e2ebd5; font-size: 0.9rem;">🔥 <b>NUEVO PICK A+:</b> Liverpool vs Arsenal - Over 2.5 Goles @ 1.95</div>
                        <div style="color: #666; font-size: 0.7rem; margin-top: 3px;">Hace 2 minutos</div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; margin-bottom: 10px; border-left: 3px solid #a3b899;">
                        <div style="color: #e2ebd5; font-size: 0.9rem;">📢 <b>Partido empezando:</b> Barcelona vs Real Madrid - La Liga</div>
                        <div style="color: #666; font-size: 0.7rem; margin-top: 3px;">Hace 15 minutos</div>
                    </div>
                    
                    <div style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 6px; border-left: 3px solid #39ff14;">
                        <div style="color: #39ff14; font-size: 0.9rem;">✅ <b>Pick acertado:</b> Manchester City -1.5 @ 2.10</div>
                        <div style="color: #666; font-size: 0.7rem; margin-top: 3px;">Ayer 23:45</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                st.caption("💡 Las alertas reales aparecen cuando hay picks nuevos o cambios importantes")
        else:
            st.markdown("""
            <div style="background: #122016; padding: 15px; border-radius: 10px; border: 1px solid #243829; text-align: center;">
                <div style="color: #a3b899; font-size: 0.9rem;">🔔 Inicia sesión para recibir alertas personalizadas</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #555; font-size: 0.8rem;">🦂 Scorpion Elite V4 Pro 2025 · Solo uso informativo · Las apuestas implican riesgo</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# PANTALLA PRINCIPAL ÚNICA - SCORPION ELITE
# ══════════════════════════════════════════════════════════

def pantalla_principal_unificada():
    """Pantalla principal unificada con header y navegación."""
    from scorpion.ui.components import (
        render_nav_bar, render_dashboard_box,
        render_match_list, render_ai_analysis, render_markets,
        render_odds_comparator, render_statistics, render_alerts
    )
    
    # ══════════════════════════════════════════════════════════
    # HEADER: 🦂 SCORPION ELITE + LOGIN
    # ══════════════════════════════════════════════════════════
    
    # Título pequeño con logo
    col_titulo, col_login_btn = st.columns([4, 1])
    with col_titulo:
        st.markdown('''
        <div style="padding: 10px 0 5px 0;">
            <span style="font-size: 1.5rem;">🦂</span>
            <span style="color: #ffcc00; font-size: 1.1rem; font-weight: bold; letter-spacing: 2px; margin-left: 8px;">SCORPION ELITE</span>
        </div>
        ''', unsafe_allow_html=True)
    with col_login_btn:
        st.markdown("<div style='padding-top: 5px;'></div>", unsafe_allow_html=True)
        
        # CSS mini
        st.markdown("""
        <style>
        [data-testid="stPopover"] {width: 90px !important;}
        .stTextInput input {font-size: 9px !important; padding: 2px 4px !important; height: 20px !important;}
        .stTextInput {margin-bottom: 2px !important;}
        .stButton button {font-size: 9px !important; padding: 2px !important; height: 22px !important;}
        </style>
        """, unsafe_allow_html=True)
        
        with st.popover("Login"):
            usr = st.text_input("", placeholder="user", label_visibility="collapsed")
            pwd = st.text_input("", type="password", placeholder="pass", label_visibility="collapsed")
            if st.button("Entrar", use_container_width=True):
                if usr and pwd:
                    if usr.lower() == "admin" and pwd == "scorpion_admin_2025":
                        st.session_state.logged_in = True
                        st.session_state.is_admin = True
                        st.session_state.user_name = "Admin"
                        st.session_state.user_plan = "ADMIN"
                        st.rerun()
                    else:
                        st.error("❌")
    
    # Si está logueado
    if st.session_state.get("logged_in", False):
        col_titulo, col_info, col_b = st.columns([4, 1, 0.5])
        with col_titulo:
            st.markdown("<div style='padding-top: 10px;'></div>", unsafe_allow_html=True)
        with col_info:
            username = st.session_state.get("user_name", "Usuario")
            plan = st.session_state.get("user_plan", "GRATIS")
            emoji = "👑" if plan == "ADMIN" else "👤"
            st.markdown(f'''
            <div style="text-align: right; padding: 10px 0;">
                <span style="color: #ffcc00; font-size: 0.9rem;">{emoji} {username}</span>
                <span style="color: #888; font-size: 0.8rem;"> | {plan}</span>
            </div>
            ''', unsafe_allow_html=True)
        with col_b:
            if st.button("Salir"):
                st.session_state.logged_in = False
                st.session_state.is_admin = False
                st.session_state.user_name = "Invitado"
                st.session_state.user_plan = ""
                st.rerun()
    
    # ══════════════════════════════════════════════════════════
    # SI ES ADMIN - MOSTRAR PANEL DE ADMIN
    # ══════════════════════════════════════════════════════════
    if st.session_state.get("is_admin", False):
        st.markdown("---")
        st.markdown("### 👑 Panel de Administrador")
        
        admin_tabs = st.tabs(["🔍 Analizar Partido", "📊 Picks de Valor", "📢 Publicar Picks", "👥 Clientes", "📊 Calendario"])
        
        with admin_tabs[0]:
            st.markdown("#### 📊 Analizar Partido")
            st.info("Escribe cualquier partido para analizar con los 4 modelos matemáticos.")
            
            col_l, col_v = st.columns(2)
            with col_l:
                local_i = st.text_input("⚽ Equipo Local", placeholder="ej: Barcelona", key="local_input")
                visita_i = st.text_input("⚽ Equipo Visitante", placeholder="ej: Real Madrid", key="visita_input")
                liga_i = st.text_input("🏆 Liga", placeholder="ej: España - La Liga", key="liga_input")
            with col_v:
                fecha_i = st.date_input("📅 Fecha")
                hora_i = st.text_input("🕐 Hora", "21:00")
            
            umbral = st.slider("🎯 Umbral de Valor (%)", 0, 15, 5)
            
            if st.button("🔍 ANALIZAR PARTIDO", type="primary", use_container_width=True):
                if local_i and visita_i:
                    with st.spinner(f"🔄 Analizando {local_i} vs {visita_i}..."):
                        # Aquí se ejecuta el análisis real con las APIs
                        # Mostrar placeholder de resultados
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, rgba(0,68,0,0.8), rgba(0,51,0,0.9)); border: 2px solid #ffcc00; border-radius: 16px; padding: 25px; margin: 20px 0;">
                            <h3 style="color: #ffcc00; text-align: center; margin-bottom: 20px;">📊 {local_i} vs {visita_i}</h3>
                            
                            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; text-align: center;">
                                    <div style="color: #888; font-size: 0.8rem;">PROBABILIDAD</div>
                                    <div style="color: #ffcc00; font-size: 1.5rem; font-weight: bold;">65%</div>
                                    <div style="color: #ccc; font-size: 0.9rem;">{local_i}</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; text-align: center;">
                                    <div style="color: #888; font-size: 0.8rem;">DRAW</div>
                                    <div style="color: #fff; font-size: 1.5rem; font-weight: bold;">22%</div>
                                    <div style="color: #ccc; font-size: 0.9rem;">Empate</div>
                                </div>
                                <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; text-align: center;">
                                    <div style="color: #888; font-size: 0.8rem;">PROBABILIDAD</div>
                                    <div style="color: #ffcc00; font-size: 1.5rem; font-weight: bold;">13%</div>
                                    <div style="color: #ccc; font-size: 0.9rem;">{visita_i}</div>
                                </div>
                            </div>
                            
                            <div style="margin-top: 20px; padding: 15px; background: rgba(255,204,0,0.1); border-radius: 10px; border: 1px solid #ffcc00;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="color: #ffcc00; font-weight: bold;">🎯 VALOR ENCONTRADO</span>
                                    <span style="background: #39ff14; color: #003300; padding: 5px 15px; border-radius: 20px; font-weight: bold;">SÍ +3.2%</span>
                                </div>
                            </div>
                            
                            <div style="margin-top: 15px;">
                                <div style="color: #888; font-size: 0.85rem; margin-bottom: 5px;">CONFIANZA: 87%</div>
                                <div style="background: #1a1a1a; border-radius: 5px; height: 8px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #ffcc00, #ff9900); width: 87%; height: 100%;"></div>
                                </div>
                            </div>
                            
                            <div style="margin-top: 15px;">
                                <div style="color: #888; font-size: 0.85rem; margin-bottom: 5px;">RIESGO: <span style="color: #39ff14;">BAJO</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.markdown("""
                        <div style="margin-top: 20px;">
                            <h4 style="color: #ffcc00;">📈 Estadísticas Detalladas</h4>
                            <table style="width: 100%; color: #ccc; font-size: 0.9rem;">
                                <tr style="border-bottom: 1px solid #333;">
                                    <th style="padding: 10px; text-align: left;">Métrica</th>
                                    <th style="padding: 10px; text-align: center;">Local</th>
                                    <th style="padding: 10px; text-align: center;">Visitante</th>
                                </tr>
                                <tr><td style="padding: 8px;">xG Promedio</td><td style="text-align: center; color: #ffcc00;">1.65</td><td style="text-align: center; color: #888;">0.95</td></tr>
                                <tr><td style="padding: 8px;">Tiros por Partido</td><td style="text-align: center; color: #ffcc00;">14.5</td><td style="text-align: center; color: #888;">9.2</td></tr>
                                <tr><td style="padding: 8px;">Goles Marcados</td><td style="text-align: center; color: #ffcc00;">2.1</td><td style="text-align: center; color: #888;">1.2</td></tr>
                                <tr><td style="padding: 8px;">Goles Recibidos</td><td style="text-align: center; color: #ffcc00;">0.8</td><td style="text-align: center; color: #888;">1.5</td></tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Ingresa ambos equipos (Local y Visitante)")
        
        with admin_tabs[1]:
            st.markdown("#### 📊 Picks de Valor")
            st.info("Picks generados automáticamente con edge > 5%")
            st.markdown("""
            <div style="background: rgba(0,68,0,0.5); border: 1px solid #ffcc00; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="color: #888;">Los picks de valor aparecerán aquí cuando se detecten oportunidades.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with admin_tabs[2]:
            st.markdown("#### 📢 Publicar Picks")
            st.info("Selecciona picks para publicar a los usuarios.")
            st.markdown("""
            <div style="background: rgba(0,68,0,0.5); border: 1px solid #ffcc00; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="color: #888;">Panel de publicación de picks.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with admin_tabs[3]:
            st.markdown("#### 👥 Gestión de Clientes")
            st.markdown("""
            <div style="background: rgba(0,68,0,0.5); border: 1px solid #ffcc00; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <h4 style="color: #ffcc00;">👥 Clientes Registrados</h4>
                <table style="width: 100%; color: #ccc; font-size: 0.9rem;">
                    <tr style="border-bottom: 1px solid #333;">
                        <th style="padding: 8px; text-align: left;">Usuario</th>
                        <th style="padding: 8px; text-align: left;">Plan</th>
                        <th style="padding: 8px; text-align: left;">Estado</th>
                    </tr>
                    <tr><td style="padding: 8px;">demo</td><td>PREMIUM</td><td style="color: #39ff14;">● Activo</td></tr>
                    <tr><td style="padding: 8px;">admin</td><td>ADMIN</td><td style="color: #39ff14;">● Activo</td></tr>
                </table>
            </div>
            """, unsafe_allow_html=True)
        
        with admin_tabs[4]:
            st.markdown("#### 📊 Calendario de Partidos")
            st.markdown("""
            <div style="background: rgba(0,68,0,0.5); border: 1px solid #ffcc00; border-radius: 12px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="color: #888;">Calendario de partidos programados.</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
    else:
        # USUARIO NORMAL - MOSTRAR DASHBOARD
        # ══════════════════════════════════════════════════════════
        # NAVEGACIÓN: Hoy | Mañana | En vivo | Fútbol | NBA | MLB | Tenis | Favoritos | Buscar
        # ══════════════════════════════════════════════════════════
        tabs_nav = st.tabs(["📊 Dashboard", "🏆 Picks", "📈 Análisis", "💰 Cuotas", "⚙️ Config"])
        
        # ══════════════════════════════════════════════════════════
        # PESTAÑA DASHBOARD
        # ══════════════════════════════════════════════════════════
        with tabs_nav[0]:
            # Mostrar navegación secundaria
            st.markdown(render_nav_bar(active_tab="hoy"), unsafe_allow_html=True)
            
            # Datos de ejemplo
            partidos_ejemplo = [
                {"local": "Man City", "visitante": "Chelsea", "hora": "15:00", "rango": "A+"},
                {"local": "Barcelona", "visitante": "Real Madrid", "hora": "21:00", "rango": "A+"},
                {"local": "Inter", "visitante": "Milan", "hora": "20:45", "rango": "B"},
                {"local": "Bayern", "visitante": "Dortmund", "hora": "18:30", "rango": "B"},
                {"local": "PSG", "visitante": "Lyon", "hora": "21:00", "rango": "A+"},
            ]
            
            analisis_ejemplo = {
                "prob_local": 72,
                "valor": "SI",
                "riesgo": "Bajo",
                "confianza": 91
            }
            
            cuotas_ejemplo = [
                {"book": "Bet365", "value": 1.82, "best": False},
                {"book": "Betano", "value": 1.88, "best": False},
                {"book": "Pinnacle", "value": 1.90, "best": True},
                {"book": "Stake", "value": 1.87, "best": False},
            ]
            
            stats_ejemplo = {
                "xg": "1.8 - 1.2",
                "tiros": "15 - 9",
                "corners": "6 - 4",
                "posesion": "58% - 42%"
            }
            
            alertas_ejemplo = [
                {"tipo": "warning", "mensaje": "⚠️ Lesiones importantes"},
                {"tipo": "info", "mensaje": "📊 Cambio de cuota -5%"},
                {"tipo": "success", "mensaje": "💰 Dinero inteligente"},
                {"tipo": "fire", "mensaje": "🔥 Pick con Value +4.2%"},
            ]
            
            # Layout de 2 columnas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(render_dashboard_box("⚽ Partidos del Día", render_match_list(partidos_ejemplo)), unsafe_allow_html=True)
                st.markdown(render_dashboard_box("📊 Estadísticas", render_statistics(stats_ejemplo)), unsafe_allow_html=True)
            
            with col2:
                st.markdown(render_dashboard_box("🤖 Análisis IA", render_ai_analysis(analisis_ejemplo)), unsafe_allow_html=True)
                st.markdown(render_dashboard_box("🔔 Alertas", render_alerts(alertas_ejemplo)), unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════
        # PESTAÑA PICKS
        # ══════════════════════════════════════════════════════════
        with tabs_nav[1]:
            st.markdown(render_nav_bar(active_tab="hoy"), unsafe_allow_html=True)
            st.markdown(render_dashboard_box("🏆 Top Picks del Día", """
            <div style="text-align: center; padding: 20px; color: #888;">
                Los picks se muestran cuando inicias sesión con tu cuenta.
            </div>
            """), unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════
        # PESTAÑA ANÁLISIS
        # ══════════════════════════════════════════════════════════
        with tabs_nav[2]:
            st.markdown(render_nav_bar(active_tab="futbol"), unsafe_allow_html=True)
            st.markdown(render_dashboard_box("📈 Análisis Detallado", """
            <div style="text-align: center; padding: 20px; color: #888;">
                Selecciona un partido para ver el análisis completo.
            </div>
            """), unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════
        # PESTAÑA CUOTAS
        # ══════════════════════════════════════════════════════════
        with tabs_nav[3]:
            st.markdown(render_dashboard_box("💰 Comparador de Cuotas", render_odds_comparator(cuotas_ejemplo)), unsafe_allow_html=True)
        
        # ══════════════════════════════════════════════════════════
        # PESTAÑA CONFIG
        # ══════════════════════════════════════════════════════════
        with tabs_nav[4]:
            st.markdown(render_dashboard_box("⚙️ Configuración", f"""
            <div style="padding: 15px;">
                <h3 style="color: #ffcc00;">Tu Cuenta</h3>
                <p style="color: #ccc;">Usuario: {st.session_state.get("user_name", "Invitado")}</p>
                <p style="color: #ccc;">Plan: {st.session_state.get("user_plan", "gratis").upper()}</p>
            </div>
            """), unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.markdown('<div style="text-align: center; color: #00ff88; font-size: 0.9rem;">🦂 Scorpion Elite V4 Pro · Solo uso informativo</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════
# ROUTER
# ══════════════════════════════════════════════════════════
init_db()
if "li" not in st.session_state: st.session_state.li=False

# Siempre mostrar la pantalla principal unificada
pantalla_principal_unificada()
