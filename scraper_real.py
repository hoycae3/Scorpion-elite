#!/usr/bin/env python3
"""
Scraper Real de Fútbol - Scorpion Elite
Usa Playwright para extraer datos reales de Flashscore

Incluye:
- Partidos de los próximos 7 días
- Priorización mejorada de ligas

Ejecución: python scraper_real.py
"""

import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from supabase import create_client
import json

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Prioridades de ligas MEJORADAS
LIGAS_PRIORIDAD = {
    # Top tier (15)
    "champions league": 15,
    
    # Top europeas (13-14)
    "premier league": 14,  # Inglaterra
    "la liga": 13, "laliga": 13,
    "serie a": 12,
    "bundesliga": 11,
    "ligue 1": 10,
    
    # Europa League (9)
    "europa league": 9,
    
    # Libertadores (8)
    "libertadores": 8,
    
    # Sudamérica - Alta prioridad (7)
    "brasileiro": 7, "serie a betano": 7, "serie a brasil": 7,
    "liga argentina": 7, "primera nacional": 7, "liga profesional": 7,
    
    # Otras ligas importantes (6)
    "liga colombiana": 6, "liga i": 6, "categoría primera": 6,
    "liga 1": 6, "liga perú": 6,
    "liga chile": 6, "primera division chile": 6,
    "j1 league": 6, "j league": 6, "liga japones": 6,
    "liga uruguaya": 6, "primera division uru": 6,
    "liga mx": 6, "liga mexicana": 6,
    "copa argentina": 6,
    "copa libertadores": 6,
    
    # Europa media-alta (5-6)
    "eredivisie": 6, "eredivisie holanda": 6, "holanda": 6,
    "primeira liga": 5, "liga portuguesa": 5,
    "super lig": 5, "turkish": 5,
    "mls": 5,
    "belgian": 4, "belgian pro": 4,
    "austrian": 4, "austrian bundesliga": 4,
    "copa do brasil": 4,
}


def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase no configurado")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return None


# Equipos conocidos por liga
EQUIPOS_PREMIER = ["manchester", "liverpool", "arsenal", "chelsea", "tottenham", "manchester utd", "manchester city", "newcastle", "brighton", "aston villa", "west ham"]
EQUIPOS_LA_LIGA = ["barcelona", "real madrid", "atletico", "sevilla", "real sociedad", "villarreal", "bilbao", "betis", "valencia"]
EQUIPOS_SERIE_A = ["juventus", "inter", "ac milan", "milan", "roma", "napoli", "lazio", "atalanta", "fiorentina"]
EQUIPOS_BUNDESLIGA = ["bayern", "dortmund", "rb leipzig", "leverkusen", "frankfurt", "wolfsburg", "borussia"]
EQUIPOS_LIGUE_1 = ["psg", "marseille", "lyon", "monaco", "lille", "nice", "rennes", "lorient"]
EQUIPOS_BRASILEIRAO = ["flamengo", "palmeiras", "corinthians", "sao paulo", "grêmio", "internacional", "cruzeiro", "atletico mineiro", "botafogo", "fluminense", "bahia", "santos", "vasco", "bragantino", "mirassol", "chapecoense", "atletico-go"]
EQUIPOS_LIGA_MX = ["club america", "chivas", "cruz azul", "pumas", "tigres", "monterrey", "leon", "santos", "puebla", "tijuana", "juarez", "queretaro", "pachuca", "atlas"]
EQUIPOS_LIGA_ARG = ["river plate", "boca juniors", "independiente", "racing", "velez", "huracan", "lanus", "banfield", "estudiantes", "gimnasia", "talleres", "belgrano", "newells", "rosario central", "argentinos"]
EQUIPOS_LIGA_COL = ["millonarios", "america", "atletico nacional", "junior", "santa fe", "tolima", "medellin", "once Caldas", "pasto", "cali"]
EQUIPOS_LIGA_PERU = ["universitario", "cristal", "alianza lima", "sporting cristal", "melgar", "cienciano", "deportivo municipal", "sport boys", "cantolao", " Grau", "AD Tarma", "U. de Deportes"]
EQUIPOS_LIGA_CHILE = ["colo colo", "ucatolica", "u. de chile", "huachipato", "palestino", "audax", "magallanes", "copiapo"]
EQUIPOS_LIGA_URU = ["penarol", "nacional", "defensor", "wanderers", "cerro", "danubio", "progreso", "boston river"]
EQUIPOS_J1_LEAGUE = ["yokohama", "kawasaki", " Cerezo", "urawa", " Kashima", "frontale", "gamba", "sanfrecce", "nagoya", "tosu"]
EQUIPOS_EREDIVISIE = ["ajax", "psv", "feyenoord", "az", "twente", "utrecht"]
EQUIPOS_MLS = ["los angeles", "la galaxy", "lafc", "atlanta", "seattle", "portland", "nycfc", "new york", "miami", "orlando", "charleston", "austin", "dallas", "houston", "philadelphia", "toronto", "vancouver", "montreal", "chicago", "nashville", "colorado", "salt lake", "kansas city", "philadelphia"]
EQUIPOS_LIBERTADORES = ["palmeiras", "flamengo", "grêmio", "internacional", "athletico", "corinthians", "atletico mineiro"]


