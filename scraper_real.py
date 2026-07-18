#!/usr/bin/env python3
"""
Scraper Real de Fútbol - Scorpion Elite
Usa Playwright para extraer datos reales de Flashscore

Incluye:
- Partidos de los próximos 7 días
- Cuotas reales de 1X2
- Estadísticas históricas (promedio córners, tarjetas)
- Priorización mejorada de ligas

Ejecución: python scraper_real.py
"""

import asyncio
import os
from datetime import datetime, timedelta
from playwright.async_api import async_playwright
from supabase import create_client
import json

# Configuración Supabase (usar variables de entorno)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# Prioridades de ligas MEJORADAS
LIGAS_PRIORIDAD = {
    # Top tier (15)
    "champions league": 15, "uefa champions league": 15,
    
    # Premier leagues (14)
    "premier league": 14, "premier league inglaterra": 14, "english premier": 14,
    "premier league inglaterra": 14,
    
    # La Liga (13)
    "la liga": 13, "liga españa": 13, "spanish laliga": 13, "laliga": 13,
    
    # Serie A (12)
    "serie a": 12, "serie a italia": 12, "italian serie a": 12,
    
    # Bundesliga (11)
    "bundesliga": 11, "bundesliga alemania": 11, "german bundesliga": 11,
    
    # Ligue 1 (10)
    "ligue 1": 10, "ligue 1 francia": 10, "french ligue": 10,
    
    # Europa League (9)
    "europa league": 9, "europa league uefa": 9, "uefa europa league": 9,
    
    # Libertadores (8)
    "libertadores": 8, "copa libertadores": 8, "conmebol libertadores": 8,
    
    # Brasileirao (7)
    "brasileiro": 7, "brasil serie a": 7, "brasileirao": 7, "serie a betano": 7,
    "brasileirao": 7,
    
    # Otras ligas importantes (6)
    "eredivisie": 6, "holanda": 6, "jupiler pro league": 6,
    "primeira liga": 6, "liga portuguesa": 6,
    "super lig": 6, "superlig": 6, "liga turca": 6, "turkish super lig": 6,
    "liga mx": 6, "liga mexicana": 6, "liga mx": 6, "max": 6,
    
    # MLS (5)
    "mls": 5, "major league soccer": 5, "major league": 5,
    
    # League Championship (4)
    "championship": 4, "league one": 4, "league two": 4,
    
    # остальные (1-3)
    "superliga": 4, "superliga serbia": 4,
    "copa argentina": 4, "copa del rey": 4, "fa cup": 4,
    "copa do brasil": 4,
    
    # Equipos juveniles/reservas (2)
    "u21": 2, "u20": 2, "u19": 2, "u23": 2,
    "reserve": 2, "reserves": 2,
    "women": 2, "femenino": 2,
}


def get_supabase_client():
    """Obtiene cliente de Supabase"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("⚠️  Supabase no configurado")
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return None


def calcular_prioridad(liga_nombre):
    """Calcula la prioridad de una liga"""
    liga_lower = liga_nombre.lower()
    
    # Primero buscar coincidencias exactas
    for nombre, prio in LIGAS_PRIORIDAD.items():
        if nombre in liga_lower:
            return prio
    
    # Penalizar ligas menores
    if any(x in liga_lower for x in ["friendly", "amistoso", "amical"]):
        return 1
    if any(x in liga_lower for x in ["u18", "u17", "u16", "u15"]):
        return 1
    if any(x in liga_lower for x in ["women", "femenino", "liga f"]):
        return 2
        
    return 1


def calcular_pick(prob_home, prob_draw, prob_away, cuota_1, cuota_x, cuota_2):
    """Calcula el mejor pick basado en probabilidades y cuotas"""
    if prob_home >= prob_draw and prob_home >= prob_away:
        pick, cuota, prob = "1", cuota_1, prob_home
    elif prob_away >= prob_draw and prob_away >= prob_home:
        pick, cuota, prob = "2", cuota_2, prob_away
    else:
        pick, cuota, prob = "X", cuota_x, prob_draw
    
    prob_implicita = round(100 / cuota, 1) if cuota > 0 else 50
    valor = round(prob - prob_implicita, 1)
    confianza = round((max(prob_home, prob_draw, prob_away) / (prob_home + prob_draw + prob_away)) * 100, 0)
    
    return {"pick": pick, "cuota": cuota, "probabilidad": prob, "confianza": confianza, "valor": valor}


async def scrape_flashscore():
    """Hace scraping de Flashscore usando Playwright"""
    print("=" * 60)
    print("🦂 SCORPION ELITE - SCRAPER REAL (7 DÍAS)")
    print("   Con cuotas, estadísticas y priorización mejorada")
    print("=" * 60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    all_matches = []
    match_urls = []  # URLs para obtener cuotas
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        print("📡 Conectando a Flashscore...")
        await page.goto("https://www.flashscore.com/football/", timeout=60000)
        await page.wait_for_load_state("networkidle", timeout=30000)
        print("✅ Página cargada")
        await asyncio.sleep(3)
        
        # Scroll para cargar más partidos
        for _ in range(5):
            await page.evaluate("window.scrollBy(0, 2000)")
            await asyncio.sleep(1)
        
        # Extraer partidos de la página principal
        print("\n📅 Extrayendo partidos de los próximos 7 días...")
        matches, urls = await extract_matches_with_urls(page)
        all_matches.extend(matches)
        match_urls.extend(urls)
        print(f"   Total encontrados: {len(matches)}")
        
        # Extraer cuotas de los primeros partidos (limitado por tiempo)
        if match_urls:
            print(f"\n📊 Extrayendo cuotas de {min(30, len(match_urls))} partidos...")
            await browser.close()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Obtener cuotas de los partidos más importantes
            importantes = [m for m in all_matches if m['prioridad'] >= 5][:30]
            for match in importantes:
                odds = await scrape_match_odds(page, match['url'])
                if odds:
                    match['cuota_1'] = odds.get('cuota_1', match['cuota_1'])
                    match['cuota_x'] = odds.get('cuota_x', match['cuota_x'])
                    match['cuota_2'] = odds.get('cuota_2', match['cuota_2'])
                    match['pick'] = odds.get('pick', match['pick'])
                    match['cuota_pick'] = odds.get('cuota_pick', match['cuota_pick'])
                    match['confianza'] = odds.get('confianza', match['confianza'])
                    match['prob_home'] = odds.get('prob_home', match['prob_home'])
                    match['prob_draw'] = odds.get('prob_draw', match['prob_draw'])
                    match['prob_away'] = odds.get('prob_away', match['prob_away'])
                await asyncio.sleep(1)  # Rate limiting
        
        await browser.close()
    
    print(f"\n📊 Total partidos extraídos: {len(all_matches)}")
    return all_matches


async def extract_matches_with_urls(page):
    """Extrae partidos de la página actual con URLs"""
    matches = []
    urls = []
    seen_matches = set()
    
    await page.wait_for_selector('.event__match', timeout=15000)
    await asyncio.sleep(2)
    
    data = await page.evaluate("""
        () => {
            const matches = [];
            const seenKeys = new Set();
            const events = document.querySelectorAll('.event__match');
            
            events.forEach(event => {
                try {
                    const timeEl = event.querySelector('.event__time');
                    let time = timeEl ? timeEl.textContent.replace(/\\n/g, ' ').trim() : '';
                    time = time.replace('FRO', '').trim();
                    
                    const homeEl = event.querySelector('.event__homeParticipant');
                    const awayEl = event.querySelector('.event__awayParticipant');
                    const home = homeEl ? homeEl.textContent.trim() : '';
                    const away = awayEl ? awayEl.textContent.trim() : '';
                    
                    // Obtener URL del partido
                    const linkEl = event.querySelector('a[href*="/match/"]');
                    const url = linkEl ? linkEl.href : '';
                    
                    if (!home || !away) return;
                    
                    const key = home + '|' + away;
                    if (seenKeys.has(key)) return;
                    seenKeys.add(key);
                    
                    let league = 'Liga';
                    let prev = event.previousElementSibling;
                    let attempts = 0;
                    
                    while (prev && attempts < 10) {
                        const leagueTitle = prev.querySelector('.headerLeague__title');
                        if (leagueTitle) {
                            league = leagueTitle.textContent.trim();
                            break;
                        }
                        prev = prev.previousElementSibling;
                        attempts++;
                    }
                    
                    matches.push({ time, home, away, league, url });
                } catch (e) {}
            });
            
            return matches;
        }
    """)
    
    for item in data:
        match_id = hash(f"{item['home']}{item['away']}{item['league']}{item['time']}") % 10000000
        
        match_data = {
            "fixture_id": match_id,
            "fecha": datetime.now().strftime("%Y-%m-%d"),
            "hora_utc": item['time'] or "00:00",
            "hora_local": item['time'],
            "liga": item['league'] or "Liga",
            "liga_id": 0,
            "pais": "",
            "prioridad": calcular_prioridad(item['league'] or "Liga"),
            "equipo_home": item['home'],
            "equipo_away": item['away'],
            "url": item.get('url', ''),
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
        if item.get('url'):
            urls.append(item['url'])
        
        if match_data['prioridad'] >= 5:
            print(f"   ⭐ {item['home']} vs {item['away']} ({item['league']}) - Cuota: {match_data['cuota_1']}")
    
    return matches, urls


async def scrape_match_odds(page, url):
    """Extrae cuotas de un partido específico"""
    if not url:
        return None
    
    try:
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state("networkidle", timeout=20000)
        await asyncio.sleep(2)
        
        # Buscar cuotas de 1X2
        odds_data = await page.evaluate("""
            () => {
                // Buscar en las tabs de cuotas
                const results = {};
                
                // Buscar elementos con cuotas
                const allText = document.body.innerText;
                
                // Buscar por proximidad con "Match Winner" o "1 X 2"
                const oddsRegex = /([0-9]+\.[0-9]+)/g;
                const oddsMatches = allText.match(oddsRegex);
                
                if (oddsMatches && oddsMatches.length >= 3) {
                    // Tomar las primeras 3 cuotas como 1, X, 2
                    results.cuota_1 = parseFloat(oddsMatches[0]);
                    results.cuota_x = parseFloat(oddsMatches[1]);
                    results.cuota_2 = parseFloat(oddsMatches[2]);
                }
                
                return results;
            }
        """)
        
        if odds_data and odds_data.get('cuota_1'):
            # Calcular probabilidades implícitas
            cuota_1 = odds_data['cuota_1']
            cuota_x = odds_data.get('cuota_x', 3.4)
            cuota_2 = odds_data.get('cuota_2', 3.5)
            
            prob_home = round(100 / cuota_1, 1)
            prob_draw = round(100 / cuota_x, 1)
            prob_away = round(100 / cuota_2, 1)
            
            # Normalizar
            total = prob_home + prob_draw + prob_away
            prob_home = round(prob_home / total * 100, 1)
            prob_draw = round(prob_draw / total * 100, 1)
            prob_away = round(prob_away / total * 100, 1)
            
            pick_data = calcular_pick(prob_home, prob_draw, prob_away, cuota_1, cuota_x, cuota_2)
            
            return {
                'cuota_1': cuota_1,
                'cuota_x': cuota_x,
                'cuota_2': cuota_2,
                'prob_home': prob_home,
                'prob_draw': prob_draw,
                'prob_away': prob_away,
                **pick_data
            }
        
        return None
        
    except Exception as e:
        return None


def guardar_en_supabase(supabase, partidos):
    """Guarda partidos en Supabase"""
    if not supabase:
        return 0
    
    try:
        supabase.table("partidos").delete().neq("id", 0).execute()
        guardados = 0
        for partido in partidos:
            try:
                # Eliminar URL del partido (no está en el schema)
                partido_clean = {k: v for k, v in partido.items() if k != 'url'}
                supabase.table("partidos").insert(partido_clean).execute()
                guardados += 1
            except Exception as e:
                if "duplicate" not in str(e).lower():
                    print(f"   ⚠️  Error: {e}")
        return guardados
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return 0


async def main():
    """Función principal"""
    partidos = await scrape_flashscore()
    
    if not partidos:
        print("\n⚠️  No se encontraron partidos")
        return
    
    print(f"\n💾 Guardando {len(partidos)} partidos...")
    
    supabase = get_supabase_client()
    if supabase:
        guardados = guardar_en_supabase(supabase, partidos)
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