# LIGAS A EXCLUIR (muy regionales o menores)
LIGAS_EXCLUIR = [
    "queensland", "npl queensland", "npl victoria", "npl nsw", "npl western australia",
    "victoria premier", "nsw league", "sa state", "wa state",
    "tasmania", "canadian premier", "supra", "vancouver",
    "kazakhstan", "azerbaijan premier", "sierra leone premier",
    "fiji premier", "malta premier", "malaysia premier", "singapore premier",
    "hong kong premier", "taiwan league", "myanmar premier", "cambodia premier",
    "nigerian premier", "ghana premier", "kenyan premier", "ugandan premier",
    "zambia premier", "zimbabwe premier", "botswana premier",
    "india i league", "bangladesh premier", "nepal premier",
    "jordan premier", "lebanon premier", "syria premier", "iraq premier",
    "bahrain premier", "qatar league", "kuwait premier", "oman premier",
    "uae league", "saudi professional", "belarusian cup", "polish cup", 
    "czech cup", "romanian cup", "slovak cup", "friendly women",
    "ykkonen", "veikkausliiga", "kakkosliiga",  # Finlandia
    "national league", "nsfw", "nwsl women",  # Mujeres Canada
    "super league", "elite league",  # Generic
]


def calcular_prioridad(liga_nombre, pais="", equipo_home="", equipo_away=""):
    liga_lower = liga_nombre.lower()
    home_lower = equipo_home.lower() if equipo_home else ""
    away_lower = equipo_away.lower() if equipo_away else ""
    
    # Si la liga es solo "Liga" (genérica), no dar prioridad alta por equipo
    liga_es_generica = liga_lower.strip() == "liga"
    
    # EXCLUIR ligas muy regionales
    for exclude in LIGAS_EXCLUIR:
        if exclude in liga_lower:
            return 0  # Excluir completamente
    
    # PREMIUM: Solo Inglaterra tiene P14 para Premier League
    if "premier league" in liga_lower:
        if any(e in home_lower for e in EQUIPOS_PREMIER) or any(e in away_lower for e in EQUIPOS_PREMIER):
            return 14
        return 1  # Otras Premier Leagues = P1 (muy abajo)
    
    # Buscar coincidencias en liga
    for nombre, prio in LIGAS_PRIORIDAD.items():
        if nombre in liga_lower:
            return prio
    
    # PREMIUM: Detectar por equipos SOLO si la liga NO es genérica
    # (para evitar que "Arsenal Dzerzhinsk" se confunda con Arsenal de Inglaterra)
    
    if not liga_es_generica:
        # La Liga (SOLO si no es Serie B)
        if "serie b" not in liga_lower and "segunda" not in liga_lower:
            if any(e in home_lower for e in EQUIPOS_LA_LIGA) or any(e in away_lower for e in EQUIPOS_LA_LIGA):
                return 13
        
        # Serie A Italia (SOLO si no es Serie B)
        if "serie b" not in liga_lower and "segunda" not in liga_lower:
            if any(e in home_lower for e in EQUIPOS_SERIE_A) or any(e in away_lower for e in EQUIPOS_SERIE_A):
                return 12
        
        # Bundesliga (SOLO si no es 2 Bundesliga)
        if "2. bundesliga" not in liga_lower and "bundesliga 2" not in liga_lower:
            if any(e in home_lower for e in EQUIPOS_BUNDESLIGA) or any(e in away_lower for e in EQUIPOS_BUNDESLIGA):
                return 11
        
        # Ligue 1 (SOLO si no es Ligue 2)
        if "ligue 2" not in liga_lower:
            if any(e in home_lower for e in EQUIPOS_LIGUE_1) or any(e in away_lower for e in EQUIPOS_LIGUE_1):
                return 10
        
        # Premier League Inglaterra
        if any(e in home_lower for e in EQUIPOS_PREMIER) or any(e in away_lower for e in EQUIPOS_PREMIER):
            return 14
        
        # Brasileirao (incluye Serie B)
        if any(e in home_lower for e in EQUIPOS_BRASILEIRAO) or any(e in away_lower for e in EQUIPOS_BRASILEIRAO):
            if "serie b" in liga_lower:
                return 5  # Serie B de Brasil = P5
            return 7  # Serie A = P7
        
        # Liga MX
        if any(e in home_lower for e in EQUIPOS_LIGA_MX) or any(e in away_lower for e in EQUIPOS_LIGA_MX):
            return 6
        
        # Liga Argentina
        if any(e in home_lower for e in EQUIPOS_LIGA_ARG) or any(e in away_lower for e in EQUIPOS_LIGA_ARG):
            return 7
        
        # Liga Colombia
        if any(e in home_lower for e in EQUIPOS_LIGA_COL) or any(e in away_lower for e in EQUIPOS_LIGA_COL):
            return 6
        
        # Liga Peru
        if any(e in home_lower for e in EQUIPOS_LIGA_PERU) or any(e in away_lower for e in EQUIPOS_LIGA_PERU):
            return 6
        
        # Liga Chile
        if any(e in home_lower for e in EQUIPOS_LIGA_CHILE) or any(e in away_lower for e in EQUIPOS_LIGA_CHILE):
            return 6
        
        # Liga Uruguay
        if any(e in home_lower for e in EQUIPOS_LIGA_URU) or any(e in away_lower for e in EQUIPOS_LIGA_URU):
            return 6
        
        # J1 League
        if any(e in home_lower for e in EQUIPOS_J1_LEAGUE) or any(e in away_lower for e in EQUIPOS_J1_LEAGUE):
            return 6
        
        # Eredivisie
        if any(e in home_lower for e in EQUIPOS_EREDIVISIE) or any(e in away_lower for e in EQUIPOS_EREDIVISIE):
            return 6
        
        # MLS
        if any(e in home_lower for e in EQUIPOS_MLS) or any(e in away_lower for e in EQUIPOS_MLS):
            return 5
    
    # Inglaterra championship
    if "england" in pais.lower() or "inglaterra" in pais.lower():
        if "championship" in liga_lower:
            return 6
    
    # Inglaterra League One
    if "england" in pais.lower() or "inglaterra" in pais.lower():
        if "league one" in liga_lower:
            return 4
    
    # Penalizar ligas menores
    if any(x in liga_lower for x in ["friendly", "amistoso", "amical"]):
        return 1
    if any(x in liga_lower for x in ["u21", "u20", "u19", "u18", "u17", "u16"]):
        return 1
    if any(x in liga_lower for x in ["women", "femenino"]):
        return 1
    if "championship" in liga_lower:
        return 2
    
    return 1


def calcular_pick(prob_home, prob_draw, prob_away, cuota_1, cuota_x, cuota_2):
    if prob_home >= prob_draw and prob_home >= prob_away:
        pick, cuota, prob = "1", cuota_1, prob_home
    elif prob_away >= prob_draw and prob_away >= prob_home:
        pick, cuota, prob = "2", cuota_2, prob_away
    else:
        pick, cuota, prob = "X", cuota_x, prob_draw
    
    prob_implicita = round(100 / cuota, 1) if cuota > 0 else 50
    valor = round(prob - prob_implicita, 1)
    confianza = int(round((max(prob_home, prob_draw, prob_away) / (prob_home + prob_draw + prob_away)) * 100))
    
    return {"pick": pick, "cuota": cuota, "probabilidad": prob, "confianza": confianza, "valor": valor}


async def scrape_flashscore():
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER REAL (7 DÍAS)")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_matches = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Obtener la fecha actual y los próximos 7 días
        today = datetime.now()
        dates_to_scrape = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
        
        print("📅 Extrayendo partidos de los próximos 7 días...")
        
        # Primero ir a la página principal
        print("📡 Conectando a Flashscore...")
        await page.goto("https://www.flashscore.com/football/", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        print("✅ Página cargada")
        await asyncio.sleep(3)
        
        for date_str in dates_to_scrape:
            print(f"   📅 {date_str}...")
            try:
                # Scroll para cargar más partidos
                for _ in range(5):
                    await page.evaluate("window.scrollBy(0, 2000)")
                    await asyncio.sleep(1)
                
                # Extraer partidos de la página actual
                date_matches = await extract_matches_for_date(page, date_str)
                all_matches.extend(date_matches)
                print(f"      ✅ {len(date_matches)} partidos")
                
            except Exception as e:
                print(f"      ⚠️ Error: {e}")
                continue
        
        await browser.close()
    
    print(f"\n📊 Total partidos extraídos: {len(all_matches)}")
    return all_matches


async def extract_matches_for_date(page, date_str):
    """Extrae partidos para una fecha específica"""
    matches = []
    seen_matches = set()
    
    await page.wait_for_selector('.event__match', timeout=15000)
    await asyncio.sleep(2)
    
    data = await page.evaluate(f"""
        () => {{
            const matches = [];
            const seenKeys = new Set();
            const events = document.querySelectorAll('.event__match');
            
            events.forEach(event => {{
                try {{
                    const timeEl = event.querySelector('.event__time');
                    let time = timeEl ? timeEl.textContent.replace(/\\n/g, ' ').trim() : '';
                    time = time.replace('FRO', '').trim();
                    
                    const homeEl = event.querySelector('.event__homeParticipant');
                    const awayEl = event.querySelector('.event__awayParticipant');
                    const home = homeEl ? homeEl.textContent.trim() : '';
                    const away = awayEl ? awayEl.textContent.trim() : '';
                    
                    if (!home || !away) return;
                    
                    const key = home + '|' + away;
                    if (seenKeys.has(key)) return;
                    seenKeys.add(key);
                    
                    let league = 'Liga';
                    let country = '';
                    let prev = event.previousElementSibling;
                    let attempts = 0;
                    
                    while (prev && attempts < 10) {{
                        const leagueTitle = prev.querySelector('.headerLeague__title');
                        const leagueCountry = prev.querySelector('.headerLeague__country');
                        if (leagueTitle) {{
                            league = leagueTitle.textContent.trim();
                            country = leagueCountry ? leagueCountry.textContent.trim() : '';
                            break;
                        }}
                        prev = prev.previousElementSibling;
                        attempts++;
                    }}
                    
                    matches.push({{ time, home, away, league, country }});
                }} catch (e) {{}}
            }});
            
            return matches;
        }}
    """)
    
    for item in data:
        match_id = hash(f"{item['home']}{item['away']}{item['league']}{item['time']}{date_str}") % 10000000
        prioridad = calcular_prioridad(item['league'] or "Liga", item.get('country', ''), item.get('home', ''), item.get('away', ''))
        
        match_data = {
            "fixture_id": match_id,
            "fecha": date_str,
            "hora_utc": item['time'] or "00:00",
            "hora_local": item['time'],
            "liga": item['league'] or "Liga",
            "liga_id": 0,
            "pais": item.get('country', ''),
            "prioridad": prioridad,
            "equipo_home": item['home'],
            "equipo_away": item['away'],
            "prob_home": 45,
            "prob_draw": 30,
            "prob_away": 25,
            "cuota_1": 2.10,
            "cuota_x": 3.40,
            "cuota_2": 3.50,
            "pick": "1",
            "cuota_pick": 2.10,
            "confianza": 45,
            "valor": 0,
            "actualizado_en": datetime.now().isoformat()
        }
        
        matches.append(match_data)
        
        if prioridad >= 5:
            print(f"   ⭐ {item['home']} vs {item['away']} ({item['league']})")
    
    return matches


def guardar_en_supabase(supabase, partidos):
    if not supabase:
        return 0
    
    try:
        guardados = 0
        for partido in partidos:
            try:
                # Usar upsert para actualizar o insertar
                supabase.table("partidos").upsert(partido, on_conflict="fixture_id").execute()
                guardados += 1
            except Exception as e:
                # Si falla el upsert, intentar solo insert
                try:
                    supabase.table("partidos").insert(partido).execute()
                    guardados += 1
                except:
                    pass
        return guardados
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return 0


async def main():
    partidos = await scrape_flashscore()
    
    if not partidos:
        print("\n⚠️  No se encontraron partidos")
        return
    
    # Filtrar partidos excluidos (prioridad 0)
    partidos_filtrados = [p for p in partidos if p.get('prioridad', 0) > 0]
    eliminados = len(partidos) - len(partidos_filtrados)
    
    if eliminados > 0:
        print(f"📊 Excluidos {eliminados} partidos menores")
    
    print(f"\n💾 Guardando {len(partidos_filtrados)} partidos...")
    
    supabase = get_supabase_client()
    if supabase:
        guardados = guardar_en_supabase(supabase, partidos_filtrados)
        print(f"\n✅ {guardados} partidos guardados en Supabase")
    else:
        print("\n⚠️  Modo demo - datos no guardados")
        with open("partidos_debug.json", "w") as f:
            json.dump(partidos, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ SCRAPER COMPLETADO")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
